# Technology Stack: CI Benchmark Infrastructure

**Project:** asebytes -- CI benchmark PR comments, committed results, GitHub Pages dashboard
**Researched:** 2026-03-09
**Confidence:** HIGH (primary tool verified via official repo, docs, and multiple sources)

## Recommendation: github-action-benchmark

Use `benchmark-action/github-action-benchmark@v1` for all three requirements (PR comments, committed results, GitHub Pages dashboard). It is purpose-built for this exact use case, actively maintained (1.2k stars, commits through 2025), and has native pytest-benchmark JSON support.

## Recommended Stack

### CI Benchmark Action

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| benchmark-action/github-action-benchmark | @v1 | PR comments, regression alerts, GitHub Pages dashboard | Native `tool: 'pytest'` input parses pytest-benchmark JSON directly. Stores history in `gh-pages` branch. Generates interactive Chart.js graphs. Supports `comment-on-alert`, `comment-always`, `auto-push`. Zero external services -- everything stays in-repo. **Confidence: HIGH** |

### GitHub Infrastructure

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| actions/checkout | @v4 | Fetch code for benchmark job | Required for github-action-benchmark to access gh-pages branch data |
| actions/download-artifact | @v4 | Retrieve benchmark JSON from matrix jobs | Post-matrix benchmark job needs results from all Python versions |
| actions/upload-artifact | @v4 | Archive raw JSON per run | Already in workflow. Keep for debugging/audit trail alongside committed results |
| GitHub Pages | N/A | Host interactive performance dashboard | Free for public repos. github-action-benchmark generates the index.html + data.js automatically |

### Existing Stack (unchanged)

| Technology | Version | Purpose | Notes |
|------------|---------|---------|-------|
| pytest-benchmark | >=5.2.1 | Generate benchmark JSON | Already produces `benchmark_results.json` via `--benchmark-json`. No changes needed to benchmark execution |
| uv / astral-sh/setup-uv | @v5 | Package management in CI | Already configured. Benchmarks run via `uv run pytest -m benchmark` |

## What github-action-benchmark Provides

### PR Comments (BENCH-01)
- `comment-on-alert: true` posts a comment when regression exceeds `alert-threshold` (default 200%)
- `comment-always: true` posts comparison on every PR (alternative -- recommended for asebytes)
- Comment includes table: benchmark name, current value, previous value, ratio
- Requires `github-token: ${{ secrets.GITHUB_TOKEN }}` and `permissions: pull-requests: write`

### Committed Results (BENCH-02)
- `auto-push: true` commits benchmark data to `gh-pages` branch automatically
- Data stored as JSON in configurable path (default: `dev/bench/`)
- Historical data accumulates -- each push appends to the dataset
- `max-items-in-chart: 100` controls history depth (prevents unbounded growth)
- Conditional push: `auto-push: ${{ github.event_name == 'push' && github.ref == 'refs/heads/main' }}` to only persist on main

### GitHub Pages Dashboard (BENCH-03)
- Generates `index.html` with Chart.js interactive line graphs
- One chart per benchmark group, tooltips show commit hash + values
- Accessible at `https://<user>.github.io/<repo>/dev/bench/`
- No build step needed -- the action generates static HTML directly

## Key Configuration Inputs

