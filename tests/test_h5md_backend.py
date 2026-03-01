"""E2E tests for the H5MD backend.

Every test uses io1 for writing and io2 (fresh instance) for reading.
"""

import h5py
import numpy as np
import numpy.testing as npt
import pytest
from ase.build import molecule, bulk
from ase.calculators.singlepoint import SinglePointCalculator
import ase.collections

import asebytes
from asebytes.h5md._backend import H5MDBackend
from asebytes._convert import atoms_to_dict, dict_to_atoms


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def h5_path(tmp_path):
    return str(tmp_path / "test.h5")


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
    def test_write_read_single_frame(self, h5_path):
        atoms = molecule("H2O")

        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(atoms)])
        io1.close()

        io2 = H5MDBackend(h5_path, readonly=True)
        assert len(io2) == 1
        row = io2.get(0)
        recovered = dict_to_atoms(row)
        npt.assert_array_equal(
            recovered.get_atomic_numbers(), atoms.get_atomic_numbers()
        )
        npt.assert_allclose(recovered.get_positions(), atoms.get_positions())
        io2.close()

    def test_write_read_multiple_frames(self, h5_path, water_frames):
        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(a) for a in water_frames])
        io1.close()

        io2 = H5MDBackend(h5_path, readonly=True)
        assert len(io2) == 3
        for i, atoms in enumerate(water_frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            npt.assert_array_equal(
                recovered.get_atomic_numbers(), atoms.get_atomic_numbers()
            )
            npt.assert_allclose(recovered.get_positions(), atoms.get_positions())
        io2.close()

    def test_append_twice(self, h5_path, water_frames):
        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(water_frames[0])])
        io1.extend([atoms_to_dict(a) for a in water_frames[1:]])
        io1.close()

        io2 = H5MDBackend(h5_path, readonly=True)
        assert len(io2) == 3
        for i, atoms in enumerate(water_frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            npt.assert_allclose(recovered.get_positions(), atoms.get_positions())
        io2.close()

    def test_len_empty_file(self, h5_path):
        io1 = H5MDBackend(h5_path)
        assert len(io1) == 0
        io1.close()


# ---------------------------------------------------------------------------
# Variable particle count
# ---------------------------------------------------------------------------


class TestVariableShape:
    def test_s22_variable_sizes(self, h5_path, s22_frames):
        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(a) for a in s22_frames])
        io1.close()

        io2 = H5MDBackend(h5_path, readonly=True)
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

    def test_growing_system(self, h5_path):
        """System where atom count grows each frame."""
        frames = []
        for n in [2, 5, 10, 3]:
            atoms = molecule("H2O") if n <= 3 else molecule("CH4")
            frames.append(atoms)

        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(a) for a in frames])
        io1.close()

        io2 = H5MDBackend(h5_path, readonly=True)
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
    def test_energy_forces(self, h5_path, water_frames):
        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(a) for a in water_frames])
        io1.close()

        io2 = H5MDBackend(h5_path, readonly=True)
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

    def test_stress(self, h5_path, pbc_frames):
        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(a) for a in pbc_frames])
        io1.close()

        io2 = H5MDBackend(h5_path, readonly=True)
        for i, atoms in enumerate(pbc_frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            npt.assert_allclose(
                recovered.calc.results["stress"],
                atoms.calc.results["stress"],
            )
        io2.close()

    def test_s22_with_calc_variable(self, h5_path, s22_with_calc):
        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(a) for a in s22_with_calc])
        io1.close()

        io2 = H5MDBackend(h5_path, readonly=True)
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
    def test_periodic_system(self, h5_path, pbc_frames):
        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(a) for a in pbc_frames])
        io1.close()

        io2 = H5MDBackend(h5_path, readonly=True)
        for i, atoms in enumerate(pbc_frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            npt.assert_allclose(recovered.get_cell().array, atoms.get_cell().array)
            npt.assert_array_equal(recovered.get_pbc(), atoms.get_pbc())
        io2.close()

    def test_mixed_pbc(self, h5_path, mixed_pbc_frames):
        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(a) for a in mixed_pbc_frames])
        io1.close()

        io2 = H5MDBackend(h5_path, readonly=True)
        for i, atoms in enumerate(mixed_pbc_frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            npt.assert_array_equal(recovered.get_pbc(), atoms.get_pbc())
            npt.assert_allclose(recovered.get_cell().array, atoms.get_cell().array)
        io2.close()


# ---------------------------------------------------------------------------
# Info, arrays, velocities
# ---------------------------------------------------------------------------


class TestInfoAndArrays:
    def test_custom_info_and_arrays(self, h5_path, info_arrays_calc_frames):
        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(a) for a in info_arrays_calc_frames])
        io1.close()

        io2 = H5MDBackend(h5_path, readonly=True)
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
            npt.assert_allclose(recovered.get_velocities(), atoms.get_velocities())
        io2.close()


