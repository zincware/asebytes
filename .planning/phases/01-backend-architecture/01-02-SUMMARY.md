---
phase: 01-backend-architecture
plan: 02
subsystem: database
tags: [columnar, hdf5, zarr, padded, variable-atoms]

# Dependency graph
requires:
  - phase: 01-backend-architecture plan 01
    provides: BaseColumnarBackend with hook pattern, HDF5Store all-axis-None maxshape
provides:
  - PaddedColumnarBackend with rectangular padded per-atom storage
  - .h5p and .zarrp extension support for padded variant
  - _n_atoms tracking and axis-1 resize for variable particle counts
affects: [01-backend-architecture plan 03, 02-h5md-compliance]

# Tech tracking
tech-stack:
  added: []
  patterns: [padded rectangular storage with NaN/zero fill, axis-1 resize on max_atoms growth]

key-files:
  created:
    - src/asebytes/columnar/_padded.py
    - tests/test_padded_backend.py
  modified:
    - src/asebytes/columnar/__init__.py

key-decisions:
  - "Padded extensions .h5p/.zarrp remapped to .h5/.zarr stores internally"
  - "_n_atoms tracked as internal metadata (underscore-prefixed), not exposed via get_column"
  - "Axis-1 resize uses read-expand-rewrite via HDF5/Zarr native resize"

patterns-established:
  - "PaddedColumnarBackend hooks: _unpad_per_atom slices to [:n_atoms], _discover_variant caches _n_atoms and max_atoms"
  - "Extension remapping pattern: padded-specific extensions (.h5p, .zarrp) create standard stores"

requirements-completed: [ARCH-03]

# Metrics
duration: 4min
completed: 2026-03-06
---

# Phase 01 Plan 02: Padded Columnar Backend Summary

**PaddedColumnarBackend with (n_frames, max_atoms, ...) rectangular storage, NaN/zero padding, _n_atoms tracking, and axis-1 resize for variable particle counts**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-06T11:49:22Z
- **Completed:** 2026-03-06T11:53:10Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Implemented PaddedColumnarBackend inheriting BaseColumnarBackend with all per-atom read/write hooks
- Per-atom arrays stored as (n_frames, max_atoms, ...) with NaN fill for floats, 0 for ints, False for bools
- Variable particle counts: _n_atoms column tracks real atom count, read unpads to correct shape
- Axis-1 resize works when new batch has more atoms than existing max
- Both HDF5 (.h5p) and Zarr (.zarrp) formats fully supported
- 15 tests covering round-trip, variable particles, resize, scalars, fill values, get_column

## Task Commits

Each task was committed atomically:

1. **Task 1: Create PaddedColumnarBackend with tests (TDD)** - `467309a` (test: RED), `c44f303` (feat: GREEN)
2. **Task 2: Update columnar __init__.py exports and verify integration** - `dfa9e06` (chore)

_TDD task had separate RED/GREEN commits._

## Files Created/Modified
- `src/asebytes/columnar/_padded.py` - PaddedColumnarBackend with padded rectangular per-atom storage
- `tests/test_padded_backend.py` - 15 tests for padded storage (parametrized over HDF5 and Zarr)
- `src/asebytes/columnar/__init__.py` - Added PaddedColumnarBackend to exports

## Decisions Made
- Used .h5p/.zarrp extensions remapped to .h5/.zarr stores internally (avoids adding new store types)
- _n_atoms is internal metadata (underscore-prefixed), not exposed via get_column public API
- Axis-1 resize uses h5py/zarr native resize (HDF5Store maxshape already all-None from Plan 01)
- Adjusted _n_atoms test to verify via cache/store directly since underscore columns are internal

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed _n_atoms test to use internal API**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** get_column("_n_atoms") returns [None, None, None] because underscore-prefixed columns route through base ReadBackend.get_column which calls get() -- and get() skips underscore columns
- **Fix:** Changed test to verify _n_atoms via _n_atoms_cache and _store.get_array() instead of get_column()
- **Files modified:** tests/test_padded_backend.py
- **Verification:** All 15 tests pass
- **Committed in:** c44f303 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Test adjustment only -- implementation correct, test expectation mismatched internal API design.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Both RaggedColumnarBackend and PaddedColumnarBackend now coexist as BaseColumnarBackend subclasses
- Plan 03 (registry update) can now register both backend types with appropriate extensions
- PaddedColumnarBackend's storage layout matches znh5md, ready for H5MD compatibility in Phase 2
- All 1677 tests pass (15 new padded-specific, full suite green)

---
*Phase: 01-backend-architecture*
*Completed: 2026-03-06*

## Self-Check: PASSED

All 4 files verified present. All 3 task commits (467309a, c44f303, dfa9e06) found in git history. Line counts meet minimums (_padded.py: 514 >= 150, test_padded_backend.py: 237 >= 50).
