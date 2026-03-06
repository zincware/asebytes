# Roadmap: asebytes Maintenance & Performance Overhaul

## Overview

This roadmap delivers a clean, fast, fully-tested asebytes package through four phases: first refactor the backend architecture (split padded/ragged, extract shared base class, remove legacy code), then achieve H5MD compliance with znh5md interop and fix dependency versions, then build a unified contract test suite that proves correctness across all backends, and finally establish benchmark baselines and optimize performance. The ordering is driven by hard dependencies: architecture must stabilize before H5MD can build on it, both must be correct before the test suite can validate them, and benchmarks must exist before optimization makes sense.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Backend Architecture** - Extract BaseColumnarBackend, split padded/ragged variants, remove legacy Zarr, clean dead code
- [x] **Phase 2: H5MD Compliance** - Full H5MD 1.1 spec compliance with znh5md interop, dependency version fixes (completed 2026-03-06)
- [ ] **Phase 3: Contract Test Suite** - Unified parametrized test suite covering all backends through all facades
- [ ] **Phase 4: Benchmarks & Performance** - Establish benchmark baselines with pytest-benchmark, then optimize hot paths

## Phase Details

### Phase 1: Backend Architecture
**Goal**: All columnar backends use a clean inheritance hierarchy with dedicated padded and ragged variants, dispatched by file extension
**Depends on**: Nothing (first phase)
**Requirements**: ARCH-01, ARCH-02, ARCH-03, ARCH-04, ARCH-05, ARCH-06, QUAL-01, QUAL-05
**Success Criteria** (what must be TRUE):
  1. BaseColumnarBackend exists with shared logic (_postprocess, _serialize_value, _prepare_scalar_column, _discover, metadata management) and RaggedColumnarBackend and PaddedColumnarBackend inherit from it
  2. Opening a file with a ragged extension (e.g. `.h5`) creates a RaggedColumnarBackend, and a padded extension (e.g. `.h5p`) creates a PaddedColumnarBackend -- no ambiguity in registry resolution
  3. Legacy Zarr backend directory (`src/asebytes/zarr/`) is deleted and no imports reference it
  4. Existing tests pass against the new backend classes without behavior changes
**Plans:** 3/3 plans executed

Plans:
- [x] 01-01-PLAN.md — Extract BaseColumnarBackend + RaggedColumnarBackend, move utilities
- [x] 01-02-PLAN.md — Create PaddedColumnarBackend with padded storage
- [x] 01-03-PLAN.md — Update registry, delete legacy zarr, clean dead code

### Phase 2: H5MD Compliance
**Goal**: H5MDBackend reads and writes H5MD 1.1 compliant files with full znh5md interop, sharing logic with PaddedColumnarBackend via inheritance
**Depends on**: Phase 1
**Requirements**: H5MD-01, H5MD-02, H5MD-03, H5MD-04, H5MD-05, QUAL-02, QUAL-03, QUAL-04
**Success Criteria** (what must be TRUE):
  1. H5MDBackend can write ASE Atoms trajectories and the resulting file structure matches H5MD 1.1 spec (particles group with step/time/value datasets)
  2. Files written by znh5md can be read by H5MDBackend, and files written by H5MDBackend can be read by znh5md -- verified programmatically
  3. ASE Atoms round-trip through H5MDBackend preserves positions, cell, pbc, calculator results, info dict, arrays, and constraints
  4. H5MDBackend inherits shared columnar logic from BaseColumnarBackend rather than reimplementing it
  5. Dependency versions are corrected: lmdb >=1.6.0, h5py >=3.12.0, no unnecessary upper bounds
**Plans:** 4/4 plans complete

Plans:
- [x] 02-01-PLAN.md — Fix dependency versions, rename h5md extra to h5, generalize file_handle/file_factory
- [ ] 02-02-PLAN.md — Create H5MDStore implementing ColumnarStore with H5MD group layout
- [ ] 02-03-PLAN.md — Rewrite H5MDBackend to inherit PaddedColumnarBackend
- [ ] 02-04-PLAN.md — Add new feature tests, verify znh5md interop

### Phase 3: Contract Test Suite
**Goal**: A single parametrized test suite proves every backend is correct through BlobIO, ObjectIO, and ASEIO facades, with async mirrors
**Depends on**: Phase 1, Phase 2
**Requirements**: TEST-01, TEST-02, TEST-03, TEST-04, TEST-06, TEST-08, TEST-09, QUAL-06
**Success Criteria** (what must be TRUE):
  1. Running `uv run pytest tests/contract/` exercises every backend (HDF5 ragged, HDF5 padded, Zarr ragged, Zarr padded, H5MD, LMDB, MongoDB, Redis) through shared parametrized test functions
  2. Edge cases (empty datasets, single-frame, variable particle counts, large arrays, NaN/inf, empty strings, nested info dicts) are tested for every backend that supports them
  3. Async facades (AsyncBlobIO, AsyncObjectIO, AsyncASEIO) have mirrored parametrized tests using `@pytest.mark.anyio`
  4. H5MD spec compliance tests verify file structure, and interop tests validate cross-tool read/write with znh5md
  5. Tests against MongoDB and Redis run against real services via CI containers and fail (not skip) when services are unavailable
  6. Read-only backends (ASE .traj/.xyz/.extxyz, HuggingFace) are tested with a read-only contract subset (get, slice, keys, len, iteration)
**Plans:** 2/4 plans executed

Plans:
- [ ] 03-01-PLAN.md — Contract conftest, docker-compose, markers, and sync facade tests (BlobIO, ObjectIO, ASEIO)
- [ ] 03-02-PLAN.md — Async facade contract tests and H5MD compliance/interop tests
- [ ] 03-03-PLAN.md — Delete overlapping tests, remove importorskip patterns, clean conftest
- [ ] 03-04-PLAN.md — Read-only backend contract tests (ASE .traj/.xyz/.extxyz, HuggingFace)

### Phase 4: Benchmarks & Performance
**Goal**: Measurable performance baselines exist for all file-based backends, and targeted optimizations improve hot paths
**Depends on**: Phase 3
**Requirements**: TEST-05, TEST-07, PERF-01, PERF-02, PERF-03, PERF-04
**Success Criteria** (what must be TRUE):
  1. `uv run pytest benchmarks/` runs a pytest-benchmark suite covering sequential read, random access read, bulk write (extend), and column read for each file-based backend at multiple dataset sizes
  2. Benchmark data is generated synthetically via molify (smiles2conformers, pack, SinglePointCalculator, constraints, custom info/arrays) with no HuggingFace login required
  3. HDF5 backends have tuned chunk cache settings (rdcc_nbytes and rdcc_nslots) and benchmarks show measurable improvement on random access patterns
  4. MongoDB backend uses TTL index for cache expiration and Redis backend uses Lua scripts for bounds checking, with benchmark evidence of improvement
**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Backend Architecture | 3/3 | Complete | 2026-03-06 |
| 2. H5MD Compliance | 4/4 | Complete   | 2026-03-06 |
| 3. Contract Test Suite | 2/4 | In Progress|  |
| 4. Benchmarks & Performance | 0/2 | Not started | - |
