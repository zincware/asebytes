"""AsyncASEIO — async facade for str-level backends.

Mirrors ASEIO but all I/O is async. __getitem__ is sync and returns
awaitable views; materialization happens on ``await`` or ``async for``.
"""

from __future__ import annotations

from typing import Any, overload

import ase

from ._async_backends import AsyncReadBackend, AsyncReadWriteBackend
from ._async_views import (
    AsyncASEColumnView,
    AsyncColumnView,
    AsyncRowView,
    AsyncSingleRowView,
    AsyncViewParent,
)


class AsyncASEIO:
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
            from ._registry import get_backend_cls, parse_uri
            from ._async_backends import SyncToAsyncAdapter

            scheme, _remainder = parse_uri(backend)
            cls = get_backend_cls(backend, readonly=readonly)
            if scheme is not None:
                sync_backend = cls.from_uri(backend, **kwargs)
            else:
                sync_backend = cls(backend, **kwargs)
            self._backend: AsyncReadBackend[str, Any] = SyncToAsyncAdapter(sync_backend)
        else:
            self._backend = backend

    # -- AsyncViewParent implementation ------------------------------------

    def __len__(self) -> int:
        raise TypeError(
            "len() is not available on async objects. Use 'await db.len()' instead."
        )

    async def len(self) -> int:
        return await self._backend.len()

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

    async def _get_available_keys(self, index: int) -> list[str]:
        return await self._backend.get_available_keys(index)

    def _build_result(self, row: Any) -> ase.Atoms | None:
        """Convert dict to ase.Atoms via dict_to_atoms."""
        if row is None:
            return None
        from ._convert import dict_to_atoms

        return dict_to_atoms(row)

    # ── __getitem__ → sync, returns views ─────────────────────────────

    @overload
    def __getitem__(self, index: int) -> AsyncSingleRowView[ase.Atoms | None]: ...
    @overload
    def __getitem__(self, index: slice) -> AsyncRowView[ase.Atoms | None]: ...
    @overload
    def __getitem__(self, index: list[int]) -> AsyncRowView[ase.Atoms | None]: ...
    @overload
    def __getitem__(self, index: str) -> AsyncASEColumnView: ...
    @overload
    def __getitem__(self, index: list[str]) -> AsyncASEColumnView: ...

    def __getitem__(
        self,
        index: int | slice | str | list[int] | list[str],
    ) -> AsyncSingleRowView[ase.Atoms | None] | AsyncRowView[ase.Atoms | None] | AsyncColumnView:
        if isinstance(index, int):
            # For negative indices we need len, but len is async.
            # Store the raw index; _read_row will handle IndexError at
            # the backend level.
            return AsyncSingleRowView(self, index)
        if isinstance(index, slice):
            return _DeferredSliceRowView(self, index, column_view_cls=AsyncASEColumnView)
        if isinstance(index, str):
            return AsyncASEColumnView(self, index)
        if isinstance(index, list):
            if not index:
                return AsyncRowView(self, [])
            if isinstance(index[0], int):
                return AsyncRowView(self, index, contiguous=False, column_view_cls=AsyncASEColumnView)
            if isinstance(index[0], str):
                return AsyncASEColumnView(self, index)
        raise TypeError(f"Unsupported index type: {type(index)}")

    # ── Top-level async write methods ─────────────────────────────────

    async def extend(self, data: list[Any]) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.extend(data)

    async def insert(self, index: int, data: Any) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.insert(index, data)

    async def adrop(self, *, keys: list[str]) -> None:
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

    # -- Async iteration ---------------------------------------------------

    async def __aiter__(self):
        n = await self._backend.len()
        for i in range(n):
            row = await self._backend.get(i)
            yield self._build_result(row)

    # ── Context manager ───────────────────────────────────────────────

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

    def __repr__(self) -> str:
        return f"AsyncASEIO(backend={self._backend!r})"


