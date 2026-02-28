# Universal Backend Adapters Design

## Problem

Currently only LMDB has both blob-level and object-level backends. The object backend (`LMDBObjectBackend`) manually wraps the blob backend with msgpack serialization. Other backends (H5MD, Zarr, ASE files, HuggingFace) only operate at the object level. There is no way to get a blob-level view of a Zarr or H5MD store, and the blob-to-object conversion logic in LMDB is duplicated rather than reusable.

### Current state

| Backend      | Blob (`dict[bytes,bytes]`) | Object (`dict[str,Any]`) |
|--------------|---------------------------|--------------------------|
| LMDB         | `LMDBBlobBackend`         | `LMDBObjectBackend` (wraps blob) |
| H5MD         | -                         | `H5MDBackend` (native)   |
| Zarr         | -                         | `ZarrBackend` (native)   |
| ASE files    | -                         | `ASEReadOnlyBackend` (native) |
| HuggingFace  | -                         | `HuggingFaceBackend` (native) |

### Goal

Any backend should be usable at any level (blob or object) via generic, composable adapters. The registry should auto-resolve missing levels. Tests should cover the full matrix.

## Design

### 1. Adapter Classes

Four sync adapter classes in `src/asebytes/_adapters.py`, following the existing Read/ReadWrite inheritance pattern:

#### Blob → Object (deserialize)

```
BlobToObjectReadAdapter(ReadBackend[str, Any])
    wraps: BlobReadBackend
    get() → deserialize dict[bytes,bytes] via msgpack → dict[str,Any]

BlobToObjectReadWriteAdapter(BlobToObjectReadAdapter, ReadWriteBackend[str, Any])
    wraps: BlobReadWriteBackend
    set()/extend()/insert() → serialize dict[str,Any] via msgpack → dict[bytes,bytes]
```

#### Object → Blob (serialize)

```
ObjectToBlobReadAdapter(ReadBackend[bytes, bytes])
    wraps: ObjectReadBackend
    get() → serialize dict[str,Any] via msgpack → dict[bytes,bytes]

ObjectToBlobReadWriteAdapter(ObjectToBlobReadAdapter, ReadWriteBackend[bytes, bytes])
    wraps: ObjectReadWriteBackend
    set()/extend()/insert() → deserialize dict[bytes,bytes] via msgpack → dict[str,Any]
```

#### Conversion logic

- Serialization: `{k.encode(): msgpack.packb(v, default=m.encode) for k, v in data.items()}`
- Deserialization: `{k.decode(): msgpack.unpackb(v, object_hook=m.decode) for k, v in raw.items()}`
- None placeholders pass through unchanged.

#### ASE level

ASE conversion (dict ↔ Atoms) stays at the facade level (ASEIO). No ASE-level backend adapter — it doesn't fit the `ReadBackend[K,V]` protocol since `get()` would return `Atoms` not `dict[K,V]`.

### 2. Async Adapters

Dedicated async adapter classes in `src/asebytes/_async_adapters.py` that wrap `AsyncReadBackend` / `AsyncReadWriteBackend` directly:

```
AsyncBlobToObjectReadAdapter(AsyncReadBackend[str, Any])
    └── AsyncBlobToObjectReadWriteAdapter(..., AsyncReadWriteBackend[str, Any])

AsyncObjectToBlobReadAdapter(AsyncReadBackend[bytes, bytes])
    └── AsyncObjectToBlobReadWriteAdapter(..., AsyncReadWriteBackend[bytes, bytes])
```

These `await` the inner backend's async methods and apply msgpack conversion synchronously (CPU-bound, fast). This preserves native async benefits for backends like Redis that are natively async.

Composing sync adapters through `SyncToAsyncAdapter` is explicitly NOT the approach — it would lose native async performance.

### 3. Registry Enhancement

`_registry.py` gains fallback resolution:

#### `get_blob_backend_cls(path)`

1. Check `_BLOB_BACKEND_REGISTRY` for a native blob backend.
2. If not found, check `_BACKEND_REGISTRY` for an object backend.
3. Return a factory/class that wraps the object backend with `ObjectToBlobReadWriteAdapter`.

#### `get_backend_cls(path)`

