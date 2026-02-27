"""Tests for RawReadableBackend / RawWritableBackend ABCs.

These are bytes-level protocols (dict[bytes, bytes] | None) that
BytesIO and AsyncBytesIO delegate to. Currently no ABC exists for this
level — BytesIO is LMDB-concrete.
"""

from __future__ import annotations

from typing import Iterator

import pytest

from asebytes._protocols import RawReadableBackend, RawWritableBackend


# ── Minimal in-memory implementations for testing defaults ──────────────


class MemoryRawReadable(RawReadableBackend):
    """In-memory implementation of the read-only bytes-level protocol."""

    def __init__(self, data: list[dict[bytes, bytes] | None] | None = None):
        self._data: list[dict[bytes, bytes] | None] = data or []

    def __len__(self) -> int:
        return len(self._data)

    def get_schema(self) -> list[bytes]:
        keys: set[bytes] = set()
        for row in self._data:
            if row is not None:
                keys.update(row.keys())
        return sorted(keys)

    def read_row(
        self, index: int, keys: list[bytes] | None = None
    ) -> dict[bytes, bytes] | None:
        if index < 0 or index >= len(self._data):
            raise IndexError(index)
        row = self._data[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)


class MemoryRawWritable(MemoryRawReadable, RawWritableBackend):
    """In-memory implementation of the read-write bytes-level protocol."""

    def write_row(self, index: int, data: dict[bytes, bytes] | None) -> None:
        if index < len(self._data):
            self._data[index] = data
        elif index == len(self._data):
            self._data.append(data)
        else:
            raise IndexError(index)

    def insert_row(self, index: int, data: dict[bytes, bytes] | None) -> None:
        self._data.insert(index, data)

    def delete_row(self, index: int) -> None:
        del self._data[index]

    def append_rows(self, data: list[dict[bytes, bytes] | None]) -> None:
        self._data.extend(data)


# ── Tests: cannot instantiate abstract classes ──────────────────────────


class TestAbstractInstantiation:
    def test_cannot_instantiate_raw_readable(self):
        with pytest.raises(TypeError):
            RawReadableBackend()

    def test_cannot_instantiate_raw_writable(self):
        with pytest.raises(TypeError):
            RawWritableBackend()


# ── Tests: RawReadableBackend ───────────────────────────────────────────


class TestRawReadable:
    def test_len(self):
        backend = MemoryRawReadable([{b"a": b"1"}, {b"b": b"2"}])
        assert len(backend) == 2

    def test_len_empty(self):
        backend = MemoryRawReadable([])
        assert len(backend) == 0

    def test_get_schema(self):
        backend = MemoryRawReadable([
            {b"a": b"1", b"b": b"2"},
            {b"b": b"3", b"c": b"4"},
        ])
        assert backend.get_schema() == [b"a", b"b", b"c"]

    def test_get_schema_skips_none_placeholders(self):
        backend = MemoryRawReadable([{b"a": b"1"}, None, {b"b": b"2"}])
        assert backend.get_schema() == [b"a", b"b"]

    def test_read_row(self):
        backend = MemoryRawReadable([{b"a": b"1", b"b": b"2"}])
        assert backend.read_row(0) == {b"a": b"1", b"b": b"2"}

    def test_read_row_with_keys(self):
        backend = MemoryRawReadable([{b"a": b"1", b"b": b"2"}])
        assert backend.read_row(0, keys=[b"a"]) == {b"a": b"1"}

    def test_read_row_none_placeholder(self):
        backend = MemoryRawReadable([None])
        assert backend.read_row(0) is None

    def test_read_row_out_of_bounds(self):
        backend = MemoryRawReadable([{b"a": b"1"}])
        with pytest.raises(IndexError):
            backend.read_row(5)

    # -- Default implementations --

    def test_get_available_keys(self):
        backend = MemoryRawReadable([{b"a": b"1", b"b": b"2"}])
        assert sorted(backend.get_available_keys(0)) == [b"a", b"b"]

    def test_get_available_keys_none_placeholder(self):
        backend = MemoryRawReadable([None])
        assert backend.get_available_keys(0) == []

    def test_read_rows_default(self):
        backend = MemoryRawReadable([{b"a": b"1"}, {b"a": b"2"}, {b"a": b"3"}])
        rows = backend.read_rows([0, 2])
        assert rows == [{b"a": b"1"}, {b"a": b"3"}]

    def test_read_rows_with_none(self):
        backend = MemoryRawReadable([{b"a": b"1"}, None, {b"a": b"3"}])
        rows = backend.read_rows([0, 1, 2])
        assert rows == [{b"a": b"1"}, None, {b"a": b"3"}]

    def test_iter_rows_default(self):
        backend = MemoryRawReadable([{b"a": b"1"}, {b"a": b"2"}])
        result = list(backend.iter_rows([0, 1]))
        assert result == [{b"a": b"1"}, {b"a": b"2"}]

    def test_iter_rows_is_iterator(self):
        backend = MemoryRawReadable([{b"a": b"1"}])
        it = backend.iter_rows([0])
        assert hasattr(it, "__next__")


# ── Tests: RawWritableBackend ───────────────────────────────────────────


