"""AsyncASEIO — async facade for str-level backends.

Mirrors ASEIO but all I/O is async. __getitem__ is sync and returns
awaitable views; materialization happens on ``await`` or ``async for``.
"""

from __future__ import annotations

from typing import Any, overload

from ._async_backends import AsyncReadBackend, AsyncReadWriteBackend
from ._async_views import (
    AsyncColumnView,
    AsyncRowView,
    AsyncSingleRowView,
    AsyncViewParent,
)


class AsyncASEIO:
    """Async storage-agnostic interface for dict[str, Any] rows.

    Wraps an AsyncReadableBackend or AsyncWritableBackend. If the backend
    is sync, wrap it with SyncToAsyncAdapter before passing it here.

    ``__getitem__`` is synchronous and returns awaitable views.
    ``await db[0]`` materializes a single row, ``await db[0:10]`` materializes
    a list.
    """

    def __init__(self, backend: AsyncReadBackend[str, Any]):
        self._backend = backend

    # -- AsyncViewParent implementation ------------------------------------

    def __len__(self) -> int:
        raise TypeError(
            "len() is not available on async objects. Use 'await db.alen()' instead."
        )

    async def alen(self) -> int:
        return await self._backend.alen()

    async def _read_row(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any] | None:
        return await self._backend.aget(index, keys)

    async def _read_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any] | None]:
        return await self._backend.aget_many(indices, keys)

    async def _read_column(self, key: str, indices: list[int]) -> list[Any]:
        return await self._backend.aget_column(key, indices)

    async def _write_row(self, index: int, data: Any) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.aset(index, data)

    async def _delete_row(self, index: int) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.adelete(index)

    async def _delete_rows(self, start: int, stop: int) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.adelete_many(start, stop)

    async def _update_row(self, index: int, data: Any) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.aupdate(index, data)

    async def _drop_keys(self, keys: list[str], indices: list[int]) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.adrop_keys(keys, indices)

    async def _get_available_keys(self, index: int) -> list[str]:
        return await self._backend.aget_available_keys(index)

    def _build_result(self, row: Any) -> Any:
        """Identity transform — returns dict as-is.

        Subclasses (or a future AsyncASEAtomIO) can override to convert
        to ase.Atoms via dict_to_atoms.
        """
        return row

    # ── __getitem__ → sync, returns views ─────────────────────────────

    @overload
    def __getitem__(self, index: int) -> AsyncSingleRowView: ...
    @overload
    def __getitem__(self, index: slice) -> AsyncRowView: ...
    @overload
    def __getitem__(self, index: list[int]) -> AsyncRowView: ...
    @overload
    def __getitem__(self, index: str) -> AsyncColumnView: ...
    @overload
    def __getitem__(self, index: list[str]) -> AsyncColumnView: ...

    def __getitem__(
        self,
        index: int | slice | str | list[int] | list[str],
    ) -> AsyncSingleRowView | AsyncRowView | AsyncColumnView:
        if isinstance(index, int):
            # For negative indices we need len, but alen is async.
            # Store the raw index; _read_row will handle IndexError at
            # the backend level.
            return AsyncSingleRowView(self, index)
        if isinstance(index, slice):
            # We can't resolve slice without len. Store slice and resolve
            # lazily in the view's __await__.
            return _DeferredSliceRowView(self, index)
        if isinstance(index, str):
            return AsyncColumnView(self, index)
        if isinstance(index, list):
            if not index:
                return AsyncRowView(self, [])
            if isinstance(index[0], int):
                return AsyncRowView(self, index, contiguous=False)
            if isinstance(index[0], str):
                return AsyncColumnView(self, index)
        raise TypeError(f"Unsupported index type: {type(index)}")

    # ── Top-level async write methods ─────────────────────────────────

    async def aextend(self, data: list[Any]) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.aextend(data)

    async def ainsert(self, index: int, data: Any) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.ainsert(index, data)

    async def adrop(self, *, keys: list[str]) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.adrop_keys(keys)

    async def aclear(self) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.aclear()

    async def aremove(self) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.aremove()

    async def areserve(self, count: int) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.areserve(count)

    # -- Async iteration ---------------------------------------------------

    async def __aiter__(self):
        n = await self._backend.alen()
        for i in range(n):
            row = await self._backend.aget(i)
            yield self._build_result(row)

    # ── Context manager ───────────────────────────────────────────────

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

    def __repr__(self) -> str:
        return f"AsyncASEIO(backend={self._backend!r})"


class _DeferredSliceRowView(AsyncRowView):
    """AsyncRowView that resolves a slice lazily via alen().

    When __getitem__ receives a slice, we can't call len() synchronously
    on an async object. This subclass stores the raw slice and resolves
    it to concrete indices on first await / aiter.
    """

    def __init__(self, parent: AsyncASEIO, slc: slice):
        # Initialize with empty indices — will be resolved lazily
        super().__init__(parent, [], contiguous=True)
        self._slice = slc
        self._resolved = False

    async def _ensure_resolved(self) -> None:
        if not self._resolved:
            n = await self._parent.alen()
            self._indices = list(range(n))[self._slice]
            self._resolved = True

    def __len__(self) -> int:
        if not self._resolved:
            raise TypeError(
                "len() not available until slice is resolved. "
                "Use 'await view' or 'async for' first."
            )
        return len(self._indices)

    def __await__(self):
        return self._deferred_materialize().__await__()

    async def _deferred_materialize(self) -> list[Any]:
        await self._ensure_resolved()
        return await super()._materialize()

    async def __aiter__(self):
        await self._ensure_resolved()
        async for item in super().__aiter__():
            yield item

    async def achunked(self, chunk_size: int = 1000):
        await self._ensure_resolved()
        async for item in super().achunked(chunk_size):
            yield item

    async def adelete(self) -> None:
        await self._ensure_resolved()
        await super().adelete()

    async def aset(self, data: list[Any]) -> None:
        await self._ensure_resolved()
        await super().aset(data)

    async def aupdate(self, data: dict) -> None:
        await self._ensure_resolved()
        await super().aupdate(data)

    async def adrop(self, keys: list[str]) -> None:
        await self._ensure_resolved()
        await super().adrop(keys)
