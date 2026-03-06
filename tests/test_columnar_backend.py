"""Tests for the unified ColumnarBackend."""

from __future__ import annotations

import numpy as np
import pytest

from asebytes.columnar import ColumnarBackend


@pytest.fixture(params=[".h5", ".zarr"], ids=["HDF5", "Zarr"])
def backend(tmp_path, request):
    """Yield a fresh ColumnarBackend for each storage engine."""
    path = str(tmp_path / f"test{request.param}")
    b = ColumnarBackend(path)
    yield b
    b.close()


def _make_rows(n_frames: int, rng=None) -> list[dict[str, object]]:
    """Create test rows with varying atom counts."""
    if rng is None:
        rng = np.random.default_rng(42)
    rows = []
    for i in range(n_frames):
        n_atoms = rng.integers(3, 20)
        rows.append({
            "arrays.positions": rng.random((n_atoms, 3)),
            "arrays.numbers": rng.integers(1, 30, size=n_atoms),
            "calc.energy": float(-i * 0.1),
            "calc.forces": rng.random((n_atoms, 3)) * 0.01,
            "info.label": f"frame_{i}",
        })
    return rows


class TestInitAndEmpty:
    def test_empty_len(self, backend):
        assert len(backend) == 0

    def test_reopen_empty(self, tmp_path):
        path = str(tmp_path / "reopen.h5")
        b = ColumnarBackend(path)
        assert len(b) == 0
        b.close()
        b2 = ColumnarBackend(path)
        assert len(b2) == 0
        b2.close()

    def test_list_groups(self, tmp_path):
        path = str(tmp_path / "grp.h5")
        b = ColumnarBackend(path, group="mygrp")
        b.extend([{"arrays.positions": np.zeros((1, 3)), "arrays.numbers": np.array([1])}])
        b.close()
        groups = ColumnarBackend.list_groups(path)
        assert "mygrp" in groups


class TestExtend:
    def test_extend_basic(self, backend):
        rows = _make_rows(10)
        n = backend.extend(rows)
        assert n == 10
        assert len(backend) == 10

    def test_extend_twice(self, backend):
        rows1 = _make_rows(10)
        backend.extend(rows1)
        rows2 = _make_rows(5, rng=np.random.default_rng(99))
        backend.extend(rows2)
        assert len(backend) == 15

    def test_extend_empty(self, backend):
        assert backend.extend([]) == 0

    def test_extend_ragged(self, backend):
        """Frame 0: 3 atoms, Frame 1: 100 atoms."""
        rows = [
            {
                "arrays.positions": np.zeros((3, 3)),
                "arrays.numbers": np.array([1, 1, 1]),
                "calc.energy": -1.0,
            },
            {
                "arrays.positions": np.ones((100, 3)),
                "arrays.numbers": np.arange(100),
                "calc.energy": -2.0,
            },
        ]
        backend.extend(rows)
        assert len(backend) == 2

        r0 = backend.get(0)
        assert r0["arrays.positions"].shape == (3, 3)
        np.testing.assert_array_equal(r0["arrays.positions"], np.zeros((3, 3)))

        r1 = backend.get(1)
        assert r1["arrays.positions"].shape == (100, 3)
        np.testing.assert_array_equal(r1["arrays.positions"], np.ones((100, 3)))


class TestGet:
    def test_get_single(self, backend):
        rows = _make_rows(5)
        backend.extend(rows)
        r = backend.get(0)
        assert r is not None
        np.testing.assert_allclose(r["arrays.positions"], rows[0]["arrays.positions"])
        assert abs(r["calc.energy"] - rows[0]["calc.energy"]) < 1e-10

    def test_get_last(self, backend):
        rows = _make_rows(5)
        backend.extend(rows)
        r = backend.get(-1)
        assert r is not None
        np.testing.assert_allclose(r["arrays.positions"], rows[4]["arrays.positions"])

    def test_get_with_keys(self, backend):
        rows = _make_rows(5)
        backend.extend(rows)
        r = backend.get(0, keys=["calc.energy"])
        assert "calc.energy" in r
        assert "arrays.positions" not in r

    def test_get_out_of_bounds(self, backend):
        rows = _make_rows(3)
        backend.extend(rows)
        with pytest.raises(IndexError):
            backend.get(10)

    def test_get_many(self, backend):
        rows = _make_rows(5)
        backend.extend(rows)
        results = backend.get_many([0, 2, 4])
        assert len(results) == 3
        for i, idx in enumerate([0, 2, 4]):
            np.testing.assert_allclose(
                results[i]["arrays.positions"], rows[idx]["arrays.positions"]
            )

    def test_get_many_reversed(self, backend):
        rows = _make_rows(5)
        backend.extend(rows)
        results = backend.get_many([4, 2, 0])
        assert len(results) == 3
        for i, idx in enumerate([4, 2, 0]):
            np.testing.assert_allclose(
                results[i]["arrays.positions"], rows[idx]["arrays.positions"]
            )


