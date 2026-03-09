# Codebase Structure

**Analysis Date:** 2026-03-06

## Directory Layout

```
asebytes/
├── src/asebytes/              # Main package source
│   ├── __init__.py            # Public API re-exports, optional dep handling
│   ├── _backends.py           # Sync backend ABCs (ReadBackend, ReadWriteBackend)
│   ├── _async_backends.py     # Async backend ABCs + SyncToAsync adapters
│   ├── _adapters.py           # Sync blob<->object adapters
│   ├── _async_adapters.py     # Async blob<->object adapters
│   ├── _blob_io.py            # BlobIO facade (MutableSequence[dict[bytes,bytes]])
│   ├── _object_io.py          # ObjectIO facade (MutableSequence[dict[str,Any]])
│   ├── io.py                  # ASEIO facade (MutableSequence[ase.Atoms])
│   ├── _async_blob_io.py      # AsyncBlobIO facade
│   ├── _async_object_io.py    # AsyncObjectIO facade
│   ├── _async_io.py           # AsyncASEIO facade
│   ├── _views.py              # Sync RowView, ColumnView, ASEColumnView
│   ├── _async_views.py        # Async view counterparts
│   ├── _concat.py             # ConcatView (lazy read-only concatenation)
│   ├── _convert.py            # atoms_to_dict / dict_to_atoms conversion
│   ├── _schema.py             # SchemaEntry dataclass, infer_schema()
│   ├── _columnar.py           # Columnar helpers (concat_varying, fill values, etc.)
│   ├── encode.py              # encode(atoms) -> dict[bytes,bytes]
│   ├── decode.py              # decode(data) -> ase.Atoms
│   ├── metadata.py            # get_metadata() for blob introspection
│   ├── ase/                   # ASE file-based read-only backend
│   │   ├── __init__.py        # Re-exports ASEReadOnlyBackend
│   │   └── _backend.py        # ASEReadOnlyBackend (wraps ase.io.read)
│   ├── columnar/              # Unified columnar backend (HDF5 + Zarr)
│   │   ├── __init__.py        # Re-exports ColumnarBackend
│   │   ├── _backend.py        # ColumnarBackend (offset+flat ragged storage)
│   │   └── _store.py          # ColumnarStore protocol, HDF5Store, ZarrStore
│   ├── h5md/                  # Legacy H5MD backend
│   │   ├── __init__.py
│   │   ├── _backend.py        # H5MDBackend
│   │   └── _mapping.py        # H5MD-specific key mappings
│   ├── hf/                    # HuggingFace datasets backend
│   │   ├── __init__.py
│   │   ├── _backend.py        # HuggingFaceBackend (read-only)
│   │   └── _mappings.py       # ColumnMapping, COLABFIT, OPTIMADE presets
│   ├── lmdb/                  # LMDB backend (blob + object levels)
│   │   ├── __init__.py
│   │   ├── _backend.py        # LMDBObjectBackend, LMDBObjectReadBackend
│   │   └── _blob_backend.py   # LMDBBlobBackend
│   ├── memory/                # In-memory backend (testing/ephemeral)
│   │   ├── __init__.py
│   │   └── _backend.py        # MemoryObjectBackend
│   ├── mongodb/               # MongoDB backend (sync + async)
│   │   ├── __init__.py
│   │   ├── _backend.py        # MongoObjectBackend
│   │   └── _async_backend.py  # AsyncMongoObjectBackend
│   ├── redis/                 # Redis backend (sync + async, blob-level)
│   │   ├── __init__.py
│   │   ├── _backend.py        # RedisBlobBackend
│   │   ├── _async_backend.py  # AsyncRedisBlobBackend
│   │   └── _lua.py            # Lua scripts for atomic Redis operations
│   └── zarr/                  # Legacy Zarr backend (superseded by columnar/)
│       ├── __init__.py
│       └── _backend.py        # ZarrBackend
├── tests/                     # All test files (flat, no subdirs except benchmarks/)
│   ├── conftest.py            # Shared fixtures
│   ├── test_*.py              # ~90 test files
│   └── benchmarks/            # pytest-benchmark tests
│       ├── conftest.py
│       └── test_bench_*.py
├── benchmarks/                # Standalone benchmark scripts
│   ├── bench_columnar.py
│   └── proposals/             # Experimental benchmark proposals
├── docs/                      # Documentation and benchmark visualizations
│   ├── plans/                 # Design plans
│   ├── specs/                 # Specifications
│   └── visualize_benchmarks.py
├── scripts/                   # Utility scripts
│   └── download_benchmark_data.py
├── pyproject.toml             # Project config (uv build, dependencies, pytest)
├── uv.lock                   # Lockfile
├── Design.md                 # Design document
├── TODO.md                   # Task tracking
└── .planning/                # GSD planning documents
    └── codebase/             # Architecture analysis output
```

