# Coding Conventions

**Analysis Date:** 2026-03-06

## Naming Patterns

**Files:**
- Private modules: underscore prefix `_backends.py`, `_blob_io.py`, `_views.py`, `_convert.py`
- Async mirrors: `_async_` prefix matching sync counterpart: `_async_backends.py`, `_async_blob_io.py`, `_async_views.py`
- Public entry points: no underscore: `io.py`, `encode.py`, `decode.py`
- Backend sub-packages: named by storage engine: `lmdb/`, `hf/`, `zarr/`, `h5md/`, `mongodb/`, `redis/`, `columnar/`, `memory/`, `ase/`
- Test files: `test_<feature>.py` (flat in `tests/`, no nesting except `tests/benchmarks/`)

**Classes:**
- PascalCase throughout
- ABCs: `ReadBackend`, `ReadWriteBackend`, `AsyncReadBackend`, `AsyncReadWriteBackend`
- Async ABCs: `Async` prefix: `AsyncReadBackend`, `AsyncBlobReadBackend`
- Facades: short names: `BlobIO`, `ObjectIO`, `ASEIO`, `AsyncASEIO`, `AsyncBlobIO`, `AsyncObjectIO`
- Adapters: descriptive compound names: `BlobToObjectReadAdapter`, `SyncToAsyncReadWriteAdapter`
- Views: `RowView`, `ColumnView`, `ASEColumnView` (sync); `AsyncRowView`, `AsyncColumnView` (async)
- Type aliases: assigned at module level as plain assignments (not classes): `BlobReadBackend = ReadBackend[bytes, bytes]`

**Functions:**
- snake_case for all functions and methods
- Private methods: single underscore prefix: `_read_row`, `_build_result`, `_check_index`, `_discover`
- Helper functions at module level: underscore prefix: `_deserialize_row`, `_serialize_row`, `_is_contiguous`, `_sub_select`
- Public API methods match Python stdlib patterns: `__getitem__`, `__len__`, `extend`, `insert`, `get`, `update`, `keys`, `schema`

**Variables:**
- snake_case for all variables
- Module-level constants: UPPER_SNAKE_CASE: `DEFAULT_GROUP`, `_NEVER_PER_ATOM`, `_KNOWN_SCHEMES`, `_SKIP_KEYS`
- TypeVars: single uppercase letters: `K`, `V`, `R`
- Private instance attributes: single underscore: `self._backend`, `self._store`, `self._cache`, `self._rows`

**Types:**
- Use `from __future__ import annotations` in all source modules (PEP 563 deferred evaluation)
- Use `X | Y` union syntax (not `Union[X, Y]`) throughout
- Use `list[X]`, `dict[X, Y]` lowercase generics (not `List`, `Dict`)
- Return type annotations on all public methods
- Parameter type annotations on all public methods
- Use `@overload` for `__getitem__` polymorphism in facades and views

## Code Style

**Formatting:**
- No formatter config file detected (no ruff, black, or prettier config)
- 4-space indentation
- Double quotes for strings
- Lines typically under 100 characters, some up to ~110

**Linting:**
- No linter config file detected
- Code follows PEP 8 conventions implicitly
- `from __future__ import annotations` used consistently in `src/` modules

**Imports:**
- Standard library first, then third-party, then local
- Local imports use relative paths within the package: `from ._backends import ReadBackend`
- Lazy imports inside functions for optional deps and circular avoidance:
  ```python
  def extend(self, values):
      from ._registry import get_backend_cls  # lazy to avoid circular
  ```

## Import Organization

**Order:**
1. `from __future__ import annotations` (always first line in src modules)
2. Standard library: `abc`, `collections.abc`, `typing`, `json`, `pathlib`, `shutil`, `asyncio`
3. Third-party: `ase`, `numpy`, `msgpack`, `msgpack_numpy`
4. Local relative: `from ._backends import ReadBackend`

**Path Aliases:**
- No path aliases configured (no `tsconfig.json` equivalent)
- All local imports use relative paths: `from ._backends import ...`, `from .._adapters import ...`

**Deferred/Lazy Imports:**
- Registry and adapter imports are done inside methods to avoid circular imports:
  ```python
  # In _blob_io.py
  def __init__(self, backend):
      if isinstance(backend, str):
          from ._registry import get_blob_backend_cls, parse_uri
  ```
- Optional dependency imports wrapped in try/except at module level in `__init__.py`:
  ```python
  try:
      from .lmdb import LMDBBlobBackend
  except ImportError:
      pass
  ```

## Error Handling

