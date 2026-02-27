"""Tests for ASEIO cache_to middleware."""

from __future__ import annotations

from typing import Any

import ase
import numpy as np
import pytest
from ase.calculators.singlepoint import SinglePointCalculator

from asebytes import ASEIO
from asebytes._convert import atoms_to_dict
from asebytes._backends import ReadBackend, ReadWriteBackend


# ---------------------------------------------------------------------------
# In-memory backends for isolated testing
# ---------------------------------------------------------------------------


class InMemoryReadOnly(ReadBackend):
    """Read-only backend backed by a plain list. Tracks access counts."""

    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = rows
        self.access_count = 0

    def __len__(self) -> int:
        return len(self._rows)

    def get(self, index: int, keys: list[str] | None = None) -> dict[str, Any]:
        if index < 0 or index >= len(self._rows):
            raise IndexError(index)
        self.access_count += 1
        row = self._rows[index]
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)


class InMemoryWritable(ReadWriteBackend):
    """Writable backend backed by a plain list."""

    def __init__(self):
        self._rows: list[dict[str, Any]] = []

    def __len__(self) -> int:
        return len(self._rows)

    def get(self, index: int, keys: list[str] | None = None) -> dict[str, Any]:
        if index < 0 or index >= len(self._rows):
            raise IndexError(index)
        row = self._rows[index]
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    def set(self, index: int, data: dict[str, Any]) -> None:
        while len(self._rows) <= index:
            self._rows.append({})
        self._rows[index] = data

    def insert(self, index: int, data: dict[str, Any]) -> None:
        self._rows.insert(index, data)

    def delete(self, index: int) -> None:
        del self._rows[index]

    def extend(self, data: list[dict[str, Any]]) -> None:
        self._rows.extend(data)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_atoms(i: int) -> ase.Atoms:
    atoms = ase.Atoms("H", positions=[[float(i), 0.0, 0.0]])
    atoms.info["tag"] = f"mol_{i}"
    atoms.calc = SinglePointCalculator(atoms)
    atoms.calc.results = {"energy": float(-i)}
    return atoms


@pytest.fixture
def source_rows():
    """5 rows as flat dicts."""
    return [atoms_to_dict(_make_atoms(i)) for i in range(5)]


@pytest.fixture
def source(source_rows):
    """Read-only source backend with 5 rows."""
    return InMemoryReadOnly(source_rows)


@pytest.fixture
def cache():
    """Empty writable cache backend."""
    return InMemoryWritable()


# ---------------------------------------------------------------------------
# Basic cache behavior
# ---------------------------------------------------------------------------


class TestCacheToBasic:
    def test_read_populates_cache(self, source, cache):
        """First read should populate the cache."""
        db = ASEIO(source, cache_to=cache)
        atoms = db[0]
        assert isinstance(atoms, ase.Atoms)
        assert len(cache) == 1

    def test_second_read_hits_cache(self, source, cache):
        """Second read of same index should not hit source."""
        db = ASEIO(source, cache_to=cache)
        db[0]
        count_after_first = source.access_count
        db[0]
        assert source.access_count == count_after_first

    def test_cache_miss_reads_source(self, source, cache):
        """Cache miss should read from source."""
        db = ASEIO(source, cache_to=cache)
        db[0]
        db[1]
        assert source.access_count == 2
        assert len(cache) == 2

    def test_full_epoch_fills_cache(self, source, cache):
        """Iterating all rows should fill cache completely."""
        db = ASEIO(source, cache_to=cache)
        for _ in db:
            pass
        assert len(cache) == 5
        # Second pass should not touch source
        source.access_count = 0
        for _ in db:
            pass
        assert source.access_count == 0

    def test_len_delegates_to_source(self, source, cache):
        """len() should come from source, not cache."""
        db = ASEIO(source, cache_to=cache)
        assert len(db) == 5
        assert len(cache) == 0  # len() didn't trigger any reads


