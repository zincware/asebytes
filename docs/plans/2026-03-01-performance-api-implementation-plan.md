# Performance & API Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement 6 non-cache improvements: IndexError bounds checking, auto copy semantics, `_n_atoms` length column, LMDB batch `get_column`, `schema()` method, and registry unification.

**Architecture:** Changes touch backend ABCs, all 6 facade classes (3 sync + 3 async), view classes, the LMDB/Zarr/H5MD backends, the registry, and serialization layer. Each task is independent after Task 1 provides the bounds-checking foundation.

**Tech Stack:** Python 3.10+, numpy, msgpack, lmdb, zarr, h5py, pytest, anyio. Use `Literal` types and strong type hints throughout. TDD: write failing test first, then implement. Never use `pytest.mark.xfail`. Never cache backend data.

**Test runner:** `uv run pytest tests/<file> -v`

---

## Task 1: IndexError for Out-of-Bounds Access

**Files:**
- Modify: `src/asebytes/_blob_io.py:161-166`
- Modify: `src/asebytes/_object_io.py:168-177`
- Modify: `src/asebytes/io.py:207-217`
- Modify: `src/asebytes/_async_blob_io.py`
- Modify: `src/asebytes/_async_object_io.py`
- Modify: `src/asebytes/_async_io.py`
- Create: `tests/test_index_bounds.py`

### Step 1: Write the failing tests

Create `tests/test_index_bounds.py`:

```python
"""Tests for IndexError on out-of-bounds access across all facades."""
from __future__ import annotations

import pytest

import asebytes


# ── Sync facades ──────────────────────────────────────────────────────────


class TestBlobIOBounds:
    @pytest.fixture
    def db(self, tmp_path):
        backend = asebytes.LMDBBlobBackend(str(tmp_path / "test.lmdb"))
        bio = asebytes.BlobIO(backend)
        bio.extend([{b"a": b"1"}, {b"b": b"2"}])
        return bio

    def test_valid_index(self, db):
        assert db[0] is not None
        assert db[1] is not None

    def test_negative_valid(self, db):
        assert db[-1] is not None
        assert db[-2] is not None

    def test_positive_oob_raises(self, db):
        with pytest.raises(IndexError):
            db[2]

    def test_large_positive_oob_raises(self, db):
        with pytest.raises(IndexError):
            db[100]

    def test_negative_oob_raises(self, db):
        with pytest.raises(IndexError):
            db[-3]

    def test_empty_db_any_index_raises(self, tmp_path):
        backend = asebytes.LMDBBlobBackend(str(tmp_path / "empty.lmdb"))
        db = asebytes.BlobIO(backend)
        with pytest.raises(IndexError):
            db[0]


class TestObjectIOBounds:
    @pytest.fixture
    def db(self, tmp_path):
        db = asebytes.ObjectIO(str(tmp_path / "test.lmdb"))
        db.extend([{"a": 1}, {"b": 2}])
        return db

    def test_positive_oob_raises(self, db):
        with pytest.raises(IndexError):
            db[2]

    def test_negative_oob_raises(self, db):
        with pytest.raises(IndexError):
            db[-3]


class TestASEIOBounds:
    @pytest.fixture
    def db(self, tmp_path, simple_atoms):
        db = asebytes.ASEIO(str(tmp_path / "test.lmdb"))
        db.extend([simple_atoms, simple_atoms])
        return db

    def test_positive_oob_raises(self, db):
        with pytest.raises(IndexError):
            db[2]

    def test_negative_oob_raises(self, db):
        with pytest.raises(IndexError):
            db[-3]

    def test_placeholder_returns_none(self, db):
        db.reserve(1)
        assert db.get(2) is None


# ── Async facades ─────────────────────────────────────────────────────────


class TestAsyncBlobIOBounds:
    @pytest.fixture
    def db(self, tmp_path):
        backend = asebytes.LMDBBlobBackend(str(tmp_path / "test.lmdb"))
        return asebytes.AsyncBlobIO(backend)

    @pytest.mark.anyio
    async def test_positive_oob_raises(self, db):
        await db.extend([{b"a": b"1"}])
        with pytest.raises(IndexError):
            await db[1]

    @pytest.mark.anyio
    async def test_negative_oob_raises(self, db):
        await db.extend([{b"a": b"1"}])
        with pytest.raises(IndexError):
            await db[-2]


class TestAsyncObjectIOBounds:
    @pytest.fixture
    def db(self, tmp_path):
        return asebytes.AsyncObjectIO(str(tmp_path / "test.lmdb"))

    @pytest.mark.anyio
    async def test_positive_oob_raises(self, db):
        await db.extend([{"a": 1}])
        with pytest.raises(IndexError):
            await db[1]


class TestAsyncASEIOBounds:
    @pytest.fixture
    def db(self, tmp_path):
        return asebytes.AsyncASEIO(str(tmp_path / "test.lmdb"))

    @pytest.mark.anyio
    async def test_positive_oob_raises(self, db, simple_atoms):
        await db.extend([simple_atoms])
        with pytest.raises(IndexError):
            await db[1]
```

