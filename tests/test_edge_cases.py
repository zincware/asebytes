"""Test edge cases and boundary conditions for asebytes.

This module tests:
- Empty and minimal Atoms objects
- Boundary conditions (empty lists, single items)
- Special values (NaN, inf, empty arrays)
- Prefix functionality
- Large data handling
"""

import numpy as np
import pytest
from ase import Atoms
from ase.calculators.singlepoint import SinglePointCalculator

import asebytes

# =============================================================================
# Edge cases for encode and decode
# =============================================================================


def test_empty_atoms_roundtrip():
    """Test serialization of empty Atoms object (no atoms)."""
    atoms = Atoms()
    byte_data = asebytes.encode(atoms)
    recovered = asebytes.decode(byte_data)

    assert len(recovered) == 0
    assert len(recovered.arrays["numbers"]) == 0


def test_single_atom_roundtrip():
    """Test serialization of single atom."""
    atoms = Atoms("H", positions=[[0, 0, 0]])
    byte_data = asebytes.encode(atoms)
    recovered = asebytes.decode(byte_data)

    assert len(recovered) == 1
    assert recovered.get_chemical_symbols() == ["H"]


def test_atoms_with_empty_info_roundtrip():
    """Test atoms with no info dictionary entries."""
    atoms = Atoms("H2", positions=[[0, 0, 0], [1, 0, 0]])
    atoms.info = {}
    byte_data = asebytes.encode(atoms)
    recovered = asebytes.decode(byte_data)

    assert len(recovered.info) == 0


def test_atoms_with_nan_in_positions():
    """Test atoms with NaN in positions array."""
    atoms = Atoms("H", positions=[[np.nan, 0, 0]])
    byte_data = asebytes.encode(atoms)
    recovered = asebytes.decode(byte_data)

    assert np.isnan(recovered.positions[0, 0])


def test_atoms_with_inf_in_positions():
    """Test atoms with infinity in positions array."""
    atoms = Atoms("H2", positions=[[np.inf, 0, 0], [0, -np.inf, 0]])
    byte_data = asebytes.encode(atoms)
    recovered = asebytes.decode(byte_data)

    assert np.isinf(recovered.positions[0, 0])
    assert np.isinf(recovered.positions[1, 1])


def test_atoms_with_zero_cell():
    """Test atoms with zero-sized cell."""
    atoms = Atoms("H", positions=[[0, 0, 0]], cell=[[0, 0, 0], [0, 0, 0], [0, 0, 0]])
    byte_data = asebytes.encode(atoms)
    recovered = asebytes.decode(byte_data)

    assert np.allclose(recovered.cell, 0)


def test_atoms_with_mixed_pbc():
    """Test atoms with mixed periodic boundary conditions."""
    atoms = Atoms("H", positions=[[0, 0, 0]], pbc=[True, False, True])
    byte_data = asebytes.encode(atoms)
    recovered = asebytes.decode(byte_data)

    assert list(recovered.pbc) == [True, False, True]


def test_atoms_with_no_calc():
    """Test atoms explicitly without calculator."""
    atoms = Atoms("H", positions=[[0, 0, 0]])
    atoms.calc = None
    byte_data = asebytes.encode(atoms)
    recovered = asebytes.decode(byte_data)

    # In fast mode, _calc attribute may not be set at all
    assert not hasattr(recovered, "_calc") or recovered.calc is None


def test_atoms_with_empty_calc_results():
    """Test atoms with calculator but empty results."""
    atoms = Atoms("H", positions=[[0, 0, 0]])
    atoms.calc = SinglePointCalculator(atoms)
    atoms.calc.results = {}
    byte_data = asebytes.encode(atoms)
    recovered = asebytes.decode(byte_data)

    # Empty calc results means no calc keys in byte_data, so calc won't be set
    # In fast mode, _calc attribute may not be set at all
    assert (
        not hasattr(recovered, "_calc")
        or recovered.calc is None
        or len(recovered.calc.results) == 0
    )


def test_atoms_with_empty_string_in_info():
    """Test atoms with empty string value in info."""
    atoms = Atoms("H", positions=[[0, 0, 0]])
    atoms.info["empty"] = ""
    byte_data = asebytes.encode(atoms)
    recovered = asebytes.decode(byte_data)

    assert recovered.info["empty"] == ""


def test_atoms_with_zero_in_info():
    """Test atoms with zero values in info."""
    atoms = Atoms("H", positions=[[0, 0, 0]])
    atoms.info["zero_int"] = 0
    atoms.info["zero_float"] = 0.0
    byte_data = asebytes.encode(atoms)
    recovered = asebytes.decode(byte_data)

    assert recovered.info["zero_int"] == 0
    assert recovered.info["zero_float"] == 0.0


def test_atoms_with_very_large_numbers():
    """Test atoms with very large atomic numbers."""
    atoms = Atoms(numbers=[118, 118])  # Oganesson
    atoms.positions = [[0, 0, 0], [1, 1, 1]]
    byte_data = asebytes.encode(atoms)
    recovered = asebytes.decode(byte_data)

    assert list(recovered.get_atomic_numbers()) == [118, 118]


