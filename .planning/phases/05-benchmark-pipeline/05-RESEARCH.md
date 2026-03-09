# Phase 5: Benchmark Pipeline - Research

**Researched:** 2026-03-09
**Domain:** GitHub Actions CI, pytest-benchmark, github-action-benchmark, gh-pages deployment
**Confidence:** HIGH

## Summary

Phase 5 creates a `benchmark.yml` workflow that triggers via `workflow_run` after the existing `tests.yml` completes on main branch pushes. It runs all benchmarks (5 test files, 2x2 dataset matrix, all backends + competitors) on Python 3.13, produces pytest-benchmark JSON, and uses `benchmark-action/github-action-benchmark@v1` to auto-push results to the `gh-pages` branch at `/dev/bench/`. The existing benchmark steps in `tests.yml` are removed, along with `docs/visualize_benchmarks.py`.

The user explicitly decided against release-triggered benchmark runs -- every main push updates the dashboard, so releases just link to the existing data. CI-04 is satisfied by documentation rather than a separate release workflow trigger.

**Primary recommendation:** Use `workflow_run` trigger with `actions/download-artifact@v4` (cross-workflow download via `run-id`) to decouple benchmarks from the test matrix, then `benchmark-action/github-action-benchmark@v1` with `auto-push: true` to commit results to gh-pages.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- All backends in CI benchmarks: LMDB, HDF5 (ragged), Zarr (ragged), H5MD, MongoDB, Redis
- Include competitor baselines: znh5md, extxyz, sqlite, aselmdb
- MongoDB and Redis Docker services needed in benchmark job (same as test job)
- Single Python version: latest (3.13) per CI-02
- Separate `benchmark.yml` workflow file (not in tests.yml)
- Triggers via `workflow_run` after tests.yml completes successfully
- Benchmark job runs only after tests pass (`needs`-like behavior via workflow_run)
- Benchmarks run only on main pushes (not PRs -- PR runs are Phase 6)
- No release-triggered benchmarks -- every main push updates the dashboard; releases just link to it
- Full 2x2 dataset matrix (small/large frames x few/many atoms)
- All benchmark groups: write, read, random_access, property_access, update
- Use pytest-benchmark defaults for rounds/iterations (auto-calibrate)
- Let github-action-benchmark auto-create the gh-pages branch on first push
- Benchmark data stored at `/dev/bench/` on gh-pages
- GitHub Pages enablement is a manual step (documented, not automated)
- Use GITHUB_TOKEN for pushing to gh-pages (no deploy key)
- Remove benchmark steps from tests.yml (run benchmarks, visualize, upload artifact)
- Remove `docs/visualize_benchmarks.py` (superseded by github-action-benchmark dashboard)
- Add `.benchmarks/` to .gitignore (pytest-benchmark local cache)
- Delete local `.benchmarks/` directory

### Claude's Discretion
- Exact github-action-benchmark configuration parameters
- Workflow step ordering and caching strategy
- How to structure the pytest-benchmark JSON output for github-action-benchmark consumption

### Deferred Ideas (OUT OF SCOPE)
- PR benchmark comparison comments with diff table -- Phase 6
- Configurable alert threshold and fail-on-regression gate -- Phase 6
- Chart.js dashboard with project docs -- Phase 7
- README live benchmark figures -- Phase 7
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CI-01 | gh-pages branch exists with GitHub Pages enabled serving benchmark dashboard | github-action-benchmark auto-creates gh-pages on first `auto-push: true` run; GitHub Pages enablement is manual (documented) |
| CI-02 | Post-matrix benchmark job runs github-action-benchmark for a single Python version (latest) | `workflow_run` trigger after tests.yml; single job on Python 3.13; no matrix |
| CI-03 | Auto-push to gh-pages only on main branch pushes, not PRs | `workflow_run` with `branches: [main]` filter ensures only main pushes trigger; `auto-push: true` only in this workflow |
| CI-04 | Release/tag events trigger a benchmark snapshot on gh-pages | User decision: NO separate release benchmark. Every main push updates dashboard. CI-04 satisfied by existing main-push pipeline -- releases link to dashboard. Document this in workflow comments. |
</phase_requirements>

## Standard Stack

### Core
| Library/Action | Version | Purpose | Why Standard |
|----------------|---------|---------|--------------|
| pytest-benchmark | >=5.2.1 | Run benchmarks, produce JSON output | Already in pyproject.toml; standard Python benchmarking |
| benchmark-action/github-action-benchmark | v1 | Parse JSON, update gh-pages, serve Chart.js dashboard | De facto standard for GitHub-hosted benchmark tracking (4k+ stars) |
| actions/upload-artifact | v4 | Upload benchmark JSON from tests workflow | GitHub official; needed for cross-workflow artifact passing |
| actions/download-artifact | v4 | Download benchmark JSON in benchmark workflow | GitHub official; supports `run-id` for cross-workflow |

