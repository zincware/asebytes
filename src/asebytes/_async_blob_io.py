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
    ``__getitem__`` is synchronous and returns awaitable views.
    """

    def __init__(self, backend: AsyncReadBackend[bytes, bytes]):
        self._backend = backend

    # -- AsyncViewParent implementation ------------------------------------

    def __len__(self) -> int:
        raise TypeError(
            "len() is not available on async objects. Use 'await io.alen()' instead."
        )

    async def alen(self) -> int:
        return await self._backend.alen()

    async def _read_row(
        self, index: int, keys: list[str] | None = None
    ) -> dict[bytes, bytes] | None:
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        return await self._backend.aget(index, byte_keys)

    async def _read_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[bytes, bytes] | None]:
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        return await self._backend.aget_many(indices, byte_keys)

    async def _read_column(self, key: str, indices: list[int]) -> list[Any]:
        byte_key = key.encode()
        return await self._backend.aget_column(byte_key, indices)

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
        byte_keys = [k.encode() if isinstance(k, str) else k for k in keys]
        await self._backend.adrop_keys(byte_keys, indices)

    async def _get_available_keys(self, index: int) -> list[bytes]:
        return await self._backend.aget_available_keys(index)

    def _build_result(self, row: Any) -> Any:
        """Identity transform -- returns raw dict[bytes, bytes] as-is."""
        return row

    # -- __getitem__ -> sync, returns views ---------------------------------

    @overload
    def __getitem__(self, index: int) -> AsyncSingleRowView: ...
    @overload
    def __getitem__(self, index: slice) -> AsyncRowView: ...
    @overload
    def __getitem__(self, index: list[int]) -> AsyncRowView: ...

    def __getitem__(
        self,
        index: int | slice | list[int],
    ) -> AsyncSingleRowView | AsyncRowView:
        if isinstance(index, int):
            return AsyncSingleRowView(self, index)
        if isinstance(index, slice):
            return _DeferredSliceRowView(self, index)
        if isinstance(index, list):
            if not index:
                return AsyncRowView(self, [])
            if isinstance(index[0], int):
                return AsyncRowView(self, index, contiguous=False)
        raise TypeError(f"Unsupported index type: {type(index)}")

    # -- Top-level async methods -------------------------------------------

    async def aextend(self, data: list[dict[bytes, bytes] | None]) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.aextend(data)

    async def ainsert(self, index: int, data: dict[bytes, bytes] | None) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.ainsert(index, data)

    async def adrop(self, *, keys: list[bytes]) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.adrop_keys(keys)

    async def aschema(self) -> list[bytes]:
        return await self._backend.aschema()

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

    # -- Context manager ---------------------------------------------------

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

    def __repr__(self) -> str:
        return f"AsyncBlobIO(backend={self._backend!r})"
