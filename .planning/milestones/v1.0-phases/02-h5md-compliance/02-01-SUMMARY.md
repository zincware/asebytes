---
phase: 02-h5md-compliance
plan: 01
subsystem: infra
tags: [h5py, hdf5, dependencies, file-handle, columnar]

# Dependency graph
requires:
  - phase: 01-backend-architecture
    provides: BaseColumnarBackend, HDF5Store, registry infrastructure
provides:
  - Corrected dependency versions (lmdb>=1.6.0, h5py>=3.12.0)
  - Renamed h5md extra to h5
  - file_handle support in HDF5Store and BaseColumnarBackend
  - file_factory support in BaseColumnarBackend
affects: [02-h5md-compliance]

# Tech tracking
tech-stack:
  added: []
  patterns: [file_handle/file_factory injection for HDF5Store, mutual-exclusivity validation]

key-files:
  created: []
  modified:
    - pyproject.toml
    - src/asebytes/_registry.py
    - src/asebytes/columnar/_store.py
    - src/asebytes/columnar/_base.py
    - src/asebytes/__init__.py
    - tests/test_optional_deps.py

key-decisions:
  - "file_handle creates HDF5Store with _owns_file=False (caller manages lifecycle)"
  - "file_factory called immediately at init time (not lazy) since _discover() needs the store"
  - "Error messages use uv add instead of pip install for consistency with project tooling"

patterns-established:
  - "file_handle/file_factory pattern: mutual exclusivity with store and file params, validated at init"
  - "HDF5Store _owns_file tracks ownership for close() behavior"

requirements-completed: [QUAL-02, QUAL-03, QUAL-04, H5MD-05]

# Metrics
duration: 3min
completed: 2026-03-06
---

# Phase 02 Plan 01: Dependencies and File Handle Support Summary

**Fixed lmdb/h5py dependency versions, renamed h5md extra to h5, and added file_handle/file_factory injection to HDF5Store and BaseColumnarBackend**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-06T13:54:17Z
- **Completed:** 2026-03-06T13:57:17Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Corrected lmdb version pin from >=1.7.5 (non-existent) to >=1.6.0 and bumped h5py from >=3.8.0 to >=3.12.0
- Renamed optional extra from h5md to h5 across pyproject.toml, registry hints, and dev dependencies
- HDF5Store now accepts file_handle parameter for pre-opened h5py.File objects with proper ownership tracking
- BaseColumnarBackend accepts file_handle and file_factory with mutual exclusivity validation against store and file

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix dependency versions, rename extra, update registry hints** - `d240bda` (chore)
2. **Task 2: Generalize file_handle and file_factory into HDF5Store and BaseColumnarBackend** - `5ed9d58` (feat)

## Files Created/Modified
- `pyproject.toml` - Fixed lmdb/h5py versions, renamed h5md extra to h5
- `src/asebytes/_registry.py` - Updated extras hints from h5md to h5, changed pip to uv in error message
- `src/asebytes/columnar/_store.py` - Added file_handle parameter to HDF5Store
- `src/asebytes/columnar/_base.py` - Added file_handle and file_factory parameters to BaseColumnarBackend
- `src/asebytes/__init__.py` - Updated error message from pip install to uv add
- `tests/test_optional_deps.py` - Updated test expectations for uv add error messages

## Decisions Made
- file_handle creates HDF5Store with _owns_file=False so caller manages file lifecycle
- file_factory is called immediately at init (not lazy) because _discover() needs the store at construction time
- Error messages updated from "pip install" to "uv add" for project tooling consistency

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated error messages and tests for uv add**
- **Found during:** Task 2 (test suite run)
- **Issue:** Changing registry error message from "pip install" to "uv add" broke test_optional_deps.py assertions, and __init__.py had matching pip install message
- **Fix:** Updated __init__.py error message and all test expectations to use "uv add"
- **Files modified:** src/asebytes/__init__.py, tests/test_optional_deps.py
- **Verification:** Full test suite passes (2004 passed)
- **Committed in:** 5ed9d58 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Necessary consistency fix. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- file_handle/file_factory pattern ready for H5MDBackend rewrite (plan 02-02)
- All dependency versions corrected and verified
- Full test suite green (2004 passed)

---
*Phase: 02-h5md-compliance*
*Completed: 2026-03-06*
