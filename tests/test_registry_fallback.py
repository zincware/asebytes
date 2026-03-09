import pytest
from asebytes._registry import get_backend_cls, get_blob_backend_cls


def test_get_blob_backend_cls_zarr_fallback():
    cls = get_blob_backend_cls("test.zarr")
    assert cls is not None


def test_get_blob_backend_cls_h5_fallback():
    cls = get_blob_backend_cls("test.h5")
    assert cls is not None


def test_get_blob_backend_cls_lmdb_native():
    from asebytes.lmdb import LMDBBlobBackend
    cls = get_blob_backend_cls("test.lmdb")
    assert cls is LMDBBlobBackend


def test_get_blob_backend_cls_unknown_raises():
    with pytest.raises(KeyError):
        get_blob_backend_cls("test.unknown")


def test_zarr_blob_fallback_creates_working_backend(tmp_path):
    factory = get_blob_backend_cls("test.zarr")
    backend = factory(str(tmp_path / "test.zarr"))
    assert len(backend) == 0
