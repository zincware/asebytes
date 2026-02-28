"""Tests that async views dispatch to bulk methods for contiguous indices
and fall back to individual calls for non-contiguous indices.
"""
from __future__ import annotations

from typing import Any

import pytest

from asebytes._async_views import AsyncColumnView, AsyncRowView


# ── Call-tracking async mock parent ──────────────────────────────────────


class AsyncTrackingParent:
    """Async mock parent that tracks which methods are called."""

    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = [dict(r) for r in rows]
        self.calls: list[tuple[str, ...]] = []

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

    async def _write_row(self, index, data):
        self.calls.append(("_write_row", index))
        self._rows[index] = data

    async def _update_row(self, index, data):
        self.calls.append(("_update_row", index))
        self._rows[index].update(data)

    async def _update_many(self, start, data):
        self.calls.append(("_update_many", start, len(data)))
        for i, d in enumerate(data):
            self._rows[start + i].update(d)

    async def _set_column(self, key, start, values):
        self.calls.append(("_set_column", key, start, len(values)))
        for i, v in enumerate(values):
            self._rows[start + i][key] = v

    async def _write_many(self, start, data):
        self.calls.append(("_write_many", start, len(data)))
        for i, d in enumerate(data):
            self._rows[start + i] = d

    async def _delete_row(self, index):
        del self._rows[index]

    async def _delete_rows(self, start, stop):
        for i in range(stop - 1, start - 1, -1):
            del self._rows[i]

    async def _drop_keys(self, keys, indices):
        pass

    async def _keys(self, index):
        return list(self._rows[index].keys())


@pytest.fixture
def rows():
    return [
        {"a": 1, "b": 10},
        {"a": 2, "b": 20},
        {"a": 3, "b": 30},
        {"a": 4, "b": 40},
        {"a": 5, "b": 50},
    ]


# ── AsyncRowView.set() dispatch ─────────────────────────────────────────


class TestAsyncRowViewSetDispatch:
    @pytest.mark.anyio
    async def test_contiguous_uses_write_many(self, rows):
        parent = AsyncTrackingParent(rows)
        view = AsyncRowView(parent, [0, 1, 2])
        await view.set([{"a": 10}, {"a": 20}, {"a": 30}])
        assert any(c[0] == "_write_many" for c in parent.calls)
        assert not any(c[0] == "_write_row" for c in parent.calls)

    @pytest.mark.anyio
    async def test_non_contiguous_uses_write_row(self, rows):
        parent = AsyncTrackingParent(rows)
        view = AsyncRowView(parent, [0, 2, 4])
        await view.set([{"a": 10}, {"a": 20}, {"a": 30}])
        assert any(c[0] == "_write_row" for c in parent.calls)
        assert not any(c[0] == "_write_many" for c in parent.calls)

    @pytest.mark.anyio
    async def test_contiguous_data_correct(self, rows):
        parent = AsyncTrackingParent(rows)
        view = AsyncRowView(parent, [1, 2, 3])
        await view.set([{"a": 99}, {"a": 88}, {"a": 77}])
        assert parent._rows[1] == {"a": 99}
        assert parent._rows[2] == {"a": 88}
        assert parent._rows[3] == {"a": 77}
        assert parent._rows[0] == {"a": 1, "b": 10}  # untouched


# ── AsyncRowView.update() dispatch ──────────────────────────────────────


class TestAsyncRowViewUpdateDispatch:
    @pytest.mark.anyio
    async def test_contiguous_uses_update_many(self, rows):
        parent = AsyncTrackingParent(rows)
        view = AsyncRowView(parent, [0, 1, 2])
        await view.update({"a": 99})
        assert any(c[0] == "_update_many" for c in parent.calls)
        assert not any(c[0] == "_update_row" for c in parent.calls)

    @pytest.mark.anyio
    async def test_non_contiguous_uses_update_row(self, rows):
        parent = AsyncTrackingParent(rows)
        view = AsyncRowView(parent, [0, 2, 4])
        await view.update({"a": 99})
        assert any(c[0] == "_update_row" for c in parent.calls)
        assert not any(c[0] == "_update_many" for c in parent.calls)

    @pytest.mark.anyio
    async def test_contiguous_data_correct(self, rows):
        parent = AsyncTrackingParent(rows)
        view = AsyncRowView(parent, [0, 1, 2])
        await view.update({"a": 99})
        assert parent._rows[0]["a"] == 99
        assert parent._rows[0]["b"] == 10  # untouched
        assert parent._rows[1]["a"] == 99
        assert parent._rows[2]["a"] == 99


