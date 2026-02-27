from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from ._protocols import (
    RawReadableBackend,
    RawWritableBackend,
    ReadableBackend,
    WritableBackend,
)


# ── Async bytes-level protocols ─────────────────────────────────────────


class AsyncRawReadableBackend(ABC):
    """Async read-only backend at the raw bytes level."""

    @abstractmethod
    async def alen(self) -> int: ...

    @abstractmethod
    async def get_schema(self) -> list[bytes]: ...

    @abstractmethod
    async def read_row(
        self, index: int, keys: list[bytes] | None = None
    ) -> dict[bytes, bytes] | None: ...

    async def get_available_keys(self, index: int) -> list[bytes]:
        row = await self.read_row(index)
        return list(row.keys()) if row is not None else []

    async def read_rows(
        self, indices: list[int], keys: list[bytes] | None = None
    ) -> list[dict[bytes, bytes] | None]:
        return [await self.read_row(i, keys) for i in indices]

    async def iter_rows(
        self, indices: list[int], keys: list[bytes] | None = None
    ) -> AsyncIterator[dict[bytes, bytes] | None]:
        for i in indices:
            yield await self.read_row(i, keys)


class AsyncRawWritableBackend(AsyncRawReadableBackend):
    """Async read-write backend at the raw bytes level."""

    @abstractmethod
    async def write_row(
        self, index: int, data: dict[bytes, bytes] | None
    ) -> None: ...

    @abstractmethod
    async def insert_row(
        self, index: int, data: dict[bytes, bytes] | None
    ) -> None: ...

    @abstractmethod
    async def delete_row(self, index: int) -> None: ...

    @abstractmethod
    async def append_rows(
        self, data: list[dict[bytes, bytes] | None]
    ) -> None: ...

    async def update_row(self, index: int, data: dict[bytes, bytes]) -> None:
        row = await self.read_row(index) or {}
        row.update(data)
        await self.write_row(index, row)

    async def delete_rows(self, start: int, stop: int) -> None:
        for i in range(stop - 1, start - 1, -1):
            await self.delete_row(i)

    async def write_rows(
        self, start: int, data: list[dict[bytes, bytes] | None]
    ) -> None:
        for i, d in enumerate(data):
            await self.write_row(start + i, d)

    async def drop_keys(
        self, keys: list[bytes], indices: list[int] | None = None
    ) -> None:
        if indices is None:
            n = await self.alen()
            indices = list(range(n))
        key_set = set(keys)
        for i in indices:
            row = await self.read_row(i)
            if row is None:
                continue
            pruned = {k: v for k, v in row.items() if k not in key_set}
            await self.write_row(i, pruned)

    async def reserve(self, count: int) -> None:
        await self.append_rows([None] * count)

    async def clear(self) -> None:
        n = await self.alen()
        for i in range(n - 1, -1, -1):
            await self.delete_row(i)

    async def remove(self) -> None:
        raise NotImplementedError


# ── Async str-level protocols ───────────────────────────────────────────


class AsyncReadableBackend(ABC):
    """Async read-only backend at the str/Any level."""

    @abstractmethod
    async def alen(self) -> int: ...

    @abstractmethod
    async def columns(self, index: int = 0) -> list[str]: ...

    @abstractmethod
    async def read_row(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any] | None: ...

    async def read_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any] | None]:
        return [await self.read_row(i, keys) for i in indices]

    async def iter_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> AsyncIterator[dict[str, Any] | None]:
        for i in indices:
            yield await self.read_row(i, keys)

    async def read_column(
        self, key: str, indices: list[int] | None = None
    ) -> list[Any]:
        if indices is None:
            n = await self.alen()
            indices = list(range(n))
        results = []
        for i in indices:
            row = await self.read_row(i, [key])
            results.append(row[key] if row is not None else None)
        return results


class AsyncWritableBackend(AsyncReadableBackend):
    """Async read-write backend at the str/Any level."""

    @abstractmethod
    async def write_row(
        self, index: int, data: dict[str, Any] | None
    ) -> None: ...

    @abstractmethod
    async def insert_row(
        self, index: int, data: dict[str, Any] | None
    ) -> None: ...

    @abstractmethod
    async def delete_row(self, index: int) -> None: ...

    @abstractmethod
    async def append_rows(
        self, data: list[dict[str, Any] | None]
    ) -> None: ...

    async def update_row(self, index: int, data: dict[str, Any]) -> None:
        row = await self.read_row(index) or {}
        row.update(data)
        await self.write_row(index, row)

    async def delete_rows(self, start: int, stop: int) -> None:
        for i in range(stop - 1, start - 1, -1):
            await self.delete_row(i)

    async def write_rows(
        self, start: int, data: list[dict[str, Any] | None]
    ) -> None:
        for i, d in enumerate(data):
            await self.write_row(start + i, d)

    async def drop_keys(
        self, keys: list[str], indices: list[int] | None = None
    ) -> None:
        if indices is None:
            n = await self.alen()
            indices = list(range(n))
        key_set = set(keys)
        for i in indices:
            row = await self.read_row(i)
            if row is None:
                continue
            pruned = {k: v for k, v in row.items() if k not in key_set}
            await self.write_row(i, pruned)

    async def reserve(self, count: int) -> None:
        await self.append_rows([None] * count)

    async def clear(self) -> None:
        n = await self.alen()
        for i in range(n - 1, -1, -1):
            await self.delete_row(i)

    async def remove(self) -> None:
        raise NotImplementedError


