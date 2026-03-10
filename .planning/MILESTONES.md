# Milestones

## v0.3.1 CI Benchmark Infrastructure (Shipped: 2026-03-10)

**Phases completed:** 4 phases, 4 plans
**Timeline:** 2026-03-09 → 2026-03-10 (2 days)

**Key accomplishments:**
1. Benchmark CI workflow with github-action-benchmark auto-pushing to gh-pages on every main merge
2. PR benchmark comparison with 150% fail-on-regression gate and configurable alert threshold
3. GitHub Pages landing page with project info and live Chart.js benchmark dashboard
4. README updated with live dashboard link replacing 10 static PNG embeds
5. Per-test group isolation (UUID-based) fixing MongoDB and Redis contract test flakiness

---

## v1.0 Maintenance & Performance Overhaul (Shipped: 2026-03-06)

**Phases completed:** 4 phases, 13 plans
**Files modified:** 142 | **Lines changed:** +26,544 / -4,919
**Source:** 12,608 LOC | **Tests:** 22,740 LOC

**Key accomplishments:**
1. Refactored columnar backend into BaseColumnarBackend + RaggedColumnarBackend + PaddedColumnarBackend hierarchy with extension-based registry dispatch (.h5/.zarr ragged, .h5p/.zarrp padded)
2. Rewrote H5MDBackend as PaddedColumnarBackend subclass with H5MDStore for H5MD 1.1 group layout — reduced from 1473 to 714 lines, full znh5md interop verified
3. Built unified contract test suite (425+ tests) exercising all 9 RW backends + 3 read-only + HuggingFace through sync and async facades
4. Established pytest-benchmark baselines with 2x2 parametrization matrix (frames x atoms) using synthetic data — no auth-gated dependencies
5. Optimized hot paths: HDF5 rdcc_nslots tuning (10-14% faster H5MD reads), MongoDB TTL cache, Redis Lua scripts, facade bounds-check elimination
6. Cleaned codebase: deleted legacy Zarr backend, removed 3,568 lines of duplicate tests, fixed dependency versions (lmdb>=1.6.0, h5py>=3.12.0)

---