@pytest.mark.parametrize("fast", [True, False])
def test_minimal_atoms_both_modes(fast):
    """Test minimal atoms object in both fast modes."""
    atoms = Atoms("H")
    byte_data = asebytes.encode(atoms)
    recovered = asebytes.decode(byte_data, fast=fast)

    assert len(recovered) == 1


# =============================================================================
# Edge cases for BytesIO
# =============================================================================


def test_bytesio_with_empty_prefix(tmp_path):
    """Test BytesIO with empty prefix (default behavior)."""
    io = asebytes.BytesIO(str(tmp_path / "test.db"), prefix=b"")
    io[0] = {b"test": b"data"}
    assert io[0] == {b"test": b"data"}


def test_bytesio_with_custom_prefix(tmp_path):
    """Test BytesIO with custom prefix."""
    io = asebytes.BytesIO(str(tmp_path / "test.db"), prefix=b"myprefix/")
    io[0] = {b"test": b"data"}
    assert io[0] == {b"test": b"data"}
    assert len(io) == 1


def test_bytesio_multiple_prefixes_isolated(tmp_path):
    """Test that different prefixes create isolated namespaces."""
    db_path = str(tmp_path / "test.db")
    io1 = asebytes.BytesIO(db_path, prefix=b"prefix1/")
    io2 = asebytes.BytesIO(db_path, prefix=b"prefix2/")

    io1[0] = {b"test": b"data1"}
    io2[0] = {b"test": b"data2"}

    assert io1[0] == {b"test": b"data1"}
    assert io2[0] == {b"test": b"data2"}
    assert len(io1) == 1
    assert len(io2) == 1


def test_bytesio_empty_data_dict(tmp_path):
    """Test BytesIO with empty data dictionary."""
    io = asebytes.BytesIO(str(tmp_path / "test.db"))
    io[0] = {}
    assert io[0] == {}
    assert len(io) == 1


def test_bytesio_single_key_value(tmp_path):
    """Test BytesIO with single key-value pair."""
    io = asebytes.BytesIO(str(tmp_path / "test.db"))
    io[0] = {b"single": b"value"}
    assert io[0] == {b"single": b"value"}


def test_bytesio_many_keys(tmp_path):
    """Test BytesIO with many keys in single entry."""
    io = asebytes.BytesIO(str(tmp_path / "test.db"))
    data = {f"key{i}".encode(): f"value{i}".encode() for i in range(100)}
    io[0] = data
    recovered = io[0]

    assert len(recovered) == 100
    assert recovered[b"key50"] == b"value50"


def test_bytesio_extend_empty_list(tmp_path):
    """Test extending BytesIO with empty list."""
    io = asebytes.BytesIO(str(tmp_path / "test.db"))
    io[0] = {b"test": b"data"}
    io.extend([])
    assert len(io) == 1


def test_bytesio_extend_single_item(tmp_path):
    """Test extending BytesIO with single item."""
    io = asebytes.BytesIO(str(tmp_path / "test.db"))
    io.extend([{b"test": b"data"}])
    assert len(io) == 1
    assert io[0] == {b"test": b"data"}


def test_bytesio_insert_at_zero_empty(tmp_path):
    """Test inserting at index 0 in empty BytesIO."""
    io = asebytes.BytesIO(str(tmp_path / "test.db"))
    io.insert(0, {b"test": b"data"})
    assert len(io) == 1
    assert io[0] == {b"test": b"data"}


def test_bytesio_insert_negative_clamped_to_zero(tmp_path):
    """Test that negative insert index is clamped to 0."""
    io = asebytes.BytesIO(str(tmp_path / "test.db"))
    io[0] = {b"first": b"data"}
    io.insert(-10, {b"inserted": b"data"})

    assert len(io) == 2
    assert io[0] == {b"inserted": b"data"}
    assert io[1] == {b"first": b"data"}


def test_bytesio_insert_beyond_length_appends(tmp_path):
    """Test that insert beyond length appends to end."""
    io = asebytes.BytesIO(str(tmp_path / "test.db"))
    io[0] = {b"first": b"data"}
    io.insert(100, {b"last": b"data"})

    assert len(io) == 2
    assert io[1] == {b"last": b"data"}


def test_bytesio_get_with_empty_keys_list(tmp_path):
    """Test BytesIO.get() with empty keys list returns empty dict."""
    io = asebytes.BytesIO(str(tmp_path / "test.db"))
    io[0] = {b"key1": b"value1", b"key2": b"value2"}
    result = io.get(0, keys=[])

    assert result == {}


def test_bytesio_get_with_nonexistent_keys(tmp_path):
    """Test BytesIO.get() with keys that don't exist."""
    io = asebytes.BytesIO(str(tmp_path / "test.db"))
    io[0] = {b"key1": b"value1"}
    result = io.get(0, keys=[b"nonexistent"])

    assert result == {}


