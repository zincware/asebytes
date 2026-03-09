"""Tests for batched LMDB get_column (single cursor.getmulti call)."""
from __future__ import annotations

import numpy as np
import pytest

from asebytes import ObjectIO


@pytest.fixture
def db(tmp_path):
    db = ObjectIO(str(tmp_path / "test.lmdb"))
    rows = [{"energy": float(i), "name": f"mol_{i}"} for i in range(100)]
    db.extend(rows)
    return db


class TestBatchGetColumn:
    def test_full_column(self, db):
        energies = db["energy"].to_list()
        assert len(energies) == 100
        assert energies[0] == pytest.approx(0.0)
        assert energies[99] == pytest.approx(99.0)

    def test_partial_indices(self, db):
        energies = db[[0, 50, 99]]["energy"].to_list()
        assert energies == pytest.approx([0.0, 50.0, 99.0])

    def test_missing_key_returns_nones(self, db):
        result = db._backend.get_column("nonexistent", [0, 1, 2])
        assert result == [None, None, None]

    def test_column_with_placeholder(self, tmp_path):
        db = ObjectIO(str(tmp_path / "sparse.lmdb"))
        db.extend([{"a": 1}])
        db.reserve(1)
        db.extend([{"a": 3}])
        result = db._backend.get_column("a", [0, 1, 2])
        assert result[0] == 1
        assert result[1] is None
        assert result[2] == 3

    def test_empty_indices(self, db):
        result = db._backend.get_column("energy", [])
        assert result == []

    def test_large_batch(self, tmp_path):
        db = ObjectIO(str(tmp_path / "large.lmdb"))
        rows = [{"val": float(i)} for i in range(10_000)]
        db.extend(rows)
        result = db._backend.get_column("val")
        assert len(result) == 10_000
        assert result[0] == pytest.approx(0.0)
        assert result[9999] == pytest.approx(9999.0)

    def test_string_column(self, db):
        names = db["name"].to_list()
        assert len(names) == 100
        assert names[0] == "mol_0"
        assert names[99] == "mol_99"

    def test_numpy_array_column(self, tmp_path):
        db = ObjectIO(str(tmp_path / "arrays.lmdb"))
        rows = [{"forces": np.random.randn(3, 3)} for _ in range(10)]
        db.extend(rows)
        result = db._backend.get_column("forces")
        assert len(result) == 10
        assert isinstance(result[0], np.ndarray)
        assert result[0].shape == (3, 3)
