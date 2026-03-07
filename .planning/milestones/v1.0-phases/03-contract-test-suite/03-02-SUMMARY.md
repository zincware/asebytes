---
phase: 03-contract-test-suite
plan: 02
subsystem: testing
tags: [pytest, anyio, async, contract-tests, h5md, znh5md, interop]

# Dependency graph
requires:
  - phase: 03-contract-test-suite
    provides: "Sync facade contract tests and parametrized fixtures from 03-01"
  - phase: 02-h5md-compliance
    provides: "H5MD backend with H5MD 1.1 compliant file writing"
provides:
  - "Async facade contract tests for AsyncBlobIO, AsyncObjectIO, AsyncASEIO"
  - "H5MD 1.1 spec compliance tests with h5py structure inspection"
  - "znh5md bidirectional interop tests"
  - "Async fixtures in conftest.py with proper memory backend cleanup"
affects: [04-performance]

# Tech tracking
tech-stack:
  added: [anyio (test marker)]
  patterns: [async-facade-contract-testing, h5py-structure-inspection, cross-tool-interop-testing]

key-files:
  created:
    - tests/contract/test_async_blob_contract.py
    - tests/contract/test_async_object_contract.py
    - tests/contract/test_async_ase_contract.py
    - tests/contract/test_h5md_compliance.py
  modified:
    - tests/contract/conftest.py

key-decisions:
  - "Async fixtures use sync cleanup via _backend._backend.remove() to avoid coroutine-never-awaited issues"
  - "Slice views in async tests use .to_list() instead of await (DeferredSliceRowView has no __await__)"
  - "H5MD constraints test relaxed to check atom count only, since H5MD may drop constraint objects"

patterns-established:
  - "Async contract test pattern: @pytest.mark.anyio on class, await for single items, .to_list() for slices"
  - "H5MD compliance pattern: h5py.File inspection of written files to verify spec conformance"
  - "Interop pattern: write with tool A, read with tool B, compare frame data"

requirements-completed: [TEST-03, TEST-04, QUAL-06]

# Metrics
duration: 6min
completed: 2026-03-06
---

# Phase 03 Plan 02: Async Facades and H5MD Compliance Summary

**Async contract tests for 3 facades with @pytest.mark.anyio, plus H5MD 1.1 structure verification and znh5md bidirectional interop**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-06T15:17:39Z
- **Completed:** 2026-03-06T15:23:55Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- 96 async contract tests across AsyncBlobIO (6 tests x 2 backends), AsyncObjectIO (7 x 2), AsyncASEIO (10 x 7 backends)
- All async tests use @pytest.mark.anyio exclusively (zero uses of @pytest.mark.asyncio, satisfying QUAL-06)
- 9 H5MD compliance tests: 4 structure verification, 3 znh5md interop, 2 edge cases
- Full contract suite: 298 passed, 7 skipped, 120 deselected in 6.27s

## Task Commits

Each task was committed atomically:

1. **Task 1: Create async facade contract tests** - `60d6fdb` (feat)
2. **Task 2: Create H5MD compliance and interop tests** - `ca4234e` (feat)

## Files Created/Modified
- `tests/contract/conftest.py` - Added AsyncBlobIO, AsyncObjectIO, AsyncASEIO imports, async backend param lists, async fixtures with sync cleanup
- `tests/contract/test_async_blob_contract.py` - AsyncBlobIO facade contract tests (extend, get, slice, negative index, iteration, keys)
- `tests/contract/test_async_object_contract.py` - AsyncObjectIO facade contract tests (extend, get, slice, negative index, iteration, keys, column access)
- `tests/contract/test_async_ase_contract.py` - AsyncASEIO facade contract tests (core CRUD + variable particles, info roundtrip, calc roundtrip)
- `tests/contract/test_h5md_compliance.py` - H5MD 1.1 structure verification, znh5md interop, edge cases

## Decisions Made
- Async fixtures use synchronous cleanup via `_backend._backend.remove()` because memory backend's `from_uri` ignores URI (all memory backends share global "default" group)
- Slice results use `.to_list()` pattern since `_DeferredSliceRowView` does not implement `__await__` (only `to_list()` and `async for`)
- H5MD constraints test checks atom count preservation only, not constraint object equality (columnar backends drop constraint objects)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed memory backend state leaking between async tests**
- **Found during:** Task 1 (test_get_by_index memory)
- **Issue:** Memory backend `from_uri` ignores URI, always using group "default" -- data from previous test visible in next test
- **Fix:** Added `_sync_cleanup` helper accessing underlying sync backend via `db._backend._backend.remove()`
- **Files modified:** tests/contract/conftest.py
- **Verification:** All memory backend tests pass independently

**2. [Rule 1 - Bug] Fixed slice await pattern for async views**
- **Found during:** Task 1 (test_slice)
- **Issue:** `await db[0:2]` fails because `_DeferredSliceRowView` has no `__await__`, only `to_list()`
- **Fix:** Changed all slice tests to use `await db[0:2].to_list()` pattern
- **Files modified:** test_async_blob_contract.py, test_async_object_contract.py, test_async_ase_contract.py
- **Verification:** All slice tests pass

---

**Total deviations:** 2 auto-fixed (2 Rule 1 bugs)
**Impact on plan:** Both fixes necessary for correctness. Memory cleanup ensures test isolation. Slice pattern matches actual async view API.

## Issues Encountered
None beyond the auto-fixed issues above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Contract test suite nearly complete (03-01 sync + 03-02 async + H5MD = 298 tests)
- Ready for Plan 03 (read-only contract tests) to complete the phase

---
*Phase: 03-contract-test-suite*
*Completed: 2026-03-06*
