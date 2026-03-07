---
phase: 02-h5md-compliance
verified: 2026-03-06T14:30:00Z
status: passed
score: 5/5 success criteria verified
must_haves:
  truths:
    - "H5MDBackend can write ASE Atoms trajectories and the resulting file structure matches H5MD 1.1 spec"
    - "Files written by znh5md can be read by H5MDBackend, and vice versa"
    - "ASE Atoms round-trip preserves positions, cell, pbc, calc results, info, arrays, and constraints"
    - "H5MDBackend inherits shared columnar logic from BaseColumnarBackend"
    - "Dependency versions corrected: lmdb >=1.6.0, h5py >=3.12.0, no unnecessary upper bounds"
  artifacts:
    - path: "src/asebytes/h5md/_backend.py"
      provides: "H5MDBackend inheriting PaddedColumnarBackend"
    - path: "src/asebytes/h5md/_store.py"
      provides: "H5MDStore implementing ColumnarStore with H5MD group layout"
    - path: "src/asebytes/h5md/__init__.py"
      provides: "Package exports including H5MDStore"
    - path: "src/asebytes/h5md/_mapping.py"
      provides: "ASE-to-H5MD name mapping constants"
    - path: "pyproject.toml"
      provides: "Corrected dependency versions and renamed extra"
    - path: "src/asebytes/_registry.py"
      provides: "Updated extras hint from h5md to h5"
    - path: "src/asebytes/columnar/_store.py"
      provides: "HDF5Store with file_handle support"
    - path: "src/asebytes/columnar/_base.py"
      provides: "BaseColumnarBackend with file_handle and file_factory"
    - path: "tests/test_h5md_backend.py"
      provides: "62 H5MD tests including auto-infer, constraints, units, file_handle, znh5md interop"
  key_links:
    - from: "src/asebytes/h5md/_backend.py"
      to: "src/asebytes/columnar/_padded.py"
      via: "class H5MDBackend(PaddedColumnarBackend)"
    - from: "src/asebytes/h5md/_backend.py"
      to: "src/asebytes/h5md/_store.py"
      via: "creates H5MDStore in __init__"
    - from: "src/asebytes/h5md/_store.py"
      to: "src/asebytes/h5md/_mapping.py"
      via: "imports ASE_TO_H5MD, H5MD_TO_ASE, KNOWN_PARTICLE_ELEMENTS, ORIGIN_ATTR"
---

# Phase 2: H5MD Compliance Verification Report

