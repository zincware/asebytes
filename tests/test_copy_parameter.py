"""Test the copy parameter in decode function.

The copy parameter controls whether numpy arrays are copied to make them writable.
When copy=True (default), arrays are writable but use more memory.
When copy=False, arrays are read-only but save memory.
"""

import msgpack
import msgpack_numpy as m
import numpy as np
import pytest

import asebytes


@pytest.mark.parametrize("fast", [True, False])
def test_copy_true_makes_arrays_writable(fast):
    """Test that copy=True makes all arrays writable."""
    numbers = np.array([1, 1, 8], dtype=np.int32)
    positions = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])

    data = {
        b"arrays.numbers": msgpack.packb(numbers, default=m.encode),
        b"arrays.positions": msgpack.packb(positions, default=m.encode),
    }

    atoms = asebytes.decode(data, fast=fast, copy=True)

    # All arrays should be writable
    assert atoms.arrays["numbers"].flags.writeable
    assert atoms.arrays["positions"].flags.writeable

    # Should be able to modify
    atoms[0].symbol = "C"
    atoms[0].position = [1.0, 2.0, 3.0]

    assert atoms[0].symbol == "C"
    assert np.allclose(atoms[0].position, [1.0, 2.0, 3.0])


def test_copy_false_makes_arrays_readonly_fast_mode():
    """Test that copy=False keeps arrays read-only in fast mode (memory efficient).

    Note: This only works with fast=True. When fast=False, ASE's standard
    constructor makes its own copies, so arrays will be writable regardless.
    """
    numbers = np.array([1, 1, 8], dtype=np.int32)
    positions = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])

    data = {
        b"arrays.numbers": msgpack.packb(numbers, default=m.encode),
        b"arrays.positions": msgpack.packb(positions, default=m.encode),
    }

    atoms = asebytes.decode(data, fast=True, copy=False)

    # Arrays should be read-only in fast mode
    assert not atoms.arrays["numbers"].flags.writeable
    assert not atoms.arrays["positions"].flags.writeable

    # Attempting to modify should raise an error
    with pytest.raises(ValueError, match="read-only"):
        atoms[0].symbol = "C"


@pytest.mark.parametrize("fast", [True, False])
def test_copy_default_is_true(fast):
    """Test that copy defaults to True for backward compatibility."""
    numbers = np.array([1, 1], dtype=np.int32)
    positions = np.zeros((2, 3))

    data = {
        b"arrays.numbers": msgpack.packb(numbers, default=m.encode),
        b"arrays.positions": msgpack.packb(positions, default=m.encode),
    }

    # Don't specify copy parameter
    atoms = asebytes.decode(data, fast=fast)

    # Should be writable by default
    assert atoms.arrays["numbers"].flags.writeable
    assert atoms.arrays["positions"].flags.writeable

    # Should be able to modify
    atoms[0].symbol = "C"
    assert atoms[0].symbol == "C"


@pytest.mark.parametrize("fast", [True, False])
@pytest.mark.parametrize("copy", [True, False])
def test_copy_parameter_with_info_arrays(fast, copy):
    """Test that copy parameter affects numpy arrays in info dict."""
    numbers = np.array([1], dtype=np.int32)
    info_array = np.array([1.0, 2.0, 3.0])

    data = {
        b"arrays.numbers": msgpack.packb(numbers, default=m.encode),
        b"info.test_array": msgpack.packb(info_array, default=m.encode),
    }

    atoms = asebytes.decode(data, fast=fast, copy=copy)

    # Check if info array is writable based on copy parameter
    if copy:
        assert atoms.info["test_array"].flags.writeable
        atoms.info["test_array"][0] = 999.0
        assert atoms.info["test_array"][0] == 999.0
    else:
        assert not atoms.info["test_array"].flags.writeable
        with pytest.raises(ValueError, match="read-only"):
            atoms.info["test_array"][0] = 999.0


@pytest.mark.parametrize("fast", [True, False])
@pytest.mark.parametrize("copy", [True, False])
def test_copy_parameter_with_calc_arrays(fast, copy):
    """Test that copy parameter affects numpy arrays in calc results."""
    numbers = np.array([1], dtype=np.int32)
    energy = np.array(-1.5)
    forces = np.array([[0.1, 0.2, 0.3]])

    data = {
        b"arrays.numbers": msgpack.packb(numbers, default=m.encode),
        b"calc.energy": msgpack.packb(energy, default=m.encode),
        b"calc.forces": msgpack.packb(forces, default=m.encode),
    }

    atoms = asebytes.decode(data, fast=fast, copy=copy)

    # Check calc result arrays
    if copy:
        assert atoms.calc.results["forces"].flags.writeable
        atoms.calc.results["forces"][0][0] = 999.0
        assert atoms.calc.results["forces"][0][0] == 999.0
    else:
        assert not atoms.calc.results["forces"].flags.writeable
        with pytest.raises(ValueError, match="read-only"):
            atoms.calc.results["forces"][0][0] = 999.0


@pytest.mark.parametrize("fast", [True, False])
def test_copy_parameter_with_custom_arrays(fast):
    """Test that copy parameter affects custom arrays in atoms.arrays."""
    numbers = np.array([1, 1], dtype=np.int32)
    custom_array = np.array([10.0, 20.0])

    data = {
        b"arrays.numbers": msgpack.packb(numbers, default=m.encode),
        b"arrays.custom_data": msgpack.packb(custom_array, default=m.encode),
    }

    # Test with copy=True
    atoms_copy = asebytes.decode(data, fast=fast, copy=True)
    assert atoms_copy.arrays["custom_data"].flags.writeable
    atoms_copy.arrays["custom_data"][0] = 999.0
    assert atoms_copy.arrays["custom_data"][0] == 999.0

    # Test with copy=False
    atoms_nocopy = asebytes.decode(data, fast=fast, copy=False)
    assert not atoms_nocopy.arrays["custom_data"].flags.writeable
    with pytest.raises(ValueError, match="read-only"):
        atoms_nocopy.arrays["custom_data"][0] = 999.0