class _DeferredColumnFromSlice:
    """Deferred column view created from an unresolved slice row view.

    Resolves the parent slice on to_list/aiter, then delegates to the
    appropriate column view class.
    """

    def __init__(self, parent_row_view: _DeferredSliceRowView, keys: str | list[str]):
        self._parent_row_view = parent_row_view
        self._keys = keys

    async def to_list(self):
        await self._parent_row_view._ensure_resolved()
        cls = self._parent_row_view._column_view_cls
        view = cls(
            self._parent_row_view._parent,
            self._keys,
            self._parent_row_view._indices,
        )
        return await view.to_list()

    async def __aiter__(self):
        await self._parent_row_view._ensure_resolved()
        cls = self._parent_row_view._column_view_cls
        view = cls(
            self._parent_row_view._parent,
            self._keys,
            self._parent_row_view._indices,
        )
        async for item in view:
            yield item

    async def to_dict(self):
        await self._parent_row_view._ensure_resolved()
        cls = self._parent_row_view._column_view_cls
        view = cls(
            self._parent_row_view._parent,
            self._keys,
            self._parent_row_view._indices,
        )
        return await view.to_dict()

    def __getitem__(self, key):
        # Support chaining: db[0:3]["calc.energy"][0:2]
        return _DeferredSubColumnFromSlice(self, key)


class _DeferredSubColumnFromSlice:
    """Sub-selection on a deferred column, resolves parent first."""

    def __init__(self, parent: _DeferredColumnFromSlice, key):
        self._parent = parent
        self._key = key

    async def to_list(self):
        await self._parent._parent_row_view._ensure_resolved()
        cls = self._parent._parent_row_view._column_view_cls
        view = cls(
            self._parent._parent_row_view._parent,
            self._parent._keys,
            self._parent._parent_row_view._indices,
        )
        sub = view[self._key]
        if hasattr(sub, 'to_list'):
            return await sub.to_list()
        return sub

    async def __aiter__(self):
        await self._parent._parent_row_view._ensure_resolved()
        cls = self._parent._parent_row_view._column_view_cls
        view = cls(
            self._parent._parent_row_view._parent,
            self._parent._keys,
            self._parent._parent_row_view._indices,
        )
        sub = view[self._key]
        if hasattr(sub, '__aiter__'):
            async for item in sub:
                yield item


class _DeferredSliceRowView(AsyncRowView[ase.Atoms | None]):
    """AsyncRowView that resolves a slice lazily via len().

    When __getitem__ receives a slice, we can't call len() synchronously
    on an async object. This subclass stores the raw slice and resolves
    it to concrete indices on first await / aiter.
    """

    def __init__(self, parent: AsyncASEIO, slc: slice, *, column_view_cls=None):
        # Initialize with empty indices — will be resolved lazily
        super().__init__(parent, [], contiguous=True, column_view_cls=column_view_cls)
        self._slice = slc
        self._resolved = False

    async def _ensure_resolved(self) -> None:
        if not self._resolved:
            n = await self._parent.len()
            self._indices = list(range(n))[self._slice]
            self._resolved = True

    def __len__(self) -> int:
        if not self._resolved:
            raise TypeError(
                "len() not available until slice is resolved. "
                "Use 'to_list()' or 'async for' first."
            )
        return len(self._indices)

    async def to_list(self) -> list[Any]:
        await self._ensure_resolved()
        return await super().to_list()

    async def __aiter__(self):
        await self._ensure_resolved()
        async for item in super().__aiter__():
            yield item

    async def achunked(self, chunk_size: int = 1000):
        await self._ensure_resolved()
        async for item in super().achunked(chunk_size):
            yield item

    async def delete(self) -> None:
        await self._ensure_resolved()
        await super().delete()

    async def set(self, data: list[Any]) -> None:
        await self._ensure_resolved()
        await super().set(data)

    async def update(self, data: dict) -> None:
        await self._ensure_resolved()
        await super().update(data)

    async def adrop(self, keys: list[str]) -> None:
        await self._ensure_resolved()
        await super().adrop(keys)

    def __getitem__(self, key):
        # For column access (str/list[str]), we need resolved indices.
        # Since __getitem__ is sync, we create views that defer too.
        if isinstance(key, str):
            return _DeferredColumnFromSlice(self, key)
        if isinstance(key, list) and key and isinstance(key[0], str):
            return _DeferredColumnFromSlice(self, key)
        # For int/slice/list[int], delegate to parent (may need resolution)
        if self._resolved:
            return super().__getitem__(key)
        # For unresolved int/slice, we can't sub-select yet
        raise TypeError(
            "Cannot sub-select by int/slice from unresolved slice. "
            "Use 'to_list()' or 'async for' first, or index by column key."
        )
