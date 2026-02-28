"""AsyncObjectIO -- async facade for object-level backends.

Mirrors ObjectIO but all I/O is async. __getitem__ is sync and returns
awaitable views; materialization happens on ``await`` or ``async for``.
"""

from __future__ import annotations

from typing import Any, overload

from ._async_backends import AsyncReadBackend, AsyncReadWriteBackend
from ._async_views import (
    AsyncColumnView,
    AsyncRowView,
    AsyncSingleRowView,
    _DeferredSliceRowView,
)


class AsyncObjectIO:
    """Async storage-agnostic interface for dict[str, Any] rows.

    Wraps an AsyncReadBackend or AsyncReadWriteBackend. If *backend* is a
    string path, auto-creates a sync backend via the registry and wraps
    it with SyncToAsyncAdapter.

    ``__getitem__`` is synchronous and returns awaitable views.
    ``await db[0]`` materializes a single row, ``await db[0:10]`` materializes
    a list.
    """

    def __init__(
        self,
        backend: str | AsyncReadBackend[str, Any],
        *,
        readonly: bool | None = None,
        **kwargs: Any,
    ):
        if isinstance(backend, str):
            from ._registry import get_async_backend_cls, parse_uri
            from ._async_backends import sync_to_async, AsyncReadBackend as _AsyncRB

            scheme, _remainder = parse_uri(backend)
            cls = get_async_backend_cls(backend, readonly=readonly)
            if scheme is not None and hasattr(cls, "from_uri"):
                inst = cls.from_uri(backend, **kwargs)
            else:
                inst = cls(backend, **kwargs)
            if isinstance(inst, _AsyncRB):
                self._backend: AsyncReadBackend[str, Any] = inst
            else:
                self._backend = sync_to_async(inst)
        else:
            self._backend = backend

    # -- AsyncViewParent implementation ------------------------------------

    def __len__(self) -> int:
        raise TypeError(
            "len() is not available on async objects. Use 'await db.len()' instead."
        )

    async def len(self) -> int:
        return await self._backend.len()

    async def keys(self, index: int) -> list[str]:
        """Return keys present at *index*."""
        return await self._backend.keys(index)

    async def _read_row(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any] | None:
        return await self._backend.get(index, keys)

    async def _read_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any] | None]:
        return await self._backend.get_many(indices, keys)

    async def _read_column(self, key: str, indices: list[int]) -> list[Any]:
        return await self._backend.get_column(key, indices)

    async def _write_row(self, index: int, data: Any) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.set(index, data)

    async def _delete_row(self, index: int) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.delete(index)

    async def _delete_rows(self, start: int, stop: int) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.delete_many(start, stop)

    async def _update_row(self, index: int, data: Any) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.update(index, data)

    async def _drop_keys(self, keys: list[str], indices: list[int]) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.drop_keys(keys, indices)

    async def _keys(self, index: int) -> list[str]:
        return await self._backend.keys(index)

    def _build_result(self, row: Any) -> dict[str, Any] | None:
        """Identity transform -- returns dict as-is.

        Subclasses (e.g. AsyncASEIO) can override to convert
        to ase.Atoms via dict_to_atoms.
        """
        return row

    # -- __getitem__ -> sync, returns views ---------------------------------

    @overload
    def __getitem__(self, index: int) -> AsyncSingleRowView[dict[str, Any] | None]: ...
    @overload
    def __getitem__(self, index: slice) -> AsyncRowView[dict[str, Any] | None]: ...
    @overload
    def __getitem__(self, index: list[int]) -> AsyncRowView[dict[str, Any] | None]: ...
    @overload
    def __getitem__(self, index: str) -> AsyncColumnView: ...
    @overload
    def __getitem__(self, index: list[str]) -> AsyncColumnView: ...

    def __getitem__(
        self,
        index: int | slice | str | list[int] | list[str],
    ) -> AsyncSingleRowView[dict[str, Any] | None] | AsyncRowView[dict[str, Any] | None] | AsyncColumnView:
        if isinstance(index, int):
            return AsyncSingleRowView(self, index)
        if isinstance(index, slice):
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

    # -- Top-level async write methods -------------------------------------

    async def extend(self, data: list[Any]) -> int:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        return await self._backend.extend(data)

    async def insert(self, index: int, data: Any) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.insert(index, data)

    async def get(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any] | None:
        """Read a single row, optionally filtering to specific keys."""
        return await self._backend.get(index, keys)

    async def drop(self, *, keys: list[str]) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.drop_keys(keys)

    async def clear(self) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.clear()

    async def remove(self) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.remove()

    async def reserve(self, count: int) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.reserve(count)

    async def update(self, index: int, data: dict[str, Any]) -> None:
        """Partial update: merge *data* into existing row at *index*."""
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.update(index, data)

    # -- Async iteration ---------------------------------------------------

    async def __aiter__(self):
        n = await self._backend.len()
        for i in range(n):
            row = await self._backend.get(i)
            yield self._build_result(row)

    # -- Context manager ---------------------------------------------------

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

    def __repr__(self) -> str:
        return f"AsyncObjectIO(backend={self._backend!r})"
