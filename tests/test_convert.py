import ase
import numpy as np
import pytest
from ase.calculators.singlepoint import SinglePointCalculator
from ase.constraints import FixAtoms

from asebytes._convert import atoms_to_dict, dict_to_atoms


def test_roundtrip_simple():
    atoms = ase.Atoms("H2", positions=[[0, 0, 0], [1, 0, 0]])
    d = atoms_to_dict(atoms)
    result = dict_to_atoms(d)
    assert result == atoms


def test_roundtrip_with_cell_pbc():
    atoms = ase.Atoms(
        "H",
        positions=[[0, 0, 0]],
        cell=[[10, 0, 0], [0, 10, 0], [0, 0, 10]],
        pbc=[True, True, False],
    )
    d = atoms_to_dict(atoms)
    result = dict_to_atoms(d)
    assert np.allclose(result.cell, atoms.cell)
    assert np.array_equal(result.pbc, atoms.pbc)


def test_roundtrip_with_info():
    atoms = ase.Atoms("H", positions=[[0, 0, 0]])
    atoms.info["smiles"] = "CCO"
    atoms.info["data"] = np.array([1, 2, 3])
    d = atoms_to_dict(atoms)
    assert d["info.smiles"] == "CCO"
    assert np.array_equal(d["info.data"], np.array([1, 2, 3]))
    result = dict_to_atoms(d)
    assert result.info["smiles"] == "CCO"


def test_roundtrip_with_calc():
    atoms = ase.Atoms("H2", positions=[[0, 0, 0], [1, 0, 0]])
    atoms.calc = SinglePointCalculator(atoms)
    atoms.calc.results = {
        "energy": -10.5,
        "forces": np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]),
    }
    d = atoms_to_dict(atoms)
    assert d["calc.energy"] == -10.5
    assert np.allclose(d["calc.forces"], [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    result = dict_to_atoms(d)
    assert result.calc.results["energy"] == pytest.approx(-10.5)


def test_roundtrip_with_constraints():
    atoms = ase.Atoms("H2O", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]])
    atoms.set_constraint(FixAtoms(indices=[0, 2]))
    d = atoms_to_dict(atoms)
    assert "constraints" in d
    result = dict_to_atoms(d)
    assert len(result.constraints) == 1


def test_atoms_to_dict_keys():
    """Verify the dict key format."""
    atoms = ase.Atoms("H", positions=[[0, 0, 0]])
    atoms.info["tag"] = "test"
    d = atoms_to_dict(atoms)
    assert "cell" in d
    assert "pbc" in d
    assert "arrays.positions" in d
    assert "arrays.numbers" in d
    assert "info.tag" in d


def test_dict_to_atoms_fast_mode():
    atoms = ase.Atoms("H2", positions=[[0, 0, 0], [1, 0, 0]])
    d = atoms_to_dict(atoms)
    result_fast = dict_to_atoms(d, fast=True)
    result_slow = dict_to_atoms(d, fast=False)
    assert result_fast == result_slow


def test_dict_to_atoms_empty():
    result = dict_to_atoms({})
    assert len(result) == 0


def test_atoms_to_dict_type_error():
    with pytest.raises(TypeError):
        atoms_to_dict("not atoms")


def test_roundtrip_dot_keys():
    """Keys with dots in info should roundtrip correctly."""
    atoms = ase.Atoms("H", positions=[[0, 0, 0]])
    atoms.info["data.value"] = 42
    d = atoms_to_dict(atoms)
    assert d["info.data.value"] == 42
    result = dict_to_atoms(d)
    assert result.info["data.value"] == 42
