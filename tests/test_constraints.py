"""Tests for constraint serialization and deserialization."""

import numpy as np
import pytest
from ase import Atoms
from ase.constraints import (
    FixAtoms,
    FixBondLength,
    FixBondLengths,
    FixedLine,
    FixedPlane,
)

import asebytes


def test_fix_atoms_constraint_roundtrip():
    """Test FixAtoms constraint survives roundtrip."""
    atoms = Atoms("H2O", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]])
    constraint = FixAtoms(indices=[0, 2])
    atoms.set_constraint(constraint)

    byte_data = asebytes.encode(atoms)
    assert b"constraints" in byte_data

    recovered = asebytes.decode(byte_data)
    assert len(recovered.constraints) == 1
    assert isinstance(recovered.constraints[0], FixAtoms)
    assert list(recovered.constraints[0].index) == [0, 2]


def test_fix_bond_length_constraint_roundtrip():
    """Test FixBondLength constraint survives roundtrip."""
    atoms = Atoms("H2", positions=[[0, 0, 0], [1, 0, 0]])
    constraint = FixBondLength(0, 1)
    atoms.set_constraint(constraint)

    byte_data = asebytes.encode(atoms)
    recovered = asebytes.decode(byte_data)

    assert len(recovered.constraints) == 1
    assert isinstance(recovered.constraints[0], FixBondLengths)
    assert recovered.constraints[0].pairs[0].tolist() == [0, 1]


def test_fixed_line_constraint_roundtrip():
    """Test FixedLine constraint survives roundtrip."""
    atoms = Atoms("H", positions=[[0, 0, 0]])
    constraint = FixedLine(0, direction=[1, 0, 0])
    atoms.set_constraint(constraint)

    byte_data = asebytes.encode(atoms)
    recovered = asebytes.decode(byte_data)

    assert len(recovered.constraints) == 1
    assert isinstance(recovered.constraints[0], FixedLine)
    assert recovered.constraints[0].index == 0
    np.testing.assert_array_almost_equal(recovered.constraints[0].dir, [1, 0, 0])


def test_fixed_plane_constraint_roundtrip():
    """Test FixedPlane constraint survives roundtrip."""
    atoms = Atoms("H", positions=[[0, 0, 0]])
    constraint = FixedPlane(0, direction=[0, 0, 1])
    atoms.set_constraint(constraint)

    byte_data = asebytes.encode(atoms)
    recovered = asebytes.decode(byte_data)

    assert len(recovered.constraints) == 1
    assert isinstance(recovered.constraints[0], FixedPlane)
    assert recovered.constraints[0].index == 0
    np.testing.assert_array_almost_equal(recovered.constraints[0].dir, [0, 0, 1])


def test_multiple_constraints_roundtrip():
    """Test multiple constraints survive roundtrip."""
    atoms = Atoms("H2O", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]])
    constraints = [
        FixAtoms(indices=[0]),
        FixBondLength(1, 2),
    ]
    atoms.set_constraint(constraints)

    byte_data = asebytes.encode(atoms)
    recovered = asebytes.decode(byte_data)

    assert len(recovered.constraints) == 2
    assert isinstance(recovered.constraints[0], FixAtoms)
    assert isinstance(recovered.constraints[1], FixBondLengths)
    assert list(recovered.constraints[0].index) == [0]
    assert recovered.constraints[1].pairs[0].tolist() == [1, 2]


@pytest.mark.parametrize("fast", [True, False])
def test_constraints_with_fast_mode(fast):
    """Test constraints work with both fast modes."""
    atoms = Atoms("H2O", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]])
    constraint = FixAtoms(indices=[0, 2])
    atoms.set_constraint(constraint)

    byte_data = asebytes.encode(atoms)
    recovered = asebytes.decode(byte_data, fast=fast)

    assert len(recovered.constraints) == 1
    assert isinstance(recovered.constraints[0], FixAtoms)
    assert list(recovered.constraints[0].index) == [0, 2]


def test_constraint_with_other_data_roundtrip():
    """Test constraints work alongside info, arrays, and calc data."""
    atoms = Atoms("H2O", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]])
    atoms.info["energy"] = -10.5
    atoms.arrays["forces"] = np.array(
        [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]
    )
    constraint = FixAtoms(indices=[0])
    atoms.set_constraint(constraint)

    byte_data = asebytes.encode(atoms)
    recovered = asebytes.decode(byte_data)

    assert recovered.info["energy"] == -10.5
    np.testing.assert_array_equal(recovered.arrays["forces"], atoms.arrays["forces"])
    assert len(recovered.constraints) == 1
    assert isinstance(recovered.constraints[0], FixAtoms)
    assert list(recovered.constraints[0].index) == [0]


def test_empty_constraints_list():
    """Test that empty constraints list is handled correctly."""
    atoms = Atoms("H2O", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]])
    atoms.set_constraint([])

    byte_data = asebytes.encode(atoms)
    recovered = asebytes.decode(byte_data)

    assert len(recovered.constraints) == 0
