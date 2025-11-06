"""Test error handling for asebytes functions.

This module tests expected failures and error conditions:
- TypeError when non-Atoms objects are passed
- KeyError when required keys are missing
- ValueError for invalid data
- IndexError for out-of-bounds access
"""
import numpy as np
import pytest
from ase import Atoms
from ase.calculators.singlepoint import SinglePointCalculator

import asebytes


# =============================================================================
# Tests for to_bytes errors
# =============================================================================


def test_to_bytes_with_non_atoms_string_raises_typeerror():
    """Test that to_bytes raises TypeError for string input."""
    with pytest.raises(TypeError, match="Input must be an ase.Atoms object"):
        asebytes.to_bytes("not an atoms object")


def test_to_bytes_with_dict_raises_typeerror():
    """Test that to_bytes raises TypeError for dict input."""
    with pytest.raises(TypeError, match="Input must be an ase.Atoms object"):
        asebytes.to_bytes({"positions": [[0, 0, 0]]})


def test_to_bytes_with_list_raises_typeerror():
    """Test that to_bytes raises TypeError for list input."""
    with pytest.raises(TypeError, match="Input must be an ase.Atoms object"):
        asebytes.to_bytes([1, 2, 3])


def test_to_bytes_with_none_raises_typeerror():
    """Test that to_bytes raises TypeError for None input."""
    with pytest.raises(TypeError, match="Input must be an ase.Atoms object"):
        asebytes.to_bytes(None)


def test_to_bytes_with_numpy_array_raises_typeerror():
    """Test that to_bytes raises TypeError for numpy array input."""
    arr = np.array([[0, 0, 0], [1, 1, 1]])
    with pytest.raises(TypeError, match="Input must be an ase.Atoms object"):
        asebytes.to_bytes(arr)


def test_to_bytes_with_integer_raises_typeerror():
    """Test that to_bytes raises TypeError for integer input."""
    with pytest.raises(TypeError, match="Input must be an ase.Atoms object"):
        asebytes.to_bytes(42)


def test_arrays_key_with_dot_in_middle_raises_valueerror():
    """Test that dots in middle of arrays keys raise ValueError."""
    atoms = Atoms("H", positions=[[0, 0, 0]])
    atoms.arrays["my.array.data"] = np.array([1.0])
    with pytest.raises(
        ValueError,
        match="Key 'my\\.array\\.data' in atoms\\.arrays contains a dot",
    ):
        asebytes.to_bytes(atoms)


def test_info_key_with_multiple_dots_raises_valueerror():
    """Test that multiple dots in info keys raise ValueError."""
    atoms = Atoms("H", positions=[[0, 0, 0]])
    atoms.info["a.b.c"] = "value"
    with pytest.raises(
        ValueError, match="Key 'a\\.b\\.c' in atoms\\.info contains a dot"
    ):
        asebytes.to_bytes(atoms)


def test_calc_results_key_with_dot_raises_valueerror():
    """Test that dots in calc.results keys raise ValueError."""
    atoms = Atoms("H", positions=[[0, 0, 0]])
    atoms.calc = SinglePointCalculator(atoms)
    atoms.calc.results["invalid.energy"] = -10.0
    with pytest.raises(
        ValueError,
        match="Key 'invalid\\.energy' in atoms\\.calc\\.results contains a dot",
    ):
        asebytes.to_bytes(atoms)


# =============================================================================
# Tests for from_bytes errors
# =============================================================================


def test_from_bytes_missing_cell_raises_keyerror():
    """Test that missing cell key raises KeyError."""
    data = {
        b"pbc": b"test",
        b"arrays.numbers": b"test",
    }
    with pytest.raises(KeyError, match="b'cell'"):
        asebytes.from_bytes(data)


