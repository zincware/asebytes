# ASE I/O Read-Only Backend

## Summary

Add a read-only backend wrapping `ase.io.read` so that `ASEIO` can open
trajectory files (`.traj`, `.xyz`, `.extxyz`) directly. Lazy per-frame
loading with a configurable LRU cache. No writes.

## Architecture

`ASEReadOnlyBackend(ReadableBackend)` — lives at `src/asebytes/ase/`.

- Reads individual frames via `ase.io.read(file, index=N)`.
- Converts to `dict[str, Any]` via `atoms_to_dict()` and caches.
- `__len__` raises `RuntimeError` until the length is known (discovered
  through `count_frames()`, a complete iteration, or an out-of-bounds read).
- `iter_rows` streams via `ase.io.iread()` for sequential access.
- Registry entries for `*.traj`, `*.xyz`, `*.extxyz` (all read-only, no
  writable variant).

## ASEIO changes

- `readonly: bool` → `readonly: bool | None = None`.
  - `None` (default): auto-detect from registry. If no writable variant
    exists, select the read-only backend without requiring the user to
    pass `readonly=True`.
  - `True`: always select read-only backend.
  - `False`: always select writable backend; raise `TypeError` if none.
- `__getitem__(int)`: when `len()` raises `RuntimeError` (unknown length),
  skip bounds checking and delegate to the backend. The backend converts
  ASE errors to `IndexError`. Negative indices are passed through to
  `ase.io.read` which supports them natively.
- `__getitem__(slice | list[int])`: if length is unknown, propagate the
  `RuntimeError` — user must call `count_frames()` first.

## Caching

```python
class ASEReadOnlyBackend(ReadableBackend):
    def __init__(self, file: str, cache_size: int = 1000):
        self._file = file
        self._cache_size = cache_size
        self._cache: OrderedDict[int, dict[str, Any]] = OrderedDict()
        self._length: int | None = None
```

- `read_row(i)`: cache check → miss → `ase.io.read(file, index=i)` →
  `atoms_to_dict()` → cache → evict oldest if over capacity.
- `iter_rows(indices)`: streams via `ase.io.iread()` for sequential
  access, populates cache as side-effect.
- `count_frames()`: scans file via `ase.io.iread()`, sets `_length`.
  Called explicitly by the user; never called implicitly by `__len__`.
- Cache stores `dict[str, Any]`, not `ase.Atoms`.

## Registry

```python
_BACKEND_REGISTRY = {
    "*.lmdb":   ("asebytes.lmdb", "LMDBBackend", "LMDBReadOnlyBackend"),
    "*.traj":   ("asebytes.ase",  None,           "ASEReadOnlyBackend"),
    "*.xyz":    ("asebytes.ase",  None,           "ASEReadOnlyBackend"),
    "*.extxyz": ("asebytes.ase",  None,           "ASEReadOnlyBackend"),
}
```

`get_backend_cls` changes:

```python
def get_backend_cls(path: str, *, readonly: bool | None = None):
    ...
    if readonly is True:   return read_only_cls
    if readonly is False:
        if writable is None: raise TypeError(...)
        return writable_cls
    # None → auto: prefer writable if available, else readonly
    if writable is not None: return writable_cls
    return read_only_cls
```

## File structure

**New:**
```
src/asebytes/ase/__init__.py      # exports ASEReadOnlyBackend
src/asebytes/ase/_backend.py      # implementation
tests/test_ase_backend.py         # tests
```

**Modified:**
```
src/asebytes/_registry.py         # add entries, update get_backend_cls signature
src/asebytes/io.py                # readonly: bool | None, unknown-length bounds
src/asebytes/__init__.py          # export ASEReadOnlyBackend
```

## Testing

- Fixtures write temporary `.xyz` / `.extxyz` files via `ase.io.write`.
- Cache: hit, miss, eviction at capacity.
- `__len__`: raises before `count_frames()`, works after.
- `count_frames()`: returns correct count, sets `_length`.
- Negative indexing: `read_row(-1)` works without knowing length.
- Streaming: `iter_rows` yields frames sequentially.
- Registry: `ASEIO("file.xyz")` auto-selects read-only backend.
- `ASEIO("file.xyz", readonly=False)` raises `TypeError`.
- Columns: `columns()` returns correct keys from first frame.
- ASEIO readonly=None auto-detection for both LMDB and ASE formats.
