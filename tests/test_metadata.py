import numpy as np
import pytest
from ase.calculators.singlepoint import SinglePointCalculator

import asebytes


def test_get_metadata_basic_structure(ethanol):
    """Test get_metadata returns correct structure for basic atom data."""
    atoms = ethanol[0]
    byte_data = asebytes.encode(atoms)

    metadata = asebytes.get_metadata(byte_data)

    # Check that keys are decoded strings
    assert all(isinstance(key, str) for key in metadata.keys())

    # Check cell metadata
    assert metadata["cell"] == {"type": "ndarray", "dtype": "float64", "shape": (3, 3)}

    # Check pbc metadata
    assert metadata["pbc"] == {"type": "ndarray", "dtype": "bool", "shape": (3,)}

    # Check arrays.numbers metadata
    assert metadata["arrays.numbers"]["type"] == "ndarray"
    assert metadata["arrays.numbers"]["dtype"] == "int64"
    assert len(metadata["arrays.numbers"]["shape"]) == 1

    # Check arrays.positions metadata
    assert metadata["arrays.positions"]["type"] == "ndarray"
    assert metadata["arrays.positions"]["dtype"] == "float64"
    assert len(metadata["arrays.positions"]["shape"]) == 2
    assert metadata["arrays.positions"]["shape"][1] == 3


def test_get_metadata_python_primitives(ethanol):
    """Test get_metadata correctly identifies Python primitive types."""
    atoms = ethanol[0]
    atoms.info["string_val"] = "Hello, ASEBytes!"
    atoms.info["int_val"] = 42
    atoms.info["float_val"] = 3.14159
    atoms.info["bool_val"] = True
    atoms.info["none_val"] = None

    byte_data = asebytes.encode(atoms)
    metadata = asebytes.get_metadata(byte_data)

    assert metadata["info.string_val"] == {"type": "str"}
    assert metadata["info.int_val"] == {"type": "int"}
    assert metadata["info.float_val"] == {"type": "float"}
    assert metadata["info.bool_val"] == {"type": "bool"}
    assert metadata["info.none_val"] == {"type": "NoneType"}


def test_get_metadata_collections(ethanol):
    """Test get_metadata correctly identifies list and dict types."""
    atoms = ethanol[0]
    atoms.info["list_val"] = [1, 2, 3, 4, 5]
    atoms.info["dict_val"] = {"a": 1, "b": [1, 2, 3], "c": {"nested": "dict"}}

    byte_data = asebytes.encode(atoms)
    metadata = asebytes.get_metadata(byte_data)

    assert metadata["info.list_val"] == {"type": "list"}
    assert metadata["info.dict_val"] == {"type": "dict"}


def test_get_metadata_numpy_scalars(ethanol):
    """Test get_metadata correctly identifies NumPy scalar types."""
    atoms = ethanol[0]
    atoms.info["bool_scalar"] = np.bool_(True)
    atoms.info["float32_scalar"] = np.float32(2.718)
    atoms.info["int32_scalar"] = np.int32(42)

    byte_data = asebytes.encode(atoms)
    metadata = asebytes.get_metadata(byte_data)

    assert metadata["info.bool_scalar"] == {"type": "numpy_scalar", "dtype": "bool"}
    assert metadata["info.float32_scalar"] == {
        "type": "numpy_scalar",
        "dtype": "float32",
    }
    assert metadata["info.int32_scalar"] == {"type": "numpy_scalar", "dtype": "int32"}


def test_get_metadata_numpy_arrays_various_shapes(ethanol):
    """Test get_metadata handles various array shapes correctly."""
    atoms = ethanol[0]
    atoms.info["array_1d"] = np.array([1, 2, 3], dtype=np.int16)
    atoms.info["array_2d"] = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.int32)
    atoms.info["array_3d"] = np.array(
        [[[1, 2], [3, 4]], [[5, 6], [7, 8]]], dtype=np.int64
    )

    byte_data = asebytes.encode(atoms)
    metadata = asebytes.get_metadata(byte_data)

    assert metadata["info.array_1d"] == {
        "type": "ndarray",
        "dtype": "int16",
        "shape": (3,),
    }
    assert metadata["info.array_2d"] == {
        "type": "ndarray",
        "dtype": "int32",
        "shape": (2, 3),
    }
    assert metadata["info.array_3d"] == {
        "type": "ndarray",
        "dtype": "int64",
        "shape": (2, 2, 2),
    }


def test_get_metadata_with_calc_results(ethanol):
    """Test get_metadata handles calculator results correctly."""
    atoms = ethanol[0]
    atoms.calc = SinglePointCalculator(atoms)
    atoms.calc.results = {
        "energy": -10.5,
        "forces": np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]),
    }

    byte_data = asebytes.encode(atoms)
    metadata = asebytes.get_metadata(byte_data)

    assert metadata["calc.energy"] == {"type": "float"}
    assert metadata["calc.forces"] == {
        "type": "ndarray",
        "dtype": "float64",
        "shape": (3, 3),
    }


def test_get_metadata_nested_dict_with_arrays(ethanol):
    """Test get_metadata identifies nested dict correctly (no nested type info)."""
    atoms = ethanol[0]
    atoms.info["complex_data"] = {
        "array1": np.array([1, 2, 3], dtype=np.int32),
        "array2": np.array([[5.0, 6.0], [7.0, 8.0]], dtype=np.float64),
    }

    byte_data = asebytes.encode(atoms)
    metadata = asebytes.get_metadata(byte_data)

    # Should just report as dict, not nested structure
    assert metadata["info.complex_data"] == {"type": "dict"}
