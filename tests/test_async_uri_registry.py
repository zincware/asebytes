"""Tests for async URI registry -- native async backends for URI schemes."""

import pytest


def test_get_async_backend_cls_exists():
    from asebytes._registry import get_async_backend_cls
    assert callable(get_async_backend_cls)


def test_async_mongodb_returns_native_class():
    """mongodb:// should resolve to AsyncMongoObjectBackend, not sync wrapper."""
    from asebytes._registry import get_async_backend_cls
    cls = get_async_backend_cls("mongodb://localhost/db/col")
    assert cls.__name__ == "AsyncMongoObjectBackend"


def test_async_memory_falls_back_to_sync():
    """memory:// has no async-specific entry, should return sync class."""
    from asebytes._registry import get_async_backend_cls
    cls = get_async_backend_cls("memory://")
    # Returns sync MemoryObjectBackend (caller wraps with sync_to_async)
    assert cls.__name__ == "MemoryObjectBackend"


def test_async_lmdb_falls_back_to_sync():
    """*.lmdb has no async-specific entry, should return sync class."""
    from asebytes._registry import get_async_backend_cls
    cls = get_async_backend_cls("data.lmdb")
    assert cls.__name__ == "LMDBObjectBackend"


def test_parse_uri_recognises_async_only_schemes():
    """parse_uri should recognise schemes from _ASYNC_URI_REGISTRY too."""
    from asebytes._registry import parse_uri
    scheme, remainder = parse_uri("mongodb://localhost/db")
    assert scheme == "mongodb"


@pytest.mark.anyio
async def test_async_objectio_uses_native_backend_for_memory():
    """AsyncObjectIO("memory://") should work (sync fallback + wrap)."""
    from asebytes import AsyncObjectIO
    db = AsyncObjectIO("memory://")
    await db.extend([{"a": 1}])
    n = await db.len()
    assert n == 1
