"""Test that atoms[atom_id].symbol assignment works correctly.

This test verifies that symbol assignment works with both fast=True and fast=False
modes in asebytes.decode(). Symbol assignment is a common ASE operation that should
work correctly regardless of how the Atoms object was created.
"""

import msgpack
import msgpack_numpy as m
import numpy as np
import pytest

import asebytes


@pytest.mark.parametrize("fast", [True, False])
def test_symbol_assignment_basic(fast):
    """Test that basic symbol assignment works."""
    numbers = np.array([1, 1, 8], dtype=np.int32)  # H, H, O
    positions = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])

    data = {
        b"arrays.numbers": msgpack.packb(numbers, default=m.encode),
        b"arrays.positions": msgpack.packb(positions, default=m.encode),
    }

    atoms = asebytes.decode(data, fast=fast)

    # Should be able to assign symbol by index
    assert atoms[0].symbol == "H"
    atoms[0].symbol = "C"
    assert atoms[0].symbol == "C"
    assert atoms.get_chemical_symbols()[0] == "C"
    assert atoms.get_atomic_numbers()[0] == 6


@pytest.mark.parametrize("fast", [True, False])
def test_symbol_assignment_from_another_atom(fast):
    """Test that assigning symbol from another atom works."""
    numbers = np.array([1, 1, 8], dtype=np.int32)  # H, H, O
    positions = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])

    data = {
        b"arrays.numbers": msgpack.packb(numbers, default=m.encode),
        b"arrays.positions": msgpack.packb(positions, default=m.encode),
    }

    atoms = asebytes.decode(data, fast=fast)

    # Should be able to assign symbol from another atom
    source_symbol = atoms[2].symbol  # O
    assert source_symbol == "O"

    atoms[1].symbol = source_symbol
    assert atoms[1].symbol == "O"
    assert atoms.get_chemical_symbols()[1] == "O"
    assert atoms.get_atomic_numbers()[1] == 8


@pytest.mark.parametrize("fast", [True, False])
def test_symbol_is_string_not_object(fast):
    """Test that atom.symbol returns a string, not an object with .name attribute."""
    numbers = np.array([1], dtype=np.int32)

    data = {
        b"arrays.numbers": msgpack.packb(numbers, default=m.encode),
    }

    atoms = asebytes.decode(data, fast=fast)
    atom = atoms[0]

    # atom.symbol should be a string
    assert isinstance(atom.symbol, str)

    # atom.symbol should NOT have a .name attribute
    assert not hasattr(atom.symbol, "name")

    # Trying to access .name should raise AttributeError
    with pytest.raises(AttributeError):
        _ = atom.symbol.name


@pytest.mark.parametrize("fast", [True, False])
def test_multiple_symbol_assignments(fast):
    """Test multiple symbol assignments in sequence."""
    numbers = np.array([1, 1, 1, 1], dtype=np.int32)  # 4 H atoms
    positions = np.zeros((4, 3))

    data = {
        b"arrays.numbers": msgpack.packb(numbers, default=m.encode),
        b"arrays.positions": msgpack.packb(positions, default=m.encode),
    }

    atoms = asebytes.decode(data, fast=fast)

    # Change multiple atoms
    atoms[0].symbol = "C"
    atoms[1].symbol = "N"
    atoms[2].symbol = "O"
    atoms[3].symbol = "F"

    expected_symbols = ["C", "N", "O", "F"]
    expected_numbers = [6, 7, 8, 9]

    assert atoms.get_chemical_symbols() == expected_symbols
    assert list(atoms.get_atomic_numbers()) == expected_numbers


@pytest.mark.parametrize("fast", [True, False])
def test_symbol_assignment_edge_cases(fast):
    """Test symbol assignment with various element types."""
    numbers = np.array([1, 6, 79], dtype=np.int32)  # H, C, Au
    positions = np.zeros((3, 3))

    data = {
        b"arrays.numbers": msgpack.packb(numbers, default=m.encode),
        b"arrays.positions": msgpack.packb(positions, default=m.encode),
    }

    atoms = asebytes.decode(data, fast=fast)

    # Test with different element types
    atoms[0].symbol = "He"  # Single atom noble gas
    atoms[1].symbol = "Fe"  # Transition metal
    atoms[2].symbol = "U"  # Heavy element

    assert atoms.get_chemical_symbols() == ["He", "Fe", "U"]
    assert list(atoms.get_atomic_numbers()) == [2, 26, 92]


@pytest.mark.parametrize("fast", [True, False])
def test_position_modification(fast):
    """Test that positions can be modified after decoding."""
    numbers = np.array([1, 1, 8], dtype=np.int32)  # H, H, O
    positions = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])

    data = {
        b"arrays.numbers": msgpack.packb(numbers, default=m.encode),
        b"arrays.positions": msgpack.packb(positions, default=m.encode),
    }

    atoms = asebytes.decode(data, fast=fast)

    # Should be able to modify positions by index
    original_pos = atoms[0].position.copy()
    assert np.allclose(original_pos, [0.0, 0.0, 0.0])

    atoms[0].position = [2.0, 3.0, 4.0]
    assert np.allclose(atoms[0].position, [2.0, 3.0, 4.0])
    assert np.allclose(atoms.positions[0], [2.0, 3.0, 4.0])


@pytest.mark.parametrize("fast", [True, False])
def test_positions_array_modification(fast):
    """Test that the positions array itself can be modified."""
    numbers = np.array([1, 1], dtype=np.int32)  # H, H
    positions = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])

    data = {
        b"arrays.numbers": msgpack.packb(numbers, default=m.encode),
        b"arrays.positions": msgpack.packb(positions, default=m.encode),
    }

    atoms = asebytes.decode(data, fast=fast)

    # Should be able to modify the entire positions array
    new_positions = np.array([[5.0, 6.0, 7.0], [8.0, 9.0, 10.0]])
    atoms.positions[:] = new_positions

    assert np.allclose(atoms.positions, new_positions)
    assert np.allclose(atoms[0].position, [5.0, 6.0, 7.0])
    assert np.allclose(atoms[1].position, [8.0, 9.0, 10.0])


@pytest.mark.parametrize("fast", [True, False])
def test_numbers_array_modification(fast):
    """Test that the numbers array can be modified directly."""
    numbers = np.array([1, 1, 8], dtype=np.int32)  # H, H, O
    positions = np.zeros((3, 3))

    data = {
        b"arrays.numbers": msgpack.packb(numbers, default=m.encode),
        b"arrays.positions": msgpack.packb(positions, default=m.encode),
    }

    atoms = asebytes.decode(data, fast=fast)

    # Should be able to modify numbers array directly
    atoms.arrays["numbers"][0] = 6  # Change H to C
    assert atoms.arrays["numbers"][0] == 6
    assert atoms.get_atomic_numbers()[0] == 6
    assert atoms[0].symbol == "C"