class TestGetColumn:
    def test_scalar_column(self, backend):
        rows = _make_rows(5)
        backend.extend(rows)
        energies = backend.get_column("calc.energy")
        assert len(energies) == 5
        for i in range(5):
            assert abs(energies[i] - rows[i]["calc.energy"]) < 1e-10

    def test_per_atom_column(self, backend):
        rows = _make_rows(5)
        backend.extend(rows)
        positions = backend.get_column("arrays.positions")
        assert len(positions) == 5
        for i in range(5):
            np.testing.assert_allclose(positions[i], rows[i]["arrays.positions"])

    def test_column_with_indices(self, backend):
        rows = _make_rows(5)
        backend.extend(rows)
        energies = backend.get_column("calc.energy", [0, 2, 4])
        assert len(energies) == 3


class TestSet:
    def test_set_scalar(self, backend):
        rows = _make_rows(5)
        backend.extend(rows)
        backend.set(2, {"calc.energy": 999.0})
        r = backend.get(2)
        assert abs(r["calc.energy"] - 999.0) < 1e-10

    def test_set_per_atom_same_length(self, backend):
        rows = _make_rows(5)
        backend.extend(rows)
        n_atoms = rows[0]["arrays.positions"].shape[0]
        new_pos = np.ones((n_atoms, 3)) * 42.0
        backend.set(0, {"arrays.positions": new_pos})
        r = backend.get(0)
        np.testing.assert_allclose(r["arrays.positions"], new_pos)

    def test_set_per_atom_different_length_raises(self, backend):
        rows = _make_rows(5)
        backend.extend(rows)
        with pytest.raises(ValueError, match="Cannot change atom count"):
            backend.set(0, {"arrays.positions": np.zeros((999, 3))})


class TestSetColumn:
    def test_set_column_scalar(self, backend):
        rows = _make_rows(5)
        backend.extend(rows)
        new_energies = [100.0, 200.0]
        backend.set_column("calc.energy", 0, new_energies)
        e = backend.get_column("calc.energy")
        assert abs(e[0] - 100.0) < 1e-10
        assert abs(e[1] - 200.0) < 1e-10


class TestSchema:
    def test_schema_basic(self, backend):
        rows = _make_rows(5)
        backend.extend(rows)
        s = backend.schema()
        assert "arrays.positions" in s
        assert "calc.energy" in s
        assert s["arrays.positions"].shape[0] == "N"
        assert s["calc.energy"].shape == ()

    def test_keys(self, backend):
        rows = _make_rows(5)
        backend.extend(rows)
        k = backend.keys(0)
        assert "arrays.positions" in k
        assert "calc.energy" in k
        assert "info.label" in k


class TestNegativeIndex:
    def test_negative(self, backend):
        rows = _make_rows(5)
        backend.extend(rows)
        r1 = backend.get(-1)
        r2 = backend.get(4)
        assert abs(r1["calc.energy"] - r2["calc.energy"]) < 1e-10


class TestInsertDeleteNotImpl:
    def test_insert(self, backend):
        with pytest.raises(NotImplementedError):
            backend.insert(0, {})

    def test_delete(self, backend):
        with pytest.raises(NotImplementedError):
            backend.delete(0)


class TestRemoveClear:
    def test_clear(self, tmp_path):
        path = str(tmp_path / "clear.h5")
        b = ColumnarBackend(path)
        b.extend(_make_rows(5))
        assert len(b) == 5
        b.clear()
        assert len(b) == 0

    def test_remove(self, tmp_path):
        import os
        path = str(tmp_path / "remove.h5")
        b = ColumnarBackend(path)
        b.extend(_make_rows(3))
        b.remove()
        assert not os.path.exists(path)