# ── AsyncColumnView.set() single-key dispatch ───────────────────────────


class TestAsyncColumnViewSetSingleKeyDispatch:
    @pytest.mark.anyio
    async def test_contiguous_uses_set_column(self, rows):
        parent = AsyncTrackingParent(rows)
        view = AsyncColumnView(parent, "a", list(range(5)))
        await view[:3].set([10, 20, 30])
        assert any(c[0] == "_set_column" for c in parent.calls)
        assert not any(c[0] == "_update_row" for c in parent.calls)

    @pytest.mark.anyio
    async def test_non_contiguous_uses_update_row(self, rows):
        parent = AsyncTrackingParent(rows)
        view = AsyncColumnView(parent, "a", [0, 2, 4])
        await view.set([10, 20, 30])
        assert any(c[0] == "_update_row" for c in parent.calls)
        assert not any(c[0] == "_set_column" for c in parent.calls)

    @pytest.mark.anyio
    async def test_contiguous_data_correct(self, rows):
        parent = AsyncTrackingParent(rows)
        view = AsyncColumnView(parent, "a", list(range(5)))
        await view[:3].set([10, 20, 30])
        assert parent._rows[0]["a"] == 10
        assert parent._rows[1]["a"] == 20
        assert parent._rows[2]["a"] == 30
        assert parent._rows[0]["b"] == 10  # untouched


# ── AsyncColumnView.set() multi-key dispatch ────────────────────────────


class TestAsyncColumnViewSetMultiKeyDispatch:
    @pytest.mark.anyio
    async def test_contiguous_uses_update_many(self, rows):
        parent = AsyncTrackingParent(rows)
        view = AsyncColumnView(parent, ["a", "b"], list(range(5)))
        await view[:3].set([[10, 100], [20, 200], [30, 300]])
        assert any(c[0] == "_update_many" for c in parent.calls)
        assert not any(c[0] == "_update_row" for c in parent.calls)

    @pytest.mark.anyio
    async def test_non_contiguous_uses_update_row(self, rows):
        parent = AsyncTrackingParent(rows)
        view = AsyncColumnView(parent, ["a", "b"], [0, 2, 4])
        await view.set([[10, 100], [20, 200], [30, 300]])
        assert any(c[0] == "_update_row" for c in parent.calls)
        assert not any(c[0] == "_update_many" for c in parent.calls)

    @pytest.mark.anyio
    async def test_contiguous_data_correct(self, rows):
        parent = AsyncTrackingParent(rows)
        view = AsyncColumnView(parent, ["a", "b"], list(range(5)))
        await view[:3].set([[10, 100], [20, 200], [30, 300]])
        assert parent._rows[0]["a"] == 10
        assert parent._rows[0]["b"] == 100
        assert parent._rows[2]["a"] == 30
        assert parent._rows[2]["b"] == 300


# ── Edge cases ──────────────────────────────────────────────────────────


class TestAsyncBulkWriteEdgeCases:
    @pytest.mark.anyio
    async def test_single_element_is_contiguous(self, rows):
        """A single-element view is trivially contiguous."""
        parent = AsyncTrackingParent(rows)
        view = AsyncRowView(parent, [2])
        await view.set([{"a": 99}])
        assert any(c[0] == "_write_many" for c in parent.calls)

    @pytest.mark.anyio
    async def test_empty_view_set_no_calls(self, rows):
        parent = AsyncTrackingParent(rows)
        view = AsyncRowView(parent, [])
        await view.set([])
        assert len(parent.calls) == 0