## Directory Purposes

**`src/asebytes/` (core package):**
- Purpose: All library source code
- Contains: Core ABCs, facades, views, adapters, registry, conversion utilities
- Key files: `_backends.py` (contracts), `_registry.py` (discovery), `io.py` (main facade)
- Convention: Underscore-prefixed files (`_backends.py`) are internal; non-prefixed (`io.py`, `encode.py`) are part of public API

**`src/asebytes/{backend_name}/` (backend packages):**
- Purpose: Each backend lives in its own subpackage
- Contains: `__init__.py` (re-exports), `_backend.py` (implementation), optional helper modules
- Pattern: `_backend.py` for sync, `_async_backend.py` for async backends
- Key constraint: Each is an optional dependency -- lazy-imported in `__init__.py` with try/except

**`tests/` (test suite):**
- Purpose: pytest test files for all functionality
- Contains: ~90 `test_*.py` files, flat layout (no per-backend subdirs)
- Key files: `conftest.py` (shared fixtures), `benchmarks/` subdirectory for perf tests
- Naming: `test_{feature}.py` -- descriptive names like `test_columnar_backend.py`, `test_concat_view.py`

**`benchmarks/` (standalone benchmarks):**
- Purpose: Performance benchmarking scripts outside pytest
- Contains: `bench_columnar.py`, `proposals/` for experimental benchmarks

**`docs/` (documentation):**
- Purpose: Design docs, specs, benchmark visualizations
- Contains: Benchmark PNG charts, `plans/`, `specs/` subdirs

## Key File Locations

**Entry Points:**
- `src/asebytes/__init__.py`: Package entry -- all public symbols re-exported here
- `src/asebytes/io.py`: `ASEIO` class -- the primary user-facing facade

**Configuration:**
- `pyproject.toml`: Build config (uv_build), dependencies, optional extras, pytest config
- `.python-version`: Python version pin (3.11)

**Core Logic:**
- `src/asebytes/_backends.py`: Sync backend ABC hierarchy
- `src/asebytes/_async_backends.py`: Async backend ABCs + sync-to-async adapters
- `src/asebytes/_registry.py`: Backend discovery and resolution
- `src/asebytes/_views.py`: Lazy view classes (RowView, ColumnView)
- `src/asebytes/_convert.py`: ASE Atoms <-> flat dict conversion
- `src/asebytes/columnar/_backend.py`: Unified columnar backend (most complex backend)
- `src/asebytes/columnar/_store.py`: Storage protocol + HDF5/Zarr implementations

**Testing:**
- `tests/conftest.py`: Shared test fixtures
- `tests/test_columnar_backend.py`: ColumnarBackend tests
- `tests/test_aseio.py`: ASEIO facade tests
- `tests/test_views.py`: View class tests
- `tests/test_concat_view.py`: ConcatView tests

## Naming Conventions

**Files:**
- `_name.py`: Internal module (not directly imported by users)
- `name.py`: Public module (e.g., `io.py`, `encode.py`, `decode.py`)
- `_backend.py`: Backend implementation within a backend subpackage
- `_async_*.py`: Async counterpart of a sync module
- `test_*.py`: Test file

**Directories:**
- `src/asebytes/{backend}/`: Backend subpackage named after the storage technology
- `src/asebytes/columnar/`: Unified columnar backend (replaces separate h5md/zarr)

