# Project Research Summary

**Project:** asebytes maintenance and performance overhaul
**Domain:** Multi-backend scientific IO library (columnar storage for ASE Atoms)
**Researched:** 2026-03-06
**Confidence:** HIGH

## Executive Summary

asebytes is a Python IO library providing a unified MutableSequence facade over multiple storage backends (HDF5, Zarr, LMDB, MongoDB, Redis) for ASE Atoms trajectory data. The codebase has a clean layered architecture (Facade -> Backend ABC -> Store) but suffers from one structural problem that blocks all other improvements: the ColumnarBackend conflates padded and ragged storage strategies in a single 990-line class, while the H5MDBackend reimplements much of the same logic independently. This duplication must be resolved before testing, benchmarking, or optimization work can proceed cleanly.

The recommended approach is a bottom-up refactor: extract a shared BaseColumnarBackend, split into dedicated RaggedColumnarBackend and PaddedColumnarBackend, refactor H5MDBackend to inherit shared logic, then build a contract test suite parametrized across all backends. Only after correctness is proven should performance optimization begin. The stack is mature and stable -- h5py, zarr v3, lmdb, msgpack, pytest-benchmark are all well-chosen with no substitutions needed. The ad-hoc benchmark script should be migrated to pytest-benchmark fixtures for statistical rigor.

The key risks are: (1) metadata cache desync after the backend split, mitigated by extracting shared metadata management into the base class first; (2) HDF5 chunk cache thrashing on random access, mitigated by benchmarking access patterns before and after changes; (3) Zarr v3 API instability, mitigated by pinning to a specific minor version immediately; and (4) test suite explosion from Cartesian parametrization, mitigated by layering the test pyramid with slow-marked full-matrix tests.

## Key Findings

### Recommended Stack

The existing stack is well-chosen. No major technology changes needed -- only version floor corrections and tooling improvements.

**Core technologies:**
- **h5py >=3.12**: HDF5 read/write -- mature, stable, only viable Python HDF5 binding (bump floor from 3.8)
- **zarr >=3.0,<3.2**: Zarr v3 columnar storage -- pin upper bound due to rapid breaking changes in v3 releases
- **lmdb >=1.6.0**: Embedded key-value blob backend -- fix floor from nonexistent 1.7.5 to actual latest 1.6.2
- **msgpack + msgpack-numpy**: Binary serialization -- 3x faster decode than JSON, cross-language, no reason to switch
- **pytest-benchmark >=5.2.1**: Statistical microbenchmarks -- replace ad-hoc `time.perf_counter()` scripts
- **anyio pytest plugin**: Async testing -- simpler than pytest-asyncio, already a dependency

**Action items:** Fix lmdb version floor, bump h5py floor to 3.12, pin zarr upper bound, migrate benchmarks to pytest-benchmark.

### Expected Features

Most table-stakes features are already implemented. The gaps are in testing, benchmarking, and backend variant separation.

**Must have (table stakes -- already implemented but need validation):**
- MutableSequence API, slicing with lazy views, context managers, compression
- Column-oriented reads, bulk write (`extend`), async support, multiple backends
- Variable particle count support (ragged trajectories)
- Padded storage for uniform-size trajectories

**Must have (table stakes -- gaps to close):**
- H5MD read/write interoperability with znh5md (partially implemented, untested)
- Reproducible benchmark suite (ad-hoc only)
- Parametrized test suite with full coverage (exists but "messy")
- Split padded vs ragged into separate backend variants

**Should have (differentiators -- already implemented):**
- Unified facade across all backends (core value prop)
- Lazy concatenation (`db1 + db2`)
- Fast `dict_to_atoms` bypass (~6x speedup)
- Sync-to-async adapter
- Extension-based dispatch for padded vs ragged (planned, not yet implemented)

**Defer:**
- Cache-to improvements -- nice but not core maintenance scope
- Schema-in-metadata optimization -- post-overhaul polish
- New backend types -- explicitly out of scope

### Architecture Approach

The target architecture introduces a BaseColumnarBackend template method class that owns shared logic (~60% of current ColumnarBackend: scalar columns, JSON serialization, fill values, postprocessing, classification). RaggedColumnarBackend and PaddedColumnarBackend inherit from it, overriding only per-atom storage methods. H5MDBackend also inherits shared logic but uses h5py directly instead of ColumnarStore due to H5MD's incompatible nested layout. The registry dispatches based on file extension to separate variants.

