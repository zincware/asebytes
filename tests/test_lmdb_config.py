"""Tests for LMDB configuration options."""

import tempfile
from pathlib import Path

import ase
import pytest

from asebytes import ASEIO, BytesIO


def test_custom_map_size():
    """Test custom map_size configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db = ASEIO(str(Path(tmpdir) / "test.lmdb"), map_size=1024**3)  # 1GB
        atoms = ase.Atoms("H2O", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        db.append(atoms)
        assert len(db) == 1
        assert db.io.env.info()["map_size"] == 1024**3


def test_readonly_mode():
    """Test readonly mode prevents writes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.lmdb")

        # Create database with write access
        db_write = ASEIO(db_path)
        atoms = ase.Atoms("H2O", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        db_write.append(atoms)
        db_write.io.env.close()

        # Open in readonly mode
        db_read = ASEIO(db_path, readonly=True)
        assert len(db_read) == 1

        # Verify writes fail
        with pytest.raises(Exception):  # lmdb.ReadonlyError
            db_read.append(atoms)


def test_max_readers_configuration():
    """Test max_readers configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db = ASEIO(str(Path(tmpdir) / "test.lmdb"), max_readers=64)
        atoms = ase.Atoms("H2O", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        db.append(atoms)
        assert db.io.env.info()["max_readers"] == 64


def test_lmdb_kwargs_passthrough():
    """Test that additional lmdb kwargs are passed through."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test sync=False for faster (but less durable) writes
        db = ASEIO(str(Path(tmpdir) / "test.lmdb"), sync=False)
        atoms = ase.Atoms("H2O", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        db.append(atoms)
        assert len(db) == 1


def test_bytesio_configuration():
    """Test BytesIO accepts same configuration options."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db = BytesIO(
            str(Path(tmpdir) / "test.lmdb"),
            map_size=2 * 1024**3,  # 2GB
            max_readers=32,
            sync=False,
        )
        data = {b"key1": b"value1", b"key2": b"value2"}
        db.append(data)
        assert len(db) == 1
        assert db.env.info()["map_size"] == 2 * 1024**3
        assert db.env.info()["max_readers"] == 32
