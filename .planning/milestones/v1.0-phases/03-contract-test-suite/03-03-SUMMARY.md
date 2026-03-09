---
phase: 03-contract-test-suite
plan: 03
subsystem: testing
tags: [pytest, cleanup, test-dedup, importorskip]

# Dependency graph
requires:
  - phase: 03-contract-test-suite
    provides: "Contract test suite (plans 01+02) that subsumes per-backend tests"
provides:
  - "Clean test directory with contract suite as primary coverage source"
  - "Fail-not-skip policy enforced for pymongo/redis imports"
affects: [04-performance]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Direct import instead of pytest.importorskip for required dependencies"
    - "Contract suite as single source of truth for backend correctness"

key-files:
  created: []
  modified:
    - tests/conftest.py
    - tests/test_mongodb.py
    - tests/test_redis.py
    - tests/test_redis_registry.py
    - tests/test_review_critical_fixes.py

key-decisions:
  - "Deleted 10 overlapping test files (3568 lines) fully subsumed by contract suite"
  - "Kept importorskip for znh5md/molify/datasets as optional/external deps"

patterns-established:
  - "TEST-09: required deps use direct import (fail on missing), optional deps use importorskip"

requirements-completed: [TEST-01, TEST-09]

# Metrics
duration: 2min
completed: 2026-03-06
---

# Phase 3 Plan 03: Test Cleanup Summary

**Deleted 10 overlapping test files (3568 lines) subsumed by contract suite, enforced fail-not-skip import policy for pymongo/redis**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-06T15:26:04Z
- **Completed:** 2026-03-06T15:28:49Z
- **Tasks:** 1
- **Files modified:** 15 (10 deleted, 5 modified)

## Accomplishments
- Deleted 10 test files fully subsumed by the contract test suite (3568 lines removed)
- Replaced pytest.importorskip with direct imports for pymongo and redis in 4 files
- Removed uni_blob_backend/uni_object_backend fixtures and factory functions from root conftest.py
- All 2039 remaining tests pass (8 skipped, 321 deselected)

## Task Commits

Each task was committed atomically:

1. **Task 1: Delete overlapping tests and remove importorskip patterns** - `f989500` (chore)

## Files Created/Modified

**Deleted (subsumed by contract suite):**
- `tests/test_universal_blob_backend.py` - parametrized blob backend tests
- `tests/test_universal_object_backend.py` - parametrized object backend tests
- `tests/test_aseio.py` - ASEIO CRUD tests
- `tests/test_bytesio.py` - BlobIO CRUD tests
- `tests/test_bytesio_update.py` - BlobIO update tests
- `tests/test_async_aseio.py` - async ASEIO tests
- `tests/test_async_blob_io.py` - async BlobIO tests
- `tests/test_async_object_io.py` - async ObjectIO tests
- `tests/test_async_aseio_atoms.py` - async atoms round-trip tests
- `tests/test_h5md_backend.py` - H5MD backend tests

**Modified:**
- `tests/conftest.py` - removed uni_blob_backend/uni_object_backend fixtures and factory functions
- `tests/test_mongodb.py` - replaced importorskip with direct import
- `tests/test_redis.py` - replaced importorskip with direct import
- `tests/test_redis_registry.py` - replaced importorskip with direct import
- `tests/test_review_critical_fixes.py` - replaced importorskip with direct import

## Decisions Made
- Kept pytest.importorskip for znh5md, molify, and datasets as these are genuinely optional/external dependencies
- Used noqa comments on pymongo/redis imports where the module isn't used directly but import ensures availability

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 03 (Contract Test Suite) complete -- all 3 plans executed
- Test directory lean with contract suite as primary backend correctness source
- Ready for Phase 04 (Performance)

---
*Phase: 03-contract-test-suite*
*Completed: 2026-03-06*
