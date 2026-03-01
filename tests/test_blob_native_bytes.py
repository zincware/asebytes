"""Tests for BlobIO, AsyncBlobIO native bytes key passthrough.

After the generic K refactor, blob IO classes must pass bytes keys directly
to the backend WITHOUT encoding/decoding. Views accept bytes keys natively.

These tests verify the encoding bridge is fully removed.
"""

from __future__ import annotations

from typing import Any

import pytest

from asebytes._views import ColumnView, RowView


# ── Sync BlobIO ────────────────────────────────────────────────────────────


class TestBlobIONativeBytes:
    """BlobIO._read_row/column/rows pass bytes keys directly to backend."""

    def test_column_view_from_bytes_key(self, tmp_path):
        """blobdb[b"key"] returns ColumnView (no decode)."""
        from asebytes._blob_io import BlobIO
        from asebytes._backends import ReadWriteBackend

        class MemBlob(ReadWriteBackend):
            def __init__(self):
                self._rows = [
                    {b"name": b"alice", b"age": b"30"},
                    {b"name": b"bob", b"age": b"25"},
                ]

            def __len__(self):
                return len(self._rows)

            def get(self, index, keys=None):
                row = self._rows[index]
                if keys is not None:
                    return {k: row[k] for k in keys if k in row}
                return dict(row)

            def get_many(self, indices, keys=None):
                return [self.get(i, keys) for i in indices]

            def iter_rows(self, indices, keys=None):
                for i in indices:
                    yield self.get(i, keys)

            def get_column(self, key, indices):
                return [self._rows[i][key] for i in indices]

            def set(self, index, data):
                self._rows[index] = data

            def update(self, index, data):
                self._rows[index].update(data)

            def delete(self, index):
                del self._rows[index]

            def delete_many(self, start, stop):
                del self._rows[start:stop]

            def extend(self, data):
                self._rows.extend(data)

            def insert(self, index, data):
                self._rows.insert(index, data)

            @staticmethod
            def list_groups(path: str, **kwargs) -> list[str]:
                return []

        backend = MemBlob()
        db = BlobIO(backend)

        # bytes key → ColumnView
        cv = db[b"name"]
        assert isinstance(cv, ColumnView)

        # Column values should be bytes (not re-keyed str)
        result = cv.to_list()
        assert result == [b"alice", b"bob"]

    def test_column_view_int_index(self, tmp_path):
        """blobdb[b"name"][0] returns single bytes value."""
        from asebytes._blob_io import BlobIO
        from asebytes._backends import ReadWriteBackend

        class MemBlob(ReadWriteBackend):
            def __init__(self):
                self._rows = [{b"name": b"alice"}, {b"name": b"bob"}]

            def __len__(self):
                return len(self._rows)

            def get(self, index, keys=None):
                row = self._rows[index]
                if keys is not None:
                    return {k: row[k] for k in keys if k in row}
                return dict(row)

            def get_many(self, indices, keys=None):
                return [self.get(i, keys) for i in indices]

            def iter_rows(self, indices, keys=None):
                for i in indices:
                    yield self.get(i, keys)

            def get_column(self, key, indices):
                return [self._rows[i][key] for i in indices]

            def set(self, index, data):
                self._rows[index] = data

            def update(self, index, data):
                self._rows[index].update(data)

            def delete(self, index):
                del self._rows[index]

            def delete_many(self, start, stop):
                del self._rows[start:stop]

            def extend(self, data):
                self._rows.extend(data)

            def insert(self, index, data):
                self._rows.insert(index, data)

            @staticmethod
            def list_groups(path: str, **kwargs) -> list[str]:
                return []

        db = BlobIO(MemBlob())
        assert db[b"name"][0] == b"alice"

    def test_slice_then_bytes_key(self):
        """blobdb[0:2][b"name"] returns ColumnView with bytes values."""
        from asebytes._blob_io import BlobIO
        from asebytes._backends import ReadWriteBackend

        class MemBlob(ReadWriteBackend):
            def __init__(self):
                self._rows = [
                    {b"x": b"1"},
                    {b"x": b"2"},
                    {b"x": b"3"},
                ]

            def __len__(self):
                return len(self._rows)

            def get(self, index, keys=None):
                row = self._rows[index]
                if keys is not None:
                    return {k: row[k] for k in keys if k in row}
                return dict(row)

            def get_many(self, indices, keys=None):
                return [self.get(i, keys) for i in indices]

            def iter_rows(self, indices, keys=None):
                for i in indices:
                    yield self.get(i, keys)

            def get_column(self, key, indices):
                return [self._rows[i][key] for i in indices]

            def set(self, index, data):
                self._rows[index] = data

            def update(self, index, data):
                self._rows[index].update(data)

            def delete(self, index):
                del self._rows[index]

            def delete_many(self, start, stop):
                del self._rows[start:stop]

            def extend(self, data):
                self._rows.extend(data)

            def insert(self, index, data):
                self._rows.insert(index, data)

            @staticmethod
            def list_groups(path: str, **kwargs) -> list[str]:
                return []

        db = BlobIO(MemBlob())
        rv = db[0:2]
        assert isinstance(rv, RowView)
        cv = rv[b"x"]
        assert isinstance(cv, ColumnView)
        assert cv.to_list() == [b"1", b"2"]

    def test_list_bytes_keys(self):
        """blobdb[[b"name", b"age"]] returns multi-column ColumnView."""
        from asebytes._blob_io import BlobIO
        from asebytes._backends import ReadWriteBackend

        class MemBlob(ReadWriteBackend):
            def __init__(self):
                self._rows = [
                    {b"name": b"alice", b"age": b"30"},
                ]

            def __len__(self):
                return len(self._rows)

            def get(self, index, keys=None):
                row = self._rows[index]
                if keys is not None:
                    return {k: row[k] for k in keys if k in row}
                return dict(row)

            def get_many(self, indices, keys=None):
                return [self.get(i, keys) for i in indices]

            def iter_rows(self, indices, keys=None):
                for i in indices:
                    yield self.get(i, keys)

            def get_column(self, key, indices):
                return [self._rows[i][key] for i in indices]

            def set(self, index, data):
                self._rows[index] = data

            def update(self, index, data):
                self._rows[index].update(data)

            def delete(self, index):
                del self._rows[index]

            def delete_many(self, start, stop):
                del self._rows[start:stop]

            def extend(self, data):
                self._rows.extend(data)

            def insert(self, index, data):
                self._rows.insert(index, data)

            @staticmethod
            def list_groups(path: str, **kwargs) -> list[str]:
                return []

        db = BlobIO(MemBlob())
        result = db[[b"name", b"age"]].to_dict()
        assert result == {
            b"name": [b"alice"],
            b"age": [b"30"],
        }


