---
phase: 4
slug: benchmarks-performance
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-06
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + pytest-benchmark 5.2.1 |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options] |
| **Quick run command** | `uv run pytest tests/ -x -m "not benchmark"` |
| **Full suite command** | `uv run pytest tests/benchmarks/ -m benchmark --benchmark-enable` |
| **Estimated runtime** | ~30 seconds (contract tests), ~120 seconds (benchmarks) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -m "not benchmark"`
- **After every plan wave:** Run `uv run pytest tests/benchmarks/ -m benchmark --benchmark-enable`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | TEST-05 | benchmark | `uv run pytest tests/benchmarks/ -m benchmark --benchmark-enable -x` | Partial (lemat needs replacing) | pending |
| 04-01-02 | 01 | 1 | TEST-07 | benchmark | `uv run pytest tests/benchmarks/ -m benchmark --benchmark-enable` | Partial (single size) | pending |
| 04-02-01 | 02 | 2 | PERF-01 | benchmark | `uv run pytest tests/benchmarks/test_bench_random_access.py -m benchmark --benchmark-enable -k h5` | Exists | pending |
| 04-02-02 | 02 | 2 | PERF-02 | benchmark | `uv run pytest tests/benchmarks/test_bench_read.py -m benchmark --benchmark-enable -k mongodb` | Exists | pending |
| 04-02-03 | 02 | 2 | PERF-03 | benchmark | `uv run pytest tests/benchmarks/test_bench_read.py -m benchmark --benchmark-enable -k redis` | Exists | pending |
| 04-02-04 | 02 | 2 | PERF-04 | manual | `--benchmark-save=baseline` then `--benchmark-compare` | No baselines yet | pending |

*Status: pending · green · red · flaky*

---

## Wave 0 Requirements

- [ ] Replace `lemat` fixture in `tests/conftest.py` with molify/ase.build periodic data
- [ ] Add frame-count parametrization to `tests/benchmarks/conftest.py` DATASETS
- [ ] Add `_attach_full_properties` helper for consistent data generation
- [ ] Verify `--benchmark-save` creates `.benchmarks/` directory correctly

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Baseline comparison | PERF-04 | Requires before/after benchmark runs | Run with `--benchmark-save=baseline`, apply optimizations, run with `--benchmark-save=optimized`, compare with `--benchmark-compare` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
