"""Tests for new methods on existing ReadWriteBackend.

Covers: delete_many, set_many, drop_keys, reserve, clear, remove,
and None placeholder support in existing methods.
"""

from __future__ import annotations

from typing import Any

import pytest

from asebytes._backends import ReadWriteBackend


class MemoryWritable(ReadWriteBackend):
    """In-memory ReadWriteBackend for testing default implementations."""

    def __init__(self, data: list[dict[str, Any] | None] | None = None):
        self._data: list[dict[str, Any] | None] = data or []

    def __len__(self) -> int:
        return len(self._data)

    def get(self, index: int, keys: list[str] | None = None) -> dict[str, Any] | None:
        if index < 0 or index >= len(self._data):
            raise IndexError(index)
        row = self._data[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    def set(self, index: int, data: dict[str, Any] | None) -> None:
        if index < len(self._data):
            self._data[index] = data
        elif index == len(self._data):
            self._data.append(data)
        else:
            raise IndexError(index)

    def insert(self, index: int, data: dict[str, Any] | None) -> None:
        self._data.insert(index, data)

    def delete(self, index: int) -> None:
        del self._data[index]

    def extend(self, data: list[dict[str, Any] | None]) -> None:
        self._data.extend(data)

    @staticmethod
    def list_groups(path: str, **kwargs) -> list[str]:
        return []


class TestReadWriteBackendNewMethods:
    """Test the new default methods added to ReadWriteBackend."""

    def test_delete_many(self):
        backend = MemoryWritable(
            [
                {"a": 0},
                {"a": 1},
                {"a": 2},
                {"a": 3},
                {"a": 4},
            ]
        )
        backend.delete_many(1, 4)  # delete indices 1, 2, 3
        assert len(backend) == 2
        assert backend.get(0) == {"a": 0}
        assert backend.get(1) == {"a": 4}

    def test_delete_many_empty_range(self):
        backend = MemoryWritable([{"a": 0}, {"a": 1}])
        backend.delete_many(1, 1)  # empty range
        assert len(backend) == 2

    def test_set_many(self):
        backend = MemoryWritable([{"a": 0}, {"a": 1}, {"a": 2}])
        backend.set_many(1, [{"a": 99}, {"a": 98}])
        assert backend.get(0) == {"a": 0}
        assert backend.get(1) == {"a": 99}
        assert backend.get(2) == {"a": 98}

    def test_set_many_with_none(self):
        backend = MemoryWritable([{"a": 0}, {"a": 1}, {"a": 2}])
        backend.set_many(0, [None, {"a": 99}])
        assert backend.get(0) is None
        assert backend.get(1) == {"a": 99}
        assert backend.get(2) == {"a": 2}

    def test_drop_keys_all_rows(self):
        backend = MemoryWritable(
            [
                {"a": 1, "b": 2, "c": 3},
                {"a": 4, "b": 5, "c": 6},
            ]
        )
        backend.drop_keys(["b", "c"])
        assert backend.get(0) == {"a": 1}
        assert backend.get(1) == {"a": 4}

    def test_drop_keys_specific_indices(self):
        backend = MemoryWritable(
            [
                {"a": 1, "b": 2},
                {"a": 3, "b": 4},
                {"a": 5, "b": 6},
            ]
        )
        backend.drop_keys(["b"], indices=[0, 2])
        assert backend.get(0) == {"a": 1}
        assert backend.get(1) == {"a": 3, "b": 4}
        assert backend.get(2) == {"a": 5}

    def test_drop_keys_skips_none(self):
        backend = MemoryWritable([None, {"a": 1, "b": 2}])
        backend.drop_keys(["b"])
        assert backend.get(0) is None
        assert backend.get(1) == {"a": 1}

    def test_reserve(self):
        backend = MemoryWritable([{"a": 1}])
        backend.reserve(3)
        assert len(backend) == 4
        assert backend.get(0) == {"a": 1}
        for i in range(1, 4):
            assert backend.get(i) is None

    def test_clear(self):
        backend = MemoryWritable([{"a": 1}, {"a": 2}, {"a": 3}])
        backend.clear()
        assert len(backend) == 0

    def test_clear_empty(self):
        backend = MemoryWritable([])
        backend.clear()  # should not raise
        assert len(backend) == 0

    def test_remove_raises_not_implemented(self):
        backend = MemoryWritable([])
        with pytest.raises(NotImplementedError):
            backend.remove()

    def test_update_on_none_placeholder(self):
        backend = MemoryWritable([None])
        backend.update(0, {"a": 1})
        assert backend.get(0) == {"a": 1}


class TestNonePlaceholderSupport:
    """Test that None placeholders work throughout."""

    def test_extend_with_none(self):
        backend = MemoryWritable([])
        backend.extend([{"a": 1}, None, {"a": 3}])
        assert len(backend) == 3
        assert backend.get(1) is None

    def test_insert_none(self):
        backend = MemoryWritable([{"a": 1}])
        backend.insert(0, None)
        assert len(backend) == 2
        assert backend.get(0) is None
        assert backend.get(1) == {"a": 1}

    def test_set_none(self):
        backend = MemoryWritable([{"a": 1}])
        backend.set(0, None)
        assert backend.get(0) is None

    def test_get_many_with_none(self):
        backend = MemoryWritable([{"a": 1}, None, {"a": 3}])
        rows = backend.get_many([0, 1, 2])
        assert rows[0] == {"a": 1}
        assert rows[1] is None
        assert rows[2] == {"a": 3}

    def test_iter_rows_with_none(self):
        backend = MemoryWritable([None, {"a": 1}])
        rows = list(backend.iter_rows([0, 1]))
        assert rows[0] is None
        assert rows[1] == {"a": 1}

    def test_keys_on_none_row(self):
        backend = MemoryWritable([None])
        assert backend.keys(0) == []
