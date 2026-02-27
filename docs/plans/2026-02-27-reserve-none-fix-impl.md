# reserve/None Bug Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the 3 bugs surfaced by `tests/test_reserve_none.py` so all 40 parametrized tests pass.

**Architecture:** Each backend needs minimal, targeted changes. Zarr and H5MD need their `extend()` to filter out `None` rows while still incrementing `_n_frames` (since `len()` must count them). LMDB needs `get()` to return `None` when a row has no fields. No new abstractions needed.

**Tech Stack:** zarr, h5py, lmdb, numpy, pytest

---

## Bug 1: Zarr `extend()` crashes on None rows

**Root cause:** `zarr/_backend.py:231` does `{k for row in data for k in row}` which calls `__iter__` on `None`.

### Task 1: Fix Zarr `extend()` to handle None rows

**Files:**
- Modify: `src/asebytes/zarr/_backend.py:226-262`

**Step 1: Edit `extend()` to skip None rows in key collection and value extraction, but still count them in `n_new`**

In `src/asebytes/zarr/_backend.py`, the `extend` method (line ~226) needs these changes:

1. Filter None when collecting keys (line 231):
```python
# Before:
all_keys = sorted({k for row in data for k in row})

# After:
all_keys = sorted({k for row in data if row is not None for k in row})
```

2. Skip None rows when determining max atoms (lines 234-241):
```python
# Before:
for row in data:
    pos = row.get("arrays.positions")

# After:
for row in data:
    if row is None:
        continue
    pos = row.get("arrays.positions")
```

3. Handle None in value extraction (line 247):
```python
# Before:
values = [row.get(key) for row in data]

# After:
values = [row.get(key) if row is not None else None for row in data]
```

The `_write_column` method already handles `None` values in the values list (it writes fill values / NaN for missing data), so no changes needed there.

**Step 2: Make Zarr `get()` return None for rows with no data**

In `src/asebytes/zarr/_backend.py`, `get()` (line ~113) currently returns `{}` for a row where all columns have no data. After `reserve`, the reserved rows have no data written to any column, so `result` will be `{}`.

```python
# Before (line ~127):
return result

# After:
return result if result else None
```

Similarly, `get_many()` (line ~129) needs to propagate None. Check if its internal logic already builds per-row dicts — it does via columnar access. Apply same fix at the return point for each row.

Read `get_many` carefully and apply the same `or None` pattern to each row dict.

**Step 3: Run the zarr tests**

Run: `uv run pytest tests/test_reserve_none.py -k zarr -v --tb=short`

Expected: All 10 zarr tests pass.

**Step 4: Commit**

```bash
git add src/asebytes/zarr/_backend.py
git commit -m "fix: handle None rows in Zarr extend() and get()"
```

---

## Bug 2: H5MD `extend()` crashes on None rows

**Root cause:** Identical pattern to Zarr — `h5md/_backend.py:415` does `{k for row in data for k in row}`.

### Task 2: Fix H5MD `extend()` to handle None rows

**Files:**
- Modify: `src/asebytes/h5md/_backend.py:407-455`

**Step 1: Apply the same 3 fixes as Zarr's `extend()`**

1. Filter None when collecting keys (line 415):
```python
all_keys = sorted({k for row in data if row is not None for k in row})
```

2. Skip None in max atoms loop (lines 419-425):
```python
for row in data:
    if row is None:
        continue
    pos = row.get("arrays.positions")
```

3. Handle None in value extraction (line 434):
```python
values = [row.get(key) if row is not None else None for row in data]
```

4. Handle None in `_write_connectivity` call (line 437) — check if it iterates rows:
```python
# If _write_connectivity iterates data rows, filter None there too
```

**Step 2: Make H5MD `get()` return None for empty rows**

Same pattern as Zarr — `get()` returns `{}` for rows with no columns. Change the return to:
```python
return result if result else None
```

Apply same fix to `get_many()`.

**Step 3: Run the h5md tests**

Run: `uv run pytest tests/test_reserve_none.py -k h5md -v --tb=short`

Expected: All 10 h5md tests pass.

