# Code Review Fixes — Design

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address all issues (2-13) from the code review of the backend abstraction refactor.

**Architecture:** Targeted fixes across 8 files — protocol extension, backend split, registry, view/index fixes, and minor cleanups. No new architectural concepts; all changes refine the existing design.

**Tech Stack:** Python, ASE, LMDB, msgpack

---

### Task 1: Add `update_row()` to WritableBackend protocol

**Files:**
- Modify: `src/asebytes/_protocols.py`
- Modify: `src/asebytes/lmdb/_backend.py`
- Modify: `src/asebytes/io.py`

**Changes:**

1. Add `update_row()` method to `WritableBackend` with default read-modify-write:
```python
def update_row(self, index: int, data: dict[str, Any]) -> None:
    """Partial update. Default: read-modify-write."""
    row = self.read_row(index)
    row.update(data)
    self.write_row(index, row)
```

2. Override in `LMDBBackend` with optimized partial update via `BytesIO.update()`:
```python
def update_row(self, index: int, data: dict[str, Any]) -> None:
    raw = {k.encode(): msgpack.packb(v, default=m.encode) for k, v in data.items()}
    self._store.update(index, raw)
```

3. Update `ASEIO.update()` to call `self._backend.update_row(index, flat_data)` instead of read-modify-write.

---

### Task 2: Split LMDBBackend into read-only and read-write classes

**Files:**
- Modify: `src/asebytes/lmdb/_backend.py`
- Modify: `src/asebytes/lmdb/__init__.py`
- Modify: `src/asebytes/__init__.py`

**Changes:**

Split into:
```python
class LMDBReadOnlyBackend(ReadableBackend):
    # __init__(file, prefix, map_size, **lmdb_kwargs) — always readonly=True
    # __len__, columns, read_row, read_rows, read_column
    # @property env -> self._store.env

class LMDBBackend(LMDBReadOnlyBackend, WritableBackend):
    # __init__(file, prefix, map_size, readonly=False, **lmdb_kwargs)
    # write_row, insert_row, delete_row, append_rows, update_row
```

Add `env` property on `LMDBReadOnlyBackend` to expose LMDB environment publicly.

Export `LMDBReadOnlyBackend` from `lmdb/__init__.py` and `asebytes/__init__.py`.

---

### Task 3: Implement batched LMDB reads (single transaction)

**Files:**
- Modify: `src/asebytes/lmdb/_backend.py`

**Changes:**

Override `read_rows()` and `read_column()` on `LMDBReadOnlyBackend` to use a single LMDB read transaction:

```python
def read_rows(self, indices, keys=None):
    byte_keys = [k.encode() for k in keys] if keys else None
    with self._store.env.begin() as txn:
        return [self._deserialize_row(self._store._get_with_txn(txn, i, byte_keys)) for i in indices]

def read_column(self, key, indices=None):
    if indices is None:
        indices = list(range(len(self)))
    byte_key = key.encode()
    with self._store.env.begin() as txn:
        return [msgpack.unpackb(self._store._get_with_txn(txn, i, [byte_key])[byte_key], object_hook=m.decode) for i in indices]
```

Note: This requires BytesIO to expose a `_get_with_txn(txn, index, keys)` helper, or we access the internals directly. Alternatively, just open one transaction and call the underlying LMDB cursor ourselves. Decide during implementation based on BytesIO internals.

---

### Task 4: Add backend registry with glob patterns

**Files:**
- Create: `src/asebytes/_registry.py`
- Modify: `src/asebytes/lmdb/__init__.py`
- Modify: `src/asebytes/io.py`

**Changes:**

```python
# _registry.py
import fnmatch
import importlib

# pattern -> (module_path, writable_cls_name | None, readonly_cls_name)
_BACKEND_REGISTRY: dict[str, tuple[str, str | None, str]] = {
    "*.lmdb": ("asebytes.lmdb", "LMDBBackend", "LMDBReadOnlyBackend"),
}

def get_backend_cls(path: str, *, readonly: bool = False):
    for pattern, (module_path, writable, read_only) in _BACKEND_REGISTRY.items():
        if fnmatch.fnmatch(path, pattern):
            mod = importlib.import_module(module_path)
            if not readonly and writable is None:
                raise TypeError(f"Backend for '{path}' is read-only, no writable variant available")
            cls_name = read_only if readonly else writable
            return getattr(mod, cls_name)
    raise KeyError(f"No backend registered for '{path}'")
```

