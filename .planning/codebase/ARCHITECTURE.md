# Architecture

**Analysis Date:** 2026-03-06

## Pattern Overview

**Overall:** Layered Facade + Backend pattern with generic typing

**Key Characteristics:**
- Three-tier type system: blob-level (`bytes, bytes`), object-level (`str, Any`), ASE-level (`str, Atoms`)
- Sync and async mirrors at every layer (facades, backends, views, adapters)
- Registry-based backend resolution from file paths/URIs to backend classes
- Lazy views (RowView, ColumnView) for deferred materialization
- Cross-layer adapters bridge blob <-> object backends transparently

## Layers

**Backend ABCs (storage contracts):**
- Purpose: Define the storage contract all backends must satisfy
- Location: `src/asebytes/_backends.py` (sync), `src/asebytes/_async_backends.py` (async)
- Contains: `ReadBackend[K,V]`, `ReadWriteBackend[K,V]` (sync); `AsyncReadBackend[K,V]`, `AsyncReadWriteBackend[K,V]` (async)
- Type aliases: `BlobReadBackend = ReadBackend[bytes, bytes]`, `ObjectReadBackend = ReadBackend[str, Any]`, etc.
- Key methods (read): `__len__`, `get`, `get_many`, `iter_rows`, `get_column`, `keys`, `schema`
- Key methods (write): `set`, `delete`, `extend`, `insert`, `update`, `set_many`, `update_many`, `set_column`, `reserve`, `clear`, `remove`, `drop_keys`
- Used by: All facade classes and adapters

**Backend Implementations (storage engines):**
- Purpose: Concrete storage engines implementing the backend ABCs
- Locations:
  - `src/asebytes/columnar/_backend.py` -- `ColumnarBackend` (HDF5 + Zarr via offset+flat ragged storage)
  - `src/asebytes/columnar/_store.py` -- `ColumnarStore` protocol, `HDF5Store`, `ZarrStore`
  - `src/asebytes/lmdb/_blob_backend.py` -- `LMDBBlobBackend` (blob-level)
  - `src/asebytes/lmdb/_backend.py` -- `LMDBObjectBackend`, `LMDBObjectReadBackend` (object-level, wraps blob via adapters)
  - `src/asebytes/memory/_backend.py` -- `MemoryObjectBackend` (in-memory, for testing)
  - `src/asebytes/ase/_backend.py` -- `ASEReadOnlyBackend` (read-only, wraps ase.io.read)
  - `src/asebytes/hf/_backend.py` -- `HuggingFaceBackend` (read-only, HuggingFace datasets)
  - `src/asebytes/h5md/_backend.py` -- `H5MDBackend` (legacy HDF5 format)
  - `src/asebytes/mongodb/_backend.py` -- `MongoObjectBackend`; `src/asebytes/mongodb/_async_backend.py` -- `AsyncMongoObjectBackend`
  - `src/asebytes/redis/_backend.py` -- `RedisBlobBackend`; `src/asebytes/redis/_async_backend.py` -- `AsyncRedisBlobBackend`
  - `src/asebytes/zarr/_backend.py` -- `ZarrBackend` (legacy, superseded by ColumnarBackend)
- Depends on: Backend ABCs, external storage libraries (h5py, zarr, lmdb, pymongo, redis)
- Used by: Facades (via registry resolution)

**Adapters (type conversion):**
- Purpose: Bridge between blob-level and object-level backends; bridge sync to async
- Location: `src/asebytes/_adapters.py` (sync blob<->object), `src/asebytes/_async_adapters.py` (async blob<->object), `src/asebytes/_async_backends.py` (sync-to-async)
- Contains:
  - `BlobToObjectReadAdapter`, `BlobToObjectReadWriteAdapter` -- deserialize `dict[bytes,bytes]` to `dict[str,Any]` via msgpack
  - `ObjectToBlobReadAdapter`, `ObjectToBlobReadWriteAdapter` -- serialize `dict[str,Any]` to `dict[bytes,bytes]` via msgpack
  - `SyncToAsyncReadAdapter`, `SyncToAsyncReadWriteAdapter` -- wrap sync backends for async use via `asyncio.to_thread`
  - `sync_to_async()` factory function
- Depends on: Backend ABCs, msgpack, msgpack_numpy
- Used by: Registry fallback resolution, LMDB object backends, async facades

**Registry (backend discovery):**
- Purpose: Map file paths/URIs to backend classes using glob patterns and URI schemes
- Location: `src/asebytes/_registry.py`
- Contains: `_REGISTRY` list of `_RegistryEntry` tuples, `resolve_backend()`, `parse_uri()`, backward-compat wrappers
- Resolution order: URI scheme first, then file-extension glob pattern; filter by layer (blob/object) and async preference; cross-layer adapter fallback
- Depends on: Backend implementations (lazy import via `importlib.import_module`)
- Used by: All facades when constructed with a string path