**Step 4: Commit**

```bash
git add src/asebytes/h5md/_backend.py
git commit -m "fix: handle None rows in H5MD extend() and get()"
```

---

## Bug 3: LMDB `get()` returns `{}` instead of `None`

**Root cause:** `LMDBBlobBackend.get_with_txn()` returns `{}` for rows with no fields. `LMDBObjectBackend.get()` deserializes `{}` to `{}`.

### Task 3: Fix LMDB blob backend `get()` to return None for empty rows

**Files:**
- Modify: `src/asebytes/lmdb/_blob_backend.py:216-252`

**Step 1: In `get_with_txn()`, return None when result is empty and no specific keys were requested**

The tricky part: if the caller asked for specific `keys` and got nothing back, that's a `KeyError` (existing behavior). But if no keys were requested and result is empty, that means the row is a None placeholder.

```python
# At line ~246, before return:
# If caller didn't request specific keys and got nothing, it's a None placeholder
if keys_set is None and not result:
    return None
return result
```

**Step 2: Run lmdb_blob tests**

Run: `uv run pytest tests/test_reserve_none.py -k lmdb_blob -v --tb=short`

Expected: All 10 lmdb_blob tests pass.

**Step 3: Commit**

```bash
git add src/asebytes/lmdb/_blob_backend.py
git commit -m "fix: LMDB blob get() returns None for empty placeholder rows"
```

---

### Task 4: Fix LMDB object backend `get()` to propagate None

**Files:**
- Modify: `src/asebytes/lmdb/_backend.py:57-63` and `src/asebytes/lmdb/_backend.py:65-84`

**Step 1: In `LMDBObjectReadBackend.get()`, propagate None from blob layer**

```python
# Before (line ~57-63):
def get(self, index, keys=None):
    self._check_index(index)
    byte_keys = [k.encode() for k in keys] if keys is not None else None
    raw = self._store.get(index, keys=byte_keys)
    return self._deserialize_row(raw)

# After:
def get(self, index, keys=None):
    self._check_index(index)
    byte_keys = [k.encode() for k in keys] if keys is not None else None
    raw = self._store.get(index, keys=byte_keys)
    if raw is None:
        return None
    return self._deserialize_row(raw)
```

**Step 2: Fix `iter_rows()` and `get_many()` to propagate None**

Both call `self._store.get_with_txn(txn, i, byte_keys)` and pass the result to `_deserialize_row`. Add None check before deserialization.

```python
# iter_rows — wrap the yield:
raw = self._store.get_with_txn(txn, i, byte_keys)
yield None if raw is None else self._deserialize_row(raw)

# get_many — wrap the list comprehension:
return [
    None if (raw := self._store.get_with_txn(txn, i, byte_keys)) is None
    else self._deserialize_row(raw)
    for i in indices
]
```

**Step 3: Run lmdb_object tests**

Run: `uv run pytest tests/test_reserve_none.py -k lmdb_object -v --tb=short`

Expected: All 10 lmdb_object tests pass.

**Step 4: Commit**

```bash
git add src/asebytes/lmdb/_backend.py
git commit -m "fix: LMDB object backend propagates None from blob layer"
```

---

### Task 5: Final verification — all 40 tests green

**Step 1: Run the full test file**

Run: `uv run pytest tests/test_reserve_none.py -v`

Expected: 40 passed, 0 failed.

**Step 2: Run full test suite to check for regressions**

Run: `uv run pytest --tb=short -q`

Expected: No new failures.

**Step 3: Commit if any fixups were needed, otherwise done**

---

## Summary

| Task | Backend | Fix | Files |
|------|---------|-----|-------|
| 1 | Zarr | Filter None in extend(), return None from get() | `zarr/_backend.py` |
| 2 | H5MD | Same as Zarr | `h5md/_backend.py` |
| 3 | LMDB blob | Return None from get_with_txn() for empty rows | `lmdb/_blob_backend.py` |
| 4 | LMDB object | Propagate None through get/iter_rows/get_many | `lmdb/_backend.py` |
| 5 | All | Full test suite verification | — |
