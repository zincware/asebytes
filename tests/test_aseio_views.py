import ase
import numpy as np
import pytest
from ase.calculators.singlepoint import SinglePointCalculator

from asebytes import ASEIO
from asebytes._views import ASEColumnView, ColumnView, RowView
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
    assert isinstance(view, ASEColumnView)
    assert len(view) == 10


def test_column_view_iter(db):
    """ASEIO column access returns Atoms."""
    results = list(db["calc.energy"])
    assert len(results) == 10
    assert all(isinstance(r, ase.Atoms) for r in results)
    assert results[0].calc.results["energy"] == pytest.approx(0.0)
    assert results[9].calc.results["energy"] == pytest.approx(-9.0)


def test_column_view_getitem_int(db):
    val = db["calc.energy"][5]
    assert isinstance(val, ase.Atoms)
    assert val.calc.results["energy"] == pytest.approx(-5.0)


def test_column_view_getitem_slice(db):
    view = db["calc.energy"][3:6]
    assert isinstance(view, ASEColumnView)
    values = list(view)
    assert all(isinstance(v, ase.Atoms) for v in values)


# --- Multi-column views ---


def test_getitem_list_str(db):
    view = db[["calc.energy", "info.tag"]]
    assert isinstance(view, ASEColumnView)
    assert not view._single
    assert len(view) == 10


def test_multi_column_view_iter(db):
    """ASEIO multi-column returns Atoms."""
    results = list(db[["calc.energy", "info.tag"]][:3])
    assert len(results) == 3
    assert all(isinstance(r, ase.Atoms) for r in results)
    assert results[0].calc.results["energy"] == pytest.approx(0.0)
    assert results[0].info["tag"] == "mol_0"


def test_multi_column_view_to_dict_raises(db):
    """to_dict() is not available on ASEIO column views."""
    with pytest.raises(TypeError, match="to_dict.*not available"):
        db[["calc.energy", "info.tag"]][:3].to_dict()


# --- Chaining ---


def test_row_then_column(db):
    """db[5:8]["calc.energy"] should work — returns Atoms."""
    results = list(db[5:8]["calc.energy"])
    assert len(results) == 3
    assert all(isinstance(r, ase.Atoms) for r in results)
    energies = [r.calc.results["energy"] for r in results]
    assert energies == pytest.approx([-5.0, -6.0, -7.0])


def test_column_then_slice(db):
    """db["calc.energy"][5:8] should work — returns Atoms."""
    results = list(db["calc.energy"][5:8])
    assert len(results) == 3
    assert all(isinstance(r, ase.Atoms) for r in results)


def test_both_orderings_equal(db):
    """db[5:8]["calc.energy"] == db["calc.energy"][5:8]"""
    via_row = [r.calc.results["energy"] for r in db[5:8]["calc.energy"]]
    via_col = [r.calc.results["energy"] for r in db["calc.energy"][5:8]]
    assert via_row == pytest.approx(via_col)


def test_row_then_multi_column(db):
    """db[0:3][["calc.energy", "info.tag"]] should work — returns Atoms."""
    view = db[0:3][["calc.energy", "info.tag"]]
    assert isinstance(view, ASEColumnView)
    assert not view._single
    rows = list(view)
    assert len(rows) == 3
    assert all(isinstance(r, ase.Atoms) for r in rows)


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
    results = list(db_from_backend["calc.energy"])
    assert len(results) == 5
    assert all(isinstance(r, ase.Atoms) for r in results)
