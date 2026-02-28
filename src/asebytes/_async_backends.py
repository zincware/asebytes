from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any, Generic, TypeVar

from ._backends import ReadBackend, ReadWriteBackend

K = TypeVar("K")
V = TypeVar("V")


# ── Async generic read backend ───────────────────────────────────────────


class AsyncReadBackend(Generic[K, V], ABC):
    """Async read-only backend. Mirrors ReadBackend with a-prefix methods."""

    @abstractmethod
    async def len(self) -> int: ...

    @abstractmethod
    async def get(
        self, index: int, keys: list[K] | None = None
    ) -> dict[K, V] | None: ...

    async def get_many(
        self, indices: list[int], keys: list[K] | None = None
    ) -> list[dict[K, V] | None]:
        """Read multiple rows. Default: loops over get."""
        return [await self.get(i, keys) for i in indices]

    async def iter_rows(
        self, indices: list[int], keys: list[K] | None = None
    ) -> AsyncIterator[dict[K, V] | None]:
        """Yield rows one at a time."""
        for i in indices:
            yield await self.get(i, keys)

    async def get_column(self, key: K, indices: list[int] | None = None) -> list[Any]:
        """Read a single column. Default: loops over get."""
        if indices is None:
            n = await self.len()
            indices = list(range(n))
        results = []
        for i in indices:
            row = await self.get(i, [key])
            results.append(row[key] if row is not None else None)
        return results

    async def keys(self, index: int) -> list[K]:
        """Return keys present at index WITHOUT loading values.

        Override for backends where key-existence checks are cheaper than
        full reads.
        """
        row = await self.get(index)
        if row is None:
            return []
        return list(row.keys())


# ── Async generic read-write backend ─────────────────────────────────────


class AsyncReadWriteBackend(AsyncReadBackend[K, V], ABC):
    """Async read-write backend. Mirrors ReadWriteBackend with a-prefix."""

    @abstractmethod
    async def set(self, index: int, value: dict[K, V] | None) -> None: ...

    @abstractmethod
    async def delete(self, index: int) -> None: ...

    @abstractmethod
    async def extend(self, values: list[dict[K, V] | None]) -> None: ...

    @abstractmethod
    async def insert(self, index: int, value: dict[K, V] | None) -> None: ...

    async def update(self, index: int, data: dict[K, V]) -> None:
        """Partial update. Default: get+merge+set."""
        row = await self.get(index) or {}
        row.update(data)
        await self.set(index, row)

    async def delete_many(self, start: int, stop: int) -> None:
        """Delete contiguous range [start, stop). Default: loop in reverse."""
        for i in range(stop - 1, start - 1, -1):
            await self.delete(i)

    async def drop_keys(
        self, keys: list[K], indices: list[int] | None = None
    ) -> None:
        """Remove specific keys from rows."""
        if indices is None:
            n = await self.len()
            indices = list(range(n))
        key_set = set(keys)
        for i in indices:
            row = await self.get(i)
            if row is None:
                continue
            pruned = {k: v for k, v in row.items() if k not in key_set}
            await self.set(i, pruned)

    async def set_many(self, start: int, data: list[dict[K, V] | None]) -> None:
        """Overwrite contiguous rows [start, start+len(data)).

        Override for backends where batch writes are cheaper than
        individual set() calls.
        """
        for i, row in enumerate(data):
            await self.set(start + i, row)

    async def reserve(self, count: int) -> None:
        await self.extend([None] * count)

    async def clear(self) -> None:
        n = await self.len()
        for i in range(n - 1, -1, -1):
            await self.delete(i)

    async def remove(self) -> None:
        raise NotImplementedError


# ── Sync-to-async adapters ──────────────────────────────────────────────


class SyncToAsyncReadAdapter(AsyncReadBackend[K, V]):
    """Wraps a sync ReadBackend[K,V] -> AsyncReadBackend[K,V].

    Uses asyncio.to_thread for all calls.
    """

    def __init__(self, backend: ReadBackend[K, V]):
        self._backend = backend

    async def len(self) -> int:
        return await asyncio.to_thread(len, self._backend)

    async def get(self, index, keys=None):
        return await asyncio.to_thread(self._backend.get, index, keys)

    async def get_many(self, indices, keys=None):
        return await asyncio.to_thread(self._backend.get_many, indices, keys)

    async def get_column(self, key, indices=None):
        return await asyncio.to_thread(self._backend.get_column, key, indices)

    async def keys(self, index):
        return await asyncio.to_thread(self._backend.keys, index)

    async def iter_rows(self, indices, keys=None):
        rows = await asyncio.to_thread(list, self._backend.iter_rows(indices, keys))
        for row in rows:
            yield row


class SyncToAsyncReadWriteAdapter(SyncToAsyncReadAdapter[K, V], AsyncReadWriteBackend[K, V]):
    """Wraps a sync ReadWriteBackend[K,V] -> AsyncReadWriteBackend[K,V].

    Inherits all read methods from SyncToAsyncReadAdapter.
    """

    def __init__(self, backend: ReadWriteBackend[K, V]):
        super().__init__(backend)

    async def set(self, index, value):
        return await asyncio.to_thread(self._backend.set, index, value)

    async def delete(self, index):
        return await asyncio.to_thread(self._backend.delete, index)

    async def extend(self, values):
        return await asyncio.to_thread(self._backend.extend, values)

    async def insert(self, index, value):
        return await asyncio.to_thread(self._backend.insert, index, value)

    async def update(self, index, data):
        return await asyncio.to_thread(self._backend.update, index, data)

    async def delete_many(self, start, stop):
        return await asyncio.to_thread(self._backend.delete_many, start, stop)

    async def drop_keys(self, keys, indices=None):
        return await asyncio.to_thread(self._backend.drop_keys, keys, indices)

    async def set_many(self, start, data):
        return await asyncio.to_thread(self._backend.set_many, start, data)

    async def reserve(self, count):
        return await asyncio.to_thread(self._backend.reserve, count)

    async def clear(self):
        return await asyncio.to_thread(self._backend.clear)

    async def remove(self):
        return await asyncio.to_thread(self._backend.remove)


def sync_to_async(backend: ReadBackend[K, V]) -> AsyncReadBackend[K, V]:
    """Wrap a sync backend as an async backend, choosing the right adapter."""
    if isinstance(backend, ReadWriteBackend):
        return SyncToAsyncReadWriteAdapter(backend)
    return SyncToAsyncReadAdapter(backend)


# Backward-compat alias
SyncToAsyncAdapter = SyncToAsyncReadWriteAdapter


# ── Type aliases ─────────────────────────────────────────────────────────

AsyncBlobReadBackend = AsyncReadBackend[bytes, bytes]
AsyncBlobReadWriteBackend = AsyncReadWriteBackend[bytes, bytes]
AsyncObjectReadBackend = AsyncReadBackend[str, Any]
AsyncObjectReadWriteBackend = AsyncReadWriteBackend[str, Any]
