# Phase 4: Benchmarks & Performance - Context

**Gathered:** 2026-03-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish measurable performance baselines with pytest-benchmark for all backends, then implement targeted optimizations (HDF5 chunk cache, MongoDB TTL, Redis Lua bounds). H5MD is an externally defined standard and MUST NOT be modified — optimizations apply only to asebytes-native formats (.h5, .h5p, .zarr, .zarrp) and network backends.

</domain>

<decisions>
## Implementation Decisions

### Benchmark suite design
- Build on existing pytest-benchmark suite at `tests/benchmarks/` (5 files, all backends, facade-level)
- Update ROADMAP to reference `uv run pytest tests/benchmarks/` instead of `benchmarks/`
- Organize by operation (existing structure: bench_read, bench_write, bench_random_access, bench_property_access, bench_update)
- Benchmark through facades (ASEIO/ObjectIO) like real users — not direct backend access
- Cover ALL backends (file-based + MongoDB + Redis + LMDB + Memory)
- Keep third-party comparisons (aselmdb, sqlite, znh5md, extxyz) — they are dev dependencies, and being worse than them shows where to improve
- Isolate benchmarks from regular test suite via `@pytest.mark.benchmark` marker with pytest config excluding them from default runs

### Synthetic data generation
- Remove lemat dataset (depends on HuggingFace data, violates TEST-06)
- Replace with molify-generated data using molify.pack for periodic structures
- 2x2 parametrization matrix: frames=[100, 1000] x atoms=[small ~9 via smiles2conformers('CCO'), large ~50-100 via pack]
- Full properties per frame: positions, numbers, cell, pbc, SinglePointCalculator (energy, forces, stress), constraints, custom info/arrays
- Session-scoped fixtures for data generation (generate once, reuse across all benchmarks)

### Optimization scope
- PERF-01: HDF5 chunk cache tuning (rdcc_nbytes + rdcc_nslots) for .h5/.h5p backends
- PERF-02: MongoDB TTL cache with 1-second TTL (even 1ms gives 2.6x speedup per RESULTS.md; 1s is conservative)
- PERF-03: Redis Lua-only bounds checking — remove separate len() round-trip, Lua script does LLEN + bounds check atomically (2 RT -> 1 RT)
- H5MD is NOT touched — it follows the H5MD 1.1 spec, not asebytes-native storage
- No other optimizations beyond PERF-01/02/03

### Baseline recording
- Use pytest-benchmark `--benchmark-save=baseline` for JSON result storage
- Commit `.benchmarks/` directory to git for reproducible comparisons
- No CI regression detection for now (shared runners are noisy) — defer to pytest-codspeed (OPT-03, v2)
- Before/after comparison via `--benchmark-compare`

### Claude's Discretion
- Exact rdcc_nslots value for HDF5 chunk cache (tune based on benchmark evidence)
- Whether to add a `--benchmark-only` pytest marker alias for convenience
- How to handle MongoDB/Redis service unavailability during benchmark runs (skip vs fail)

</decisions>

<specifics>
## Specific Ideas

- "If we are worse than third-party alternatives, we know where to improve most" — benchmarks serve as a competitive analysis tool, not just baselines
- lemat must go — it depends on HuggingFace data which can't run in CI (TEST-06 violation)
- RESULTS.md in `benchmarks/proposals/` has proven speedup numbers: MongoDB TTL 3.5x, Redis Lua 1.9x — these are validated, not speculative

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/benchmarks/` — Complete pytest-benchmark suite (5 files, conftest with BenchDB dataclass, all backend fixtures including third-party comparisons)
- `tests/conftest.py` — Session-scoped `ethanol` fixture (1000 frames via molify.smiles2conformers), `mongo_uri`/`redis_uri` fixtures
- `benchmarks/proposals/` — Ad-hoc benchmark scripts with RESULTS.md containing proven optimization data
- `src/asebytes/redis/_lua.py` — Existing Lua scripts for atomic Redis operations
- `src/asebytes/columnar/_store.py` — HDF5Store already accepts `rdcc_nbytes` (64MB default), missing rdcc_nslots

### Established Patterns
- pytest-benchmark with `@pytest.mark.benchmark(group="...")` grouping
- Pre-populated BenchDB fixtures that exclude setup cost from measurements
- Facade-level benchmarking through ASEIO/ObjectIO constructors with path strings
- Third-party comparisons using native APIs (ase.db.connect, znh5md.IO, ase.io.write)

### Integration Points
- `tests/conftest.py` — Add new molify.pack fixtures here (session-scoped)
- `tests/benchmarks/conftest.py` — Update dataset parametrization (replace lemat with pack-generated data, add frame count parametrization)
- `src/asebytes/columnar/_store.py` line 83 — Add rdcc_nslots parameter alongside existing rdcc_nbytes
- `src/asebytes/mongodb/_backend.py` — Add TTL index for metadata cache
- `src/asebytes/redis/_lua.py` — Update Lua scripts with bounds checking
- `pyproject.toml` — Add benchmark marker to pytest config (addopts or markers)

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-benchmarks-performance*
*Context gathered: 2026-03-06*
