import os

import ase
import ase.build
import ase.collections
import molify
import numpy as np
import pytest
from ase.calculators.singlepoint import SinglePointCalculator
from ase.constraints import FixAtoms

# ---------------------------------------------------------------------------
# Network backend URIs (shared across all test modules)
# ---------------------------------------------------------------------------

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://root:example@localhost:27017")
REDIS_URI = os.environ.get("REDIS_URI", "redis://localhost:6379")


@pytest.fixture
def mongo_uri() -> str:
    """Return the MongoDB connection URI."""
    return MONGO_URI


@pytest.fixture
def redis_uri() -> str:
    """Return the Redis connection URI."""
    return REDIS_URI


EXTENSIONS = [".lmdb", ".h5", ".zarr"]


@pytest.fixture(params=EXTENSIONS)
def db_path(tmp_path, request):
    """Yield a fresh path with each writable-backend extension."""
    return str(tmp_path / f"test{request.param}")


def _attach_full_properties(
    frames: list[ase.Atoms], seed: int = 42
) -> list[ase.Atoms]:
    """Attach full properties to each Atoms frame for benchmark realism.

    Adds: SinglePointCalculator (energy, forces, stress), FixAtoms constraint,
    custom info (step, label), custom array (charges).
    """
    rng = np.random.RandomState(seed)
    for i, atoms in enumerate(frames):
        n = len(atoms)
        # Calculator with energy, forces, stress
        atoms.calc = SinglePointCalculator(atoms)
        atoms.calc.results = {
            "energy": float(-i * 0.1),
            "forces": rng.randn(n, 3) * 0.01,
            "stress": rng.randn(6) * 0.001,
        }
        # Constraint
        atoms.set_constraint(FixAtoms(indices=[0]))
        # Custom info
        atoms.info["step"] = i
        atoms.info["label"] = f"frame_{i}"
        # Custom array
        atoms.new_array("charges", rng.randn(n))
    return frames


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


# ---------------------------------------------------------------------------
# Session-scoped benchmark data fixtures (2x2: frames x atoms)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def ethanol_100() -> list[ase.Atoms]:
    """100 ethanol conformers (~9 atoms) with full properties."""
    frames = molify.smiles2conformers("CCO", numConfs=100)
    return _attach_full_properties(frames, seed=100)


@pytest.fixture(scope="session")
def ethanol_1000() -> list[ase.Atoms]:
    """1000 ethanol conformers (~9 atoms) with full properties."""
    frames = molify.smiles2conformers("CCO", numConfs=1000)
    return _attach_full_properties(frames, seed=1000)


@pytest.fixture(scope="session")
def periodic_100() -> list[ase.Atoms]:
    """100 periodic Cu FCC frames (~108 atoms) with full properties."""
    template = ase.build.bulk("Cu", "fcc", a=3.6) * (3, 3, 3)
    rng = np.random.RandomState(200)
    frames = []
    for _ in range(100):
        atoms = template.copy()
        atoms.positions += rng.randn(*atoms.positions.shape) * 0.01
        frames.append(atoms)
    return _attach_full_properties(frames, seed=200)


@pytest.fixture(scope="session")
def periodic_1000() -> list[ase.Atoms]:
    """1000 periodic Cu FCC frames (~108 atoms) with full properties."""
    template = ase.build.bulk("Cu", "fcc", a=3.6) * (3, 3, 3)
    rng = np.random.RandomState(300)
    frames = []
    for _ in range(1000):
        atoms = template.copy()
        atoms.positions += rng.randn(*atoms.positions.shape) * 0.01
        frames.append(atoms)
    return _attach_full_properties(frames, seed=300)


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

