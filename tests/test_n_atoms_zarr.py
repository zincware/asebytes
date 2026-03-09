"""Tests for _n_atoms length column in Zarr backend."""
import ase
import numpy as np
import pytest
from asebytes import ASEIO


@pytest.fixture
def zarr_path(tmp_path):
    return str(tmp_path / "test.zarr")


class TestDtypePreservation:
    def test_numbers_roundtrip_int(self, zarr_path):
        atoms = ase.Atoms("H2O", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        db = ASEIO(zarr_path)
        db.extend([atoms])
        result = db[0]
        assert np.issubdtype(result.numbers.dtype, np.integer)

    def test_custom_int_array_preserved(self, zarr_path):
        atoms = ase.Atoms("H2", positions=[[0, 0, 0], [1, 0, 0]])
        atoms.arrays["tags"] = np.array([1, 2], dtype=np.int32)
        db = ASEIO(zarr_path)
        db.extend([atoms])
        result = db[0]
        assert np.issubdtype(result.arrays["tags"].dtype, np.integer)
        np.testing.assert_array_equal(result.arrays["tags"], [1, 2])


class TestVariableLengthRoundtrip:
    def test_varying_atom_counts(self, zarr_path):
        atoms_list = [
            ase.Atoms("H", positions=[[0, 0, 0]]),
            ase.Atoms("H2O", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]]),
            ase.Atoms("H2", positions=[[0, 0, 0], [1, 0, 0]]),
        ]
        db = ASEIO(zarr_path)
        db.extend(atoms_list)
        for i, original in enumerate(atoms_list):
            result = db[i]
            assert len(result) == len(original)
            np.testing.assert_allclose(result.positions, original.positions)

    def test_column_access_varying_lengths(self, zarr_path):
        atoms_list = [
            ase.Atoms("H", positions=[[0, 0, 0]]),
            ase.Atoms("H3", positions=[[0, 0, 0], [1, 0, 0], [2, 0, 0]]),
        ]
        db = ASEIO(zarr_path)
        db.extend(atoms_list)
        positions = db["arrays.positions"].to_list()
        assert len(positions[0]) == 1
        assert len(positions[1]) == 3


class TestFillValues:
    def test_float_arrays_use_nan_fill(self, zarr_path):
        atoms = ase.Atoms("H", positions=[[1.5, 2.5, 3.5]])
        db = ASEIO(zarr_path)
        db.extend([atoms])
        result = db[0]
        assert result.positions.dtype == np.float64

    def test_int_arrays_use_zero_fill(self, zarr_path):
        atoms = ase.Atoms("H2", positions=[[0, 0, 0], [1, 0, 0]])
        atoms.arrays["ids"] = np.array([10, 20], dtype=np.int64)
        db = ASEIO(zarr_path)
        db.extend([atoms])
        result = db[0]
        assert np.issubdtype(result.arrays["ids"].dtype, np.integer)
        np.testing.assert_array_equal(result.arrays["ids"], [10, 20])


class TestGetMany:
    def test_get_many_varying_atoms(self, zarr_path):
        atoms_list = [
            ase.Atoms("H", positions=[[0, 0, 0]]),
            ase.Atoms("H2O", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]]),
            ase.Atoms("H2", positions=[[0, 0, 0], [1, 0, 0]]),
        ]
        db = ASEIO(zarr_path)
        db.extend(atoms_list)
        results = db[0:3]
        for i, original in enumerate(atoms_list):
            assert len(results[i]) == len(original)
            np.testing.assert_allclose(results[i].positions, original.positions)


class TestMultipleBatchExtend:
    def test_two_batch_extend(self, zarr_path):
        db = ASEIO(zarr_path)
        db.extend([ase.Atoms("H", positions=[[0, 0, 0]])])
        db.extend([ase.Atoms("H2O", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]])])
        assert len(db[0]) == 1
        assert len(db[1]) == 3
