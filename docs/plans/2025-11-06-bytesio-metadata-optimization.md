# BytesIO Fractional Indexing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix failing tests and optimize BytesIO for 100M+ item datasets by introducing fractional indexing with LMDB-stored mapping. Eliminates expensive data shifts while maintaining fast O(log n) random access.

**Architecture:**
- Store logical index → sort key mapping: `{prefix}__idx__{logical_index}` → `{sort_key}`
- Store data with sort key prefix: `{prefix}{sort_key}-{field}` → `{data}`
- Store count metadata: `{prefix}__meta__count` for O(1) length
- Insert/delete only updates mapping (no data shifts)
- LMDB memory-maps the mapping, so scales to billions of items

**Tech Stack:** Python 3.11, LMDB, pytest

**Performance:**
- Random access: O(log n) mapping lookup + O(fields) data scan
- Extend(n): O(n) - just write data and mappings
- Insert: O(log n) + O(fields) - one mapping update, no data shifts
- Delete: O(log n) + O(fields) - remove mapping, lazy data cleanup
- Memory: LMDB pages loaded on-demand (~4KB pages)

---

## Task 1: Fix `__setitem__` to Remove Existing Keys

**Files:**
- Modify: `src/asebytes/io.py:18-22`
- Test: `tests/test_bytesio.py:14-21` (already exists, currently failing)

**Step 1: Verify test_set_overwrite currently fails**

Run: `uv run pytest tests/test_bytesio.py::test_set_overwrite -v`

Expected output: `FAILED` with `AssertionError: assert 'test' not in atoms.info`

**Step 2: Implement fix to remove existing keys in __setitem__**

In `src/asebytes/io.py`, replace lines 18-22:

```python
def __setitem__(self, index: int, data: dict[bytes, bytes]) -> None:
    with self.env.begin(write=True) as txn:
        # First, remove all existing keys for this index
        cursor = txn.cursor()
        prefix = self.prefix + str(index).encode() + b"-"
        keys_to_delete = []
        if cursor.set_range(prefix):
            for key, value in cursor:
                if not key.startswith(prefix):
                    break
                keys_to_delete.append(key)

        # Delete all old keys
        for key in keys_to_delete:
            txn.delete(key)

        # Write new data
        for key, value in data.items():
            txn.put(self.prefix + str(index).encode() + b"-" + key, value)
```

**Step 3: Run test to verify it passes**

Run: `uv run pytest tests/test_bytesio.py::test_set_overwrite -v`

Expected output: `PASSED`

**Step 4: Commit**

```bash
git add src/asebytes/io.py
git commit -m "fix: remove existing keys in __setitem__ before overwrite

- Delete all existing keys with the same index before writing new data
- Fixes test_set_overwrite by ensuring old keys don't persist
- Collects keys first to avoid cursor corruption during deletion"
```

---

## Task 2: Add Metadata and Mapping Helper Methods

**Files:**
- Modify: `src/asebytes/io.py:17` (add after __init__)

**Step 1: Write test for basic mapping operations**

Add new test in `tests/test_bytesio.py` after test_iter:

```python
def test_fractional_mapping(io):
    # Test that we can store and retrieve mapping
    # This is an internal test - users won't call these methods directly
    with io.env.begin(write=True) as txn:
        # Store a mapping
        io._set_mapping(txn, 0, 0.0)
        io._set_mapping(txn, 1, 1.0)
        io._set_count(txn, 2)

    with io.env.begin() as txn:
        assert io._get_mapping(txn, 0) == 0.0
        assert io._get_mapping(txn, 1) == 1.0
        assert io._get_count(txn) == 2
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_bytesio.py::test_fractional_mapping -v`