# ---------------------------------------------------------------------------
# Column reads
# ---------------------------------------------------------------------------


class TestColumnReads:
    def test_read_energy_column(self, h5_path, water_frames):
        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(a) for a in water_frames])
        io1.close()

        io2 = H5MDBackend(h5_path, readonly=True)
        energies = io2.get_column("calc.energy")
        assert len(energies) == 3
        for i, atoms in enumerate(water_frames):
            npt.assert_allclose(energies[i], atoms.calc.results["energy"])
        io2.close()

    def test_keys_list(self, h5_path, water_frames):
        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(a) for a in water_frames])
        io1.close()

        io2 = H5MDBackend(h5_path, readonly=True)
        cols = io2.keys(0)
        assert "arrays.positions" in cols
        assert "arrays.numbers" in cols
        assert "calc.energy" in cols
        assert "calc.forces" in cols
        io2.close()


# ---------------------------------------------------------------------------
# H5MD file structure validation
# ---------------------------------------------------------------------------


class TestH5MDStructure:
    def test_h5md_metadata(self, h5_path, water_frames):
        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(water_frames[0])])
        io1.close()

        with h5py.File(h5_path, "r") as f:
            assert "h5md" in f
            npt.assert_array_equal(f["h5md"].attrs["version"], [1, 1])
            assert "author" in f["h5md"]
            assert "creator" in f["h5md"]

    def test_particles_group_structure(self, h5_path, water_frames):
        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(water_frames[0])])
        io1.close()

        with h5py.File(h5_path, "r") as f:
            assert "particles/atoms" in f
            p = f["particles/atoms"]
            # Species (numbers)
            assert "species" in p
            assert "value" in p["species"]
            assert "step" in p["species"]
            assert "time" in p["species"]
            # Position
            assert "position" in p
            assert "value" in p["position"]
            # Box
            assert "box" in p
            assert p["box"].attrs["dimension"] == 3

    def test_author_metadata_not_set(self, h5_path, water_frames):
        """Author attrs are absent when kwargs are not provided."""
        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(water_frames[0])])
        io1.close()

        with h5py.File(h5_path, "r") as f:
            author = f["h5md/author"]
            assert "name" not in author.attrs
            assert "email" not in author.attrs

    def test_author_metadata_set(self, h5_path, water_frames):
        """Author attrs are written when kwargs are provided."""
        io1 = H5MDBackend(
            h5_path, author_name="Alice", author_email="alice@example.com"
        )
        io1.extend([atoms_to_dict(water_frames[0])])
        io1.close()

        with h5py.File(h5_path, "r") as f:
            assert f["h5md/author"].attrs["name"] == "Alice"
            assert f["h5md/author"].attrs["email"] == "alice@example.com"

    def test_author_metadata_partial(self, h5_path, water_frames):
        """Only provided author attrs are written."""
        io1 = H5MDBackend(h5_path, author_name="Bob")
        io1.extend([atoms_to_dict(water_frames[0])])
        io1.close()

        with h5py.File(h5_path, "r") as f:
            assert f["h5md/author"].attrs["name"] == "Bob"
            assert "email" not in f["h5md/author"].attrs

    def test_creator_version_dynamic(self, h5_path, water_frames):
        """Creator version matches the installed asebytes version."""
        import asebytes

        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(water_frames[0])])
        io1.close()

        with h5py.File(h5_path, "r") as f:
            assert f["h5md/creator"].attrs["name"] == "asebytes"
            assert f["h5md/creator"].attrs["version"] == asebytes.__version__

    def test_list_groups(self, h5_path, water_frames):
        """list_groups returns available particles groups."""
        io1 = H5MDBackend(h5_path, group="atoms")
        io1.extend([atoms_to_dict(water_frames[0])])
        io1.close()

        groups = H5MDBackend.list_groups(h5_path)
        assert groups == ["atoms"]

    def test_list_groups_multiple(self, h5_path, water_frames):
        """list_groups returns multiple groups when present."""
        with h5py.File(h5_path, "a") as f:
            io1 = H5MDBackend(file_handle=f, group="atoms")
            io1.extend([atoms_to_dict(water_frames[0])])
            io2 = H5MDBackend(file_handle=f, group="solvent")
            io2.extend([atoms_to_dict(water_frames[0])])

        groups = H5MDBackend.list_groups(h5_path)
        assert "atoms" in groups
        assert "solvent" in groups

    def test_list_groups_empty(self, h5_path):
        """list_groups returns empty list for non-H5MD file."""
        with h5py.File(h5_path, "w"):
            pass
        assert H5MDBackend.list_groups(h5_path) == []

    def test_origin_attributes(self, h5_path, info_arrays_calc_frames):
        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(info_arrays_calc_frames[0])])
        io1.close()

        with h5py.File(h5_path, "r") as f:
            p = f["particles/atoms"]
            assert p["species"].attrs["ASE_ENTRY_ORIGIN"] == "atoms"
            assert p["position"].attrs["ASE_ENTRY_ORIGIN"] == "atoms"
            assert p["force"].attrs["ASE_ENTRY_ORIGIN"] == "calc"
            assert p["mlip_forces"].attrs["ASE_ENTRY_ORIGIN"] == "arrays"