def test_bytesio_get_mixed_existing_nonexistent_keys(tmp_path):
    """Test BytesIO.get() with mix of existing and non-existing keys."""
    io = asebytes.BytesIO(str(tmp_path / "test.db"))
    io[0] = {b"key1": b"value1", b"key2": b"value2"}
    result = io.get(0, keys=[b"key1", b"nonexistent", b"key2"])

    assert result == {b"key1": b"value1", b"key2": b"value2"}


# =============================================================================
# Edge cases for ASEIO
# =============================================================================


def test_aseio_with_empty_prefix(tmp_path):
    """Test ASEIO with empty prefix."""
    io = asebytes.ASEIO(str(tmp_path / "test.db"), prefix=b"")
    atoms = Atoms("H", positions=[[0, 0, 0]])
    io[0] = atoms
    assert io[0] == atoms


def test_aseio_with_custom_prefix(tmp_path):
    """Test ASEIO with custom prefix."""
    io = asebytes.ASEIO(str(tmp_path / "test.db"), prefix=b"atoms/")
    atoms = Atoms("H", positions=[[0, 0, 0]])
    io[0] = atoms
    assert io[0] == atoms


def test_aseio_extend_empty_list(tmp_path):
    """Test extending ASEIO with empty list."""
    io = asebytes.ASEIO(str(tmp_path / "test.db"))
    atoms = Atoms("H", positions=[[0, 0, 0]])
    io[0] = atoms
    io.extend([])
    assert len(io) == 1


def test_aseio_extend_single_atom(tmp_path):
    """Test extending ASEIO with single atoms object."""
    io = asebytes.ASEIO(str(tmp_path / "test.db"))
    atoms = Atoms("H", positions=[[0, 0, 0]])
    io.extend([atoms])
    assert len(io) == 1
    assert io[0] == atoms


def test_aseio_insert_at_zero_empty(tmp_path):
    """Test inserting at index 0 in empty ASEIO."""
    io = asebytes.ASEIO(str(tmp_path / "test.db"))
    atoms = Atoms("H", positions=[[0, 0, 0]])
    io.insert(0, atoms)
    assert len(io) == 1
    assert io[0] == atoms


def test_aseio_iteration_empty(tmp_path):
    """Test iteration over empty ASEIO."""
    io = asebytes.ASEIO(str(tmp_path / "test.db"))
    result = list(io)
    assert result == []


def test_aseio_get_with_no_keys_parameter(tmp_path):
    """Test ASEIO.get() without keys parameter returns full atoms."""
    io = asebytes.ASEIO(str(tmp_path / "test.db"))
    atoms = Atoms("H2", positions=[[0, 0, 0], [1, 0, 0]])
    atoms.info["test"] = "value"
    io[0] = atoms

    recovered = io.get(0)
    assert recovered == atoms
    assert recovered.info["test"] == "value"


def test_aseio_get_with_empty_keys_list(tmp_path):
    """Test ASEIO.get() with empty keys list."""
    io = asebytes.ASEIO(str(tmp_path / "test.db"))
    atoms = Atoms("H", positions=[[0, 0, 0]])
    io[0] = atoms

    # With empty keys list, decode will create an empty atoms object
    recovered = io.get(0, keys=[])
    assert len(recovered) == 0  # Empty atoms since no data was retrieved


def test_aseio_get_only_required_keys(tmp_path):
    """Test ASEIO.get() with only the minimum required keys."""
    io = asebytes.ASEIO(str(tmp_path / "test.db"))
    atoms = Atoms("H", positions=[[0, 0, 0]])
    atoms.info["extra"] = "data"
    io[0] = atoms

    # Get only required keys (cell, pbc, numbers, positions)
    recovered = io.get(
        0, keys=[b"cell", b"pbc", b"arrays.numbers", b"arrays.positions"]
    )
    assert len(recovered) == 1
    assert "extra" not in recovered.info


def test_aseio_multiple_prefixes_isolated(tmp_path):
    """Test that different ASEIO prefixes create isolated namespaces."""
    db_path = str(tmp_path / "test.db")
    io1 = asebytes.ASEIO(db_path, prefix=b"set1/")
    io2 = asebytes.ASEIO(db_path, prefix=b"set2/")

    atoms1 = Atoms("H", positions=[[0, 0, 0]])
    atoms2 = Atoms("He", positions=[[1, 1, 1]])

    io1[0] = atoms1
    io2[0] = atoms2

    assert io1[0] == atoms1
    assert io2[0] == atoms2
    assert len(io1) == 1
    assert len(io2) == 1


def test_aseio_len_after_operations(tmp_path):
    """Test that len() is correct after various operations."""
    io = asebytes.ASEIO(str(tmp_path / "test.db"))
    atoms = Atoms("H", positions=[[0, 0, 0]])

    assert len(io) == 0

    io[0] = atoms
    assert len(io) == 1

    io.insert(0, atoms)
    assert len(io) == 2

    del io[0]
    assert len(io) == 1

    io.extend([atoms, atoms])
    assert len(io) == 3
