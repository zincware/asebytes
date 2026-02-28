# Review Issue Fixes Design

**Goal:** Fix all 7 issues identified in the code review of `feat/async-backends` vs `main`, plus consolidate duplicated deferred view classes.

**Branch:** `feat/async-backends`

---

## Issue 1 (Critical): SyncToAsyncAdapter wraps read-only backends as writable

### Problem

`SyncToAsyncAdapter` inherits `AsyncReadWriteBackend` unconditionally. When a read-only sync backend (e.g. `ASEReadOnlyBackend`) is passed to an async facade, it gets wrapped as writable. The facade's `isinstance(self._backend, AsyncReadWriteBackend)` guard always passes, so write calls hit `AttributeError` instead of a clean `TypeError("Backend is read-only")`.

### Fix

Split into two adapter classes:

```python
class SyncToAsyncReadAdapter(AsyncReadBackend[K, V]):
    """Wraps a sync ReadBackend for use with async facades."""
    def __init__(self, backend: ReadBackend[K, V]):
        self._backend = backend
    # Only read methods: __len__, get, get_many, get_column, keys, iter_rows

class SyncToAsyncReadWriteAdapter(
    SyncToAsyncReadAdapter[K, V],
    AsyncReadWriteBackend[K, V],
):
    """Wraps a sync ReadWriteBackend for use with async facades."""
    def __init__(self, backend: ReadWriteBackend[K, V]):
        super().__init__(backend)
    # Write methods: set, delete, extend, insert, update, delete_many,
    # drop_keys, set_many, reserve, clear, remove
```

Add a factory function:

```python
def sync_to_async(backend: ReadBackend[K, V]) -> AsyncReadBackend[K, V]:
    if isinstance(backend, ReadWriteBackend):
        return SyncToAsyncReadWriteAdapter(backend)
    return SyncToAsyncReadAdapter(backend)
```

Update all 3 async facade `__init__` methods to call `sync_to_async()` instead of `SyncToAsyncAdapter()`.

**Files:**
- `src/asebytes/_async_backends.py` — split class, add factory
- `src/asebytes/_async_blob_io.py` — use `sync_to_async()`
- `src/asebytes/_async_object_io.py` — use `sync_to_async()`
- `src/asebytes/_async_io.py` — use `sync_to_async()`
- `src/asebytes/__init__.py` — update exports if needed

---

## Issue 2 (Important): Missing `update()` on async facades

### Problem

Sync facades (`BlobIO`, `ObjectIO`, `ASEIO`) all have `update()`. Async facades don't — `update()` exists only on deferred view classes.

### Fix

Add `async def update()` to all 3 async facades:

- `AsyncBlobIO.update(index: int, data: dict[bytes, bytes]) -> None`
- `AsyncObjectIO.update(index: int, data: dict[str, Any]) -> None`
- `AsyncASEIO.update(index: int, *, info=None, arrays=None, calc=None) -> None` — mirrors sync ASEIO's namespace-aware signature

Each checks `isinstance(self._backend, AsyncReadWriteBackend)` before delegating.

**Files:**
- `src/asebytes/_async_blob_io.py`
- `src/asebytes/_async_object_io.py`
- `src/asebytes/_async_io.py`

---

## Issue 3 (Important): Missing `clear()`/`remove()` on sync facades

### Problem

Async facades have `clear()` and `remove()`. Sync facades don't.

### Fix

Add to `BlobIO`, `ObjectIO`, and `ASEIO`:

```python
def clear(self) -> None:
    if not isinstance(self._backend, ReadWriteBackend):
        raise TypeError("Backend is read-only")
    self._backend.clear()

def remove(self) -> None:
    if not isinstance(self._backend, ReadWriteBackend):
        raise TypeError("Backend is read-only")
    self._backend.remove()
```

**Files:**
- `src/asebytes/_blob_io.py`
- `src/asebytes/_object_io.py`
- `src/asebytes/io.py`

---

## Issue 4 (Important): BlobIO `__getitem__` doesn't normalize negative indices

### Problem

`ObjectIO` and `ASEIO` normalize `if index < 0: index += len(self)` for int indices. `BlobIO` passes raw int directly to backend.

### Fix

Add negative index normalization to `BlobIO.__getitem__` for the `isinstance(index, int)` branch, matching ObjectIO/ASEIO.

**Files:**
- `src/asebytes/_blob_io.py`

---

## Issue 5 (Important): Duplicated `_DeferredSliceRowView`

### Problem

