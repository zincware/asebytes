# Phase 6: PR Feedback - Research

**Researched:** 2026-03-09
**Domain:** GitHub Actions CI / github-action-benchmark PR integration
**Confidence:** HIGH

## Summary

Phase 6 extends the existing `benchmark.yml` workflow to provide PR authors with benchmark comparison feedback and a fail-on-regression gate. The implementation uses github-action-benchmark's built-in features: `summary-always` for Job Summary tables, `comment-on-alert` for commit comments on regressions, and `fail-on-alert` for the merge gate.

The key architectural decision is adding a `pull_request` trigger to the existing workflow file and using `if` conditions on `github.event_name` to differentiate main-push behavior (auto-push to gh-pages) from PR behavior (compare-only, no push). The action automatically fetches gh-pages branch data for comparison, so PR runs can compare against the main baseline without any custom scripting.

**Primary recommendation:** Add `pull_request` trigger to existing `benchmark.yml` with conditional `auto-push` and `save-data-file` based on event type. Enable `summary-always`, `comment-on-alert`, and `fail-on-alert` with `alert-threshold: '150%'`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Add `pull_request` trigger (opened + synchronize) to existing `benchmark.yml` -- same file handles both main and PR flows
- Main pushes continue using `workflow_run` trigger (existing Phase 5 behavior)
- PR benchmarks run independently -- do NOT wait for tests to pass
- Concurrency cancel per PR number: `concurrency: { group: 'benchmark-${{ github.event.pull_request.number }}', cancel-in-progress: true }`
- Use `if` conditions on `github.event_name` to distinguish main vs PR behavior at step level
- Use github-action-benchmark's built-in features -- NO custom comparison script
- `summary-always: true` -- full comparison table in Job Summary
- `comment-on-alert: true` -- commit comment with comparison table when regressions exceed threshold
- Compare against gh-pages baseline (action auto-fetches from gh-pages branch)
- PR runs set `auto-push: false` -- do not pollute gh-pages baseline with PR data
- `fail-on-alert: true` -- workflow step fails when regression exceeds threshold
- `alert-threshold: '150%'` -- benchmark 1.5x worse than baseline triggers failure
- Same threshold for alert and fail (no separate `fail-threshold`)
- Branch protection is documented in workflow comments, not automated
- Full benchmark suite -- same as main: all backends, all groups, full 2x2 dataset matrix
- Same Docker services (MongoDB 7, Redis 7)
- Python 3.13 only

### Claude's Discretion
- Exact `if` condition expressions for main vs PR step differentiation
- How to structure the benchmark job to avoid duplicating steps (shared job with conditional steps vs separate jobs)
- Whether `alert-comment-cc-users` should mention anyone
- Workflow step ordering within the PR flow

### Deferred Ideas (OUT OF SCOPE)
- Per-backend grouping in PR comparison tables (PR-04) -- future requirement
- Visualization PNGs embedded in PR comments (PR-05) -- future requirement
- Chart.js dashboard -- Phase 7
- README live benchmark figures -- Phase 7
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PR-01 | PRs receive a full benchmark comparison summary (tables with deltas for all benchmarks) vs main -- showing both regressions and improvements | `summary-always: true` renders a full comparison table in GitHub Actions Job Summary; `comment-on-alert: true` posts commit comments on regressions |
| PR-02 | Alert threshold is configurable (starting at 150%) | `alert-threshold` input accepts percentage string (e.g., '150%'); visible in workflow YAML for easy editing |
| PR-03 | Fail-on-regression gate blocks PR merge on benchmark regression | `fail-on-alert: true` causes step failure when threshold exceeded; combined with branch protection rules requiring the check to pass |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| benchmark-action/github-action-benchmark | v1 | Benchmark comparison, alerting, Job Summary | Already used in Phase 5; has built-in PR comparison features |

### Supporting
| Tool | Purpose | When to Use |
|------|---------|-------------|
| GitHub Actions `concurrency` | Cancel in-progress PR benchmark runs | Every PR push to avoid wasted compute |
| GitHub Branch Protection | Require benchmark check to pass before merge | Manual repo configuration after workflow is deployed |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Built-in action features | Custom comparison script | More control over table formatting, but violates user's locked decision to use built-in features |
| Commit comments (`comment-on-alert`) | `actions/github-script` for PR comments | PR comments are more discoverable, but adds complexity; Job Summary covers the primary table need |

## Architecture Patterns

### Recommended: Single Workflow, Conditional Steps

The existing `benchmark.yml` should remain a single file with both triggers. Use `if` conditions at the step level to differentiate behavior.

**Structure:**
```yaml
on:
  workflow_run:
    workflows: ["Tests"]
    types: [completed]
    branches: [main]
  pull_request:
    types: [opened, synchronize]

concurrency:
  group: benchmark-${{ github.event.pull_request.number || github.sha }}
  cancel-in-progress: true
```

**Key pattern:** The `benchmark` job's `if` condition must handle both triggers:
- For `workflow_run`: `github.event.workflow_run.conclusion == 'success'`
- For `pull_request`: always run (no precondition)

