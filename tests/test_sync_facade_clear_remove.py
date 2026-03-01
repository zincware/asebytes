"""Tests for clear() and remove() on sync facades."""

from __future__ import annotations

import pytest
from typing import Any
from asebytes._backends import ReadBackend, ReadWriteBackend
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

    @staticmethod
    def list_groups(path: str, **kwargs) -> list[str]:
        return []


class MemoryRO(ReadBackend):
    def __init__(self):
        pass

    def __len__(self):
        return 0

    def get(self, index, keys=None):
        raise IndexError(index)

    @staticmethod
    def list_groups(path: str, **kwargs) -> list[str]:
        return []


class TestBlobIOClearRemove:
    def test_clear(self):
        io = BlobIO(MemoryRW([{b"a": b"1"}, {b"a": b"2"}]))
        io.clear()
        assert len(io) == 0

    def test_clear_readonly_raises(self):
        io = BlobIO(MemoryRO())
        with pytest.raises(TypeError, match="read-only"):
            io.clear()

    def test_remove_raises_not_implemented(self):
        io = BlobIO(MemoryRW([]))
        with pytest.raises(NotImplementedError):
            io.remove()

    def test_remove_readonly_raises(self):
        io = BlobIO(MemoryRO())
        with pytest.raises(TypeError, match="read-only"):
            io.remove()


class TestObjectIOClearRemove:
    def test_clear(self):
        io = ObjectIO(MemoryRW([{"a": 1}, {"a": 2}]))
        io.clear()
        assert len(io) == 0

    def test_clear_readonly_raises(self):
        io = ObjectIO(MemoryRO())
        with pytest.raises(TypeError, match="read-only"):
            io.clear()

    def test_remove_raises_not_implemented(self):
        io = ObjectIO(MemoryRW([]))
        with pytest.raises(NotImplementedError):
            io.remove()