### Step 2: Run tests to verify they fail

Run: `uv run pytest tests/test_index_bounds.py -v`
Expected: `test_positive_oob_raises` and `test_large_positive_oob_raises` FAIL (currently returns None instead of raising). The negative OOB tests may already pass due to existing negative-index handling.

### Step 3: Implement bounds checking in sync facades

**BlobIO** (`src/asebytes/_blob_io.py`): In `__getitem__`, after negative-index resolution (line 162-165), add upper-bounds check before calling `self._backend.get(index)`:

Replace lines 161-166:
```python
        if isinstance(index, int):
            if index < 0:
                index += len(self)
            if index < 0:
                raise IndexError(index)
            return self._backend.get(index)
```

With:
```python
        if isinstance(index, int):
            n = len(self)
            if index < 0:
                index += n
            if index < 0 or index >= n:
                raise IndexError(index)
            return self._backend.get(index)
```

**ObjectIO** (`src/asebytes/_object_io.py`): Same pattern at lines 168-177:

Replace:
```python
        if isinstance(index, int):
            if index < 0:
                index += len(self)
            if index < 0:
                raise IndexError(index)
            return self._backend.get(index)
```

With:
```python
        if isinstance(index, int):
            n = len(self)
            if index < 0:
                index += n
            if index < 0 or index >= n:
                raise IndexError(index)
            return self._backend.get(index)
```

**ASEIO** (`src/asebytes/io.py`): Same pattern at lines 211-217:

Replace:
```python
        if isinstance(index, int):
            if index < 0:
                index += len(self)  # raises TypeError if unknown
            if index < 0:
                raise IndexError(index)
            row = self._read_row(index)
            return dict_to_atoms(row)
```

With:
```python
        if isinstance(index, int):
            n = len(self)
            if index < 0:
                index += n
            if index < 0 or index >= n:
                raise IndexError(index)
            row = self._read_row(index)
            return dict_to_atoms(row)
```

### Step 4: Implement bounds checking in async facades

Apply the same pattern to all three async facades. The async facades use `AsyncSingleRowView` so the bounds check needs to happen before constructing the view. Find the `__getitem__` int branch in each async facade and add `n = len(self._backend)` (sync len) or appropriate bounds check.

**Note:** Async facades may need to check bounds inside the `AsyncSingleRowView.__await__` path since `len()` on async backends requires `await`. Check how each async facade resolves length. The `_async_blob_io.py`, `_async_object_io.py`, `_async_io.py` files all have `__len__` that calls sync `len(self._backend)` — so bounds checking in `__getitem__` before constructing the view should work.

### Step 5: Run tests to verify they pass

Run: `uv run pytest tests/test_index_bounds.py -v`
Expected: ALL PASS

### Step 6: Run full test suite to check for regressions

Run: `uv run pytest tests/ -v --timeout=120`
Expected: No regressions. Some existing tests that relied on `db[oob] → None` may need updating — fix those tests to use valid indices or expect IndexError.

### Step 7: Commit

```bash
git add tests/test_index_bounds.py src/asebytes/_blob_io.py src/asebytes/_object_io.py src/asebytes/io.py src/asebytes/_async_blob_io.py src/asebytes/_async_object_io.py src/asebytes/_async_io.py
git commit -m "feat: raise IndexError for out-of-bounds access on all facades"
```

---

## Task 2: Auto Copy Semantics per Backend

**Files:**
- Modify: `src/asebytes/_backends.py:14,85`
- Modify: `src/asebytes/_async_backends.py:17,84`
- Modify: `src/asebytes/_convert.py:71`
- Modify: `src/asebytes/decode.py:14`
- Modify: `src/asebytes/io.py:189-192,216-217`
- Modify: `src/asebytes/_async_io.py` (equivalent `_build_result`)
- Create: `tests/test_copy_semantics.py`

### Step 1: Write the failing tests

Create `tests/test_copy_semantics.py`:

```python
"""Tests for auto copy semantics based on backend mutability."""
from __future__ import annotations

import numpy as np
import pytest

import asebytes
from asebytes._backends import ReadBackend, ReadWriteBackend


class TestBackendMutabilityFlag:
    def test_read_backend_not_mutable(self):
        assert ReadBackend._returns_mutable is False

    def test_readwrite_backend_mutable(self):
        assert ReadWriteBackend._returns_mutable is True


class TestCopyOnReadWrite:
    """ReadWriteBackends should copy arrays (mutations don't corrupt storage)."""

    @pytest.fixture
    def db(self, tmp_path, simple_atoms):
        db = asebytes.ASEIO(str(tmp_path / "test.lmdb"))
        db.extend([simple_atoms])
        return db

    def test_returned_positions_are_copies(self, db):
        atoms = db[0]
        original = atoms.positions.copy()
        atoms.positions[:] = 999.0  # mutate
        atoms2 = db[0]
        np.testing.assert_array_equal(atoms2.positions, original)


class TestNoCopyOnReadOnly:
    """ReadBackends should NOT copy arrays (saves memory)."""

    def test_read_backend_flag(self):
        # Any concrete ReadBackend (not ReadWriteBackend) should have
        # _returns_mutable = False
        assert not ReadBackend._returns_mutable
```

