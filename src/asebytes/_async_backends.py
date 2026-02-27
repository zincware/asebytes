from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any, Generic, TypeVar

from ._backends import ReadWriteBackend

K = TypeVar("K")
V = TypeVar("V")


# ── Async generic read backend ───────────────────────────────────────────


class AsyncReadBackend(Generic[K, V], ABC):
    """Async read-only backend. Mirrors ReadBackend with a-prefix methods."""

    @abstractmethod
    async def alen(self) -> int: ...

    @abstractmethod
    async def aget(
        self, index: int, keys: list[K] | None = None
    ) -> dict[K, V] | None: ...

    @abstractmethod
    async def aschema(self) -> list[K]: ...

    async def aget_many(
        self, indices: list[int], keys: list[K] | None = None
    ) -> list[dict[K, V] | None]:
        """Read multiple rows. Default: loops over aget."""
        return [await self.aget(i, keys) for i in indices]

    async def aiter_rows(
        self, indices: list[int], keys: list[K] | None = None
    ) -> AsyncIterator[dict[K, V] | None]:
        """Yield rows one at a time."""
        for i in indices:
            yield await self.aget(i, keys)

    async def aget_column(self, key: K, indices: list[int] | None = None) -> list[Any]:
        """Read a single column. Default: loops over aget."""
        if indices is None:
            n = await self.alen()
            indices = list(range(n))
        results = []
        for i in indices:
            row = await self.aget(i, [key])
            results.append(row[key] if row is not None else None)
        return results

    async def aget_available_keys(self, index: int) -> list[K]:
        """Return keys present at index WITHOUT loading values.

        Override for backends where key-existence checks are cheaper than
        full reads.
        """
        row = await self.aget(index)
        if row is None:
            return []
        return list(row.keys())


# ── Async generic read-write backend ─────────────────────────────────────


class AsyncReadWriteBackend(AsyncReadBackend[K, V], ABC):
    """Async read-write backend. Mirrors ReadWriteBackend with a-prefix."""

    @abstractmethod
    async def aset(self, index: int, value: dict[K, V] | None) -> None: ...

    @abstractmethod
    async def adelete(self, index: int) -> None: ...

    @abstractmethod
    async def aextend(self, values: list[dict[K, V] | None]) -> None: ...

    @abstractmethod
    async def ainsert(self, index: int, value: dict[K, V] | None) -> None: ...

    async def aupdate(self, index: int, data: dict[K, V]) -> None:
        """Partial update. Default: aget+merge+aset."""
        row = await self.aget(index) or {}
        row.update(data)
        await self.aset(index, row)

    async def adelete_many(self, start: int, stop: int) -> None:
        """Delete contiguous range [start, stop). Default: loop in reverse."""
        for i in range(stop - 1, start - 1, -1):
            await self.adelete(i)

    async def adrop_keys(
        self, keys: list[K], indices: list[int] | None = None
    ) -> None:
        """Remove specific keys from rows."""
        if indices is None:
            n = await self.alen()
            indices = list(range(n))
        key_set = set(keys)
        for i in indices:
            row = await self.aget(i)
            if row is None:
                continue
            pruned = {k: v for k, v in row.items() if k not in key_set}
            await self.aset(i, pruned)

    async def aset_many(self, start: int, data: list[dict[K, V] | None]) -> None:
        """Overwrite contiguous rows [start, start+len(data)).

        Override for backends where batch writes are cheaper than
        individual aset() calls.
        """
        for i, row in enumerate(data):
            await self.aset(start + i, row)

    async def areserve(self, count: int) -> None:
        await self.aextend([None] * count)

    async def aclear(self) -> None:
        n = await self.alen()
        for i in range(n - 1, -1, -1):
            await self.adelete(i)

    async def aremove(self) -> None:
        raise NotImplementedError


# ── Sync-to-async adapter ────────────────────────────────────────────────


class SyncToAsyncAdapter(AsyncReadWriteBackend[K, V]):
    """Wraps a sync ReadWriteBackend[K,V] → AsyncReadWriteBackend[K,V].

    Uses asyncio.to_thread for all calls. Preserves backend overrides
    (e.g., if backend has optimized get_many, adapter calls it via to_thread).
    """

    def __init__(self, backend: ReadWriteBackend[K, V]):
        self._backend = backend

    async def alen(self) -> int:
        return await asyncio.to_thread(len, self._backend)

    async def aget(self, index, keys=None):
        return await asyncio.to_thread(self._backend.get, index, keys)

    async def aschema(self):
        return await asyncio.to_thread(self._backend.schema)

    async def aget_many(self, indices, keys=None):
        return await asyncio.to_thread(self._backend.get_many, indices, keys)

    async def aget_column(self, key, indices=None):
        return await asyncio.to_thread(self._backend.get_column, key, indices)

    async def aget_available_keys(self, index):
        return await asyncio.to_thread(self._backend.get_available_keys, index)

    async def aset(self, index, value):
        return await asyncio.to_thread(self._backend.set, index, value)

    async def adelete(self, index):
        return await asyncio.to_thread(self._backend.delete, index)

    async def aextend(self, values):
        return await asyncio.to_thread(self._backend.extend, values)

    async def ainsert(self, index, value):
        return await asyncio.to_thread(self._backend.insert, index, value)

    async def aupdate(self, index, data):
        return await asyncio.to_thread(self._backend.update, index, data)

    async def adelete_many(self, start, stop):
        return await asyncio.to_thread(self._backend.delete_many, start, stop)

    async def adrop_keys(self, keys, indices=None):
        return await asyncio.to_thread(self._backend.drop_keys, keys, indices)

    async def aset_many(self, start, data):
        return await asyncio.to_thread(self._backend.set_many, start, data)

    async def areserve(self, count):
        return await asyncio.to_thread(self._backend.reserve, count)

    async def aclear(self):
        return await asyncio.to_thread(self._backend.clear)

    async def aremove(self):
        return await asyncio.to_thread(self._backend.remove)


# ── Type aliases ─────────────────────────────────────────────────────────

AsyncBlobReadBackend = AsyncReadBackend[bytes, bytes]
AsyncBlobReadWriteBackend = AsyncReadWriteBackend[bytes, bytes]
AsyncObjectReadBackend = AsyncReadBackend[str, Any]
AsyncObjectReadWriteBackend = AsyncReadWriteBackend[str, Any]
