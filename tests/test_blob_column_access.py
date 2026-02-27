"""Tests for column access on BlobIO, AsyncBlobIO, AsyncBytesIO.

BlobIO uses bytes keys natively (K=bytes). All column access must use bytes keys.
"""
from __future__ import annotations

from typing import Any

import pytest

from asebytes._backends import ReadWriteBackend
from asebytes._async_backends import SyncToAsyncAdapter
from asebytes._blob_io import BlobIO
from asebytes._async_blob_io import AsyncBlobIO
from asebytes._async_bytesio import AsyncBytesIO
from asebytes._views import ColumnView
from asebytes._async_views import AsyncColumnView


# ── Blob backend ────────────────────────────────────────────────────────


class MemoryBlobBackend(ReadWriteBackend):
    def __init__(self):
        self._rows: list[dict[bytes, bytes] | None] = []

    def __len__(self):
        return len(self._rows)

    def schema(self):
        if not self._rows or self._rows[0] is None:
            return []
        return sorted(self._rows[0].keys())

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

    def get_column(self, key, indices=None):
        if indices is None:
            indices = list(range(len(self)))
        return [self.get(i, [key])[key] for i in indices]


@pytest.fixture
def blob_backend():
    b = MemoryBlobBackend()
    b.extend([
        {b"name": b"alice", b"age": b"30"},
        {b"name": b"bob", b"age": b"25"},
        {b"name": b"carol", b"age": b"35"},
    ])
    return b


# ── BlobIO column access ────────────────────────────────────────────────


class TestBlobIOColumnAccess:
    def test_bytes_key_returns_column_view(self, blob_backend):
        io = BlobIO(blob_backend)
        view = io[b"name"]
        assert isinstance(view, ColumnView)

    def test_list_bytes_returns_column_view(self, blob_backend):
        io = BlobIO(blob_backend)
        view = io[[b"name", b"age"]]
        assert isinstance(view, ColumnView)
        assert not view._single

    def test_bytes_key_to_list(self, blob_backend):
        io = BlobIO(blob_backend)
        result = io[b"name"].to_list()
        assert result == [b"alice", b"bob", b"carol"]

    def test_multi_bytes_key_to_list(self, blob_backend):
        io = BlobIO(blob_backend)
        result = io[[b"name", b"age"]].to_list()
        assert result == [[b"alice", b"30"], [b"bob", b"25"], [b"carol", b"35"]]

    def test_bytes_key_int_index(self, blob_backend):
        io = BlobIO(blob_backend)
        assert io[b"name"][0] == b"alice"

    def test_bytes_key_to_dict(self, blob_backend):
        io = BlobIO(blob_backend)
        result = io[[b"name", b"age"]].to_dict()
        assert result == {
            b"name": [b"alice", b"bob", b"carol"],
            b"age": [b"30", b"25", b"35"],
        }


# ── AsyncBlobIO column access ───────────────────────────────────────────


class TestAsyncBlobIOColumnAccess:
    @pytest.mark.anyio
    async def test_bytes_key_returns_async_column_view(self, blob_backend):
        io = AsyncBlobIO(SyncToAsyncAdapter(blob_backend))
        view = io[b"name"]
        assert isinstance(view, AsyncColumnView)

    @pytest.mark.anyio
    async def test_list_bytes_returns_async_column_view(self, blob_backend):
        io = AsyncBlobIO(SyncToAsyncAdapter(blob_backend))
        view = io[[b"name", b"age"]]
        assert isinstance(view, AsyncColumnView)

    @pytest.mark.anyio
    async def test_bytes_key_to_list(self, blob_backend):
        io = AsyncBlobIO(SyncToAsyncAdapter(blob_backend))
        result = await io[b"name"].to_list()
        assert result == [b"alice", b"bob", b"carol"]

    @pytest.mark.anyio
    async def test_bytes_key_int_index(self, blob_backend):
        io = AsyncBlobIO(SyncToAsyncAdapter(blob_backend))
        result = await io[b"name"][0]
        assert result == b"alice"


# ── AsyncBytesIO column access ──────────────────────────────────────────


class TestAsyncBytesIOColumnAccess:
    @pytest.mark.anyio
    async def test_bytes_key_returns_async_column_view(self, blob_backend):
        io = AsyncBytesIO(SyncToAsyncAdapter(blob_backend))
        view = io[b"name"]
        assert isinstance(view, AsyncColumnView)

    @pytest.mark.anyio
    async def test_list_bytes_returns_async_column_view(self, blob_backend):
        io = AsyncBytesIO(SyncToAsyncAdapter(blob_backend))
        view = io[[b"name", b"age"]]
        assert isinstance(view, AsyncColumnView)

    @pytest.mark.anyio
    async def test_bytes_key_to_list(self, blob_backend):
        io = AsyncBytesIO(SyncToAsyncAdapter(blob_backend))
        result = await io[b"name"].to_list()
        assert result == [b"alice", b"bob", b"carol"]