### Step 2: Run tests to verify they fail

Run: `uv run pytest tests/test_copy_semantics.py -v`
Expected: `TestBackendMutabilityFlag` tests FAIL because `_returns_mutable` doesn't exist yet.

### Step 3: Add `_returns_mutable` to backend ABCs

**`src/asebytes/_backends.py`**: Add class attribute to both ABCs:

After line 23 (inside `ReadBackend` class body, before `list_groups`):
```python
    _returns_mutable: bool = False
```

After line 90 (inside `ReadWriteBackend` class body, before `set`):
```python
    _returns_mutable: bool = True
```

**`src/asebytes/_async_backends.py`**: Same pattern:

Inside `AsyncReadBackend` (after line 18):
```python
    _returns_mutable: bool = False
```

Inside `AsyncReadWriteBackend` (after line 84):
```python
    _returns_mutable: bool = True
```

### Step 4: Thread `copy=` through ASEIO's `_build_result`

**`src/asebytes/_convert.py`**: Add `copy` parameter to `dict_to_atoms`:

Change signature at line 71:
```python
def dict_to_atoms(data: dict[str, Any], fast: bool = True, copy: bool = True) -> ase.Atoms:
```

When `copy=True`, copy arrays before assigning. When `copy=False`, reference directly (current behavior at line 124-126). Add copying logic for array values:

At line 124-126, change:
```python
            atoms.arrays[array_name] = (
                value if isinstance(value, np.ndarray) else np.asarray(value)
            )
```

To:
```python
            arr = value if isinstance(value, np.ndarray) else np.asarray(value)
            atoms.arrays[array_name] = np.array(arr, copy=True) if copy else arr
```

Similarly for calc arrays at line 147:
```python
            _calc.results[calc_key] = np.array(value, copy=True) if copy and isinstance(value, np.ndarray) else value
```

**`src/asebytes/io.py`**: Pass `copy=` in `_build_result`:

Change lines 189-192:
```python
    def _build_result(self, row: dict[str, Any] | None) -> ase.Atoms | None:
        if row is None:
            return None
        return dict_to_atoms(row)
```

To:
```python
    def _build_result(self, row: dict[str, Any] | None) -> ase.Atoms | None:
        if row is None:
            return None
        copy = getattr(self._backend, '_returns_mutable', True)
        return dict_to_atoms(row, copy=copy)
```

Also change line 217 (`__getitem__` direct call):
```python
            return dict_to_atoms(row)
```
To:
```python
            copy = getattr(self._backend, '_returns_mutable', True)
            return dict_to_atoms(row, copy=copy)
```

Apply the same pattern to `_async_io.py` `_build_result`.

### Step 5: Run tests

Run: `uv run pytest tests/test_copy_semantics.py tests/test_copy_parameter.py -v`
Expected: ALL PASS

### Step 6: Run full test suite

Run: `uv run pytest tests/ -v --timeout=120`
Expected: No regressions.

### Step 7: Commit

```bash
git add src/asebytes/_backends.py src/asebytes/_async_backends.py src/asebytes/_convert.py src/asebytes/decode.py src/asebytes/io.py src/asebytes/_async_io.py tests/test_copy_semantics.py
git commit -m "feat: auto copy semantics — ReadBackend skips copies, ReadWriteBackend copies arrays"
```

---

## Task 3: `_n_atoms` Length Column for Zarr and H5MD

This is the largest task. Split into subtasks.

**Files:**
- Modify: `src/asebytes/_columnar.py`
- Modify: `src/asebytes/zarr/_backend.py`
- Modify: `src/asebytes/h5md/_backend.py`
- Create: `tests/test_n_atoms_zarr.py`
- Create: `tests/test_n_atoms_h5md.py`

### Step 1: Write the failing tests for Zarr

Create `tests/test_n_atoms_zarr.py`:

```python
"""Tests for _n_atoms length column in Zarr backend."""
from __future__ import annotations

import ase
import numpy as np
import pytest

import asebytes


@pytest.fixture
def zarr_path(tmp_path):
    return str(tmp_path / "test.zarr")


class TestDtypePreservation:
    """Per-atom integer arrays must NOT be promoted to float64."""

    def test_numbers_roundtrip_int(self, zarr_path):
        atoms = ase.Atoms("H2O", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        db = asebytes.ASEIO(zarr_path)
        db.extend([atoms])
        result = db[0]
        assert result.numbers.dtype == np.int64 or result.numbers.dtype == np.int32

    def test_custom_int_array_preserved(self, zarr_path):
        atoms = ase.Atoms("H2", positions=[[0, 0, 0], [1, 0, 0]])
        atoms.arrays["tags"] = np.array([1, 2], dtype=np.int32)
        db = asebytes.ASEIO(zarr_path)
        db.extend([atoms])
        result = db[0]
        assert result.arrays["tags"].dtype in (np.int32, np.int64)
        np.testing.assert_array_equal(result.arrays["tags"], [1, 2])


class TestVariableLengthRoundtrip:
    """Variable-length structures must roundtrip without data loss."""

    def test_varying_atom_counts(self, zarr_path):
        atoms_list = [
            ase.Atoms("H", positions=[[0, 0, 0]]),
            ase.Atoms("H2O", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]]),
            ase.Atoms("H2", positions=[[0, 0, 0], [1, 0, 0]]),
        ]
        db = asebytes.ASEIO(zarr_path)
        db.extend(atoms_list)

        for i, original in enumerate(atoms_list):
            result = db[i]
            assert len(result) == len(original)
            np.testing.assert_allclose(result.positions, original.positions)

    def test_column_access_varying_lengths(self, zarr_path):
        atoms_list = [
            ase.Atoms("H", positions=[[0, 0, 0]]),
            ase.Atoms("H3", positions=[[0, 0, 0], [1, 0, 0], [2, 0, 0]]),
        ]
        db = asebytes.ASEIO(zarr_path)
        db.extend(atoms_list)

        positions = db["arrays.positions"].to_list()
        assert len(positions[0]) == 1
        assert len(positions[1]) == 3


class TestNAtomsFillValue:
    """Fill values must be dtype-appropriate, not always NaN/float64."""

    def test_float_arrays_use_nan_fill(self, zarr_path):
        atoms = ase.Atoms("H", positions=[[1.5, 2.5, 3.5]])
        db = asebytes.ASEIO(zarr_path)
        db.extend([atoms])
        result = db[0]
        assert result.positions.dtype == np.float64

    def test_int_arrays_use_zero_fill(self, zarr_path):
        atoms = ase.Atoms("H2", positions=[[0, 0, 0], [1, 0, 0]])
        atoms.arrays["ids"] = np.array([10, 20], dtype=np.int64)
        db = asebytes.ASEIO(zarr_path)
        db.extend([atoms])
        result = db[0]
        # ids should be int, not float
        assert np.issubdtype(result.arrays["ids"].dtype, np.integer)
        np.testing.assert_array_equal(result.arrays["ids"], [10, 20])
```

### Step 2: Run tests to verify they fail

Run: `uv run pytest tests/test_n_atoms_zarr.py -v`
Expected: `TestDtypePreservation::test_custom_int_array_preserved` and `TestNAtomsFillValue::test_int_arrays_use_zero_fill` FAIL (int arrays currently come back as float64).

### Step 3: Update `_columnar.py`

Replace `strip_nan_padding` with `get_fill_value`:

```python
def get_fill_value(dtype: np.dtype) -> int | float:
    """Return an appropriate fill value for padding arrays of the given dtype.

    - Floating-point dtypes: NaN
    - Integer dtypes: 0
    - Boolean: False
    """
    if np.issubdtype(dtype, np.floating):
        return np.nan
    if np.issubdtype(dtype, np.integer):
        return 0
    if np.issubdtype(dtype, np.bool_):
        return False
    return 0
```

Update `concat_varying` to preserve dtype:

```python
def concat_varying(
    arrays: list[np.ndarray], fillvalue: float | int | None = None
) -> np.ndarray:
    """Concatenate arrays of varying shapes with padding.

    If fillvalue is None, uses get_fill_value based on the common dtype.
    """
    if not arrays:
        return np.array([])
    dtype = arrays[0].dtype
    if fillvalue is None:
        fillvalue = get_fill_value(dtype)
    maxshape = list(arrays[0].shape)
    for a in arrays[1:]:
        for i, (m, s) in enumerate(zip(maxshape, a.shape)):
            maxshape[i] = max(m, s)
    out = np.full((len(arrays), *maxshape), fillvalue, dtype=dtype)
    for i, a in enumerate(arrays):
        slices = tuple(slice(0, s) for s in a.shape)
        out[(i,) + slices] = a
    return out
```

Remove `strip_nan_padding` entirely.

### Step 4: Update Zarr backend

In `src/asebytes/zarr/_backend.py`, modify:

1. **Write path (`extend` / `_prepare_column` / `_pad_per_atom`):** Store `_n_atoms` column. Preserve original dtype when creating Zarr arrays. Use `get_fill_value(dtype)` instead of hardcoded `np.nan` / `np.float64`.

2. **Read path (`get` / `get_many` / `get_column` / `_postprocess`):** Read `_n_atoms[frame_index]` and slice `array[:n_atoms]` instead of calling `strip_nan_padding()`. Remove all `strip_nan_padding` calls.

3. **Key detail:** `_n_atoms` is stored as a regular Zarr array named `_n_atoms` in the same group. It's written during `extend()` alongside the data columns.

### Step 5: Update H5MD backend