**Facades (user-facing API):**
- Purpose: Provide `MutableSequence`-style API with lazy views
- Location:
  - Sync: `src/asebytes/_blob_io.py` (`BlobIO`), `src/asebytes/_object_io.py` (`ObjectIO`), `src/asebytes/io.py` (`ASEIO`)
  - Async: `src/asebytes/_async_blob_io.py` (`AsyncBlobIO`), `src/asebytes/_async_object_io.py` (`AsyncObjectIO`), `src/asebytes/_async_io.py` (`AsyncASEIO`)
- Contains: `__getitem__` dispatching (int -> single row, slice/list[int] -> RowView, str/list[str] -> ColumnView), MutableSequence CRUD, `__add__`/`__radd__` for lazy concat
- Depends on: Backend ABCs, Registry, Views
- Used by: End users

**Views (lazy access):**
- Purpose: Lazy row/column views that defer I/O until materialization
- Location: `src/asebytes/_views.py` (sync), `src/asebytes/_async_views.py` (async)
- Contains:
  - `ViewParent` protocol -- defines the internal API facades must implement (`_read_row`, `_read_rows`, `_iter_rows`, `_read_column`, `_build_result`, `_write_row`, etc.)
  - `RowView[R]` -- lazy subset of rows; supports `__iter__`, `chunked()`, `to_list()`, `set()`, `update()`, `delete()`, `drop()`
  - `ColumnView` -- lazy column(s); supports `__iter__`, `to_list()`, `to_dict()`, `set()`
  - `ASEColumnView` -- subclass that wraps results through `dict_to_atoms()`
- Depends on: ViewParent protocol (implemented by facades and ConcatView)
- Used by: Facades via `__getitem__`

**ConcatView (lazy concatenation):**
- Purpose: Read-only virtual concatenation of multiple IO instances
- Location: `src/asebytes/_concat.py`
- Contains: `ConcatView[T]` -- implements ViewParent protocol (read side only), maps global indices to source-local indices
- Created via: `io1 + io2` or `sum([io1, io2, io3], [])`
- Depends on: Views, Facades
- Used by: End users for multi-file access

**Conversion (ASE <-> dict):**
- Purpose: Convert between `ase.Atoms` objects and flat `dict[str, Any]` representation
- Location: `src/asebytes/_convert.py` (logical dict), `src/asebytes/encode.py` (bytes dict), `src/asebytes/decode.py` (bytes dict)
- Key functions:
  - `atoms_to_dict(atoms)` -> `dict[str, Any]` with keys like `cell`, `pbc`, `arrays.positions`, `info.smiles`, `calc.energy`
  - `dict_to_atoms(data, fast=True, copy=True)` -> `ase.Atoms` (fast path bypasses Atoms.__init__ for ~6x speedup)
  - `encode(atoms)` -> `dict[bytes, bytes]` (msgpack serialization)
  - `decode(data)` -> `ase.Atoms` (msgpack deserialization)
- Depends on: ASE, numpy, msgpack
- Used by: ASEIO facade (`_build_result`), adapters

**Schema (introspection):**
- Purpose: Inspect column metadata (dtype, shape)
- Location: `src/asebytes/_schema.py`
- Contains: `SchemaEntry` dataclass, `infer_schema()` function
- Used by: Backends (`.schema()` method), facades

## Data Flow

**Read Path (ASEIO example):**

1. User calls `db[0]` or `db["calc.energy"]` on an `ASEIO` instance
2. Facade dispatches based on index type: int -> single row, str -> `ASEColumnView`
3. For single row: facade calls `self._read_row(index)` which delegates to `self._backend.get(index)`
4. Backend reads from storage (LMDB, HDF5, Zarr, etc.) and returns `dict[str, Any]`
5. Facade calls `self._build_result(row)` which calls `dict_to_atoms(row)` -> `ase.Atoms`
6. If cache_to is set, step 3 checks cache first, writes to cache on miss

**Write Path (ASEIO example):**

1. User calls `db[0] = atoms` or `db.extend([atoms1, atoms2])`
2. Facade converts `ase.Atoms` -> `dict[str, Any]` via `atoms_to_dict()`
3. Facade checks backend is `ReadWriteBackend` (raises `TypeError` if read-only)
4. Delegates to `self._backend.set(index, data)` or `self._backend.extend(data_list)`
5. Backend writes to storage

**View Materialization:**

1. `db[0:10]` returns `RowView(self, [0,1,...,9])` -- no I/O yet
2. `for atoms in db[0:10]:` triggers `RowView.__iter__` -> `parent._iter_rows(indices)` -> `parent._build_result(row)`
3. `db["calc.energy"].to_list()` triggers `ColumnView.__iter__` -> `parent._read_column(key, indices)`
4. `db[0:10]["calc.energy"].set([...])` triggers `ColumnView.set()` -> `parent._set_column()` or `parent._update_row()`

**Backend Resolution:**