**Classes:**
- `{Name}Backend`: Backend implementations (e.g., `ColumnarBackend`, `LMDBBlobBackend`)
- `{Name}IO`: Facade classes (e.g., `ASEIO`, `BlobIO`, `ObjectIO`)
- `Async{Name}`: Async variants (e.g., `AsyncASEIO`, `AsyncBlobIO`)
- `{Name}View`: View classes (e.g., `RowView`, `ColumnView`, `ASEColumnView`)
- `{A}To{B}{RW}Adapter`: Adapters (e.g., `BlobToObjectReadWriteAdapter`)

**Methods:**
- `_read_row`, `_read_rows`, `_iter_rows`, `_read_column`: Internal read methods on facades (ViewParent protocol)
- `_write_row`, `_write_many`, `_update_row`, `_update_many`: Internal write methods
- `_build_result`: Transform raw dict to output type (identity for ObjectIO, dict_to_atoms for ASEIO)
- `get`, `set`, `extend`, `delete`, `insert`: Backend CRUD methods
- `get_many`, `iter_rows`, `get_column`: Batch/streaming read methods
- `to_list()`, `to_dict()`, `chunked()`: View materialization methods

## Where to Add New Code

**New Storage Backend:**
1. Create `src/asebytes/{name}/` directory
2. Add `__init__.py` re-exporting backend class
3. Add `_backend.py` implementing `ReadWriteBackend[str, Any]` or `ReadBackend[str, Any]`
4. For async: add `_async_backend.py` implementing `AsyncReadWriteBackend[str, Any]`
5. Register in `src/asebytes/_registry.py` `_REGISTRY` list
6. Add optional dependency in `pyproject.toml` `[project.optional-dependencies]`
7. Add lazy import in `src/asebytes/__init__.py` with try/except block
8. Add `_OPTIONAL_ATTRS` entry for helpful error messages
9. Tests: add `tests/test_{name}_backend.py`

**New Facade Method:**
1. Add to sync facade in `src/asebytes/io.py` (or `_blob_io.py`, `_object_io.py`)
2. Mirror in async facade in `src/asebytes/_async_io.py` (or `_async_blob_io.py`, `_async_object_io.py`)
3. If view-related, update `ViewParent` protocol in `src/asebytes/_views.py` and `_async_views.py`
4. Update `ConcatView` in `src/asebytes/_concat.py` if it should participate

**New View Capability:**
1. Add to `RowView` or `ColumnView` in `src/asebytes/_views.py`
2. Mirror in `AsyncRowView` / `AsyncColumnView` in `src/asebytes/_async_views.py`
3. If it needs backend support, add to `ViewParent` protocol and implement in all facades + ConcatView

**New Backend ABC Method:**
1. Add abstract/default method to `ReadBackend` or `ReadWriteBackend` in `src/asebytes/_backends.py`
2. Mirror in `AsyncReadBackend` or `AsyncReadWriteBackend` in `src/asebytes/_async_backends.py`
3. Update `SyncToAsyncReadAdapter` / `SyncToAsyncReadWriteAdapter` in `_async_backends.py`
4. Update all adapter classes in `_adapters.py` and `_async_adapters.py`
5. Override in backends that can do better than the default

**New Test:**
- Place in `tests/test_{descriptive_name}.py` (flat, no subdirs)
- Use fixtures from `tests/conftest.py`
- Benchmark tests go in `tests/benchmarks/test_bench_{name}.py`

## Special Directories

**`.planning/`:**
- Purpose: GSD planning and codebase analysis documents
- Generated: Yes (by codebase mapping)
- Committed: No (in `.gitignore` typically)

**`.benchmarks/`:**
- Purpose: pytest-benchmark result storage
- Generated: Yes (by benchmark runs)
- Committed: No

**`tmp/`:**
- Purpose: Temporary test/benchmark output files
- Generated: Yes
- Committed: No

**`dist/`:**
- Purpose: Built package distributions
- Generated: Yes (by `uv build`)
- Committed: No

**`.venv/`:**
- Purpose: Virtual environment
- Generated: Yes (by `uv sync`)
- Committed: No

---

*Structure analysis: 2026-03-06*
