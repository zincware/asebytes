"""Tests for memory:// URI integration."""

import pytest


def test_objectio_memory_uri():
    from asebytes import ObjectIO
    db = ObjectIO("memory://")
    db.extend([{"a": 1}, {"a": 2}])
    assert len(db) == 2
    assert db[0] == {"a": 1}


def test_aseio_memory_uri(ethanol):
    from asebytes import ASEIO
    db = ASEIO("memory://")
    db.extend(ethanol[:2])
    assert len(db) == 2


def test_blobio_memory_uri():
    """BlobIO("memory://") should work via ObjectToBlob adapter fallback."""
    from asebytes import BlobIO
    db = BlobIO("memory://")
    db.extend([{b"k": b"v"}])
    assert len(db) == 1


@pytest.mark.anyio
async def test_async_objectio_memory_uri():
    from asebytes import AsyncObjectIO
    db = AsyncObjectIO("memory://")
    await db.extend([{"a": 1}])
    assert await db.len() == 1


def test_memory_backend_importable():
    from asebytes import MemoryObjectBackend
    backend = MemoryObjectBackend()
    assert len(backend) == 0