class TestRawWritable:
    def test_write_row(self):
        backend = MemoryRawWritable([{b"a": b"1"}])
        backend.write_row(0, {b"a": b"99"})
        assert backend.read_row(0) == {b"a": b"99"}

    def test_write_row_none(self):
        backend = MemoryRawWritable([{b"a": b"1"}])
        backend.write_row(0, None)
        assert backend.read_row(0) is None

    def test_insert_row(self):
        backend = MemoryRawWritable([{b"a": b"1"}, {b"a": b"3"}])
        backend.insert_row(1, {b"a": b"2"})
        assert len(backend) == 3
        assert backend.read_row(1) == {b"a": b"2"}

    def test_insert_row_none(self):
        backend = MemoryRawWritable([{b"a": b"1"}])
        backend.insert_row(0, None)
        assert len(backend) == 2
        assert backend.read_row(0) is None
        assert backend.read_row(1) == {b"a": b"1"}

    def test_delete_row(self):
        backend = MemoryRawWritable([{b"a": b"1"}, {b"a": b"2"}])
        backend.delete_row(0)
        assert len(backend) == 1
        assert backend.read_row(0) == {b"a": b"2"}

    def test_append_rows(self):
        backend = MemoryRawWritable([])
        backend.append_rows([{b"a": b"1"}, {b"a": b"2"}])
        assert len(backend) == 2

    def test_append_rows_with_none(self):
        backend = MemoryRawWritable([])
        backend.append_rows([{b"a": b"1"}, None, {b"a": b"3"}])
        assert len(backend) == 3
        assert backend.read_row(1) is None

    # -- Default implementations of new methods --

    def test_update_row_default(self):
        """Default update_row does read-modify-write."""
        backend = MemoryRawWritable([{b"a": b"1", b"b": b"2"}])
        backend.update_row(0, {b"a": b"99"})
        assert backend.read_row(0) == {b"a": b"99", b"b": b"2"}

    def test_update_row_on_none_placeholder(self):
        """Updating a None placeholder should create a row with the given keys."""
        backend = MemoryRawWritable([None])
        backend.update_row(0, {b"a": b"1"})
        assert backend.read_row(0) == {b"a": b"1"}

    def test_delete_rows_default(self):
        """Default delete_rows deletes contiguous range [start, stop)."""
        backend = MemoryRawWritable([
            {b"a": b"0"}, {b"a": b"1"}, {b"a": b"2"},
            {b"a": b"3"}, {b"a": b"4"},
        ])
        backend.delete_rows(1, 4)  # delete indices 1, 2, 3
        assert len(backend) == 2
        assert backend.read_row(0) == {b"a": b"0"}
        assert backend.read_row(1) == {b"a": b"4"}

    def test_write_rows_default(self):
        """Default write_rows overwrites contiguous range."""
        backend = MemoryRawWritable([{b"a": b"0"}, {b"a": b"1"}, {b"a": b"2"}])
        backend.write_rows(1, [{b"a": b"99"}, {b"a": b"98"}])
        assert backend.read_row(0) == {b"a": b"0"}
        assert backend.read_row(1) == {b"a": b"99"}
        assert backend.read_row(2) == {b"a": b"98"}

    def test_drop_keys_default(self):
        """Default drop_keys removes specific keys from all rows."""
        backend = MemoryRawWritable([
            {b"a": b"1", b"b": b"2", b"c": b"3"},
            {b"a": b"4", b"b": b"5", b"c": b"6"},
        ])
        backend.drop_keys([b"b", b"c"])
        assert backend.read_row(0) == {b"a": b"1"}
        assert backend.read_row(1) == {b"a": b"4"}

    def test_drop_keys_with_indices(self):
        """drop_keys with indices only affects specified rows."""
        backend = MemoryRawWritable([
            {b"a": b"1", b"b": b"2"},
            {b"a": b"3", b"b": b"4"},
            {b"a": b"5", b"b": b"6"},
        ])
        backend.drop_keys([b"b"], indices=[0, 2])
        assert backend.read_row(0) == {b"a": b"1"}
        assert backend.read_row(1) == {b"a": b"3", b"b": b"4"}  # untouched
        assert backend.read_row(2) == {b"a": b"5"}

    def test_drop_keys_skips_none_placeholders(self):
        backend = MemoryRawWritable([None, {b"a": b"1", b"b": b"2"}])
        backend.drop_keys([b"b"])  # should not crash on None row
        assert backend.read_row(0) is None
        assert backend.read_row(1) == {b"a": b"1"}

    def test_reserve_default(self):
        """Default reserve appends None placeholders."""
        backend = MemoryRawWritable([{b"a": b"1"}])
        backend.reserve(3)
        assert len(backend) == 4
        assert backend.read_row(0) == {b"a": b"1"}
        assert backend.read_row(1) is None
        assert backend.read_row(2) is None
        assert backend.read_row(3) is None

    def test_clear_default(self):
        """Default clear removes all rows."""
        backend = MemoryRawWritable([{b"a": b"1"}, {b"a": b"2"}])
        backend.clear()
        assert len(backend) == 0

    def test_remove_raises_not_implemented(self):
        """Default remove() raises NotImplementedError."""
        backend = MemoryRawWritable([])
        with pytest.raises(NotImplementedError):
            backend.remove()
