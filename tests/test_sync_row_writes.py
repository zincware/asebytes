"""Tests for sync RowView write methods: set(), update(), delete().

- set() accepts list of dicts, rejects list-of-lists with clear error
- update() merges dict into all rows
- delete() removes contiguous rows
"""
from __future__ import annotations

from typing import Any

import pytest

from asebytes._views import RowView


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

    def _delete_row(self, index):
        del self._rows[index]

    def _delete_rows(self, start, stop):
        for i in range(stop - 1, start - 1, -1):
            del self._rows[i]


@pytest.fixture
def parent():
    return MockParent([
        {"a": 1, "b": 10},
        {"a": 2, "b": 20},
        {"a": 3, "b": 30},
        {"a": 4, "b": 40},
        {"a": 5, "b": 50},
    ])


class TestRowViewSet:
    def test_set_overwrites_rows(self, parent):
        view = RowView(parent, list(range(5)))
        view[:3].set([{"a": 10}, {"a": 20}, {"a": 30}])
        assert parent._rows[0] == {"a": 10}
        assert parent._rows[1] == {"a": 20}
        assert parent._rows[2] == {"a": 30}
        assert parent._rows[3] == {"a": 4, "b": 40}  # untouched

    def test_set_rejects_non_list(self, parent):
        view = RowView(parent, list(range(5)))
        with pytest.raises(TypeError):
            view[:3].set(42)

    def test_set_rejects_list_of_lists(self, parent):
        """Row-only writes must be dicts, not lists-of-lists."""
        view = RowView(parent, list(range(5)))
        with pytest.raises(ValueError, match="column-filtered"):
            view[:3].set([[1, 2], [3, 4], [5, 6]])

    def test_set_length_mismatch(self, parent):
        view = RowView(parent, list(range(5)))
        with pytest.raises(ValueError, match="[Ll]ength"):
            view[:3].set([{"a": 1}])


class TestRowViewUpdate:
    def test_update_merges(self, parent):
        view = RowView(parent, list(range(5)))
        view[:3].update({"a": 99})
        assert parent._rows[0]["a"] == 99
        assert parent._rows[0]["b"] == 10  # untouched
        assert parent._rows[2]["a"] == 99
        assert parent._rows[3]["a"] == 4  # untouched

    def test_update_must_be_dict(self, parent):
        view = RowView(parent, list(range(5)))
        with pytest.raises(TypeError):
            view[:3].update([1, 2, 3])


class TestRowViewDelete:
    def test_delete_contiguous(self, parent):
        view = RowView(parent, [1, 2, 3])
        view.delete()
        assert len(parent._rows) == 2
        assert parent._rows[0] == {"a": 1, "b": 10}
        assert parent._rows[1] == {"a": 5, "b": 50}

    def test_delete_non_contiguous_raises(self, parent):
        view = RowView(parent, [0, 2, 4])
        with pytest.raises(TypeError, match="contiguous"):
            view.delete()
