"""Tests for async update_many / set_column ABC defaults + SyncToAsync adapter."""
from __future__ import annotations
from typing import Any

import pytest

from asebytes._async_backends import AsyncReadWriteBackend, SyncToAsyncReadWriteAdapter
from asebytes._backends import ReadWriteBackend


class InMemoryBackend(ReadWriteBackend[str, Any]):
    def __init__(self, rows):
        self._rows = list(rows)

    def __len__(self):
        return len(self._rows)

    def get(self, index, keys=None):
        row = self._rows[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    def set(self, index, value):
        self._rows[index] = value

    def delete(self, index):
        del self._rows[index]

    def extend(self, values):
        self._rows.extend(values)
        return len(self._rows)

    def insert(self, index, value):
        self._rows.insert(index, value)


class AsyncInMemoryBackend(AsyncReadWriteBackend[str, Any]):
    def __init__(self, rows):
        self._rows = list(rows)

    async def len(self):
        return len(self._rows)

    async def get(self, index, keys=None):
        row = self._rows[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    async def set(self, index, value):
        self._rows[index] = value

    async def delete(self, index):
        del self._rows[index]

    async def extend(self, values):
        self._rows.extend(values)
        return len(self._rows)

    async def insert(self, index, value):
        self._rows.insert(index, value)


ROWS = [
    {"a": 1, "b": 10},
    {"a": 2, "b": 20},
    {"a": 3, "b": 30},
    {"a": 4, "b": 40},
    {"a": 5, "b": 50},
]


class TestAsyncUpdateMany:
    @pytest.mark.anyio
    async def test_basic(self):
        be = AsyncInMemoryBackend([dict(r) for r in ROWS])
        await be.update_many(1, [{"a": 20}, {"a": 30}])
        assert be._rows[1] == {"a": 20, "b": 20}
        assert be._rows[2] == {"a": 30, "b": 30}

    @pytest.mark.anyio
    async def test_empty(self):
        be = AsyncInMemoryBackend([dict(r) for r in ROWS])
        await be.update_many(0, [])
        assert be._rows[0] == {"a": 1, "b": 10}

    @pytest.mark.anyio
    async def test_none_row(self):
        be = AsyncInMemoryBackend([dict(r) for r in ROWS])
        be._rows[0] = None
        await be.update_many(0, [{"a": 99}])
        assert be._rows[0] == {"a": 99}


class TestAsyncSetColumn:
    @pytest.mark.anyio
    async def test_basic(self):
        be = AsyncInMemoryBackend([dict(r) for r in ROWS])
        await be.set_column("a", 1, [20, 30])
        assert be._rows[1] == {"a": 20, "b": 20}
        assert be._rows[2] == {"a": 30, "b": 30}

    @pytest.mark.anyio
    async def test_empty(self):
        be = AsyncInMemoryBackend([dict(r) for r in ROWS])
        await be.set_column("a", 0, [])
        assert be._rows[0] == {"a": 1, "b": 10}


class TestSyncToAsyncAdapter:
    @pytest.mark.anyio
    async def test_update_many_delegates(self):
        sync_be = InMemoryBackend([dict(r) for r in ROWS])
        adapter = SyncToAsyncReadWriteAdapter(sync_be)
        await adapter.update_many(0, [{"a": 10}, {"a": 20}])
        assert sync_be._rows[0] == {"a": 10, "b": 10}
        assert sync_be._rows[1] == {"a": 20, "b": 20}

    @pytest.mark.anyio
    async def test_set_column_delegates(self):
        sync_be = InMemoryBackend([dict(r) for r in ROWS])
        adapter = SyncToAsyncReadWriteAdapter(sync_be)
        await adapter.set_column("a", 2, [30, 40])
        assert sync_be._rows[2] == {"a": 30, "b": 30}
        assert sync_be._rows[3] == {"a": 40, "b": 40}
