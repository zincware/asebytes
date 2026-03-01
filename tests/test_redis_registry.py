"""Tests for redis:// URI dispatch through the registry.

Verifies that BlobIO, ObjectIO, AsyncBlobIO, and AsyncObjectIO can all
be constructed from a ``redis://`` URI string, routing through the new
blob-level URI registries.
"""

from __future__ import annotations

import uuid

import pytest

redis_mod = pytest.importorskip("redis")


def test_parse_uri_recognizes_redis():
    from asebytes._registry import parse_uri

    scheme, remainder = parse_uri("redis://localhost:6379/0/myprefix")
    assert scheme == "redis"


def test_get_blob_backend_cls_returns_redis():
    from asebytes._registry import get_blob_backend_cls
    from asebytes.redis import RedisBlobBackend

    cls = get_blob_backend_cls("redis://localhost:6379")
    assert cls is RedisBlobBackend


def test_get_backend_cls_returns_adapter_for_redis():
    from asebytes._registry import get_backend_cls

    cls = get_backend_cls("redis://localhost:6379")
    assert callable(cls)


def test_blobio_redis_uri(redis_uri):
    from asebytes import BlobIO

    prefix = f"test_{uuid.uuid4().hex[:8]}"
    uri = f"{redis_uri}/0/{prefix}"
    db = BlobIO(uri)
    try:
        db.extend([{b"x": b"1"}, {b"y": b"2"}])
        assert len(db) == 2
        assert db[0] == {b"x": b"1"}
    finally:
        db.remove()


def test_objectio_redis_uri(redis_uri):
    from asebytes import ObjectIO

    prefix = f"test_{uuid.uuid4().hex[:8]}"
    uri = f"{redis_uri}/0/{prefix}"
    db = ObjectIO(uri)
    try:
        db.extend([{"x": 1, "y": 2.5}])
        assert len(db) == 1
        row = db[0]
        assert row["x"] == 1
        assert row["y"] == 2.5
    finally:
        db.remove()


@pytest.mark.anyio
async def test_async_blobio_redis_uri(redis_uri):
    from asebytes import AsyncBlobIO

    prefix = f"test_{uuid.uuid4().hex[:8]}"
    uri = f"{redis_uri}/0/{prefix}"
    db = AsyncBlobIO(uri)
    try:
        await db.extend([{b"x": b"1"}])
        assert await db.len() == 1
    finally:
        await db.remove()


@pytest.mark.anyio
async def test_async_objectio_redis_uri(redis_uri):
    from asebytes import AsyncObjectIO

    prefix = f"test_{uuid.uuid4().hex[:8]}"
    uri = f"{redis_uri}/0/{prefix}"
    db = AsyncObjectIO(uri)
    try:
        await db.extend([{"x": 1}])
        assert await db.len() == 1
    finally:
        await db.remove()
