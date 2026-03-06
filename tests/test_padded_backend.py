"""Tests for PaddedColumnarBackend."""

from __future__ import annotations

import numpy as np
import pytest

from asebytes.columnar._padded import PaddedColumnarBackend


@pytest.fixture(params=[".h5p", ".zarrp"], ids=["HDF5-padded", "Zarr-padded"])
def backend(tmp_path, request):
    """Yield a fresh PaddedColumnarBackend for each storage engine."""
    path = str(tmp_path / f"test{request.param}")
    b = PaddedColumnarBackend(path)
    yield b
    b.close()


def _make_uniform_rows(n_frames: int = 4, n_atoms: int = 3) -> list[dict]:
    """Create rows with uniform atom counts."""
    rng = np.random.default_rng(42)
    rows = []
    for i in range(n_frames):
        rows.append({
            "arrays.positions": rng.random((n_atoms, 3)),
            "arrays.numbers": rng.integers(1, 30, size=n_atoms).astype(np.int32),
            "cell": np.eye(3) * 10.0,
            "pbc": np.array([True, True, True]),
            "calc.energy": float(-i * 0.1),
        })
    return rows


def _make_variable_rows() -> list[dict]:
    """Create rows with variable atom counts: 3, 5, 2."""
    rng = np.random.default_rng(99)
    counts = [3, 5, 2]
    rows = []
    for i, na in enumerate(counts):
        rows.append({
            "arrays.positions": rng.random((na, 3)),
            "arrays.numbers": rng.integers(1, 30, size=na).astype(np.int32),
            "cell": np.eye(3) * 10.0,
            "pbc": np.array([True, True, True]),
            "calc.energy": float(-i * 0.5),
        })
    return rows


class TestRoundTrip:
    """Write + read round-trip with uniform atom counts."""

    def test_extend_and_read_back(self, backend):
        rows = _make_uniform_rows(4, 3)
        backend.extend(rows)
        assert len(backend) == 4

        for i, orig in enumerate(rows):
            got = backend.get(i)
            assert got is not None
            np.testing.assert_allclose(
                got["arrays.positions"], orig["arrays.positions"]
            )
            np.testing.assert_array_equal(
                got["arrays.numbers"], orig["arrays.numbers"]
            )
            np.testing.assert_allclose(got["cell"], orig["cell"])
            np.testing.assert_array_equal(got["pbc"], orig["pbc"])
            assert got["calc.energy"] == pytest.approx(orig["calc.energy"])


class TestVariableParticleCounts:
    """Extend frames with different n_atoms; verify unpadding on read."""

    def test_variable_atoms_roundtrip(self, backend):
        rows = _make_variable_rows()
        backend.extend(rows)
        assert len(backend) == 3

        counts = [3, 5, 2]
        for i, (orig, na) in enumerate(zip(rows, counts)):
            got = backend.get(i)
            assert got is not None
            assert got["arrays.positions"].shape == (na, 3), (
                f"Frame {i}: expected ({na}, 3), got {got['arrays.positions'].shape}"
            )
            np.testing.assert_allclose(
                got["arrays.positions"], orig["arrays.positions"]
            )
            assert got["arrays.numbers"].shape == (na,)
            np.testing.assert_array_equal(
                got["arrays.numbers"], orig["arrays.numbers"]
            )


class TestAxisResize:
    """Extend with 3-atom frames, then with 5-atom frames. Verify both."""

    def test_resize_expands_axis1(self, backend):
        rng = np.random.default_rng(7)
        batch1 = [
            {
                "arrays.positions": rng.random((3, 3)),
                "arrays.numbers": rng.integers(1, 10, size=3).astype(np.int32),
            }
            for _ in range(2)
        ]
        backend.extend(batch1)
        assert len(backend) == 2

        batch2 = [
            {
                "arrays.positions": rng.random((5, 3)),
                "arrays.numbers": rng.integers(1, 10, size=5).astype(np.int32),
            }
            for _ in range(2)
        ]
        backend.extend(batch2)
        assert len(backend) == 4

        # First batch should still read correctly with 3 atoms
        for i in range(2):
            got = backend.get(i)
            assert got is not None
            assert got["arrays.positions"].shape == (3, 3)
            np.testing.assert_allclose(
                got["arrays.positions"], batch1[i]["arrays.positions"]
            )

        # Second batch should have 5 atoms
        for i in range(2):
            got = backend.get(2 + i)
            assert got is not None
            assert got["arrays.positions"].shape == (5, 3)
            np.testing.assert_allclose(
                got["arrays.positions"], batch2[i]["arrays.positions"]
            )


