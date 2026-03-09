"""Async column access dimensionality tests.

Same rules as sync:
- db["a"][i]     → scalar
- db["a"][:n]    → 1D list
- db[["a","b"]][i] → 1D list  (NOT dict)
- db[["a","b"]][:n] → 2D list (NOT list[dict])
"""
from __future__ import annotations

from typing import Any

import pytest

from asebytes._async_views import AsyncColumnView


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

    def _build_result(self, row):
        return row


@pytest.fixture
def parent():
    return AsyncMockParent([
        {"a": 1, "b": 10},
        {"a": 2, "b": 20},
        {"a": 3, "b": 30},
        {"a": 4, "b": 40},
        {"a": 5, "b": 50},
    ])


class TestAsyncScalarScalar:
    """db["a"][i] → scalar (via AsyncSingleRowView, already works)."""
    pass  # Already covered by existing tests


class TestAsyncVectorScalar:
    @pytest.mark.anyio
    async def test_single_key_to_list(self, parent):
        view = AsyncColumnView(parent, "a", list(range(5)))
        result = await view[:3].to_list()
        assert result == [1, 2, 3]


class TestAsyncScalarVector:
    @pytest.mark.anyio
    async def test_multi_key_to_list_returns_2d(self, parent):
        """await db[["a","b"]][:3] → [[1,10], [2,20], [3,30]]"""
        view = AsyncColumnView(parent, ["a", "b"], list(range(5)))
        result = await view[:3].to_list()
        assert result == [[1, 10], [2, 20], [3, 30]]

    @pytest.mark.anyio
    async def test_multi_key_to_list_not_dicts(self, parent):
        view = AsyncColumnView(parent, ["a", "b"], list(range(5)))
        result = await view[:3].to_list()
        assert not any(isinstance(r, dict) for r in result)

    @pytest.mark.anyio
    async def test_multi_key_aiter_yields_lists(self, parent):
        view = AsyncColumnView(parent, ["a", "b"], list(range(5)))
        sub = view[:3]
        result = []
        async for item in sub:
            result.append(item)
        assert all(isinstance(r, list) for r in result)
        assert result[0] == [1, 10]


class TestAsyncToDictUnchanged:
    @pytest.mark.anyio
    async def test_to_dict_multi(self, parent):
        view = AsyncColumnView(parent, ["a", "b"], list(range(3)))
        d = await view.to_dict()
        assert d == {"a": [1, 2, 3], "b": [10, 20, 30]}
