"""Tests for async awaitable views.

Covers:
- AsyncSingleRowView: __await__, set, delete, update, akeys
- AsyncRowView: __await__, __aiter__, achunked, set, delete (contiguous only),
  update, adrop, __getitem__ chaining
- AsyncColumnView: __await__, __aiter__, to_list, to_dict, __getitem__ chaining
- Non-contiguous delete raises TypeError
"""

from __future__ import annotations

from typing import Any

import pytest

from asebytes._async_views import (
    AsyncColumnView,
    AsyncRowView,
    AsyncSingleRowView,
)


# ── Async mock parent ──────────────────────────────────────────────────


class AsyncMockParent:
    """Mock parent implementing the async view parent protocol.

    Works at str-level (dict[str, Any]) like AsyncASEIO would.
    """

    def __init__(self, rows: list[dict[str, Any] | None]):
        self._rows = rows

    def __len__(self) -> int:
        return len(self._rows)

    async def _len(self) -> int:
        return len(self._rows)

    async def _read_row(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any] | None:
        row = self._rows[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    async def _read_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any] | None]:
        return [await self._read_row(i, keys) for i in indices]

    async def _read_column(
        self, key: str, indices: list[int]
    ) -> list[Any]:
        result = []
        for i in indices:
            row = self._rows[i]
            result.append(row[key] if row is not None else None)
        return result

    async def _write_row(
        self, index: int, data: dict[str, Any] | None
    ) -> None:
        if index < len(self._rows):
            self._rows[index] = data
        elif index == len(self._rows):
            self._rows.append(data)

    async def _insert_row(
        self, index: int, data: dict[str, Any] | None
    ) -> None:
        self._rows.insert(index, data)

    async def _delete_row(self, index: int) -> None:
        del self._rows[index]

    async def _delete_rows(self, start: int, stop: int) -> None:
        for i in range(stop - 1, start - 1, -1):
            del self._rows[i]

    async def _update_row(self, index: int, data: dict[str, Any]) -> None:
        row = self._rows[index] or {}
        row.update(data)
        self._rows[index] = row

    async def _drop_keys(
        self, keys: list[str], indices: list[int]
    ) -> None:
        key_set = set(keys)
        for i in indices:
            row = self._rows[i]
            if row is None:
                continue
            self._rows[i] = {k: v for k, v in row.items() if k not in key_set}

    async def _get_available_keys(self, index: int) -> list[str]:
        row = self._rows[index]
        return sorted(row.keys()) if row is not None else []

    def _build_result(self, row: dict[str, Any] | None) -> dict[str, Any] | None:
        """Identity transform — no Atoms conversion in these tests."""
        return row


@pytest.fixture
def parent():
    rows = [
        {"calc.energy": float(-i), "info.tag": f"mol_{i}", "calc.forces": [float(i)]}
        for i in range(10)
    ]
    return AsyncMockParent(rows)


@pytest.fixture
def parent_with_none():
    rows: list[dict[str, Any] | None] = [
        {"calc.energy": -1.0},
        None,
        {"calc.energy": -3.0},
    ]
    return AsyncMockParent(rows)


# ========================================================================
# AsyncSingleRowView
# ========================================================================


class TestAsyncSingleRowView:
    @pytest.mark.anyio
    async def test_await_returns_row(self, parent):
        view = AsyncSingleRowView(parent, 0)
        result = await view
        assert result == {"calc.energy": 0.0, "info.tag": "mol_0", "calc.forces": [0.0]}

    @pytest.mark.anyio
    async def test_await_none_placeholder(self, parent_with_none):
        view = AsyncSingleRowView(parent_with_none, 1)
        result = await view
        assert result is None

    @pytest.mark.anyio
    async def test_set(self, parent):
        view = AsyncSingleRowView(parent, 0)
        await view.set({"calc.energy": -99.0})
        assert parent._rows[0] == {"calc.energy": -99.0}

    @pytest.mark.anyio
    async def test_set_none(self, parent):
        view = AsyncSingleRowView(parent, 0)
        await view.set(None)
        assert parent._rows[0] is None

    @pytest.mark.anyio
    async def test_delete(self, parent):
        original_len = len(parent._rows)
        view = AsyncSingleRowView(parent, 0)
        await view.delete()
        assert len(parent._rows) == original_len - 1

    @pytest.mark.anyio
    async def test_update(self, parent):
        view = AsyncSingleRowView(parent, 0)
        await view.update({"calc.energy": -99.0})
        assert parent._rows[0]["calc.energy"] == -99.0
        assert parent._rows[0]["info.tag"] == "mol_0"  # untouched

    @pytest.mark.anyio
    async def test_akeys(self, parent):
        view = AsyncSingleRowView(parent, 0)
        keys = await view.akeys()
        assert sorted(keys) == ["calc.energy", "calc.forces", "info.tag"]

    @pytest.mark.anyio
    async def test_akeys_none_placeholder(self, parent_with_none):
        view = AsyncSingleRowView(parent_with_none, 1)
        keys = await view.akeys()
        assert keys == []


