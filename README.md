# asebytes

Storage-agnostic, lazy-loading data layer with pluggable backends (LMDB, Zarr, HDF5/H5MD, HuggingFace Datasets, ASE file formats). Three IO tiers — raw bytes, structured dicts, and ASE Atoms — each with full sync and async APIs plus pandas-style column views.

```
pip install asebytes[lmdb]      # LMDB backend (recommended)
pip install asebytes[zarr]      # Zarr backend (fast compression)
pip install asebytes[h5md]      # HDF5/H5MD backend
pip install asebytes[hf]        # HuggingFace Datasets backend
pip install asebytes[mongodb]   # MongoDB backend (shared remote storage)
# In-memory backend (MemoryObjectBackend) is built-in — no extras needed
```

## Quick Start

```python
from asebytes import ASEIO

# Sync
db = ASEIO("data.lmdb")
db.extend(atoms_list)
db[0] = new_atoms
atoms = db[0]

# Async
import asyncio
from asebytes import AsyncASEIO

async def main():
    db = AsyncASEIO("data.lmdb")
    await db.extend(atoms_list)
    atoms = await db[0]
    async for atoms in db:
        process(atoms)

asyncio.run(main())
```

String paths auto-detect the backend from the file extension. Pass a backend instance directly for full control.

## Three IO Layers

| Class | Async class | Row type | Use case |
|-------|-------------|----------|----------|
| `ASEIO` | `AsyncASEIO` | `ase.Atoms` | Atomistic simulations |
| `ObjectIO` | `AsyncObjectIO` | `dict[str, Any]` | Structured data without ASE |
| `BlobIO` | `AsyncBlobIO` | `dict[bytes, bytes]` | Raw bytes, zero deserialization |

### ASEIO — Atoms objects

```python
from asebytes import ASEIO, AsyncASEIO

# Sync
db = ASEIO("atoms.lmdb")
db.extend(atoms_list)
db.update(0, calc={"energy": -10.5})
atoms = db[0]                  # ase.Atoms

# Async
db = AsyncASEIO("atoms.lmdb")
await db.extend(atoms_list)
atoms = await db[0]            # ase.Atoms
await db[0].update({"calc.energy": -10.5})
```

### ObjectIO — plain dicts

```python
from asebytes import ObjectIO, AsyncObjectIO

# Sync
db = ObjectIO("records.lmdb")
db.extend([
    {"arrays.numbers": [29], "calc.energy": -3.5},
    {"arrays.numbers": [26], "calc.energy": -8.3},
])
row = db[0]  # {"arrays.numbers": [29], "calc.energy": -3.5}

# Async
db = AsyncObjectIO("records.lmdb")
await db.extend([{"arrays.numbers": [29], "calc.energy": -3.5}])
row = await db[0]
```

### BlobIO — raw bytes

```python
from asebytes import BlobIO, AsyncBlobIO

# Sync
db = BlobIO("blobs.lmdb")
db.extend([{b"key": b"value"}, {b"key": b"other"}])
row = db[0]                    # {b"key": b"value"}

# Async
db = AsyncBlobIO("blobs.lmdb")
await db.extend([{b"key": b"value"}])
row = await db[0]
```

## Lazy Views

Indexing with slices, lists, or strings returns lazy views — nothing is loaded until you iterate or materialize.

### Row views

```python
# Sync
view = db[5:100]               # RowView (lazy)
view = db[[0, 42, 99]]         # RowView from index list
for row in view:
    process(row)

# Async
view = db[5:100]               # AsyncRowView (lazy)
async for row in view:
    process(row)
rows = await view.to_list()    # materialize to list
```

### Column views

```python
# Sync
energies = db["calc.energy"].to_list()
cols = db[["calc.energy", "calc.forces"]].to_dict()
# → {"calc.energy": [...], "calc.forces": [...]}

# Async
energies = await db["calc.energy"].to_list()
cols = await db[["calc.energy", "calc.forces"]].to_dict()
```

### Chaining rows + columns

```python
# Sync
db[0:500]["calc.energy"].to_list()

# Async
await db[0:500]["calc.energy"].to_list()
```

### Materialization

```python
# Sync
view.to_list()                 # load all into memory
view.to_dict()                 # column-oriented dict (ColumnView only)
for batch in view.chunked(1000):  # iterate in chunks
    process(batch)

# Async
await view.to_list()
await view.to_dict()
async for batch in view.chunked(1000):
    process(batch)
```

### Write-back

Views support in-place mutations when backed by a writable backend.

```python
# Sync
db[0:10].set(new_rows)         # overwrite rows
db[0:10].update({"info.tag": "train"})  # partial update (applies to all rows)
db[0:10].delete()              # delete rows (contiguous only)

# Async
await db[0:10].set(new_rows)
await db[0:10].update({"info.tag": "train"})
await db[0:10].delete()
```

## Backends

Backend is auto-detected from the file extension:

