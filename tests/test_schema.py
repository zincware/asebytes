"""Tests for schema() method on ObjectIO and ASEIO."""
from __future__ import annotations

import ase
import numpy as np
import pytest

from asebytes import ASEIO, ObjectIO
from asebytes._async_object_io import AsyncObjectIO
from asebytes._async_io import AsyncASEIO
from asebytes._schema import SchemaEntry


class TestSchemaEntry:
    def test_frozen(self):
        entry = SchemaEntry(dtype=np.dtype("float64"), shape=())
        with pytest.raises(AttributeError):
            entry.dtype = np.dtype("int32")

    def test_scalar(self):
        entry = SchemaEntry(dtype=np.dtype("float64"), shape=())
        assert entry.shape == ()

    def test_per_atom(self):
        entry = SchemaEntry(dtype=np.dtype("float64"), shape=("N", 3))
        assert entry.shape == ("N", 3)


class TestObjectIOSchema:
    def test_schema_keys(self, tmp_path):
        db = ObjectIO(str(tmp_path / "test.lmdb"))
        db.extend([{"energy": -10.5, "forces": np.zeros((3, 3))}])
        s = db.schema(0)
        assert "energy" in s
        assert "forces" in s

    def test_forces_shape(self, tmp_path):
        db = ObjectIO(str(tmp_path / "test.lmdb"))
        db.extend([{"energy": -10.5, "forces": np.zeros((3, 3))}])
        s = db.schema(0)
        assert s["forces"].shape == (3, 3)
        assert s["forces"].dtype == np.dtype("float64")

    def test_energy_scalar(self, tmp_path):
        db = ObjectIO(str(tmp_path / "test.lmdb"))
        db.extend([{"energy": -10.5}])
        s = db.schema(0)
        assert s["energy"].shape == ()

    def test_schema_no_index(self, tmp_path):
        db = ObjectIO(str(tmp_path / "test.lmdb"))
        db.extend([{"energy": -10.5}])
        s = db.schema()
        assert "energy" in s

    def test_schema_empty_raises(self, tmp_path):
        db = ObjectIO(str(tmp_path / "empty.lmdb"))
        with pytest.raises(IndexError):
            db.schema()

    def test_string_column(self, tmp_path):
        db = ObjectIO(str(tmp_path / "test.lmdb"))
        db.extend([{"name": "water"}])
        s = db.schema(0)
        assert s["name"].dtype is str
        assert s["name"].shape == ()


class TestASEIOSchema:
    def test_schema_has_expected_keys(self, tmp_path):
        atoms = ase.Atoms("H2O", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        atoms.info["smiles"] = "O"
        from ase.calculators.singlepoint import SinglePointCalculator
        calc = SinglePointCalculator(atoms, energy=-10.5)
        atoms.calc = calc
        db = ASEIO(str(tmp_path / "test.lmdb"))
        db.extend([atoms])
        s = db.schema(0)
        assert "arrays.positions" in s
        assert "arrays.numbers" in s
        assert "calc.energy" in s
        assert "info.smiles" in s

    def test_positions_schema(self, tmp_path):
        atoms = ase.Atoms("H2O", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        db = ASEIO(str(tmp_path / "test.lmdb"))
        db.extend([atoms])
        s = db.schema(0)
        entry = s["arrays.positions"]
        assert entry.dtype == np.dtype("float64")
        assert len(entry.shape) == 2

    def test_energy_scalar_schema(self, tmp_path):
        atoms = ase.Atoms("H")
        from ase.calculators.singlepoint import SinglePointCalculator
        calc = SinglePointCalculator(atoms, energy=-10.5)
        atoms.calc = calc
        db = ASEIO(str(tmp_path / "test.lmdb"))
        db.extend([atoms])
        s = db.schema(0)
        entry = s["calc.energy"]
        assert entry.shape == ()

    def test_schema_no_index(self, tmp_path):
        atoms = ase.Atoms("H")
        db = ASEIO(str(tmp_path / "test.lmdb"))
        db.extend([atoms])
        s = db.schema()
        assert "arrays.positions" in s

    def test_schema_empty_raises(self, tmp_path):
        db = ASEIO(str(tmp_path / "empty.lmdb"))
        with pytest.raises(IndexError):
            db.schema()


class TestAsyncObjectIOSchema:
    @pytest.mark.anyio
    async def test_schema_keys(self, tmp_path):
        db = AsyncObjectIO(str(tmp_path / "test.lmdb"))
        await db.extend([{"energy": -10.5, "forces": np.zeros((3, 3))}])
        s = await db.schema(0)
        assert "energy" in s
        assert "forces" in s

    @pytest.mark.anyio
    async def test_schema_empty_raises(self, tmp_path):
        db = AsyncObjectIO(str(tmp_path / "empty.lmdb"))
        with pytest.raises(IndexError):
            await db.schema()


class TestAsyncASEIOSchema:
    @pytest.mark.anyio
    async def test_schema_keys(self, tmp_path, simple_atoms):
        db = AsyncASEIO(str(tmp_path / "test.lmdb"))
        await db.extend([simple_atoms])
        s = await db.schema(0)
        assert "arrays.positions" in s
        assert "arrays.numbers" in s

    @pytest.mark.anyio
    async def test_schema_empty_raises(self, tmp_path):
        db = AsyncASEIO(str(tmp_path / "empty.lmdb"))
        with pytest.raises(IndexError):
            await db.schema()
