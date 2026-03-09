# Feature Landscape

**Domain:** Scientific data IO library for ASE Atoms with pluggable storage backends
**Researched:** 2026-03-06

## Table Stakes

Features users expect. Missing = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| MutableSequence API (`__getitem__`, `__setitem__`, `extend`, `__len__`) | znh5md and ASE DB both provide this; users expect list-like access to trajectory frames | Low | Already implemented via facades |
| Slicing with lazy views (`db[0:10]`, `db["energy"]`) | znh5md supports slicing; MDAnalysis provides lazy trajectory access; numpy users expect this | Med | Already implemented (RowView, ColumnView) |
| H5MD read/write interoperability with znh5md | znh5md is the de facto H5MD tool in the ASE ecosystem; files must round-trip | High | Partially implemented but untested against znh5md files; critical gap |
| Variable particle count support (ragged trajectories) | Molecular systems change size (reactions, grand canonical); znh5md pads with np.nan; this is expected | Med | Offset+flat approach exists in ColumnarBackend; needs split into padded vs ragged variants |
| Padded storage for uniform-size trajectories | H5MD spec standard; znh5md default; simpler/faster when all frames have same atom count | Med | Bundled in ColumnarBackend; needs dedicated variant |
| Context manager support (`with ASEIO(...) as db:`) | h5py, zarr, and every file-based library supports this; prevents file handle leaks | Low | Already implemented on facades and backends |
| Compression options (gzip for HDF5, blosc/lz4 for Zarr) | h5py and zarr both expose compression; scientific datasets are large; users expect control | Low | Already implemented via HDF5Store/ZarrStore params |
| Column-oriented reads (`db["calc.energy"]`) | Extracting a single property across all frames is the most common analysis pattern; znh5md and ASE DB support this | Med | Already implemented via ColumnView and `get_column` |
| Schema/metadata introspection | Users need to know what keys exist, their dtypes and shapes without loading data; ASE DB provides `.metadata`, h5py exposes attrs | Low | `schema()` and `keys()` exist but schema is inferred per-row rather than stored; should be O(1) from backend metadata |
| Bulk write (`extend`) with good performance | Writing thousands of frames is the primary write pattern; znh5md benchmarks emphasize write speed | Med | Already implemented; performance varies by backend |
| Async support | Modern Python data pipelines use asyncio; MongoDB/Redis are inherently async; users expect async for network backends | High | Already implemented with full sync/async mirror |
| Multiple backend support (HDF5, Zarr, LMDB, MongoDB, Redis) | Different use cases need different backends; h5py for HPC, zarr for cloud, MongoDB for web services | High | Already implemented via registry pattern |
| Reproducible benchmark suite | Every serious IO library (h5py, zarr, MDAnalysis) publishes benchmarks; users need to compare options | Med | Ad-hoc benchmarks exist but no structured, repeatable suite with synthetic data |
| Parametrized test suite with full coverage | Open-source data libraries must prove correctness across backends and edge cases | High | Tests exist but are described as "messy"; need restructuring |
| `close()` method and resource cleanup | File handles, connections must be cleanly released; every IO library provides this | Low | Already implemented on all backends |
| Read-only mode | Opening files for read without risk of modification is essential for shared data; h5py and zarr both support `mode="r"` | Low | Already implemented via `ReadBackend` vs `ReadWriteBackend` distinction |

## Differentiators

Features that set product apart. Not expected, but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Unified facade across all backends | Unlike znh5md (HDF5-only) or ASE DB (SQLite/JSON-only), asebytes provides one API for HDF5/Zarr/LMDB/MongoDB/Redis; users never change application code when switching storage | Low | Already the core value prop; needs polish and testing |
| Lazy concatenation (`db1 + db2`) | Multi-file access without copying; MDAnalysis supports this for trajectories but znh5md does not; valuable for large dataset workflows | Low | Already implemented via ConcatView |
| Fast `dict_to_atoms` bypass of `Atoms.__init__` | ~6x speedup for deserialization; no other library does this; matters when reading millions of frames | Low | Already implemented in `_convert.py` |
| Automatic cross-layer adapter resolution | BlobIO backend used from ObjectIO transparently via msgpack adapter; no manual wiring needed | Low | Already implemented in registry |
| Dedicated padded vs ragged backends with extension-based dispatch | Users pick strategy by file extension (`.h5-padded` / `.h5-ragged`); no config flags, no wrong defaults; cleaner than znh5md's implicit padding | Med | Planned; needs implementation |
| Column-level partial updates (`db[0:10]["calc.energy"].set([...])`) | Update a single property across frames without rewriting entire rows; unique to asebytes; saves enormous time for post-hoc calculator results | Med | Already implemented via ColumnView.set() |
| Per-backend performance optimizations (MongoDB TTL cache, Redis Lua bounds) | Measured 1.9-3.5x improvements from backend-specific optimizations; makes network backends viable for interactive use | Med | Benchmarked and validated; implementation pending |
| Chunked iteration (`db[0:10000].chunked(batch_size=100)`) | Process large datasets in memory-safe batches; not available in znh5md; useful for ML training pipelines | Low | Already implemented in RowView |
| Sync-to-async adapter | Any sync backend automatically works in async contexts via `asyncio.to_thread`; no async reimplementation needed per backend | Low | Already implemented |
| Copy semantics control (`_returns_mutable`) | Backends that deserialize (LMDB/msgpack) skip unnecessary numpy copies; mutable backends (memory) copy to prevent aliasing | Low | Already implemented; invisible to users but measurable |
| Type-safe generic backends (`ReadBackend[K,V]`) | Backend contract enforced at type-check time; prevents subtle bugs when mixing blob/object layers | Low | Already implemented |
| Cache-to secondary backend | Read from primary, write-through to cache backend for hot-path acceleration | Med | Partially implemented in ASEIO (`cache_to` param) |

