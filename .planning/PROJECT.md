# asebytes

## What This Is

A Python abstraction layer providing BlobIO, ObjectIO, and ASEIO facades with pandas-like slicing over pluggable storage backends (HDF5, Zarr, LMDB, H5MD, MongoDB, Redis). Clean inheritance hierarchy (BaseColumnarBackend -> Ragged/Padded/H5MD variants), extension-based registry dispatch, and full async mirrors.

## Core Value

Every storage backend must be fast, correct, and tested through a single parametrized test suite.

## Requirements

### Validated

- ✓ BaseColumnarBackend + RaggedColumnarBackend + PaddedColumnarBackend hierarchy — v1.0
- ✓ Extension-based dispatch (.h5/.zarr ragged, .h5p/.zarrp padded, .h5md H5MD) — v1.0
- ✓ Legacy Zarr backend removed — v1.0
- ✓ H5MD 1.1 compliant read/write with znh5md interop — v1.0
- ✓ H5MDBackend as PaddedColumnarBackend subclass — v1.0
- ✓ Unified contract test suite (425+ tests, 9 RW + 3 RO + HF backends) — v1.0
- ✓ Async test suite with @pytest.mark.anyio — v1.0
- ✓ Synthetic benchmark suite with 2x2 parametrization matrix — v1.0
- ✓ HDF5 chunk cache tuning, MongoDB TTL cache, Redis Lua scripts — v1.0
- ✓ Dependencies corrected (lmdb>=1.6.0, h5py>=3.12.0, no upper bounds) — v1.0
- ✓ Dead code removed, _postprocess() consolidated — v1.0
- ✓ CI benchmark pipeline with auto-push to gh-pages — v0.3.1
- ✓ PR benchmark comparison with fail-on-regression gate — v0.3.1
- ✓ GitHub Pages dashboard with Chart.js time-series charts — v0.3.1
- ✓ github-action-benchmark selected as CI benchmark tool — v0.3.1
- ✓ Per-test group isolation for MongoDB/Redis backends — v0.3.1

### Active

(None — planning next milestone)

### Backlog

- [ ] Store schema in backend metadata at write time for O(1) introspection (OPT-01)
- [ ] Improve cache-to secondary backend pattern in ASEIO (OPT-02)
- [ ] Investigate pytest-codspeed for CI-stable benchmarks (OPT-03)

### Out of Scope

- Backwards compatibility with existing data files — pre-release, format changes expected
- New backends or new facade types — maintenance, not feature expansion
- Mobile or web interfaces — Python library
- pyh5md read support — znh5md is the priority for H5MD interop
- Query/filter engine (SQL-like WHERE) — ASE DB handles this
- Distributed/parallel writes — HDF5 MPI is complex

## Context

Shipped v1.0 (architecture overhaul) and v0.3.1 (CI benchmark infrastructure).
12,608 LOC source (Python), 22,740 LOC tests.
Tech stack: h5py, zarr, lmdb, pymongo, redis, ase, molify, pytest-benchmark, github-action-benchmark.
CI: benchmark pipeline on gh-pages, PR regression gate at 150%, public dashboard.

Backend hierarchy:
- `BaseColumnarBackend(ReadWriteBackend[str, Any])` — shared logic (795 lines)
  - `RaggedColumnarBackend` — offset+flat per-atom storage (*.h5, *.zarr)
  - `PaddedColumnarBackend` — NaN/zero-padded rectangular storage (*.h5p, *.zarrp)
    - `H5MDBackend` — H5MD 1.1 group layout translation (*.h5md)

Known performance characteristics:
- LMDB fastest for random access (2-35ms)
- H5MD on par with LMDB for trajectory reads (~2-29ms)
- Zarr ragged has poor random access (549-6254ms) but acceptable trajectory reads
- H5MD 8x faster than znh5md for single-frame reads

## Constraints

- **Python**: >=3.11, tested on 3.11/3.12/3.13
- **Build**: uv only — no pip, no bare python
- **Tooling**: Never use `sed` for edits, never use `pytest.mark.xfail`, never cache backend data
- **H5MD compat**: Must read/write files interoperable with znh5md >=0.4.8
- **CI**: No test data behind authentication walls — all synthetic or bundled
- **No backwards compat**: Data format changes are allowed

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| File-extension-based dispatch for padded vs ragged | Simpler than parameter-based; registry already uses glob patterns | ✓ Good — .h5/.zarr ragged, .h5p/.zarrp padded, .h5md H5MD |
| Drop legacy Zarr backend | Superseded by ColumnarBackend; reduces maintenance surface | ✓ Good — deleted src/asebytes/zarr/ cleanly |
| No backwards compatibility | Pre-release package; freedom to optimize formats | ✓ Good — enabled clean architecture changes |
| Synthetic test data via molify | Reproducible, no auth gates, covers realistic molecular structures | ✓ Good — 2x2 parametrization matrix works well |
| Full H5MD read+write compliance | Interop with znh5md ecosystem is a hard requirement | ✓ Good — bidirectional interop verified |
| H5MDBackend inherits PaddedColumnarBackend | Both use padded storage; avoids reimplementing shared logic | ✓ Good — reduced 1473 to 714 lines |
| Base+hook pattern for _postprocess/_discover | Allows subclass customization without overriding core methods | ✓ Good — clean extension points |
| Padded extensions remap internally (.h5p -> .h5) | Reuse existing HDF5Store/ZarrStore; extension only selects backend class | ✓ Good |
| Constraints serialized as JSON in info column | Avoids architectural changes to columnar storage for H5MD round-trip | ✓ Good — simple, reliable |
| TTL cache for MongoDB metadata (1s window) | Reduces redundant metadata fetches within tight loops | ✓ Good — measurable improvement |
| Facade bounds-check elimination | Delegate IndexError to backend instead of pre-checking len() | ✓ Good — saves round-trip for positive indices |
| github-action-benchmark for CI | Lightweight, gh-pages native, Chart.js auto-generated | ✓ Good — handles store, compare, and dashboard |
| Dual benchmark-action steps (main vs PR) | GitHub Actions can't conditionally set `with:` inputs | ✓ Good — clean separation of concerns |
| UUID-based group isolation in tests | Per-test unique groups prevent data leakage across backends | ✓ Good — fixed MongoDB/Redis flakiness |

---
*Last updated: 2026-03-10 after v0.3.1 milestone*