### Supporting
| Library/Action | Version | Purpose | When to Use |
|----------------|---------|---------|-------------|
| astral-sh/setup-uv | v5 | Install uv + Python | Already used in tests.yml; reuse in benchmark.yml |
| actions/checkout | v4 | Checkout repository | Standard; needed for benchmark run |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| workflow_run trigger | Single workflow with `needs` | workflow_run keeps benchmark decoupled from test matrix; cleaner separation |
| GITHUB_TOKEN | Deploy key / PAT | GITHUB_TOKEN is simpler, no secret management; sufficient for same-repo gh-pages push |

## Architecture Patterns

### Workflow Architecture

Two-workflow design with artifact handoff:

```
tests.yml (push/PR)                    benchmark.yml (workflow_run)
  ├── test matrix (3.11, 3.12, 3.13)    ├── triggers: workflow_run [Tests] completed
  ├── run benchmarks (3.13 only)         ├── if: conclusion == 'success'
  ├── upload benchmark JSON artifact     ├── download artifact (run-id from event)
  └── ...                                ├── run github-action-benchmark
                                         └── auto-push to gh-pages
```

**IMPORTANT DECISION:** The user wants benchmarks to run inside `benchmark.yml`, NOT inside `tests.yml`. The `workflow_run` trigger means benchmark.yml fires after tests.yml completes, and benchmark.yml itself runs the benchmarks. There is no need to pass artifacts between workflows -- benchmark.yml checks out the code, installs deps, runs pytest-benchmark, and pushes results. This is simpler and avoids cross-workflow artifact complexity.

**Revised architecture (simpler):**
```
tests.yml (push/PR)                    benchmark.yml (workflow_run)
  ├── test matrix (3.11, 3.12, 3.13)    ├── triggers: workflow_run [Tests] completed, branches [main]
  └── (no benchmark steps)              ├── if: conclusion == 'success'
                                         ├── checkout code
                                         ├── setup uv + Python 3.13
                                         ├── install deps + start services
                                         ├── run pytest-benchmark → JSON
                                         └── github-action-benchmark auto-push to gh-pages
```

### Recommended Workflow Structure

```yaml
# .github/workflows/benchmark.yml
name: Benchmarks

on:
  workflow_run:
    workflows: ["Tests"]
    types: [completed]
    branches: [main]

permissions:
  deployments: write
  contents: write

jobs:
  benchmark:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'success' }}

    services:
      redis:
        image: redis:7
        ports: ["6379:6379"]
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      mongodb:
        image: mongo:7
        env:
          MONGO_INITDB_ROOT_USERNAME: root
          MONGO_INITDB_ROOT_PASSWORD: example
        ports: ["27017:27017"]
        options: >-
          --health-cmd "mongosh --eval 'db.runCommand(\"ping\").ok' --quiet"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Install uv and set Python version
        uses: astral-sh/setup-uv@v5
        with:
          python-version: "3.13"

      - name: Install package
        run: uv sync --all-extras --dev

      - name: Run benchmarks
        run: |
          uv run pytest -m benchmark --benchmark-only \
            --benchmark-json=benchmark_results.json

      - name: Store benchmark result
        uses: benchmark-action/github-action-benchmark@v1
        with:
          tool: "pytest"
          output-file-path: benchmark_results.json
          gh-pages-branch: gh-pages
          benchmark-data-dir-path: dev/bench
          github-token: ${{ secrets.GITHUB_TOKEN }}
          auto-push: true
```

### Anti-Patterns to Avoid
- **Running benchmarks in test matrix:** Wastes CI time by running benchmarks on Python 3.11 and 3.12 where results are discarded. Benchmark only on 3.13.
- **Using `workflow_dispatch` instead of `workflow_run`:** Loses automatic triggering; `workflow_run` ensures benchmarks only run after tests pass.
- **Storing benchmark JSON as artifact then downloading:** Over-engineering; since benchmark.yml runs its own benchmarks, no cross-workflow artifact transfer needed.
- **Using `comment-on-alert` in Phase 5:** This is Phase 6 scope (PR comparison comments). Keep Phase 5 focused on auto-push to gh-pages only.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Benchmark tracking over time | Custom data.js / JSON append logic | github-action-benchmark `auto-push` | Handles git operations, data.js format, Chart.js index.html generation |
| Benchmark visualization | matplotlib PNGs (visualize_benchmarks.py) | github-action-benchmark Chart.js dashboard | Auto-generated, interactive, no maintenance |
| gh-pages branch management | Manual git checkout/push scripts | github-action-benchmark `auto-push: true` | Handles orphan branch creation, merge, force-push |
| Benchmark JSON parsing | Custom JSON parsing/aggregation | github-action-benchmark `tool: pytest` | Knows pytest-benchmark JSON schema natively |

