"""Tests for unified backend registry."""
from __future__ import annotations

import fnmatch

import pytest

from asebytes._registry import resolve_backend, parse_uri
from asebytes.columnar import RaggedColumnarBackend, PaddedColumnarBackend


class TestResolveByExtension:
    def test_lmdb_object(self):
        cls = resolve_backend("data.lmdb", layer="object")
        assert cls is not None

    def test_h5_resolves_to_ragged(self):
        cls = resolve_backend("data.h5", layer="object")
        assert cls is RaggedColumnarBackend

    def test_zarr_resolves_to_ragged(self):
        cls = resolve_backend("data.zarr", layer="object")
        assert cls is RaggedColumnarBackend

    def test_h5p_resolves_to_padded(self):
        cls = resolve_backend("data.h5p", layer="object")
        assert cls is PaddedColumnarBackend

    def test_zarrp_resolves_to_padded(self):
        cls = resolve_backend("data.zarrp", layer="object")
        assert cls is PaddedColumnarBackend

    def test_h5md_resolves_to_h5md(self):
        from asebytes.h5md import H5MDBackend
        cls = resolve_backend("data.h5md", layer="object")
        assert cls is H5MDBackend

    def test_lmdb_blob(self):
        cls = resolve_backend("data.lmdb", layer="blob")
        assert cls is not None


class TestNoGlobCollisions:
    """Verify that padded extensions do not collide with ragged patterns (ARCH-06)."""

    def test_h5p_does_not_match_h5_pattern(self):
        assert fnmatch.fnmatch("file.h5p", "*.h5") is False

    def test_zarrp_does_not_match_zarr_pattern(self):
        assert fnmatch.fnmatch("file.zarrp", "*.zarr") is False


class TestResolveByScheme:
    def test_memory_object(self):
        cls = resolve_backend("memory://test", layer="object")
        assert cls is not None

    def test_redis_blob(self):
        cls = resolve_backend("redis://localhost", layer="blob")
        assert cls is not None


class TestResolveAsync:
    def test_async_prefers_native(self):
        cls = resolve_backend("mongodb://localhost", layer="object", async_=True)
        assert cls is not None
        assert "Async" in cls.__name__

    def test_async_falls_back_to_sync(self):
        cls = resolve_backend("data.lmdb", layer="object", async_=True)
        assert cls is not None


class TestResolveWritability:
    def test_writable_preferred(self):
        cls = resolve_backend("data.lmdb", layer="object", writable=True)
        assert cls is not None

    def test_readonly_available(self):
        cls = resolve_backend("data.lmdb", layer="object", writable=False)
        assert cls is not None

    def test_readonly_only_raises_on_write(self):
        with pytest.raises(TypeError):
            resolve_backend("data.traj", layer="object", writable=True)


class TestUnknownPath:
    def test_unknown_extension_raises(self):
        with pytest.raises(ValueError, match="No backend"):
            resolve_backend("data.unknown", layer="object")

    def test_unknown_scheme_raises(self):
        with pytest.raises(ValueError, match="No backend"):
            resolve_backend("ftp://server/data", layer="object")


class TestCrossLayerAdapter:
    def test_redis_object_via_adapter(self):
        cls = resolve_backend("redis://localhost", layer="object")
        assert cls is not None

    def test_zarr_blob_via_adapter(self):
        cls = resolve_backend("data.zarr", layer="blob")
        assert cls is not None


class TestBackwardCompat:
    def test_get_backend_cls_still_works(self):
        from asebytes._registry import get_backend_cls
        cls = get_backend_cls("test.lmdb")
        assert cls is not None

    def test_get_blob_backend_cls_still_works(self):
        from asebytes._registry import get_blob_backend_cls
        cls = get_blob_backend_cls("test.lmdb")
        assert cls is not None

    def test_get_async_backend_cls_still_works(self):
        from asebytes._registry import get_async_backend_cls
        cls = get_async_backend_cls("test.lmdb")
        assert cls is not None
