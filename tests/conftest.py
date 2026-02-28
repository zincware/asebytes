import pathlib

import ase
import ase.build
import ase.collections
import molify
import numpy as np
import pytest
from ase.calculators.singlepoint import SinglePointCalculator

LEMAT_PATH = pathlib.Path(__file__).parent / "data" / "lemat_1000.lmdb"

EXTENSIONS = [".lmdb", ".h5", ".zarr"]


@pytest.fixture(params=EXTENSIONS)
def db_path(tmp_path, request):
    """Yield a fresh path with each writable-backend extension."""
    return str(tmp_path / f"test{request.param}")


@pytest.fixture
def ethanol() -> list[ase.Atoms]:
    """Return 1000 ethanol conformers with calculator results."""
    frames = molify.smiles2conformers("CCO", numConfs=1000)
    rng = np.random.RandomState(42)
    for i, atoms in enumerate(frames):
        n = len(atoms)
        atoms.calc = SinglePointCalculator(atoms)
        atoms.calc.results = {
            "energy": float(-i * 0.1),
            "forces": rng.randn(n, 3) * 0.01,
            "stress": rng.randn(6) * 0.001,
        }
    return frames


@pytest.fixture(scope="session")
def lemat() -> list[ase.Atoms]:
    """Return 1000 LeMat-Traj frames (positions, cell, pbc, calc only).

    Info metadata is stripped and stress is normalized to Voigt (6,) form
    so that all backends receive identical data for fair comparison.
    """
    if not LEMAT_PATH.exists():
        pytest.skip(
            "LeMat-Traj data not available. "
            "Run: uv run python scripts/download_benchmark_data.py"
        )
    from asebytes import ASEIO

    db = ASEIO(str(LEMAT_PATH), readonly=True)
    clean = []
    for a in db:
        b = ase.Atoms(
            numbers=a.numbers, positions=a.positions, cell=a.cell, pbc=a.pbc
        )
        if a.calc is not None:
            results = {}
            for k, v in a.calc.results.items():
                if k == "stress" and isinstance(v, np.ndarray) and v.shape == (3, 3):
                    v = np.array(
                        [v[0, 0], v[1, 1], v[2, 2], v[1, 2], v[0, 2], v[0, 1]]
                    )
                results[k] = v
            calc = SinglePointCalculator(b)
            calc.results = results
            b.calc = calc
        clean.append(b)
    return clean


@pytest.fixture
def simple_atoms() -> ase.Atoms:
    """Return a simple single-atom Atoms object."""
    return ase.Atoms("H", positions=[[0, 0, 0]])


@pytest.fixture
def h2o_atoms() -> ase.Atoms:
    """Return a water molecule."""
    return ase.Atoms("H2O", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]])


@pytest.fixture
def atoms_with_info() -> ase.Atoms:
    """Return Atoms object with various info entries."""
    atoms = ase.Atoms("H2", positions=[[0, 0, 0], [1, 0, 0]])
    atoms.info["string_data"] = "test"
    atoms.info["int_data"] = 42
    atoms.info["float_data"] = 3.14
    atoms.info["bool_data"] = True
    atoms.info["list_data"] = [1, 2, 3]
    atoms.info["dict_data"] = {"key": "value"}
    atoms.info["numpy_data"] = np.array([1, 2, 3])
    return atoms


@pytest.fixture
def atoms_with_calc() -> ase.Atoms:
    """Return Atoms object with calculator and results."""
    from ase.calculators.singlepoint import SinglePointCalculator

    atoms = ase.Atoms("H2", positions=[[0, 0, 0], [1, 0, 0]])
    atoms.calc = SinglePointCalculator(atoms)
    atoms.calc.results = {
        "energy": -10.5,
        "forces": np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]),
    }
    return atoms


@pytest.fixture
def empty_atoms() -> ase.Atoms:
    """Return empty Atoms object with no atoms."""
    return ase.Atoms()


@pytest.fixture
def atoms_with_pbc() -> ase.Atoms:
    """Return Atoms object with periodic boundary conditions."""
    atoms = ase.Atoms(
        "H",
        positions=[[0, 0, 0]],
        cell=[[10, 0, 0], [0, 10, 0], [0, 0, 10]],
        pbc=[True, True, False],
    )
    return atoms


