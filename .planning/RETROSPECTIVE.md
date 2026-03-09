# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — Maintenance & Performance Overhaul

**Shipped:** 2026-03-06
**Phases:** 4 | **Plans:** 13

### What Was Built
- Clean backend inheritance hierarchy (Base -> Ragged/Padded/H5MD) with extension-based dispatch
- H5MDBackend rewritten as PaddedColumnarBackend subclass with full znh5md interop
- Unified contract test suite (425+ tests) covering all backends through all facades
- Benchmark suite with synthetic data, 2x2 parametrization, saved baselines
- Performance optimizations: HDF5 chunk cache, MongoDB TTL cache, Redis Lua scripts, facade bounds-check elimination

### What Worked
- Coarse 4-phase granularity kept planning overhead low while maintaining clear dependencies
- Architecture-first ordering paid off: H5MD refactor was straightforward because the base class existed
- Contract test suite as Phase 3 caught integration issues before Phase 4 benchmarks
- Synthetic data via molify eliminated all CI auth dependencies
- Parallel plan execution within phases saved significant time

### What Was Inefficient
- ROADMAP.md plan checkboxes got out of sync with actual completion (Phase 3 shows 3/4 in roadmap but 4/4 on disk)
- Zarr ragged trajectory read regression (2-6x slower) was only caught during manual benchmark comparison, not by any automated gate
- Nyquist validation was only completed for 1/4 phases — the others were left in draft state

### Patterns Established
- Extension-based backend dispatch: `.h5`/`.zarr` ragged, `.h5p`/`.zarrp` padded, `.h5md` H5MD
- Contract test pattern: parametrized fixtures in conftest.py, capability marks for backend-specific gating
- Benchmark pattern: session-scoped synthetic fixtures, 2x2 matrix, `--benchmark-save` for baselines
- Base+hook pattern: `_postprocess`/`_discover` with `_unpad_per_atom`/`_discover_variant` hooks

### Key Lessons
1. Benchmark baselines should be saved in git (`.benchmarks/`) from the start — without them, cross-branch comparison requires manual worktree setup
2. Performance regression tests need an automated gate, not just human review of benchmark output
3. `pytest.skip` in fixtures violates fail-fast principles — always let tests fail when services are unavailable

### Cost Observations
- Model mix: balanced profile (sonnet for research/planning, opus for execution/verification)
- All 13 plans executed in a single day
- Notable: Phase 4 Plan 02 (22min) was the longest — performance optimization required careful measurement

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0 | 4 | 13 | First milestone — established baseline process |

### Cumulative Quality

| Milestone | Tests | Source LOC | Test LOC |
|-----------|-------|-----------|----------|
| v1.0 | 425+ contract + benchmarks | 12,608 | 22,740 |

### Top Lessons (Verified Across Milestones)

1. Architecture changes before feature work — dependency ordering prevents rework
2. Contract tests before benchmarks — correctness before performance
