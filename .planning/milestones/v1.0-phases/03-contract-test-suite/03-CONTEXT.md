# Phase 3: Contract Test Suite - Context

**Gathered:** 2026-03-06
**Status:** Ready for planning

<domain>
## Phase Boundary

A single parametrized test suite proves every backend is correct through BlobIO, ObjectIO, and ASEIO facades, with async mirrors. Includes H5MD spec compliance tests, edge case coverage, and service-dependent backend validation. Overlapping existing tests are deleted as the contract suite supersedes them.

</domain>

<decisions>
## Implementation Decisions

### Test organization
- Fresh `tests/contract/` directory alongside existing tests
- Organized by facade: `test_blob_contract.py`, `test_object_contract.py`, `test_ase_contract.py`, `test_h5md_compliance.py`
- Async tests in separate files: `test_async_blob_contract.py`, `test_async_object_contract.py`, `test_async_ase_contract.py`
- Contract-specific `conftest.py` in `tests/contract/` owns all backend parametrization fixtures
- Root `conftest.py` keeps shared atom fixtures (s22, ethanol, atoms_with_*) — contract tests access them via pytest fixture mechanism (no direct imports from conftest)
- Existing tests that overlap with contract suite are deleted in this phase

### Backend matrix
- Full matrix: every backend tested through every facade it supports (Blob, Object, ASE) via adapters where needed
- Read-write backends in matrix: HDF5 ragged (.h5), HDF5 padded (.h5p), Zarr ragged (.zarr), Zarr padded (.zarrp), H5MD (.h5md), LMDB (.lmdb), MongoDB (mongodb://), Redis (redis://), Memory (memory://)
- Read-only backends get a read-only contract subset (get, slice, keys, len, iteration): ASE .traj/.xyz/.extxyz, HuggingFace
- H5MD compliance tests (file structure, znh5md interop) in dedicated `test_h5md_compliance.py`
- H5MD also participates in normal ASEIO contract tests as a parametrized backend
- All backends tested through async facades via SyncToAsyncAdapter (not just native async ones)

### Service failure policy
- MongoDB and Redis tests always fail (not skip) when services are unavailable — both locally and in CI
- `@pytest.mark.mongodb` and `@pytest.mark.redis` marks for selective running (`pytest -m 'not mongodb and not redis'`)
- `@pytest.mark.hf` mark for HuggingFace tests — skipped in CI, run locally when network is available
- Minimal `docker-compose.yml` at project root with MongoDB + Redis matching URIs in conftest.py

### Fixture strategy
- Reuse existing s22/ethanol/atoms_with_* fixtures from root conftest.py (accessed via pytest fixture mechanism)
- Both s22 (variable particle counts, 22 frames) and ethanol (fixed-size, 1000 frames) used as primary fixtures
- Backend capabilities expressed as pytest.param marks (e.g., supports_variable_particles, supports_per_atom_arrays) — edge case tests skip backends that lack the capability
- Round-trip verification at Atoms level: positions, numbers, cell, pbc, calc results, info, arrays, constraints compared via np.allclose / equality

### Claude's Discretion
- Which existing test files to delete (overlap analysis during planning)
- Exact capability marks and which backends get which marks
- Test helper utilities for Atoms comparison
- How to structure read-only contract tests for ASE/HF backends
- Fixture file generation for read-only backend tests

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- Root `conftest.py`: rich fixture library (s22 variants, ethanol, atoms_with_*, water, full_water, s22_info_arrays_calc, s22_mixed_pbc_cell, etc.)
- Existing `uni_blob_backend` / `uni_object_backend` fixtures: pattern reference for backend parametrization (covers 3 backends, needs expansion to 9+)
- `_registry.py`: complete backend registry with 8+ pattern/scheme entries — source of truth for which backends exist
- `SyncToAsyncAdapter` in `_async_backends.py`: wraps sync backends for async testing

### Established Patterns
- Backend registration via `_REGISTRY` list with pattern/scheme matching
- Three facade layers: BlobIO (bytes,bytes), ObjectIO (str,Any), ASEIO (str,Atoms) with adapter wrapping between layers
- `@pytest.mark.anyio` for async tests (QUAL-06 requirement)
- conftest.py uses `pytest.param` with ids for backend parametrization

### Integration Points
- `tests/contract/conftest.py`: new file providing backend parametrization for all 9 read-write backends + read-only backends
- `docker-compose.yml`: new file at project root for MongoDB + Redis services
- `pyproject.toml`: may need pytest mark registration for mongodb/redis/hf marks
- Existing test files: some will be deleted after contract suite supersedes them

</code_context>

<specifics>
## Specific Ideas

- Backend fixtures should use pytest.param with clear ids (e.g., "h5-ragged", "h5-padded", "zarr-ragged", "zarr-padded", "h5md", "lmdb", "mongodb", "redis", "memory")
- No direct imports from conftest.py — all test data accessed via pytest fixture mechanism
- s22 exercises variable particle count paths; ethanol exercises large fixed-size paths — both are valuable contract test inputs

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-contract-test-suite*
*Context gathered: 2026-03-06*