**Patterns:**
- `TypeError` for wrong input types: `raise TypeError("Input must be an ase.Atoms object.")`
- `TypeError("Backend is read-only")` when write operations are called on read-only facades (checked via `isinstance(self._backend, ReadWriteBackend)`)
- `IndexError` with the index value for out-of-bounds: `raise IndexError(index)`
- `IndexError` with descriptive message in backends: `raise IndexError(f"Index {index} out of range for {self._n_frames} frames")`
- `KeyError` for missing keys: `raise KeyError(key)` or `raise KeyError(f"No backend registered for '{path}'")`
- `ValueError` for invalid data: `raise ValueError(f"Invalid key {key!r}. Keys must start with ...")`
- `NotImplementedError` for unimplemented operations: `raise NotImplementedError("Columnar backend does not support insert")`
- `ImportError` with install hint for missing optional deps:
  ```python
  raise ImportError(
      f"Backend '{module_path}' requires additional dependencies. "
      f"Install them with: pip install asebytes[{hint}]"
  )
  ```

**Read-only Guard Pattern:**
Every write method in facades (`BlobIO`, `ObjectIO`, `ASEIO`) checks before delegating:
```python
def extend(self, values) -> int:
    if not isinstance(self._backend, ReadWriteBackend):
        raise TypeError("Backend is read-only")
    return self._backend.extend(list(values))
```

**Negative Index Normalization:**
All facades normalize negative indices before checking bounds:
```python
if index < 0:
    index += n
if index < 0 or index >= n:
    raise IndexError(index)
```

## Logging

**Framework:** No logging framework used. No `logging` imports anywhere in the source.

**Patterns:**
- `warnings.warn()` for non-fatal advisory messages (e.g., cache_to with writable source in `src/asebytes/io.py`)
- Errors are raised, not logged

## Comments

**When to Comment:**
- Section dividers using Unicode box-drawing: `# -- Optimised partial update ------------------------------------------`
- Module-level docstrings explain the purpose and design of each module
- Class docstrings use numpy-style with Parameters section
- Inline comments explain non-obvious logic (e.g., `# len("arrays.") == 7`)

**Docstrings:**
- Numpy-style docstrings on public classes and methods:
  ```python
  def get(self, index: int, keys: list[str] | None = None) -> dict[str, Any] | None:
      """Read a single row, optionally filtering to specific keys."""
  ```
- Parameters, Returns, Raises sections where appropriate
- Private methods have brief one-line docstrings or no docstring

## Function Design

**Size:**
- Methods are typically 5-30 lines
- Complex methods (`get_many` in `ColumnarBackend`) can reach 60+ lines but are well-commented
- No hard limit enforced

**Parameters:**
- Keyword-only for optional parameters using `*`: `def __init__(self, backend, *, readonly=None, **kwargs)`
- `**kwargs` forwarded to backend constructors
- Default `None` for optional parameters, resolved internally

**Return Values:**
- `None` for placeholder/missing rows (not sentinel values)
- `dict[K, V] | None` for row reads
- `int` from `extend()` returning new total length
- Views (`RowView`, `ColumnView`) from slice/string indexing

## Module Design

**Exports:**
- Explicit `__all__` in `src/asebytes/__init__.py` listing all public names
- `__getattr__` for lazy error messages on optional dependencies
- Optional backends added to `__all__` only if their deps import successfully

**Barrel Files:**
- `src/asebytes/__init__.py` is the main barrel file re-exporting everything
- Sub-packages (`lmdb/`, `hf/`, etc.) have `__init__.py` that re-export their public classes

**Sync/Async Symmetry:**
- Every sync facade has an async mirror: `BlobIO` / `AsyncBlobIO`, `ObjectIO` / `AsyncObjectIO`, `ASEIO` / `AsyncASEIO`
- Every sync backend ABC has an async mirror: `ReadBackend` / `AsyncReadBackend`
- Every sync view has an async mirror: `RowView` / `AsyncRowView`
- `SyncToAsyncAdapter` bridges sync backends to async facades via `asyncio.to_thread`

**Facade Internal API:**
All three sync facades (`BlobIO`, `ObjectIO`, `ASEIO`) implement a consistent set of `_read_row`, `_read_rows`, `_iter_rows`, `_read_column`, `_write_row`, `_update_row`, `_delete_row`, `_build_result` methods used by views. New facades must implement this protocol (defined in `_views.py` as `ViewParent`).

**Key Namespace Convention (ASEIO-specific):**
- `cell`, `pbc`, `constraints` at top level
- `arrays.<name>` for per-atom arrays (positions, numbers, forces, etc.)
- `info.<name>` for metadata
- `calc.<name>` for calculator results
- Validated by `ASEIO._validate_keys()` on update

---

*Convention analysis: 2026-03-06*
