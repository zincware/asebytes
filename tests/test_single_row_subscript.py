"""Tests for AsyncSingleRowView[str/bytes] subscripting.

Bug: ablobdb[0][b"arrays.positions"] raises
     TypeError: 'AsyncSingleRowView' object is not subscriptable

Sync blobdb[0][b"key"] works because __getitem__(int) returns the dict
directly. Async ablobdb[0] returns AsyncSingleRowView which must support
further key subscripting to be usable.

Expected:
  await ablobdb[0][b"key"]  →  column value at row 0
  await ablobdb[0]["key"]   →  column value at row 0
  await ablobdb[0][["a", "b"]]  →  [val_a, val_b]
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from asebytes._async_views import AsyncSingleRowView


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
# AsyncSingleRowView key subscripting
# ══════════════════════════════════════════════════════════════════════════


class TestAsyncSingleRowViewKeySubscript:
    """await db[0]["key"] should return the column value, not the full row."""

    @pytest.mark.anyio
    async def test_str_key_returns_scalar(self, rows):
        parent = AsyncMockParent(rows)
        view = AsyncSingleRowView(parent, 0)
        result = await view["a"]
        assert result == 1

    @pytest.mark.anyio
    async def test_str_key_returns_array(self, rows):
        parent = AsyncMockParent(rows)
        view = AsyncSingleRowView(parent, 0)
        result = await view["b"]
        assert isinstance(result, np.ndarray)
        np.testing.assert_array_equal(result, [10, 20])

    @pytest.mark.anyio
    async def test_str_key_not_dict(self, rows):
        parent = AsyncMockParent(rows)
        view = AsyncSingleRowView(parent, 0)
        result = await view["a"]
        assert not isinstance(result, dict)

    @pytest.mark.anyio
    async def test_bytes_key_returns_scalar(self):
        """db[0][b"key"] should work with bytes-keyed parent."""
        parent = AsyncMockParent([{b"a": 1, b"b": b"hello"}])
        view = AsyncSingleRowView(parent, 0)
        result = await view[b"a"]
        assert result == 1

    @pytest.mark.anyio
    async def test_list_str_keys_returns_list(self, rows):
        parent = AsyncMockParent(rows)
        view = AsyncSingleRowView(parent, 0)
        result = await view[["a", "c"]]
        assert isinstance(result, list)
        assert result == [1, "x"]

    @pytest.mark.anyio
    async def test_list_bytes_keys_returns_list(self):
        """list[bytes] keys work with bytes-keyed parent."""
        parent = AsyncMockParent([{b"a": 1, b"c": b"x"}])
        view = AsyncSingleRowView(parent, 0)
        result = await view[[b"a", b"c"]]
        assert isinstance(result, list)
        assert result == [1, b"x"]

    @pytest.mark.anyio
    async def test_nonexistent_key_raises(self, rows):
        parent = AsyncMockParent(rows)
        view = AsyncSingleRowView(parent, 0)
        with pytest.raises(KeyError):
            await view["nonexistent"]

    @pytest.mark.anyio
    async def test_negative_index_str_key(self, rows):
        parent = AsyncMockParent(rows)
        view = AsyncSingleRowView(parent, -1)
        result = await view["a"]
        assert result == 3

    @pytest.mark.anyio
    async def test_matches_column_view_result(self, rows):
        """db[0]["a"] should equal db["a"][0]."""
        from asebytes._async_views import AsyncColumnView

        parent = AsyncMockParent(rows)
        via_row = await AsyncSingleRowView(parent, 0)["a"]
        via_col = await AsyncColumnView(parent, "a", list(range(3)))[0]
        assert via_row == via_col
