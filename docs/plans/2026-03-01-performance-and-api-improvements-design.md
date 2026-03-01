# Performance and API Improvements Design

**Date:** 2026-03-01
**Status:** Approved
**Approach:** Test-driven development. Use `Literal` types and strong type hints throughout.
**Backward compatibility:** Not required (pre-release).

---

## 1. `_n_atoms` Length Column (Zarr + H5MD)

### Problem

Both columnar backends (Zarr, H5MD) pad variable-length per-atom arrays with NaN to rectangular shape. This:
- Promotes all per-atom arrays to `float64` (int32 arrays lose their dtype)
- Requires O(max_atoms) NaN-scanning on every read (`strip_nan_padding()`)
- Wastes disk space (int32 → float64 = 2x)

### Design

Store an explicit `_n_atoms` integer column alongside per-atom data. On read, slice `array[:n_atoms]` instead of scanning for NaN.

**Write path:**
1. Compute `n_atoms = len(positions)` (or `len(numbers)`) per frame
2. Store per-atom arrays padded to `max_atoms` **in their original dtype**, using a dtype-appropriate fill value (0 for ints, NaN for floats)
3. Write `_n_atoms[frame] = n_atoms` as int32

**Read path:**
1. Read `n_atoms = _n_atoms[frame]`
2. Return `array[:n_atoms]` — a zero-copy view, O(1)

**No backward compat fallback needed** — pre-release.

**Shared logic:** `_columnar.py` gains a `get_fill_value(dtype)` helper. `strip_nan_padding()` is removed.

### Files changed

- `src/asebytes/_columnar.py` — remove `strip_nan_padding`, add `get_fill_value(dtype)`
- `src/asebytes/zarr/_backend.py` — `_pad_per_atom`, `_postprocess`, `extend`, `get`, `get_many`, `get_column`
- `src/asebytes/h5md/_backend.py` — same methods
- Tests for both backends: verify dtype preservation, variable-length round-trip, int arrays

### Impact

| Operation | Before | After |
|---|---|---|
| Row read (per-atom col) | O(max_atoms) NaN scan | O(1) slice |
| Column read (N frames) | O(N * max_atoms) | O(N) int reads + O(N) slices |
| Append | 1 pad + 1 write per col | Same + 1 int write |
| Disk size | float64 always | Original dtype |

---

## 2. LMDB Batch `get_column`

### Problem

`get_column` loops N times calling `get_with_txn(txn, i, [key])`, each of which does a separate `cursor.getmulti([one_key])`. N syscall-level cursor operations.

### Design

Build the full LMDB key list upfront and issue a single `cursor.getmulti(all_keys)`:

```python
def get_column(self, key: str, indices: list[int] | None = None) -> list[Any]:
    byte_key = key.encode()
    if indices is None:
        indices = list(range(len(self)))
    with self._store.env.begin() as txn:
        lmdb_keys = [
            str(self._store._resolve_sort_key(i)).encode() + b"-" + byte_key
            for i in indices
        ]
        fetched = dict(txn.cursor().getmulti(lmdb_keys))
        return [
            msgpack.unpackb(fetched[k], object_hook=m.decode) if k in fetched else None
            for k in lmdb_keys
        ]
```

### Files changed

- `src/asebytes/lmdb/_backend.py` — `_LMDBReadMixin.get_column` (~15 lines)
- Tests: verify column read returns same results, benchmark N=10K

### Impact

| Operation | Before | After |
|---|---|---|
| get_column (N rows) | N cursor.getmulti calls | 1 cursor.getmulti call |
| get / get_many | Unaffected | Unaffected |
| Writes | Unaffected | Unaffected |

---

## 3. Copy Semantics (Auto per Backend)

### Problem

`decode.py` defaults to `copy=True`, creating unnecessary array copies for read-only backends (HuggingFace, ASE files). For large datasets this doubles memory.

### Design

Add a class-level attribute to backend ABCs:

```python
class ReadBackend(ABC, Generic[K, V]):
    _returns_mutable: bool = False

class ReadWriteBackend(ReadBackend[K, V]):
    _returns_mutable: bool = True
```

Facades check `self._backend._returns_mutable` and pass `copy=` to `decode()` / `dict_to_atoms()`:
- `_returns_mutable = True` → `copy=True` (safe mutation, in-memory backend stores references)
- `_returns_mutable = False` → `copy=False` (read-only source, no mutation risk)

Special case: In-memory `ReadWriteBackend` stores Python dicts with references — `copy=True` is essential. LMDB `ReadWriteBackend` returns fresh deserialized arrays — could be `copy=False`, but keeping `copy=True` for all `ReadWriteBackend` is simpler and safer.

### Files changed

- `src/asebytes/_backends.py` — add `_returns_mutable` attribute
- `src/asebytes/_async_backends.py` — same
- `src/asebytes/_convert.py` — thread `copy=` through `dict_to_atoms()`
- `src/asebytes/decode.py` — already has `copy=` parameter, just change call sites
- `src/asebytes/io.py`, `_object_io.py` — pass `copy=` when calling decode/convert
- `src/asebytes/_async_io.py`, `_async_object_io.py` — same
- Tests: verify read-only backends return views (not copies), read-write return copies

### Impact

| Operation | Before | After (read-only backend) |
|---|---|---|
| Row read | 1 copy per array | 0 copies |
| Column read | N copies | 0 copies |
| Bulk read | N * M copies | 0 copies |
| Writes | Unaffected | Unaffected |

---

## 4. IndexError for Out-of-Bounds

### Problem

`db[i]` returns `None` for both "placeholder row" and "index doesn't exist". This violates Python conventions and hides bugs.

### Design

Facades raise `IndexError` when `i >= len(db)` or `i < -len(db)`. `None` is reserved for placeholder rows from `reserve()`.

**Enforcement point:** Facade `__getitem__` and view `__getitem__`, before calling backend:

```python
def __getitem__(self, index: int) -> T:
    length = len(self)
    if index >= length or index < -length:
        raise IndexError(f"index {index} out of range for store with {length} entries")
    ...
```

### Files changed

- `src/asebytes/_blob_io.py`, `_object_io.py`, `io.py` — add bounds check in `__getitem__`
- `src/asebytes/_async_blob_io.py`, `_async_object_io.py`, `_async_io.py` — same
- `src/asebytes/_views.py`, `_async_views.py` — add bounds check in view `__getitem__`
- Tests: verify IndexError raised, verify None still returned for placeholders

### Impact

| Operation | Before | After |
|---|---|---|
| Valid index | Returns data | Same |
| Placeholder | Returns None | Returns None |
| Out-of-bounds | Returns None (silent) | Raises IndexError |

---

## 5. Registry Unification

### Problem

6 registries (`_BACKEND_REGISTRY`, `_BLOB_BACKEND_REGISTRY`, `_URI_REGISTRY`, `_ASYNC_URI_REGISTRY`, `_BLOB_URI_REGISTRY`, `_ASYNC_BLOB_URI_REGISTRY`) with duplicated resolution logic.

### Design

**Single registry** — a list of backend class references. Each backend declares capabilities via class attributes:

```python
from typing import Literal

class LMDBBlobBackend(ReadWriteBackend[bytes, bytes]):
    _registry_patterns: list[str] = ["*.lmdb"]
    _registry_schemes: list[str] = []
    _registry_layer: Literal["blob", "object"] = "blob"
    _registry_async_native: bool = False

class AsyncMongoObjectBackend(AsyncReadWriteBackend[str, Any]):
    _registry_patterns: list[str] = []
    _registry_schemes: list[str] = ["mongodb"]
    _registry_layer: Literal["blob", "object"] = "object"
    _registry_async_native: bool = True
```

**Single resolver function:**