Same pattern as Zarr. The H5MD backend stores `_n_atoms` as an HDF5 dataset. Update `_pad_per_atom`, `_postprocess_typed`, and read methods to use `_n_atoms` instead of `strip_nan_padding`.

### Step 6: Remove all `strip_nan_padding` imports

Search for and remove all imports/calls of `strip_nan_padding` across the codebase:

Run: `uv run python -c "import ast; print('done')"` to verify imports are clean.

### Step 7: Run tests

Run: `uv run pytest tests/test_n_atoms_zarr.py tests/test_zarr_backend.py tests/test_h5md_backend.py tests/test_dataset_roundtrip.py -v`
Expected: ALL PASS

### Step 8: Run full test suite

Run: `uv run pytest tests/ -v --timeout=120`
Expected: No regressions. Some tests may need updating if they asserted float64 dtype for integer arrays.

### Step 9: Commit

```bash
git add src/asebytes/_columnar.py src/asebytes/zarr/_backend.py src/asebytes/h5md/_backend.py tests/test_n_atoms_zarr.py tests/test_n_atoms_h5md.py
git commit -m "feat: _n_atoms length column for Zarr/H5MD — dtype preservation and O(1) reads"
```

---

## Task 4: LMDB Batch `get_column`

**Files:**
- Modify: `src/asebytes/lmdb/_backend.py:62-78`
- Create: `tests/test_lmdb_batch_get_column.py`

### Step 1: Write the failing test

Create `tests/test_lmdb_batch_get_column.py`:

```python
"""Tests for batched LMDB get_column (single cursor.getmulti call)."""
from __future__ import annotations

import numpy as np
import pytest

import asebytes


@pytest.fixture
def db(tmp_path):
    db = asebytes.ObjectIO(str(tmp_path / "test.lmdb"))
    rows = [{"energy": float(i), "name": f"mol_{i}"} for i in range(100)]
    db.extend(rows)
    return db


class TestBatchGetColumn:
    def test_full_column(self, db):
        energies = db["energy"].to_list()
        assert len(energies) == 100
        assert energies[0] == pytest.approx(0.0)
        assert energies[99] == pytest.approx(99.0)

    def test_partial_indices(self, db):
        energies = db[[0, 50, 99]]["energy"].to_list()
        assert energies == pytest.approx([0.0, 50.0, 99.0])

    def test_missing_key_returns_nones(self, db):
        result = db._backend.get_column("nonexistent", [0, 1, 2])
        assert result == [None, None, None]

    def test_column_with_placeholder(self, tmp_path):
        db = asebytes.ObjectIO(str(tmp_path / "sparse.lmdb"))
        db.extend([{"a": 1}])
        db.reserve(1)
        db.extend([{"a": 3}])
        result = db._backend.get_column("a", [0, 1, 2])
        assert result[0] == 1
        assert result[1] is None
        assert result[2] == 3

    def test_large_batch(self, tmp_path):
        db = asebytes.ObjectIO(str(tmp_path / "large.lmdb"))
        rows = [{"val": float(i)} for i in range(10_000)]
        db.extend(rows)
        result = db._backend.get_column("val")
        assert len(result) == 10_000
        assert result[0] == pytest.approx(0.0)
        assert result[9999] == pytest.approx(9999.0)
```

### Step 2: Run test to verify current behavior