# ── Sync-to-async adapters ──────────────────────────────────────────────


class SyncToAsyncRawAdapter(AsyncRawWritableBackend):
    """Wraps a sync RawWritableBackend, runs all methods via to_thread."""

    def __init__(self, sync_backend: RawWritableBackend):
        self._sync = sync_backend

    async def alen(self) -> int:
        return await asyncio.to_thread(len, self._sync)

    async def get_schema(self) -> list[bytes]:
        return await asyncio.to_thread(self._sync.get_schema)

    async def read_row(self, index, keys=None):
        return await asyncio.to_thread(self._sync.read_row, index, keys)

    async def get_available_keys(self, index):
        return await asyncio.to_thread(self._sync.get_available_keys, index)

    async def read_rows(self, indices, keys=None):
        return await asyncio.to_thread(self._sync.read_rows, indices, keys)

    async def write_row(self, index, data):
        return await asyncio.to_thread(self._sync.write_row, index, data)

    async def insert_row(self, index, data):
        return await asyncio.to_thread(self._sync.insert_row, index, data)

    async def delete_row(self, index):
        return await asyncio.to_thread(self._sync.delete_row, index)

    async def append_rows(self, data):
        return await asyncio.to_thread(self._sync.append_rows, data)

    async def update_row(self, index, data):
        return await asyncio.to_thread(self._sync.update_row, index, data)

    async def delete_rows(self, start, stop):
        return await asyncio.to_thread(self._sync.delete_rows, start, stop)

    async def write_rows(self, start, data):
        return await asyncio.to_thread(self._sync.write_rows, start, data)

    async def drop_keys(self, keys, indices=None):
        return await asyncio.to_thread(self._sync.drop_keys, keys, indices)

    async def reserve(self, count):
        return await asyncio.to_thread(self._sync.reserve, count)

    async def clear(self):
        return await asyncio.to_thread(self._sync.clear)

    async def remove(self):
        return await asyncio.to_thread(self._sync.remove)


class SyncToAsyncAdapter(AsyncWritableBackend):
    """Wraps a sync WritableBackend, runs all methods via to_thread."""

    def __init__(self, sync_backend: WritableBackend):
        self._sync = sync_backend

    async def alen(self) -> int:
        return await asyncio.to_thread(len, self._sync)

    async def columns(self, index=0):
        return await asyncio.to_thread(self._sync.columns, index)

    async def read_row(self, index, keys=None):
        return await asyncio.to_thread(self._sync.read_row, index, keys)

    async def read_rows(self, indices, keys=None):
        return await asyncio.to_thread(self._sync.read_rows, indices, keys)

    async def read_column(self, key, indices=None):
        return await asyncio.to_thread(self._sync.read_column, key, indices)

    async def write_row(self, index, data):
        return await asyncio.to_thread(self._sync.write_row, index, data)

    async def insert_row(self, index, data):
        return await asyncio.to_thread(self._sync.insert_row, index, data)

    async def delete_row(self, index):
        return await asyncio.to_thread(self._sync.delete_row, index)

    async def append_rows(self, data):
        return await asyncio.to_thread(self._sync.append_rows, data)

    async def update_row(self, index, data):
        return await asyncio.to_thread(self._sync.update_row, index, data)

    async def delete_rows(self, start, stop):
        return await asyncio.to_thread(self._sync.delete_rows, start, stop)

    async def write_rows(self, start, data):
        return await asyncio.to_thread(self._sync.write_rows, start, data)

    async def drop_keys(self, keys, indices=None):
        return await asyncio.to_thread(self._sync.drop_keys, keys, indices)

    async def reserve(self, count):
        return await asyncio.to_thread(self._sync.reserve, count)

    async def clear(self):
        return await asyncio.to_thread(self._sync.clear)

    async def remove(self):
        return await asyncio.to_thread(self._sync.remove)