**Key insight:** `github-action-benchmark` handles the entire pipeline from JSON ingestion to gh-pages deployment. Zero custom code needed.

## Common Pitfalls

### Pitfall 1: workflow_run only triggers from default branch workflow file
**What goes wrong:** The `benchmark.yml` workflow file must exist on the default branch (main) for `workflow_run` to trigger. If you create it on a feature branch, it won't fire.
**Why it happens:** GitHub requires `workflow_run` workflow definitions to be on the default branch.
**How to avoid:** Merge the `benchmark.yml` to main first, then test. On the first merge, tests.yml will run and benchmark.yml will trigger.
**Warning signs:** Benchmark workflow never appears in Actions tab despite tests.yml completing.

### Pitfall 2: workflow_run branch filter applies to the triggering workflow's branch
**What goes wrong:** The `branches: [main]` filter in `workflow_run` filters on the branch that triggered the upstream workflow (tests.yml), not on the benchmark workflow's own branch.
**Why it happens:** Misunderstanding of branch filter scope.
**How to avoid:** This is actually the desired behavior -- `branches: [main]` means "only trigger when tests.yml ran on main," which is exactly what we want.

### Pitfall 3: GITHUB_TOKEN permissions for gh-pages push
**What goes wrong:** Auto-push fails with 403 because GITHUB_TOKEN lacks write permissions.
**Why it happens:** Default GITHUB_TOKEN permissions may be read-only depending on repo settings.
**How to avoid:** Set explicit `permissions: { contents: write, deployments: write }` at workflow or job level.
**Warning signs:** "HttpError: Resource not accessible by integration" in benchmark step logs.

### Pitfall 4: Docker services in workflow_run jobs
**What goes wrong:** MongoDB and Redis services not available because they're defined in tests.yml but not benchmark.yml.
**Why it happens:** `workflow_run` creates an entirely separate workflow run -- no shared services/environment.
**How to avoid:** Duplicate the `services` block from tests.yml into benchmark.yml's job definition.

### Pitfall 5: Removing benchmark steps from tests.yml prematurely
**What goes wrong:** Old benchmark data stops being collected before new pipeline is working.
**Why it happens:** Removing tests.yml benchmark steps in a different commit than adding benchmark.yml.
**How to avoid:** Add benchmark.yml and remove tests.yml benchmark steps in the same PR/merge. The first main push after merge will trigger the new pipeline.

### Pitfall 6: gh-pages branch not auto-created
**What goes wrong:** github-action-benchmark fails because gh-pages doesn't exist yet.
**Why it happens:** First-run issue; the action should auto-create the branch but edge cases exist.
**How to avoid:** The action with `auto-push: true` creates gh-pages automatically on first run. If it fails, manually create an orphan gh-pages branch: `git checkout --orphan gh-pages && git rm -rf . && git commit --allow-empty -m "init gh-pages" && git push origin gh-pages`.

## Code Examples

### pytest-benchmark JSON output format (consumed by github-action-benchmark)

```json
{
  "machine_info": { ... },
  "commit_info": { ... },
  "benchmarks": [
    {
      "group": "write_trajectory",
      "name": "test_write_trajectory_asebytes_lmdb[ethanol_100]",
      "fullname": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_lmdb[ethanol_100]",
      "stats": {
        "min": 0.001234,
        "max": 0.002345,
        "mean": 0.001567,
        "stddev": 0.000234,
        "rounds": 10,
        "iterations": 1,
        ...
      }
    }
  ]
}
```

github-action-benchmark with `tool: "pytest"` knows this format natively. No transformation needed.

### github-action-benchmark key inputs

```yaml
- uses: benchmark-action/github-action-benchmark@v1
  with:
    # Required
    tool: "pytest"                              # Parser type
    output-file-path: benchmark_results.json    # pytest-benchmark JSON

    # gh-pages configuration
    gh-pages-branch: gh-pages                   # Target branch (default)
    benchmark-data-dir-path: dev/bench          # Path on gh-pages (default)

    # Push configuration
    auto-push: true                             # Commit and push to gh-pages
    github-token: ${{ secrets.GITHUB_TOKEN }}   # Auth for push

    # Optional -- leave defaults for Phase 5
    # name: "Benchmark"                         # Display name in dashboard
    # comment-on-alert: false                   # Phase 6
    # alert-threshold: "150%"                   # Phase 6
    # fail-on-alert: false                      # Phase 6
    # max-items-in-chart: 0                     # Phase 7 (0 = unlimited)
```

