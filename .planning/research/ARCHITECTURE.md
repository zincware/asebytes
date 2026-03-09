# Architecture: CI Benchmark Infrastructure

**Domain:** CI/CD benchmark integration for Python library
**Researched:** 2026-03-09
**Confidence:** HIGH (github-action-benchmark is well-documented, pytest-benchmark integration is a documented example)

## Current State

The existing workflow (`.github/workflows/tests.yml`) runs a 3x Python matrix (3.11, 3.12, 3.13) with Redis and MongoDB service containers. Each matrix leg:

1. Checks out code
2. Installs uv + dependencies
3. Runs `pytest` (full test suite)
4. Runs `pytest -m benchmark --benchmark-only --benchmark-json=benchmark_results.json`
5. Runs `docs/visualize_benchmarks.py` to produce PNGs
6. Uploads `benchmark_results.json` + `*.png` as artifacts per Python version

**Problem:** Results are ephemeral artifacts. No historical tracking, no PR feedback, no dashboard.

## Recommended Architecture

Use `benchmark-action/github-action-benchmark@v1` as the single tool for all three features (PR comments, committed results, GitHub Pages dashboard). It natively supports pytest-benchmark JSON, handles gh-pages commits, generates interactive dashboards, and supports PR alert comments.

### Architecture Overview

```
                    tests.yml (existing)
                          |
          +---------------+---------------+
          |               |               |
     py3.11 job      py3.12 job      py3.13 job
          |               |               |
    benchmark JSON   benchmark JSON   benchmark JSON
          |               |               |
          +-------+-------+
                  |
          benchmark job (NEW, needs: test)
                  |
          +-------+-------+-------+
          |               |       |
     download         download   download
     3.11 artifact    3.12 art.  3.13 art.
          |               |       |
     github-action-   (repeat)  (repeat)
     benchmark@v1
     name: "py3.11"
          |
     gh-pages branch
     /dev/bench/py3.11/
     /dev/bench/py3.12/
     /dev/bench/py3.13/
          |
     GitHub Pages dashboard
     https://<user>.github.io/asebytes/dev/bench/
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `test` job (existing, per matrix leg) | Run benchmarks, produce JSON, upload artifacts | Artifact storage |
| `benchmark` job (NEW, runs after all matrix legs) | Download artifacts, run github-action-benchmark per Python version, push to gh-pages | `test` job via artifacts, gh-pages branch |
| `gh-pages` branch | Store historical benchmark data as JSON + HTML dashboard | GitHub Pages |
| GitHub Pages | Serve interactive dashboard | End users via browser |

### Data Flow

```
1. PR opened / push to main
   |
2. test job (matrix: 3.11, 3.12, 3.13) runs in parallel
   |-- pytest-benchmark produces benchmark_results.json
   |-- visualize_benchmarks.py produces PNGs (keep for artifact archive)
   |-- upload-artifact: benchmark-results-{python-version}
   |
