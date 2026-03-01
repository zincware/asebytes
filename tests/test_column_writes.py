"""Tests for ColumnView.set() and AsyncColumnView.set() write methods.

Rules:
- Single-key: db["a"][:3].set([v1, v2, v3])  → update each row with {key: value}
- Multi-key: db[["a","b"]][:3].set([[1,10],[2,20],[3,30]])  → update each row
- Must be list: db["a"][:3].set(42) → TypeError
- Length mismatch: db["a"][:3].set([1,2]) → ValueError
- Inner length mismatch: db[["a","b"]][:3].set([[1],[2],[3]]) → ValueError
"""
from __future__ import annotations

from typing import Any

import pytest

from asebytes._views import ColumnView
from asebytes._async_views import AsyncColumnView


# ── Sync mock parent ────────────────────────────────────────────────────


class MockParent:
    def __init__(self, rows):
        self._rows = rows

    def __len__(self):
        return len(self._rows)

    def _read_row(self, index, keys=None):
        row = self._rows[index]
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    def _read_rows(self, indices, keys=None):
        return [self._read_row(i, keys) for i in indices]

    def _iter_rows(self, indices, keys=None):
        for i in indices:
            yield self._read_row(i, keys)

    def _read_column(self, key, indices):
        return [self._rows[i][key] for i in indices]

    def _build_result(self, row):
        return row

    def _write_row(self, index, data):
        self._rows[index] = data

    def _update_row(self, index, data):
        self._rows[index].update(data)

    def _update_many(self, start, data):
        for i, d in enumerate(data):
            self._rows[start + i].update(d)

    def _set_column(self, key, start, values):
        for i, v in enumerate(values):
            self._rows[start + i][key] = v

    def _write_many(self, start, data):
        for i, d in enumerate(data):
            self._rows[start + i] = d


# ── Async mock parent ───────────────────────────────────────────────────


class AsyncMockParent:
    def __init__(self, rows):
        self._rows = rows

    def __len__(self):
        return len(self._rows)

    async def len(self):
        return len(self._rows)

    async def _read_row(self, index, keys=None):
        row = self._rows[index]
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    async def _read_rows(self, indices, keys=None):
        return [await self._read_row(i, keys) for i in indices]

    async def _read_column(self, key, indices):
        return [self._rows[i][key] for i in indices]

    async def _write_row(self, index, data):
        self._rows[index] = data

    async def _update_row(self, index, data):
        self._rows[index].update(data)

    async def _update_many(self, start, data):
        for i, d in enumerate(data):
            self._rows[start + i].update(d)

    async def _set_column(self, key, start, values):
        for i, v in enumerate(values):
            self._rows[start + i][key] = v

    async def _write_many(self, start, data):
        for i, d in enumerate(data):
            self._rows[start + i] = d

    def _build_result(self, row):
        return row


@pytest.fixture
def rows():
    return [
        {"a": 1, "b": 10, "c": 100},
        {"a": 2, "b": 20, "c": 200},
        {"a": 3, "b": 30, "c": 300},
        {"a": 4, "b": 40, "c": 400},
        {"a": 5, "b": 50, "c": 500},
    ]


# ── Sync ColumnView.set() ──────────────────────────────────────────────


class TestColumnViewSetSingleKey:
    def test_set_single_key(self, rows):
        parent = MockParent([dict(r) for r in rows])
        view = ColumnView(parent, "a", list(range(5)))
        view[:3].set([10, 20, 30])
        assert parent._rows[0]["a"] == 10
        assert parent._rows[1]["a"] == 20
        assert parent._rows[2]["a"] == 30
        # untouched rows
        assert parent._rows[3]["a"] == 4
        # untouched keys
        assert parent._rows[0]["b"] == 10

    def test_set_must_be_list(self, rows):
        parent = MockParent([dict(r) for r in rows])
        view = ColumnView(parent, "a", list(range(5)))
        with pytest.raises(TypeError):
            view[:3].set(42)

    def test_set_length_mismatch(self, rows):
        parent = MockParent([dict(r) for r in rows])
        view = ColumnView(parent, "a", list(range(5)))
        with pytest.raises(ValueError):
            view[:3].set([1, 2])


class TestColumnViewSetMultiKey:
    def test_set_multi_key(self, rows):
        parent = MockParent([dict(r) for r in rows])
        view = ColumnView(parent, ["a", "b"], list(range(5)))
        view[:3].set([[10, 100], [20, 200], [30, 300]])
        assert parent._rows[0]["a"] == 10
        assert parent._rows[0]["b"] == 100
        assert parent._rows[2]["a"] == 30
        assert parent._rows[2]["b"] == 300
        # untouched
        assert parent._rows[0]["c"] == 100

    def test_set_multi_key_inner_length_mismatch(self, rows):
        parent = MockParent([dict(r) for r in rows])
        view = ColumnView(parent, ["a", "b"], list(range(5)))
        with pytest.raises(ValueError):
            view[:3].set([[1], [2], [3]])  # inner length 1, expect 2

    def test_set_readback_roundtrip(self, rows):
        """Write then read back — values should match."""
        parent = MockParent([dict(r) for r in rows])
        view = ColumnView(parent, "a", list(range(5)))
        view[:3].set([99, 88, 77])
        result = list(view[:3])
        assert result == [99, 88, 77]


# ── Async AsyncColumnView.set() ───────────────────────────────────────


class TestAsyncColumnViewset:
    @pytest.mark.anyio
    async def test_set_single_key(self, rows):
        parent = AsyncMockParent([dict(r) for r in rows])
        view = AsyncColumnView(parent, "a", list(range(5)))
        await view[:3].set([10, 20, 30])
        assert parent._rows[0]["a"] == 10
        assert parent._rows[1]["a"] == 20
        assert parent._rows[2]["a"] == 30

    @pytest.mark.anyio
    async def test_set_multi_key(self, rows):
        parent = AsyncMockParent([dict(r) for r in rows])
        view = AsyncColumnView(parent, ["a", "b"], list(range(5)))
        await view[:3].set([[10, 100], [20, 200], [30, 300]])
        assert parent._rows[0]["a"] == 10
        assert parent._rows[0]["b"] == 100

    @pytest.mark.anyio
    async def test_set_must_be_list(self, rows):
        parent = AsyncMockParent([dict(r) for r in rows])
        view = AsyncColumnView(parent, "a", list(range(5)))
        with pytest.raises(TypeError):
            await view[:3].set(42)

    @pytest.mark.anyio
    async def test_set_length_mismatch(self, rows):
        parent = AsyncMockParent([dict(r) for r in rows])
        view = AsyncColumnView(parent, "a", list(range(5)))
        with pytest.raises(ValueError):
            await view[:3].set([1, 2])
