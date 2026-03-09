"""Tests for SyncToAsyncReadAdapter / SyncToAsyncReadWriteAdapter."""

from __future__ import annotations

import pytest
from typing import Any

from asebytes._backends import ReadBackend, ReadWriteBackend
from asebytes._async_backends import (
    AsyncReadBackend,
    AsyncReadWriteBackend,
    sync_to_async,
)


class MemoryReadOnly(ReadBackend):
    """Minimal read-only backend for testing."""

    def __init__(self, data: list[dict[str, Any] | None] | None = None):
        self._data = data or []

    def __len__(self) -> int:
        return len(self._data)

    def get(self, index, keys=None):
        if index < 0 or index >= len(self._data):
            raise IndexError(index)
        row = self._data[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    @staticmethod
    def list_groups(path: str, **kwargs) -> list[str]:
        return []


class MemoryReadWrite(MemoryReadOnly, ReadWriteBackend):
    """Minimal read-write backend for testing."""

    def set(self, index, value):
        if index < len(self._data):
            self._data[index] = value
        elif index == len(self._data):
            self._data.append(value)
        else:
            raise IndexError(index)

    def delete(self, index):
        del self._data[index]

    def extend(self, values):
        self._data.extend(values)

    def insert(self, index, value):
        self._data.insert(index, value)


class TestSyncToAsyncReadOnly:
    """Read-only adapter must NOT be an AsyncReadWriteBackend."""

    @pytest.mark.anyio
    async def test_read_only_adapter_type(self):
        backend = MemoryReadOnly([{"a": 1}])
        adapter = sync_to_async(backend)
        assert isinstance(adapter, AsyncReadBackend)
        assert not isinstance(adapter, AsyncReadWriteBackend)

    @pytest.mark.anyio
    async def test_read_only_adapter_get(self):
        backend = MemoryReadOnly([{"a": 1}, {"b": 2}])
        adapter = sync_to_async(backend)
        assert await adapter.get(0) == {"a": 1}
        assert await adapter.len() == 2

    @pytest.mark.anyio
    async def test_read_only_adapter_keys(self):
        backend = MemoryReadOnly([{"a": 1, "b": 2}])
        adapter = sync_to_async(backend)
        assert sorted(await adapter.keys(0)) == ["a", "b"]

    @pytest.mark.anyio
    async def test_read_only_adapter_no_set(self):
        backend = MemoryReadOnly([{"a": 1}])
        adapter = sync_to_async(backend)
        assert not hasattr(adapter, "set")


class TestSyncToAsyncReadWrite:
    """Read-write adapter must be an AsyncReadWriteBackend."""

    @pytest.mark.anyio
    async def test_read_write_adapter_type(self):
        backend = MemoryReadWrite([{"a": 1}])
        adapter = sync_to_async(backend)
        assert isinstance(adapter, AsyncReadBackend)
        assert isinstance(adapter, AsyncReadWriteBackend)

    @pytest.mark.anyio
    async def test_read_write_adapter_set(self):
        backend = MemoryReadWrite([{"a": 1}])
        adapter = sync_to_async(backend)
        await adapter.set(0, {"a": 99})
        assert await adapter.get(0) == {"a": 99}

    @pytest.mark.anyio
    async def test_read_write_adapter_update(self):
        backend = MemoryReadWrite([{"a": 1, "b": 2}])
        adapter = sync_to_async(backend)
        await adapter.update(0, {"a": 99})
        assert await adapter.get(0) == {"a": 99, "b": 2}

    @pytest.mark.anyio
    async def test_read_write_adapter_extend(self):
        backend = MemoryReadWrite([])
        adapter = sync_to_async(backend)
        await adapter.extend([{"a": 1}, {"a": 2}])
        assert await adapter.len() == 2

    @pytest.mark.anyio
    async def test_read_write_adapter_delete(self):
        backend = MemoryReadWrite([{"a": 1}, {"a": 2}])
        adapter = sync_to_async(backend)
        await adapter.delete(0)
        assert await adapter.len() == 1

    @pytest.mark.anyio
    async def test_read_write_adapter_clear(self):
        backend = MemoryReadWrite([{"a": 1}, {"a": 2}])
        adapter = sync_to_async(backend)
        await adapter.clear()
        assert await adapter.len() == 0