| Input | Value | Purpose |
|-------|-------|---------|
| `tool` | `'pytest'` | Parse pytest-benchmark JSON format |
| `output-file-path` | `benchmark_results.json` | Path to pytest-benchmark output |
| `github-token` | `${{ secrets.GITHUB_TOKEN }}` | Required for comments and auto-push |
| `auto-push` | `${{ github.event_name == 'push' && ... }}` | Only commit results on main merges |
| `comment-on-alert` | `true` | Post PR comment on regression |
| `alert-threshold` | `'150%'` | Regression threshold (150% = 50% slower). Start generous, tighten after baseline |
| `fail-on-alert` | `false` | Don't fail CI on regression (start soft, tighten later) |
| `summary-always` | `true` | Add to GitHub Actions job summary |
| `benchmark-data-dir-path` | `dev/bench/py{ver}` | Path within gh-pages branch, per Python version |
| `name` | `'Python {ver}'` | Separate charts per Python version |
| `gh-pages-branch` | `gh-pages` | Branch for storing results |
| `max-items-in-chart` | `100` | Limit historical data points |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| CI benchmark action | github-action-benchmark | **bencher.dev** | Requires external SaaS service or self-hosted server. Overkill for a library with <20 benchmarks. Free tier has metric limits. Adds API token management. Use if you need statistical regression detection with custom thresholds later. **Confidence: HIGH** |
| CI benchmark action | github-action-benchmark | **CML (cml.dev)** | ML-focused tool (model training, dataset versioning). Last release v0.20.6 (Oct 2024) -- 5+ months without updates as of research date. `cml comment create` can post markdown to PRs but has no benchmark-specific features (no trend charts, no regression detection, no historical storage). Would require writing all comparison logic manually. **Confidence: HIGH** |
| CI benchmark action | github-action-benchmark | **pytest-codspeed** | Different problem: CI-stable measurement via CPU simulation. Does NOT generate PR comments or dashboards from pytest-benchmark JSON. Requires CodSpeed cloud service. Useful as a complement (eliminates CI noise) but does not replace the dashboard/comment needs. Listed in backlog as OPT-03 -- evaluate separately. Actively maintained (v4.2.0, Oct 2025). **Confidence: HIGH** |
| CI benchmark action | github-action-benchmark | **airspeed-velocity (asv)** | Requires its own benchmark format (class-based, not pytest). Would need rewriting all benchmarks -- asebytes already has a pytest-benchmark suite. asv generates HTML reports but has no native PR comment support. Integration with pytest-benchmark is an open RFC (issue #567) with no resolution. Heavy for the use case. Latest release v0.6.5 (Sep 2025). **Confidence: HIGH** |
| CI benchmark action | github-action-benchmark | **conbench** | Enterprise-grade framework (used by Apache Arrow). Requires running a PostgreSQL server + web app. No native pytest-benchmark JSON ingestion. Massive overkill for a library project. `benchrun` package deprecated. **Confidence: MEDIUM** |
| CI benchmark action | github-action-benchmark | **Custom script + gh CLI** | Could manually parse JSON, compute diffs, post via `gh pr comment`. But reinvents what github-action-benchmark already does with tested edge cases (first run, missing baseline, chart generation). Not worth the maintenance. **Confidence: HIGH** |

## What NOT to Add

| Avoid | Why | Impact |
|-------|-----|--------|
| bencher.dev / Bencher Cloud | External service dependency for a simple library. API tokens, metric quotas, vendor lock-in | Complexity without proportional benefit |
| CML (iterative/cml) | Stale maintenance (last release Oct 2024). ML-focused, not benchmark-focused. No chart generation | Would require custom scripting for features github-action-benchmark provides out of the box |
| asv (airspeed-velocity) | Incompatible benchmark format. Would require rewriting existing pytest-benchmark suite | Wasted effort -- existing benchmarks work |
| conbench | Requires PostgreSQL server. Enterprise-grade for Apache Arrow scale. Way too heavy | Infrastructure overhead for zero gain |
| pytest-codspeed (for this milestone) | Solves a different problem (measurement stability). Does not produce PR comments or dashboards | Keep in backlog (OPT-03). Can layer on later without conflict |
| Multiple benchmark reporting tools | Complexity. One tool should own the PR comment + dashboard pipeline | Conflicting comments, maintenance burden |

## Installation

No Python packages to install. The only addition is a GitHub Actions step:

```yaml
# In .github/workflows/tests.yml, new benchmark job
- uses: benchmark-action/github-action-benchmark@v1
  with:
    tool: pytest
    output-file-path: benchmark_results.json
    # ... (see configuration inputs above)
```

One-time manual setup:
```bash
# Create gh-pages branch
git checkout --orphan gh-pages
git reset --hard
git commit --allow-empty -m "Initialize gh-pages for benchmark dashboard"
git push origin gh-pages
git checkout main

# Then: GitHub repo Settings > Pages > Source: gh-pages branch, root directory
```

## Sources

- [github-action-benchmark repository](https://github.com/benchmark-action/github-action-benchmark) -- feature list, inputs, pytest example. HIGH confidence
- [github-action-benchmark pytest example](https://github.com/benchmark-action/github-action-benchmark/blob/master/examples/pytest/README.md) -- workflow configuration. HIGH confidence
- [github-action-benchmark marketplace](https://github.com/marketplace/actions/continuous-benchmark) -- verified active, 1.2k stars. HIGH confidence
- [Bencher pytest-benchmark docs](https://bencher.dev/learn/track-in-ci/python/pytest-benchmark/) -- bencher integration details. HIGH confidence
- [Bencher pricing](https://bencher.dev/pricing/) -- free for public, metric-based billing for self-hosted. MEDIUM confidence
- [CML releases](https://github.com/iterative/cml/releases) -- last release v0.20.6, Oct 2024. HIGH confidence
- [CML GitHub](https://github.com/iterative/cml) -- ML-focused CI tool. HIGH confidence
- [asv pytest integration RFC](https://github.com/airspeed-velocity/asv/issues/567) -- open issue, no resolution. HIGH confidence
- [conbench GitHub](https://github.com/conbench/conbench) -- enterprise CB framework. MEDIUM confidence
- [pytest-codspeed PyPI](https://pypi.org/project/pytest-codspeed/) -- v4.2.0, Oct 2025. HIGH confidence
- [pytest-codspeed CodSpeed docs](https://codspeed.io/docs/reference/pytest-codspeed) -- requires CodSpeed service. HIGH confidence

---
*Stack research for: asebytes CI benchmark infrastructure (BENCH-01 through BENCH-04)*
*Researched: 2026-03-09*
