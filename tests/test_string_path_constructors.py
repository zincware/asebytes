"""Tests for string-path constructors on all IO facades.

ASEIO already accepts str paths. This file tests the same support for:
- ObjectIO("path.lmdb")
- BlobIO("path.lmdb")
- AsyncASEIO("path.lmdb")
- AsyncObjectIO("path.lmdb")
- AsyncBlobIO("path.lmdb")
- AsyncBytesIO("path.lmdb")

Each should auto-detect the backend from the registry, just like ASEIO.
"""
from __future__ import annotations

import ase
import numpy as np
import pytest

import asebytes


# ── Helper data ──────────────────────────────────────────────────────────


def _sample_atoms() -> ase.Atoms:
    return ase.Atoms("H2", positions=[[0, 0, 0], [0, 0, 0.74]])


# ── Sync: ObjectIO from string path ─────────────────────────────────────


class TestObjectIOStringPath:
    def test_accepts_string_path(self, tmp_path):
        path = str(tmp_path / "test.lmdb")
        db = asebytes.ObjectIO(path)
        assert len(db) == 0

    def test_write_and_read_back(self, tmp_path):
        path = str(tmp_path / "test.lmdb")
        db = asebytes.ObjectIO(path)
        db.extend([{"a": 1, "b": 2}])
        assert len(db) == 1
        row = db[0]
        assert isinstance(row, dict)
        assert row["a"] == 1

    def test_readonly_kwarg(self, tmp_path):
        path = str(tmp_path / "test.lmdb")
        # Create first so the file exists
        w = asebytes.ObjectIO(path)
        w.extend([{"x": 42}])
        del w
        # Open read-only
        db = asebytes.ObjectIO(path, readonly=True)
        assert db[0]["x"] == 42

    def test_kwargs_forwarded(self, tmp_path):
        path = str(tmp_path / "test.lmdb")
        db = asebytes.ObjectIO(path, map_size=1024 * 1024)
        assert len(db) == 0

    def test_backend_instance_still_works(self, tmp_path):
        """Passing a backend directly must still work (no regression)."""
        path = str(tmp_path / "test.lmdb")
        backend = asebytes.LMDBObjectBackend(path)
        db = asebytes.ObjectIO(backend)
        assert len(db) == 0


# ── Sync: BlobIO from string path ───────────────────────────────────────


class TestBlobIOStringPath:
    def test_accepts_string_path(self, tmp_path):
        path = str(tmp_path / "test.lmdb")
        db = asebytes.BlobIO(path)
        assert len(db) == 0

    def test_write_and_read_back(self, tmp_path):
        path = str(tmp_path / "test.lmdb")
        db = asebytes.BlobIO(path)
        db.extend([{b"key": b"value"}])
        assert len(db) == 1
        row = db[0]
        assert isinstance(row, dict)
        assert row[b"key"] == b"value"

    def test_readonly_kwarg(self, tmp_path):
        path = str(tmp_path / "test.lmdb")
        w = asebytes.BlobIO(path)
        w.extend([{b"x": b"42"}])
        del w
        db = asebytes.BlobIO(path, readonly=True)
        assert db[0][b"x"] == b"42"

    def test_kwargs_forwarded(self, tmp_path):
        path = str(tmp_path / "test.lmdb")
        db = asebytes.BlobIO(path, map_size=1024 * 1024)
        assert len(db) == 0

    def test_backend_instance_still_works(self, tmp_path):
        path = str(tmp_path / "test.lmdb")
        backend = asebytes.LMDBBlobBackend(path)
        db = asebytes.BlobIO(backend)
        assert len(db) == 0


# ── Async: AsyncASEIO from string path ──────────────────────────────────


