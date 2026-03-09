"""Tests for update_many / set_column ABC defaults on ReadWriteBackend."""

from __future__ import annotations
from typing import Any

import pytest

from asebytes._backends import ReadWriteBackend


class InMemoryBackend(ReadWriteBackend[str, Any]):
    """Minimal concrete backend for testing ABC defaults."""

    def __init__(self, rows: list[dict[str, Any] | None]):
        self._rows = list(rows)

    def __len__(self) -> int:
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

    @staticmethod
    def list_groups(path: str, **kwargs) -> list[str]:
        return []


@pytest.fixture
def backend():
    return InMemoryBackend(
        [
            {"a": 1, "b": 10},
            {"a": 2, "b": 20},
            {"a": 3, "b": 30},
            {"a": 4, "b": 40},
            {"a": 5, "b": 50},
        ]
    )


class TestUpdateMany:
    def test_basic(self, backend):
        backend.update_many(1, [{"a": 20}, {"a": 30}])
        assert backend._rows[0] == {"a": 1, "b": 10}
        assert backend._rows[1] == {"a": 20, "b": 20}
        assert backend._rows[2] == {"a": 30, "b": 30}
        assert backend._rows[3] == {"a": 4, "b": 40}

    def test_empty_data(self, backend):
        backend.update_many(0, [])
        assert backend._rows[0] == {"a": 1, "b": 10}

    def test_single_element(self, backend):
        backend.update_many(2, [{"a": 99}])
        assert backend._rows[2] == {"a": 99, "b": 30}

    def test_adds_new_keys(self, backend):
        backend.update_many(0, [{"c": 100}, {"c": 200}])
        assert backend._rows[0] == {"a": 1, "b": 10, "c": 100}
        assert backend._rows[1] == {"a": 2, "b": 20, "c": 200}

    def test_none_row_becomes_dict(self, backend):
        """update_many on a None placeholder creates a new dict."""
        backend._rows[0] = None
        backend.update_many(0, [{"a": 99}])
        assert backend._rows[0] == {"a": 99}


class TestSetColumn:
    def test_basic(self, backend):
        backend.set_column("a", 1, [20, 30, 40])
        assert backend._rows[0] == {"a": 1, "b": 10}
        assert backend._rows[1] == {"a": 20, "b": 20}
        assert backend._rows[2] == {"a": 30, "b": 30}
        assert backend._rows[3] == {"a": 40, "b": 40}
        assert backend._rows[4] == {"a": 5, "b": 50}

    def test_empty_values(self, backend):
        backend.set_column("a", 0, [])
        assert backend._rows[0] == {"a": 1, "b": 10}

    def test_single_value(self, backend):
        backend.set_column("a", 3, [99])
        assert backend._rows[3] == {"a": 99, "b": 40}

    def test_adds_new_column(self, backend):
        backend.set_column("c", 0, [100, 200, 300, 400, 500])
        assert backend._rows[0]["c"] == 100
        assert backend._rows[4]["c"] == 500

    def test_none_row_becomes_dict(self, backend):
        backend._rows[0] = None
        backend.set_column("a", 0, [99])
        assert backend._rows[0] == {"a": 99}