class TestRoundTripAllTypes:
    """Test round-trip with various data types."""

    def test_string_info(self, backend):
        rows = [
            {
                "arrays.positions": np.zeros((2, 3)),
                "arrays.numbers": np.array([1, 1]),
                "info.label": "hello",
            }
        ]
        backend.extend(rows)
        r = backend.get(0)
        assert r["info.label"] == "hello"

    def test_dict_info(self, backend):
        rows = [
            {
                "arrays.positions": np.zeros((2, 3)),
                "arrays.numbers": np.array([1, 1]),
                "info.meta": {"key": "value", "num": 42},
            }
        ]
        backend.extend(rows)
        r = backend.get(0)
        assert r["info.meta"] == {"key": "value", "num": 42}

    def test_list_info(self, backend):
        rows = [
            {
                "arrays.positions": np.zeros((2, 3)),
                "arrays.numbers": np.array([1, 1]),
                "info.tags": [1, 2, 3],
            }
        ]
        backend.extend(rows)
        r = backend.get(0)
        assert r["info.tags"] == [1, 2, 3]

    def test_bool_pbc(self, backend):
        rows = [
            {
                "arrays.positions": np.zeros((1, 3)),
                "arrays.numbers": np.array([1]),
                "pbc": np.array([True, True, False]),
            }
        ]
        backend.extend(rows)
        r = backend.get(0)
        np.testing.assert_array_equal(r["pbc"], [True, True, False])

    def test_cell(self, backend):
        cell = np.eye(3) * 10.0
        rows = [
            {
                "arrays.positions": np.zeros((1, 3)),
                "arrays.numbers": np.array([1]),
                "cell": cell,
            }
        ]
        backend.extend(rows)
        r = backend.get(0)
        np.testing.assert_allclose(r["cell"], cell)


class TestLateArrivingColumn:
    """Batch 2 introduces a column that batch 1 didn't have."""

    def test_late_scalar(self, backend):
        rows1 = [
            {
                "arrays.positions": np.zeros((2, 3)),
                "arrays.numbers": np.array([1, 1]),
                "calc.energy": -1.0,
            }
        ]
        rows2 = [
            {
                "arrays.positions": np.zeros((3, 3)),
                "arrays.numbers": np.array([1, 1, 1]),
                "calc.energy": -2.0,
                "calc.stress": np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6]),
            }
        ]
        backend.extend(rows1)
        backend.extend(rows2)

        # Frame 0 should have no stress (or NaN fill)
        r0 = backend.get(0)
        assert "calc.stress" not in r0 or r0.get("calc.stress") is None

        r1 = backend.get(1)
        np.testing.assert_allclose(
            r1["calc.stress"], [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
        )

    def test_late_per_atom(self, backend):
        rows1 = [
            {
                "arrays.positions": np.zeros((2, 3)),
                "arrays.numbers": np.array([1, 1]),
            }
        ]
        rows2 = [
            {
                "arrays.positions": np.ones((3, 3)),
                "arrays.numbers": np.array([1, 1, 1]),
                "calc.forces": np.ones((3, 3)) * 0.5,
            }
        ]
        backend.extend(rows1)
        backend.extend(rows2)
        # Frame 1 should have forces
        r1 = backend.get(1)
        assert "calc.forces" in r1
        np.testing.assert_allclose(r1["calc.forces"], np.ones((3, 3)) * 0.5)


class TestRegistryResolution:
    def test_h5_resolves_columnar(self):
        from asebytes._registry import resolve_backend

        cls = resolve_backend("test.h5", layer="object")
        assert cls is ColumnarBackend

    def test_zarr_resolves_columnar(self):
        from asebytes._registry import resolve_backend

        cls = resolve_backend("test.zarr", layer="object")
        assert cls is ColumnarBackend

    def test_h5md_still_resolves_h5md(self):
        from asebytes._registry import resolve_backend
        from asebytes.h5md import H5MDBackend

        cls = resolve_backend("test.h5md", layer="object")
        assert cls is H5MDBackend
