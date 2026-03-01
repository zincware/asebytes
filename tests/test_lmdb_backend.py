import numpy as np
import pytest

from asebytes._backends import ReadBackend, ReadWriteBackend
from asebytes.lmdb import LMDBObjectBackend


@pytest.fixture
def backend(tmp_path):
    return LMDBObjectBackend(str(tmp_path / "test.lmdb"))


@pytest.fixture
def sample_row():
    return {
        "cell": np.eye(3),
        "pbc": np.array([True, True, True]),
        "arrays.numbers": np.array([1, 8]),
        "arrays.positions": np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]),
        "calc.energy": -10.5,
        "info.smiles": "O",
    }


def test_is_writable_backend(backend):
    assert isinstance(backend, ReadWriteBackend)
    assert isinstance(backend, ReadBackend)


def test_empty_len(backend):
    assert len(backend) == 0


def test_set_and_get(backend, sample_row):
    backend.set(0, sample_row)
    assert len(backend) == 1
    row = backend.get(0)
    assert row["calc.energy"] == pytest.approx(-10.5)
    assert row["info.smiles"] == "O"
    assert np.array_equal(row["arrays.numbers"], np.array([1, 8]))


def test_get_with_keys(backend, sample_row):
    backend.set(0, sample_row)
    row = backend.get(0, keys=["calc.energy", "info.smiles"])
    assert "calc.energy" in row
    assert "info.smiles" in row
    assert "arrays.positions" not in row


def test_keys(backend, sample_row):
    backend.set(0, sample_row)
    cols = backend.keys(0)
    assert "calc.energy" in cols
    assert "arrays.positions" in cols


def test_extend(backend, sample_row):
    backend.extend([sample_row, sample_row, sample_row])
    assert len(backend) == 3


def test_insert(backend, sample_row):
    row_a = {**sample_row, "calc.energy": -1.0}
    row_b = {**sample_row, "calc.energy": -2.0}
    row_c = {**sample_row, "calc.energy": -3.0}
    backend.extend([row_a, row_c])
    backend.insert(1, row_b)
    assert len(backend) == 3
    assert backend.get(0)["calc.energy"] == pytest.approx(-1.0)
    assert backend.get(1)["calc.energy"] == pytest.approx(-2.0)
    assert backend.get(2)["calc.energy"] == pytest.approx(-3.0)


def test_delete(backend, sample_row):
    row_a = {**sample_row, "calc.energy": -1.0}
    row_b = {**sample_row, "calc.energy": -2.0}
    backend.extend([row_a, row_b])
    backend.delete(0)
    assert len(backend) == 1
    assert backend.get(0)["calc.energy"] == pytest.approx(-2.0)


def test_set_overwrite(backend, sample_row):
    backend.set(0, sample_row)
    new_row = {**sample_row, "calc.energy": -99.0}
    backend.set(0, new_row)
    assert backend.get(0)["calc.energy"] == pytest.approx(-99.0)


def test_get_column(backend, sample_row):
    rows = [
        {**sample_row, "calc.energy": -1.0},
        {**sample_row, "calc.energy": -2.0},
        {**sample_row, "calc.energy": -3.0},
    ]
    backend.extend(rows)
    energies = backend.get_column("calc.energy")
    assert energies == pytest.approx([-1.0, -2.0, -3.0])


def test_get_column_with_indices(backend, sample_row):
    rows = [{**sample_row, "calc.energy": float(-i)} for i in range(5)]
    backend.extend(rows)
    energies = backend.get_column("calc.energy", indices=[0, 2, 4])
    assert energies == pytest.approx([0.0, -2.0, -4.0])


def test_get_many(backend, sample_row):
    rows = [{**sample_row, "calc.energy": float(-i)} for i in range(5)]
    backend.extend(rows)
    result = backend.get_many([1, 3])
    assert len(result) == 2
    assert result[0]["calc.energy"] == pytest.approx(-1.0)
    assert result[1]["calc.energy"] == pytest.approx(-3.0)


def test_get_nonexistent(backend):
    with pytest.raises((KeyError, IndexError)):
        backend.get(0)


def test_readonly_mode(tmp_path, sample_row):
    path = str(tmp_path / "readonly.lmdb")
    # Write first
    wb = LMDBObjectBackend(path)
    wb.set(0, sample_row)
    del wb
    # Read-only
    rb = LMDBObjectBackend(path, readonly=True)
    assert len(rb) == 1
    row = rb.get(0)
    assert row["calc.energy"] == pytest.approx(-10.5)


def test_lmdb_object_backend_uses_adapter(backend):
    from asebytes._adapters import BlobToObjectReadWriteAdapter

    assert isinstance(backend, BlobToObjectReadWriteAdapter)


def test_lmdb_object_read_backend_uses_adapter(tmp_path, sample_row):
    from asebytes._adapters import BlobToObjectReadAdapter
    from asebytes.lmdb import LMDBObjectReadBackend

    # Write some data first
    path = str(tmp_path / "read_adapter.lmdb")
    wb = LMDBObjectBackend(path)
    wb.set(0, sample_row)
    del wb

    rb = LMDBObjectReadBackend(path)
    assert isinstance(rb, BlobToObjectReadAdapter)
    assert len(rb) == 1
    row = rb.get(0)
    assert row["calc.energy"] == pytest.approx(-10.5)


def test_set_sparse_index_fills_placeholders(backend, sample_row):
    """Setting a sparse index should fill intermediate slots with placeholders.

    If we set(0, data) then set(3, data), indices 1 and 2 should exist as
    None placeholders. This prevents metadata drift between count and blocks.
    """
    backend.set(0, sample_row)
    backend.set(3, sample_row)  # Sparse - indices 1, 2 should be placeholders

    assert len(backend) == 4

    # Indices 1 and 2 should return None (placeholders)
    assert backend.get(1) is None
    assert backend.get(2) is None

    # Index 0 and 3 should have data
    assert backend.get(0)["calc.energy"] == pytest.approx(-10.5)
    assert backend.get(3)["calc.energy"] == pytest.approx(-10.5)


def test_get_column_with_missing_key(backend):
    """get_column() should return None for rows missing the requested key."""
    # Create rows where some have the key and some don't
    row_with_key = {"calc.energy": -10.5, "info.smiles": "O"}
    row_without_key = {"info.smiles": "H2O"}  # No calc.energy

    backend.set(0, row_with_key)
    backend.set(1, row_without_key)
    backend.set(2, row_with_key)

    # get_column should handle missing keys gracefully
    energies = backend.get_column("calc.energy")
    assert len(energies) == 3
    assert energies[0] == pytest.approx(-10.5)
    assert energies[1] is None  # Missing key should be None
    assert energies[2] == pytest.approx(-10.5)


def test_get_column_with_placeholders(backend, sample_row):
    """get_column() should handle None placeholder rows."""
    backend.set(0, sample_row)
    backend.set(2, sample_row)  # Index 1 is a placeholder

    assert len(backend) == 3

    # get_column should handle placeholder rows (which return None from get)
    energies = backend.get_column("calc.energy")
    assert len(energies) == 3
    assert energies[0] == pytest.approx(-10.5)
    assert energies[1] is None  # Placeholder row
    assert energies[2] == pytest.approx(-10.5)