class TestCacheToData:
    def test_cached_data_round_trips(self, source, cache):
        """Data read from cache should match source."""
        db = ASEIO(source, cache_to=cache)
        atoms_first = db[2]
        atoms_cached = db[2]
        assert atoms_first.positions[0, 0] == pytest.approx(2.0)
        assert atoms_cached.positions[0, 0] == pytest.approx(2.0)
        assert atoms_first.info["tag"] == atoms_cached.info["tag"]

    def test_partial_key_read_caches_full_row(self, source, cache):
        """Reading with keys filter should still cache the full row."""
        db = ASEIO(source, cache_to=cache)
        # Access via column view (reads specific keys) — returns Atoms
        atoms = db["calc.energy"][0]
        assert atoms.calc.results["energy"] == pytest.approx(0.0)
        # Cache should have the full row, not just calc.energy
        cached_row = cache.get(0)
        assert "arrays.positions" in cached_row
        assert "calc.energy" in cached_row
        assert "info.tag" in cached_row

    def test_negative_index(self, source, cache):
        """Negative indexing should work with cache."""
        db = ASEIO(source, cache_to=cache)
        atoms = db[-1]
        assert atoms.positions[0, 0] == pytest.approx(4.0)


class TestCacheToViews:
    def test_slice_view(self, source, cache):
        """Slice view should populate cache."""
        db = ASEIO(source, cache_to=cache)
        atoms_list = list(db[1:4])
        assert len(atoms_list) == 3
        # Cache has entries at indices 1,2,3; list-backed backend pads index 0
        assert source.access_count == 3

    def test_column_view(self, source, cache):
        """Column view should populate cache."""
        db = ASEIO(source, cache_to=cache)
        energies = db["calc.energy"].to_list()
        assert len(energies) == 5
        assert len(cache) == 5

    def test_list_index_view(self, source, cache):
        """List index should populate cache."""
        db = ASEIO(source, cache_to=cache)
        atoms_list = list(db[[0, 3, 4]])
        assert len(atoms_list) == 3
        assert source.access_count == 3


class TestCacheToReadOnly:
    def test_source_readonly_stays_readonly(self, source, cache):
        """ASEIO with read-only source should remain read-only even with cache."""
        db = ASEIO(source, cache_to=cache)
        with pytest.raises(TypeError, match="read-only"):
            db.extend([ase.Atoms("H")])

    def test_no_cache_to(self, source):
        """Without cache_to, should work normally."""
        db = ASEIO(source)
        atoms = db[0]
        assert isinstance(atoms, ase.Atoms)


class TestCacheToStringPath:
    def test_string_cache_path(self, source, tmp_path):
        """cache_to as string path should auto-create LMDB backend."""
        cache_path = str(tmp_path / "cache.lmdb")
        db = ASEIO(source, cache_to=cache_path)
        atoms = db[0]
        assert isinstance(atoms, ase.Atoms)
        # Read again — should hit cache
        source.access_count = 0
        atoms2 = db[0]
        assert source.access_count == 0
        assert atoms2.positions[0, 0] == pytest.approx(0.0)


class TestCacheToWithLMDB:
    def test_lmdb_source_with_cache(self, tmp_path):
        """LMDB source with LMDB cache."""
        source_path = str(tmp_path / "source.lmdb")
        cache_path = str(tmp_path / "cache.lmdb")

        # Write source data
        source_db = ASEIO(source_path)
        source_db.extend([_make_atoms(i) for i in range(5)])

        # Read with cache
        db = ASEIO(source_path, readonly=True, cache_to=cache_path)
        atoms = db[0]
        assert atoms.positions[0, 0] == pytest.approx(0.0)

    def test_persistent_cache_across_opens(self, tmp_path):
        """Cache should persist across ASEIO instances."""
        source_path = str(tmp_path / "source.lmdb")
        cache_path = str(tmp_path / "cache.lmdb")

        # Write source
        source_db = ASEIO(source_path)
        source_db.extend([_make_atoms(i) for i in range(5)])

        # First open — populate cache
        db1 = ASEIO(source_path, readonly=True, cache_to=cache_path)
        list(db1)  # fill cache

        # Second open — cache should be populated
        from asebytes.lmdb import LMDBObjectBackend

        cache_backend = LMDBObjectBackend(cache_path, readonly=True)
        assert len(cache_backend) == 5


class TestCacheToWithH5MD:
    def test_h5md_source_with_lmdb_cache(self, tmp_path):
        """H5MD source with LMDB cache."""
        h5_path = str(tmp_path / "source.h5")
        cache_path = str(tmp_path / "cache.lmdb")

        # Write source data
        source_db = ASEIO(h5_path)
        source_db.extend([_make_atoms(i) for i in range(5)])

        # Read with cache
        db = ASEIO(h5_path, readonly=True, cache_to=cache_path)
        atoms_list = list(db)
        assert len(atoms_list) == 5
        assert atoms_list[2].positions[0, 0] == pytest.approx(2.0)