1. Check `_BACKEND_REGISTRY` for a native object backend (existing behavior).
2. If not found, check `_BLOB_BACKEND_REGISTRY` for a blob backend.
3. Return a factory/class that wraps the blob backend with `BlobToObjectReadWriteAdapter`.

The fallback is transparent — callers get a backend class that they construct with the same arguments.

### 4. LMDB Refactor

`LMDBObjectBackend` and `LMDBObjectReadBackend` become thin subclasses of the generic adapters:

```python
class LMDBObjectReadBackend(BlobToObjectReadAdapter):
    def __init__(self, file, prefix=b"", map_size=10737418240, **lmdb_kwargs):
        super().__init__(LMDBBlobBackend(file, prefix, map_size, readonly=True, **lmdb_kwargs))

    @property
    def env(self):
        return self._store.env

class LMDBObjectBackend(BlobToObjectReadWriteAdapter):
    def __init__(self, file, prefix=b"", map_size=10737418240, readonly=False, **lmdb_kwargs):
        super().__init__(LMDBBlobBackend(file, prefix, map_size, readonly, **lmdb_kwargs))

    @property
    def env(self):
        return self._store.env
```

The msgpack serialization logic is removed from LMDB-specific code — it lives in the generic adapter.

The LMDB-specific optimizations (`iter_rows` with single transaction, `get_column` with single transaction, `get_with_txn`) need consideration. Options:
- The adapter's default implementations (loop over `get()`) may be sufficient.
- If LMDB transaction batching is critical for performance, `LMDBObjectReadBackend` can override `iter_rows`/`get_many`/`get_column` to use `env.begin()` directly. These overrides would call the blob backend's transactional methods and deserialize.

### 5. Test Fixtures

Universal parametrized fixtures in `conftest.py`:

```python
# Backend factory functions
def _lmdb_blob(tmp_path):
    return LMDBBlobBackend(str(tmp_path / "test.lmdb"))

def _lmdb_object(tmp_path):
    return BlobToObjectReadWriteAdapter(_lmdb_blob(tmp_path))

def _zarr_object(tmp_path):
    return ZarrBackend(str(tmp_path / "test.zarr"))

def _zarr_blob(tmp_path):
    return ObjectToBlobReadWriteAdapter(_zarr_object(tmp_path))

def _h5md_object(tmp_path):
    return H5MDBackend(str(tmp_path / "test.h5"))

def _h5md_blob(tmp_path):
    return ObjectToBlobReadWriteAdapter(_h5md_object(tmp_path))

# Parametrized blob-level fixture
@pytest.fixture(params=[
    pytest.param(_lmdb_blob, id="lmdb-blob-native"),
    pytest.param(_zarr_blob, id="zarr-blob-via-adapter"),
    pytest.param(_h5md_blob, id="h5md-blob-via-adapter"),
])
def blob_backend(tmp_path, request):
    return request.param(tmp_path)

# Parametrized object-level fixture
@pytest.fixture(params=[
    pytest.param(_lmdb_object, id="lmdb-object-via-adapter"),
    pytest.param(_zarr_object, id="zarr-object-native"),
    pytest.param(_h5md_object, id="h5md-object-native"),
])
def object_backend(tmp_path, request):
    return request.param(tmp_path)
```

Tests use `blob_backend` or `object_backend` and automatically run across the full matrix. Backend-specific tests (e.g. LMDB transaction semantics) remain in their own test files.

## File Changes

| File | Change |
|------|--------|
| `src/asebytes/_adapters.py` | **New** — sync adapter classes |
| `src/asebytes/_async_adapters.py` | **New** — async adapter classes |
| `src/asebytes/_registry.py` | Add fallback resolution |
| `src/asebytes/lmdb/_backend.py` | Refactor to subclass adapters |
| `tests/conftest.py` | Add universal parametrized fixtures |
| `tests/test_adapters.py` | **New** — adapter-specific tests |
| `src/asebytes/__init__.py` | Export adapter classes |

## Non-Goals

- ASE-level backend adapter (stays at facade level)
- Changing the `ReadBackend[K,V]` protocol
- Async-first adapters that don't have sync counterparts
