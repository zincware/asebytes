# External Integrations

**Analysis Date:** 2026-03-06

## APIs & External Services

**HuggingFace Hub:**
- Read-only access to HuggingFace datasets
  - SDK/Client: `datasets` library (`datasets.load_dataset`)
  - Auth: HuggingFace token (managed by `datasets` library, typically `~/.huggingface/token`)
  - Backend: `src/asebytes/hf/_backend.py` (`HuggingFaceBackend`)
  - URI schemes: `hf://`, `colabfit://`, `optimade://`
  - Supports streaming and downloaded modes
  - Column mappings: `src/asebytes/hf/_mappings.py` (`COLABFIT`, `OPTIMADE`, `ColumnMapping`)

## Data Storage

**LMDB (embedded key-value store):**
- Local file-based storage, no server required
  - Client: `lmdb` Python bindings
  - Backend: `src/asebytes/lmdb/_blob_backend.py` (`LMDBBlobBackend`), `src/asebytes/lmdb/_backend.py` (`LMDBObjectBackend`, `LMDBObjectReadBackend`)
  - Storage layout: `{path}/{group}/data.mdb` (directory-based LMDB environments)
  - Default map size: 10GB

**HDF5 (columnar file storage):**
- Local file-based hierarchical data format
  - Client: `h5py`
  - Store: `src/asebytes/columnar/_store.py` (`HDF5Store`)
  - Backend: `src/asebytes/columnar/_backend.py` (`ColumnarBackend`)
  - File pattern: `*.h5`, `*.h5md` (H5MD uses legacy `src/asebytes/h5md/_backend.py`)
  - Default compression: gzip
  - Default chunk cache: 64MB (`rdcc_nbytes`)

**Zarr (columnar array storage):**
- Local directory-based array storage (Zarr v3)
  - Client: `zarr` (v3 API)
  - Store: `src/asebytes/columnar/_store.py` (`ZarrStore`)
  - Backend: `src/asebytes/columnar/_backend.py` (`ColumnarBackend`)
  - File pattern: `*.zarr`
  - Default compressor: LZ4 via Blosc codec
  - Also has legacy backend: `src/asebytes/zarr/_backend.py` (`ZarrBackend`)

**MongoDB:**
- Document database for object-level storage
  - Connection: URI string (default `mongodb://localhost:27017`)
  - Client: `pymongo.MongoClient` (sync), `motor` or similar for async
  - Sync backend: `src/asebytes/mongodb/_backend.py` (`MongoObjectBackend`)
  - Async backend: `src/asebytes/mongodb/_async_backend.py` (`AsyncMongoObjectBackend`)
  - Default database: `asebytes`
  - Groups map to MongoDB collections
  - Values serialized via BSON + msgpack for numpy arrays

**Redis:**
- In-memory key-value store for blob-level storage
  - Connection: URI string (default `redis://localhost:6379`)
  - Client: `redis.Redis` (sync), `redis.asyncio.Redis` (async)
  - Sync backend: `src/asebytes/redis/_backend.py` (`RedisBlobBackend`)
  - Async backend: `src/asebytes/redis/_async_backend.py` (`AsyncRedisBlobBackend`)
  - Lua scripts for atomic operations: `src/asebytes/redis/_lua.py`
  - Storage layout: `{group}:sort_keys` (LIST), `{group}:row:{sk}` (HASH per row)

**In-Memory:**
- Pure Python dict-based storage (no external dependency)
  - Backend: `src/asebytes/memory/_backend.py` (`MemoryObjectBackend`)
  - URI scheme: `memory://`

**ASE File Formats (read-only):**
- Read-only access to ASE-supported file formats
  - Backend: `src/asebytes/ase/_backend.py` (`ASEReadOnlyBackend`)
  - File patterns: `*.traj`, `*.xyz`, `*.extxyz`
  - Uses ASE's built-in `ase.io.read`

**File Storage:**
- Local filesystem only (no cloud object storage)
- LMDB, HDF5, Zarr all use local file paths

**Caching:**
- No external caching service
- In-process caches: HuggingFace backend has LRU row cache, LMDB caches block/schema metadata, HDF5/Zarr cache array references

## Authentication & Identity

**Auth Provider:**
- None (library, not a service)
- HuggingFace authentication handled by the `datasets` library's own token management
- MongoDB/Redis authentication via connection URI credentials

## Monitoring & Observability

**Error Tracking:**
- None

**Logs:**
- No structured logging framework; uses Python exceptions for error signaling

## CI/CD & Deployment

**Hosting:**
- PyPI (library package, `dist/` directory present)
- GitHub: `https://github.com/zincware/asebytes`

**CI Pipeline:**
- GitHub Actions (`.github/workflows/tests.yml`)
- Matrix: Python 3.11, 3.12, 3.13 on ubuntu-latest
- Services: Redis 7 (port 6379), MongoDB 7 (port 27017)
- Steps: `uv sync --all-extras --dev` -> `uv run pytest` -> benchmarks -> artifact upload
- Benchmark results uploaded as artifacts (JSON + PNG)

## Environment Configuration

**Required env vars:**
- None required (all configuration via constructor arguments)

**Secrets location:**
- CI: MongoDB credentials hardcoded in workflow (`root`/`example` for test instance)
- No production secrets management (library package)

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## Backend Registry

The backend registry (`src/asebytes/_registry.py`) maps file patterns and URI schemes to backend classes with lazy imports. This is the central integration point:

| Pattern/Scheme | Layer | Backend Class | Module |
|---|---|---|---|
| `*.lmdb` | object | `LMDBObjectBackend` / `LMDBObjectReadBackend` | `asebytes.lmdb` |
| `*.lmdb` | blob | `LMDBBlobBackend` | `asebytes.lmdb` |
| `*.h5` | object | `ColumnarBackend` | `asebytes.columnar` |
| `*.h5md` | object | `H5MDBackend` | `asebytes.h5md` |
| `*.zarr` | object | `ColumnarBackend` | `asebytes.columnar` |
| `*.traj`, `*.xyz`, `*.extxyz` | object | `ASEReadOnlyBackend` | `asebytes.ase` |
| `hf://` | object | `HuggingFaceBackend` | `asebytes.hf._backend` |
| `colabfit://` | object | `HuggingFaceBackend` | `asebytes.hf._backend` |
| `optimade://` | object | `HuggingFaceBackend` | `asebytes.hf._backend` |
| `mongodb://` | object | `MongoObjectBackend` (sync) / `AsyncMongoObjectBackend` (async) | `asebytes.mongodb` |
| `memory://` | object | `MemoryObjectBackend` | `asebytes.memory._backend` |
| `redis://` | blob | `RedisBlobBackend` (sync) / `AsyncRedisBlobBackend` (async) | `asebytes.redis` |

Cross-layer adapter fallback automatically wraps blob backends with `BlobToObject*Adapter` (and vice versa) when no direct match exists for the requested layer.

---

*Integration audit: 2026-03-06*