Update `ASEIO.__init__()`:
```python
def __init__(self, backend, *, readonly=False, **kwargs):
    if isinstance(backend, str):
        from asebytes._registry import get_backend_cls
        cls = get_backend_cls(backend, readonly=readonly)
        self._backend = cls(backend, **kwargs)
    else:
        self._backend = backend
```

---

### Task 5: Fix index handling (issues #3, #4, #5)

**Files:**
- Modify: `src/asebytes/io.py`
- Modify: `src/asebytes/_views.py`

**Changes:**

1. **ASEIO.__getitem__ int bounds check (issue #5):**
```python
if isinstance(index, int):
    if index < 0:
        index += len(self)
    if index < 0 or index >= len(self):
        raise IndexError(index)
```

2. **ASEIO.__getitem__ list[int] negative normalization:**
```python
if isinstance(index, list) and index and isinstance(index[0], int):
    n = len(self)
    normalized = []
    for i in index:
        idx = i + n if i < 0 else i
        if idx < 0 or idx >= n:
            raise IndexError(i)
        normalized.append(idx)
    return RowView(self, normalized)
```

3. **RowView.__getitem__ empty list (issue #4):**
Add `if not key: return RowView(self._parent, [])` before the isinstance checks.

4. **RowView.__getitem__ int negative normalization:**
Already handled by `_sub_select` (Python list negative indexing), but add bounds check after.

5. **RowView.__getitem__ list[int] negative normalization:**
Same pattern as ASEIO.

---

### Task 6: Fix BytesIO.__delitem__ negative indices (issue #7)

**Files:**
- Modify: `src/asebytes/_bytesio.py`

**Changes:**

```python
def __delitem__(self, key: int) -> None:
    with self.env.begin(write=True) as txn:
        current_count = self._get_count(txn)
        if key < 0:
            key += current_count
        if key < 0 or key >= current_count:
            raise IndexError(f"Index {key} out of range [0, {current_count})")
```

---

### Task 7: Add ViewParent Protocol and __bool__ to views (issues #9, #11)

**Files:**
- Modify: `src/asebytes/_views.py`

**Changes:**

1. Add `ViewParent` Protocol:
```python
from typing import Protocol

class ViewParent(Protocol):
    def __len__(self) -> int: ...
    def _read_row(self, index: int, keys: list[str] | None = None) -> dict[str, Any]: ...
    def _read_rows(self, indices: list[int], keys: list[str] | None = None) -> list[dict[str, Any]]: ...
    def _read_column(self, key: str, indices: list[int]) -> list[Any]: ...
    def _build_atoms(self, row: dict[str, Any]) -> ase.Atoms: ...
```

2. Type `parent` as `ViewParent` in RowView and ColumnView.

3. Add `__bool__` to both:
```python
def __bool__(self) -> bool:
    return len(self) > 0
```

---

### Task 8: Minor cleanups (issues #8, #10, #12)

**Files:**
- Modify: `src/asebytes/_convert.py` (docstring note)
- Modify: `tests/test_benchmark_backend.py` (remove unused import)
- Modify: `tests/test_lmdb_config.py` (use `_backend.env` instead of `_backend._store.env`)

**Changes:**

1. Add docstring note to `dict_to_atoms`:
   > "Arrays are referenced, not copied. For LMDB backends this is safe (deserialization creates fresh arrays). In-memory backends should copy if mutation is a concern."

2. Remove `import ase` from `test_benchmark_backend.py`.

3. Update `test_lmdb_config.py`:
   - `db._backend._store.env` → `db._backend.env`
   - `db_write._backend._store.env` → `db_write._backend.env`

---

### Task 9: Update tests for new behavior

**Files:**
- Modify: `tests/test_lmdb_backend.py` (add LMDBReadOnlyBackend tests)
- Modify: `tests/test_aseio_views.py` (add update_row, readonly, registry, index edge case tests)
- Modify: `tests/test_protocols.py` (add update_row test)

**Changes:**

- Test `LMDBReadOnlyBackend` separately (read works, write raises)
- Test `ASEIO(path, readonly=True)` creates read-only backend, write operations raise `TypeError`
- Test `update_row` partial update only writes changed keys
- Test backend registry with `*.lmdb` pattern and unknown pattern raises `KeyError`
- Test negative index normalization in `ASEIO.__getitem__` and views
- Test empty list returns empty view
- Test `bool(empty_view)` is False, `bool(non_empty_view)` is True

---

### Task 10: Run full test suite + benchmarks

Verify all tests pass and no performance regressions from the changes.
