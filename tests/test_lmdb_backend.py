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


def test_write_and_read_row(backend, sample_row):
    backend.write_row(0, sample_row)
    assert len(backend) == 1
    row = backend.read_row(0)
    assert row["calc.energy"] == pytest.approx(-10.5)
    assert row["info.smiles"] == "O"
    assert np.array_equal(row["arrays.numbers"], np.array([1, 8]))


def test_read_row_with_keys(backend, sample_row):
    backend.write_row(0, sample_row)
    row = backend.read_row(0, keys=["calc.energy", "info.smiles"])
    assert "calc.energy" in row
    assert "info.smiles" in row
    assert "arrays.positions" not in row


def test_columns(backend, sample_row):
    backend.write_row(0, sample_row)
    cols = backend.columns()
    assert "calc.energy" in cols
    assert "arrays.positions" in cols


def test_append_rows(backend, sample_row):
    backend.append_rows([sample_row, sample_row, sample_row])
    assert len(backend) == 3


def test_insert_row(backend, sample_row):
    row_a = {**sample_row, "calc.energy": -1.0}
    row_b = {**sample_row, "calc.energy": -2.0}
    row_c = {**sample_row, "calc.energy": -3.0}
    backend.append_rows([row_a, row_c])
    backend.insert_row(1, row_b)
    assert len(backend) == 3
    assert backend.read_row(0)["calc.energy"] == pytest.approx(-1.0)
    assert backend.read_row(1)["calc.energy"] == pytest.approx(-2.0)
    assert backend.read_row(2)["calc.energy"] == pytest.approx(-3.0)


def test_delete_row(backend, sample_row):
    row_a = {**sample_row, "calc.energy": -1.0}
    row_b = {**sample_row, "calc.energy": -2.0}
    backend.append_rows([row_a, row_b])
    backend.delete_row(0)
    assert len(backend) == 1
    assert backend.read_row(0)["calc.energy"] == pytest.approx(-2.0)


def test_write_row_overwrite(backend, sample_row):
    backend.write_row(0, sample_row)
    new_row = {**sample_row, "calc.energy": -99.0}
    backend.write_row(0, new_row)
    assert backend.read_row(0)["calc.energy"] == pytest.approx(-99.0)


def test_read_column(backend, sample_row):
    rows = [
        {**sample_row, "calc.energy": -1.0},
        {**sample_row, "calc.energy": -2.0},
        {**sample_row, "calc.energy": -3.0},
    ]
    backend.append_rows(rows)
    energies = backend.read_column("calc.energy")
    assert energies == pytest.approx([-1.0, -2.0, -3.0])


def test_read_column_with_indices(backend, sample_row):
    rows = [
        {**sample_row, "calc.energy": float(-i)}
        for i in range(5)
    ]
    backend.append_rows(rows)
    energies = backend.read_column("calc.energy", indices=[0, 2, 4])
    assert energies == pytest.approx([0.0, -2.0, -4.0])


def test_read_rows(backend, sample_row):
    rows = [
        {**sample_row, "calc.energy": float(-i)}
        for i in range(5)
    ]
    backend.append_rows(rows)
    result = backend.read_rows([1, 3])
    assert len(result) == 2
    assert result[0]["calc.energy"] == pytest.approx(-1.0)
    assert result[1]["calc.energy"] == pytest.approx(-3.0)


def test_read_row_nonexistent(backend):
    with pytest.raises((KeyError, IndexError)):
        backend.read_row(0)


def test_readonly_mode(tmp_path, sample_row):
    path = str(tmp_path / "readonly.lmdb")
    # Write first
    wb = LMDBObjectBackend(path)
    wb.write_row(0, sample_row)
    del wb
    # Read-only
    rb = LMDBObjectBackend(path, readonly=True)
    assert len(rb) == 1
    row = rb.read_row(0)
    assert row["calc.energy"] == pytest.approx(-10.5)
