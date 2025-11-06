import ase
import molify
import numpy as np
import pytest


@pytest.fixture
def ethanol() -> list[ase.Atoms]:
    """Return a list of ethanol molecules."""
    frames = molify.smiles2conformers("CCO", numConfs=1000)
    return frames


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

    return asebytes.BytesIO(str(tmp_path / "test.db"))


@pytest.fixture
def aseio_instance(tmp_path):
    """Return an ASEIO instance for testing."""
    import asebytes

    return asebytes.ASEIO(str(tmp_path / "test.db"))
