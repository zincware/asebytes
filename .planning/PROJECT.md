# asebytes Maintenance & Performance Overhaul

## What This Is

A maintenance and performance overhaul of the asebytes package — a Python abstraction layer providing BlobIO, ObjectIO, and ASEIO facades with pandas-like slicing over pluggable storage backends (HDF5, Zarr, LMDB, H5MD, MongoDB, Redis). The package has not shipped yet, so breaking changes to data formats and APIs are permitted.

## Core Value

Every storage backend must be fast, correct, and tested through a single parametrized test suite — no duplicated integration tests, no CI dependencies on external data sources.

## Requirements

### Validated

- Existing capability: Three-tier facade system (BlobIO, ObjectIO, ASEIO) with sync + async mirrors
- Existing capability: Lazy views (RowView, ColumnView, ConcatView) for deferred materialization
- Existing capability: Registry-based backend resolution from file paths/URIs
- Existing capability: Adapters bridging blob <-> object and sync -> async layers
- Existing capability: Columnar storage with offset+flat ragged approach (HDF5Store, ZarrStore)
- Existing capability: ASE Atoms <-> dict conversion with fast path bypassing Atoms.__init__

### Active

- [ ] Split columnar backends into dedicated padded and ragged variants with distinct file extensions (e.g. `.h5-padded` / `.h5-ragged`, `.zarr-padded` / `.zarr-ragged`) registered separately in the registry
- [ ] Full H5MD read+write compliance tested against znh5md/pyh5md files, including padding support introduced by znh5md
- [ ] Remove legacy Zarr backend (`src/asebytes/zarr/`) — superseded by ColumnarBackend
- [ ] Declutter codebase: eliminate duplicate logic, dead code, sloppy reimplementations; leverage proper abstraction layers throughout
- [ ] Improve abstraction layers where missing — ensure backends delegate to shared base implementations rather than reimplementing common patterns
- [ ] Performance improvements across all hot paths: reads, writes, slicing, backend init — with measurable benchmark baselines
- [ ] Unified parametrized test suite: each backend tested for blob/object/ase IO support using shared parametrized tests for standard and edge cases
- [ ] Async test coverage: parametrized async tests mirroring sync test suite for all async facades
- [ ] Performance benchmarks using synthetic data (molify.smiles2conformers, molify.pack, SinglePointCalculator, constraints, custom info/arrays entries) — no HuggingFace login-gated data in CI
- [ ] Clean up and improve MongoDB, Redis, ASE read-only, and HuggingFace backends (keep all, improve tests)

### Out of Scope

- Backwards compatibility with existing data files — package is pre-release, format changes are expected
- New backends or new facade types — this is maintenance, not feature expansion
- Mobile or web interfaces — this is a Python library
- Compatibility with anything other than znh5md for H5MD — pyh5md read support is nice-to-have but znh5md is the priority

## Context

- The codebase already has a codebase map at `.planning/codebase/` with ARCHITECTURE.md and STACK.md
- Brownfield project: significant existing code with established patterns
- Two storage strategies exist today (zero-padded and arrow-like ragged+index) but they're bundled in the same ColumnarBackend — need to split into dedicated backends with clear file-extension-based dispatch
- H5MD backend exists but is labeled "legacy" and needs compliance testing against the H5MD 1.1 spec and znh5md's padding extensions
- Test data examples exist in the sibling `../znh5md` repo — use as reference for comprehensive ASE Atoms test fixtures
- Test fixtures should use `molify` for generating realistic molecular structures with calculators, constraints, and custom properties
- Current test framework is described as "messy" — needs restructuring around pytest parametrization

## Constraints

- **Python**: >=3.11, tested on 3.11/3.12/3.13
- **Build**: uv only — no pip, no bare python
- **Tooling**: Never use `sed` for edits, never use `pytest.mark.xfail`, never cache backend data
- **H5MD compat**: Must read/write files interoperable with znh5md >=0.4.8
- **CI**: No test data behind authentication walls (HuggingFace login) — all test data must be synthetic or bundled
- **No backwards compat**: Data format changes are allowed and encouraged if they improve performance

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| File-extension-based dispatch for padded vs ragged | Simpler than parameter-based; registry already uses glob patterns | -- Pending |
| Drop legacy Zarr backend | Superseded by ColumnarBackend; reduces maintenance surface | -- Pending |
| No backwards compatibility | Pre-release package; freedom to optimize formats | -- Pending |
| Synthetic test data via molify | Reproducible, no auth gates, covers realistic molecular structures | -- Pending |
| Full H5MD read+write compliance | Interop with znh5md ecosystem is a hard requirement | -- Pending |

---
*Last updated: 2026-03-06 after initialization*