class TestScalarColumns:
    """Scalar columns (cell, pbc, info values) are unaffected by padding."""

    def test_scalar_not_padded(self, backend):
        rows = _make_variable_rows()
        backend.extend(rows)

        for i, orig in enumerate(rows):
            got = backend.get(i)
            assert got is not None
            np.testing.assert_allclose(got["cell"], orig["cell"])
            np.testing.assert_array_equal(got["pbc"], orig["pbc"])
            assert got["calc.energy"] == pytest.approx(orig["calc.energy"])


class TestGetColumn:
    """get_column for per-atom columns returns list of unpadded arrays."""

    def test_get_column_per_atom(self, backend):
        rows = _make_variable_rows()
        backend.extend(rows)

        positions = backend.get_column("arrays.positions")
        assert len(positions) == 3

        counts = [3, 5, 2]
        for i, (pos, na) in enumerate(zip(positions, counts)):
            assert pos is not None
            assert pos.shape == (na, 3), (
                f"Frame {i}: expected ({na}, 3), got {pos.shape}"
            )
            np.testing.assert_allclose(pos, rows[i]["arrays.positions"])


class TestNAtoms:
    """_n_atoms column is tracked and readable."""

    def test_n_atoms_tracked(self, backend):
        rows = _make_variable_rows()
        backend.extend(rows)

        # _n_atoms is internal metadata; verify via cache and store
        assert backend._n_atoms_cache is not None
        assert len(backend._n_atoms_cache) == 3
        np.testing.assert_array_equal(backend._n_atoms_cache, [3, 5, 2])

        # Also verify from store directly
        raw = backend._store.get_array("_n_atoms")
        np.testing.assert_array_equal(raw, [3, 5, 2])


class TestFillValues:
    """NaN fill for float, 0 for int, False for bool."""

    def test_fill_values(self, tmp_path):
        """Check that padded regions use correct fill values."""
        path = str(tmp_path / "fill.h5p")
        b = PaddedColumnarBackend(path)
        rng = np.random.default_rng(0)

        # Frame 1: 2 atoms, frame 2: 4 atoms
        rows = [
            {
                "arrays.positions": rng.random((2, 3)),
                "arrays.numbers": rng.integers(1, 10, size=2).astype(np.int32),
            },
            {
                "arrays.positions": rng.random((4, 3)),
                "arrays.numbers": rng.integers(1, 10, size=4).astype(np.int32),
            },
        ]
        b.extend(rows)

        # Read raw padded data from store for positions (float -> NaN fill)
        raw_pos = b._store.get_slice("arrays.positions", 0)
        # Should be shape (4, 3) -- padded to max_atoms=4
        assert raw_pos.shape == (4, 3)
        # Last 2 rows should be NaN
        assert np.all(np.isnan(raw_pos[2:]))

        # Read raw padded data for numbers (int -> 0 fill)
        raw_nums = b._store.get_slice("arrays.numbers", 0)
        assert raw_nums.shape == (4,)
        assert np.all(raw_nums[2:] == 0)

        b.close()


class TestLen:
    """len() returns correct frame count."""

    def test_len(self, backend):
        assert len(backend) == 0
        backend.extend(_make_uniform_rows(3))
        assert len(backend) == 3
        backend.extend(_make_uniform_rows(2))
        assert len(backend) == 5
