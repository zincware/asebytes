---
phase: 03-contract-test-suite
plan: 04
subsystem: testing
tags: [pytest, contract-tests, read-only, ASE, HuggingFace, parametrize]

# Dependency graph
requires:
  - phase: 03-contract-test-suite
    plan: 01
    provides: "Contract test foundation with conftest.py, assert_atoms_equal, capability marks"
provides:
  - "Read-only contract tests for ASE file formats (.traj, .xyz, .extxyz)"
  - "HuggingFace synthetic contract tests with @pytest.mark.hf"
  - "readonly_aseio and hf_aseio fixtures in conftest.py"
  - "READONLY_ASE_BACKENDS param list"
affects: [04-performance]

# Tech tracking
tech-stack:
  added: [datasets (test fixture)]
  patterns: [synthetic-hf-fixture, count-frames-before-len]

key-files:
  created:
    - tests/contract/test_readonly_contract.py
  modified:
    - tests/contract/conftest.py

key-decisions:
  - "ASEReadOnlyBackend requires count_frames() before len() works; readonly_aseio fixture calls it automatically"
  - "HuggingFace tests use synthetic datasets.Dataset from s22 data to avoid network/auth dependencies (TEST-06)"
  - "All tests use s22 collection (22 frames) as canonical test data for read-only backends"

patterns-established:
  - "Read-only fixture pattern: write data with ase.io.write, open via ASEIO, call count_frames() on backend"
  - "Synthetic HuggingFace pattern: datasets.Dataset.from_dict() + ColumnMapping + direct HuggingFaceBackend injection"

requirements-completed: [TEST-01, TEST-02, TEST-06]

# Metrics
duration: 2min
completed: 2026-03-06
---

# Phase 03 Plan 04: Read-Only Contract Tests Summary

**36 read-only contract tests for ASE file formats (.traj, .xyz, .extxyz) and synthetic HuggingFace backend via parametrized ASEIO facade**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-06T15:17:41Z
- **Completed:** 2026-03-06T15:19:15Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- 30 ASE read-only tests (10 tests x 3 formats) covering len, get, negative index, slice, iteration, keys, write-rejection, and data preservation
- 6 HuggingFace tests using synthetic datasets.Dataset (no network/auth required)
- Full contract suite (187 pass, 7 skip, 80 deselected) remains green

## Task Commits

Each task was committed atomically:

1. **Task 1: Add read-only fixtures to conftest and create read-only contract tests** - `53abc25` (feat)

## Files Created/Modified
- `tests/contract/test_readonly_contract.py` - Read-only contract tests for ASE formats and HuggingFace
- `tests/contract/conftest.py` - Added READONLY_ASE_BACKENDS, readonly_aseio fixture, hf_aseio fixture

## Decisions Made
- ASEReadOnlyBackend does not know its length until count_frames() is called; the readonly_aseio fixture calls it so all tests can use len(), slicing, and negative indexing naturally
- HuggingFace fixture builds a synthetic datasets.Dataset from s22 positions/numbers, injecting HuggingFaceBackend directly into ASEIO -- zero network access, satisfying TEST-06
- Used s22 collection (22 variable-size molecules) as canonical test data, matching the existing contract test foundation

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Read-only contract tests complete; full contract test suite covers all 9 RW backends plus 3 read-only backends
- Ready for async facade tests or performance phase

---
*Phase: 03-contract-test-suite*
*Completed: 2026-03-06*
