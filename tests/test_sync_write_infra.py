"""Tests for sync write infrastructure (_write_row, _update_row) on IO classes.

Phase 2: ViewParent protocol gains _write_row and _update_row;
ObjectIO and BlobIO implement them.
"""
from __future__ import annotations

from typing import Any

import pytest

from asebytes._backends import ReadWriteBackend
from asebytes._object_io import ObjectIO
from asebytes._blob_io import BlobIO


# ── In-memory object-level backend ──────────────────────────────────────


class MemoryObjectBackend(ReadWriteBackend):
    def __init__(self):
        self._rows: list[dict[str, Any] | None] = []

    def __len__(self):
        return len(self._rows)

    def get(self, index, keys=None):
        row = self._rows[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    def set(self, index, data):
        if index < len(self._rows):
            self._rows[index] = data
        elif index == len(self._rows):
            self._rows.append(data)
        else:
            raise IndexError(index)

    def insert(self, index, data):
        self._rows.insert(index, data)

    def delete(self, index):
        del self._rows[index]

    def extend(self, data):
        self._rows.extend(data)


# ── In-memory blob-level backend ────────────────────────────────────────


class MemoryBlobBackend(ReadWriteBackend):
    def __init__(self):
        self._rows: list[dict[bytes, bytes] | None] = []

    def __len__(self):
        return len(self._rows)

    def get(self, index, keys=None):
        row = self._rows[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    def set(self, index, data):
        if index < len(self._rows):
            self._rows[index] = data
        elif index == len(self._rows):
            self._rows.append(data)
        else:
            raise IndexError(index)

    def insert(self, index, data):
        self._rows.insert(index, data)

    def delete(self, index):
        del self._rows[index]

    def extend(self, data):
        self._rows.extend(data)


# ── ObjectIO write tests ────────────────────────────────────────────────


class TestObjectIOWrite:
    @pytest.fixture
    def io(self):
        b = MemoryObjectBackend()
        b.extend([{"a": 1, "b": 2}, {"a": 3, "b": 4}, {"a": 5, "b": 6}])
        return ObjectIO(b)

    def test_write_row(self, io):
        """_write_row should overwrite the full row."""
        io._write_row(0, {"a": 99, "b": 100})
        assert io[0] == {"a": 99, "b": 100}

    def test_update_row(self, io):
        """_update_row should merge keys into existing row."""
        io._update_row(0, {"a": 99})
        row = io[0]
        assert row["a"] == 99
        assert row["b"] == 2  # untouched


# ── BlobIO write tests ──────────────────────────────────────────────────


class TestBlobIOWrite:
    @pytest.fixture
    def io(self):
        b = MemoryBlobBackend()
        b.extend([
            {b"a": b"1", b"b": b"2"},
            {b"a": b"3", b"b": b"4"},
        ])
        return BlobIO(b)

    def test_write_row(self, io):
        """_write_row should overwrite via str→bytes encoding."""
        io._write_row(0, {b"a": b"99", b"b": b"100"})
        assert io[0] == {b"a": b"99", b"b": b"100"}

    def test_update_row(self, io):
        """_update_row should merge keys."""
        io._update_row(0, {b"a": b"99"})
        row = io[0]
        assert row[b"a"] == b"99"
        assert row[b"b"] == b"2"