# ---------------------------------------------------------------------------
# ZnH5MD cross-compatibility
# ---------------------------------------------------------------------------


class TestZnH5MDCompat:
    """Write with asebytes → read with znh5md, and vice versa."""

    def test_write_asebytes_read_znh5md(self, h5_path, water_frames):
        znh5md = pytest.importorskip("znh5md")

        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(a) for a in water_frames])
        io1.close()

        io2 = znh5md.IO(h5_path)
        assert len(io2) == 3
        for i, atoms in enumerate(water_frames):
            recovered = io2[i]
            npt.assert_array_equal(
                recovered.get_atomic_numbers(), atoms.get_atomic_numbers()
            )
            npt.assert_allclose(recovered.get_positions(), atoms.get_positions())

    def test_write_znh5md_read_asebytes(self, h5_path, water_frames):
        znh5md = pytest.importorskip("znh5md")

        io1 = znh5md.IO(h5_path)
        io1.extend(water_frames)

        io2 = H5MDBackend(h5_path, readonly=True)
        assert len(io2) == 3
        for i, atoms in enumerate(water_frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            npt.assert_array_equal(
                recovered.get_atomic_numbers(), atoms.get_atomic_numbers()
            )
            npt.assert_allclose(recovered.get_positions(), atoms.get_positions())
        io2.close()

    def test_write_znh5md_read_asebytes_with_calc(self, h5_path, s22_with_calc):
        znh5md = pytest.importorskip("znh5md")

        io1 = znh5md.IO(h5_path)
        io1.extend(s22_with_calc)

        io2 = H5MDBackend(h5_path, readonly=True)
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

    def test_write_asebytes_read_znh5md_variable_shape(self, h5_path, s22_frames):
        znh5md = pytest.importorskip("znh5md")

        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(a) for a in s22_frames])
        io1.close()

        io2 = znh5md.IO(h5_path)
        assert len(io2) == len(s22_frames)
        for i, atoms in enumerate(s22_frames):
            recovered = io2[i]
            assert len(recovered) == len(atoms)
            npt.assert_array_equal(
                recovered.get_atomic_numbers(), atoms.get_atomic_numbers()
            )

    def test_write_znh5md_read_asebytes_variable_shape(self, h5_path, s22_frames):
        znh5md = pytest.importorskip("znh5md")

        io1 = znh5md.IO(h5_path)
        io1.extend(s22_frames)

        io2 = H5MDBackend(h5_path, readonly=True)
        assert len(io2) == len(s22_frames)
        for i, atoms in enumerate(s22_frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            assert len(recovered) == len(atoms)
            npt.assert_array_equal(
                recovered.get_atomic_numbers(), atoms.get_atomic_numbers()
            )
        io2.close()

    def test_write_znh5md_read_asebytes_info(self, h5_path, info_arrays_calc_frames):
        znh5md = pytest.importorskip("znh5md")

        io1 = znh5md.IO(h5_path)
        io1.extend(info_arrays_calc_frames)

        io2 = H5MDBackend(h5_path, readonly=True)
        for i, atoms in enumerate(info_arrays_calc_frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            npt.assert_allclose(
                recovered.info["mlip_energy"], atoms.info["mlip_energy"]
            )
            assert recovered.info["collection"] == "s22"
        io2.close()


# ---------------------------------------------------------------------------
# Connectivity (molify)
# ---------------------------------------------------------------------------


class TestConnectivity:
    """Round-trip tests for molify connectivity data."""

    def test_connectivity_round_trip(self, h5_path):
        molify = pytest.importorskip("molify")

        frames = molify.smiles2conformers("CCO", numConfs=3)
        assert "connectivity" in frames[0].info

        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(a) for a in frames])
        io1.close()

        # Verify H5MD structure
        with h5py.File(h5_path, "r") as f:
            assert "connectivity/atoms/bonds" in f
            bonds_grp = f["connectivity/atoms/bonds"]
            assert bonds_grp["value"].dtype == np.int32
            assert "particles_group" in bonds_grp.attrs
            assert "observables/atoms/connectivity" not in f

        io2 = H5MDBackend(h5_path, readonly=True)
        for i, atoms in enumerate(frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            # connectivity survives (tuples become lists in JSON)
            orig = [list(t) for t in atoms.info["connectivity"]]
            assert recovered.info["connectivity"] == orig
            npt.assert_array_equal(
                recovered.get_atomic_numbers(), atoms.get_atomic_numbers()
            )
            npt.assert_allclose(
                recovered.get_positions(), atoms.get_positions(), atol=1e-10
            )
        io2.close()

    def test_connectivity_with_smiles(self, h5_path):
        molify = pytest.importorskip("molify")

        frames = molify.smiles2conformers("c1ccccc1", numConfs=2)  # benzene
        assert "smiles" in frames[0].info
        assert "connectivity" in frames[0].info

        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(a) for a in frames])
        io1.close()

        # Verify H5MD structure
        with h5py.File(h5_path, "r") as f:
            assert "connectivity/atoms/bonds" in f
            assert f["connectivity/atoms/bonds"]["value"].dtype == np.int32
            assert "particles_group" in f["connectivity/atoms/bonds"].attrs

        io2 = H5MDBackend(h5_path, readonly=True)
        for i, atoms in enumerate(frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            assert recovered.info["smiles"] == atoms.info["smiles"]
            assert len(recovered.info["connectivity"]) == len(
                atoms.info["connectivity"]
            )
        io2.close()

    def test_connectivity_znh5md_to_asebytes(self, h5_path):
        molify = pytest.importorskip("molify")
        znh5md = pytest.importorskip("znh5md")

        frames = molify.smiles2conformers("CCO", numConfs=3)

        io1 = znh5md.IO(h5_path)
        io1.extend(frames)

        # znh5md stores connectivity as float64 array (n_bonds, 3),
        # not JSON — so both readers return numpy arrays
        io2 = H5MDBackend(h5_path, readonly=True)
        for i, atoms in enumerate(frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            orig = np.array([list(t) for t in atoms.info["connectivity"]])
            npt.assert_array_equal(recovered.info["connectivity"], orig)
        io2.close()

    def test_connectivity_h5md_structure(self, h5_path):
        """Verify /connectivity/atoms/bonds exists with correct dtype and attributes."""
        molify = pytest.importorskip("molify")

        frames = molify.smiles2conformers("CCO", numConfs=3)

        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(a) for a in frames])
        io1.close()

        with h5py.File(h5_path, "r") as f:
            assert "connectivity" in f
            assert "atoms" in f["connectivity"]
            atoms_conn = f["connectivity/atoms"]
            assert "bonds" in atoms_conn
            bonds_grp = atoms_conn["bonds"]
            assert "value" in bonds_grp
            assert "step" in bonds_grp
            assert "time" in bonds_grp
            ds = bonds_grp["value"]
            assert ds.dtype == np.int32
            assert ds.shape[0] == len(frames)
            assert ds.shape[2] == 2
            # particles_group reference
            assert "particles_group" in bonds_grp.attrs
            # bond_orders
            assert "bond_orders" in atoms_conn
            ds_o = atoms_conn["bond_orders/value"]
            assert ds_o.dtype == np.float64
            assert ds_o.shape[0] == len(frames)

    def test_connectivity_variable_molecules(self, h5_path):
        """Write frames with different molecules (different bond counts)."""
        molify = pytest.importorskip("molify")

        ethanol = molify.smiles2conformers("CCO", numConfs=2)
        benzene = molify.smiles2conformers("c1ccccc1", numConfs=2)
        frames = ethanol + benzene

        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(a) for a in frames])
        io1.close()

        io2 = H5MDBackend(h5_path, readonly=True)
        assert len(io2) == 4
        for i, atoms in enumerate(frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            orig = [list(t) for t in atoms.info["connectivity"]]
            assert recovered.info["connectivity"] == orig
        io2.close()

    def test_connectivity_mixed_with_without(self, h5_path):
        """Some frames have connectivity, some don't."""
        molify = pytest.importorskip("molify")
        from ase.build import molecule as ase_molecule

        mol_frames = molify.smiles2conformers("CCO", numConfs=2)
        plain = ase_molecule("H2O")
        # plain has no connectivity
        frames_data = (
            [atoms_to_dict(mol_frames[0])]
            + [atoms_to_dict(plain)]
            + [atoms_to_dict(mol_frames[1])]
        )

        io1 = H5MDBackend(h5_path)
        io1.extend(frames_data)
        io1.close()

        io2 = H5MDBackend(h5_path, readonly=True)
        assert len(io2) == 3
        # Frame 0 has connectivity
        row0 = io2.get(0)
        assert "info.connectivity" in row0
        orig0 = [list(t) for t in mol_frames[0].info["connectivity"]]
        assert row0["info.connectivity"] == orig0
        # Frame 1 (plain H2O) has no connectivity
        row1 = io2.get(1)
        assert "info.connectivity" not in row1
        # Frame 2 has connectivity
        row2 = io2.get(2)
        assert "info.connectivity" in row2
        orig2 = [list(t) for t in mol_frames[1].info["connectivity"]]
        assert row2["info.connectivity"] == orig2
        io2.close()

    def test_connectivity_mixed_molecules_separate_appends(self, h5_path):
        """Write ethanol→benzene→water in separate appends, verify round-trip."""
        molify = pytest.importorskip("molify")

        ethanol = molify.smiles2conformers("CCO", numConfs=1)
        benzene = molify.smiles2conformers("c1ccccc1", numConfs=1)
        water = molify.smiles2conformers("O", numConfs=1)

        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(a) for a in ethanol])
        io1.extend([atoms_to_dict(a) for a in benzene])
        io1.extend([atoms_to_dict(a) for a in water])
        io1.close()

        all_frames = ethanol + benzene + water
        io2 = H5MDBackend(h5_path, readonly=True)
        assert len(io2) == 3
        for i, atoms in enumerate(all_frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            orig = [list(t) for t in atoms.info["connectivity"]]
            assert recovered.info["connectivity"] == orig
            npt.assert_array_equal(
                recovered.get_atomic_numbers(), atoms.get_atomic_numbers()
            )
        io2.close()


# ---------------------------------------------------------------------------
# Variable-size appends (multiple extend calls)
# ---------------------------------------------------------------------------


class TestVariableSizeAppends:
    """Test alternating larger/smaller atom counts across separate appends."""

    def test_append_larger_smaller_larger(self, h5_path):
        """Append H2O (3) → CH4 (5) → H2 (2) → benzene (12)."""
        batches = [
            [molecule("H2O") for _ in range(3)],
            [molecule("CH4") for _ in range(2)],
            [molecule("H2") for _ in range(3)],
            [molecule("C6H6") for _ in range(2)],
        ]
        all_frames = [a for batch in batches for a in batch]

        io1 = H5MDBackend(h5_path)
        for batch in batches:
            io1.extend([atoms_to_dict(a) for a in batch])
        io1.close()

        io2 = H5MDBackend(h5_path, readonly=True)
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
        path = str(tmp_path / "test.h5")
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

    def test_append_with_calc_variable_sizes(self, h5_path):
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

        io1 = H5MDBackend(h5_path)
        for batch in batches:
            io1.extend([atoms_to_dict(a) for a in batch])
        io1.close()

        io2 = H5MDBackend(h5_path, readonly=True)
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

    def test_append_variable_interop_asebytes_to_znh5md(self, h5_path):
        """Write variable appends with asebytes, read with znh5md."""
        znh5md = pytest.importorskip("znh5md")

        batches = [
            [molecule("H2O") for _ in range(3)],
            [molecule("CH4") for _ in range(2)],
            [molecule("H2") for _ in range(3)],
        ]
        all_frames = [a for batch in batches for a in batch]

        io1 = H5MDBackend(h5_path)
        for batch in batches:
            io1.extend([atoms_to_dict(a) for a in batch])
        io1.close()

        io2 = znh5md.IO(h5_path)
        assert len(io2) == len(all_frames)
        for i, atoms in enumerate(all_frames):
            recovered = io2[i]
            assert len(recovered) == len(atoms)
            npt.assert_array_equal(
                recovered.get_atomic_numbers(), atoms.get_atomic_numbers()
            )

    def test_append_variable_interop_znh5md_to_asebytes(self, h5_path):
        """Write variable extends with znh5md, read with asebytes."""
        znh5md = pytest.importorskip("znh5md")

        batches = [
            [molecule("H2O") for _ in range(3)],
            [molecule("CH4") for _ in range(2)],
            [molecule("H2") for _ in range(3)],
        ]
        all_frames = [a for batch in batches for a in batch]

        io1 = znh5md.IO(h5_path)
        for batch in batches:
            io1.extend(batch)

        io2 = H5MDBackend(h5_path, readonly=True)
        assert len(io2) == len(all_frames)
        for i, atoms in enumerate(all_frames):
            row = io2.get(i)
            recovered = dict_to_atoms(row)
            assert len(recovered) == len(atoms)
            npt.assert_array_equal(
                recovered.get_atomic_numbers(), atoms.get_atomic_numbers()
            )
        io2.close()

    def test_bulk_read_variable_appends(self, h5_path):
        """Verify get_many bulk path works with variable-size appended data."""
        batches = [
            [molecule("H2O") for _ in range(3)],
            [molecule("CH4") for _ in range(2)],
            [molecule("H2") for _ in range(3)],
        ]
        all_frames = [a for batch in batches for a in batch]

        io1 = H5MDBackend(h5_path)
        for batch in batches:
            io1.extend([atoms_to_dict(a) for a in batch])
        io1.close()

        io2 = H5MDBackend(h5_path, readonly=True)
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
    def test_aseio_h5_extension(self, h5_path, water_frames):
        io1 = asebytes.ASEIO(h5_path)
        io1.extend(water_frames)

        io2 = asebytes.ASEIO(h5_path, readonly=True)
        assert len(io2) == 3
        for i, atoms in enumerate(water_frames):
            recovered = io2[i]
            npt.assert_array_equal(
                recovered.get_atomic_numbers(), atoms.get_atomic_numbers()
            )
            npt.assert_allclose(recovered.get_positions(), atoms.get_positions())

    def test_aseio_h5md_extension(self, tmp_path, water_frames):
        path = str(tmp_path / "test.h5md")
        io1 = asebytes.ASEIO(path)
        io1.extend(water_frames)

        io2 = asebytes.ASEIO(path, readonly=True)
        assert len(io2) == 3


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_index_error(self, h5_path, water_frames):
        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(water_frames[0])])
        io1.close()

        io2 = H5MDBackend(h5_path, readonly=True)
        with pytest.raises(IndexError):
            io2.get(1)
        with pytest.raises(IndexError):
            io2.get(-2)
        io2.close()

    def test_negative_index(self, h5_path, water_frames):
        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(a) for a in water_frames])
        io1.close()

        io2 = H5MDBackend(h5_path, readonly=True)
        row = io2.get(-1)
        recovered = dict_to_atoms(row)
        npt.assert_allclose(recovered.get_positions(), water_frames[-1].get_positions())
        io2.close()

    def test_insert_not_implemented(self, h5_path):
        io1 = H5MDBackend(h5_path)
        with pytest.raises(NotImplementedError):
            io1.insert(0, {})
        io1.close()

    def test_delete_not_implemented(self, h5_path):
        io1 = H5MDBackend(h5_path)
        with pytest.raises(NotImplementedError):
            io1.delete(0)
        io1.close()

    def test_file_handle(self, h5_path, water_frames):
        """Test file_handle parameter for fsspec compatibility."""
        io1 = H5MDBackend(h5_path)
        io1.extend([atoms_to_dict(a) for a in water_frames])
        io1.close()

        with h5py.File(h5_path, "r") as f:
            io2 = H5MDBackend(file_handle=f, readonly=True)
            assert len(io2) == 3
            row = io2.get(0)
            recovered = dict_to_atoms(row)
            npt.assert_allclose(
                recovered.get_positions(), water_frames[0].get_positions()
            )


