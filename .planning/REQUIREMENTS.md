# Requirements: asebytes Maintenance & Performance Overhaul

**Defined:** 2026-03-06
**Core Value:** Every storage backend must be fast, correct, and tested through a single parametrized test suite

## v1 Requirements

### Backend Architecture

- [x] **ARCH-01**: Extract BaseColumnarBackend with shared logic (_postprocess, _serialize_value, _prepare_scalar_column, _discover, metadata management) from ColumnarBackend and H5MDBackend
- [x] **ARCH-02**: Create RaggedColumnarBackend using offset+flat storage strategy, inheriting from BaseColumnarBackend
- [x] **ARCH-03**: Create PaddedColumnarBackend using NaN/zero-fill storage strategy, inheriting from BaseColumnarBackend
- [x] **ARCH-04**: Register dedicated file extensions for padded and ragged variants in the registry (e.g. `.h5`/`.zarr` for ragged, `.h5p`/`.zarrp` for padded or similar -- exact naming TBD)
- [x] **ARCH-05**: Remove legacy Zarr backend (`src/asebytes/zarr/`) and all references to it
- [x] **ARCH-06**: Update registry to avoid glob collisions between new extension patterns

### H5MD Compliance

**Note:** The H5MD 1.1 spec (https://www.nongnu.org/h5md/h5md.html) is the ground truth. ZnH5MD *extends* the standard with additional conventions (NaN padding for variable particle counts, pbc_group for per-frame PBC, custom info/arrays storage). Requirements distinguish between spec compliance and znh5md extension support.

**Architectural consideration:** H5MD uses padded storage -- evaluate whether H5MDBackend can be implemented as a specialization of PaddedColumnarBackend with H5MD-specific group layout on top, rather than a fully separate backend.

- [x] **H5MD-01**: H5MDBackend can read and write files compliant with the H5MD 1.1 specification (particles, observables, time-dependent data with step/time/value structure)
- [x] **H5MD-02**: H5MDBackend supports znh5md extensions: NaN padding for variable particle counts, pbc_group for per-frame PBC, custom info/arrays storage conventions
- [x] **H5MD-03**: H5MDBackend can read files written by znh5md and znh5md can read files written by H5MDBackend (cross-tool interop)
- [x] **H5MD-04**: H5MDBackend round-trips ASE Atoms objects through write-then-read without data loss (positions, cell, pbc, calc results, info, arrays, constraints)
- [x] **H5MD-05**: H5MDBackend shares logic with PaddedColumnarBackend where possible (both use padded storage), with H5MD-specific group layout handled via h5py directly

### Testing

- [x] **TEST-01**: Contract test suite with parametrized fixtures testing every backend through BlobIO, ObjectIO, and ASEIO facades
- [x] **TEST-02**: Edge case tests included in contract suite: empty datasets, single-frame, variable particle counts, large arrays, special float values (NaN, inf), empty strings, nested info dicts
- [ ] **TEST-03**: Async test suite mirroring sync contract tests using `@pytest.mark.anyio` for AsyncBlobIO, AsyncObjectIO, AsyncASEIO
- [ ] **TEST-04**: H5MD spec compliance tests verifying H5MD 1.1 structure, plus interop tests writing with znh5md then reading with asebytes and vice versa
- [ ] **TEST-05**: Performance benchmark suite using pytest-benchmark with synthetic data generated via molify (smiles2conformers, pack, SinglePointCalculator, constraints, custom info/arrays)
- [x] **TEST-06**: No test data behind authentication walls -- all CI test data is synthetic or bundled fixtures
- [ ] **TEST-07**: Benchmark covers: sequential read, random access read, bulk write (extend), column read, for each file-based backend, at multiple dataset sizes
- [x] **TEST-08**: All backend tests run against real services (Redis, MongoDB, etc.) via CI service containers -- no mocking to avoid service dependencies; only mock where semantically sensible
- [x] **TEST-09**: Tests must fail (not skip) when a required service or dependency is unavailable -- fix existing tests that use skip-if-not-available patterns

### Performance

- [ ] **PERF-01**: HDF5 chunk cache tuning -- set both rdcc_nbytes and rdcc_nslots for optimal random and sequential access
- [ ] **PERF-02**: MongoDB backend optimization with TTL index for cache expiration
- [ ] **PERF-03**: Redis backend optimization with Lua server-side scripts for bounds checking
- [ ] **PERF-04**: Establish benchmark baselines for all file-based backends before and after optimization changes

### Code Quality

- [x] **QUAL-01**: Consolidate duplicated _postprocess() logic across ColumnarBackend, ZarrBackend, H5MDBackend into BaseColumnarBackend
- [x] **QUAL-02**: Fix lmdb version pin (>=1.7.5 does not exist on PyPI -- correct to >=1.6.0)
- [x] **QUAL-03**: Bump h5py floor from >=3.8.0 to >=3.12.0 for modern HDF5 C library and bug fixes
- [x] **QUAL-04**: Remove unnecessary upper bounds on package versions -- prefer open-ended floors (>=X) for future safety
- [x] **QUAL-05**: Remove dead code paths and unused imports across all backend modules
- [ ] **QUAL-06**: Standardize async test markers to `@pytest.mark.anyio` consistently

## v2 Requirements

### Optimization Polish

- **OPT-01**: Store schema in backend metadata at write time for O(1) introspection (currently inferred per-row)
- **OPT-02**: Improve cache-to secondary backend pattern in ASEIO
- **OPT-03**: Investigate pytest-codspeed for CI-stable benchmarks (CPU simulation, no noise)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Query/filter engine (SQL-like WHERE) | ASE DB handles this; asebytes is IO, not a database |
| Unit conversion system | MDAnalysis handles this; ASE conventions are sufficient |
| Schema migration / versioning | Pre-release package; break formats freely until v1.0 |
| GUI or web interface | Python library for computational scientists |
| Distributed/parallel writes | HDF5 MPI is complex; out of scope for maintenance |
| New backend types | Maintenance overhaul, not feature expansion |
| Backwards compatibility with existing data files | Pre-release; format changes expected and encouraged |
| pyh5md read support | Nice-to-have but znh5md is the priority for H5MD interop |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ARCH-01 | Phase 1 | Complete |
| ARCH-02 | Phase 1 | Complete |
| ARCH-03 | Phase 1 | Complete |
| ARCH-04 | Phase 1 | Complete |
| ARCH-05 | Phase 1 | Complete |
| ARCH-06 | Phase 1 | Complete |
| H5MD-01 | Phase 2 | Complete |
| H5MD-02 | Phase 2 | Complete |
| H5MD-03 | Phase 2 | Complete |
| H5MD-04 | Phase 2 | Complete |
| H5MD-05 | Phase 2 | Complete |
| TEST-01 | Phase 3 | Complete |
| TEST-02 | Phase 3 | Complete |
| TEST-03 | Phase 3 | Pending |
| TEST-04 | Phase 3 | Pending |
| TEST-05 | Phase 4 | Pending |
| TEST-06 | Phase 3 | Complete |
| TEST-07 | Phase 4 | Pending |
| TEST-08 | Phase 3 | Complete |
| TEST-09 | Phase 3 | Complete |
| PERF-01 | Phase 4 | Pending |
| PERF-02 | Phase 4 | Pending |
| PERF-03 | Phase 4 | Pending |
| PERF-04 | Phase 4 | Pending |
| QUAL-01 | Phase 1 | Complete |
| QUAL-02 | Phase 2 | Complete |
| QUAL-03 | Phase 2 | Complete |
| QUAL-04 | Phase 2 | Complete |
| QUAL-05 | Phase 1 | Complete |
| QUAL-06 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 30 total
- Mapped to phases: 30
- Unmapped: 0

---
*Requirements defined: 2026-03-06*
*Last updated: 2026-03-06 after roadmap creation*
