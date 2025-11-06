import numpy as np
import pytest
from ase.calculators.singlepoint import SinglePointCalculator

import asebytes


def test_round_trip(ethanol):
    atoms = ethanol[0]
    byte_data = asebytes.to_bytes(atoms)
    assert byte_data.keys() == {
        b"cell",
        b"pbc",
        b"arrays:numbers",
        b"arrays:positions",
        b"info:smiles",
        b"info:connectivity",
    }
    recovered_atoms = asebytes.from_bytes(byte_data)
    assert atoms == recovered_atoms


@pytest.mark.parametrize(
    "value",
    [
        np.bool_(True),
        np.float32(2.718),
        np.int32(42),
        np.array([1, 2, 3], dtype=np.int16),
        np.array([[1, 2, 3], [4, 5, 6]], dtype=np.int32),
        np.array([[[1, 2], [3, 4]], [[5, 6], [7, 8]]], dtype=np.int64),
    ],
)
def test_info_numpy_array(ethanol, value):
    atoms = ethanol[0]
    atoms.info["data"] = value
    byte_data = asebytes.to_bytes(atoms)
    assert b"info:data" in byte_data
    recovered_atoms = asebytes.from_bytes(byte_data)
    assert np.array_equal(atoms.info["data"], recovered_atoms.info["data"])


@pytest.mark.parametrize(
    "value",
    [
        "Hello, ASEBytes!",
        123456,
        3.14159,
        True,
        None,
        {"a": 1, "b": [1, 2, 3], "c": {"nested": "dict"}},
        [1, 2, 3, 4, 5],
    ],
)
def test_info_python_type(ethanol, value):
    atoms = ethanol[0]
    atoms.info["data"] = value
    byte_data = asebytes.to_bytes(atoms)
    assert b"info:data" in byte_data
    recovered_atoms = asebytes.from_bytes(byte_data)
    assert atoms.info["data"] == recovered_atoms.info["data"]


@pytest.mark.parametrize(
    "value",
    [
        {
            "array1": np.array([1, 2, 3], dtype=np.int32),
            "array2": np.array([[5.0, 6.0], [7.0, 8.0]], dtype=np.float64),
        },
        {
            "array1": np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64),
            "array2": [1, 2, 3, 4, 5],
        },
    ],
)
def test_info_nested_numpy_array(ethanol, value):
    atoms = ethanol[0]
    atoms.info["data"] = value
    byte_data = asebytes.to_bytes(atoms)
    assert b"info:data" in byte_data
    recovered_atoms = asebytes.from_bytes(byte_data)
    assert np.array_equal(
        atoms.info["data"]["array1"], recovered_atoms.info["data"]["array1"]
    )
    assert np.array_equal(
        atoms.info["data"]["array2"], recovered_atoms.info["data"]["array2"]
    )


@pytest.mark.parametrize(
    "value",
    [
        {
            "energy": -10.5,
            "forces": np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]),
        },
        {
            "energy": 0.0,
            "stress": np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]),
        },
    ],
)
def test_calc_results(ethanol, value):
    atoms = ethanol[0]
    atoms.calc = SinglePointCalculator(atoms)
    atoms.calc.results = value
    byte_data = asebytes.to_bytes(atoms)
    for key in value:
        assert f"calc:{key}".encode() in byte_data
    recovered_atoms = asebytes.from_bytes(byte_data)
    assert atoms.calc.results.keys() == recovered_atoms.calc.results.keys()
    for key in atoms.calc.results:
        original = atoms.calc.results[key]
        recovered = recovered_atoms.calc.results[key]
        if isinstance(original, np.ndarray):
            assert np.array_equal(original, recovered)
        else:
            assert original == recovered
