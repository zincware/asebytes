import pathlib

import ase
import molify
import numpy as np
import pytest
from ase.calculators.singlepoint import SinglePointCalculator

LEMAT_PATH = pathlib.Path(__file__).parent / "data" / "lemat_1000.lmdb"


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
