"""Tests for RowView.drop() on sync facades."""
from __future__ import annotations
import pytest
from asebytes._backends import ReadWriteBackend
from asebytes._blob_io import BlobIO
from asebytes._object_io import ObjectIO


class MemoryRW(ReadWriteBackend):
    def __init__(self, data=None):
        self._data = data or []
    def __len__(self):
        return len(self._data)
    def get(self, index, keys=None):
        row = self._data[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)
    def set(self, index, value):
        if index < len(self._data):
            self._data[index] = value
        elif index == len(self._data):
            self._data.append(value)
        else:
            raise IndexError(index)
    def delete(self, index):
        del self._data[index]
    def extend(self, values):
        self._data.extend(values)
    def insert(self, index, value):
        self._data.insert(index, value)


class TestObjectIORowViewDrop:
    def test_drop_on_slice(self):
        io = ObjectIO(MemoryRW([
            {"a": 1, "b": 2, "c": 3},
            {"a": 4, "b": 5, "c": 6},
            {"a": 7, "b": 8, "c": 9},
        ]))
        view = io[0:2]
        view.drop(["b", "c"])
        assert io.get(0) == {"a": 1}
        assert io.get(1) == {"a": 4}
        assert io.get(2) == {"a": 7, "b": 8, "c": 9}

    def test_drop_on_list_indices(self):
        io = ObjectIO(MemoryRW([
            {"a": 1, "b": 2},
            {"a": 3, "b": 4},
            {"a": 5, "b": 6},
        ]))
        view = io[[0, 2]]
        view.drop(["b"])
        assert io.get(0) == {"a": 1}
        assert io.get(1) == {"a": 3, "b": 4}
        assert io.get(2) == {"a": 5}


class TestBlobIORowViewDrop:
    def test_drop_on_slice(self):
        io = BlobIO(MemoryRW([
            {b"a": b"1", b"b": b"2"},
            {b"a": b"3", b"b": b"4"},
        ]))
        view = io[0:2]
        view.drop([b"b"])
        assert io.get(0) == {b"a": b"1"}
        assert io.get(1) == {b"a": b"3"}
