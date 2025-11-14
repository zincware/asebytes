"""Tests for BytesIO.update() method."""

import msgpack
import msgpack_numpy as m
import pytest

import asebytes


@pytest.fixture
def io(tmp_path):
    """Create a BytesIO instance for testing."""
    return asebytes.BytesIO(str(tmp_path / "test.db"))


def test_update_add_new_keys(io, ethanol):
    """Test updating an entry by adding new keys."""
    # Arrange: Store initial data
    io[0] = asebytes.encode(ethanol[0])

    # Act: Add new keys
    new_data = {
        b"info.s22": msgpack.packb(123.45, default=m.encode),
        b"info.new_property": msgpack.packb("test_value", default=m.encode),
    }
    io.update(0, new_data)

    # Assert: Verify new keys exist and old keys remain
    data = io[0]
    assert b"info.s22" in data
    assert b"info.new_property" in data
    assert msgpack.unpackb(data[b"info.s22"], object_hook=m.decode) == 123.45
    assert (
        msgpack.unpackb(data[b"info.new_property"], object_hook=m.decode)
        == "test_value"
    )

    # Old keys should still exist
    assert b"cell" in data
    assert b"pbc" in data
    assert b"arrays.positions" in data


def test_update_overwrite_existing_keys(io, ethanol):
    """Test updating an entry by overwriting existing keys."""
    # Arrange: Store initial data with info
    atoms = ethanol[0].copy()
    atoms.info["s22"] = 100.0
    io[0] = asebytes.encode(atoms)

    # Verify initial value
    initial_data = io[0]
    assert msgpack.unpackb(initial_data[b"info.s22"], object_hook=m.decode) == 100.0

    # Act: Overwrite existing key
    new_data = {
        b"info.s22": msgpack.packb(999.99, default=m.encode),
    }
    io.update(0, new_data)

    # Assert: Verify key was overwritten
    updated_data = io[0]
    assert msgpack.unpackb(updated_data[b"info.s22"], object_hook=m.decode) == 999.99


def test_update_empty_dict_does_nothing(io, ethanol):
    """Test that updating with empty dict is a no-op."""
    # Arrange: Store initial data
    io[0] = asebytes.encode(ethanol[0])
    initial_data = io[0]

    # Act: Update with empty dict
    io.update(0, {})

    # Assert: Data should be unchanged
    final_data = io[0]
    assert final_data == initial_data


def test_update_multiple_keys_at_once(io, ethanol):
    """Test updating multiple keys in a single atomic operation."""
    # Arrange: Store initial data
    io[0] = asebytes.encode(ethanol[0])

    # Act: Update multiple keys
    new_data = {
        b"info.s22": msgpack.packb(123.45, default=m.encode),
        b"info.connectivity": msgpack.packb([[0, 1], [1, 2]], default=m.encode),
        b"calc.energy": msgpack.packb(-156.4, default=m.encode),
        b"calc.forces": msgpack.packb([[0.1, 0.2, 0.3]], default=m.encode),
    }
    io.update(0, new_data)

    # Assert: All keys should be present
    data = io[0]
    assert b"info.s22" in data
    assert b"info.connectivity" in data
    assert b"calc.energy" in data
    assert b"calc.forces" in data

    # Verify values
    assert msgpack.unpackb(data[b"info.s22"], object_hook=m.decode) == 123.45
    assert msgpack.unpackb(data[b"calc.energy"], object_hook=m.decode) == -156.4


def test_update_nonexistent_index_raises_keyerror(io):
    """Test that updating a non-existent index raises KeyError."""
    # Act & Assert: Should raise KeyError
    with pytest.raises(KeyError, match="Index 0 not found"):
        io.update(0, {b"info.test": msgpack.packb("value", default=m.encode)})


def test_update_preserves_available_keys_metadata(io, ethanol):
    """Test that update() properly updates the available keys metadata."""
    # Arrange: Store initial data
    io[0] = asebytes.encode(ethanol[0])
    initial_keys = set(io.get_available_keys(0))

    # Act: Add new keys
    new_data = {
        b"info.new_key1": msgpack.packb("value1", default=m.encode),
        b"info.new_key2": msgpack.packb("value2", default=m.encode),
    }
    io.update(0, new_data)

    # Assert: Available keys should include new keys
    updated_keys = set(io.get_available_keys(0))
    assert b"info.new_key1" in updated_keys
    assert b"info.new_key2" in updated_keys

    # Old keys should still be present
    for key in initial_keys:
        assert key in updated_keys


