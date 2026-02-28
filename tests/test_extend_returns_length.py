"""Tests that extend() returns the new length across all backend layers."""

import pytest

from asebytes import BlobIO, ObjectIO, ASEIO
from asebytes._backends import ReadWriteBackend
from asebytes.lmdb import LMDBBlobBackend, LMDBObjectBackend


class TestExtendReturnsLength:
    """extend() should return the new total length (int)."""

    def test_blob_backend_extend(self, tmp_path):
        backend = LMDBBlobBackend(str(tmp_path / "test.lmdb"))
        result = backend.extend([{b"k": b"v1"}, {b"k": b"v2"}])
        assert result == 2
        result2 = backend.extend([{b"k": b"v3"}])
        assert result2 == 3

    def test_object_backend_extend(self, tmp_path):
        backend = LMDBObjectBackend(str(tmp_path / "test.lmdb"))
        result = backend.extend([{"a": 1}, {"a": 2}])
        assert result == 2
        result2 = backend.extend([{"a": 3}])
        assert result2 == 3

    def test_blobio_extend(self, tmp_path):
        db = BlobIO(str(tmp_path / "test.lmdb"))
        result = db.extend([{b"k": b"v1"}, {b"k": b"v2"}])
        assert result == 2

    def test_objectio_extend(self, tmp_path):
        db = ObjectIO(str(tmp_path / "test.lmdb"))
        result = db.extend([{"a": 1}])
        assert result == 1

    def test_aseio_extend(self, tmp_path, ethanol):
        db = ASEIO(str(tmp_path / "test.lmdb"))
        result = db.extend(ethanol[:3])
        assert result == 3
        result2 = db.extend(ethanol[3:5])
        assert result2 == 5

    def test_extend_empty_list(self, tmp_path):
        backend = LMDBBlobBackend(str(tmp_path / "test.lmdb"))
        backend.extend([{b"k": b"v1"}])
        result = backend.extend([])
        assert result == 1  # unchanged length


@pytest.mark.anyio
class TestAsyncExtendReturnsLength:
    """Async extend() should also return new length."""

    async def test_async_blobio_extend(self, tmp_path):
        from asebytes import AsyncBlobIO
        db = AsyncBlobIO(str(tmp_path / "test.lmdb"))
        result = await db.extend([{b"k": b"v1"}, {b"k": b"v2"}])
        assert result == 2

    async def test_async_objectio_extend(self, tmp_path):
        from asebytes import AsyncObjectIO
        db = AsyncObjectIO(str(tmp_path / "test.lmdb"))
        result = await db.extend([{"a": 1}])
        assert result == 1

    async def test_async_aseio_extend(self, tmp_path, ethanol):
        from asebytes import AsyncASEIO
        db = AsyncASEIO(str(tmp_path / "test.lmdb"))
        result = await db.extend(ethanol[:3])
        assert result == 3

    async def test_sync_to_async_adapter_extend(self, tmp_path):
        from asebytes._async_backends import SyncToAsyncReadWriteAdapter
        backend = LMDBObjectBackend(str(tmp_path / "test.lmdb"))
        adapter = SyncToAsyncReadWriteAdapter(backend)
        result = await adapter.extend([{"a": 1}, {"a": 2}])
        assert result == 2