**Phase Goal:** H5MDBackend reads and writes H5MD 1.1 compliant files with full znh5md interop, sharing logic with PaddedColumnarBackend via inheritance
**Verified:** 2026-03-06T14:30:00Z
**Status:** passed
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths (from ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | H5MDBackend writes H5MD 1.1 compliant files (particles group with step/time/value datasets) | VERIFIED | H5MDStore creates step/time/value triad per element (lines 353-357 of _store.py). TestUnitAttributes and TestAutoInferVariableShape verify file structure via direct h5py inspection. |
| 2 | Files written by znh5md readable by H5MDBackend and vice versa | VERIFIED | TestZnH5MDCompat class has 8+ cross-compatibility tests (lines 505-600+ of test_h5md_backend.py). Foreign file discovery fallback in _discover() (lines 172-216 of _backend.py). |
| 3 | ASE Atoms round-trip preserves positions, cell, pbc, calc results, info, arrays, and constraints | VERIFIED | TestConstraintRoundTrip (3 tests), existing round-trip tests (51 original), constraint serialization via info.constraints_json column. |
| 4 | H5MDBackend inherits shared columnar logic from BaseColumnarBackend | VERIFIED | `class H5MDBackend(PaddedColumnarBackend)` at line 48 of _backend.py. _PostProc enum deleted. File reduced from 1473 to 714 lines. |
| 5 | Dependency versions corrected: lmdb >=1.6.0, h5py >=3.12.0, no unnecessary upper bounds | VERIFIED | pyproject.toml line 47: `lmdb>=1.6.0`, line 53: `h5py>=3.12.0`. Extra renamed from `h5md` to `h5` (line 52). No upper bounds on any dependency. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/asebytes/h5md/_backend.py` | H5MDBackend inheriting PaddedColumnarBackend | VERIFIED | 714 lines, contains `class H5MDBackend(PaddedColumnarBackend)`, no _PostProc enum |
| `src/asebytes/h5md/_store.py` | H5MDStore implementing ColumnarStore | VERIFIED | 516 lines, `class H5MDStore`, full path translation, step/time/value creation |
| `src/asebytes/h5md/__init__.py` | Updated exports | VERIFIED | Exports H5MDBackend, H5MDObjectBackend, H5MDStore |
| `src/asebytes/h5md/_mapping.py` | ASE-to-H5MD name mapping | VERIFIED | H5MD_TO_ASE, ASE_TO_H5MD, KNOWN_PARTICLE_ELEMENTS, ORIGIN_ATTR |
| `pyproject.toml` | Corrected deps and renamed extra | VERIFIED | lmdb>=1.6.0, h5py>=3.12.0, extra is `h5` not `h5md` |
| `src/asebytes/_registry.py` | Updated extras hints | VERIFIED | Lines 74-75: `"asebytes.h5md": "h5"`, `"asebytes.h5md._backend": "h5"` |
| `src/asebytes/columnar/_store.py` | HDF5Store with file_handle | VERIFIED | file_handle parameter at line 79, _owns_file tracking |
| `src/asebytes/columnar/_base.py` | BaseColumnarBackend with file_handle/file_factory | VERIFIED | Both parameters at lines 61-62, mutual exclusivity validation |
| `tests/test_h5md_backend.py` | New feature tests | VERIFIED | 62 tests total: auto-infer (3), constraints (3), units (3), file_handle (2+1), znh5md interop (8+) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `_backend.py` | `_padded.py` | `class H5MDBackend(PaddedColumnarBackend)` | WIRED | Line 48, import at line 18 |
| `_backend.py` | `_store.py` | `H5MDStore(...)` creation in __init__ | WIRED | Lines 84-94, import at line 26 |
| `_backend.py` | `_mapping.py` | `ASE_TO_H5MD, H5MD_TO_ASE, KNOWN_PARTICLE_ELEMENTS, ORIGIN_ATTR` | WIRED | Import at lines 20-25 |
| `_store.py` | `_mapping.py` | `ASE_TO_H5MD, H5MD_TO_ASE, KNOWN_PARTICLE_ELEMENTS, ORIGIN_ATTR` | WIRED | Import at lines 22-26 |
| `_store.py` | `columnar/_store.py` | Implements ColumnarStore protocol | WIRED | All protocol methods implemented (create_array, get_array, etc.) |
| `_base.py` | `_store.py` | `HDF5Store(file_handle=...)` creation | WIRED | Lines 95-98 pass file_handle to HDF5Store |
| `tests/test_h5md_backend.py` | `_backend.py` | imports and exercises H5MDBackend | WIRED | 62 tests all pass |
| `tests/test_h5md_backend.py` | `znh5md` | cross-import interop tests | WIRED | pytest.importorskip("znh5md") used in TestZnH5MDCompat |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| H5MD-01 | 02-02, 02-03 | H5MD 1.1 compliant read/write (particles, observables, step/time/value) | SATISFIED | H5MDStore creates proper group layout; verified by unit tests and h5py inspection |
| H5MD-02 | 02-03 | znh5md extensions: NaN padding, pbc_group, custom info/arrays | SATISFIED | PaddedColumnarBackend handles NaN padding; pbc_group parameter in __init__; info/arrays storage via H5MDStore path translation |
| H5MD-03 | 02-04 | Cross-tool interop with znh5md | SATISFIED | TestZnH5MDCompat has 8+ bidirectional tests; all pass |
| H5MD-04 | 02-03, 02-04 | ASE Atoms round-trip without data loss | SATISFIED | 62 tests pass including constraints, connectivity, variable-shape, info dict |
| H5MD-05 | 02-01, 02-02, 02-03 | H5MDBackend shares logic with PaddedColumnarBackend | SATISFIED | Inherits PaddedColumnarBackend; H5MD-specific logic only in overrides |
| QUAL-02 | 02-01 | Fix lmdb version pin (>=1.6.0) | SATISFIED | pyproject.toml: `lmdb>=1.6.0` |
| QUAL-03 | 02-01 | Bump h5py floor to >=3.12.0 | SATISFIED | pyproject.toml: `h5py>=3.12.0` |
| QUAL-04 | 02-01 | Remove unnecessary upper bounds | SATISFIED | No upper bounds on any dependency in pyproject.toml |

All 8 requirements mapped to this phase are satisfied. No orphaned requirements found.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| _backend.py | 702 | "placeholder rows" in error message | Info | Not a stub -- legitimate error message for append-only semantics |

No TODOs, FIXMEs, empty implementations, or stub patterns found in any H5MD module.

### Human Verification Required

### 1. H5MD File Structure Validation with External Tool

**Test:** Open a file written by H5MDBackend with an external H5MD viewer (e.g. h5dump or HDFView) and verify the group structure matches H5MD 1.1 spec.
**Expected:** /h5md group with version=[1,1], /particles/{grp}/{element}/value|step|time structure, /observables for scalars.
**Why human:** While tests verify structure via h5py, validating against an external reference tool provides additional confidence.

### 2. znh5md Interop with Real-World Datasets

**Test:** Use znh5md to write a complex trajectory (many species, variable particle counts, constraints, connectivity) and read with H5MDBackend.
**Expected:** All data preserved with no corruption or data type mismatches.
**Why human:** Tests use synthetic small molecules; real-world datasets may exercise edge cases not covered.

### Gaps Summary

No gaps found. All 5 success criteria from ROADMAP.md are verified. All 8 requirements are satisfied. The full test suite passes (2015 tests, 62 H5MD-specific). The H5MDBackend was successfully rewritten from a 1473-line monolith to a 714-line PaddedColumnarBackend subclass with H5MDStore handling the H5MD group layout translation.

---

_Verified: 2026-03-06T14:30:00Z_
_Verifier: Claude (gsd-verifier)_
