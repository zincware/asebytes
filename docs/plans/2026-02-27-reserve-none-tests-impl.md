# reserve/None Tests Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Write failing TDD tests that verify `reserve()` and `None` placeholder semantics across all 4 concrete ReadWriteBackend implementations.

**Architecture:** Single test file `tests/test_reserve_none.py` with a parametrized fixture yielding each backend pre-seeded with 2 rows. 10 test methods exercise reserve, None in extend, get, len, iteration, set-after-reserve. Tests are expected to fail — this is the "red" phase of TDD.

**Tech Stack:** pytest, numpy, asebytes backends (LMDBBlobBackend, LMDBObjectBackend, ZarrBackend, H5MDBackend)

---

### Task 1: Write the parametrized fixture and first test

**Files:**
- Create: `tests/test_reserve_none.py`

**Step 1: Write the full test file with fixture + all 10 tests**

The fixture creates each backend, seeds it with 2 rows via `extend()`, and yields a `(backend, sample_row)` tuple. A helper builds appropriate sample rows per backend type.

```python
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
```

**Step 2: Run the tests to confirm they fail (TDD red phase)**

Run: `python -m pytest tests/test_reserve_none.py -v --tb=short 2>&1 | head -80`

Expected: Multiple failures. Specifically:
- **zarr** and **h5md** tests crash with `AttributeError` in `extend` (iterating `None.keys()`)
- **lmdb** `get()` tests fail because `get()` returns `{}` instead of `None`
- Some tests may pass on lmdb (e.g. `test_reserve_increases_len`) since extend handles `None` → `{}`

**Step 3: Commit the failing tests**

```bash
git add tests/test_reserve_none.py
git commit -m "test: add failing TDD tests for reserve/None on all backends

10 test cases × 4 backends covering reserve(), None placeholders,
iteration, get_many, set-after-reserve, and extend-with-None.

Expected to fail — see docs/plans/2026-02-27-reserve-none-tests-design.md
for the contract these tests encode."
```

---

### Task 2: Verify test results and document failures

**Step 1: Run tests and capture output**

Run: `python -m pytest tests/test_reserve_none.py -v --tb=short 2>&1 | tail -50`

**Step 2: Verify the failure pattern matches expectations**

Check that:
- zarr/h5md backends fail on ANY test that calls `reserve()` or `extend([..., None, ...])`
- lmdb backends fail on `test_reserve_get_returns_none` (returns `{}` not `None`)
- `test_reserve_zero_is_noop` might pass on all backends (no None rows created)

Record the exact failure counts in a comment at the top of the test file (optional, for tracking).

**Step 3: No commit needed — this is just verification**

---

## Summary

This plan creates **1 file** with **10 test methods** and **2 fixtures**, producing **40 parametrized test runs**. All tests encode the decided semantics from the design doc. The tests are intentionally written to fail, surfacing the 3 known bugs:

1. Zarr `extend` crashes on `None` rows
2. H5MD `extend` crashes on `None` rows
3. LMDB `get` returns `{}` instead of `None` for reserved slots

The next phase (not in this plan) will fix these bugs to make the tests green.
