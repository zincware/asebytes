---
status: diagnosed
phase: 06-pr-feedback
source: 06-01-SUMMARY.md
started: 2026-03-10T12:00:00Z
updated: 2026-03-10T12:01:00Z
---

## Current Test

[testing complete]

## Tests

### 1. PR Benchmark Comparison Table
expected: When a PR is opened, the Benchmarks workflow runs and the Job Summary shows a comparison table with performance diffs against the main branch baseline (not just test names).
result: issue
reported: "the summary only shows which tests were running but no diffs"
severity: major

### 2. Fail-on-Regression Gate
expected: If any benchmark regresses beyond 150% of baseline, the Benchmarks check fails and blocks the PR merge (requires branch protection enabled).
result: skipped
reason: not tested; not relevant

### 3. Concurrency Cancellation
expected: Pushing a new commit to a PR while benchmarks are running cancels the in-progress run and starts a new one.
result: pass

### 4. Main Branch Auto-Push
expected: When Tests workflow succeeds on main, benchmarks run and results are auto-pushed to gh-pages at /dev/bench/ — visible on the dashboard.
result: pass

## Summary

total: 4
passed: 2
issues: 1
pending: 0
skipped: 1

## Gaps

- truth: "PR Job Summary shows comparison table with performance diffs against main branch baseline"
  status: failed
  reason: "User reported: the summary only shows which tests were running but no diffs"
  severity: major
  test: 1
  root_cause: "The comparison table is written to GITHUB_STEP_SUMMARY (workflow run Summary tab) but NOT posted as a PR comment. comment-always defaults to false, and comment-on-alert only fires on regression. User expects diffs visible on the PR page itself."
  artifacts:
    - path: ".github/workflows/benchmark.yml"
      issue: "PR comparison step missing comment-always: true"
  missing:
    - "Add comment-always: true to PR benchmark step"
  debug_session: ".planning/debug/bench-summary-no-diffs.md"