def test_from_bytes_missing_pbc_raises_keyerror():
    """Test that missing pbc key raises KeyError."""
    import msgpack
    import msgpack_numpy as m

    data = {
        b"cell": msgpack.packb(np.eye(3), default=m.encode),
        b"arrays.numbers": msgpack.packb(np.array([1]), default=m.encode),
    }
    with pytest.raises(KeyError, match="b'pbc'"):
        asebytes.from_bytes(data)


def test_from_bytes_missing_numbers_raises_keyerror():
    """Test that missing arrays.numbers key raises KeyError."""
    import msgpack
    import msgpack_numpy as m

    data = {
        b"cell": msgpack.packb(np.eye(3), default=m.encode),
        b"pbc": msgpack.packb(np.array([True, True, True]).tobytes()),
    }
    with pytest.raises(KeyError, match="b'arrays.numbers'"):
        asebytes.from_bytes(data)


def test_from_bytes_with_unknown_key_raises_valueerror():
    """Test that unknown top-level keys raise ValueError."""
    import msgpack
    import msgpack_numpy as m

    atoms = Atoms("H", positions=[[0, 0, 0]])
    data = asebytes.to_bytes(atoms)
    # Add an unknown key
    data[b"unknown_key"] = msgpack.packb("value", default=m.encode)

    with pytest.raises(ValueError, match="Unknown key in data: b'unknown_key'"):
        asebytes.from_bytes(data)


def test_from_bytes_with_invalid_prefix_raises_valueerror():
    """Test that keys with invalid prefixes raise ValueError."""
    import msgpack
    import msgpack_numpy as m

    atoms = Atoms("H", positions=[[0, 0, 0]])
    data = asebytes.to_bytes(atoms)
    # Add a key with invalid prefix
    data[b"invalid.prefix.key"] = msgpack.packb("value", default=m.encode)

    with pytest.raises(ValueError, match="Unknown key in data"):
        asebytes.from_bytes(data)


@pytest.mark.parametrize("fast", [True, False])
def test_from_bytes_missing_required_keys_both_modes(fast):
    """Test that missing required keys raise errors in both fast modes."""
    import msgpack
    import msgpack_numpy as m

    data = {
        b"cell": msgpack.packb(np.eye(3), default=m.encode),
        b"pbc": msgpack.packb(np.array([True, True, True]).tobytes()),
        # Missing arrays.numbers
    }
    with pytest.raises(KeyError):
        asebytes.from_bytes(data, fast=fast)


# =============================================================================
# Tests for BytesIO errors
# =============================================================================


def test_bytesio_getitem_nonexistent_index_raises_keyerror(tmp_path):
    """Test that accessing non-existent index raises KeyError."""
    io = asebytes.BytesIO(str(tmp_path / "test.db"))
    with pytest.raises(KeyError, match="Index 0 not found"):
        _ = io[0]


def test_bytesio_getitem_negative_index_nonexistent_raises_keyerror(tmp_path):
    """Test that accessing negative non-existent index raises KeyError."""
    io = asebytes.BytesIO(str(tmp_path / "test.db"))
    io[0] = {b"test": b"data"}
    # Negative indices are not supported, so it tries to look up mapping for -1
    with pytest.raises(KeyError):
        _ = io[-1]


def test_bytesio_delitem_out_of_bounds_raises_indexerror(tmp_path):
    """Test that deleting out-of-bounds index raises IndexError."""
    io = asebytes.BytesIO(str(tmp_path / "test.db"))
    io[0] = {b"test": b"data"}

    with pytest.raises(IndexError, match="Index 5 out of range"):
        del io[5]


def test_bytesio_delitem_negative_out_of_bounds_raises_indexerror(tmp_path):
    """Test that deleting negative out-of-bounds index raises IndexError."""
    io = asebytes.BytesIO(str(tmp_path / "test.db"))
    io[0] = {b"test": b"data"}

    with pytest.raises(IndexError, match="Index -1 out of range"):
        del io[-1]


def test_bytesio_get_nonexistent_index_raises_keyerror(tmp_path):
    """Test that get() with non-existent index raises KeyError."""
    io = asebytes.BytesIO(str(tmp_path / "test.db"))
    with pytest.raises(KeyError, match="Index 0 not found"):
        io.get(0)