# ── Async BlobIO ─────────────────────────────────────────────────────────


class AsyncMemBlob:
    """Minimal async blob backend for testing native bytes passthrough."""

    def __init__(self, rows: list[dict[bytes, bytes]]):
        self._rows = rows

    async def len(self):
        return len(self._rows)

    async def get(self, index, keys=None):
        row = self._rows[index]
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    async def get_many(self, indices, keys=None):
        return [await self.get(i, keys) for i in indices]

    async def get_column(self, key, indices):
        return [self._rows[i][key] for i in indices]

    async def set(self, index, data):
        self._rows[index] = data

    async def update(self, index, data):
        self._rows[index].update(data)

    async def delete(self, index):
        del self._rows[index]

    async def delete_many(self, start, stop):
        del self._rows[start:stop]

    async def extend(self, data):
        self._rows.extend(data)

    async def insert(self, index, data):
        self._rows.insert(index, data)

    async def drop_keys(self, keys, indices=None):
        pass

    async def keys(self, index):
        return list(self._rows[index].keys())

    async def clear(self):
        self._rows.clear()

    async def remove(self):
        pass

    async def reserve(self, count):
        pass


class TestAsyncBlobIONativeBytes:
    """AsyncBlobIO must pass bytes keys directly, no encode/decode."""

    @pytest.mark.anyio
    async def test_column_view_from_bytes_key(self):
        """ablobdb[b"name"] returns column values as bytes."""
        from asebytes._async_blob_io import AsyncBlobIO

        backend = AsyncMemBlob(
            [
                {b"name": b"alice", b"age": b"30"},
                {b"name": b"bob", b"age": b"25"},
            ]
        )
        db = AsyncBlobIO(backend)
        result = await db[b"name"].to_list()
        assert result == [b"alice", b"bob"]

    @pytest.mark.anyio
    async def test_column_view_int_index(self):
        """ablobdb[b"name"][0] returns single bytes value."""
        from asebytes._async_blob_io import AsyncBlobIO

        db = AsyncBlobIO(AsyncMemBlob([{b"name": b"alice"}]))
        result = await db[b"name"][0]
        assert result == b"alice"

    @pytest.mark.anyio
    async def test_slice_then_bytes_key(self):
        """ablobdb[0:2][b"name"] returns ColumnView with bytes values."""
        from asebytes._async_blob_io import AsyncBlobIO

        db = AsyncBlobIO(
            AsyncMemBlob(
                [
                    {b"x": b"1"},
                    {b"x": b"2"},
                    {b"x": b"3"},
                ]
            )
        )
        result = await db[0:2][b"x"].to_list()
        assert result == [b"1", b"2"]

    @pytest.mark.anyio
    async def test_single_row_bytes_key(self):
        """await ablobdb[0][b"name"] returns bytes value."""
        from asebytes._async_blob_io import AsyncBlobIO

        db = AsyncBlobIO(AsyncMemBlob([{b"name": b"alice"}]))
        result = await db[0][b"name"]
        assert result == b"alice"

    @pytest.mark.anyio
    async def test_list_bytes_keys(self):
        """ablobdb[[b"name", b"age"]] returns multi-column ColumnView."""
        from asebytes._async_blob_io import AsyncBlobIO

        db = AsyncBlobIO(
            AsyncMemBlob(
                [
                    {b"name": b"alice", b"age": b"30"},
                ]
            )
        )
        result = await db[[b"name", b"age"]].to_dict()
        assert result == {
            b"name": [b"alice"],
            b"age": [b"30"],
        }


