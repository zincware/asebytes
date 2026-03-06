"""E2E tests for the Zarr backend.

Every test uses io1 for writing and io2 (fresh instance) for reading.
"""

import numpy as np
import numpy.testing as npt
import pytest
from ase.build import molecule, bulk
from ase.calculators.singlepoint import SinglePointCalculator
import ase.collections

import asebytes
from asebytes.columnar import RaggedColumnarBackend as ZarrBackend
from asebytes._convert import atoms_to_dict, dict_to_atoms


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def zarr_path(tmp_path):
    return str(tmp_path / "test.zarr")


@pytest.fixture
def water_frames():
    """3 water molecules with energy + forces."""
    frames = []
    for i in range(3):
        atoms = molecule("H2O")
        atoms.positions += np.random.RandomState(i).randn(3, 3) * 0.1
        atoms.calc = SinglePointCalculator(
            atoms,
            energy=-10.5 + i * 0.1,
            forces=np.random.RandomState(i).randn(3, 3) * 0.01,
        )
        frames.append(atoms)
    return frames


@pytest.fixture
def s22_frames():
    """S22 dataset - variable size molecules."""
    return list(ase.collections.s22)


@pytest.fixture
def s22_with_calc():
    """S22 with energy and forces."""
    frames = []
    rng = np.random.RandomState(42)
    for atoms in ase.collections.s22:
        atoms.calc = SinglePointCalculator(
            atoms,
            energy=rng.randn(),
            forces=rng.randn(len(atoms), 3),
        )
        frames.append(atoms)
    return frames


@pytest.fixture
def pbc_frames():
    """Frames with periodic boundary conditions and cell."""
    frames = []
    rng = np.random.RandomState(0)
    for i in range(5):
        atoms = bulk("Cu", "fcc", a=3.6)
        atoms.positions += rng.randn(len(atoms), 3) * 0.05
        atoms.calc = SinglePointCalculator(
            atoms,
            energy=rng.randn(),
            forces=rng.randn(len(atoms), 3),
            stress=rng.randn(6),
        )
        frames.append(atoms)
    return frames


@pytest.fixture
def mixed_pbc_frames():
    """Frames with varying PBC per frame."""
    frames = []
    rng = np.random.RandomState(1)
    for atoms in ase.collections.s22:
        atoms.set_pbc(rng.rand(3) > 0.5)
        atoms.set_cell(rng.rand(3, 3) * 10)
        frames.append(atoms)
    return frames


@pytest.fixture
def info_arrays_calc_frames():
    """Frames with info, custom arrays, calc, and velocities."""
    frames = []
    rng = np.random.RandomState(42)
    for atoms in ase.collections.s22:
        atoms.info["mlip_energy"] = rng.rand()
        atoms.info["collection"] = "s22"
        atoms.info["metadata"] = {"author": "test", "version": 1}
        atoms.info["tags"] = [1, 2, 3]
        atoms.new_array("mlip_forces", rng.rand(len(atoms), 3))
        atoms.set_velocities(rng.rand(len(atoms), 3))
        atoms.calc = SinglePointCalculator(
            atoms,
            energy=rng.rand(),
            forces=rng.rand(len(atoms), 3),
        )
        frames.append(atoms)
    return frames


# ---------------------------------------------------------------------------
# Basic round-trip
# ---------------------------------------------------------------------------


