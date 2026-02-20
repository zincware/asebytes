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
    """Return a BytesIO instance for testing."""
    import asebytes

    return asebytes.BytesIO(str(tmp_path / "test.lmdb"))


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
    images = []
    for atoms in ase.collections.s22:
        calc = SinglePointCalculator(atoms, energy=np.random.rand())
        atoms.calc = calc
        images.append(atoms)
    return images


@pytest.fixture
def s22_energy_forces() -> list[ase.Atoms]:
    images = []
    for atoms in ase.collections.s22:
        calc = SinglePointCalculator(
            atoms, energy=np.random.rand(), forces=np.random.rand(len(atoms), 3)
        )
        atoms.calc = calc
        images.append(atoms)
    return images


@pytest.fixture
def s22_all_properties() -> list[ase.Atoms]:
    images = []
    for atoms in ase.collections.s22:
        energy = np.random.rand()
        energies = np.random.rand(len(atoms))
        free_energy = np.random.rand()
        forces = np.random.rand(len(atoms), 3)
        stress = np.random.rand(6)
        stresses = np.random.rand(len(atoms), 6)
        dipole = np.random.rand(3)
        magmom = np.random.rand()
        magmoms = np.random.rand(len(atoms))
        dielectric_tensor = np.random.rand(3, 3)
        born_effective_charges = np.random.rand(len(atoms), 3)
        polarization = np.random.rand(3)

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
    images = []
    for atoms in ase.collections.s22:
        atoms.info.update(
            {
                "mlip_energy": np.random.rand(),
                "mlip_energy_2": np.random.rand(),
                "mlip_stress": np.random.rand(6),
                "collection": "s22",
                "metadata": {"author": "Jane Doe", "date": "2021-09-01"},
                "lst": [1, 2, 3],
            }
        )
        atoms.new_array("mlip_forces", np.random.rand(len(atoms), 3))
        atoms.new_array("mlip_forces_2", np.random.rand(len(atoms), 3))
        atoms.set_velocities(np.random.rand(len(atoms), 3))
        calc = SinglePointCalculator(
            atoms, energy=np.random.rand(), forces=np.random.rand(len(atoms), 3)
        )
        atoms.calc = calc
        images.append(atoms)
    return images


@pytest.fixture
def s22_mixed_pbc_cell() -> list[ase.Atoms]:
    images = []
    for atoms in ase.collections.s22:
        atoms.set_pbc(np.random.rand(3) > 0.5)
        atoms.set_cell(np.random.rand(3, 3))
        atoms.info["mlip_energy"] = np.random.rand()
        atoms.new_array("mlip_forces", np.random.rand(len(atoms), 3))
        images.append(atoms)
    return images


@pytest.fixture
def s22_illegal_calc_results() -> list[ase.Atoms]:
    images = []
    for atoms in ase.collections.s22:
        atoms.calc = SinglePointCalculator(atoms)
        atoms.calc.results["mlip_energy"] = np.random.rand()
        atoms.calc.results["dict"] = {"author": "Jane Doe", "date": "2021-09-01"}
        atoms.calc.results["float"] = 3.14
        atoms.calc.results["int"] = 42
        atoms.calc.results["list"] = [1, 2, 3]
        atoms.calc.results["str"] = '{"author": "Jane Doe", "date": "2021-09-01"}'
        atoms.calc.results["list_array"] = [np.random.rand(3), np.random.rand(3)]
        atoms.calc.results["list_str"] = ["Jane Doe", "John Doe"]
        images.append(atoms)
    return images


@pytest.fixture
def water() -> list[ase.Atoms]:
    """Get a dataset without positions (all at origin)."""
    return [ase.Atoms("H2O")]


@pytest.fixture
def s22_nested_calc() -> list[ase.Atoms]:
    images = []
    for atoms in ase.collections.s22:
        atoms.calc = SinglePointCalculator(atoms)
        atoms.calc.results["forces"] = np.random.rand(len(atoms), 3)
        atoms.calc.results["forces_contributions"] = [
            [
                np.random.rand(len(atoms), 3),
                np.random.rand(len(atoms), 3),
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
    images = []
    for atoms in ase.collections.s22:
        if np.random.random() > 0.5:
            atoms.info.update({"mlip_energy": np.random.rand()})
        if np.random.random() > 0.5:
            atoms.new_array("mlip_forces", np.random.rand(len(atoms), 3))
        if np.random.random() > 0.5:
            calc = SinglePointCalculator(atoms)
            set_calc = False
            if np.random.random() > 0.5:
                calc.results["energy"] = np.random.rand()
                set_calc = True
            if np.random.random() > 0.5:
                calc.results["forces"] = np.random.rand(len(atoms), 3)
                set_calc = True
            if set_calc:
                atoms.calc = calc
        images.append(atoms)
    return images