@pytest.fixture
def atoms_with_constraints() -> ase.Atoms:
    """Return Atoms object with constraints."""
    from ase.constraints import FixAtoms

    atoms = ase.Atoms("H2O", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]])
    constraint = FixAtoms(indices=[0, 2])
    atoms.set_constraint(constraint)
    return atoms


@pytest.fixture
def bytesio_instance(tmp_path):
    """Return a BlobIO instance for testing."""
    import asebytes

    return asebytes.BlobIO(asebytes.LMDBBlobBackend(str(tmp_path / "test.lmdb")))


@pytest.fixture
def aseio_instance(tmp_path):
    """Return an ASEIO instance for testing."""
    import asebytes

    return asebytes.ASEIO(str(tmp_path / "test.lmdb"))


# ---------------------------------------------------------------------------
# ZnH5MD-ported fixtures: diverse datasets for multi-backend round-trip tests
# ---------------------------------------------------------------------------


@pytest.fixture
def s22() -> list[ase.Atoms]:
    return list(ase.collections.s22)


@pytest.fixture
def s22_energy() -> list[ase.Atoms]:
    rng = np.random.RandomState(10)
    images = []
    for atoms in ase.collections.s22:
        calc = SinglePointCalculator(atoms, energy=rng.rand())
        atoms.calc = calc
        images.append(atoms)
    return images


@pytest.fixture
def s22_energy_forces() -> list[ase.Atoms]:
    rng = np.random.RandomState(11)
    images = []
    for atoms in ase.collections.s22:
        calc = SinglePointCalculator(
            atoms, energy=rng.rand(), forces=rng.rand(len(atoms), 3)
        )
        atoms.calc = calc
        images.append(atoms)
    return images


@pytest.fixture
def s22_all_properties() -> list[ase.Atoms]:
    rng = np.random.RandomState(12)
    images = []
    for atoms in ase.collections.s22:
        energy = rng.rand()
        energies = rng.rand(len(atoms))
        free_energy = rng.rand()
        forces = rng.rand(len(atoms), 3)
        stress = rng.rand(6)
        stresses = rng.rand(len(atoms), 6)
        dipole = rng.rand(3)
        magmom = rng.rand()
        magmoms = rng.rand(len(atoms))
        dielectric_tensor = rng.rand(3, 3)
        born_effective_charges = rng.rand(len(atoms), 3)
        polarization = rng.rand(3)

        calc = SinglePointCalculator(
            atoms,
            energy=energy,
            energies=energies,
            free_energy=free_energy,
            forces=forces,
            stress=stress,
            stresses=stresses,
            dipole=dipole,
            magmom=magmom,
            magmoms=magmoms,
            dielectric_tensor=dielectric_tensor,
            born_effective_charges=born_effective_charges,
            polarization=polarization,
        )
        atoms.calc = calc
        images.append(atoms)
    return images


@pytest.fixture
def s22_info_arrays_calc() -> list[ase.Atoms]:
    rng = np.random.RandomState(13)
    images = []
    for atoms in ase.collections.s22:
        atoms.info.update(
            {
                "mlip_energy": rng.rand(),
                "mlip_energy_2": rng.rand(),
                "mlip_stress": rng.rand(6),
                "collection": "s22",
                "metadata": {"author": "Jane Doe", "date": "2021-09-01"},
                "lst": [1, 2, 3],
            }
        )
        atoms.new_array("mlip_forces", rng.rand(len(atoms), 3))
        atoms.new_array("mlip_forces_2", rng.rand(len(atoms), 3))
        atoms.set_velocities(rng.rand(len(atoms), 3))
        calc = SinglePointCalculator(
            atoms, energy=rng.rand(), forces=rng.rand(len(atoms), 3)
        )
        atoms.calc = calc
        images.append(atoms)
    return images


@pytest.fixture
def s22_mixed_pbc_cell() -> list[ase.Atoms]:
    rng = np.random.RandomState(14)
    images = []
    for atoms in ase.collections.s22:
        atoms.set_pbc(rng.rand(3) > 0.5)
        atoms.set_cell(rng.rand(3, 3))
        atoms.info["mlip_energy"] = rng.rand()
        atoms.new_array("mlip_forces", rng.rand(len(atoms), 3))
        images.append(atoms)
    return images


