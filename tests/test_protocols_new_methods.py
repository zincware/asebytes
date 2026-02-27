"""Tests for new methods on existing WritableBackend.

Covers: delete_rows, write_rows, drop_keys, reserve, clear, remove,
and None placeholder support in existing methods.
"""

from __future__ import annotations

from typing import Any

import pytest

from asebytes._protocols import WritableBackend


class MemoryWritable(WritableBackend):
    """In-memory WritableBackend for testing default implementations."""

    def __init__(self, data: list[dict[str, Any] | None] | None = None):
        self._data: list[dict[str, Any] | None] = data or []

    def __len__(self) -> int:
        return len(self._data)

    def columns(self, index: int = 0) -> list[str]:
        if not self._data:
            return []
        row = self._data[index]
        return sorted(row.keys()) if row is not None else []

    def read_row(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any] | None:
        if index < 0 or index >= len(self._data):
            raise IndexError(index)
        row = self._data[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    def write_row(self, index: int, data: dict[str, Any] | None) -> None:
        if index < len(self._data):
            self._data[index] = data
        elif index == len(self._data):
            self._data.append(data)
        else:
            raise IndexError(index)

    def insert_row(self, index: int, data: dict[str, Any] | None) -> None:
        self._data.insert(index, data)

    def delete_row(self, index: int) -> None:
        del self._data[index]

    def append_rows(self, data: list[dict[str, Any] | None]) -> None:
        self._data.extend(data)


class TestWritableBackendNewMethods:
    """Test the new default methods added to WritableBackend."""

    def test_delete_rows(self):
        backend = MemoryWritable([
            {"a": 0}, {"a": 1}, {"a": 2}, {"a": 3}, {"a": 4},
        ])
        backend.delete_rows(1, 4)  # delete indices 1, 2, 3
        assert len(backend) == 2
        assert backend.read_row(0) == {"a": 0}
        assert backend.read_row(1) == {"a": 4}

    def test_delete_rows_empty_range(self):
        backend = MemoryWritable([{"a": 0}, {"a": 1}])
        backend.delete_rows(1, 1)  # empty range
        assert len(backend) == 2

    def test_write_rows(self):
        backend = MemoryWritable([{"a": 0}, {"a": 1}, {"a": 2}])
        backend.write_rows(1, [{"a": 99}, {"a": 98}])
        assert backend.read_row(0) == {"a": 0}
        assert backend.read_row(1) == {"a": 99}
        assert backend.read_row(2) == {"a": 98}

    def test_write_rows_with_none(self):
        backend = MemoryWritable([{"a": 0}, {"a": 1}, {"a": 2}])
        backend.write_rows(0, [None, {"a": 99}])
        assert backend.read_row(0) is None
        assert backend.read_row(1) == {"a": 99}
        assert backend.read_row(2) == {"a": 2}

    def test_drop_keys_all_rows(self):
        backend = MemoryWritable([
            {"a": 1, "b": 2, "c": 3},
            {"a": 4, "b": 5, "c": 6},
        ])
        backend.drop_keys(["b", "c"])
        assert backend.read_row(0) == {"a": 1}
        assert backend.read_row(1) == {"a": 4}

    def test_drop_keys_specific_indices(self):
        backend = MemoryWritable([
            {"a": 1, "b": 2},
            {"a": 3, "b": 4},
            {"a": 5, "b": 6},
        ])
        backend.drop_keys(["b"], indices=[0, 2])
        assert backend.read_row(0) == {"a": 1}
        assert backend.read_row(1) == {"a": 3, "b": 4}
        assert backend.read_row(2) == {"a": 5}

    def test_drop_keys_skips_none(self):
        backend = MemoryWritable([None, {"a": 1, "b": 2}])
        backend.drop_keys(["b"])
        assert backend.read_row(0) is None
        assert backend.read_row(1) == {"a": 1}

    def test_reserve(self):
        backend = MemoryWritable([{"a": 1}])
        backend.reserve(3)
        assert len(backend) == 4
        assert backend.read_row(0) == {"a": 1}
        for i in range(1, 4):
            assert backend.read_row(i) is None

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

    def test_update_row_on_none_placeholder(self):
        backend = MemoryWritable([None])
        backend.update_row(0, {"a": 1})
        assert backend.read_row(0) == {"a": 1}


class TestNonePlaceholderSupport:
    """Test that None placeholders work throughout."""

    def test_append_rows_with_none(self):
        backend = MemoryWritable([])
        backend.append_rows([{"a": 1}, None, {"a": 3}])
        assert len(backend) == 3
        assert backend.read_row(1) is None

    def test_insert_none(self):
        backend = MemoryWritable([{"a": 1}])
        backend.insert_row(0, None)
        assert len(backend) == 2
        assert backend.read_row(0) is None
        assert backend.read_row(1) == {"a": 1}

    def test_write_none(self):
        backend = MemoryWritable([{"a": 1}])
        backend.write_row(0, None)
        assert backend.read_row(0) is None

    def test_read_rows_with_none(self):
        backend = MemoryWritable([{"a": 1}, None, {"a": 3}])
        rows = backend.read_rows([0, 1, 2])
        assert rows[0] == {"a": 1}
        assert rows[1] is None
        assert rows[2] == {"a": 3}

    def test_iter_rows_with_none(self):
        backend = MemoryWritable([None, {"a": 1}])
        rows = list(backend.iter_rows([0, 1]))
        assert rows[0] is None
        assert rows[1] == {"a": 1}

    def test_columns_on_none_row(self):
        backend = MemoryWritable([None])
        assert backend.columns(0) == []
