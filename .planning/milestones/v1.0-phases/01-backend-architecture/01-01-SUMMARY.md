---
phase: 01-backend-architecture
plan: 01
subsystem: database
tags: [columnar, hdf5, zarr, inheritance, ragged]

# Dependency graph
requires: []
provides:
  - BaseColumnarBackend with shared logic for all columnar variants
  - RaggedColumnarBackend with offset+flat per-atom storage
  - columnar/_utils.py with extracted helper functions
  - HDF5Store all-axis-None maxshape for future axis-1 resize
affects: [01-backend-architecture plan 02, 01-backend-architecture plan 03]

# Tech tracking
tech-stack:
  added: []
  patterns: [base-class + hook pattern for per-atom read/write, _discover_variant hook]

key-files:
  created:
    - src/asebytes/columnar/_base.py
    - src/asebytes/columnar/_ragged.py
    - src/asebytes/columnar/_utils.py
  modified:
    - src/asebytes/columnar/__init__.py
    - src/asebytes/columnar/_store.py
    - src/asebytes/_columnar.py
    - tests/test_columnar_backend.py

key-decisions:
  - "Base+hook pattern: _postprocess calls _unpad_per_atom hook, _discover calls _discover_variant hook"
  - "Dropped .hdf5 extension support in BaseColumnarBackend (only .h5 and .zarr)"
  - "Left _backend.py in place for registry transition in Plan 03"

patterns-established:
  - "BaseColumnarBackend hook methods: _discover_variant, _unpad_per_atom, _read_per_atom_value, _write_per_atom_column, _set_per_atom_value, _has_per_atom_data, _get_many_per_atom, _get_column_per_atom"
  - "Shared logic in base, variant-specific overrides in subclasses"

requirements-completed: [ARCH-01, ARCH-02, QUAL-01]

# Metrics
duration: 5min
completed: 2026-03-06
---

# Phase 01 Plan 01: Base + Ragged Backend Summary

**Extracted BaseColumnarBackend with 20+ shared methods and RaggedColumnarBackend with offset+flat per-atom overrides, maintaining full backward compatibility**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-06T11:41:49Z
- **Completed:** 2026-03-06T11:46:56Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Extracted all shared columnar logic (15+ methods) into BaseColumnarBackend in _base.py
- Created RaggedColumnarBackend in _ragged.py overriding only per-atom read/write hooks
- Moved helper functions to columnar/_utils.py with re-export shim in _columnar.py
- Updated HDF5Store.create_array to use all-axis-None maxshape (enables PaddedColumnarBackend in Plan 02)
- All 1662 tests pass (103 columnar-specific, full suite green)

## Task Commits

Each task was committed atomically:

1. **Task 1: Move helpers and create BaseColumnarBackend + RaggedColumnarBackend** - `69b4da7` (feat)
2. **Task 2: Validate RaggedColumnarBackend through direct instantiation** - `39f2eaa` (test)

## Files Created/Modified
- `src/asebytes/columnar/_base.py` - BaseColumnarBackend with all shared logic
- `src/asebytes/columnar/_ragged.py` - RaggedColumnarBackend with offset+flat storage
- `src/asebytes/columnar/_utils.py` - Extracted helpers (concat_varying, get_fill_value, jsonable, get_version)
- `src/asebytes/columnar/__init__.py` - Updated exports with new classes and backward compat aliases
- `src/asebytes/columnar/_store.py` - HDF5Store maxshape changed to all-axis-None
- `src/asebytes/_columnar.py` - Now re-export shim for backward compatibility
- `tests/test_columnar_backend.py` - Added RaggedColumnarBackend smoke tests

## Decisions Made
- Used base+hook pattern: _postprocess calls _unpad_per_atom, _discover calls _discover_variant
- Dropped .hdf5 extension in BaseColumnarBackend (per CONTEXT.md, only .h5 supported)
- Left original _backend.py in place to avoid breaking registry during transition (Plan 03 scope)
- Added _get_many_per_atom and _get_column_per_atom as overridable hooks for batched per-atom reads

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- BaseColumnarBackend is ready for PaddedColumnarBackend to subclass (Plan 02)
- HDF5Store maxshape supports all-axis resize needed for padded storage
- Hook methods (_unpad_per_atom, _discover_variant, _read_per_atom_value, _write_per_atom_column) provide clean extension points
- Original _backend.py still serves registry -- Plan 03 will update registry to point to new classes

---
*Phase: 01-backend-architecture*
*Completed: 2026-03-06*

## Self-Check: PASSED

All 7 files verified present. Both task commits (69b4da7, 39f2eaa) found in git history.