1. User passes string path to facade: `ASEIO("data.h5")`
2. Facade calls `get_backend_cls("data.h5")` which calls `resolve_backend("data.h5", layer="object")`
3. Registry iterates `_REGISTRY`, matches `"*.h5"` pattern -> `ColumnarBackend`
4. Facade instantiates: `ColumnarBackend("data.h5")`
5. For URIs like `"mongodb://host/db"`: `parse_uri()` extracts scheme, registry matches scheme entry, facade calls `cls.from_uri(uri)`
6. For cross-layer: if no object backend for `"*.lmdb"` blob-only pattern, registry wraps with `BlobToObjectReadWriteAdapter`

**State Management:**
- Backends own all state (file handles, connections, caches)
- Facades hold a single `_backend` reference
- Views hold a `_parent` reference (facade or ConcatView) and index lists
- No global mutable state except `MemoryObjectBackend._GLOBAL_STORAGE`
- Backend data is NEVER cached in facades -- always read from backend (another client can modify)

## Key Abstractions

**ReadBackend[K,V] / ReadWriteBackend[K,V]:**
- Purpose: Generic storage contract parameterized by key type K and value type V
- Examples: `src/asebytes/_backends.py`
- Pattern: Template Method -- base class provides default implementations (e.g. `get_many` loops over `get`), subclasses override for efficiency

**ColumnarStore Protocol:**
- Purpose: Decouple columnar storage logic from HDF5/Zarr specifics
- Examples: `src/asebytes/columnar/_store.py`
- Pattern: Strategy -- `ColumnarBackend` delegates array I/O to a `ColumnarStore` implementation

**ViewParent Protocol:**
- Purpose: Define the internal contract facades must satisfy for views to work
- Examples: `src/asebytes/_views.py`
- Pattern: Protocol-based duck typing -- both facades and `ConcatView` implement this

**ConcatView:**
- Purpose: Virtual concatenation of multiple IO instances with global-to-local index mapping
- Examples: `src/asebytes/_concat.py`
- Pattern: Composite -- presents multiple sources as one, implements ViewParent protocol

## Entry Points

**Package import:**
- Location: `src/asebytes/__init__.py`
- Responsibilities: Re-export all public APIs; lazy import of optional backends with helpful error messages via `__getattr__`

**Sync Facades (primary user API):**
- `ASEIO(path_or_backend)` at `src/asebytes/io.py` -- ASE Atoms interface
- `ObjectIO(path_or_backend)` at `src/asebytes/_object_io.py` -- dict[str, Any] interface
- `BlobIO(path_or_backend)` at `src/asebytes/_blob_io.py` -- dict[bytes, bytes] interface

**Async Facades:**
- `AsyncASEIO(path_or_backend)` at `src/asebytes/_async_io.py`
- `AsyncObjectIO(path_or_backend)` at `src/asebytes/_async_object_io.py`
- `AsyncBlobIO(path_or_backend)` at `src/asebytes/_async_blob_io.py`

**Low-level utilities:**
- `encode(atoms)` / `decode(data)` at `src/asebytes/encode.py` / `src/asebytes/decode.py` -- direct blob serialization
- `atoms_to_dict(atoms)` / `dict_to_atoms(data)` at `src/asebytes/_convert.py` -- logical dict conversion

## Error Handling

**Strategy:** Fail-fast with descriptive errors

**Patterns:**
- Read-only enforcement: facades check `isinstance(self._backend, ReadWriteBackend)` before every write operation, raise `TypeError("Backend is read-only")`
- Index bounds: backends validate indices and raise `IndexError`
- Missing optional deps: `__init__.py` uses try/except ImportError blocks; `_OPTIONAL_ATTRS` dict + `__getattr__` provides helpful install instructions
- Registry miss: `resolve_backend()` raises `ValueError("No backend found for ...")` or `TypeError("...is read-only, no writable variant")`
- Key validation: ASEIO `.update()` validates keys match namespace convention (`arrays.*`, `info.*`, `calc.*`, `cell`, `pbc`, `constraints`)
- Cache writes: best-effort (`except Exception: pass`) in ASEIO `_read_row` with cache_to

## Cross-Cutting Concerns

**Logging:** No logging framework. No log statements in source code.

**Validation:** Key namespace validation in `ASEIO.update()` via `_validate_keys()`. Index bounds checking in backends and facades. Type checking for write operations.

**Authentication:** Delegated to backend-specific connection parameters (MongoDB URI, Redis URL, HuggingFace tokens). No auth layer in asebytes itself.

**Serialization:** Two parallel paths:
- Blob level: msgpack + msgpack_numpy (`encode`/`decode`, adapters)
- Object level: native Python types stored directly (columnar backends use numpy + JSON for complex types)

**Copy semantics:** `_returns_mutable` flag on backends controls whether `dict_to_atoms` copies numpy arrays. Backends that return fresh data on every read (e.g. LMDB deserializing msgpack) set `_returns_mutable = False` to skip copies. Mutable backends (e.g. MemoryObjectBackend returning list references) set `_returns_mutable = True`.

---

*Architecture analysis: 2026-03-06*