Run: `uv run pytest tests/test_lmdb_batch_get_column.py -v`
Expected: All PASS (correctness is unchanged; we're optimizing performance). These tests serve as regression guards.

### Step 3: Implement batched get_column

Replace `_LMDBReadMixin.get_column` in `src/asebytes/lmdb/_backend.py` (lines 62-78):

```python
    def get_column(self, key: str, indices: list[int] | None = None) -> list[Any]:
        if indices is None:
            indices = list(range(len(self)))
        if not indices:
            return []
        byte_key = key.encode()
        with self._store.env.begin() as txn:
            self._store._ensure_cache(txn)
            # Build all LMDB keys at once for a single cursor.getmulti call
            lmdb_keys = []
            for i in indices:
                sort_key = self._store._resolve_sort_key(i)
                lmdb_keys.append(str(sort_key).encode() + b"-" + byte_key)
            fetched = dict(txn.cursor().getmulti(lmdb_keys))
            return [
                msgpack.unpackb(fetched[k], object_hook=m.decode)
                if k in fetched
                else None
                for k in lmdb_keys
            ]
```

### Step 4: Run tests

Run: `uv run pytest tests/test_lmdb_batch_get_column.py tests/test_lmdb_backend.py -v`
Expected: ALL PASS

### Step 5: Run full test suite

Run: `uv run pytest tests/ -v --timeout=120`
Expected: No regressions.

### Step 6: Commit

```bash
git add src/asebytes/lmdb/_backend.py tests/test_lmdb_batch_get_column.py
git commit -m "perf: batch LMDB get_column into single cursor.getmulti call"
```

---

## Task 5: `schema()` Method

**Files:**
- Create: `src/asebytes/_schema.py`
- Modify: `src/asebytes/_object_io.py`
- Modify: `src/asebytes/io.py`
- Modify: `src/asebytes/_async_object_io.py`
- Modify: `src/asebytes/_async_io.py`
- Modify: `src/asebytes/__init__.py` (export `SchemaEntry`)
- Create: `tests/test_schema.py`

### Step 1: Write the failing tests

Create `tests/test_schema.py`:

```python
"""Tests for schema() method on ObjectIO and ASEIO."""
from __future__ import annotations

import ase
import numpy as np
import pytest

import asebytes
from asebytes._schema import SchemaEntry


class TestSchemaEntry:
    def test_frozen(self):
        entry = SchemaEntry(dtype=np.dtype("float64"), shape=())
        with pytest.raises(AttributeError):
            entry.dtype = np.dtype("int32")

    def test_scalar(self):
        entry = SchemaEntry(dtype=np.dtype("float64"), shape=())
        assert entry.shape == ()

    def test_per_atom(self):
        entry = SchemaEntry(dtype=np.dtype("float64"), shape=("N", 3))
        assert entry.shape == ("N", 3)


class TestASEIOSchema:
    @pytest.fixture
    def db(self, tmp_path):
        atoms = ase.Atoms("H2O", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        atoms.info["smiles"] = "O"
        from ase.calculators.singlepoint import SinglePointCalculator

        calc = SinglePointCalculator(atoms, energy=-10.5)
        atoms.calc = calc
        db = asebytes.ASEIO(str(tmp_path / "test.lmdb"))
        db.extend([atoms])
        return db

    def test_schema_has_expected_keys(self, db):
        s = db.schema(0)
        assert "arrays.positions" in s
        assert "arrays.numbers" in s
        assert "calc.energy" in s
        assert "info.smiles" in s

    def test_positions_schema(self, db):
        s = db.schema(0)
        entry = s["arrays.positions"]
        assert entry.dtype == np.dtype("float64")
        # shape should indicate per-atom: ("N", 3) or (3, 3) for 3 atoms
        assert len(entry.shape) == 2

    def test_energy_scalar_schema(self, db):
        s = db.schema(0)
        entry = s["calc.energy"]
        assert entry.shape == ()

    def test_schema_no_index_uses_first_row(self, db):
        s = db.schema()
        assert "arrays.positions" in s

    def test_schema_empty_raises(self, tmp_path):
        db = asebytes.ASEIO(str(tmp_path / "empty.lmdb"))
        with pytest.raises(IndexError):
            db.schema()


class TestObjectIOSchema:
    @pytest.fixture
    def db(self, tmp_path):
        db = asebytes.ObjectIO(str(tmp_path / "test.lmdb"))
        db.extend([{"energy": -10.5, "forces": np.zeros((3, 3))}])
        return db

    def test_schema_keys(self, db):
        s = db.schema(0)
        assert "energy" in s
        assert "forces" in s

    def test_forces_shape(self, db):
        s = db.schema(0)
        assert s["forces"].shape == (3, 3)
        assert s["forces"].dtype == np.dtype("float64")
```

### Step 2: Run tests to verify they fail

Run: `uv run pytest tests/test_schema.py -v`
Expected: FAIL — `_schema` module doesn't exist, `schema()` method doesn't exist.

### Step 3: Create `_schema.py`

Create `src/asebytes/_schema.py`:

```python
"""Schema introspection types."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class SchemaEntry:
    """Describes one column's type and shape.

    Attributes
    ----------
    dtype : np.dtype | type
        The numpy dtype (for arrays/scalars) or Python type (for non-array values).
    shape : tuple[int | str, ...]
        Shape of the value. ``()`` for scalars. ``("N", 3)`` for per-atom 3D arrays
        where ``"N"`` indicates a variable dimension.
    """

    dtype: np.dtype | type
    shape: tuple[int | str, ...]


def infer_schema(row: dict[str, Any]) -> dict[str, SchemaEntry]:
    """Infer schema from a single row's values.

    Parameters
    ----------
    row : dict[str, Any]
        A single data row with string keys.

    Returns
    -------
    dict[str, SchemaEntry]
        Mapping from key name to its inferred schema entry.
    """
    schema: dict[str, SchemaEntry] = {}
    for key, value in row.items():
        if isinstance(value, np.ndarray):
            schema[key] = SchemaEntry(dtype=value.dtype, shape=value.shape)
        elif isinstance(value, (int, float, bool, np.integer, np.floating)):
            dtype = np.dtype(type(value)) if not isinstance(value, (np.integer, np.floating)) else np.dtype(value.dtype)
            schema[key] = SchemaEntry(dtype=dtype, shape=())
        elif isinstance(value, str):
            schema[key] = SchemaEntry(dtype=str, shape=())
        elif isinstance(value, list):
            schema[key] = SchemaEntry(dtype=list, shape=(len(value),))
        else:
            schema[key] = SchemaEntry(dtype=type(value), shape=())
    return schema
```

### Step 4: Add `schema()` to ObjectIO

In `src/asebytes/_object_io.py`, add after `keys()` (around line 73):

```python
    def schema(self, index: int | None = None) -> dict[str, SchemaEntry]:
        """Inspect column names, dtypes, and shapes.

        Parameters
        ----------
        index : int | None
            Row to inspect. If None, inspects row 0 as representative.

        Returns
        -------
        dict[str, SchemaEntry]
            Mapping from column name to dtype and shape info.
        """
        from ._schema import infer_schema

        if index is None:
            index = 0
        row = self._backend.get(index)
        if row is None:
            return {}
        return infer_schema(row)
```

### Step 5: Add `schema()` to ASEIO

In `src/asebytes/io.py`, add after `keys()` (around line 109):

```python
    def schema(self, index: int | None = None) -> dict[str, SchemaEntry]:
        """Inspect column names, dtypes, and shapes.

        Parameters
        ----------
        index : int | None
            Row to inspect. If None, inspects row 0 as representative.

        Returns
        -------
        dict[str, SchemaEntry]
            Mapping from column name to dtype and shape info.
        """
        from ._schema import infer_schema

        if index is None:
            index = 0
        row = self._read_row(index)
        if row is None:
            return {}
        return infer_schema(row)
```

### Step 6: Add async `schema()` to AsyncObjectIO and AsyncASEIO

Same pattern but `async def schema(...)` with `await self._backend.get(index)`.

### Step 7: Export `SchemaEntry` from `__init__.py`

Add `SchemaEntry` to the imports in `src/asebytes/__init__.py`.

### Step 8: Run tests

Run: `uv run pytest tests/test_schema.py -v`
Expected: ALL PASS

### Step 9: Run full test suite

Run: `uv run pytest tests/ -v --timeout=120`
Expected: No regressions.

### Step 10: Commit

```bash
git add src/asebytes/_schema.py src/asebytes/_object_io.py src/asebytes/io.py src/asebytes/_async_object_io.py src/asebytes/_async_io.py src/asebytes/__init__.py tests/test_schema.py
git commit -m "feat: add schema() method for column dtype/shape introspection"
```

---

## Task 6: Registry Unification

**Files:**
- Modify: `src/asebytes/_registry.py` (rewrite)
- Modify: `src/asebytes/_backends.py` (add `_registry_*` class attributes)
- Modify: `src/asebytes/_async_backends.py` (same)
- Modify: All backend modules (add `_registry_*` class attributes)
- Modify: `src/asebytes/_blob_io.py`, `_object_io.py`, `io.py` (use new resolver)
- Modify: `src/asebytes/_async_blob_io.py`, `_async_object_io.py`, `_async_io.py` (use new resolver)
- Create: `tests/test_unified_registry.py`

### Step 1: Write the failing tests

Create `tests/test_unified_registry.py`:

```python
"""Tests for unified registry with capability-declaring backends."""
from __future__ import annotations

from typing import Literal

import pytest

from asebytes._registry import resolve_backend


class TestResolveByExtension:
    def test_lmdb_object(self):
        cls = resolve_backend("data.lmdb", layer="object")
        assert cls is not None

    def test_zarr_object(self):
        cls = resolve_backend("data.zarr", layer="object")
        assert cls is not None

    def test_h5md_object(self):
        cls = resolve_backend("data.h5", layer="object")
        assert cls is not None

    def test_lmdb_blob(self):
        cls = resolve_backend("data.lmdb", layer="blob")
        assert cls is not None


class TestResolveByScheme:
    def test_memory_object(self):
        cls = resolve_backend("memory://test", layer="object")
        assert cls is not None

    def test_redis_blob(self):
        cls = resolve_backend("redis://localhost", layer="blob")
        assert cls is not None


class TestResolveAsync:
    def test_async_prefers_native(self):
        cls = resolve_backend("mongodb://localhost", layer="object", async_=True)
        assert cls is not None

    def test_async_falls_back_to_sync(self):
        cls = resolve_backend("data.lmdb", layer="object", async_=True)
        # Should return the sync class (caller wraps with SyncToAsyncAdapter)
        assert cls is not None


class TestResolveWritability:
    def test_writable_preferred(self):
        cls = resolve_backend("data.lmdb", layer="object", writable=True)
        assert cls is not None

    def test_readonly_available(self):
        cls = resolve_backend("data.lmdb", layer="object", writable=False)
        assert cls is not None


class TestUnknownPath:
    def test_unknown_extension_raises(self):
        with pytest.raises(ValueError, match="No backend"):
            resolve_backend("data.unknown", layer="object")

    def test_unknown_scheme_raises(self):
        with pytest.raises(ValueError, match="No backend"):
            resolve_backend("ftp://server/data", layer="object")
```

### Step 2: Run tests to verify they fail

Run: `uv run pytest tests/test_unified_registry.py -v`
Expected: FAIL — `resolve_backend` doesn't exist.

### Step 3: Add `_registry_*` class attributes to backend ABCs

In `src/asebytes/_backends.py`, add to `ReadBackend`:

```python
    _registry_patterns: list[str] = []
    _registry_schemes: list[str] = []
    _registry_layer: Literal["blob", "object"] = "object"
```

### Step 4: Add `_registry_*` to each concrete backend

Add class attributes to every backend class. Examples:

**LMDB blob backend** (`lmdb/_blob_backend.py`):
```python
class LMDBBlobBackend(ReadWriteBackend[bytes, bytes]):
    _registry_patterns = ["*.lmdb"]
    _registry_schemes: list[str] = []
    _registry_layer: Literal["blob", "object"] = "blob"
```

**LMDB object backend** (`lmdb/_backend.py`):
```python
class LMDBObjectBackend(_LMDBReadMixin, BlobToObjectReadWriteAdapter):
    _registry_patterns = ["*.lmdb"]
    _registry_schemes: list[str] = []
    _registry_layer: Literal["blob", "object"] = "object"
```

**Zarr backend** (`zarr/_backend.py`):
```python
class ZarrBackend(ReadWriteBackend[str, Any]):
    _registry_patterns = ["*.zarr"]
    _registry_schemes: list[str] = []
    _registry_layer: Literal["blob", "object"] = "object"
```

Continue for H5MD, MongoDB, Redis, Memory, HuggingFace, ASE backends.

### Step 5: Rewrite `_registry.py`

Replace the 6 registries and 4 resolver functions with a single `_REGISTRY` list and `resolve_backend()`:

```python
"""Unified backend registry.

Each backend class declares its capabilities via class attributes:
    _registry_patterns: list[str]  — file glob patterns (e.g. ["*.lmdb"])
    _registry_schemes: list[str]   — URI schemes (e.g. ["mongodb"])
    _registry_layer: Literal["blob", "object"]
"""
from __future__ import annotations

import fnmatch
from typing import Any, Literal
from urllib.parse import urlparse

_REGISTRY: list[tuple[str, str, str | None]] = [
    # (module_path, class_name, readonly_class_name | None)
    # ... entries for all backends
]

def parse_uri(path: str) -> tuple[str | None, str]:
    """Split path into (scheme, remainder). Returns (None, path) for plain paths."""
    if "://" in path:
        parsed = urlparse(path)
        return parsed.scheme, path
    return None, path


def resolve_backend(
    path_or_uri: str,
    *,
    layer: Literal["blob", "object"],
    async_: bool = False,
    writable: bool | None = None,
) -> type:
    """Resolve a path or URI to a backend class.

    Parameters
    ----------
    path_or_uri : str
        File path or URI (e.g., "data.lmdb", "mongodb://localhost").
    layer : Literal["blob", "object"]
        Required storage layer.
    async_ : bool
        If True, prefer native async backends.
    writable : bool | None
        If True, require writable. If False, require read-only. None = prefer writable.

    Returns
    -------
    type
        The resolved backend class.

    Raises
    ------
    ValueError
        If no matching backend found.
    """
    # Implementation: iterate _REGISTRY, match by scheme or pattern,
    # filter by layer, async, writable. Import lazily.
    ...
```

The detailed implementation imports backend modules lazily (same as current registry) and uses the class attributes for filtering. Keep the existing `parse_uri()` function.

**Also preserve backward compatibility** of the old function names (`get_backend_cls`, `get_blob_backend_cls`, etc.) as thin wrappers around `resolve_backend` — or update all call sites.

### Step 6: Update facade `__init__` methods

Update `BlobIO.__init__`, `ObjectIO.__init__`, `ASEIO.__init__` and their async counterparts to call `resolve_backend()` instead of `get_backend_cls()` / `get_blob_backend_cls()`.

### Step 7: Run tests

Run: `uv run pytest tests/test_unified_registry.py tests/test_registry_uri.py tests/test_async_uri_registry.py tests/test_registry_fallback.py tests/test_string_path_constructors.py -v`
Expected: ALL PASS

### Step 8: Run full test suite

Run: `uv run pytest tests/ -v --timeout=120`
Expected: No regressions.

### Step 9: Commit

```bash
git add src/asebytes/_registry.py src/asebytes/_backends.py src/asebytes/_async_backends.py src/asebytes/lmdb/ src/asebytes/zarr/ src/asebytes/h5md/ src/asebytes/_blob_io.py src/asebytes/_object_io.py src/asebytes/io.py src/asebytes/_async_blob_io.py src/asebytes/_async_object_io.py src/asebytes/_async_io.py tests/test_unified_registry.py
git commit -m "refactor: unify 6 backend registries into single resolve_backend()"
```

---

## Final Verification

After all 6 tasks are complete:

1. Run full test suite: `uv run pytest tests/ -v --timeout=120`
2. Run benchmarks to verify performance: `uv run pytest tests/benchmarks/ -m benchmark -v` (optional)
3. Check for any remaining `strip_nan_padding` references: search codebase
4. Verify all new code has type hints and uses `Literal` where appropriate