3. benchmark job (needs: [test], runs-on: ubuntu-latest)
   |-- download-artifact: all benchmark-results-* artifacts
   |-- FOR EACH python version:
   |     |-- github-action-benchmark@v1
   |     |     tool: pytest
   |     |     output-file-path: benchmark-results-{ver}/benchmark_results.json
   |     |     name: "Python {ver}"
   |     |     benchmark-data-dir-path: dev/bench/py{ver}
   |     |     github-token: ${{ secrets.GITHUB_TOKEN }}
   |     |     comment-on-alert: true          (PR comment on regression)
   |     |     alert-threshold: "150%"         (50% regression triggers alert)
   |     |     fail-on-alert: false            (warn, don't block)
   |     |     auto-push: true                 (push only on main, see condition)
   |     |     gh-pages-branch: gh-pages
   |
4. gh-pages branch updated (main push only)
   |-- /dev/bench/py3.11/data.js  (appended benchmark entry)
   |-- /dev/bench/py3.12/data.js
   |-- /dev/bench/py3.13/data.js
   |-- /dev/bench/index.html      (auto-generated dashboard)
   |
5. GitHub Pages serves dashboard
```

## Key Design Decisions

### Decision 1: Single `benchmark` job after matrix completes

**Why:** `github-action-benchmark` pushes to gh-pages. If each matrix leg pushes independently, you get race conditions on the gh-pages branch. A single post-matrix job serializes the three `github-action-benchmark` calls.

**Implementation:** Use `needs: [test]` to wait for all matrix legs, then `actions/download-artifact@v4` to pull all three JSON files.

### Decision 2: Separate `benchmark-data-dir-path` per Python version

**Why:** Each Python version is a separate benchmark "suite." Using `name: "Python 3.11"` + `benchmark-data-dir-path: dev/bench/py3.11` gives each its own time-series chart on the dashboard. Users can compare performance across Python versions visually.

### Decision 3: `auto-push: true` only on main branch pushes

**Why:** On PRs, you want comparison comments but should NOT push results to gh-pages (PR benchmarks are noisy, transient, and would pollute the historical record). Use a conditional:

```yaml
auto-push: ${{ github.event_name == 'push' && github.ref == 'refs/heads/main' }}
```

PR runs still get `comment-on-alert: true` which compares against the last stored result and comments on the PR if regression is detected.

### Decision 4: Keep existing visualize_benchmarks.py + artifact uploads

**Why:** The PNGs serve a different purpose (static per-run snapshots in artifact archives). The github-action-benchmark dashboard provides historical trends. Both are valuable. No reason to remove existing functionality.

### Decision 5: No committed benchmark JSON in the repo's main branch

**Why:** The PROJECT.md mentions "Benchmark JSON committed to repo, overwritten per merge/tag" (BENCH-02). However, storing benchmark data in gh-pages via `github-action-benchmark` is strictly better:

- Keeps main branch clean (no benchmark data noise in git history)
- Dashboard is auto-generated from gh-pages data
- Historical tracking built-in
- No merge conflicts from benchmark data updates

If a committed-to-main JSON is still desired (e.g., for local comparison scripts), add a simple step that commits `benchmark_results.json` to a `benchmarks/results/` directory. But recommend against it -- gh-pages handles this better.

### Decision 6: alert-threshold at 150%

**Why:** CI environments have ~5-20% variance. A 150% threshold (50% regression) catches real regressions without false positives. Can be tuned after observing noise levels.

## Workflow Changes (Concrete)

### Existing steps to KEEP (no changes)

All current steps in the `test` job remain unchanged. The benchmark run, visualization, and artifact upload continue as-is.

### NEW: `benchmark` job

```yaml
  benchmark:
    needs: [test]
    runs-on: ubuntu-latest
    if: github.event_name == 'push' || github.event_name == 'pull_request'
    permissions:
      contents: write       # needed for gh-pages push
      pull-requests: write  # needed for PR comments
    steps:
      - uses: actions/checkout@v4

      - name: Download benchmark results (3.11)
        uses: actions/download-artifact@v4
        with:
          name: benchmark-results-3.11
          path: benchmark-results-3.11

      - name: Download benchmark results (3.12)
        uses: actions/download-artifact@v4
        with:
          name: benchmark-results-3.12
          path: benchmark-results-3.12

      - name: Download benchmark results (3.13)
        uses: actions/download-artifact@v4
        with:
          name: benchmark-results-3.13
          path: benchmark-results-3.13

      - name: Store benchmark (Python 3.11)
        uses: benchmark-action/github-action-benchmark@v1
        with:
          tool: pytest
          output-file-path: benchmark-results-3.11/benchmark_results.json
          name: "Python 3.11"
          benchmark-data-dir-path: dev/bench/py3.11
          github-token: ${{ secrets.GITHUB_TOKEN }}
          comment-on-alert: true
          alert-threshold: "150%"
          fail-on-alert: false
          auto-push: ${{ github.event_name == 'push' && github.ref == 'refs/heads/main' }}
          gh-pages-branch: gh-pages

      - name: Store benchmark (Python 3.12)
        uses: benchmark-action/github-action-benchmark@v1
        with:
          tool: pytest
          output-file-path: benchmark-results-3.12/benchmark_results.json
          name: "Python 3.12"
          benchmark-data-dir-path: dev/bench/py3.12
          github-token: ${{ secrets.GITHUB_TOKEN }}
          comment-on-alert: true
          alert-threshold: "150%"
          fail-on-alert: false
          auto-push: ${{ github.event_name == 'push' && github.ref == 'refs/heads/main' }}
          gh-pages-branch: gh-pages

      - name: Store benchmark (Python 3.13)
        uses: benchmark-action/github-action-benchmark@v1
        with:
          tool: pytest
          output-file-path: benchmark-results-3.13/benchmark_results.json
          name: "Python 3.13"
          benchmark-data-dir-path: dev/bench/py3.13
          github-token: ${{ secrets.GITHUB_TOKEN }}
          comment-on-alert: true
          alert-threshold: "150%"
          fail-on-alert: false
          auto-push: ${{ github.event_name == 'push' && github.ref == 'refs/heads/main' }}
          gh-pages-branch: gh-pages
```

### NEW: One-time setup (manual)

Create the `gh-pages` branch and enable GitHub Pages:

```bash
git checkout --orphan gh-pages
git reset --hard
git commit --allow-empty -m "Initialize gh-pages for benchmark dashboard"
git push origin gh-pages
git checkout main
```

Then in GitHub repo Settings > Pages: set source to `gh-pages` branch, root directory.

## Patterns to Follow

### Pattern 1: Post-matrix aggregation job

**What:** A job with `needs: [matrix-job]` that downloads all matrix artifacts and processes them serially.
**When:** Any time matrix outputs need to be combined or processed together.
**Why:** Avoids race conditions, ensures all data is available, runs only once.

### Pattern 2: Conditional auto-push

**What:** Use `auto-push: ${{ github.event_name == 'push' && github.ref == 'refs/heads/main' }}` to only persist results on main.
**When:** Any data that should only be committed from trusted branches.
**Why:** PRs should compare against baseline but not pollute it. Fork PRs lack write permissions anyway.

### Pattern 3: Per-suite benchmark-data-dir-path

**What:** Give each benchmark suite (Python version, backend type, etc.) its own directory on gh-pages.
**When:** Multiple benchmark dimensions exist.
**Why:** Each gets its own chart. Dashboard shows all suites. Clean data separation.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Running github-action-benchmark inside the matrix

**What:** Adding the benchmark action step directly in each matrix leg.
**Why bad:** Race conditions pushing to gh-pages. Three concurrent git pushes to the same branch will fail or lose data.
**Instead:** Post-matrix aggregation job (Pattern 1).

### Anti-Pattern 2: Committing benchmark JSON to main branch

**What:** Adding a step to commit benchmark_results.json to the repo's main branch after each CI run.
**Why bad:** Pollutes git history with binary-ish JSON data. Creates merge conflicts when multiple PRs merge. The gh-pages approach is purpose-built for this.
**Instead:** Let github-action-benchmark manage data on gh-pages.

### Anti-Pattern 3: Using `pull_request_target` for benchmark PR comments

**What:** Using `pull_request_target` to get write permissions for PR comments on fork PRs.
**Why bad:** Security risk -- `pull_request_target` runs the base branch workflow but can be tricked into running fork code with secrets.
**Instead:** Use `pull_request` event. Fork PRs won't get benchmark comments (acceptable tradeoff). For this project (likely no forks), `pull_request` with `permissions: pull-requests: write` is sufficient.

### Anti-Pattern 4: Storing all Python versions in one benchmark-data-dir-path

**What:** Using a single `name` parameter to differentiate Python versions within one directory.
**Why bad:** Charts become cluttered with 3x the data points. Hard to isolate per-version trends.
**Instead:** Separate `benchmark-data-dir-path` per Python version.

## Build Order (Dependency-aware)

| Phase | What | Depends On | Rationale |
|-------|------|-----------|-----------|
| 1 | Create `gh-pages` branch (manual, one-time) | Nothing | Required before any benchmark data can be pushed |
| 2 | Enable GitHub Pages in repo settings | Phase 1 | Required for dashboard to be accessible |
| 3 | Add `benchmark` job to `tests.yml` with `auto-push` on main only | Phases 1-2 | Core integration -- start accumulating data on main pushes |
| 4 | Enable `comment-on-alert` for PR feedback | Phase 3 | Needs baseline data from at least one main push to compare against |
| 5 | Tune `alert-threshold` based on observed CI variance | Phase 4 | Need real data to calibrate; start at 150%, adjust down if no false positives |
| 6 | (Optional) Add custom dashboard page or link from README | Phase 3 | Polish; the auto-generated dashboard works immediately |

**Key dependency:** Phase 4 (PR comments) technically works from Phase 3, but the first PR comparison requires at least one main branch data point stored on gh-pages. So the first merge to main after Phase 3 seeds the baseline.

## Scalability Considerations

| Concern | Current (3 versions) | At 5 versions | At 10+ versions |
|---------|---------------------|---------------|-----------------|
| CI time | +2-3min for benchmark job | +4-5min | Consider parallel benchmark jobs with locking |
| gh-pages size | ~KB per commit | Still small | Prune old entries periodically |
| Dashboard load | Fast, 3 charts | Fine | May want custom index.html grouping |
| Artifact storage | 3 artifacts/run | 5 artifacts/run | GitHub artifact retention policy (90 days default) handles cleanup |

## Sources

- [benchmark-action/github-action-benchmark](https://github.com/benchmark-action/github-action-benchmark) - PRIMARY tool, supports pytest natively, gh-pages dashboard, PR comments (HIGH confidence)
- [github-action-benchmark pytest example](https://github.com/benchmark-action/github-action-benchmark/blob/master/examples/pytest/README.md) - Pytest-specific configuration (HIGH confidence)
- [github-action-benchmark action.yml](https://github.com/benchmark-action/github-action-benchmark/blob/master/action.yml) - Full input parameter definitions (HIGH confidence)
- [openpgpjs/github-action-pull-request-benchmark](https://github.com/openpgpjs/github-action-pull-request-benchmark) - Fork focused on PR comparison; evaluated but original action covers needs (MEDIUM confidence)
- [nils-braun/pytest-benchmark-commenter](https://github.com/nils-braun/pytest-benchmark-commenter) - Alternative for PR comments only; rejected because github-action-benchmark does comments + dashboard + storage (MEDIUM confidence)
- [Running benchmarks for PRs via GitHub Actions (werat.dev)](https://werat.dev/blog/running-benchmarks-for-pull-requests-via-github-actions/) - Patterns for workflow_run and fork security (MEDIUM confidence)
- [GitHub Docs: Events that trigger workflows](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows) - workflow_run and pull_request security model (HIGH confidence)

---

*Architecture analysis: 2026-03-09*