class TestShortColumns:
    """Test handling of columns shorter than requested indices."""

    def test_get_many_with_short_columns(self, h5_path, water_frames):
        """get_many() should skip columns shorter than requested indices.

        This matches the behavior of get() which skips short columns.
        """
        io1 = H5MDBackend(h5_path)
        # Write 3 frames first
        io1.extend([atoms_to_dict(a) for a in water_frames])
        io1.close()

        # Manually add a short column (only 2 entries vs 3 frames)
        with h5py.File(h5_path, "r+") as f:
            grp = f.create_group("observables/atoms/short_col")
            grp.create_dataset("value", data=[1.0, 2.0])  # Only 2 values
            grp.create_dataset("step", data=1)
            grp.create_dataset("time", data=1.0)
            grp.attrs["asebytes_origin"] = "calc"

        # Now get_many should not crash when accessing index 2
        io2 = H5MDBackend(h5_path, readonly=True)
        # Reading indices 0, 1, 2 - but short_col only has indices 0, 1
        rows = io2.get_many([0, 1, 2])
        assert len(rows) == 3
        # All rows should have positions
        for row in rows:
            assert "arrays.positions" in row
        # The short column should only appear in rows where it exists
        # (indices 0 and 1)
        # Note: after the fix, rows[2] should NOT have calc.short_col
        io2.close()