class TestAsyncASEIOStringPath:
    @pytest.mark.anyio
    async def test_accepts_string_path(self, tmp_path):
        path = str(tmp_path / "test.lmdb")
        db = asebytes.AsyncASEIO(path)
        assert await db.len() == 0

    @pytest.mark.anyio
    async def test_write_and_read_back(self, tmp_path):
        path = str(tmp_path / "test.lmdb")
        # Seed data via sync ASEIO
        sync_db = asebytes.ASEIO(path)
        sync_db.append(_sample_atoms())
        del sync_db
        # Read via async
        db = asebytes.AsyncASEIO(path)
        atoms = await db[0]
        assert isinstance(atoms, ase.Atoms)
        assert len(atoms) == 2

    @pytest.mark.anyio
    async def test_readonly_kwarg(self, tmp_path):
        path = str(tmp_path / "test.lmdb")
        sync_db = asebytes.ASEIO(path)
        sync_db.append(_sample_atoms())
        del sync_db
        db = asebytes.AsyncASEIO(path, readonly=True)
        atoms = await db[0]
        assert isinstance(atoms, ase.Atoms)


# ── Async: AsyncObjectIO from string path ───────────────────────────────


class TestAsyncObjectIOStringPath:
    @pytest.mark.anyio
    async def test_accepts_string_path(self, tmp_path):
        path = str(tmp_path / "test.lmdb")
        db = asebytes.AsyncObjectIO(path)
        assert await db.len() == 0

    @pytest.mark.anyio
    async def test_write_and_read_back(self, tmp_path):
        path = str(tmp_path / "test.lmdb")
        # Seed via sync ObjectIO
        sync_db = asebytes.ObjectIO(path)
        sync_db.extend([{"a": 1}])
        del sync_db
        db = asebytes.AsyncObjectIO(path)
        row = await db[0]
        assert isinstance(row, dict)
        assert row["a"] == 1

    @pytest.mark.anyio
    async def test_readonly_kwarg(self, tmp_path):
        path = str(tmp_path / "test.lmdb")
        sync_db = asebytes.ObjectIO(path)
        sync_db.extend([{"x": 99}])
        del sync_db
        db = asebytes.AsyncObjectIO(path, readonly=True)
        row = await db[0]
        assert row["x"] == 99


# ── Async: AsyncBlobIO from string path ─────────────────────────────────


class TestAsyncBlobIOStringPath:
    @pytest.mark.anyio
    async def test_accepts_string_path(self, tmp_path):
        path = str(tmp_path / "test.lmdb")
        db = asebytes.AsyncBlobIO(path)
        assert await db.len() == 0

    @pytest.mark.anyio
    async def test_write_and_read_back(self, tmp_path):
        path = str(tmp_path / "test.lmdb")
        sync_db = asebytes.BlobIO(path)
        sync_db.extend([{b"k": b"v"}])
        del sync_db
        db = asebytes.AsyncBlobIO(path)
        row = await db[0]
        assert isinstance(row, dict)
        assert row[b"k"] == b"v"

    @pytest.mark.anyio
    async def test_readonly_kwarg(self, tmp_path):
        path = str(tmp_path / "test.lmdb")
        sync_db = asebytes.BlobIO(path)
        sync_db.extend([{b"x": b"42"}])
        del sync_db
        db = asebytes.AsyncBlobIO(path, readonly=True)
        row = await db[0]
        assert row[b"x"] == b"42"


# ── Async: AsyncBytesIO from string path ────────────────────────────────


class TestAsyncBytesIOStringPath:
    @pytest.mark.anyio
    async def test_accepts_string_path(self, tmp_path):
        path = str(tmp_path / "test.lmdb")
        db = asebytes.AsyncBytesIO(path)
        assert await db.len() == 0

    @pytest.mark.anyio
    async def test_write_and_read_back(self, tmp_path):
        path = str(tmp_path / "test.lmdb")
        sync_db = asebytes.BlobIO(path)
        sync_db.extend([{b"k": b"v"}])
        del sync_db
        db = asebytes.AsyncBytesIO(path)
        row = await db[0]
        assert isinstance(row, dict)
        assert row[b"k"] == b"v"

    @pytest.mark.anyio
    async def test_readonly_kwarg(self, tmp_path):
        path = str(tmp_path / "test.lmdb")
        sync_db = asebytes.BlobIO(path)
        sync_db.extend([{b"x": b"42"}])
        del sync_db
        db = asebytes.AsyncBytesIO(path, readonly=True)
        row = await db[0]
        assert row[b"x"] == b"42"
