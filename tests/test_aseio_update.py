"""Tests for ASEIO.update() method."""
import pytest
import numpy as np

import asebytes


@pytest.fixture
def io(tmp_path):
    """Create an ASEIO instance for testing."""
    return asebytes.ASEIO(str(tmp_path / "test.db"))


def test_update_info_add_new_keys(io, ethanol):
    """Test adding new info keys to existing atoms."""
    # Arrange: Store initial atoms
    io[0] = ethanol[0]

    # Act: Add new info keys
    io.update(0, info={"s22": 123.45, "new_property": "test_value"})

    # Assert: Retrieve and verify
    atoms = io[0]
    assert "s22" in atoms.info
    assert "new_property" in atoms.info
    assert atoms.info["s22"] == 123.45
    assert atoms.info["new_property"] == "test_value"

    # Original info should still be present
    assert "smiles" in atoms.info
    assert "connectivity" in atoms.info


def test_update_info_overwrite_existing(io, ethanol):
    """Test overwriting existing info keys."""
    # Arrange: Store atoms with initial info
    atoms = ethanol[0].copy()
    atoms.info["s22"] = 100.0
    io[0] = atoms

    # Act: Overwrite existing key
    io.update(0, info={"s22": 999.99})

    # Assert: Verify overwrite
    updated_atoms = io[0]
    assert updated_atoms.info["s22"] == 999.99


def test_update_arrays_add_forces(io, ethanol):
    """Test adding custom arrays like forces."""
    # Arrange: Store initial atoms
    io[0] = ethanol[0]

    # Act: Add forces array
    forces = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]])
    io.update(0, arrays={"forces": forces})

    # Assert: Verify forces were added
    atoms = io[0]
    assert "forces" in atoms.arrays
    np.testing.assert_array_equal(atoms.arrays["forces"], forces)

    # Original arrays should still exist
    assert "positions" in atoms.arrays
    assert "numbers" in atoms.arrays


def test_update_calc_add_energy(io, ethanol):
    """Test adding calculator results."""
    # Arrange: Store initial atoms
    io[0] = ethanol[0]

    # Act: Add calculator results
    io.update(0, calc={"energy": -156.4, "free_energy": -156.2})

    # Assert: Verify calc results
    atoms = io[0]
    assert atoms.calc is not None
    assert atoms.calc.results["energy"] == -156.4
    assert atoms.calc.results["free_energy"] == -156.2


def test_update_multiple_categories_simultaneously(io, ethanol):
    """Test updating info, arrays, and calc at the same time."""
    # Arrange: Store initial atoms
    io[0] = ethanol[0]

    # Act: Update all categories
    forces = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]])
    io.update(
        0,
        info={"s22": 123.45},
        arrays={"forces": forces},
        calc={"energy": -156.4}
    )

    # Assert: Verify all updates
    atoms = io[0]
    assert atoms.info["s22"] == 123.45
    assert "forces" in atoms.arrays
    np.testing.assert_array_equal(atoms.arrays["forces"], forces)
    assert atoms.calc.results["energy"] == -156.4


def test_update_with_numpy_array_in_info(io, ethanol):
    """Test adding numpy arrays to info dictionary."""
    # Arrange: Store initial atoms
    io[0] = ethanol[0]

    # Act: Add numpy array to info
    connectivity = np.array([[0, 1], [1, 2], [2, 0]])
    io.update(0, info={"connectivity": connectivity})

    # Assert: Verify numpy array roundtrip
    atoms = io[0]
    assert "connectivity" in atoms.info
    np.testing.assert_array_equal(atoms.info["connectivity"], connectivity)


def test_update_empty_args_does_nothing(io, ethanol):
    """Test that calling update with no args or empty dicts is a no-op."""
    # Arrange: Store initial atoms
    io[0] = ethanol[0]
    initial_atoms = io[0]

    # Act: Call with empty/None args
    io.update(0)
    atoms_after_empty_call = io[0]
    assert atoms_after_empty_call == initial_atoms

    # Act: Call with empty dicts
    io.update(0, info={}, arrays={}, calc={})
    atoms_after_empty_dicts = io[0]
    assert atoms_after_empty_dicts == initial_atoms


def test_update_nonexistent_index_raises_keyerror(io):
    """Test that updating non-existent index raises KeyError."""
    # Act & Assert
    with pytest.raises(KeyError, match="Index 0 not found"):
        io.update(0, info={"test": "value"})


def test_update_info_only(io, ethanol):
    """Test updating only info without arrays or calc."""
    # Arrange
    io[0] = ethanol[0]

    # Act
    io.update(0, info={"new_key": "new_value"})

    # Assert
    atoms = io[0]
    assert atoms.info["new_key"] == "new_value"


def test_update_arrays_only(io, ethanol):
    """Test updating only arrays without info or calc."""
    # Arrange
    io[0] = ethanol[0]

    # Act
    forces = np.ones((len(ethanol[0]), 3))
    io.update(0, arrays={"forces": forces})

    # Assert
    atoms = io[0]
    np.testing.assert_array_equal(atoms.arrays["forces"], forces)


