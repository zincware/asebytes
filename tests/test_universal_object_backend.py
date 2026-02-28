import numpy as np
import pytest
from asebytes._backends import ReadBackend, ReadWriteBackend


def test_uni_object_isinstance(uni_object_backend):
    assert isinstance(uni_object_backend, ReadBackend)


def test_uni_object_empty_len(uni_object_backend):
    assert len(uni_object_backend) == 0


def test_uni_object_extend_get(uni_object_backend):
    rows = [
        {"calc.energy": -1.0, "info.smiles": "O"},
        {"calc.energy": -2.0, "info.smiles": "CC"},
    ]
    uni_object_backend.extend(rows)
    assert len(uni_object_backend) == 2
    row = uni_object_backend.get(0)
    assert row["calc.energy"] == pytest.approx(-1.0)
    assert row["info.smiles"] == "O"


def test_uni_object_get_with_keys(uni_object_backend):
    uni_object_backend.extend([{"calc.energy": -1.0, "info.smiles": "O"}])
    row = uni_object_backend.get(0, keys=["calc.energy"])
    assert "calc.energy" in row
    assert "info.smiles" not in row


def test_uni_object_get_many(uni_object_backend):
    rows = [{"calc.energy": float(-i)} for i in range(5)]
    uni_object_backend.extend(rows)
    result = uni_object_backend.get_many([1, 3])
    assert len(result) == 2
    assert result[0]["calc.energy"] == pytest.approx(-1.0)
    assert result[1]["calc.energy"] == pytest.approx(-3.0)


def test_uni_object_none_placeholder(uni_object_backend):
    uni_object_backend.extend([{"calc.energy": -1.0}, None, {"calc.energy": -3.0}])
    assert uni_object_backend.get(1) is None


def test_uni_object_numpy_roundtrip(uni_object_backend):
    row = {
        "cell": np.eye(3),
        "arrays.positions": np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]),
        "arrays.numbers": np.array([1, 8]),
    }
    uni_object_backend.extend([row])
    result = uni_object_backend.get(0)
    assert np.allclose(result["cell"], np.eye(3))
    assert np.array_equal(result["arrays.numbers"], np.array([1, 8]))
