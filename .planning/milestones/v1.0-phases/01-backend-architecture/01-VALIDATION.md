---
phase: 1
slug: backend-architecture
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-06
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 + pytest-benchmark 5.2.1 |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/test_columnar_backend.py -x -q` |
| **Full suite command** | `uv run pytest tests/ -x -q --ignore=tests/benchmarks` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_columnar_backend.py tests/test_columnar_store.py -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -x -q --ignore=tests/benchmarks`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | ARCH-01 | unit | `uv run pytest tests/test_columnar_backend.py -x` | Yes (needs update) | pending |
| 01-01-02 | 01 | 1 | ARCH-02 | unit | `uv run pytest tests/test_columnar_backend.py -x` | Yes | pending |
| 01-02-01 | 02 | 1 | ARCH-03 | unit | `uv run pytest tests/test_columnar_backend.py -x` | Partial (migrate from zarr tests) | pending |
| 01-02-02 | 02 | 1 | ARCH-04 | unit | `uv run pytest tests/test_unified_registry.py -x` | Yes (extend) | pending |
| 01-02-03 | 02 | 1 | ARCH-06 | unit | `uv run pytest tests/test_unified_registry.py -x` | Yes | pending |
| 01-03-01 | 03 | 2 | ARCH-05 | smoke | `uv run python -c "import asebytes.zarr"` should fail | No — Wave 0 | pending |
| 01-03-02 | 03 | 2 | QUAL-01 | unit | `uv run pytest tests/test_columnar_backend.py -x` | Yes (covered by read tests) | pending |
| 01-03-03 | 03 | 2 | QUAL-05 | smoke | `uv run python -c "from asebytes.zarr import ZarrBackend"` should fail | No — Wave 0 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_columnar_backend.py` — parameterize to test both RaggedColumnarBackend and PaddedColumnarBackend
- [ ] `tests/test_zarr_backend.py` — convert to test PaddedColumnarBackend or delete if redundant
- [ ] `tests/test_reserve_none.py` — update ZarrBackend imports to PaddedColumnarBackend
- [ ] `tests/test_unified_registry.py` — add tests for `*.h5p` and `*.zarrp` extensions
- [ ] Add smoke test that `import asebytes.zarr` raises ImportError after deletion

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