# ========================================================================
# AsyncRowView
# ========================================================================


class TestAsyncRowView:
    # -- to_list --

    @pytest.mark.anyio
    async def test_to_list_materializes(self, parent):
        view = AsyncRowView(parent, list(range(3)))
        result = await view.to_list()
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0]["calc.energy"] == 0.0

    @pytest.mark.anyio
    async def test_to_list_with_none(self, parent_with_none):
        view = AsyncRowView(parent_with_none, [0, 1, 2])
        result = await view.to_list()
        assert result[0] == {"calc.energy": -1.0}
        assert result[1] is None
        assert result[2] == {"calc.energy": -3.0}

    # -- __aiter__ --

    @pytest.mark.anyio
    async def test_aiter(self, parent):
        view = AsyncRowView(parent, list(range(3)))
        results = []
        async for row in view:
            results.append(row)
        assert len(results) == 3
        assert results[0]["calc.energy"] == 0.0

    # -- achunked --

    @pytest.mark.anyio
    async def test_achunked(self, parent):
        view = AsyncRowView(parent, list(range(10)))
        results = []
        async for row in view.achunked(3):
            results.append(row)
        assert len(results) == 10  # yields individual items, not chunks

    @pytest.mark.anyio
    async def test_achunked_chunk_larger_than_view(self, parent):
        view = AsyncRowView(parent, [0, 1, 2])
        results = []
        async for row in view.achunked(100):
            results.append(row)
        assert len(results) == 3

    @pytest.mark.anyio
    async def test_achunked_empty_view(self, parent):
        view = AsyncRowView(parent, [])
        results = []
        async for row in view.achunked(3):
            results.append(row)
        assert len(results) == 0

    # -- __len__ --

    def test_len(self, parent):
        view = AsyncRowView(parent, list(range(5)))
        assert len(view) == 5

    # -- __getitem__ chaining --

    def test_getitem_int_returns_single_view(self, parent):
        view = AsyncRowView(parent, list(range(5, 10)))
        single = view[0]
        assert isinstance(single, AsyncSingleRowView)

    def test_getitem_slice_returns_row_view(self, parent):
        view = AsyncRowView(parent, list(range(10)))
        sub = view[2:5]
        assert isinstance(sub, AsyncRowView)
        assert len(sub) == 3

    def test_getitem_list_int_returns_row_view(self, parent):
        view = AsyncRowView(parent, list(range(10)))
        sub = view[[0, 5, 9]]
        assert isinstance(sub, AsyncRowView)
        assert len(sub) == 3

    def test_getitem_str_returns_column_view(self, parent):
        view = AsyncRowView(parent, list(range(5)))
        col = view["calc.energy"]
        assert isinstance(col, AsyncColumnView)

    def test_getitem_list_str_returns_column_view(self, parent):
        view = AsyncRowView(parent, list(range(5)))
        col = view[["calc.energy", "info.tag"]]
        assert isinstance(col, AsyncColumnView)

    # -- set --

    @pytest.mark.anyio
    async def test_set_bulk(self, parent):
        view = AsyncRowView(parent, [0, 1, 2])
        new_data = [{"calc.energy": -99.0}] * 3
        await view.set(new_data)
        assert parent._rows[0] == {"calc.energy": -99.0}
        assert parent._rows[1] == {"calc.energy": -99.0}
        assert parent._rows[2] == {"calc.energy": -99.0}

    # -- delete --

    @pytest.mark.anyio
    async def test_delete_contiguous(self, parent):
        """Contiguous slice delete should work."""
        view = AsyncRowView(parent, [2, 3, 4])  # contiguous
        view._contiguous = True
        await view.delete()
        assert len(parent._rows) == 7

    @pytest.mark.anyio
    async def test_delete_non_contiguous_raises(self, parent):
        """Non-contiguous index list should raise TypeError."""
        view = AsyncRowView(parent, [2, 5, 8])  # non-contiguous
        view._contiguous = False
        with pytest.raises(TypeError, match="contiguous"):
            await view.delete()

    # -- update --

    @pytest.mark.anyio
    async def test_update_bulk(self, parent):
        view = AsyncRowView(parent, [0, 1])
        await view.update({"calc.energy": -99.0})
        assert parent._rows[0]["calc.energy"] == -99.0
        assert parent._rows[1]["calc.energy"] == -99.0
        # Other keys untouched
        assert parent._rows[0]["info.tag"] == "mol_0"

    # -- adrop --

    @pytest.mark.anyio
    async def test_adrop(self, parent):
        view = AsyncRowView(parent, [0, 1])
        await view.adrop(keys=["calc.forces"])
        assert "calc.forces" not in parent._rows[0]
        assert "calc.forces" not in parent._rows[1]
        assert "calc.energy" in parent._rows[0]  # untouched