Combined: `if: github.event_name == 'pull_request' || github.event.workflow_run.conclusion == 'success'`

### Conditional Step Pattern for github-action-benchmark

The action step needs different inputs for main vs PR:

```yaml
- name: Store benchmark results (main)
  if: github.event_name == 'workflow_run'
  uses: benchmark-action/github-action-benchmark@v1
  with:
    tool: "pytest"
    output-file-path: benchmark_results.json
    gh-pages-branch: gh-pages
    benchmark-data-dir-path: dev/bench
    github-token: ${{ secrets.GITHUB_TOKEN }}
    auto-push: true

- name: Compare benchmark results (PR)
  if: github.event_name == 'pull_request'
  uses: benchmark-action/github-action-benchmark@v1
  with:
    tool: "pytest"
    output-file-path: benchmark_results.json
    gh-pages-branch: gh-pages
    benchmark-data-dir-path: dev/bench
    github-token: ${{ secrets.GITHUB_TOKEN }}
    auto-push: false
    save-data-file: false
    summary-always: true
    comment-on-alert: true
    fail-on-alert: true
    alert-threshold: "150%"
```

**Why two steps instead of conditional inputs:** GitHub Actions does not support `if` on individual `with` inputs. You cannot conditionally set `auto-push` within a single step. Two steps with `if` conditions is the standard pattern.

### Anti-Patterns to Avoid
- **Two separate workflow files for main and PR:** Duplicates all service definitions, checkout steps, and benchmark run commands. Use one file with conditional steps instead.
- **Running benchmarks on PR only after tests pass:** The CONTEXT.md explicitly says PR benchmarks run independently. Do NOT add a `workflow_run` dependency for PRs.
- **Using `save-data-file: true` on PRs:** This would modify the gh-pages data file in the local checkout, polluting the comparison baseline if accidentally pushed.
- **Setting `auto-push: true` on PRs:** Would allow PR authors to modify gh-pages benchmark history.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Benchmark comparison tables | Custom diff script parsing JSON | `summary-always: true` | Action already builds comparison tables with ratios and deltas |
| Regression detection | Threshold comparison logic | `alert-threshold` + `fail-on-alert` | Action handles the math, edge cases (first run, missing data) |
| PR commenting | `actions/github-script` with custom comment body | `comment-on-alert: true` | Action formats the alert comment with benchmark details |
| Concurrency cancellation | Manual job deduplication | GitHub Actions `concurrency` group | Built-in, reliable, handles edge cases |

**Key insight:** The entire phase can be implemented by configuring the existing action differently for PR context. No custom scripting is needed.

## Common Pitfalls

### Pitfall 1: Concurrency Group for Mixed Triggers
**What goes wrong:** Using `github.event.pull_request.number` in concurrency group fails for `workflow_run` events (undefined).
**Why it happens:** The concurrency group expression is evaluated for ALL triggers, not just `pull_request`.
**How to avoid:** Use fallback expression: `benchmark-${{ github.event.pull_request.number || github.sha }}`
**Warning signs:** Workflow fails to start with expression evaluation error.

### Pitfall 2: Job-Level `if` Condition Conflict
**What goes wrong:** The existing `if: github.event.workflow_run.conclusion == 'success'` blocks PR runs because `workflow_run` context is undefined for `pull_request` events.
**Why it happens:** The condition only accounts for the `workflow_run` trigger.
**How to avoid:** Update to: `if: github.event_name == 'pull_request' || github.event.workflow_run.conclusion == 'success'`
**Warning signs:** PR benchmark jobs show as "skipped" in GitHub Actions.

### Pitfall 3: Permissions for PR Commit Comments
**What goes wrong:** `comment-on-alert` fails silently or errors because token lacks permission.
**Why it happens:** Commit comments require `contents: read` permission at minimum. The workflow already has `contents: write` which is sufficient.
**How to avoid:** Keep existing `permissions: contents: write` -- it covers both main push and PR comment needs. For PRs from same-repo branches, `GITHUB_TOKEN` retains configured permissions.
**Warning signs:** Regression detected but no commit comment appears.

### Pitfall 4: No Baseline Data on First PR Run
**What goes wrong:** The first PR run has nothing to compare against if gh-pages has no data yet.
**Why it happens:** Phase 5 must have run at least once on main to populate gh-pages with baseline data.
**How to avoid:** Phase 5 is a dependency -- ensure main has pushed at least one benchmark result before testing PR flow.
**Warning signs:** Action logs show "No previous benchmark data found" or comparison table is empty.

### Pitfall 5: Fork PR Token Restrictions
**What goes wrong:** Fork PRs cannot post commit comments because `GITHUB_TOKEN` is read-only for forks.
**Why it happens:** GitHub security restriction -- fork PRs get reduced token permissions.
**How to avoid:** This is explicitly out of scope per REQUIREMENTS.md ("Fork PR benchmark comments" is out of scope). No action needed.
**Warning signs:** N/A -- documented limitation.

