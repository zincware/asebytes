"""AsyncBlobIO -- async facade for blob-level backends.

Mirrors BlobIO but all I/O is async. __getitem__ is sync and returns
awaitable views; materialization happens on ``await`` or ``async for``.
Works with dict[bytes, bytes] rows (no serialization).
"""

from __future__ import annotations

from typing import Any, overload

from ._async_backends import AsyncReadBackend, AsyncReadWriteBackend
from ._async_views import (
    AsyncColumnView,
    AsyncRowView,
    AsyncSingleRowView,
)
from ._async_object_io import _DeferredSliceRowView


class AsyncBlobIO:
    """Async storage-agnostic interface for dict[bytes, bytes] rows.

    Wraps an AsyncReadBackend[bytes, bytes] or AsyncReadWriteBackend[bytes, bytes].
    If *backend* is a string path, auto-creates a sync blob backend via the
    registry and wraps it with SyncToAsyncAdapter.

    ``__getitem__`` is synchronous and returns awaitable views.
    """

    def __init__(
        self,
        backend: str | AsyncReadBackend[bytes, bytes],
        *,
        readonly: bool | None = None,
        **kwargs: Any,
    ):
        if isinstance(backend, str):
            from ._registry import get_blob_backend_cls
            from ._async_backends import SyncToAsyncAdapter

            cls = get_blob_backend_cls(backend, readonly=readonly)
            sync_backend = cls(backend, **kwargs)
            self._backend: AsyncReadBackend[bytes, bytes] = SyncToAsyncAdapter(sync_backend)
        else:
            self._backend = backend

    # -- AsyncViewParent implementation ------------------------------------

    def __len__(self) -> int:
        raise TypeError(
            "len() is not available on async objects. Use 'await io.len()' instead."
        )

    async def len(self) -> int:
        return await self._backend.len()

    async def _read_row(
        self, index: int, keys: list[bytes] | None = None
    ) -> Any:
        return await self._backend.get(index, keys)

    async def _read_rows(
        self, indices: list[int], keys: list[bytes] | None = None
    ) -> list[Any]:
        return await self._backend.get_many(indices, keys)

    async def _read_column(self, key: bytes, indices: list[int]) -> list[Any]:
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

    async def _drop_keys(self, keys: list[bytes], indices: list[int]) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.drop_keys(keys, indices)

    async def _keys(self, index: int) -> list[bytes]:
        return await self._backend.keys(index)

    def _build_result(self, row: Any) -> dict[bytes, bytes] | None:
        """Identity transform -- returns raw dict[bytes, bytes] as-is."""
        return row

    # -- __getitem__ -> sync, returns views ---------------------------------

    @overload
    def __getitem__(self, index: int) -> AsyncSingleRowView[dict[bytes, bytes] | None]: ...
    @overload
    def __getitem__(self, index: slice) -> AsyncRowView[dict[bytes, bytes] | None]: ...
    @overload
    def __getitem__(self, index: list[int]) -> AsyncRowView[dict[bytes, bytes] | None]: ...
    @overload
    def __getitem__(self, index: str) -> AsyncColumnView: ...
    @overload
    def __getitem__(self, index: bytes) -> AsyncColumnView: ...
    @overload
    def __getitem__(self, index: list[str]) -> AsyncColumnView: ...
    @overload
    def __getitem__(self, index: list[bytes]) -> AsyncColumnView: ...

    def __getitem__(
        self,
        index: int | slice | str | bytes | list[int] | list[str] | list[bytes],
    ) -> AsyncSingleRowView[dict[bytes, bytes] | None] | AsyncRowView[dict[bytes, bytes] | None] | AsyncColumnView:
        if isinstance(index, int):
            return AsyncSingleRowView(self, index)
        if isinstance(index, slice):
            return _DeferredSliceRowView(self, index)
        if isinstance(index, (bytes, str)):
            return AsyncColumnView(self, index)
        if isinstance(index, list):
            if not index:
                return AsyncRowView(self, [])
            if isinstance(index[0], int):
                return AsyncRowView(self, index, contiguous=False)
            if isinstance(index[0], (bytes, str)):
                return AsyncColumnView(self, index)
        raise TypeError(f"Unsupported index type: {type(index)}")

    # -- Top-level async methods -------------------------------------------

    async def extend(self, data: list[dict[bytes, bytes] | None]) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.extend(data)

    async def insert(self, index: int, data: dict[bytes, bytes] | None) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.insert(index, data)

    async def drop(self, *, keys: list[bytes]) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.drop_keys(keys)

    async def get(
        self, index: int, keys: list[bytes] | None = None
    ) -> dict[bytes, bytes] | None:
        """Read a single row, optionally filtering to specific keys."""
        return await self._backend.get(index, keys)

    async def keys(self, index: int) -> list[bytes]:
        """Return keys present at *index*."""
        return await self._backend.keys(index)

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

    # -- Context manager ---------------------------------------------------

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

    def __repr__(self) -> str:
        return f"AsyncBlobIO(backend={self._backend!r})"
