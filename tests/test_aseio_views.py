import ase
import numpy as np
import pytest
from ase.calculators.singlepoint import SinglePointCalculator

from asebytes import ASEIO
from asebytes._views import ColumnView, RowView
from asebytes.lmdb import LMDBBackend


@pytest.fixture
def db(tmp_path):
    io = ASEIO(str(tmp_path / "test.lmdb"))
    for i in range(10):
        atoms = ase.Atoms("H", positions=[[float(i), 0, 0]])
        atoms.info["tag"] = f"mol_{i}"
        atoms.calc = SinglePointCalculator(atoms)
        atoms.calc.results = {"energy": float(-i)}
        io.append(atoms)
    return io


@pytest.fixture
def db_from_backend(tmp_path):
    """Test ASEIO constructed with explicit LMDBBackend."""
    backend = LMDBBackend(str(tmp_path / "backend.lmdb"))
    io = ASEIO(backend)
    for i in range(5):
        atoms = ase.Atoms("H", positions=[[float(i), 0, 0]])
        atoms.calc = SinglePointCalculator(atoms)
        atoms.calc.results = {"energy": float(-i)}
        io.append(atoms)
    return io


# --- Backward compatibility ---


def test_getitem_int(db):
    atoms = db[0]
    assert isinstance(atoms, ase.Atoms)


def test_getitem_int_negative(db):
    atoms = db[-1]
    assert isinstance(atoms, ase.Atoms)
    assert atoms.positions[0, 0] == pytest.approx(9.0)


# --- Row views ---


def test_getitem_slice(db):
    view = db[3:7]
    assert isinstance(view, RowView)
    assert len(view) == 4


def test_getitem_list_int(db):
    view = db[[0, 5, 9]]
    assert isinstance(view, RowView)
    assert len(view) == 3


def test_row_view_iter(db):
    atoms_list = list(db[0:3])
    assert len(atoms_list) == 3
    assert all(isinstance(a, ase.Atoms) for a in atoms_list)


# --- Column views ---


def test_getitem_str(db):
    view = db["calc.energy"]
    assert isinstance(view, ColumnView)
    assert len(view) == 10


def test_column_view_iter(db):
    energies = list(db["calc.energy"])
    assert len(energies) == 10
    assert energies[0] == pytest.approx(0.0)
    assert energies[9] == pytest.approx(-9.0)


def test_column_view_getitem_int(db):
    val = db["calc.energy"][5]
    assert val == pytest.approx(-5.0)


def test_column_view_getitem_slice(db):
    view = db["calc.energy"][3:6]
    assert isinstance(view, ColumnView)
    values = list(view)
    assert values == pytest.approx([-3.0, -4.0, -5.0])


# --- Multi-column views ---


def test_getitem_list_str(db):
    view = db[["calc.energy", "info.tag"]]
    assert isinstance(view, ColumnView)
    assert not view._single
    assert len(view) == 10


def test_multi_column_view_iter(db):
    rows = list(db[["calc.energy", "info.tag"]][:3])
    assert len(rows) == 3
    assert rows[0]["calc.energy"] == pytest.approx(0.0)
    assert rows[0]["info.tag"] == "mol_0"


def test_multi_column_view_to_dict(db):
    d = db[["calc.energy", "info.tag"]][:3].to_dict()
    assert d["calc.energy"] == pytest.approx([0.0, -1.0, -2.0])
    assert d["info.tag"] == ["mol_0", "mol_1", "mol_2"]


# --- Chaining ---


def test_row_then_column(db):
    """db[5:8]["calc.energy"] should work."""
    energies = list(db[5:8]["calc.energy"])
    assert energies == pytest.approx([-5.0, -6.0, -7.0])


def test_column_then_slice(db):
    """db["calc.energy"][5:8] should work."""
    energies = list(db["calc.energy"][5:8])
    assert energies == pytest.approx([-5.0, -6.0, -7.0])


def test_both_orderings_equal(db):
    """db[5:8]["calc.energy"] == db["calc.energy"][5:8]"""
    via_row = list(db[5:8]["calc.energy"])
    via_col = list(db["calc.energy"][5:8])
    assert via_row == pytest.approx(via_col)


def test_row_then_multi_column(db):
    """db[0:3][["calc.energy", "info.tag"]] should work."""
    view = db[0:3][["calc.energy", "info.tag"]]
    assert isinstance(view, ColumnView)
    assert not view._single
    rows = list(view)
    assert len(rows) == 3


# --- .columns property ---


def test_columns_property(db):
    cols = db.columns
    assert "calc.energy" in cols
    assert "arrays.positions" in cols
    assert "info.tag" in cols


# --- Backend constructor ---


def test_aseio_from_backend(db_from_backend):
    assert len(db_from_backend) == 5
    atoms = db_from_backend[0]
    assert isinstance(atoms, ase.Atoms)


def test_aseio_from_backend_views(db_from_backend):
    energies = list(db_from_backend["calc.energy"])
    assert len(energies) == 5