def test_update_with_arrays_keys(io, ethanol):
    """Test updating array keys."""
    # Arrange: Store initial data
    io[0] = asebytes.encode(ethanol[0])

    # Act: Add custom array
    import numpy as np

    forces = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    new_data = {
        b"arrays.forces": msgpack.packb(forces, default=m.encode),
    }
    io.update(0, new_data)

    # Assert: Custom array should be present
    data = io[0]
    assert b"arrays.forces" in data
    retrieved_forces = msgpack.unpackb(data[b"arrays.forces"], object_hook=m.decode)
    np.testing.assert_array_equal(retrieved_forces, forces)


def test_update_with_calc_keys(io, ethanol):
    """Test updating calculator result keys."""
    # Arrange: Store initial data
    io[0] = asebytes.encode(ethanol[0])

    # Act: Add calculator results
    new_data = {
        b"calc.energy": msgpack.packb(-156.4, default=m.encode),
        b"calc.free_energy": msgpack.packb(-156.2, default=m.encode),
    }
    io.update(0, new_data)

    # Assert: Calc keys should be present
    data = io[0]
    assert b"calc.energy" in data
    assert b"calc.free_energy" in data
    assert msgpack.unpackb(data[b"calc.energy"], object_hook=m.decode) == -156.4


def test_update_mixed_new_and_overwrite(io, ethanol):
    """Test updating with a mix of new keys and overwriting existing keys."""
    # Arrange: Store initial data with existing info key
    atoms = ethanol[0].copy()
    atoms.info["existing_key"] = "old_value"
    io[0] = asebytes.encode(atoms)

    # Act: Add new key and overwrite existing
    new_data = {
        b"info.existing_key": msgpack.packb("new_value", default=m.encode),
        b"info.new_key": msgpack.packb("brand_new", default=m.encode),
    }
    io.update(0, new_data)

    # Assert: Both operations should succeed
    data = io[0]
    assert (
        msgpack.unpackb(data[b"info.existing_key"], object_hook=m.decode) == "new_value"
    )
    assert msgpack.unpackb(data[b"info.new_key"], object_hook=m.decode) == "brand_new"


def test_update_multiple_indices(io, ethanol):
    """Test updating different indices independently."""
    # Arrange: Store data at multiple indices
    io[0] = asebytes.encode(ethanol[0])
    io[1] = asebytes.encode(ethanol[1])

    # Act: Update different indices
    io.update(0, {b"info.index": msgpack.packb(0, default=m.encode)})
    io.update(1, {b"info.index": msgpack.packb(1, default=m.encode)})

    # Assert: Each index should have its own data
    data0 = io[0]
    data1 = io[1]
    assert msgpack.unpackb(data0[b"info.index"], object_hook=m.decode) == 0
    assert msgpack.unpackb(data1[b"info.index"], object_hook=m.decode) == 1


def test_update_can_retrieve_with_get(io, ethanol):
    """Test that updated keys can be retrieved using get() method."""
    # Arrange: Store initial data
    io[0] = asebytes.encode(ethanol[0])

    # Act: Add new keys
    new_data = {
        b"info.s22": msgpack.packb(123.45, default=m.encode),
    }
    io.update(0, new_data)

    # Assert: Can retrieve with get()
    data = io.get(0, keys=[b"info.s22"])
    assert b"info.s22" in data
    assert msgpack.unpackb(data[b"info.s22"], object_hook=m.decode) == 123.45


def test_update_after_delete_and_insert(io, ethanol):
    """Test that update works correctly after delete and insert operations."""
    # Arrange: Setup initial data with deletions
    io[0] = asebytes.encode(ethanol[0])
    io[1] = asebytes.encode(ethanol[1])
    io[2] = asebytes.encode(ethanol[2])
    del io[1]  # Delete middle entry

    # Act: Update remaining entries
    io.update(0, {b"info.test": msgpack.packb("first", default=m.encode)})
    io.update(1, {b"info.test": msgpack.packb("last", default=m.encode)})  # Was index 2

    # Assert: Updates should work correctly
    data0 = io[0]
    data1 = io[1]
    assert msgpack.unpackb(data0[b"info.test"], object_hook=m.decode) == "first"
    assert msgpack.unpackb(data1[b"info.test"], object_hook=m.decode) == "last"


def test_update_does_not_affect_other_entries(io, ethanol):
    """Test that updating one entry doesn't affect others."""
    # Arrange: Store multiple entries
    io[0] = asebytes.encode(ethanol[0])
    io[1] = asebytes.encode(ethanol[1])

    # Get initial data for index 1
    data1_before = io[1].copy()

    # Act: Update index 0
    io.update(0, {b"info.test": msgpack.packb("value", default=m.encode)})

    # Assert: Index 1 should be unchanged
    data1_after = io[1]
    assert data1_after == data1_before
    assert b"info.test" not in data1_after
