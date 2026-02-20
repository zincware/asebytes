from __future__ import annotations

from typing import Any

import ase
import numpy as np
import pytest

from asebytes._views import ColumnView, RowView


class MockParent:
    """Minimal parent that views need."""

    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = rows

    def __len__(self) -> int:
        return len(self._rows)

    def _read_row(self, index: int, keys: list[str] | None = None) -> dict[str, Any]:
        row = self._rows[index]
        if keys is not None:
            return {k: row[k] for k in keys}
        return dict(row)

    def _read_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any]]:
        return [self._read_row(i, keys) for i in indices]

    def _iter_rows(self, indices: list[int], keys: list[str] | None = None):
        for i in indices:
            yield self._read_row(i, keys)

    def _read_column(self, key: str, indices: list[int]) -> list[Any]:
        return [self._rows[i][key] for i in indices]

    def _build_atoms(self, row: dict[str, Any]) -> ase.Atoms:
        """Minimal Atoms construction for testing."""
        n = len(row.get("arrays.numbers", []))
        return ase.Atoms(
            numbers=row.get("arrays.numbers", []),
            positions=row.get("arrays.positions", np.zeros((n, 3))),
        )


@pytest.fixture
def parent():
    rows = [
        {
            "arrays.numbers": np.array([1]),
            "arrays.positions": np.array([[float(i), 0, 0]]),
            "calc.energy": float(-i),
            "info.tag": f"mol_{i}",
        }
        for i in range(10)
    ]
    return MockParent(rows)


# --- RowView tests ---


class TestRowView:
    def test_len(self, parent):
        view = RowView(parent, range(3, 7))
        assert len(view) == 4

    def test_getitem_int(self, parent):
        view = RowView(parent, range(3, 7))
        atoms = view[0]  # should be row index 3
        assert isinstance(atoms, ase.Atoms)
        assert atoms.positions[0, 0] == pytest.approx(3.0)

    def test_getitem_negative_int(self, parent):
        view = RowView(parent, range(3, 7))
        atoms = view[-1]  # should be row index 6
        assert atoms.positions[0, 0] == pytest.approx(6.0)

    def test_getitem_slice(self, parent):
        view = RowView(parent, range(0, 10))
        sub = view[2:5]
        assert isinstance(sub, RowView)
        assert len(sub) == 3

    def test_getitem_list_int(self, parent):
        view = RowView(parent, range(0, 10))
        sub = view[[0, 5, 9]]
        assert isinstance(sub, RowView)
        assert len(sub) == 3

    def test_getitem_str_returns_single_column_view(self, parent):
        view = RowView(parent, range(0, 5))
        col = view["calc.energy"]
        assert isinstance(col, ColumnView)
        assert col._single
        assert len(col) == 5

    def test_getitem_list_str_returns_multi_column_view(self, parent):
        view = RowView(parent, range(0, 5))
        cols = view[["calc.energy", "info.tag"]]
        assert isinstance(cols, ColumnView)
        assert not cols._single
        assert len(cols) == 5

    def test_iter(self, parent):
        view = RowView(parent, range(0, 3))
        atoms_list = list(view)
        assert len(atoms_list) == 3
        assert all(isinstance(a, ase.Atoms) for a in atoms_list)

    def test_to_list(self, parent):
        view = RowView(parent, range(0, 3))
        atoms_list = view.to_list()
        assert len(atoms_list) == 3
        assert all(isinstance(a, ase.Atoms) for a in atoms_list)

    def test_chaining_row_then_column(self, parent):
        """db[5:10]["calc.energy"] should work."""
        view = RowView(parent, range(5, 8))
        energies = list(view["calc.energy"])
        assert energies == pytest.approx([-5.0, -6.0, -7.0])


# --- ColumnView (single key) tests ---


