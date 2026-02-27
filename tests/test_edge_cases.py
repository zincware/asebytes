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
# Edge cases for keys with dots
# =============================================================================


def test_info_key_with_dot_roundtrip():
    """Test that keys with dots in atoms.info work correctly.

    Keys containing dots should be preserved through encode/decode roundtrip.
    """
    atoms = Atoms("H", positions=[[0, 0, 0]])
    atoms.info["data.value"] = 5

    e_data = asebytes.encode(atoms)
    d_data = asebytes.decode(e_data)
    assert d_data.info["data.value"] == 5


def test_arrays_key_with_dot_roundtrip():
    """Test that keys with dots in atoms.arrays work correctly."""
    atoms = Atoms("H", positions=[[0, 0, 0]])
    atoms.arrays["custom.array"] = np.array([1.0])

    e_data = asebytes.encode(atoms)
    d_data = asebytes.decode(e_data)

    assert np.array_equal(d_data.arrays["custom.array"], np.array([1.0]))


def test_calc_results_key_with_dot_roundtrip():
    """Test that keys with dots in atoms.calc.results work correctly."""
    atoms = Atoms("H", positions=[[0, 0, 0]])
    atoms.calc = SinglePointCalculator(atoms)
    atoms.calc.results["total.energy"] = -10.5

    e_data = asebytes.encode(atoms)
    d_data = asebytes.decode(e_data)
    assert d_data.calc.results["total.energy"] == -10.5


def test_info_key_with_multiple_dots_roundtrip():
    """Test that keys with multiple dots work correctly."""
    atoms = Atoms("H", positions=[[0, 0, 0]])
    atoms.info["a.b.c.d"] = "nested"

    e_data = asebytes.encode(atoms)
    d_data = asebytes.decode(e_data)
    assert d_data.info["a.b.c.d"] == "nested"


def test_info_key_starting_with_dot_roundtrip():
    """Test that keys starting with a dot work correctly."""
    atoms = Atoms("H", positions=[[0, 0, 0]])
    atoms.info[".hidden"] = "value"

    e_data = asebytes.encode(atoms)
    d_data = asebytes.decode(e_data)
    assert d_data.info[".hidden"] == "value"


def test_info_key_ending_with_dot_roundtrip():
    """Test that keys ending with a dot work correctly."""
    atoms = Atoms("H", positions=[[0, 0, 0]])
    atoms.info["trailing."] = "value"

    e_data = asebytes.encode(atoms)
    d_data = asebytes.decode(e_data)
    assert d_data.info["trailing."] == "value"


def test_info_key_resembling_prefix_roundtrip():
    """Test that keys resembling internal prefixes work correctly.

    This tests edge cases where a key in atoms.info might look like
    it contains a prefix (e.g., 'info.data' stored in info becomes 'info.info.data').
    """
    atoms = Atoms("H", positions=[[0, 0, 0]])
    atoms.info["info.data"] = "confusing"
    atoms.info["arrays.fake"] = "also confusing"
    atoms.info["calc.pretend"] = "yet another"

    e_data = asebytes.encode(atoms)
    d_data = asebytes.decode(e_data)

    assert d_data.info["info.data"] == "confusing"
    assert d_data.info["arrays.fake"] == "also confusing"
    assert d_data.info["calc.pretend"] == "yet another"


# =============================================================================
# Edge cases for BlobIO
# =============================================================================


def test_bytesio_with_empty_prefix(tmp_path):
    """Test BlobIO with empty prefix (default behavior)."""
    io = asebytes.BlobIO(asebytes.LMDBBlobBackend(str(tmp_path / "test.lmdb"), prefix=b""))
    io[0] = {b"test": b"data"}
    assert io[0] == {b"test": b"data"}


def test_bytesio_with_custom_prefix(tmp_path):
    """Test BlobIO with custom prefix."""
    io = asebytes.BlobIO(asebytes.LMDBBlobBackend(str(tmp_path / "test.lmdb"), prefix=b"myprefix/"))
    io[0] = {b"test": b"data"}
    assert io[0] == {b"test": b"data"}
    assert len(io) == 1


def test_bytesio_multiple_prefixes_isolated(tmp_path):
    """Test that different prefixes create isolated namespaces."""
    db_path = str(tmp_path / "test.lmdb")
    io1 = asebytes.BlobIO(asebytes.LMDBBlobBackend(db_path, prefix=b"prefix1/"))
    io2 = asebytes.BlobIO(asebytes.LMDBBlobBackend(db_path, prefix=b"prefix2/"))

    io1[0] = {b"test": b"data1"}
    io2[0] = {b"test": b"data2"}

    assert io1[0] == {b"test": b"data1"}
    assert io2[0] == {b"test": b"data2"}
    assert len(io1) == 1
    assert len(io2) == 1


def test_bytesio_empty_data_dict(tmp_path):
    """Test BlobIO with empty data dictionary."""
    io = asebytes.BlobIO(asebytes.LMDBBlobBackend(str(tmp_path / "test.lmdb")))
    io[0] = {}
    assert io[0] == {}
    assert len(io) == 1


