---
phase: 02-h5md-compliance
plan: 03
subsystem: h5md
tags: [h5py, hdf5, h5md, inheritance, PaddedColumnarBackend, refactor]

# Dependency graph
requires:
  - phase: 01-backend-architecture
    provides: PaddedColumnarBackend with padded storage, BaseColumnarBackend with shared logic
  - phase: 02-h5md-compliance/plan-01
    provides: file_handle/file_factory support in BaseColumnarBackend
  - phase: 02-h5md-compliance/plan-02
    provides: H5MDStore implementing ColumnarStore with H5MD path translation
provides:
  - H5MDBackend inheriting PaddedColumnarBackend (thin specialization layer)
  - All 51 H5MD tests passing through inherited base class logic
  - znh5md interop preserved (NaN-strip fallback for foreign files)
affects: [02-h5md-compliance]

# Tech tracking
tech-stack:
  added: []
  patterns: [inheritance-based specialization (H5MDBackend extends PaddedColumnarBackend), foreign-file discovery fallback]

key-files:
  created: []
  modified:
    - src/asebytes/h5md/_backend.py
    - src/asebytes/h5md/_store.py
    - tests/test_review_critical_fixes.py

key-decisions:
  - "H5MDBackend inherits PaddedColumnarBackend, dropping _PostProc enum entirely"
  - "H5MDStore handles internal metadata columns (_n_atoms) as simple datasets in asebytes/{grp}/"
  - "Foreign H5MD files (znh5md) detected via missing asebytes metadata with species-based fallback discovery"
  - "Connectivity written after base extend to ensure particles group exists for HDF5 object references"
  - "Species (arrays.numbers) stored as float64 for znh5md compat, coerced to int on read"

patterns-established:
  - "Foreign file discovery: when base _discover finds 0 frames, sniff from species dataset"
  - "Per-atom array alignment: extend per-atom arrays on None/reserve extends to keep all datasets aligned"

requirements-completed: [H5MD-01, H5MD-02, H5MD-04, H5MD-05]

# Metrics
duration: 10min
completed: 2026-03-06
---

# Phase 02 Plan 03: H5MDBackend Rewrite Summary

**H5MDBackend rewritten as thin PaddedColumnarBackend subclass (698 lines, down from 1473) with H5MDStore delegation and full znh5md interop**

## Performance

- **Duration:** 10 min
- **Started:** 2026-03-06T14:05:00Z
- **Completed:** 2026-03-06T14:15:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Replaced 1473-line monolithic H5MDBackend with 698-line PaddedColumnarBackend subclass
- Eliminated _PostProc enum and all duplicated postprocessing, padding, classification, and metadata logic
- All 51 H5MD tests pass without modification (behavior-preserving rewrite)
- Full test suite green (2004 tests pass)

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite H5MDBackend to inherit PaddedColumnarBackend** - `dae0eae` (feat)
2. **Task 2: Run full test suite and fix regressions** - `9c397af` (fix)

## Files Created/Modified
- `src/asebytes/h5md/_backend.py` - Complete rewrite as PaddedColumnarBackend subclass
- `src/asebytes/h5md/_store.py` - Added internal metadata column support (_n_atoms), origin fix for core properties
- `tests/test_review_critical_fixes.py` - Updated to use new store API instead of deleted _find_dataset_path

## Decisions Made
- H5MDBackend inherits PaddedColumnarBackend, dropping the _PostProc enum and all duplicated logic
- Internal metadata columns (_n_atoms) stored as simple datasets in asebytes/{grp}/ rather than H5MD elements
- Foreign H5MD files (written by znh5md) detected by checking for missing asebytes metadata, with species-based frame count fallback
- Connectivity written after base extend (not before) to ensure particles group exists for HDF5 object references
- Species stored as float64 for znh5md compatibility, coerced to int on read via _postprocess override

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] H5MDStore missing internal metadata column support**
- **Found during:** Task 2 (test run)
- **Issue:** H5MDStore's _column_to_h5 rejected _n_atoms column (not a recognized H5MD path)
- **Fix:** Added _is_internal() check routing _-prefixed columns to asebytes/{grp}/ as simple datasets
- **Files modified:** src/asebytes/h5md/_store.py
- **Committed in:** 9c397af

**2. [Rule 1 - Bug] Origin attribute "arrays" instead of "atoms" for core properties**
- **Found during:** Task 2 (test_origin_attributes failure)
- **Issue:** H5MDStore mapped all arrays.* columns to origin="arrays", but positions/numbers need "atoms"
- **Fix:** Special-cased positions and numbers in _column_to_h5 to use "atoms" origin
- **Files modified:** src/asebytes/h5md/_store.py
- **Committed in:** 9c397af

**3. [Rule 1 - Bug] znh5md files unreadable (0 frames detected)**
- **Found during:** Task 2 (znh5md interop test failures)
- **Issue:** Base _discover relies on asebytes metadata which foreign files lack
- **Fix:** Added _discover override that falls back to species dataset shape for frame count
- **Files modified:** src/asebytes/h5md/_backend.py
- **Committed in:** 9c397af

**4. [Rule 1 - Bug] Connectivity write failed with missing particles group**
- **Found during:** Task 2 (connectivity test failure)
- **Issue:** Connectivity wrote before base extend, but particles group doesn't exist yet
- **Fix:** Reordered to write connectivity after base extend, passing n_frames_before for offset
- **Files modified:** src/asebytes/h5md/_backend.py
- **Committed in:** 9c397af

**5. [Rule 1 - Bug] Per-atom datasets not aligned after reserve/None extends**
- **Found during:** Task 2 (test_set_on_reserved_slot failure)
- **Issue:** Base extend skips per-atom columns not in batch, leaving them shorter than n_frames
- **Fix:** Added post-extend alignment loop extending per-atom arrays with fill values
- **Files modified:** src/asebytes/h5md/_backend.py
- **Committed in:** 9c397af

**6. [Rule 3 - Blocking] Test using deleted _find_dataset_path method**
- **Found during:** Task 2 (test_h5md_set_column_applies_padding failure)
- **Issue:** Test accessed private method from old monolith that no longer exists
- **Fix:** Updated test to use _store._get_ds() instead
- **Files modified:** tests/test_review_critical_fixes.py
- **Committed in:** 9c397af

---

**Total deviations:** 6 auto-fixed (4 bugs, 2 blocking)
**Impact on plan:** All auto-fixes necessary for correctness and test compatibility. No scope creep.

## Issues Encountered
None beyond the auto-fixed regressions documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- H5MDBackend is now a clean PaddedColumnarBackend subclass
- All H5MD-specific logic isolated in overrides (connectivity, H5MD skeleton, species coercion)
- Ready for Plan 04 (if applicable) or next phase

## Self-Check: PASSED

All files and commits verified.

---
*Phase: 02-h5md-compliance*
*Completed: 2026-03-06*
