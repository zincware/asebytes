"""Tests for column access dimensionality matrix.

Rules:
- db["a"][i]     → scalar (single value)
- db["a"][:n]    → 1D list of values
- db[["a","b"]][i] → 1D list [val_a, val_b]  (NOT dict)
- db[["a","b"]][:n] → 2D list[[val_a,val_b], ...]  (NOT list[dict])

Sync and async variants.
"""
from __future__ import annotations

from typing import Any

import pytest

from asebytes._views import ColumnView


# ── Mock parent ─────────────────────────────────────────────────────────


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


@pytest.fixture
def parent():
    return MockParent([
        {"a": 1, "b": 10, "c": 100},
        {"a": 2, "b": 20, "c": 200},
        {"a": 3, "b": 30, "c": 300},
        {"a": 4, "b": 40, "c": 400},
        {"a": 5, "b": 50, "c": 500},
    ])


# ── Scalar/Scalar: db["a"][0] → scalar ─────────────────────────────────


class TestScalarScalar:
    def test_single_key_int_returns_scalar(self, parent):
        view = ColumnView(parent, "a", range(5))
        assert view[0] == 1

    def test_single_key_int_returns_scalar_not_list(self, parent):
        view = ColumnView(parent, "a", range(5))
        result = view[0]
        assert not isinstance(result, (list, dict))


# ── Vector/Scalar: db["a"][:n] → 1D list ───────────────────────────────


class TestVectorScalar:
    def test_single_key_slice_returns_1d_list(self, parent):
        view = ColumnView(parent, "a", range(5))
        result = view[:3].to_list()
        assert result == [1, 2, 3]

    def test_single_key_iter_yields_scalars(self, parent):
        view = ColumnView(parent, "a", range(5))
        result = list(view[:3])
        assert result == [1, 2, 3]


# ── Scalar/Vector: db[["a","b"]][0] → 1D list (NOT dict) ───────────────


class TestScalarVector:
    def test_multi_key_int_returns_list(self, parent):
        """Multi-key + int selector → flat list of values, NOT a dict."""
        view = ColumnView(parent, ["a", "b"], range(5))
        result = view[0]
        assert isinstance(result, list)
        assert result == [1, 10]

    def test_multi_key_int_not_dict(self, parent):
        view = ColumnView(parent, ["a", "b"], range(5))
        result = view[0]
        assert not isinstance(result, dict)

    def test_multi_key_int_order_matches_keys(self, parent):
        """Values should be in the same order as the keys."""
        view = ColumnView(parent, ["b", "a"], range(5))
        result = view[0]
        assert result == [10, 1]  # b first, then a


# ── Matrix: db[["a","b"]][:n] → 2D list ────────────────────────────────


class TestMatrix:
    def test_multi_key_slice_to_list_returns_2d(self, parent):
        """Multi-key + slice → list of lists."""
        view = ColumnView(parent, ["a", "b"], range(5))
        result = view[:3].to_list()
        assert result == [[1, 10], [2, 20], [3, 30]]

    def test_multi_key_iter_yields_lists(self, parent):
        """Multi-key iteration yields lists, not dicts."""
        view = ColumnView(parent, ["a", "b"], range(5))
        result = list(view[:3])
        assert all(isinstance(r, list) for r in result)
        assert result[0] == [1, 10]

    def test_multi_key_to_list_not_dicts(self, parent):
        view = ColumnView(parent, ["a", "b"], range(5))
        result = view[:3].to_list()
        assert not any(isinstance(r, dict) for r in result)


# ── to_dict() is unchanged ──────────────────────────────────────────────


class TestToDictUnchanged:
    def test_to_dict_single_key(self, parent):
        view = ColumnView(parent, "a", range(5))
        d = view.to_dict()
        assert d == {"a": [1, 2, 3, 4, 5]}

    def test_to_dict_multi_key(self, parent):
        view = ColumnView(parent, ["a", "b"], range(3))
        d = view.to_dict()
        assert d == {"a": [1, 2, 3], "b": [10, 20, 30]}
