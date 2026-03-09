---
phase: 2
slug: h5md-compliance
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-06
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 |
| **Config file** | pyproject.toml [tool.pytest.ini_options] |
| **Quick run command** | `uv run pytest tests/test_h5md_backend.py -x -q` |
| **Full suite command** | `uv run pytest tests/ -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_h5md_backend.py -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| TBD | 01 | 1 | H5MD-05 | unit | `uv run pytest tests/test_h5md_backend.py -x -q` | Existing (51 tests) | pending |
| TBD | 01 | 1 | QUAL-02, QUAL-03 | smoke | `uv run python -c "import lmdb; import h5py"` | N/A | pending |
| TBD | 02 | 2 | H5MD-01 | unit+integration | `uv run pytest tests/test_h5md_backend.py::TestH5MDStructure -x` | Existing (6 tests) | pending |
| TBD | 02 | 2 | H5MD-02 | integration | `uv run pytest tests/test_h5md_backend.py::TestVariableShape tests/test_h5md_backend.py::TestPBCAndCell tests/test_h5md_backend.py::TestConnectivity -x` | Existing (13+ tests) | pending |
| TBD | 02 | 2 | H5MD-04 | integration | `uv run pytest tests/test_h5md_backend.py::TestBasicRoundTrip -x` | Existing (4 tests) | pending |
| TBD | 02 | 2 | H5MD-03 | integration | `uv run pytest tests/test_h5md_backend.py::TestZnH5MDCompat -x` | Existing (6 tests) | pending |

*Status: pending · green · red · flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_h5md_backend.py` — add tests for: auto-infer variable_shape, constraint round-trip, unit attributes on datasets, file_handle/file_factory parameters
- [ ] All 51 existing tests must pass after refactoring (regression baseline)

*Existing infrastructure covers most phase requirements; new tests needed for new features only.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| No unnecessary upper bounds in deps | QUAL-04 | Static check | Inspect pyproject.toml dependencies section |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
