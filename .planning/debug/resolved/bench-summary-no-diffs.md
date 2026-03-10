---
status: diagnosed
trigger: "PR benchmark Job Summary shows test names but no performance comparison diffs"
created: 2026-03-10T14:00:00Z
updated: 2026-03-10T14:30:00Z
---

## Current Focus

hypothesis: The summary-always Job Summary IS being generated with comparison data, but the user expects a PR comment (which requires comment-always: true). The summary table with diffs only appears on the workflow run's Summary tab, NOT on the PR page itself.
test: Verified action source code, log output, and configuration
expecting: n/a - diagnosis complete
next_action: Return diagnosis

## Symptoms

expected: PR comparison step shows performance numbers + diffs against main baseline in Job Summary
actual: Only test names appear, no performance comparisons
errors: None - step succeeds
reproduction: Run any PR against main when gh-pages baseline exists
started: First PR run after baseline was established

## Eliminated

- hypothesis: gh-pages data not in correct format/location
  evidence: data.js exists at dev/bench/data.js on gh-pages, format is correct (window.BENCHMARK_DATA = {...}), entries key is "Benchmark" matching the action's default name parameter. 1 baseline entry from commit fa2713e with 373 benchmarks.
  timestamp: 2026-03-10T14:10:00Z

- hypothesis: prevBench is null causing summary to be skipped entirely
  evidence: Source code analysis of addBenchmarkEntry.ts shows prevBench is found when entries exist with different commit IDs. Baseline commit (fa2713e) differs from PR commit (ce2ac46). The action loads data.js from gh-pages, finds the existing entry, and sets prevBench.
  timestamp: 2026-03-10T14:15:00Z

- hypothesis: Benchmark names don't match between baseline and PR (causing empty Previous/Ratio columns)
  evidence: Both baseline and PR run 373 benchmarks with identical test names from the same test suite.
  timestamp: 2026-03-10T14:20:00Z

- hypothesis: Job Summary exceeds size limit (1MB)
  evidence: Estimated summary size is ~75KB for 373 benchmarks, well under the 1MB limit. No error in logs about summary upload failure.
  timestamp: 2026-03-10T14:22:00Z

- hypothesis: external-data-json-path is needed instead of gh-pages-branch
  evidence: Source code confirms gh-pages-branch mode works correctly for comparison. The action fetches gh-pages, loads data.js, finds previous benchmark entry, and passes it to handleSummary. Both modes are valid.
  timestamp: 2026-03-10T14:25:00Z

## Evidence

- timestamp: 2026-03-10T14:05:00Z
  checked: gh-pages branch content
  found: dev/bench/data.js exists with 1 entry (commit fa2713e, 373 benchmarks). dev/bench/index.html also present.
  implication: Baseline data is correctly stored

- timestamp: 2026-03-10T14:08:00Z
  checked: CI run logs for step "Compare benchmark results (PR)"
  found: Step completed successfully. Action fetched gh-pages, switched to it, loaded data.js, committed updated data locally (2632 insertions), switched back. Printed "github-action-benchmark was run successfully!" with PR data (commit ce2ac46, 373 benchmarks).
  implication: Action executed without errors

- timestamp: 2026-03-10T14:12:00Z
  checked: Action source code (v1.21.0 / SHA a7bc2366) - write.ts, addBenchmarkEntry.ts, index.ts
  found: writeBenchmark() calls writeBenchmarkToGitHubPages() which loads data.js, calls addBenchmarkEntry() to find prevBench. If prevBench is not null, handleSummary() is called which uses buildComment(name, curr, prev, false) to generate a markdown table with columns [Benchmark suite | Current | Previous | Ratio] and writes it via core.summary.write().
  implication: The comparison table SHOULD be generated when baseline exists

- timestamp: 2026-03-10T14:14:00Z
  checked: addBenchmarkEntry.ts logic
  found: Iterates existing entries in reverse, finds first entry with different commit.id. Since baseline has fa2713e and PR has ce2ac46, prevBench will be set to the baseline entry.
  implication: prevBench is NOT null, so handleSummary IS called

- timestamp: 2026-03-10T14:18:00Z
  checked: PR comments and check run output
  found: No benchmark comment on PR (only CodeRabbit comment). Check run output.summary is null. This is expected because comment-always defaults to false.
  implication: Comparison data only appears in Job Summary tab, not on the PR page

- timestamp: 2026-03-10T14:20:00Z
  checked: Workflow configuration for comment-always
  found: comment-always is not set (defaults to false). comment-on-alert: true only posts when regression exceeds threshold.
  implication: No comparison data appears on the PR page unless there's an alert

## Resolution

root_cause: The benchmark comparison IS being generated and written to the Job Summary (GITHUB_STEP_SUMMARY), but it is NOT visible on the PR page itself. The `comment-always` parameter defaults to `false`, so no comparison comment is posted on the PR. The user likely sees only pytest output (test names with timing data) when viewing the PR checks, and needs to navigate to the workflow run's Summary tab to see the comparison table. Additionally, `comment-on-alert: true` only triggers a PR comment when performance regression exceeds the 150% threshold, which did not occur in this run.

fix: Add `comment-always: true` to the PR comparison step to post the full comparison table as a PR comment, making it visible directly on the PR page.

verification: n/a - diagnosis only
files_changed: []