@pytest.fixture
def s22_illegal_calc_results() -> list[ase.Atoms]:
    rng = np.random.RandomState(15)
    images = []
    for atoms in ase.collections.s22:
        atoms.calc = SinglePointCalculator(atoms)
        atoms.calc.results["mlip_energy"] = rng.rand()
        atoms.calc.results["dict"] = {"author": "Jane Doe", "date": "2021-09-01"}
        atoms.calc.results["float"] = 3.14
        atoms.calc.results["int"] = 42
        atoms.calc.results["list"] = [1, 2, 3]
        atoms.calc.results["str"] = '{"author": "Jane Doe", "date": "2021-09-01"}'
        atoms.calc.results["list_array"] = [rng.rand(3), rng.rand(3)]
        atoms.calc.results["list_str"] = ["Jane Doe", "John Doe"]
        images.append(atoms)
    return images


@pytest.fixture
def water() -> list[ase.Atoms]:
    """Get a dataset without positions (all at origin)."""
    return [ase.Atoms("H2O")]


@pytest.fixture
def s22_nested_calc() -> list[ase.Atoms]:
    rng = np.random.RandomState(16)
    images = []
    for atoms in ase.collections.s22:
        atoms.calc = SinglePointCalculator(atoms)
        atoms.calc.results["forces"] = rng.rand(len(atoms), 3)
        atoms.calc.results["forces_contributions"] = [
            [
                rng.rand(len(atoms), 3),
                rng.rand(len(atoms), 3),
            ]
        ]
        images.append(atoms)
    return images


@pytest.fixture
def full_water(water) -> ase.Atoms:
    """Get a water molecule with calc, info, and arrays."""
    w = water[0]
    w.calc = SinglePointCalculator(w, energy=1.0, forces=np.zeros((len(w), 3)))
    w.info["smiles"] = "O"
    w.arrays["mlip_forces"] = np.zeros((len(w), 3))
    return w


@pytest.fixture
def s22_info_arrays_calc_missing_inbetween() -> list[ase.Atoms]:
    rng = np.random.RandomState(17)
    images = []
    for atoms in ase.collections.s22:
        if rng.random() > 0.5:
            atoms.info.update({"mlip_energy": rng.rand()})
        if rng.random() > 0.5:
            atoms.new_array("mlip_forces", rng.rand(len(atoms), 3))
        if rng.random() > 0.5:
            calc = SinglePointCalculator(atoms)
            set_calc = False
            if rng.random() > 0.5:
                calc.results["energy"] = rng.rand()
                set_calc = True
            if rng.random() > 0.5:
                calc.results["forces"] = rng.rand(len(atoms), 3)
                set_calc = True
            if set_calc:
                atoms.calc = calc
        images.append(atoms)
    return images


# ---------------------------------------------------------------------------
# Universal parametrized backend fixtures (full matrix: native + adapters)
# ---------------------------------------------------------------------------

from asebytes._adapters import (
    BlobToObjectReadWriteAdapter,
    ObjectToBlobReadWriteAdapter,
)
from asebytes.lmdb import LMDBBlobBackend


def _lmdb_blob(tmp_path):
    return LMDBBlobBackend(str(tmp_path / "uni.lmdb"))


def _lmdb_object(tmp_path):
    return BlobToObjectReadWriteAdapter(_lmdb_blob(tmp_path))


def _zarr_object(tmp_path):
    from asebytes.zarr import ZarrBackend
    return ZarrBackend(str(tmp_path / "uni.zarr"))


def _zarr_blob(tmp_path):
    return ObjectToBlobReadWriteAdapter(_zarr_object(tmp_path))


def _h5md_object(tmp_path):
    from asebytes.h5md import H5MDBackend
    return H5MDBackend(str(tmp_path / "uni.h5"))


def _h5md_blob(tmp_path):
    return ObjectToBlobReadWriteAdapter(_h5md_object(tmp_path))


@pytest.fixture(params=[
    pytest.param(_lmdb_blob, id="lmdb-blob-native"),
    pytest.param(_zarr_blob, id="zarr-blob-via-adapter"),
    pytest.param(_h5md_blob, id="h5md-blob-via-adapter"),
])
def uni_blob_backend(tmp_path, request):
    """Universal blob-level backend fixture across all storage formats."""
    return request.param(tmp_path)


@pytest.fixture(params=[
    pytest.param(_lmdb_object, id="lmdb-object-via-adapter"),
    pytest.param(_zarr_object, id="zarr-object-native"),
    pytest.param(_h5md_object, id="h5md-object-native"),
])
def uni_object_backend(tmp_path, request):
    """Universal object-level backend fixture across all storage formats."""
    return request.param(tmp_path)