### Pitfall 6: `save-data-file` Default
**What goes wrong:** PR runs with default `save-data-file: true` modify the local data.js file, which could confuse subsequent steps.
**Why it happens:** The action defaults to saving data, which is intended for main pushes.
**How to avoid:** Set `save-data-file: false` on the PR step to avoid any side effects.
**Warning signs:** Unexpected file modifications in checkout directory.

## Code Examples

### Complete PR Benchmark Step
```yaml
# Source: github-action-benchmark action.yml + action's own CI workflow
- name: Compare benchmark results (PR)
  if: github.event_name == 'pull_request'
  uses: benchmark-action/github-action-benchmark@v1
  with:
    tool: "pytest"
    output-file-path: benchmark_results.json
    gh-pages-branch: gh-pages
    benchmark-data-dir-path: dev/bench
    github-token: ${{ secrets.GITHUB_TOKEN }}
    auto-push: false
    save-data-file: false
    summary-always: true
    comment-on-alert: true
    fail-on-alert: true
    alert-threshold: "150%"
```

### Concurrency Group Pattern
```yaml
# Source: GitHub Actions docs
concurrency:
  group: benchmark-${{ github.event.pull_request.number || github.sha }}
  cancel-in-progress: true
```

### Combined Job Condition
```yaml
# Source: GitHub Actions conditional patterns
jobs:
  benchmark:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request' || github.event.workflow_run.conclusion == 'success'
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Custom comparison scripts | `summary-always` Job Summary | github-action-benchmark recent versions | No custom scripting needed for comparison tables |
| Separate PR benchmark workflows | Single workflow with conditional steps | GitHub Actions `if` conditions | Less duplication, easier maintenance |
| `workflow_run` + `pull_request` in separate files | Combined triggers in one file | Standard practice | Single source of truth for benchmark configuration |

## Open Questions

1. **`comment-on-alert` creates commit comments, not PR comments**
   - What we know: The action uses GitHub's commit comment API, not the PR comment API. Commit comments appear on the "Commits" tab of a PR, not in the PR conversation.
   - What's unclear: Whether this satisfies the user's expectation for "PR comment" visibility. However, `summary-always` Job Summary is the primary comparison table mechanism (PR-01), and commit comments are supplementary alerts.
   - Recommendation: Accept commit comments as sufficient since `summary-always` Job Summary is the main feedback mechanism. The Job Summary appears directly in the PR's "Checks" tab.

2. **`alert-comment-cc-users` configuration**
   - What we know: Accepts comma-separated GitHub usernames prefixed with `@`.
   - What's unclear: Whether the project has specific maintainers to mention.
   - Recommendation: Leave empty initially. Can be added later without workflow changes.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | GitHub Actions workflow (YAML validation + live PR test) |
| Config file | `.github/workflows/benchmark.yml` |
| Quick run command | `yamllint .github/workflows/benchmark.yml` or `actionlint .github/workflows/benchmark.yml` |
| Full suite command | Open a test PR with a known benchmark regression |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PR-01 | PR receives full benchmark comparison table in Job Summary | manual | Open PR, check Actions tab Job Summary | N/A |
| PR-02 | Alert threshold is configurable at 150% | manual | Verify `alert-threshold: "150%"` in YAML | N/A |
| PR-03 | Regression beyond threshold fails the workflow | manual | Open PR with intentionally slow benchmark, verify red check | N/A |

### Sampling Rate
- **Per task commit:** YAML lint validation
- **Per wave merge:** N/A (single-plan phase)
- **Phase gate:** Open a real PR to verify comparison table renders and fail-on-alert works

### Wave 0 Gaps
None -- this phase modifies an existing workflow YAML file. No test infrastructure is needed beyond manual PR verification.

## Sources

### Primary (HIGH confidence)
- [benchmark-action/github-action-benchmark action.yml](https://github.com/benchmark-action/github-action-benchmark/blob/master/action.yml) - All input definitions, defaults, descriptions
- [github-action-benchmark CI workflow](https://github.com/benchmark-action/github-action-benchmark/blob/master/.github/workflows/ci.yml) - Action's own usage pattern with `fail-on-alert`, `summary-always`, `comment-on-alert`
- Existing `.github/workflows/benchmark.yml` in project -- Phase 5 baseline

### Secondary (MEDIUM confidence)
- [GitHub Actions permissions docs](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/controlling-permissions-for-github_token) - GITHUB_TOKEN permission model for PRs
- [GitHub Actions events docs](https://docs.github.com/actions/using-workflows/events-that-trigger-workflows) - `pull_request` trigger types and behavior

### Tertiary (LOW confidence)
- [werat.dev blog on PR benchmarks](https://werat.dev/blog/running-benchmarks-for-pull-requests-via-github-actions/) - Confirms action's warning about PR usage with auto-push; validates our `auto-push: false` approach

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using same action as Phase 5, inputs verified from action.yml
- Architecture: HIGH - Conditional step pattern is standard GitHub Actions practice, verified from action's own CI
- Pitfalls: HIGH - Identified from action docs, GitHub Actions docs, and practical experience with mixed triggers

**Research date:** 2026-03-09
**Valid until:** 2026-04-09 (stable -- github-action-benchmark v1 is mature)