# ========================================================================
# AsyncColumnView
# ========================================================================


class TestAsyncColumnView:
    # -- to_list (single key) --

    @pytest.mark.anyio
    async def test_to_list_single_key(self, parent):
        view = AsyncColumnView(parent, "calc.energy", list(range(3)))
        result = await view.to_list()
        assert result == [0.0, -1.0, -2.0]

    # -- to_list (multi key) --

    @pytest.mark.anyio
    async def test_to_list_multi_key(self, parent):
        view = AsyncColumnView(parent, ["calc.energy", "info.tag"], list(range(3)))
        result = await view.to_list()
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0] == [0.0, "mol_0"]

    # -- __aiter__ --

    @pytest.mark.anyio
    async def test_aiter_single(self, parent):
        view = AsyncColumnView(parent, "calc.energy", list(range(3)))
        result = []
        async for val in view:
            result.append(val)
        assert result == [0.0, -1.0, -2.0]

    @pytest.mark.anyio
    async def test_aiter_multi(self, parent):
        view = AsyncColumnView(parent, ["calc.energy", "info.tag"], list(range(3)))
        result = []
        async for row in view:
            result.append(row)
        assert len(result) == 3
        assert result[0] == [0.0, "mol_0"]

    # -- to_list --

    @pytest.mark.anyio
    async def test_to_list_single(self, parent):
        view = AsyncColumnView(parent, "calc.energy", list(range(3)))
        result = await view.to_list()
        assert result == [0.0, -1.0, -2.0]

    @pytest.mark.anyio
    async def test_to_list_multi(self, parent):
        view = AsyncColumnView(parent, ["calc.energy", "info.tag"], list(range(3)))
        result = await view.to_list()
        assert len(result) == 3
        assert result[0] == [0.0, "mol_0"]

    # -- to_dict --

    @pytest.mark.anyio
    async def test_to_dict_single(self, parent):
        view = AsyncColumnView(parent, "calc.energy", list(range(3)))
        result = await view.to_dict()
        assert result == {"calc.energy": [0.0, -1.0, -2.0]}

    @pytest.mark.anyio
    async def test_to_dict_multi(self, parent):
        view = AsyncColumnView(parent, ["calc.energy", "info.tag"], list(range(3)))
        result = await view.to_dict()
        assert result["calc.energy"] == [0.0, -1.0, -2.0]
        assert result["info.tag"] == ["mol_0", "mol_1", "mol_2"]

    # -- __len__ --

    def test_len(self, parent):
        view = AsyncColumnView(parent, "calc.energy", list(range(5)))
        assert len(view) == 5

    def test_len_none_indices(self, parent):
        view = AsyncColumnView(parent, "calc.energy")
        assert len(view) == 10

    # -- __getitem__ chaining --

    def test_getitem_slice(self, parent):
        view = AsyncColumnView(parent, "calc.energy", list(range(10)))
        sub = view[2:5]
        assert isinstance(sub, AsyncColumnView)
        assert len(sub) == 3

    def test_getitem_int_returns_column_value_view(self, parent):
        from asebytes._async_views import AsyncSingleColumnView
        view = AsyncColumnView(parent, "calc.energy", list(range(10)))
        single = view[0]
        assert isinstance(single, AsyncSingleColumnView)

    def test_getitem_str_narrows_multi_to_single(self, parent):
        view = AsyncColumnView(parent, ["calc.energy", "info.tag"], list(range(5)))
        col = view["calc.energy"]
        assert isinstance(col, AsyncColumnView)
        assert col._single

    # -- chaining patterns --

    @pytest.mark.anyio
    async def test_row_then_column(self, parent):
        """db[5:8]["calc.energy"] pattern."""
        row_view = AsyncRowView(parent, list(range(5, 8)))
        col_view = row_view["calc.energy"]
        result = await col_view.to_list()
        assert result == [-5.0, -6.0, -7.0]

    @pytest.mark.anyio
    async def test_column_then_slice(self, parent):
        """db["calc.energy"][5:8] pattern."""
        col_view = AsyncColumnView(parent, "calc.energy")
        sub = col_view[5:8]
        result = await sub.to_list()
        assert result == [-5.0, -6.0, -7.0]

    @pytest.mark.anyio
    async def test_both_orderings_same_result(self, parent):
        """db[5:8]["calc.energy"] == db["calc.energy"][5:8]"""
        via_row = await AsyncRowView(parent, list(range(5, 8)))["calc.energy"].to_list()
        via_col = await AsyncColumnView(parent, "calc.energy")[5:8].to_list()
        assert via_row == via_col
