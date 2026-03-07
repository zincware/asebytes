---
phase: 04-benchmarks-performance
plan: 01
subsystem: testing
tags: [pytest, benchmarks, synthetic-data, molify, ase.build, parametrization]

# Dependency graph
requires:
  - phase: 03-contract-test-suite
    provides: contract test infrastructure and conftest fixtures
provides:
  - 4 session-scoped synthetic benchmark data fixtures (2x2 frames x atoms)
  - _attach_full_properties helper for realistic Atoms data
  - padded backend benchmark fixtures (.h5p, .zarrp)
  - 2x2 dataset parametrization matrix for benchmarks
affects: [04-benchmarks-performance]

# Tech tracking
tech-stack:
  added: []
  patterns: [session-scoped synthetic data generation, 2x2 parametrization matrix]

key-files:
  created: []
  modified:
    - tests/conftest.py
    - tests/benchmarks/conftest.py
    - tests/test_benchmark_file_size.py

key-decisions:
  - "Kept ethanol fixture unchanged to preserve contract test compatibility (constraints break columnar backends)"
  - "No MemoryBackend fixture -- does not exist in codebase"
  - "Network backend fixtures (MongoDB, Redis) skip gracefully when services unavailable"

patterns-established:
  - "Session-scoped fixtures for benchmark data to avoid regeneration overhead"
  - "2x2 parametrization: frames=[100,1000] x atoms=[small ~9, large ~108]"

requirements-completed: [TEST-05, TEST-07]

# Metrics
duration: 4min
completed: 2026-03-06
---

# Phase 4 Plan 1: Benchmark Data Fixtures Summary

**Synthetic 2x2 benchmark data (ethanol/periodic x 100/1000 frames) with full properties and padded backend fixtures**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-06T16:29:24Z
- **Completed:** 2026-03-06T16:33:15Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Replaced lemat (HuggingFace-dependent) with fully synthetic benchmark data
- Added 4 session-scoped fixtures covering 2x2 parametrization matrix (frames x atoms)
- Added padded backend fixtures (bench_h5_padded, bench_zarr_padded) alongside existing ragged fixtures
- 328 benchmark tests now collect across all 4 dataset sizes

## Task Commits

Each task was committed atomically:

1. **Task 1: Replace lemat with synthetic data fixtures** - `88fb905` (feat)
2. **Task 2: Update benchmark conftest with 2x2 parametrization** - `8be4f8f` (feat)

## Files Created/Modified
- `tests/conftest.py` - Added _attach_full_properties helper and 4 session-scoped benchmark fixtures; removed lemat fixture
- `tests/benchmarks/conftest.py` - Updated DATASETS to 4 synthetic datasets; added padded backend fixtures; network backends skip gracefully
- `tests/test_benchmark_file_size.py` - Updated dataset references from lemat to new synthetic datasets

## Decisions Made
- Kept ethanol fixture unchanged (no _attach_full_properties) to preserve contract test compatibility -- adding constraints breaks columnar backend round-trips
- Skipped MemoryBackend fixture -- no MemoryBackend class exists in the codebase
- Network backend fixtures (MongoDB, Redis) use try/except to skip when services unavailable, since benchmarks measure performance not connectivity

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Reverted ethanol fixture to original behavior**
- **Found during:** Task 1
- **Issue:** Plan instructed to update ethanol fixture with _attach_full_properties, but this added constraints that broke columnar backend contract tests (FixAtoms not round-trippable)
- **Fix:** Kept ethanol fixture with original energy/forces/stress only; full properties only on session-scoped benchmark fixtures
- **Files modified:** tests/conftest.py
- **Verification:** 1845 contract tests pass
- **Committed in:** 88fb905

**2. [Rule 3 - Blocking] Updated test_benchmark_file_size.py lemat references**
- **Found during:** Task 2 verification
- **Issue:** tests/test_benchmark_file_size.py (outside benchmarks/ directory) still referenced deleted lemat fixture
- **Fix:** Updated DATASETS list and docstring to use new synthetic datasets
- **Files modified:** tests/test_benchmark_file_size.py
- **Verification:** grep -r "lemat" tests/ returns no matches
- **Committed in:** 8be4f8f

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered
None beyond the deviations documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Benchmark data infrastructure complete, ready for benchmark test implementation (04-02+)
- All 328 benchmark tests collect successfully
- Contract tests unaffected (1845 passing)

---
## Self-Check: PASSED

All files exist. All commit hashes verified.

---
*Phase: 04-benchmarks-performance*
*Completed: 2026-03-06*