| Extension | Backend | Install extra |
|-----------|---------|---------------|
| `*.lmdb` | `LMDBObjectBackend` / `LMDBBlobBackend` | `asebytes[lmdb]` |
| `*.zarr` | `ZarrBackend` | `asebytes[zarr]` |
| `*.h5` / `*.h5md` | `H5MDBackend` | `asebytes[h5md]` |
| `*.xyz` / `*.extxyz` / `*.traj` | `ASEReadOnlyBackend` | *(none)* |

URI schemes for remote/streaming sources:

| Scheme | Source | Example |
|--------|--------|---------|
| `memory://` | In-memory (no persistence) | `ObjectIO("memory://")` |
| `mongodb://` | MongoDB | `ObjectIO("mongodb://host:port/db/collection")` |
| `hf://` | HuggingFace Datasets | `ASEIO("hf://user/dataset", ...)` |
| `colabfit://` | ColabFit datasets | `ASEIO("colabfit://mlearn_Cu_train", ...)` |
| `optimade://` | OPTIMADE datasets | `ASEIO("optimade://LeMaterial/LeMat-Bulk", ...)` |

## Read-Through Cache

For slow or remote sources, `cache_to` creates a persistent local cache. First pass reads from source and fills the cache; subsequent reads are served from cache.

```python
db = ASEIO("colabfit://dataset", split="train", cache_to="cache.lmdb")
for atoms in db:    # epoch 1: reads source, populates cache
    train(atoms)
for atoms in db:    # epoch 2+: reads from local cache
    train(atoms)
```

`cache_to` is available on `ASEIO` only. Accepts a file path (auto-creates backend) or any `ReadWriteBackend` instance. No invalidation — delete the cache file to reset.

## HuggingFace Datasets

Stream or download datasets from the HuggingFace Hub via URI schemes.

```python
# ColabFit (auto-selects column mapping, streams by default)
db = ASEIO("colabfit://mlearn_Cu_train", split="train")

# OPTIMADE (e.g. LeMaterial)
db = ASEIO("optimade://LeMaterial/LeMat-Bulk", split="train", name="compatible_pbe")

# Generic HuggingFace (requires explicit column mapping)
from asebytes import ColumnMapping
mapping = ColumnMapping(
    positions="pos", numbers="nums",
    calc={"energy": "total_energy"},
)
db = ASEIO("hf://user/dataset", mapping=mapping, split="train")

# Downloaded mode for faster access
db = ASEIO("colabfit://dataset", split="train", streaming=False)
```

## Zarr / HDF5 / H5MD

### Zarr

Flat layout with Blosc/LZ4 compression. Compact files and fast reads. Supports variable particle counts via NaN padding.

```python
db = ASEIO("trajectory.zarr")
db.extend(atoms_list)

# Custom compression
from asebytes import ZarrBackend
db = ASEIO(ZarrBackend("data.zarr", compressor="zstd", clevel=9))
```

### HDF5 / H5MD

H5MD-standard files with variable particle counts, per-frame PBC, and bond connectivity.

```python
db = ASEIO("trajectory.h5", author_name="Jane Doe", compression="gzip")
db.extend(atoms_list)

# Multi-group files
from asebytes import H5MDBackend
groups = H5MDBackend.list_groups("multi.h5")
db = ASEIO("multi.h5", particles_group="solvent")
```

## MongoDB

Shared remote storage for multi-client access. Requires a running MongoDB instance (>= 4.4).

```python
# Sync
db = ObjectIO("mongodb://user:pass@host:27017/mydb/mycollection")
db.extend([{"energy": -3.5, "positions": [[0, 0, 0]]}])
row = db[0]

# Async — auto-dispatches to native AsyncMongoObjectBackend
db = AsyncObjectIO("mongodb://user:pass@host:27017/mydb/mycollection")
row = await db[0]
```

Uses a sort-key array for O(1) positional access, with server-side field filtering via MongoDB projections — requesting specific keys (e.g. `db.get(0, keys=["energy"])`) only transfers those fields over the network.

## In-Memory Backend

`MemoryObjectBackend` stores data in a plain Python list — no persistence, no dependencies. Useful for testing, ephemeral storage, and prototyping.

```python
from asebytes import ObjectIO, ASEIO

db = ObjectIO("memory://")
db.extend([{"a": 1}, {"a": 2}])
assert len(db) == 2

# Works with all facades
db = ASEIO("memory://")
db.extend(atoms_list)
```

## Key Convention

All data follows a flat namespace:

| Prefix | Content | Examples |
|--------|---------|----------|
| `arrays.*` | Per-atom arrays | `arrays.positions`, `arrays.numbers`, `arrays.forces` |
| `calc.*` | Calculator results | `calc.energy`, `calc.stress` |
| `info.*` | Frame metadata | `info.smiles`, `info.label` |
| *(top-level)* | `cell`, `pbc`, `constraints` | |