Nearly identical `_DeferredSliceRowView` classes exist in `_async_object_io.py` and `_async_io.py`. The ASEIO version adds `_DeferredColumnFromSlice` and `_DeferredSubColumnFromSlice` for its `__getitem__` override.

### Fix

Move the shared `_DeferredSliceRowView` to `_async_views.py` as a generic class parameterized by `R`. The ObjectIO version's `__getitem__` override (which handles `_DeferredSliceColumnView` for plain column access) moves into the base class. The ASEIO-specific `__getitem__` override (which creates `_DeferredColumnFromSlice`) stays in `_async_io.py` as a thin subclass `_ASEIODeferredSliceRowView(_DeferredSliceRowView)`.

**Files:**
- `src/asebytes/_async_views.py` — add generic `_DeferredSliceRowView`
- `src/asebytes/_async_object_io.py` — delete local class, import from `_async_views`
- `src/asebytes/_async_io.py` — thin subclass only

---

## Issue 6 (Important): Sync `RowView` missing `drop()` method

### Problem

`AsyncRowView` has `drop(keys)`. Sync `RowView` doesn't. The sync `ViewParent` protocol also lacks `_drop_keys`.

### Fix

Add `_drop_keys` to `ViewParent` protocol in `_views.py`. Add `def drop(self, keys)` to `RowView`:

```python
def drop(self, keys: list) -> None:
    self._parent._drop_keys(keys, self._indices)
```

Verify all facade classes that act as `ViewParent` implement `_drop_keys`. Currently, `BlobIO`, `ObjectIO`, and `ASEIO` need `_drop_keys()` added — or `drop()` on `RowView` can delegate to the backend directly through the parent. Check which pattern the async side uses and mirror it.

**Files:**
- `src/asebytes/_views.py`
- Possibly `_blob_io.py`, `_object_io.py`, `io.py` if `_drop_keys` needs adding to ViewParent implementations

---

## Issue 7 (Minor): ColumnView type annotation wrong for bytes keys

### Problem

`ColumnView.__init__` annotates `keys` as `str | list[str]` but `BlobIO` passes `bytes | list[bytes]`.

### Fix

Update to `str | bytes | list[str] | list[bytes]`.

**Files:**
- `src/asebytes/_views.py`

---

## Issue 8 (Minor): Inconsistent `__iter__` patterns

### Problem

`BlobIO.__iter__` uses `for i in range(len(self)): yield self[i]`. `ObjectIO` and `ASEIO` use `while True / try-except IndexError`.

### Fix

Standardize all 3 to the `range(len(self))` pattern.

**Files:**
- `src/asebytes/_object_io.py`
- `src/asebytes/io.py`

---

## Issue 9 (Minor): Stale comments and scratch file

- Update comments referencing `ReadableBackend` → `ReadBackend`, `WritableBackend` → `ReadWriteBackend`
- Update comments referencing `AsyncBytesIO` → `AsyncBlobIO`
- Delete or move `async-api.py` from repo root

**Files:**
- `src/asebytes/h5md/_backend.py`
- `src/asebytes/zarr/_backend.py`
- `src/asebytes/hf/_backend.py`
- `tests/test_raw_protocols.py`
- `tests/test_blob_column_access.py`
- `tests/test_string_path_constructors.py`
- `async-api.py` (delete)

---

## Updated Facade API (after all fixes)

| Method | BlobIO | ObjectIO | ASEIO | AsyncBlobIO | AsyncObjectIO | AsyncASEIO |
|--------|--------|----------|-------|-------------|---------------|------------|
| `keys(i)` | yes | yes | yes | yes | yes | yes |
| `get(i, keys)` | yes | yes | yes | yes | yes | yes |
| `update(i, d)` | yes | yes | yes* | yes | yes | yes* |
| `drop(*, keys)` | yes | yes | yes | yes | yes | yes |
| `reserve(n)` | yes | yes | yes | yes | yes | yes |
| `clear()` | yes | yes | yes | yes | yes | yes |
| `remove()` | yes | yes | yes | yes | yes | yes |
| neg index | yes | yes | yes | deferred | deferred | deferred |

*ASEIO/AsyncASEIO `update()` uses namespace kwargs: `info=, arrays=, calc=`

---

## Testing Strategy

- Write failing tests first (TDD) for each new method/fix
- Test `SyncToAsyncReadAdapter` wrapping read-only backends: write calls should raise `TypeError`
- Test `update()` on all 3 async facades
- Test `clear()`/`remove()` on all 3 sync facades
- Test `BlobIO[-1]` negative index
- Test `RowView.drop()`
- Test `ColumnView` with bytes keys (type checking)