def test_bytesio_get_available_keys_nonexistent_raises_keyerror(tmp_path):
    """Test that get_available_keys() with non-existent index raises KeyError."""
    io = asebytes.BytesIO(str(tmp_path / "test.db"))
    with pytest.raises(KeyError, match="Index 0 not found"):
        io.get_available_keys(0)


def test_bytesio_getitem_after_delete_raises_keyerror(tmp_path):
    """Test that accessing deleted index raises KeyError."""
    io = asebytes.BytesIO(str(tmp_path / "test.db"))
    io[0] = {b"test": b"data1"}
    io[1] = {b"test": b"data2"}
    del io[0]

    # After deletion, old index 1 becomes index 0
    # Trying to access index 1 should now fail
    with pytest.raises(KeyError, match="Index 1 not found"):
        _ = io[1]


def test_bytesio_delete_from_empty_raises_indexerror(tmp_path):
    """Test that deleting from empty BytesIO raises IndexError."""
    io = asebytes.BytesIO(str(tmp_path / "test.db"))
    with pytest.raises(IndexError, match="Index 0 out of range"):
        del io[0]


# =============================================================================
# Tests for ASEIO errors
# =============================================================================


def test_aseio_getitem_nonexistent_index_raises_keyerror(tmp_path):
    """Test that accessing non-existent index raises KeyError."""
    io = asebytes.ASEIO(str(tmp_path / "test.db"))
    with pytest.raises(KeyError, match="Index 0 not found"):
        _ = io[0]


def test_aseio_delitem_out_of_bounds_raises_indexerror(tmp_path):
    """Test that deleting out-of-bounds index raises IndexError."""
    io = asebytes.ASEIO(str(tmp_path / "test.db"))
    atoms = Atoms("H", positions=[[0, 0, 0]])
    io[0] = atoms

    with pytest.raises(IndexError, match="Index 5 out of range"):
        del io[5]


def test_aseio_get_nonexistent_index_raises_keyerror(tmp_path):
    """Test that get() with non-existent index raises KeyError."""
    io = asebytes.ASEIO(str(tmp_path / "test.db"))
    with pytest.raises(KeyError, match="Index 0 not found"):
        io.get(0)


def test_aseio_get_available_keys_nonexistent_raises_keyerror(tmp_path):
    """Test that get_available_keys() with non-existent index raises KeyError."""
    io = asebytes.ASEIO(str(tmp_path / "test.db"))
    with pytest.raises(KeyError, match="Index 0 not found"):
        io.get_available_keys(0)


def test_aseio_setitem_with_non_atoms_raises_typeerror(tmp_path):
    """Test that setting non-Atoms object raises TypeError."""
    io = asebytes.ASEIO(str(tmp_path / "test.db"))
    with pytest.raises(TypeError, match="Input must be an ase.Atoms object"):
        io[0] = "not an atoms object"


def test_aseio_insert_with_non_atoms_raises_typeerror(tmp_path):
    """Test that inserting non-Atoms object raises TypeError."""
    io = asebytes.ASEIO(str(tmp_path / "test.db"))
    with pytest.raises(TypeError, match="Input must be an ase.Atoms object"):
        io.insert(0, {"not": "atoms"})


def test_aseio_extend_with_non_atoms_list_raises_typeerror(tmp_path):
    """Test that extending with non-Atoms objects raises TypeError."""
    io = asebytes.ASEIO(str(tmp_path / "test.db"))
    with pytest.raises(TypeError, match="Input must be an ase.Atoms object"):
        io.extend(["not", "atoms", "objects"])


def test_aseio_delete_from_empty_raises_indexerror(tmp_path):
    """Test that deleting from empty ASEIO raises IndexError."""
    io = asebytes.ASEIO(str(tmp_path / "test.db"))
    with pytest.raises(IndexError, match="Index 0 out of range"):
        del io[0]