class TestAsyncBlobIONativeBytesAlternate:
    """AsyncBlobIO must pass bytes keys directly, no encode/decode (alternate tests)."""

    @pytest.mark.anyio
    async def test_column_view_from_bytes_key(self):
        """ablobdb[b"name"] returns column values as bytes."""
        from asebytes._async_blob_io import AsyncBlobIO

        backend = AsyncMemBlob(
            [
                {b"name": b"alice", b"age": b"30"},
                {b"name": b"bob", b"age": b"25"},
            ]
        )
        db = AsyncBlobIO(backend)
        result = await db[b"name"].to_list()
        assert result == [b"alice", b"bob"]

    @pytest.mark.anyio
    async def test_column_view_int_index(self):
        """ablobdb[b"name"][0] returns single bytes value."""
        from asebytes._async_blob_io import AsyncBlobIO

        db = AsyncBlobIO(AsyncMemBlob([{b"name": b"alice"}]))
        result = await db[b"name"][0]
        assert result == b"alice"

    @pytest.mark.anyio
    async def test_single_row_bytes_key(self):
        """await ablobdb[0][b"name"] returns bytes value."""
        from asebytes._async_blob_io import AsyncBlobIO

        db = AsyncBlobIO(AsyncMemBlob([{b"name": b"alice"}]))
        result = await db[0][b"name"]
        assert result == b"alice"

    @pytest.mark.anyio
    async def test_list_bytes_keys(self):
        """ablobdb[[b"name", b"age"]] returns multi-column ColumnView."""
        from asebytes._async_blob_io import AsyncBlobIO

        db = AsyncBlobIO(
            AsyncMemBlob(
                [
                    {b"name": b"alice", b"age": b"30"},
                ]
            )
        )
        result = await db[[b"name", b"age"]].to_dict()
        assert result == {
            b"name": [b"alice"],
            b"age": [b"30"],
        }
