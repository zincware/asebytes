"""Tests for reserve() and None placeholder semantics on all ReadWriteBackends.

These tests verify the contract from docs/plans/2026-02-27-reserve-none-tests-design.md:
- get() on a reserved slot returns None
- len() counts reserved slots
- iteration yields None for reserved slots
- set() on a reserved slot populates it normally
"""

import numpy as np
import pytest

from asebytes.lmdb._blob_backend import LMDBBlobBackend
from asebytes.lmdb._backend import LMDBObjectBackend
from asebytes.zarr._backend import ZarrBackend
from asebytes.h5md._backend import H5MDBackend


def _make_blob_row(i: int) -> dict[bytes, bytes]:
    """Sample row for LMDBBlobBackend."""
    return {b"x": str(i).encode(), b"y": str(i * 10).encode()}


def _make_object_row(i: int) -> dict[str, object]:
    """Sample row for LMDBObjectBackend / Zarr / H5MD.

    Uses the key conventions that Zarr and H5MD expect:
    arrays.positions and arrays.numbers are required for those backends
    to function correctly.
    """
    return {
        "arrays.positions": np.array([[float(i), 0.0, 0.0]]),
        "arrays.numbers": np.array([1]),
        "info.tag": i,
    }


@pytest.fixture(
    params=["lmdb_blob", "lmdb_object", "zarr", "h5md"],
    ids=["lmdb_blob", "lmdb_object", "zarr", "h5md"],
)
def rw_backend(request, tmp_path):
    """Yield (backend, sample_row_fn) for each ReadWriteBackend.

    The backend is pre-seeded with 2 rows via extend().
    sample_row_fn(i) returns a valid row for that backend type.
    """
    kind = request.param

    if kind == "lmdb_blob":
        backend = LMDBBlobBackend(str(tmp_path / "test.lmdb"))
        row_fn = _make_blob_row
    elif kind == "lmdb_object":
        backend = LMDBObjectBackend(str(tmp_path / "test.lmdb"))
        row_fn = _make_object_row
    elif kind == "zarr":
        backend = ZarrBackend(str(tmp_path / "test.zarr"))
        row_fn = _make_object_row
    elif kind == "h5md":
        backend = H5MDBackend(str(tmp_path / "test.h5"))
        row_fn = _make_object_row

    # Seed with 2 rows
    backend.extend([row_fn(0), row_fn(1)])
    assert len(backend) == 2, f"Seeding failed for {kind}"

    yield backend, row_fn


@pytest.fixture(
    params=["lmdb_blob", "lmdb_object", "zarr", "h5md"],
    ids=["lmdb_blob", "lmdb_object", "zarr", "h5md"],
)
def empty_rw_backend(request, tmp_path):
    """Yield (backend, sample_row_fn) for each backend, NOT pre-seeded."""
    kind = request.param

    if kind == "lmdb_blob":
        backend = LMDBBlobBackend(str(tmp_path / "test.lmdb"))
        row_fn = _make_blob_row
    elif kind == "lmdb_object":
        backend = LMDBObjectBackend(str(tmp_path / "test.lmdb"))
        row_fn = _make_object_row
    elif kind == "zarr":
        backend = ZarrBackend(str(tmp_path / "test.zarr"))
        row_fn = _make_object_row
    elif kind == "h5md":
        backend = H5MDBackend(str(tmp_path / "test.h5"))
        row_fn = _make_object_row

    yield backend, row_fn


# ── Core reserve semantics ────────────────────────────────────────────


class TestReserveNone:
    def test_reserve_increases_len(self, rw_backend):
        """reserve(3) on a 2-row backend makes len == 5."""
        backend, _ = rw_backend
        backend.reserve(3)
        assert len(backend) == 5

    def test_reserve_get_returns_none(self, rw_backend):
        """get() on each reserved index returns None."""
        backend, _ = rw_backend
        backend.reserve(3)
        for i in (2, 3, 4):
            assert backend.get(i) is None, f"get({i}) should be None"

    def test_reserve_original_data_intact(self, rw_backend):
        """Original rows are unaffected by reserve."""
        backend, row_fn = rw_backend
        # Snapshot originals before reserve
        orig_0 = backend.get(0)
        orig_1 = backend.get(1)
        backend.reserve(3)
        assert backend.get(0) is not None
        assert backend.get(1) is not None
        # Keys should match (values may differ in repr but keys must survive)
        assert set(backend.get(0).keys()) == set(orig_0.keys())
        assert set(backend.get(1).keys()) == set(orig_1.keys())

    def test_reserve_zero_is_noop(self, rw_backend):
        """reserve(0) does not change length or data."""
        backend, _ = rw_backend
        orig_len = len(backend)
        backend.reserve(0)
        assert len(backend) == orig_len


# ── Iteration with None ───────────────────────────────────────────────


class TestReserveIteration:
    def test_reserve_iteration_yields_none(self, rw_backend):
        """Iterating all indices after reserve yields None for reserved slots."""
        backend, _ = rw_backend
        backend.reserve(3)
        results = [backend.get(i) for i in range(len(backend))]
        assert len(results) == 5
        assert results[0] is not None
        assert results[1] is not None
        assert results[2] is None
        assert results[3] is None
        assert results[4] is None

    def test_reserve_get_many_includes_none(self, rw_backend):
        """get_many returns None for reserved slots."""
        backend, _ = rw_backend
        backend.reserve(3)
        results = backend.get_many([0, 2, 4])
        assert len(results) == 3
        assert results[0] is not None
        assert results[1] is None
        assert results[2] is None


# ── Populating reserved slots ─────────────────────────────────────────


class TestReservePopulate:
    def test_set_on_reserved_slot(self, rw_backend):
        """set() on a reserved slot populates it; others stay None."""
        backend, row_fn = rw_backend
        backend.reserve(3)
        new_row = row_fn(99)
        backend.set(3, new_row)
        assert backend.get(3) is not None
        # Adjacent reserved slots still None
        assert backend.get(2) is None
        assert backend.get(4) is None

    def test_reserve_then_extend(self, rw_backend):
        """extend() after reserve appends beyond the reserved range."""
        backend, row_fn = rw_backend
        backend.reserve(2)
        assert len(backend) == 4
        backend.extend([row_fn(10)])
        assert len(backend) == 5
        # Reserved slots still None
        assert backend.get(2) is None
        assert backend.get(3) is None
        # Extended row is real
        assert backend.get(4) is not None


# ── None in extend directly ───────────────────────────────────────────


class TestExtendWithNone:
    def test_extend_with_none_entries(self, rw_backend):
        """extend([row, None, row]) handles inline None placeholders."""
        backend, row_fn = rw_backend
        backend.extend([row_fn(10), None, row_fn(11)])
        assert len(backend) == 5
        assert backend.get(2) is not None  # row_fn(10)
        assert backend.get(3) is None       # None placeholder
        assert backend.get(4) is not None  # row_fn(11)


# ── Edge cases ────────────────────────────────────────────────────────


class TestReserveEdgeCases:
    def test_reserve_on_empty_backend(self, empty_rw_backend):
        """reserve() on a fresh empty backend works correctly."""
        backend, _ = empty_rw_backend
        backend.reserve(2)
        assert len(backend) == 2
        assert backend.get(0) is None
        assert backend.get(1) is None