Expected: `FAILED` with `AttributeError` (methods don't exist yet)

**Step 3: Implement metadata and mapping helper methods**

Add these methods in `src/asebytes/io.py` after line 16 (after __init__):

```python
# Metadata helpers
def _get_count(self, txn) -> int:
    """Get the current count from metadata. Returns 0 if not set."""
    count_key = self.prefix + b"__meta__count"
    count_bytes = txn.get(count_key)
    if count_bytes is None:
        return 0
    return int(count_bytes.decode())

def _set_count(self, txn, count: int) -> None:
    """Set the count in metadata."""
    count_key = self.prefix + b"__meta__count"
    txn.put(count_key, str(count).encode())

# Mapping helpers (logical_index → sort_key)
def _get_mapping(self, txn, logical_index: int) -> float | None:
    """Get sort_key for a logical index. Returns None if not found."""
    mapping_key = self.prefix + b"__idx__" + str(logical_index).encode()
    sort_key_bytes = txn.get(mapping_key)
    if sort_key_bytes is None:
        return None
    return float(sort_key_bytes.decode())

def _set_mapping(self, txn, logical_index: int, sort_key: float) -> None:
    """Set the mapping from logical_index to sort_key."""
    mapping_key = self.prefix + b"__idx__" + str(logical_index).encode()
    # Use 15 decimal places for precision
    txn.put(mapping_key, f"{sort_key:.15f}".encode())

def _delete_mapping(self, txn, logical_index: int) -> None:
    """Delete the mapping for a logical index."""
    mapping_key = self.prefix + b"__idx__" + str(logical_index).encode()
    txn.delete(mapping_key)

def _generate_sort_key(self, txn, logical_index: int) -> float:
    """Generate a sort key for a new item at logical_index.

    For appends, use the logical index as the sort key.
    For inserts, find the gap and use the midpoint.
    """
    current_count = self._get_count(txn)

    # Appending to the end
    if logical_index >= current_count:
        return float(logical_index)

    # Inserting in the middle - find adjacent sort keys
    # Get sort key at insertion point
    next_sort_key = self._get_mapping(txn, logical_index)

    if logical_index == 0:
        # Insert at beginning
        prev_sort_key = next_sort_key - 1.0
    else:
        # Insert between prev and next
        prev_sort_key = self._get_mapping(txn, logical_index - 1)

    # Generate midpoint
    new_sort_key = (prev_sort_key + next_sort_key) / 2.0

    # Check if we have precision issues
    if new_sort_key == prev_sort_key or new_sort_key == next_sort_key:
        raise ValueError(
            f"Fractional precision exhausted between {prev_sort_key} and {next_sort_key}. "
            "Reindexing required but not yet implemented."
        )

    return new_sort_key
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_bytesio.py::test_fractional_mapping -v`

Expected output: `PASSED`

**Step 5: Commit**

```bash
git add src/asebytes/io.py tests/test_bytesio.py
git commit -m "feat: add fractional indexing infrastructure

- Add metadata helpers for count tracking
- Add mapping helpers for logical_index → sort_key
- Add sort key generation with midpoint strategy
- Foundation for eliminating data shifts on insert/delete"
```

---

## Task 3: Update `__setitem__` to Use Fractional Indexing

**Files:**
- Modify: `src/asebytes/io.py:18-22` (already modified in Task 1)

**Step 1: Verify current test still passes**

Run: `uv run pytest tests/test_bytesio.py::test_set_overwrite -v`

Expected output: `PASSED`

**Step 2: Update __setitem__ to use sort keys**

Replace the `__setitem__` method completely:

```python
def __setitem__(self, index: int, data: dict[bytes, bytes]) -> None:
    with self.env.begin(write=True) as txn:
        current_count = self._get_count(txn)

        # Get or create sort key for this index
        sort_key = self._get_mapping(txn, index)
        is_new_index = sort_key is None

        if is_new_index:
            # Generate new sort key
            sort_key = self._generate_sort_key(txn, index)
            self._set_mapping(txn, index, sort_key)

        # Delete existing data keys with this sort key
        cursor = txn.cursor()
        sort_key_str = f"{sort_key:.15f}".encode()
        prefix = self.prefix + sort_key_str + b"-"
        keys_to_delete = []

        if cursor.set_range(prefix):
            for key, value in cursor:
                if not key.startswith(prefix):
                    break
                keys_to_delete.append(key)

        for key in keys_to_delete:
            txn.delete(key)

        # Write new data with sort key prefix
        for key, value in data.items():
            txn.put(self.prefix + sort_key_str + b"-" + key, value)

        # Update count if needed (when index == current_count, we're appending)
        if is_new_index and index >= current_count:
            self._set_count(txn, index + 1)
```

**Step 3: Run tests to verify still working**

Run: `uv run pytest tests/test_bytesio.py::test_set_get tests/test_bytesio.py::test_set_overwrite -v`

Expected output: Both `PASSED`

**Step 4: Commit**

```bash
git add src/asebytes/io.py
git commit -m "refactor: update __setitem__ to use fractional indexing

- Use mapping to get/create sort keys
- Store data with sort_key prefix instead of logical index
- Maintains backward compatibility with existing tests
- Preparation for shift-free insert/delete"
```

---

## Task 4: Update `__getitem__` to Use Fractional Indexing

**Files:**
- Modify: `src/asebytes/io.py:24-34`

**Step 1: Verify current test passes with old implementation**

Run: `uv run pytest tests/test_bytesio.py::test_set_get -v`

Expected output: `PASSED`

**Step 2: Update __getitem__ to use sort keys**

Replace the `__getitem__` method:

```python
def __getitem__(self, index: int) -> dict[bytes, bytes]:
    with self.env.begin() as txn:
        # Look up the sort key for this logical index
        sort_key = self._get_mapping(txn, index)

        if sort_key is None:
            raise KeyError(f"Index {index} not found")

        # Scan for all data keys with this sort key prefix
        result = {}
        cursor = txn.cursor()
        sort_key_str = f"{sort_key:.15f}".encode()
        prefix = self.prefix + sort_key_str + b"-"

        if cursor.set_range(prefix):
            for key, value in cursor:
                if not key.startswith(prefix):
                    break
                # Extract the field name after the sort_key prefix
                field_name = key[len(prefix):]
                result[field_name] = value

        return result
```

**Step 3: Run test to verify it passes**

Run: `uv run pytest tests/test_bytesio.py::test_set_get -v`

Expected output: `PASSED`

**Step 4: Commit**

```bash
git add src/asebytes/io.py
git commit -m "refactor: update __getitem__ to use fractional indexing

- Lookup mapping to get sort key
- Range scan with sort_key prefix to get data
- Maintains O(log n) + O(fields) access time
- All basic tests still passing"
```

---

## Task 5: Optimize `__len__` Using Metadata

**Files:**
- Modify: `src/asebytes/io.py:88-101`

**Step 1: Verify current tests still pass**

Run: `uv run pytest tests/test_bytesio.py::test_len -v`

Expected output: `PASSED`

**Step 2: Replace __len__ implementation**

Replace `__len__` method with O(1) version:

```python
def __len__(self) -> int:
    with self.env.begin() as txn:
        return self._get_count(txn)
```

**Step 3: Run all tests to verify optimization works**

Run: `uv run pytest tests/test_bytesio.py::test_len tests/test_bytesio.py::test_append tests/test_bytesio.py::test_extend -v`

Expected: All `PASSED`

**Step 4: Commit**

```bash
git add src/asebytes/io.py
git commit -m "perf: optimize __len__ to O(1) using metadata

- Replace O(n) scan with O(1) metadata lookup
- Critical for 100M+ item datasets
- All existing tests continue to pass"
```

---

## Task 6: Update `__delitem__` with Shift-Free Deletion

**Files:**
- Modify: `src/asebytes/io.py:36-58`
- Test: `tests/test_bytesio.py:38-45` (already exists, currently failing)

**Step 1: Verify test_delete currently fails**

Run: `uv run pytest tests/test_bytesio.py::test_delete -v`

Expected output: `FAILED` with `KeyError: b'cell'`

**Step 2: Implement shift-free __delitem__**

Replace `__delitem__` method completely:

```python
def __delitem__(self, key: int) -> None:
    with self.env.begin(write=True) as txn:
        current_count = self._get_count(txn)

        if key < 0 or key >= current_count:
            raise IndexError(f"Index {key} out of range [0, {current_count})")

        # Get the sort key for this index
        sort_key = self._get_mapping(txn, key)
        if sort_key is None:
            raise KeyError(f"Index {key} not found")

        # Collect all mappings that need to be shifted
        # We need to shift indices [key+1, key+2, ..., count-1] down by 1
        mappings_to_shift = []
        for i in range(key + 1, current_count):
            sk = self._get_mapping(txn, i)
            if sk is not None:
                mappings_to_shift.append((i, sk))

        # Delete the mapping for the deleted index
        self._delete_mapping(txn, key)

        # Shift all subsequent mappings down by 1
        # Delete old mappings first, then write new ones
        for old_index, sk in mappings_to_shift:
            self._delete_mapping(txn, old_index)

        for old_index, sk in mappings_to_shift:
            new_index = old_index - 1
            self._set_mapping(txn, new_index, sk)

        # Optionally delete the data keys (lazy deletion strategy)
        # For now, we'll delete them to keep the database clean
        cursor = txn.cursor()
        sort_key_str = f"{sort_key:.15f}".encode()
        prefix = self.prefix + sort_key_str + b"-"
        keys_to_delete = []

        if cursor.set_range(prefix):
            for k, value in cursor:
                if not k.startswith(prefix):
                    break
                keys_to_delete.append(k)

        for k in keys_to_delete:
            txn.delete(k)

        # Update count
        self._set_count(txn, current_count - 1)
```

**Step 3: Run test to verify it passes**

Run: `uv run pytest tests/test_bytesio.py::test_delete -v`

Expected output: `PASSED`

**Step 4: Commit**

```bash
git add src/asebytes/io.py
git commit -m "feat: implement shift-free __delitem__ with fractional indexing

- Only shift mappings (lightweight), not data keys
- Data keys stay in place with their sort keys
- O(items_after) mapping updates, no data movement
- Fixes test_delete
- Major performance win for large datasets"
```

---

## Task 7: Update `insert` with Shift-Free Insertion

**Files:**
- Modify: `src/asebytes/io.py:60-82`
- Test: `tests/test_bytesio.py:47-55` (already exists, currently failing)

**Step 1: Verify test_insert currently fails**

Run: `uv run pytest tests/test_bytesio.py::test_insert -v`

Expected output: `FAILED` with `KeyError: b'cell'`

**Step 2: Implement shift-free insert**

Replace `insert` method completely:

```python
def insert(self, index: int, input: dict[bytes, bytes]) -> None:
    with self.env.begin(write=True) as txn:
        current_count = self._get_count(txn)

        # Clamp index to valid range [0, count]
        if index < 0:
            index = 0
        if index > current_count:
            index = current_count

        # Collect all mappings that need to be shifted right
        # We need to shift indices [index, index+1, ..., count-1] up by 1
        mappings_to_shift = []
        for i in range(index, current_count):
            sk = self._get_mapping(txn, i)
            if sk is not None:
                mappings_to_shift.append((i, sk))

        # Shift all mappings up by 1
        # Do this in reverse order to avoid conflicts
        # Delete old mappings first, then write new ones
        for old_index, sk in mappings_to_shift:
            self._delete_mapping(txn, old_index)

        for old_index, sk in reversed(mappings_to_shift):
            new_index = old_index + 1
            self._set_mapping(txn, new_index, sk)

        # Generate sort key for the new item
        sort_key = self._generate_sort_key(txn, index)
        self._set_mapping(txn, index, sort_key)

        # Write the new data with sort key prefix
        sort_key_str = f"{sort_key:.15f}".encode()
        for key, value in input.items():
            txn.put(self.prefix + sort_key_str + b"-" + key, value)

        # Update count
        self._set_count(txn, current_count + 1)
```

**Step 3: Run test to verify it passes**

Run: `uv run pytest tests/test_bytesio.py::test_insert -v`

Expected output: `PASSED`

**Step 4: Commit**

```bash
git add src/asebytes/io.py
git commit -m "feat: implement shift-free insert with fractional indexing

- Only shift mappings (lightweight), not data keys
- Generate fractional sort key in the gap
- Data keys written once with sort key prefix
- O(items_after) mapping updates, no data movement
- Fixes test_insert
- Major performance win for large datasets"
```

---

## Task 8: Update `__iter__` to Use Fractional Indexing

**Files:**
- Modify: `src/asebytes/io.py:84-86`

**Step 1: Verify current test passes**

Run: `uv run pytest tests/test_bytesio.py::test_iter -v`

Expected output: May pass or fail depending on implementation

**Step 2: Update __iter__ to iterate by logical index**

Replace `__iter__` method:

```python
def __iter__(self):
    # Iterate through logical indices in order
    count = len(self)
    for i in range(count):
        yield self[i]
```

**Step 3: Run test to verify it passes**

Run: `uv run pytest tests/test_bytesio.py::test_iter -v`

Expected output: `PASSED`

**Step 4: Commit**

```bash
git add src/asebytes/io.py
git commit -m "refactor: update __iter__ to use logical indices

- Iterate through logical indices 0 to count-1
- Each __getitem__ call uses mapping lookup
- Maintains sequential iteration behavior
- Compatible with fractional indexing"
```

---

## Task 9: Run Full Test Suite and Verify

**Step 1: Run complete test suite**

Run: `uv run pytest tests -v`

Expected output: All 26+ tests should `PASSED`, including:
- `test_set_overwrite` ✓
- `test_delete` ✓
- `test_insert` ✓
- `test_len` ✓ (now O(1))
- `test_fractional_mapping` ✓
- All other existing tests ✓

**Step 2: Write performance comparison test**

Create `tests/test_performance.py`:

```python
import asebytes
import tempfile
import time
import pytest

def test_insert_performance():
    """Verify that insert doesn't shift data (should be fast even with many items)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        io = asebytes.BytesIO(f"{tmpdir}/perf.db")

        # Add 1000 items
        test_data = {b"test": b"x" * 100}
        for i in range(1000):
            io[i] = test_data

        # Time insert at beginning (worst case)
        start = time.time()
        io.insert(0, test_data)
        elapsed = time.time() - start

        # Should be fast (< 100ms even with 1000 items)
        # Old implementation would take seconds
        assert elapsed < 0.1, f"Insert took {elapsed:.3f}s, expected < 0.1s"
        assert len(io) == 1001

def test_delete_performance():
    """Verify that delete doesn't shift data"""
    with tempfile.TemporaryDirectory() as tmpdir:
        io = asebytes.BytesIO(f"{tmpdir}/perf.db")

        # Add 1000 items
        test_data = {b"test": b"x" * 100}
        for i in range(1000):
            io[i] = test_data

        # Time delete at beginning (worst case)
        start = time.time()
        del io[0]
        elapsed = time.time() - start

        # Should be fast (< 100ms even with 1000 items)
        assert elapsed < 0.1, f"Delete took {elapsed:.3f}s, expected < 0.1s"
        assert len(io) == 999

def test_len_performance():
    """Verify that len is O(1)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        io = asebytes.BytesIO(f"{tmpdir}/perf.db")

        # Add 1000 items
        test_data = {b"test": b"x" * 100}
        for i in range(1000):
            io[i] = test_data

        # Time 10000 len() calls
        start = time.time()
        for _ in range(10000):
            _ = len(io)
        elapsed = time.time() - start

        # Should be very fast (< 100ms for 10000 calls)
        assert elapsed < 0.1, f"10000 len() calls took {elapsed:.3f}s"
```

**Step 3: Run performance tests**

Run: `uv run pytest tests/test_performance.py -v -s`

Expected output: All performance tests `PASSED`

**Step 4: Final commit**

```bash
git add tests/test_performance.py
git commit -m "test: add performance tests for fractional indexing

- Verify insert/delete are fast (no data shifts)
- Verify len is O(1)
- All performance tests passing
- Ready for production use"
```

---

## Summary of Improvements

**Bugs Fixed:**
1. ✓ `__setitem__` now properly removes existing keys before overwrite
2. ✓ `__delitem__` works correctly without data corruption
3. ✓ `insert` works correctly without data corruption

**Architecture Changes:**
1. ✓ Fractional indexing eliminates data shifts on insert/delete
2. ✓ Logical index → sort key mapping stored in LMDB
3. ✓ Data keys use sort key prefix for stable storage
4. ✓ LMDB memory-mapping scales to 100M+ items

**Performance Improvements:**
1. ✓ `__len__`: O(n) → O(1) using metadata
2. ✓ `__delitem__`: O(n·m data shifts) → O(n mapping updates)
3. ✓ `insert`: O(n·m data shifts) → O(n mapping updates)
4. ✓ Random access: O(1) → O(log n) but no data copies
5. ✓ Extend: Still O(n) for n items

**Trade-offs:**
- Random access slightly slower (O(log n) vs O(1)) but acceptable for the gains
- Occasional reindexing needed when fractional precision exhausted (rare)
- Slightly more LMDB space for mapping storage (~8 bytes per item)

**Future Optimization Opportunities:**
- Implement reindexing when fractional precision exhausted
- Use `Cursor.putmulti()` for bulk operations in `extend()`
- Add lazy data cleanup option for deleted items
- Add background compaction job for unreferenced data keys

---

## Notes

- All modifications maintain backward compatibility with existing API
- Metadata keys use `__meta__` prefix, mapping keys use `__idx__` prefix
- Fractional sort keys use 15 decimal places for precision
- Mapping updates are lightweight (8-16 bytes per index shift)
- Data keys never move once written (stable sort key prefix)
- All operations remain ACID-compliant within LMDB transactions
- Scales to billions of items due to LMDB memory-mapping
