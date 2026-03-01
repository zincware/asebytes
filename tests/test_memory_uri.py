"""Tests for memory:// URI integration."""

import uuid

import pytest


def test_objectio_memory_uri():
    from asebytes import ObjectIO

    group_name = f"test_{uuid.uuid4().hex[:8]}"
    db = ObjectIO("memory://", group=group_name)
    db.extend([{"a": 1}, {"a": 2}])
    assert len(db) == 2
    assert db[0] == {"a": 1}
    db._backend.remove()


def test_aseio_memory_uri(ethanol):
    from asebytes import ASEIO

    group_name = f"test_{uuid.uuid4().hex[:8]}"
    db = ASEIO("memory://", group=group_name)
    db.extend(ethanol[:2])
    assert len(db) == 2
    db._backend.remove()


def test_blobio_memory_uri():
    """BlobIO("memory://") should work via ObjectToBlob adapter fallback."""
    from asebytes import BlobIO

    group_name = f"test_{uuid.uuid4().hex[:8]}"
    db = BlobIO("memory://", group=group_name)
    db.extend([{b"k": b"v"}])
    assert len(db) == 1
    db._backend.remove()


@pytest.mark.anyio
async def test_async_objectio_memory_uri():
    from asebytes import AsyncObjectIO

    group_name = f"test_{uuid.uuid4().hex[:8]}"
    db = AsyncObjectIO("memory://", group=group_name)
    await db.extend([{"a": 1}])
    assert await db.len() == 1
    await db._backend.remove()


def test_memory_backend_importable():
    from asebytes import MemoryObjectBackend

    group_name = f"test_{uuid.uuid4().hex[:8]}"
    backend = MemoryObjectBackend(group=group_name)
    assert len(backend) == 0
    backend.remove()
