"""Tests for __repr__ on sync facades (BlobIO, ObjectIO, ASEIO).

Async facades have __repr__; sync facades should match.
"""

from asebytes import ASEIO, BlobIO, ObjectIO
from asebytes.lmdb import LMDBBlobBackend, LMDBObjectBackend


def test_blobio_repr(tmp_path):
    backend = LMDBBlobBackend(str(tmp_path / "test.lmdb"))
    db = BlobIO(backend)
    r = repr(db)
    assert r.startswith("BlobIO(backend=")
    assert "LMDBBlobBackend" in r


def test_objectio_repr(tmp_path):
    backend = LMDBObjectBackend(str(tmp_path / "test.lmdb"))
    db = ObjectIO(backend)
    r = repr(db)
    assert r.startswith("ObjectIO(backend=")
    assert "LMDBObjectBackend" in r


def test_aseio_repr(tmp_path):
    db = ASEIO(str(tmp_path / "test.lmdb"))
    r = repr(db)
    assert r.startswith("ASEIO(backend=")