def test_bytesio_single_key_value(tmp_path):
    """Test BlobIO with single key-value pair."""
    io = asebytes.BlobIO(asebytes.LMDBBlobBackend(str(tmp_path / "test.lmdb")))
    io[0] = {b"single": b"value"}
    assert io[0] == {b"single": b"value"}


def test_bytesio_many_keys(tmp_path):
    """Test BlobIO with many keys in single entry."""
    io = asebytes.BlobIO(asebytes.LMDBBlobBackend(str(tmp_path / "test.lmdb")))
    data = {f"key{i}".encode(): f"value{i}".encode() for i in range(100)}
    io[0] = data
    recovered = io[0]

    assert len(recovered) == 100
    assert recovered[b"key50"] == b"value50"


def test_bytesio_extend_empty_list(tmp_path):
    """Test extending BlobIO with empty list."""
    io = asebytes.BlobIO(asebytes.LMDBBlobBackend(str(tmp_path / "test.lmdb")))
    io[0] = {b"test": b"data"}
    io.extend([])
    assert len(io) == 1


def test_bytesio_extend_single_item(tmp_path):
    """Test extending BlobIO with single item."""
    io = asebytes.BlobIO(asebytes.LMDBBlobBackend(str(tmp_path / "test.lmdb")))
    io.extend([{b"test": b"data"}])
    assert len(io) == 1
    assert io[0] == {b"test": b"data"}


def test_bytesio_insert_at_zero_empty(tmp_path):
    """Test inserting at index 0 in empty BlobIO."""
    io = asebytes.BlobIO(asebytes.LMDBBlobBackend(str(tmp_path / "test.lmdb")))
    io.insert(0, {b"test": b"data"})
    assert len(io) == 1
    assert io[0] == {b"test": b"data"}


def test_bytesio_insert_negative_clamped_to_zero(tmp_path):
    """Test that negative insert index is clamped to 0."""
    io = asebytes.BlobIO(asebytes.LMDBBlobBackend(str(tmp_path / "test.lmdb")))
    io[0] = {b"first": b"data"}
    io.insert(-10, {b"inserted": b"data"})

    assert len(io) == 2
    assert io[0] == {b"inserted": b"data"}
    assert io[1] == {b"first": b"data"}


def test_bytesio_insert_beyond_length_appends(tmp_path):
    """Test that insert beyond length appends to end."""
    io = asebytes.BlobIO(asebytes.LMDBBlobBackend(str(tmp_path / "test.lmdb")))
    io[0] = {b"first": b"data"}
    io.insert(100, {b"last": b"data"})

    assert len(io) == 2
    assert io[1] == {b"last": b"data"}


def test_bytesio_get_with_empty_keys_list(tmp_path):
    """Test BlobIO.get() with empty keys list returns empty dict."""
    io = asebytes.BlobIO(asebytes.LMDBBlobBackend(str(tmp_path / "test.lmdb")))
    io[0] = {b"key1": b"value1", b"key2": b"value2"}
    result = io.get(0, keys=[])

    assert result == {}


# =============================================================================
# Edge cases for ASEIO
# =============================================================================


def test_aseio_with_empty_prefix(tmp_path):
    """Test ASEIO with empty prefix."""
    io = asebytes.ASEIO(str(tmp_path / "test.lmdb"), prefix=b"")
    atoms = Atoms("H", positions=[[0, 0, 0]])
    io[0] = atoms
    assert io[0] == atoms


def test_aseio_with_custom_prefix(tmp_path):
    """Test ASEIO with custom prefix."""
    io = asebytes.ASEIO(str(tmp_path / "test.lmdb"), prefix=b"atoms/")
    atoms = Atoms("H", positions=[[0, 0, 0]])
    io[0] = atoms
    assert io[0] == atoms


def test_aseio_extend_empty_list(tmp_path):
    """Test extending ASEIO with empty list."""
    io = asebytes.ASEIO(str(tmp_path / "test.lmdb"))
    atoms = Atoms("H", positions=[[0, 0, 0]])
    io[0] = atoms
    io.extend([])
    assert len(io) == 1


def test_aseio_extend_single_atom(tmp_path):
    """Test extending ASEIO with single atoms object."""
    io = asebytes.ASEIO(str(tmp_path / "test.lmdb"))
    atoms = Atoms("H", positions=[[0, 0, 0]])
    io.extend([atoms])
    assert len(io) == 1
    assert io[0] == atoms


def test_aseio_insert_at_zero_empty(tmp_path):
    """Test inserting at index 0 in empty ASEIO."""
    io = asebytes.ASEIO(str(tmp_path / "test.lmdb"))
    atoms = Atoms("H", positions=[[0, 0, 0]])
    io.insert(0, atoms)
    assert len(io) == 1
    assert io[0] == atoms


def test_aseio_iteration_empty(tmp_path):
    """Test iteration over empty ASEIO."""
    io = asebytes.ASEIO(str(tmp_path / "test.lmdb"))
    result = list(io)
    assert result == []


def test_aseio_multiple_prefixes_isolated(tmp_path):
    """Test that different ASEIO prefixes create isolated namespaces."""
    db_path = str(tmp_path / "test.lmdb")
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
    io = asebytes.ASEIO(str(tmp_path / "test.lmdb"))
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