```python
from asebytes import atoms_to_dict, dict_to_atoms

d = atoms_to_dict(atoms)   # Atoms → flat dict
atoms = dict_to_atoms(d)   # flat dict → Atoms
```

## Facade API Reference

All three tiers share the same method names. Async facades use `await` instead of direct calls.

| Method | BlobIO / ObjectIO / ASEIO | AsyncBlobIO / AsyncObjectIO / AsyncASEIO |
|--------|---------------------------|------------------------------------------|
| Read one row | `db[i]` | `await db[i]` |
| Read with key filter | `db.get(i, keys=[...])` | `await db.get(i, keys=[...])` |
| List keys at index | `db.keys(i)` | `await db.keys(i)` |
| Append rows | `n = db.extend([...])` | `n = await db.extend([...])` |
| Insert at position | `db.insert(i, row)` | `await db.insert(i, row)` |
| Overwrite row | `db[i] = row` | `await db[i].set(row)` |
| Partial update | `db.update(i, {...})` | `await db.update(i, {...})` |
| Delete row | `del db[i]` | `await db[i].delete()` |
| Drop columns | `db.drop(keys=[...])` | `await db.drop(keys=[...])` |
| Pre-allocate slots | `db.reserve(n)` | `await db.reserve(n)` |
| Clear all rows | `db.clear()` | `await db.clear()` |
| Remove container | `db.remove()` | `await db.remove()` |
| Length | `len(db)` | `await db.len()` |
| Iterate | `for row in db:` | `async for row in db:` |
| Context manager | `with db:` | `async with db:` |

`ASEIO` / `AsyncASEIO` additionally support keyword-style updates:

```python
db.update(i, info={"tag": "done"}, calc={"energy": -10.5})
```

## Backend Adapters

Adapters convert between blob-level (`dict[bytes, bytes]`) and object-level (`dict[str, Any]`) backends:

| Adapter | Wraps | Exposes |
|---------|-------|---------|
| `BlobToObjectReadAdapter` | `ReadBackend[bytes, bytes]` | `ReadBackend[str, Any]` |
| `BlobToObjectReadWriteAdapter` | `ReadWriteBackend[bytes, bytes]` | `ReadWriteBackend[str, Any]` |
| `ObjectToBlobReadAdapter` | `ReadBackend[str, Any]` | `ReadBackend[bytes, bytes]` |
| `ObjectToBlobReadWriteAdapter` | `ReadWriteBackend[str, Any]` | `ReadWriteBackend[bytes, bytes]` |

Async variants (`AsyncBlobToObjectReadAdapter`, etc.) mirror the same pattern for async backends.

```python
from asebytes import BlobToObjectReadWriteAdapter, ObjectIO
from asebytes import LMDBBlobBackend

# Use a blob backend through the ObjectIO facade
blob_backend = LMDBBlobBackend("data.lmdb")
object_backend = BlobToObjectReadWriteAdapter(blob_backend)
db = ObjectIO(object_backend)
```

The registry uses these adapters automatically — e.g., `BlobIO("data.lmdb")` wraps the object backend as a blob backend via `ObjectToBlobReadWriteAdapter` when no native blob backend is registered.

## Custom Backends

Implement `ReadBackend[K, V]` for read-only access or `ReadWriteBackend[K, V]` for full read-write:

```python
from asebytes import ReadBackend

class MyBackend(ReadBackend[str, object]):
    def __len__(self) -> int: ...
    def get(self, index: int, keys: list[str] | None = None) -> dict[str, object] | None: ...

db = ObjectIO(MyBackend())
```

For async backends, subclass `AsyncReadBackend[K, V]` / `AsyncReadWriteBackend[K, V]`, or wrap an existing sync backend:

```python
from asebytes import SyncToAsyncAdapter, AsyncObjectIO

async_backend = SyncToAsyncAdapter(MyBackend())
db = AsyncObjectIO(async_backend)
```

## Benchmarks

1000 frames each on two datasets — ethanol conformers (small molecules, fixed size) and [LeMat-Traj](https://huggingface.co/datasets/LeMaterial/LeMat-Traj) (periodic structures, variable atom counts). All frames include energy, forces, and stress. Compared against aselmdb, znh5md, extxyz, and SQLite.

```python
# LeMat-Traj benchmark data
lemat = list(ASEIO("optimade://LeMaterial/LeMat-Traj", split="train", name="compatible_pbe")[:1000])
```

> **Note:** HDF5 performance is heavily influenced by compression and chunking settings. Both asebytes H5MD and znh5md use gzip compression by default, which reduces file size at the cost of read/write speed. The Zarr backend uses Blosc/LZ4 compression, which achieves compact file sizes with faster decompression than gzip.

### Write
![Write Performance](docs/benchmark_write.png)

### Sequential Read
![Read Performance](docs/benchmark_read.png)

### Random Access
![Random Access Performance](docs/benchmark_random_access.png)

### Column Access
![Column Access Performance](docs/benchmark_column_access.png)

### File Size
![File Size](docs/benchmark_file_size.png)