## Anti-Features

Features to explicitly NOT build.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Query/filter engine (SQL-like WHERE clauses) | ASE DB already handles this well; building a query engine is a massive scope creep; asebytes is IO, not a database | Use ASE DB for queries; asebytes for fast sequential/columnar access |
| Unit conversion system | MDAnalysis has comprehensive unit handling; duplicating it adds complexity for marginal value; ASE Atoms already carry implicit units | Let users handle units at the application layer; ASE conventions are sufficient |
| Schema migration / versioning | Pre-release package with no backwards compat promise; schema migration is premature; adds complexity to every write path | Break formats freely until v1.0; document format versions in file metadata |
| GUI or web interface | This is a Python library for computational scientists; GUIs are a different product | Provide clean Python API; let users build their own dashboards |
| Distributed/parallel writes | HDF5 parallel I/O (MPI) is notoriously complex; Zarr has better stories here but it's out of scope for a maintenance overhaul | Single-writer access; use Zarr for embarrassingly parallel workloads |
| Custom serialization formats | msgpack + numpy is proven and fast; inventing a new wire format adds risk with no clear benefit | Stick with msgpack/msgpack_numpy for blob layer; native types for columnar |
| Automatic schema inference on every read | Inferring schema per-row is wasteful; schema should be stored as backend metadata and read once | Store schema in backend attrs/metadata at write time; read from metadata on access |
| Global mutable state beyond MemoryObjectBackend | Global state makes testing fragile and concurrent access dangerous | Keep backends stateless beyond their own file handles/connections |
| Caching of backend data in facades | Another client can modify data at any time; caching leads to stale reads and subtle bugs | Always read from backend; use `cache_to` for explicit cache-aside pattern |
| Support for every ASE IO format | ASE already reads/writes 70+ formats; wrapping them all is maintenance burden with no value-add | Support ASEReadOnlyBackend for `ase.io.read()` as escape hatch; focus on high-performance formats |

## Feature Dependencies

```
Padded backend variant --> H5MD compliance testing (padded is what znh5md writes)
Ragged backend variant --> Offset+flat storage (already exists in ColumnarBackend)
H5MD compliance --> Padded backend variant (must read/write znh5md files)
H5MD compliance --> Variable PBC support (znh5md's pbc_group=True extension)
Parametrized test suite --> All backend variants must exist to be tested
Benchmark suite --> Parametrized test suite (benchmarks reuse test fixtures)
MongoDB TTL cache --> MongoDB backend cleanup
Redis Lua bounds --> Redis backend cleanup
Extension-based dispatch --> Registry update (new glob patterns)
Extension-based dispatch --> Padded + Ragged variants exist
Schema stored in metadata --> Backend write path updates
```

## MVP Recommendation

The project is a maintenance overhaul, not a greenfield build. Prioritize in this order:

1. **Split padded vs ragged columnar backends** - This unblocks H5MD compliance and extension-based dispatch. Without this, the most important features cannot be tested.

2. **H5MD compliance with znh5md interop** - This is the hardest requirement and the one most likely to surface design issues. Test early.

3. **Parametrized test suite** - Every subsequent change needs proof of correctness. Build the test harness before optimizing.

4. **Benchmark suite with synthetic data** - Establish baselines before optimizing. Use molify for realistic structures. Measure padded vs ragged, sequential vs random, single vs bulk.

5. **Backend-specific optimizations** (MongoDB TTL, Redis Lua) - These are validated wins (1.9-3.5x) but lower priority than correctness.

6. **Codebase declutter** (remove legacy Zarr backend, dead code) - Do this last since removing code is low risk and doesn't block other work.

Defer:
- **Cache-to improvements**: Nice to have but not part of core maintenance scope
- **Schema-in-metadata**: Useful optimization but can wait for post-overhaul polish
- **New backend types**: Explicitly out of scope per PROJECT.md

## Sources

- [ZnH5MD GitHub](https://github.com/zincware/ZnH5MD) - MEDIUM confidence (WebSearch + WebFetch verified)
- [H5MD 1.1 specification](https://www.nongnu.org/h5md/h5md.html) - HIGH confidence (official spec)
- [h5py documentation](https://docs.h5py.org/) - HIGH confidence (official docs)
- [Zarr documentation](https://zarr.readthedocs.io/) - HIGH confidence (official docs)
- [MDAnalysis](https://www.mdanalysis.org/) - MEDIUM confidence (WebSearch)
- [ASE database docs](https://wiki.fysik.dtu.dk/ase/ase/db/db.html) - HIGH confidence (official docs)
- [pytest-benchmark](https://pytest-benchmark.readthedocs.io/) - HIGH confidence (official docs)
- Internal benchmark results at `benchmarks/proposals/RESULTS.md` - HIGH confidence (first-party data)
- Existing codebase analysis - HIGH confidence (direct code inspection)