def test_update_calc_only(io, ethanol):
    """Test updating only calc without info or arrays."""
    # Arrange
    io[0] = ethanol[0]

    # Act
    io.update(0, calc={"energy": -100.5})

    # Assert
    atoms = io[0]
    assert atoms.calc.results["energy"] == -100.5


def test_update_with_complex_data_types(io, ethanol):
    """Test updating with various Python data types."""
    # Arrange
    io[0] = ethanol[0]

    # Act: Update with different data types
    io.update(0, info={
        "string": "text",
        "int": 42,
        "float": 3.14159,
        "bool": True,
        "list": [1, 2, 3],
        "dict": {"nested": "value"},
        "numpy": np.array([1, 2, 3]),
    })

    # Assert: Verify all types roundtrip correctly
    atoms = io[0]
    assert atoms.info["string"] == "text"
    assert atoms.info["int"] == 42
    assert atoms.info["float"] == 3.14159
    assert atoms.info["bool"] is True
    assert atoms.info["list"] == [1, 2, 3]
    assert atoms.info["dict"] == {"nested": "value"}
    np.testing.assert_array_equal(atoms.info["numpy"], np.array([1, 2, 3]))


def test_update_multiple_indices_independently(io, ethanol):
    """Test updating different indices independently."""
    # Arrange: Store multiple atoms
    io[0] = ethanol[0]
    io[1] = ethanol[1]
    io[2] = ethanol[2]

    # Act: Update each with different data
    io.update(0, info={"index": 0})
    io.update(1, info={"index": 1})
    io.update(2, info={"index": 2})

    # Assert: Each should have correct data
    assert io[0].info["index"] == 0
    assert io[1].info["index"] == 1
    assert io[2].info["index"] == 2


def test_update_preserves_original_atoms_structure(io, ethanol):
    """Test that update preserves cell, pbc, and other core atom properties."""
    # Arrange
    io[0] = ethanol[0]
    original_positions = ethanol[0].positions.copy()
    original_numbers = ethanol[0].numbers.copy()
    original_cell = ethanol[0].cell.array.copy()

    # Act: Update with new info
    io.update(0, info={"new_property": "value"})

    # Assert: Core properties unchanged
    atoms = io[0]
    np.testing.assert_array_equal(atoms.positions, original_positions)
    np.testing.assert_array_equal(atoms.numbers, original_numbers)
    np.testing.assert_array_equal(atoms.cell.array, original_cell)


def test_update_can_be_called_multiple_times(io, ethanol):
    """Test that update can be called multiple times on same index."""
    # Arrange
    io[0] = ethanol[0]

    # Act: Multiple updates
    io.update(0, info={"key1": "value1"})
    io.update(0, info={"key2": "value2"})
    io.update(0, info={"key3": "value3"})

    # Assert: All keys should be present
    atoms = io[0]
    assert atoms.info["key1"] == "value1"
    assert atoms.info["key2"] == "value2"
    assert atoms.info["key3"] == "value3"


def test_update_with_calc_forces_array(io, ethanol):
    """Test adding forces through calc parameter."""
    # Arrange
    io[0] = ethanol[0]

    # Act: Add forces via calc
    forces = np.random.randn(len(ethanol[0]), 3)
    io.update(0, calc={"forces": forces})

    # Assert
    atoms = io[0]
    np.testing.assert_array_equal(atoms.calc.results["forces"], forces)


def test_update_after_extend_operation(io, ethanol):
    """Test that update works correctly after extend."""
    # Arrange: Use extend to add multiple atoms
    io.extend(ethanol)

    # Act: Update specific indices
    io.update(0, info={"batch": "extended"})
    io.update(len(ethanol) - 1, info={"batch": "extended"})

    # Assert
    assert io[0].info["batch"] == "extended"
    assert io[len(ethanol) - 1].info["batch"] == "extended"


def test_update_typical_workflow(io, ethanol):
    """Test typical workflow: store atoms, compute properties, update."""
    # Arrange: Store initial atoms
    atoms = ethanol[0]
    io[0] = atoms

    # Act: Simulate computing properties and updating
    # Step 1: Add s22 benchmark value
    io.update(0, info={"s22": 123.45})

    # Step 2: Later, add connectivity
    connectivity = np.array([[0, 1], [1, 2]])
    io.update(0, info={"connectivity": connectivity})

    # Step 3: After calculation, add results
    io.update(0, calc={"energy": -156.4, "forces": np.random.randn(len(atoms), 3)})

    # Assert: All properties should be present
    final_atoms = io[0]
    assert final_atoms.info["s22"] == 123.45
    assert "connectivity" in final_atoms.info
    assert final_atoms.calc.results["energy"] == -156.4
    assert "forces" in final_atoms.calc.results


def test_update_does_not_affect_other_entries(io, ethanol):
    """Test that updating one entry doesn't affect others."""
    # Arrange: Store multiple entries
    io[0] = ethanol[0]
    io[1] = ethanol[1]

    # Get initial state of index 1
    atoms1_before = io[1]
    info1_before = atoms1_before.info.copy()

    # Act: Update index 0
    io.update(0, info={"test_key": "test_value"})

    # Assert: Index 1 should be unchanged
    atoms1_after = io[1]
    assert atoms1_after.info == info1_before
    assert "test_key" not in atoms1_after.info
