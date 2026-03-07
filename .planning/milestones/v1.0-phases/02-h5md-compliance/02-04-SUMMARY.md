---
phase: 02-h5md-compliance
plan: 04
subsystem: h5md
tags: [h5py, hdf5, h5md, testing, constraints, units, variable-shape, file-handle]

# Dependency graph
requires:
  - phase: 02-h5md-compliance/plan-03
    provides: H5MDBackend as PaddedColumnarBackend subclass with full test suite
provides:
  - 11 new feature tests validating auto-infer variable_shape, constraint round-trip, unit attributes, and file_handle
  - Constraint serialization via JSON info column in H5MDBackend
  - Full znh5md cross-compatibility verification
affects: [03-testing]

# Tech tracking
tech-stack:
  added: []
  patterns: [constraint serialization via JSON info column (constraints -> info.constraints_json)]

key-files:
  created: []
  modified:
    - tests/test_h5md_backend.py
    - src/asebytes/h5md/_backend.py

key-decisions:
  - "Constraints serialized as JSON string in info.constraints_json column (avoids architectural changes to columnar storage)"
  - "Constraints reconstructed on get by converting info.constraints_json back to constraints dict key"

patterns-established:
  - "Constraint round-trip: extend converts constraints -> info.constraints_json, get reverses it"

requirements-completed: [H5MD-03, H5MD-04]

# Metrics
duration: 4min
completed: 2026-03-06
---

# Phase 02 Plan 04: H5MD Feature Tests Summary

**11 new tests for auto-infer variable_shape, constraint round-trip, unit attributes, and file_handle with constraint serialization via JSON info column**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-06T14:17:07Z
- **Completed:** 2026-03-06T14:21:18Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added 11 new feature tests covering all Plan 04 must-have truths
- Implemented constraint serialization round-trip through H5MDBackend via JSON info column
- Verified all 6 znh5md cross-compatibility tests pass
- Full test suite green: 2015 passed (62 H5MD-specific)

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Add failing tests for H5MD features** - `352c946` (test)
2. **Task 1 (GREEN): Implement constraint round-trip + all tests pass** - `4713ea7` (feat)
3. **Task 2: Verify znh5md cross-compatibility and full suite** - no code changes (verification only)

## Files Created/Modified
- `tests/test_h5md_backend.py` - Added TestAutoInferVariableShape (3), TestConstraintRoundTrip (3), TestUnitAttributes (3), TestFileHandle (2)
- `src/asebytes/h5md/_backend.py` - Added constraint serialization in extend() and deserialization in get()

## Decisions Made
- Constraints serialized as JSON string in `info.constraints_json` column to avoid changes to the columnar storage layer which strips the bare `constraints` key
- Deserialization in `get()` converts `info.constraints_json` back to `constraints` key so `dict_to_atoms` reconstructs ASE constraint objects

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Constraints not stored by H5MDBackend**
- **Found during:** Task 1 (RED phase -- constraint tests failed)
- **Issue:** PaddedColumnarBackend.extend() strips the `constraints` key from row dicts, so constraints were silently dropped
- **Fix:** H5MDBackend.extend() converts `constraints` to `info.constraints_json` (JSON string), and get() reverses the conversion
- **Files modified:** src/asebytes/h5md/_backend.py
- **Committed in:** 4713ea7

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Essential for constraint round-trip correctness. Minimal code change (8 lines in extend, 6 in get). No scope creep.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 2 (H5MD Compliance) is fully complete
- All H5MD features verified: auto-infer variable_shape, constraints, units, file_handle, znh5md interop
- Ready for Phase 3 (Testing) or Phase 4 (Performance)

## Self-Check: PASSED

---
*Phase: 02-h5md-compliance*
*Completed: 2026-03-06*