### Cleanup: tests.yml after benchmark removal

Steps to remove from tests.yml:
```yaml
# REMOVE these 3 steps:
- name: Run benchmarks          # lines 58-62
- name: Visualize benchmarks    # lines 64-67
- name: Upload benchmark results # lines 69-76
```

### .gitignore addition

```
# Benchmark results (machine-specific)
.benchmarks/
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pytest-benchmark + matplotlib PNGs | github-action-benchmark + Chart.js | 2023+ | Automated dashboard, no custom code |
| Single workflow with benchmark steps | Separate workflow via workflow_run | GA feature | Decoupled, runs only on success |
| actions/upload-artifact@v3 | @v4 with run-id for cross-workflow | 2024 | Better cross-workflow support |

**Deprecated/outdated:**
- `docs/visualize_benchmarks.py`: Superseded by github-action-benchmark auto-dashboard. Delete in this phase.

## Open Questions

1. **Benchmark name grouping in dashboard**
   - What we know: github-action-benchmark groups by the `name` input. With many benchmarks (5 groups x 9 backends x 4 datasets = 180 benchmarks), the dashboard could be crowded.
   - What's unclear: Whether the default Chart.js dashboard handles 180+ data series gracefully.
   - Recommendation: Start with defaults. If crowded, consider using `name` input to separate by benchmark group (e.g., run the action step multiple times with filtered JSON). This is a Phase 7 concern.

2. **Benchmark runtime on CI**
   - What we know: With auto-calibration, pytest-benchmark adjusts rounds. 180 benchmarks could take 10-30 minutes.
   - What's unclear: Exact runtime on GitHub-hosted runners.
   - Recommendation: Accept auto-calibration defaults. Monitor first runs. If too slow, add `--benchmark-min-rounds=3` to cap iterations.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-benchmark >=5.2.1 |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest -m benchmark --benchmark-only -x --benchmark-json=benchmark_results.json` |
| Full suite command | `uv run pytest` (non-benchmark) + benchmark command above |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CI-01 | gh-pages branch exists with dashboard content | manual-only | Verify after first main push via `gh api repos/{owner}/{repo}/pages` | N/A -- infrastructure |
| CI-02 | Benchmark job runs on single Python version | manual-only | Check workflow run in Actions tab after merge | N/A -- workflow config |
| CI-03 | Auto-push only on main, not PRs | manual-only | Open test PR, verify no gh-pages push; push to main, verify gh-pages updated | N/A -- workflow config |
| CI-04 | Release/tag -> benchmark snapshot | manual-only | User decided: no release benchmarks. Verify documentation exists in workflow comments | N/A -- documentation |

**Manual-only justification:** All CI-* requirements are about GitHub Actions workflow behavior, which cannot be tested locally. Verification requires pushing to GitHub and observing workflow runs.

### Sampling Rate
- **Per task commit:** Lint the YAML with `python -c "import yaml; yaml.safe_load(open('.github/workflows/benchmark.yml'))"` to catch syntax errors
- **Per wave merge:** Push to main, observe Actions tab for workflow_run trigger
- **Phase gate:** gh-pages branch has benchmark data after first successful run

### Wave 0 Gaps
None -- existing test infrastructure (pytest-benchmark tests, pyproject.toml config) covers all benchmark execution needs. No new test files needed; this phase is purely CI infrastructure.

## Sources

### Primary (HIGH confidence)
- [benchmark-action/github-action-benchmark](https://github.com/benchmark-action/github-action-benchmark) - README, inputs, pytest example, auto-push behavior
- [GitHub Docs: workflow_run trigger](https://docs.github.com/actions/using-workflows/events-that-trigger-workflows#workflow_run) - Trigger behavior, branch filtering, artifact access, chain depth limit
- [actions/download-artifact@v4](https://github.com/actions/download-artifact/tree/v4) - Cross-workflow artifact download with run-id

### Secondary (MEDIUM confidence)
- [Cross-Workflow Artifact Passing](https://medium.com/@michamarszaek/cross-workflow-artifact-passing-in-github-actions-7f20acbb1b70) - Pattern for workflow_run + artifact download

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - github-action-benchmark is the de facto standard, well-documented
- Architecture: HIGH - workflow_run trigger is well-documented GitHub feature; pattern is straightforward
- Pitfalls: HIGH - drawn from official docs and common CI patterns

**Research date:** 2026-03-09
**Valid until:** 2026-04-09 (stable domain, unlikely to change)
