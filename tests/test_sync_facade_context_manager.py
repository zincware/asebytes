"""Tests for __enter__/__exit__ on sync facades (BlobIO, ObjectIO, ASEIO).

Async facades support `async with db:`; sync facades should support `with db:`.
"""

from asebytes import ASEIO, BlobIO, ObjectIO
from asebytes.lmdb import LMDBBlobBackend, LMDBObjectBackend


def test_blobio_context_manager(tmp_path):
    backend = LMDBBlobBackend(str(tmp_path / "test.lmdb"))
    with BlobIO(backend) as db:
        assert isinstance(db, BlobIO)
        db.extend([{b"k": b"v"}])
        assert len(db) == 1


def test_objectio_context_manager(tmp_path):
    backend = LMDBObjectBackend(str(tmp_path / "test.lmdb"))
    with ObjectIO(backend) as db:
        assert isinstance(db, ObjectIO)
        db.extend([{"key": "value"}])
        assert len(db) == 1


def test_aseio_context_manager(tmp_path, ethanol):
    with ASEIO(str(tmp_path / "test.lmdb")) as db:
        assert isinstance(db, ASEIO)
        db.extend(ethanol[:2])
        assert len(db) == 2


def test_context_manager_returns_false_on_exception(tmp_path):
    """Context manager should not suppress exceptions."""
    backend = LMDBBlobBackend(str(tmp_path / "test.lmdb"))
    try:
        with BlobIO(backend):
            raise ValueError("test error")
    except ValueError:
        pass  # Exception should propagate
    else:
        raise AssertionError("Exception was suppressed")
