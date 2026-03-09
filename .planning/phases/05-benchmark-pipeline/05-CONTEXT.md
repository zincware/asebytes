# Phase 5: Benchmark Pipeline - Context

**Gathered:** 2026-03-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Every push to main produces benchmark results stored on gh-pages, building a historical baseline. No release-triggered benchmarks — releases link to the existing dashboard. PR benchmark runs and comparison comments are Phase 6 scope.

</domain>

<decisions>
## Implementation Decisions

### Backend selection
- All backends in CI benchmarks: LMDB, HDF5 (ragged), Zarr (ragged), H5MD, MongoDB, Redis
- Include competitor baselines: znh5md, extxyz, sqlite, aselmdb
- MongoDB and Redis Docker services needed in benchmark job (same as test job)
- Single Python version: latest (3.13) per CI-02

### Workflow architecture
- Separate `benchmark.yml` workflow file (not in tests.yml)
- Triggers via `workflow_run` after tests.yml completes successfully
- Benchmark job runs only after tests pass (`needs`-like behavior via workflow_run)
- Benchmarks run only on main pushes (not PRs — PR runs are Phase 6)
- No release-triggered benchmarks — every main push updates the dashboard; releases just link to it

### Benchmark data scope
- Full 2x2 dataset matrix (small/large frames × few/many atoms)
- All benchmark groups: write, read, random_access, property_access, update
- Use pytest-benchmark defaults for rounds/iterations (auto-calibrate)

### gh-pages setup
- Let github-action-benchmark auto-create the gh-pages branch on first push
- Benchmark data stored at `/dev/bench/` on gh-pages
- GitHub Pages enablement is a manual step (documented, not automated)
- Use GITHUB_TOKEN for pushing to gh-pages (no deploy key)

### Cleanup
- Remove benchmark steps from tests.yml (run benchmarks, visualize, upload artifact)
- Remove `docs/visualize_benchmarks.py` (superseded by github-action-benchmark dashboard)
- Add `.benchmarks/` to .gitignore (pytest-benchmark local cache)
- Delete local `.benchmarks/` directory

### Claude's Discretion
- Exact github-action-benchmark configuration parameters
- Workflow step ordering and caching strategy
- How to structure the pytest-benchmark JSON output for github-action-benchmark consumption

</decisions>

<specifics>
## Specific Ideas

- "Every push to main updates the benchmark site" — no snapshot/release complexity
- "Remove .benchmarks/ local cache — gh-pages is the source of truth"
- User wants Phase 6 to run benchmarks on every PR commit and compare against gh-pages baseline with a diff table comment

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/benchmarks/` — 5 benchmark test files (write, read, random_access, property_access, update) with `@pytest.mark.benchmark` marker and groups
- `tests/benchmarks/conftest.py` — shared fixtures for benchmark data (2x2 matrix)
- `tests/conftest.py` — session-scoped benchmark data fixtures
- `pyproject.toml` — pytest-benchmark >=5.2.1, `benchmark` marker configured, default addopts exclude benchmarks

### Established Patterns
- pytest-benchmark with `--benchmark-only --benchmark-json=benchmark_results.json` (current tests.yml invocation)
- Docker services for MongoDB 7 and Redis 7 already configured in tests.yml
- uv + astral-sh/setup-uv@v5 for CI Python setup

### Integration Points
- `.github/workflows/tests.yml` — remove benchmark steps, benchmark.yml triggers after this
- `.gitignore` — add `.benchmarks/` entry
- `docs/visualize_benchmarks.py` — to be deleted
- gh-pages branch — new, created by github-action-benchmark

</code_context>

<deferred>
## Deferred Ideas

- PR benchmark comparison comments with diff table — Phase 6
- Configurable alert threshold and fail-on-regression gate — Phase 6
- Chart.js dashboard with project docs — Phase 7
- README live benchmark figures — Phase 7

</deferred>

---

*Phase: 05-benchmark-pipeline*
*Context gathered: 2026-03-09*