**Major components:**
1. **BaseColumnarBackend** -- shared columnar logic: classification, scalar write/read, serialization, postprocessing
2. **RaggedColumnarBackend** -- offset+flat ragged storage for variable-size molecular data (default)
3. **PaddedColumnarBackend** -- NaN-padded storage for uniform-size data (opt-in via extension)
4. **H5MDBackend (refactored)** -- H5MD 1.1 spec compliance, inherits from BaseColumnarBackend, uses h5py direct
5. **ColumnarStore** -- array-level I/O abstraction (HDF5Store, ZarrStore) -- keep as-is, it works well
6. **Contract test suite** -- single parametrized test suite replacing 40+ per-feature test files

### Critical Pitfalls

1. **Metadata cache desync after backend split** -- Extract shared metadata management into BaseColumnarBackend before splitting. Add invariant assertions in tests that verify `_n_frames` matches on-disk state after every mutation.
2. **HDF5 chunk cache thrashing on random access** -- Set `rdcc_nslots` per HDF Group recommendation. Benchmark random vs sequential access patterns explicitly. The offset+flat ragged layout helps (contiguous reads) but scalar columns still use fancy indexing.
3. **Duplicated postprocessing logic** -- Extract `_postprocess()` into shared function BEFORE the backend split to avoid quadrupling the duplication. Add type-identity round-trip tests.
4. **Zarr v3 API surface instability** -- Pin zarr to specific minor version immediately. All zarr calls already isolated in ZarrStore (good).
5. **Registry collision on new file extensions** -- Design extension scheme and write registry resolution tests before implementing new backends. Put specific patterns before general ones.

## Implications for Roadmap

Based on research, the dependency chain dictates a 6-phase structure. The ordering is non-negotiable for phases 1-3 due to hard dependencies; phases 4-6 can be reordered.

### Phase 1: Extract BaseColumnarBackend and Split Variants
**Rationale:** Everything else depends on this. The shared base class must exist before padded/ragged can be separated. Doing this first is a pure refactor with no behavior changes -- low risk, high unlock.
**Delivers:** BaseColumnarBackend, RaggedColumnarBackend, PaddedColumnarBackend as separate classes. Updated registry with new extension patterns.
**Addresses:** Padded vs ragged separation (table stakes), extension-based dispatch (differentiator), postprocessing deduplication
**Avoids:** Metadata cache desync (Pitfall 1), duplicated postprocessing (Pitfall 3), registry collision (Pitfall 5), per-atom misclassification (Pitfall 8)

### Phase 2: H5MD Backend Refactor and Compliance
**Rationale:** H5MD interop with znh5md is the hardest requirement and most likely to surface design issues in the BaseColumnarBackend API. Test it early before the base class solidifies.
**Delivers:** H5MDBackend inheriting from BaseColumnarBackend. Verified round-trip with znh5md-written files. Separate spec compliance vs znh5md interop test suites.
**Addresses:** H5MD read/write interoperability (table stakes), znh5md compatibility
**Avoids:** Wrong spec version testing (Pitfall 9), duplicated H5MD logic (Architecture anti-pattern 2)

### Phase 3: Contract Test Suite
**Rationale:** Every subsequent change needs proof of correctness. The test harness must exist before optimization work begins. Build it after backends are stable but before any performance tuning.
**Delivers:** `tests/contract/` directory with parametrized test classes covering all backend variants. Central conftest fixtures. Layered test pyramid with `@pytest.mark.slow` for full matrix.
**Addresses:** Parametrized test suite (table stakes), reproducible correctness validation
**Avoids:** Test suite explosion (Pitfall 7), per-test-file fixtures (Architecture anti-pattern 3)

### Phase 4: Benchmark Suite Migration
**Rationale:** Performance baselines must be established before optimization. Migrating to pytest-benchmark provides statistical rigor (warmup, rounds, stddev) and CI integration.
**Delivers:** Structured benchmark suite using pytest-benchmark fixtures. Cold-start vs warm-path separation. Multiple dataset sizes. Random vs sequential access patterns. Baseline results saved.
**Uses:** pytest-benchmark >=5.2.1, molify for synthetic data generation
**Avoids:** Benchmarks measuring setup overhead (Pitfall 10)

### Phase 5: Performance Optimization
**Rationale:** Only optimize after correctness is proven and baselines are established. The benchmark results from Phase 4 identify where to focus.
**Delivers:** HDF5 chunk cache tuning (`rdcc_nslots`), backend-specific optimizations (MongoDB TTL, Redis Lua bounds -- validated 1.9-3.5x improvements). Zarr version pin with compatibility verification.
**Addresses:** Per-backend performance optimizations (differentiator), chunk cache configuration
**Avoids:** Chunk cache thrashing (Pitfall 2), Zarr API breakage (Pitfall 4)

