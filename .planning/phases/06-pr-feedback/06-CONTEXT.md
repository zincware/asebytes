# Phase 6: PR Feedback - Context

**Gathered:** 2026-03-09
**Status:** Ready for planning

<domain>
## Phase Boundary

PR authors see benchmark comparison results and regressions block merge. PRs receive a full benchmark comparison table (Job Summary + alert comments), a configurable alert threshold (default 150%), and a fail-on-regression gate. Dashboard and README are Phase 7 scope.

</domain>

<decisions>
## Implementation Decisions

### PR trigger strategy
- Add `pull_request` trigger (opened + synchronize) to existing `benchmark.yml` — same file handles both main and PR flows
- Main pushes continue using `workflow_run` trigger (existing Phase 5 behavior)
- PR benchmarks run independently — do NOT wait for tests to pass
- Concurrency cancel per PR number: `concurrency: { group: 'benchmark-${{ github.event.pull_request.number }}', cancel-in-progress: true }`
- Use `if` conditions on `github.event_name` to distinguish main vs PR behavior at the step level

### Comment and comparison
- Use github-action-benchmark's built-in features — NO custom comparison script
- `summary-always: true` — full comparison table in GitHub Actions Job Summary (all benchmarks, current vs previous, ratio)
- `comment-on-alert: true` — commit comment with comparison table when regressions exceed threshold
- Compare against gh-pages baseline (action auto-fetches from gh-pages branch)
- PR runs set `auto-push: false` — do not pollute the gh-pages baseline with PR data

### Gate mechanism
- `fail-on-alert: true` — workflow step fails when regression exceeds threshold
- `alert-threshold: '150%'` — a benchmark 1.5x worse than baseline triggers failure (PR-02 default)
- Same threshold for alert and fail (no separate `fail-threshold`)
- Branch protection requiring benchmark check to pass is documented in workflow comments, not automated

### Benchmark scope on PRs
- Full benchmark suite — same as main: all backends, all groups, full 2x2 dataset matrix
- Same Docker services (MongoDB 7, Redis 7) as the existing benchmark job
- Python 3.13 only — consistent with main baseline for valid comparison

### Claude's Discretion
- Exact `if` condition expressions for main vs PR step differentiation
- How to structure the benchmark job to avoid duplicating steps (shared job with conditional steps vs separate jobs)
- Whether `alert-comment-cc-users` should mention anyone
- Workflow step ordering within the PR flow

</decisions>

<specifics>
## Specific Ideas

- "summary-always: true puts the full table in Job Summary" — discovered that github-action-benchmark's `buildComment()` renders a full comparison table with all benchmarks, not just alerts
- User wants the action's built-in features to handle PR-01 (comparison table) rather than custom scripting
- PR-02 specifies 150% default, matching the requirement exactly
- Branch protection is a manual repo setting — document it, don't automate it

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.github/workflows/benchmark.yml` — Phase 5 workflow with workflow_run trigger, Docker services, benchmark run step, and github-action-benchmark store step. PR logic extends this file.
- `tests/benchmarks/` — 5 benchmark test files with `@pytest.mark.benchmark` marker, shared fixtures, 2x2 dataset matrix

### Established Patterns
- `workflow_run` trigger chains after "Tests" workflow (Phase 5 decision)
- `benchmark-action/github-action-benchmark@v1` with `tool: "pytest"`, `gh-pages-branch: gh-pages`, `benchmark-data-dir-path: dev/bench`
- `uv sync --all-extras --dev` for package installation
- Docker services for MongoDB 7 and Redis 7 with health checks

### Integration Points
- `.github/workflows/benchmark.yml` — add `pull_request` trigger, concurrency group, conditional `auto-push`, alert/fail/summary options
- gh-pages branch at `/dev/bench/` — baseline data source for PR comparisons
- Branch protection settings — manual configuration after workflow is deployed

</code_context>

<deferred>
## Deferred Ideas

- Per-backend grouping in PR comparison tables (PR-04) — future requirement
- Visualization PNGs embedded in PR comments (PR-05) — future requirement
- Chart.js dashboard — Phase 7
- README live benchmark figures — Phase 7

</deferred>

---

*Phase: 06-pr-feedback*
*Context gathered: 2026-03-09*
