"""Tests for ColumnView[int] returning column value, not full row.

Bug: AsyncColumnView[int] returns AsyncSingleRowView which reads the
entire row via _build_result, ignoring the column filter.

Expected: db["key"][i] should return just the value for "key" at row i,
matching the sync ColumnView behavior.

Also tests: db["nonexistent"][i] should raise, not silently return a row.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from asebytes._views import ColumnView
from asebytes._async_views import AsyncColumnView


# ── Sync mock parent ────────────────────────────────────────────────────


class MockParent:
    def __init__(self, rows: list[dict[str, Any]]):
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


# ── Async mock parent ───────────────────────────────────────────────────


class AsyncMockParent:
    def __init__(self, rows: list[dict[str, Any]]):
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

    async def _delete_row(self, index):
        del self._rows[index]

    async def _delete_rows(self, start, stop):
        for i in range(stop - 1, start - 1, -1):
            del self._rows[i]

    async def _update_row(self, index, data):
        self._rows[index].update(data)

    async def _drop_keys(self, keys, indices):
        pass

    async def _get_available_keys(self, index):
        return list(self._rows[index].keys())

    def _build_result(self, row):
        return row


@pytest.fixture
def rows():
    return [
        {"a": 1, "b": np.array([10, 20]), "c": "x"},
        {"a": 2, "b": np.array([30, 40]), "c": "y"},
        {"a": 3, "b": np.array([50, 60]), "c": "z"},
    ]


# ══════════════════════════════════════════════════════════════════════════
# Sync ColumnView[int] — should already work correctly
# ══════════════════════════════════════════════════════════════════════════


class TestSyncColumnViewIntIndex:
    """Baseline: sync ColumnView[int] returns column value, not full row."""

    def test_single_key_int_returns_scalar(self, rows):
        parent = MockParent(rows)
        view = ColumnView(parent, "a", range(3))
        assert view[0] == 1

    def test_single_key_int_returns_array(self, rows):
        parent = MockParent(rows)
        view = ColumnView(parent, "b", range(3))
        result = view[0]
        assert isinstance(result, np.ndarray)
        np.testing.assert_array_equal(result, [10, 20])

    def test_single_key_int_is_not_dict(self, rows):
        parent = MockParent(rows)
        view = ColumnView(parent, "a", range(3))
        result = view[0]
        assert not isinstance(result, dict)

    def test_multi_key_int_returns_list_of_values(self, rows):
        parent = MockParent(rows)
        view = ColumnView(parent, ["a", "c"], range(3))
        result = view[0]
        assert isinstance(result, list)
        assert result == [1, "x"]

    def test_nonexistent_key_raises(self, rows):
        parent = MockParent(rows)
        view = ColumnView(parent, "nonexistent", range(3))
        with pytest.raises(KeyError):
            view[0]

    def test_no_indices_single_key(self, rows):
        """ColumnView with _indices=None still works for int indexing."""
        parent = MockParent(rows)
        view = ColumnView(parent, "a")
        assert view[0] == 1
        assert view[2] == 3


# ══════════════════════════════════════════════════════════════════════════
# Async AsyncColumnView[int] — BUG: returns full row instead of value
# ══════════════════════════════════════════════════════════════════════════


class TestAsyncColumnViewIntIndex:
    """AsyncColumnView[int] must return column value, not full row."""

    @pytest.mark.anyio
    async def test_single_key_int_returns_scalar(self, rows):
        parent = AsyncMockParent(rows)
        view = AsyncColumnView(parent, "a", list(range(3)))
        result = await view[0]
        assert result == 1

    @pytest.mark.anyio
    async def test_single_key_int_returns_array(self, rows):
        parent = AsyncMockParent(rows)
        view = AsyncColumnView(parent, "b", list(range(3)))
        result = await view[0]
        assert isinstance(result, np.ndarray)
        np.testing.assert_array_equal(result, [10, 20])

    @pytest.mark.anyio
    async def test_single_key_int_is_not_dict(self, rows):
        parent = AsyncMockParent(rows)
        view = AsyncColumnView(parent, "a", list(range(3)))
        result = await view[0]
        assert not isinstance(result, dict)

    @pytest.mark.anyio
    async def test_multi_key_int_returns_list_of_values(self, rows):
        parent = AsyncMockParent(rows)
        view = AsyncColumnView(parent, ["a", "c"], list(range(3)))
        result = await view[0]
        assert isinstance(result, list)
        assert result == [1, "x"]

    @pytest.mark.anyio
    async def test_nonexistent_key_raises(self, rows):
        parent = AsyncMockParent(rows)
        view = AsyncColumnView(parent, "nonexistent", list(range(3)))
        with pytest.raises(KeyError):
            await view[0]

    @pytest.mark.anyio
    async def test_no_indices_single_key(self, rows):
        """AsyncColumnView with _indices=None still filters to column."""
        parent = AsyncMockParent(rows)
        view = AsyncColumnView(parent, "a")
        result = await view[0]
        assert result == 1

    @pytest.mark.anyio
    async def test_no_indices_multi_key(self, rows):
        """AsyncColumnView with _indices=None + multi key returns list."""
        parent = AsyncMockParent(rows)
        view = AsyncColumnView(parent, ["a", "c"])
        result = await view[0]
        assert isinstance(result, list)
        assert result == [1, "x"]

    @pytest.mark.anyio
    async def test_nonexistent_key_no_indices_raises(self, rows):
        """db["nonexistent"][0] should raise even with _indices=None."""
        parent = AsyncMockParent(rows)
        view = AsyncColumnView(parent, "nonexistent")
        with pytest.raises(KeyError):
            await view[0]

    @pytest.mark.anyio
    async def test_int_and_slice_return_same_values(self, rows):
        """db["a"][0] should equal (await db["a"][:1])[0]."""
        parent = AsyncMockParent(rows)
        view = AsyncColumnView(parent, "a", list(range(3)))
        scalar = await view[0]
        via_slice = await view[:1].to_list()
        assert scalar == via_slice[0]

    @pytest.mark.anyio
    async def test_negative_int(self, rows):
        parent = AsyncMockParent(rows)
        view = AsyncColumnView(parent, "a", list(range(3)))
        result = await view[-1]
        assert result == 3