### Phase 6: Codebase Declutter
**Rationale:** Lowest risk, no downstream dependencies. Remove dead code after everything else is stable and tested.
**Delivers:** Legacy Zarr backend removed, old ColumnarBackend alias removed, string serialization convention documented, caching policy documented with `refresh()` method.
**Addresses:** Code hygiene, documented conventions
**Avoids:** String serialization asymmetry (Pitfall 11), stale cache confusion (Pitfall 6)

### Phase Ordering Rationale

- **Phase 1 before Phase 2:** H5MDBackend refactor depends on BaseColumnarBackend existing
- **Phase 1 before Phase 3:** Contract tests need all backend variants to parametrize against
- **Phase 3 before Phase 4:** Benchmark fixtures reuse test data fixtures
- **Phase 4 before Phase 5:** Must establish baselines before optimizing
- **Phase 6 is independent:** Can run anytime after Phase 3, but doing it last avoids disruption during active development
- **Phases 2 and 3 can partially overlap:** H5MD compliance tests can be written as contract tests are being built

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1 (Backend Split):** The extension naming scheme (`.h5p` vs `.h5-padded` vs constructor param) needs a user decision. Registry ordering semantics need careful design. Recommend `/gsd:research-phase`.
- **Phase 2 (H5MD Compliance):** H5MD 1.1 spec vs znh5md conventions have subtle differences (variable particle count, PBC handling, connectivity groups). Needs reference file generation and cross-tool validation. Recommend `/gsd:research-phase`.

Phases with standard patterns (skip research-phase):
- **Phase 3 (Contract Tests):** Well-documented pytest parametrization patterns. Architecture research already provides the fixture design.
- **Phase 4 (Benchmarks):** pytest-benchmark usage is straightforward. Stack research already covers the approach.
- **Phase 5 (Performance):** HDF5 chunk cache tuning is well-documented by HDF Group. Optimizations are already benchmarked in `benchmarks/proposals/RESULTS.md`.
- **Phase 6 (Declutter):** Straightforward code removal with test coverage as safety net.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified against PyPI. Only correction needed: lmdb floor fix. Established tools with stable APIs. |
| Features | HIGH | Based on direct codebase analysis and comparison with znh5md/ASE DB. Most features already implemented; gaps are clear. |
| Architecture | HIGH | Based on direct codebase analysis. The BaseColumnarBackend extraction is a well-understood refactoring pattern. Component boundaries are clear. |
| Pitfalls | HIGH | Top pitfalls sourced from HDF Group documentation, Zarr migration guides, and direct code inspection. Prevention strategies are concrete. |

**Overall confidence:** HIGH

### Gaps to Address

- **Extension naming convention:** `.h5p`/`.zarrp` vs `.h5-padded`/`.h5-ragged` vs constructor parameter. Architecture research recommends extension-based but the exact names are a user decision. Resolve in Phase 1 planning.
- **Offset caching policy:** The "never cache" rule conflicts with ragged backend performance. Architecture research recommends pragmatic caching with `refresh()` method and documented limitations. Needs explicit user sign-off.
- **znh5md reference files:** No actual znh5md-written test fixtures exist in the repo. Phase 2 needs to generate these. Verify znh5md version compatibility (>=0.4.8 recommended).
- **Async adapter performance characteristics:** The SyncToAsyncAdapter starves the thread pool on bulk reads (Pitfall 13). This is documented but not measured. Low priority -- async is for convenience, not performance.

## Sources

### Primary (HIGH confidence)
- h5py PyPI and docs -- version verification, API stability
- zarr PyPI, docs, and migration guide -- v3 breaking changes, API surface
- lmdb PyPI -- version verification (1.6.2 is actual latest, not 1.7.5)
- pytest-benchmark docs -- fixture API, grouping, baseline comparison
- anyio docs -- pytest plugin usage
- HDF Group chunk cache documentation -- `rdcc_nslots`/`rdcc_nbytes` tuning
- H5MD 1.1 specification -- spec compliance requirements
- Direct codebase analysis of `src/asebytes/` -- architecture, patterns, duplication

### Secondary (MEDIUM confidence)
- znh5md GitHub repository -- interop conventions, NaN padding approach
- MDAnalysis documentation -- feature comparison
- pytest-codspeed PyPI -- optional CI enhancement
- Internal benchmark results (`benchmarks/proposals/RESULTS.md`) -- performance data

---
*Research completed: 2026-03-06*
*Ready for roadmap: yes*