```python
def resolve_backend(
    path_or_uri: str,
    *,
    layer: Literal["blob", "object"],
    async_: bool = False,
    writable: bool | None = None,
) -> type:
    ...
```

Resolution priority:
1. Match URI scheme, then file pattern
2. Filter by requested layer (blob/object)
3. If `async_=True`, prefer `_registry_async_native=True`; fall back to sync + `SyncToAsyncAdapter`
4. If `writable=None`, prefer writable; fall back to read-only
5. If layer mismatch, auto-wrap with adapter (BlobToObject or ObjectToBlob)

**Backend registration:** Backends register themselves by being imported. The registry collects all subclasses of `ReadBackend` / `AsyncReadBackend` that have `_registry_patterns` or `_registry_schemes`. Alternatively, an explicit `register(cls)` call in each backend's `__init__.py`.

### Files changed

- `src/asebytes/_registry.py` — rewrite (~100 lines → ~80 lines)
- All backend modules — add `_registry_*` class attributes
- Facade `__init__` methods — call `resolve_backend()` instead of `get_backend_cls()` / `get_blob_backend_cls()` etc.

### Impact

| Aspect | Before | After |
|---|---|---|
| Adding new backend | Patch 1-4 dicts | Add class attributes |
| Resolution functions | 4 functions, ~200 lines total | 1 function, ~40 lines |
| Runtime performance | O(patterns) dict lookup | O(backends) list scan |

---

## 6. `schema()` Method

### Problem

No way to inspect column names, dtypes, or shapes without reading data. `keys(index)` only returns names.

### Design

Add `schema(index: int | None = None) -> dict[str, SchemaEntry]` to all facades:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class SchemaEntry:
    dtype: np.dtype | type       # np.float64, np.int32, str, etc.
    shape: tuple[int | str, ...]  # () for scalar, ("N", 3) for variable per-atom

# Usage:
db.schema(0)
# {
#     "arrays.positions": SchemaEntry(dtype=np.dtype("float64"), shape=("N", 3)),
#     "arrays.numbers": SchemaEntry(dtype=np.dtype("int32"), shape=("N",)),
#     "calc.energy": SchemaEntry(dtype=np.dtype("float64"), shape=()),
# }
```

**Implementation:**
- Default (all backends): call `get(index)`, inspect each value with `np.asarray(v).dtype` and `.shape`
- Columnar backends (Zarr, H5MD): override to read from stored metadata (dtype from array, shape from array.shape[1:]) — O(1), no data read
- `index=None` → inspect row 0 as representative; document that schema may vary per row
- BlobIO: not applicable (bytes have no schema). Only ObjectIO and ASEIO.

**"N" sentinel:** Use the string `"N"` for the variable atom dimension. All other dimensions are concrete ints.

### Files changed

- `src/asebytes/_schema.py` (new) — `SchemaEntry` dataclass
- `src/asebytes/_object_io.py`, `io.py` — add `schema()` method
- `src/asebytes/_async_object_io.py`, `_async_io.py` — add async `schema()` method
- `src/asebytes/zarr/_backend.py`, `h5md/_backend.py` — override for O(1) schema
- Tests: verify schema output for various data types

### Impact

| Operation | Cost |
|---|---|
| `schema(i)` generic | 1 row read + type inspection |
| `schema(i)` Zarr/H5MD | O(1) metadata read |
| `schema()` | Same as `schema(0)` |

---

## Implementation Order

Based on dependencies and risk:

1. **IndexError for out-of-bounds** — smallest, no dependencies, improves all subsequent testing
2. **Copy semantics** — small, foundational for correctness
3. **`_n_atoms` length column** — medium, highest performance impact, benefits from #1 and #2
4. **LMDB batch get_column** — small, independent
5. **`schema()` method** — small, benefits from #3 (dtype preservation)
6. **Registry unification** — largest surface area, lowest risk (no behavior change), do last
