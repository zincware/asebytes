"""Test decode function with optional parameters.

Only arrays.numbers should be required. All other parameters (cell, pbc, positions)
should be optional.
"""

import msgpack
import msgpack_numpy as m
import numpy as np
import pytest

import asebytes


def test_decode_with_only_numbers_required():
    """Test decode with only arrays.numbers - the minimal required data."""
    # Create minimal data with only atomic numbers
    numbers = np.array([1, 1, 8], dtype=np.int32)  # H, H, O

    data = {
        b"arrays.numbers": msgpack.packb(numbers, default=m.encode),
    }

    # This should work - only numbers is required
    atoms = asebytes.decode(data)

    # Verify the numbers were decoded correctly
    assert len(atoms) == 3
    assert list(atoms.get_atomic_numbers()) == [1, 1, 8]

    # Verify defaults are set properly
    assert atoms.cell is not None  # Should have a default cell
    assert atoms.pbc is not None  # Should have default pbc (False, False, False)
    assert list(atoms.pbc) == [False, False, False]


def test_decode_without_positions():
    """Test decode when positions are not provided."""
    numbers = np.array([6, 6], dtype=np.int32)  # C, C
    cell = np.eye(3) * 10.0
    pbc = np.array([True, True, True], dtype=bool).tobytes()

    data = {
        b"arrays.numbers": msgpack.packb(numbers, default=m.encode),
        b"cell": msgpack.packb(cell, default=m.encode),
        b"pbc": msgpack.packb(pbc),
    }

    # Should work without positions
    atoms = asebytes.decode(data)

    assert len(atoms) == 2
    assert list(atoms.get_atomic_numbers()) == [6, 6]
    # Positions should be initialized (likely to zeros or None)


def test_decode_without_cell():
    """Test decode when cell is not provided."""
    numbers = np.array([7, 7], dtype=np.int32)  # N, N
    pbc = np.array([False, False, False], dtype=bool).tobytes()

    data = {
        b"arrays.numbers": msgpack.packb(numbers, default=m.encode),
        b"pbc": msgpack.packb(pbc),
    }

    # Should work without cell
    atoms = asebytes.decode(data)

    assert len(atoms) == 2
    assert list(atoms.get_atomic_numbers()) == [7, 7]
    # Cell should have some default value


def test_decode_without_pbc():
    """Test decode when pbc is not provided."""
    numbers = np.array([8], dtype=np.int32)  # O
    cell = np.eye(3) * 5.0

    data = {
        b"arrays.numbers": msgpack.packb(numbers, default=m.encode),
        b"cell": msgpack.packb(cell, default=m.encode),
    }

    # Should work without pbc
    atoms = asebytes.decode(data)

    assert len(atoms) == 1
    assert atoms.get_atomic_numbers()[0] == 8
    # PBC should default to False
    assert list(atoms.pbc) == [False, False, False]


def test_decode_with_all_optional_parameters():
    """Test decode when all parameters are provided (current behavior)."""
    numbers = np.array([1, 8], dtype=np.int32)
    positions = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    cell = np.eye(3) * 10.0
    pbc = np.array([True, False, True], dtype=bool).tobytes()

    data = {
        b"arrays.numbers": msgpack.packb(numbers, default=m.encode),
        b"arrays.positions": msgpack.packb(positions, default=m.encode),
        b"cell": msgpack.packb(cell, default=m.encode),
        b"pbc": msgpack.packb(pbc),
    }

    atoms = asebytes.decode(data)

    assert len(atoms) == 2
    assert list(atoms.get_atomic_numbers()) == [1, 8]
    assert np.allclose(atoms.positions, positions)
    assert list(atoms.pbc) == [True, False, True]


@pytest.mark.parametrize("fast", [True, False])
def test_decode_minimal_with_fast_mode(fast):
    """Test that minimal decode works with both fast=True and fast=False."""
    numbers = np.array([1, 1], dtype=np.int32)

    data = {
        b"arrays.numbers": msgpack.packb(numbers, default=m.encode),
    }

    atoms = asebytes.decode(data, fast=fast)

    assert len(atoms) == 2
    assert list(atoms.get_atomic_numbers()) == [1, 1]


@pytest.mark.parametrize("fast", [True, False])
def test_decode_empty_atoms(fast):
    """Test that decode can create an empty Atoms object with no data."""
    # Empty data dict should create empty atoms
    data = {}

    atoms = asebytes.decode(data, fast=fast)

    assert len(atoms) == 0
    assert list(atoms.get_atomic_numbers()) == []
    assert atoms.positions.shape == (0, 3)
    assert list(atoms.pbc) == [False, False, False]


@pytest.mark.parametrize("fast", [True, False])
def test_decode_empty_with_cell_and_pbc(fast):
    """Test that decode can create empty Atoms with cell and pbc but no atoms."""
    cell = np.eye(3) * 10.0
    pbc = np.array([True, True, True], dtype=bool).tobytes()

    data = {
        b"cell": msgpack.packb(cell, default=m.encode),
        b"pbc": msgpack.packb(pbc),
    }

    atoms = asebytes.decode(data, fast=fast)

    assert len(atoms) == 0
    assert list(atoms.get_atomic_numbers()) == []
    assert atoms.positions.shape == (0, 3)
    assert list(atoms.pbc) == [True, True, True]
    assert np.allclose(atoms.cell, cell)