class TestColumnViewSingle:
    def test_len(self, parent):
        view = ColumnView(parent, "calc.energy", range(0, 10))
        assert len(view) == 10

    def test_len_none_indices(self, parent):
        view = ColumnView(parent, "calc.energy")
        assert len(view) == 10

    def test_getitem_int_unwraps(self, parent):
        """Single-key ColumnView[int] returns the value directly."""
        view = ColumnView(parent, "calc.energy", range(0, 10))
        assert view[3] == pytest.approx(-3.0)

    def test_getitem_negative_int(self, parent):
        view = ColumnView(parent, "calc.energy", range(0, 10))
        assert view[-1] == pytest.approx(-9.0)

    def test_getitem_slice(self, parent):
        view = ColumnView(parent, "calc.energy", range(0, 10))
        sub = view[2:5]
        assert isinstance(sub, ColumnView)
        assert sub._single
        assert len(sub) == 3

    def test_getitem_list_int(self, parent):
        view = ColumnView(parent, "calc.energy", range(0, 10))
        sub = view[[0, 5, 9]]
        assert isinstance(sub, ColumnView)
        assert len(sub) == 3

    def test_iter(self, parent):
        view = ColumnView(parent, "calc.energy", range(0, 5))
        values = list(view)
        assert values == pytest.approx([0.0, -1.0, -2.0, -3.0, -4.0])

    def test_to_list(self, parent):
        view = ColumnView(parent, "calc.energy", range(0, 3))
        values = view.to_list()
        assert values == pytest.approx([0.0, -1.0, -2.0])

    def test_to_dict_single(self, parent):
        """to_dict() on single-key view returns dict with one key."""
        view = ColumnView(parent, "calc.energy", range(0, 3))
        d = view.to_dict()
        assert d == {"calc.energy": pytest.approx([0.0, -1.0, -2.0])}

    def test_chaining_column_then_slice(self, parent):
        """db["calc.energy"][5:10] should work."""
        view = ColumnView(parent, "calc.energy")
        sub = view[5:8]
        values = list(sub)
        assert values == pytest.approx([-5.0, -6.0, -7.0])

    def test_same_result_both_orderings(self, parent):
        """db[5:8]["calc.energy"] == db["calc.energy"][5:8]"""
        via_row = list(RowView(parent, range(5, 8))["calc.energy"])
        via_col = list(ColumnView(parent, "calc.energy")[5:8])
        assert via_row == pytest.approx(via_col)


# --- ColumnView (multi key) tests ---


class TestColumnViewMulti:
    def test_len(self, parent):
        view = ColumnView(parent, ["calc.energy", "info.tag"], range(0, 5))
        assert len(view) == 5

    def test_getitem_int_returns_dict(self, parent):
        """Multi-key ColumnView[int] returns a dict."""
        view = ColumnView(parent, ["calc.energy", "info.tag"], range(0, 5))
        row = view[0]
        assert isinstance(row, dict)
        assert "calc.energy" in row
        assert "info.tag" in row
        assert "arrays.positions" not in row

    def test_getitem_slice(self, parent):
        view = ColumnView(parent, ["calc.energy", "info.tag"], range(0, 10))
        sub = view[2:5]
        assert isinstance(sub, ColumnView)
        assert not sub._single
        assert len(sub) == 3

    def test_getitem_str_narrows_to_single(self, parent):
        """Indexing multi-key view with str narrows to single key."""
        view = ColumnView(parent, ["calc.energy", "info.tag"], range(0, 5))
        col = view["calc.energy"]
        assert isinstance(col, ColumnView)
        assert col._single

    def test_iter_yields_dicts(self, parent):
        view = ColumnView(parent, ["calc.energy", "info.tag"], range(0, 3))
        rows = list(view)
        assert len(rows) == 3
        assert all(isinstance(r, dict) for r in rows)
        assert rows[0]["calc.energy"] == pytest.approx(0.0)
        assert rows[0]["info.tag"] == "mol_0"

    def test_to_list(self, parent):
        view = ColumnView(parent, ["calc.energy", "info.tag"], range(0, 3))
        rows = view.to_list()
        assert len(rows) == 3
        assert rows[0]["calc.energy"] == pytest.approx(0.0)

    def test_to_dict(self, parent):
        view = ColumnView(parent, ["calc.energy", "info.tag"], range(0, 3))
        d = view.to_dict()
        assert "calc.energy" in d
        assert "info.tag" in d
        assert d["calc.energy"] == pytest.approx([0.0, -1.0, -2.0])
        assert d["info.tag"] == ["mol_0", "mol_1", "mol_2"]

    def test_chaining_row_then_multi_column(self, parent):
        """db[5:8][["calc.energy", "info.tag"]] should work."""
        view = RowView(parent, range(5, 8))
        cols = view[["calc.energy", "info.tag"]]
        rows = list(cols)
        assert len(rows) == 3
        assert rows[0]["calc.energy"] == pytest.approx(-5.0)