class TestBasicRoundTrip:
    def test_write_read_single_frame(self, zarr_path):
        atoms = molecule("H2O")

        io1 = ZarrBackend(zarr_path)
        io1.extend([atoms_to_dict(atoms)])
        io1.close()

        io2 = ZarrBackend(zarr_path, readonly=True)
        assert len(io2) == 1
        row = io2.get(0)
        recovered = dict_to_atoms(row)
        npt.assert_array_equal(recovered.get_atomic_numbers(), atoms.get_atomic_numbers())
        npt.assert_allclose(recovered.get_positions(), atoms.get_positions())
        io2.close()

    def test_write_read_multiple_frames(self, zarr_path, water_frames):
        io1 = ZarrBackend(zarr_path)
        io1.extend([atoms_to_dict(a) for a in water_frames])
        io1.close()

        io2 = ZarrBackend(zarr_path, readonly=True)
        assert len(io2) == 3
        for i, atoms in enumerate(water_frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            npt.assert_array_equal(
                recovered.get_atomic_numbers(), atoms.get_atomic_numbers()
            )
            npt.assert_allclose(recovered.get_positions(), atoms.get_positions())
        io2.close()

    def test_append_twice(self, zarr_path, water_frames):
        io1 = ZarrBackend(zarr_path)
        io1.extend([atoms_to_dict(water_frames[0])])
        io1.extend([atoms_to_dict(a) for a in water_frames[1:]])
        io1.close()

        io2 = ZarrBackend(zarr_path, readonly=True)
        assert len(io2) == 3
        for i, atoms in enumerate(water_frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            npt.assert_allclose(recovered.get_positions(), atoms.get_positions())
        io2.close()

    def test_len_empty_file(self, zarr_path):
        io1 = ZarrBackend(zarr_path)
        assert len(io1) == 0
        io1.close()


# ---------------------------------------------------------------------------
# Variable particle count
# ---------------------------------------------------------------------------


class TestVariableShape:
    def test_s22_variable_sizes(self, zarr_path, s22_frames):
        io1 = ZarrBackend(zarr_path)
        io1.extend([atoms_to_dict(a) for a in s22_frames])
        io1.close()

        io2 = ZarrBackend(zarr_path, readonly=True)
        assert len(io2) == len(s22_frames)
        for i, atoms in enumerate(s22_frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            npt.assert_array_equal(
                recovered.get_atomic_numbers(), atoms.get_atomic_numbers()
            )
            npt.assert_allclose(recovered.get_positions(), atoms.get_positions())
            assert len(recovered) == len(atoms)
        io2.close()

    def test_growing_system(self, zarr_path):
        """System where atom count grows each frame."""
        frames = []
        for n in [2, 5, 10, 3]:
            atoms = molecule("H2O") if n <= 3 else molecule("CH4")
            frames.append(atoms)

        io1 = ZarrBackend(zarr_path)
        io1.extend([atoms_to_dict(a) for a in frames])
        io1.close()

        io2 = ZarrBackend(zarr_path, readonly=True)
        assert len(io2) == 4
        for i, atoms in enumerate(frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            assert len(recovered) == len(atoms)
        io2.close()


# ---------------------------------------------------------------------------
# Calculator results
# ---------------------------------------------------------------------------


class TestCalculatorResults:
    def test_energy_forces(self, zarr_path, water_frames):
        io1 = ZarrBackend(zarr_path)
        io1.extend([atoms_to_dict(a) for a in water_frames])
        io1.close()

        io2 = ZarrBackend(zarr_path, readonly=True)
        for i, atoms in enumerate(water_frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            assert recovered.calc is not None
            npt.assert_allclose(
                recovered.calc.results["energy"],
                atoms.calc.results["energy"],
            )
            npt.assert_allclose(
                recovered.calc.results["forces"],
                atoms.calc.results["forces"],
            )
        io2.close()

    def test_stress(self, zarr_path, pbc_frames):
        io1 = ZarrBackend(zarr_path)
        io1.extend([atoms_to_dict(a) for a in pbc_frames])
        io1.close()

        io2 = ZarrBackend(zarr_path, readonly=True)
        for i, atoms in enumerate(pbc_frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            npt.assert_allclose(
                recovered.calc.results["stress"],
                atoms.calc.results["stress"],
            )
        io2.close()

    def test_s22_with_calc_variable(self, zarr_path, s22_with_calc):
        io1 = ZarrBackend(zarr_path)
        io1.extend([atoms_to_dict(a) for a in s22_with_calc])
        io1.close()

        io2 = ZarrBackend(zarr_path, readonly=True)
        assert len(io2) == len(s22_with_calc)
        for i, atoms in enumerate(s22_with_calc):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            npt.assert_allclose(
                recovered.calc.results["energy"],
                atoms.calc.results["energy"],
            )
            npt.assert_allclose(
                recovered.calc.results["forces"],
                atoms.calc.results["forces"],
            )
        io2.close()


# ---------------------------------------------------------------------------
# PBC and cell
# ---------------------------------------------------------------------------


class TestPBCAndCell:
    def test_periodic_system(self, zarr_path, pbc_frames):
        io1 = ZarrBackend(zarr_path)
        io1.extend([atoms_to_dict(a) for a in pbc_frames])
        io1.close()

        io2 = ZarrBackend(zarr_path, readonly=True)
        for i, atoms in enumerate(pbc_frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            npt.assert_allclose(
                recovered.get_cell().array, atoms.get_cell().array
            )
            npt.assert_array_equal(recovered.get_pbc(), atoms.get_pbc())
        io2.close()

    def test_mixed_pbc(self, zarr_path, mixed_pbc_frames):
        io1 = ZarrBackend(zarr_path)
        io1.extend([atoms_to_dict(a) for a in mixed_pbc_frames])
        io1.close()

        io2 = ZarrBackend(zarr_path, readonly=True)
        for i, atoms in enumerate(mixed_pbc_frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            npt.assert_array_equal(recovered.get_pbc(), atoms.get_pbc())
            npt.assert_allclose(
                recovered.get_cell().array, atoms.get_cell().array
            )
        io2.close()


# ---------------------------------------------------------------------------
# Info, arrays, velocities
# ---------------------------------------------------------------------------


class TestInfoAndArrays:
    def test_custom_info_and_arrays(self, zarr_path, info_arrays_calc_frames):
        io1 = ZarrBackend(zarr_path)
        io1.extend([atoms_to_dict(a) for a in info_arrays_calc_frames])
        io1.close()

        io2 = ZarrBackend(zarr_path, readonly=True)
        for i, atoms in enumerate(info_arrays_calc_frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            # Info
            npt.assert_allclose(
                recovered.info["mlip_energy"], atoms.info["mlip_energy"]
            )
            assert recovered.info["collection"] == "s22"
            assert recovered.info["metadata"] == {"author": "test", "version": 1}
            assert recovered.info["tags"] == [1, 2, 3]
            # Custom arrays
            npt.assert_allclose(
                recovered.arrays["mlip_forces"],
                atoms.arrays["mlip_forces"],
            )
            # Velocities
            npt.assert_allclose(
                recovered.get_velocities(), atoms.get_velocities()
            )
        io2.close()


# ---------------------------------------------------------------------------
# Column reads
# ---------------------------------------------------------------------------


class TestColumnReads:
    def test_read_energy_column(self, zarr_path, water_frames):
        io1 = ZarrBackend(zarr_path)
        io1.extend([atoms_to_dict(a) for a in water_frames])
        io1.close()

        io2 = ZarrBackend(zarr_path, readonly=True)
        energies = io2.get_column("calc.energy")
        assert len(energies) == 3
        for i, atoms in enumerate(water_frames):
            npt.assert_allclose(energies[i], atoms.calc.results["energy"])
        io2.close()

    def test_keys_list(self, zarr_path, water_frames):
        io1 = ZarrBackend(zarr_path)
        io1.extend([atoms_to_dict(a) for a in water_frames])
        io1.close()

        io2 = ZarrBackend(zarr_path, readonly=True)
        cols = io2.keys(0)
        assert "arrays.positions" in cols
        assert "arrays.numbers" in cols
        assert "calc.energy" in cols
        assert "calc.forces" in cols
        io2.close()


# ---------------------------------------------------------------------------
# Bulk reads
# ---------------------------------------------------------------------------


class TestBulkReads:
    def test_read_rows_sorted(self, zarr_path, water_frames):
        io1 = ZarrBackend(zarr_path)
        io1.extend([atoms_to_dict(a) for a in water_frames])
        io1.close()

        io2 = ZarrBackend(zarr_path, readonly=True)
        rows = io2.get_many([0, 1, 2])
        assert len(rows) == 3
        for i, row in enumerate(rows):
            recovered = dict_to_atoms(row)
            npt.assert_allclose(
                recovered.get_positions(), water_frames[i].get_positions()
            )
        io2.close()

    def test_read_rows_unsorted(self, zarr_path, water_frames):
        io1 = ZarrBackend(zarr_path)
        io1.extend([atoms_to_dict(a) for a in water_frames])
        io1.close()

        io2 = ZarrBackend(zarr_path, readonly=True)
        rows = io2.get_many([2, 0, 1])
        assert len(rows) == 3
        for j, orig_idx in enumerate([2, 0, 1]):
            recovered = dict_to_atoms(rows[j])
            npt.assert_allclose(
                recovered.get_positions(), water_frames[orig_idx].get_positions()
            )
        io2.close()

    def test_read_rows_duplicate(self, zarr_path, water_frames):
        io1 = ZarrBackend(zarr_path)
        io1.extend([atoms_to_dict(a) for a in water_frames])
        io1.close()

        io2 = ZarrBackend(zarr_path, readonly=True)
        rows = io2.get_many([0, 0, 1])
        assert len(rows) == 3
        r0 = dict_to_atoms(rows[0])
        r1 = dict_to_atoms(rows[1])
        npt.assert_allclose(r0.get_positions(), r1.get_positions())
        io2.close()


# ---------------------------------------------------------------------------
# Connectivity (molify)
# ---------------------------------------------------------------------------


class TestConnectivity:
    """Round-trip tests for molify connectivity data."""

    def test_connectivity_round_trip(self, zarr_path):
        molify = pytest.importorskip("molify")

        frames = molify.smiles2conformers("CCO", numConfs=3)
        assert "connectivity" in frames[0].info

        io1 = ZarrBackend(zarr_path)
        io1.extend([atoms_to_dict(a) for a in frames])
        io1.close()

        io2 = ZarrBackend(zarr_path, readonly=True)
        for i, atoms in enumerate(frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            orig = [list(t) for t in atoms.info["connectivity"]]
            assert recovered.info["connectivity"] == orig
            npt.assert_array_equal(
                recovered.get_atomic_numbers(), atoms.get_atomic_numbers()
            )
            npt.assert_allclose(
                recovered.get_positions(), atoms.get_positions(), atol=1e-10
            )
        io2.close()

    def test_connectivity_with_smiles(self, zarr_path):
        molify = pytest.importorskip("molify")

        frames = molify.smiles2conformers("c1ccccc1", numConfs=2)
        assert "smiles" in frames[0].info
        assert "connectivity" in frames[0].info

        io1 = ZarrBackend(zarr_path)
        io1.extend([atoms_to_dict(a) for a in frames])
        io1.close()

        io2 = ZarrBackend(zarr_path, readonly=True)
        for i, atoms in enumerate(frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            assert recovered.info["smiles"] == atoms.info["smiles"]
            assert len(recovered.info["connectivity"]) == len(
                atoms.info["connectivity"]
            )
        io2.close()


# ---------------------------------------------------------------------------
# Variable-size appends (multiple extend calls)
# ---------------------------------------------------------------------------


class TestVariableSizeAppends:
    """Test alternating larger/smaller atom counts across separate appends."""

    def test_append_larger_smaller_larger(self, zarr_path):
        """Append H2O (3) -> CH4 (5) -> H2 (2) -> benzene (12)."""
        batches = [
            [molecule("H2O") for _ in range(3)],
            [molecule("CH4") for _ in range(2)],
            [molecule("H2") for _ in range(3)],
            [molecule("C6H6") for _ in range(2)],
        ]
        all_frames = [a for batch in batches for a in batch]

        io1 = ZarrBackend(zarr_path)
        for batch in batches:
            io1.extend([atoms_to_dict(a) for a in batch])
        io1.close()

        io2 = ZarrBackend(zarr_path, readonly=True)
        assert len(io2) == len(all_frames)
        for i, atoms in enumerate(all_frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            assert len(recovered) == len(atoms)
            npt.assert_array_equal(
                recovered.get_atomic_numbers(), atoms.get_atomic_numbers()
            )
            npt.assert_allclose(
                recovered.get_positions(), atoms.get_positions(), atol=1e-10
            )
        io2.close()

    def test_append_larger_smaller_via_aseio(self, tmp_path):
        """Same test through ASEIO interface."""
        path = str(tmp_path / "test.zarr")
        batches = [
            [molecule("H2O") for _ in range(3)],
            [molecule("CH4") for _ in range(2)],
            [molecule("H2") for _ in range(3)],
            [molecule("C6H6") for _ in range(2)],
        ]
        all_frames = [a for batch in batches for a in batch]

        io1 = asebytes.ASEIO(path)
        for batch in batches:
            io1.extend(batch)

        io2 = asebytes.ASEIO(path, readonly=True)
        assert len(io2) == len(all_frames)
        for i, atoms in enumerate(all_frames):
            recovered = io2[i]
            assert len(recovered) == len(atoms)
            npt.assert_array_equal(
                recovered.get_atomic_numbers(), atoms.get_atomic_numbers()
            )

    def test_append_with_calc_variable_sizes(self, zarr_path):
        """Append variable-size frames with calculator results."""
        rng = np.random.RandomState(42)
        batches = []
        for mol_name in ["H2O", "CH4", "H2", "C6H6"]:
            atoms = molecule(mol_name)
            atoms.calc = SinglePointCalculator(
                atoms,
                energy=rng.randn(),
                forces=rng.randn(len(atoms), 3),
            )
            batches.append([atoms])

        all_frames = [a for batch in batches for a in batch]

        io1 = ZarrBackend(zarr_path)
        for batch in batches:
            io1.extend([atoms_to_dict(a) for a in batch])
        io1.close()

        io2 = ZarrBackend(zarr_path, readonly=True)
        assert len(io2) == len(all_frames)
        for i, atoms in enumerate(all_frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            assert len(recovered) == len(atoms)
            npt.assert_allclose(
                recovered.calc.results["energy"],
                atoms.calc.results["energy"],
            )
            npt.assert_allclose(
                recovered.calc.results["forces"],
                atoms.calc.results["forces"],
            )
        io2.close()

    def test_bulk_read_variable_appends(self, zarr_path):
        """Verify get_many bulk path works with variable-size appended data."""
        batches = [
            [molecule("H2O") for _ in range(3)],
            [molecule("CH4") for _ in range(2)],
            [molecule("H2") for _ in range(3)],
        ]
        all_frames = [a for batch in batches for a in batch]

        io1 = ZarrBackend(zarr_path)
        for batch in batches:
            io1.extend([atoms_to_dict(a) for a in batch])
        io1.close()

        io2 = ZarrBackend(zarr_path, readonly=True)
        rows = io2.get_many(list(range(len(all_frames))))
        assert len(rows) == len(all_frames)
        for row, atoms in zip(rows, all_frames):
            recovered = dict_to_atoms(row)
            assert len(recovered) == len(atoms)
        io2.close()


# ---------------------------------------------------------------------------
# ASEIO integration
# ---------------------------------------------------------------------------


class TestASEIOIntegration:
    def test_aseio_zarr_extension(self, zarr_path, water_frames):
        io1 = asebytes.ASEIO(zarr_path)
        io1.extend(water_frames)

        io2 = asebytes.ASEIO(zarr_path, readonly=True)
        assert len(io2) == 3
        for i, atoms in enumerate(water_frames):
            recovered = io2[i]
            npt.assert_array_equal(
                recovered.get_atomic_numbers(), atoms.get_atomic_numbers()
            )
            npt.assert_allclose(recovered.get_positions(), atoms.get_positions())


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_index_error(self, zarr_path, water_frames):
        io1 = ZarrBackend(zarr_path)
        io1.extend([atoms_to_dict(water_frames[0])])
        io1.close()

        io2 = ZarrBackend(zarr_path, readonly=True)
        with pytest.raises(IndexError):
            io2.get(1)
        with pytest.raises(IndexError):
            io2.get(-2)
        io2.close()

    def test_negative_index(self, zarr_path, water_frames):
        io1 = ZarrBackend(zarr_path)
        io1.extend([atoms_to_dict(a) for a in water_frames])
        io1.close()

        io2 = ZarrBackend(zarr_path, readonly=True)
        row = io2.get(-1)
        recovered = dict_to_atoms(row)
        npt.assert_allclose(
            recovered.get_positions(), water_frames[-1].get_positions()
        )
        io2.close()

    def test_insert_not_implemented(self, zarr_path):
        io1 = ZarrBackend(zarr_path)
        with pytest.raises(NotImplementedError):
            io1.insert(0, {})
        io1.close()

    def test_delete_not_implemented(self, zarr_path):
        io1 = ZarrBackend(zarr_path)
        with pytest.raises(NotImplementedError):
            io1.delete(0)
        io1.close()


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


class TestContextManager:
    def test_context_manager(self, zarr_path, water_frames):
        with ZarrBackend(zarr_path) as io1:
            io1.extend([atoms_to_dict(a) for a in water_frames])

        with ZarrBackend(zarr_path, readonly=True) as io2:
            assert len(io2) == 3
            row = io2.get(0)
            recovered = dict_to_atoms(row)
            npt.assert_allclose(
                recovered.get_positions(), water_frames[0].get_positions()
            )
