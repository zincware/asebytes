"""Test BlobIO negative index handling."""

from __future__ import annotations

import pytest
from asebytes._backends import ReadWriteBackend
from asebytes._blob_io import BlobIO


class MemoryRW(ReadWriteBackend):
    def __init__(self, data=None):
        self._data = data or []

    def __len__(self):
        return len(self._data)

    def get(self, index, keys=None):
        if index < 0 or index >= len(self._data):
            raise IndexError(index)
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

    @staticmethod
    def list_groups(path: str, **kwargs) -> list[str]:
        return []


class TestBlobIONegativeIndex:
    def test_getitem_negative_one(self):
        io = BlobIO(MemoryRW([{b"a": b"1"}, {b"b": b"2"}, {b"c": b"3"}]))
        assert io[-1] == {b"c": b"3"}

    def test_getitem_negative_two(self):
        io = BlobIO(MemoryRW([{b"a": b"1"}, {b"b": b"2"}, {b"c": b"3"}]))
        assert io[-2] == {b"b": b"2"}

    def test_getitem_negative_out_of_bounds(self):
        io = BlobIO(MemoryRW([{b"a": b"1"}]))
        with pytest.raises(IndexError):
            io[-5]

    def test_getitem_list_negative(self):
        io = BlobIO(MemoryRW([{b"a": b"1"}, {b"b": b"2"}, {b"c": b"3"}]))
        view = io[[-1, -2]]
        assert view.to_list() == [{b"c": b"3"}, {b"b": b"2"}]

    def test_getitem_list_negative_out_of_bounds(self):
        io = BlobIO(MemoryRW([{b"a": b"1"}]))
        with pytest.raises(IndexError):
            io[[-5]]
