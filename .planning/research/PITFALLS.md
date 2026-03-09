# Domain Pitfalls

**Domain:** CI benchmark infrastructure -- PR comments, committed results, GitHub Pages dashboard
**Researched:** 2026-03-09

## Critical Pitfalls

Mistakes that cause broken CI, security vulnerabilities, or unusable benchmark tracking.

### Pitfall 1: Fork PRs Cannot Write PR Comments (GITHUB_TOKEN Scoping)

**What goes wrong:** The workflow uses `pull_request` trigger with `github-action-benchmark`'s `comment-on-alert` or a custom step that posts PR comments. This works for PRs from branches in the same repo. But for fork PRs, `GITHUB_TOKEN` is scoped to read-only -- the comment step fails silently or with a 403 error. Contributors from forks never see benchmark feedback.

**Why it happens:** GitHub restricts `GITHUB_TOKEN` permissions on `pull_request` events from forks to prevent untrusted code from modifying the target repository. This is a deliberate security boundary. The `pull_request_target` trigger has write access but runs the workflow from the base branch, not the PR branch -- so naively switching triggers means benchmarks run against the wrong code.

**Consequences:** Either fork contributors get no benchmark feedback (bad DX), or the team uses `pull_request_target` with `actions/checkout` of the PR head, which is a [known security vulnerability](https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/) ("pwn request") that lets malicious PRs exfiltrate secrets and push to the repo.

**Prevention:**
- Use a two-workflow pattern: (1) `pull_request` runs benchmarks and uploads results as an artifact, (2) a separate `workflow_run` workflow triggered on completion of (1) downloads the artifact and posts the comment. The `workflow_run` trigger runs in the base repo context with write permissions, but never checks out or executes fork code.
- Never use `pull_request_target` with `actions/checkout@v4` pointing at the PR head ref. As of December 2025, GitHub enforces that `pull_request_target` always uses the default branch's workflow file, but the checkout of untrusted code remains dangerous.
- For a simpler approach: accept that fork PRs do not get inline comments. Post benchmark results only on push to main and on same-repo PRs. Document this limitation in CONTRIBUTING.md.

**Detection:** A fork contributor opens a PR and the benchmark comment step shows "Resource not accessible by integration" in the Actions log.

**Phase:** PR comment phase. Design the workflow trigger strategy before implementing comment logic.

---

### Pitfall 2: CI Runner Variance Causes False Regressions

**What goes wrong:** GitHub Actions shared runners have variable CPU performance. The same benchmark shows 15-40% variance between runs because the runner gets a different physical host each time. A PR that changes zero benchmark-relevant code gets flagged as a "30% regression" and the team starts ignoring benchmark alerts entirely.

**Why it happens:** GitHub shared runners (`ubuntu-latest`) run on Azure VMs with heterogeneous hardware. You control the OS and architecture but not the CPU model or neighbor workload. Even pinning the runner image does not guarantee consistent CPU. The asebytes benchmarks include I/O-heavy operations (HDF5, Zarr, LMDB reads/writes) which are additionally sensitive to disk cache state and I/O scheduling.

**Consequences:** Alert fatigue. The team sets `alert-threshold` to 300% to suppress noise, which means real 2x regressions go undetected. Alternatively, the team sets `fail-on-alert: true` with a tight threshold and PRs fail randomly.

**Prevention:**
- Set `alert-threshold` to `200%` (the default) and `fail-on-alert: false`. Use comments as informational, not blocking. Only block on extreme regressions (>3x).
- Run benchmarks only on `push` to main (not on every PR). Compare consecutive main commits rather than PR vs. base. This gives a stable baseline from the same workflow.
- For PR feedback: run benchmarks on the PR but compare against a rolling window (last 5 main commits) rather than a single baseline. github-action-benchmark does not support this natively -- you would need to compute the comparison yourself from the stored JSON.
- Long-term: evaluate [pytest-codspeed](https://codspeed.io) which uses CPU instruction simulation for <1% variance. However, codspeed's instrumentation mode does not measure I/O, which is the primary bottleneck in asebytes. The walltime mode on shared runners is no better than pytest-benchmark.
- Accept variance as inherent. The benchmark dashboard's value is trend detection over many data points, not individual PR pass/fail.

**Detection:** The benchmark dashboard shows sawtooth patterns on unchanged code. The stddev in pytest-benchmark JSON exceeds 20% of the mean.

**Phase:** All phases. Set expectations early that CI benchmarks are trend indicators, not precise measurements.

---

### Pitfall 3: gh-pages Push Race Condition on Concurrent Merges

**What goes wrong:** Two PRs merge to main in quick succession. Both trigger the benchmark workflow. Both fetch `gh-pages`, append their results to `data.js`, and try to push. The second push fails with "non-fast-forward" because `gh-pages` was updated by the first push.

**Why it happens:** github-action-benchmark's `auto-push: true` does a `git pull --rebase` and retries on failure, but this retry logic has a window where it can still fail if another push lands during the rebase. With a Python matrix build (3 Python versions), you get 3 concurrent attempts to push to `gh-pages` per merge -- 6 total for two concurrent merges.

**Consequences:** Benchmark data for some commits is silently lost. The dashboard has gaps. The CI run shows a red X for a reason unrelated to code quality, confusing contributors.

**Prevention:**
- Run benchmarks on only one Python version (e.g., 3.12) to reduce concurrent push contention. The benchmark results across Python versions are not meaningfully different for I/O-bound operations.
- Use `concurrency` groups in the workflow to serialize benchmark pushes: `concurrency: { group: benchmark-deploy, cancel-in-progress: false }`. This queues pushes instead of racing them.
- Alternatively, do not use `auto-push`. Instead, upload benchmark JSON as an artifact and have a separate `workflow_run` job that downloads artifacts and pushes to `gh-pages` serially.
- If using `auto-push`, the built-in retry with rebase handles most cases. Add `max-items-in-chart: 50` to limit the data.js size so rebases are fast.

**Detection:** Workflow run fails at the "Push benchmark result" step with `! [rejected] ... (non-fast-forward)` even after retry.

**Phase:** GitHub Pages deployment phase. Choose the push strategy before implementing.

---

### Pitfall 4: Benchmark JSON Committed to Main Causes Merge Conflicts

**What goes wrong:** The plan (BENCH-02) is to commit benchmark JSON to the repo, overwritten per merge/tag. If the benchmark result file is on the `main` branch (not `gh-pages`), every merge to main modifies the same file. Two PRs based on the same commit will conflict on the benchmark JSON file when the second one tries to merge.

**Why it happens:** JSON benchmark results are not mergeable -- they are overwritten wholesale. Git cannot auto-merge two different versions of `benchmark_results.json`. This is the same problem as committing lock files or build artifacts to main.

**Consequences:** Contributors must rebase/merge main before their PR can merge, even when their changes have nothing to do with benchmarks. This creates friction proportional to merge frequency.

**Prevention:**
- Do not commit benchmark JSON to `main`. Store it on `gh-pages` branch (where github-action-benchmark puts it by default) or as a GitHub Actions artifact.
- If benchmark results must be in the repo for historical tracking: use a dedicated `benchmarks` branch (not `main`). Or commit to a path that is `.gitignore`'d on main and only written on `gh-pages`.
- For release-tagged benchmarks: use a GitHub Release asset instead of a committed file. `gh release upload v1.0 benchmark_results.json` keeps results associated with the tag without touching any branch.
- If you must commit to main: use a bot commit that runs after merge (via `push` trigger), so there is never a PR that modifies the benchmark file. The file is always overwritten by CI, never by humans.

**Detection:** PR merge blocked by "conflicts in benchmark_results.json" when the contributor changed only source code.

**Phase:** Benchmark storage phase. Decide storage location before implementing.

## Moderate Pitfalls

### Pitfall 5: GitHub Pages Not Enabled or Misconfigured

**What goes wrong:** The workflow pushes benchmark data to `gh-pages` branch, but GitHub Pages is not configured in the repository settings (Settings > Pages > Source). Or Pages is configured to serve from `main/docs` instead of `gh-pages`. The dashboard URL returns 404.

**Why it happens:** GitHub Pages configuration is a manual step in repo settings, separate from the workflow file. It is easy to set up the workflow, see green CI, and forget that the Pages source branch must be configured. Additionally, GitHub organization settings may restrict Pages to public repos only, or require admin approval.

**Prevention:**
- Document the one-time setup: create orphan `gh-pages` branch, configure Pages source in repo settings.
- Add a smoke test in the workflow: after pushing to `gh-pages`, curl the expected dashboard URL and check for 200 status. If 404, log a warning with setup instructions.
- Use `actions/deploy-pages@v4` with the newer Pages deployment API instead of branch-based deployment. This is more explicit and fails loudly if Pages is not configured.
- Verify that the repo's visibility (public/private) supports Pages. Private repos require GitHub Pro/Team/Enterprise for Pages.

**Detection:** CI is green but `https://username.github.io/asebytes/dev/bench/` returns 404.

**Phase:** GitHub Pages deployment phase. Verify Pages configuration as step 1.

---

### Pitfall 6: Benchmark Data Grows Unbounded on gh-pages

**What goes wrong:** Every push to main appends a new entry to `data.js` on `gh-pages`. After hundreds of merges, `data.js` is several MB. The GitHub Pages dashboard loads slowly. The `gh-pages` branch history accumulates thousands of commits from the benchmark bot, cluttering git log and increasing clone size.

**Why it happens:** github-action-benchmark appends by default. The `max-items-in-chart` option limits what is displayed but the data may still accumulate in the file depending on version. The git history on `gh-pages` is never squashed.

**Consequences:** Dashboard page load time degrades. `git clone` downloads all of `gh-pages` history (unless `--single-branch`). Repository size grows linearly with merge frequency.

**Prevention:**
- Set `max-items-in-chart: 50` (or similar) to limit stored data points per benchmark. This keeps `data.js` bounded.
- Periodically force-push `gh-pages` to squash history: `git checkout gh-pages && git reset --soft $(git rev-list --max-parents=0 HEAD) && git commit -m "squash" && git push -f`. Run this quarterly or when the branch exceeds a size threshold.
- Consider storing historical data externally (GitHub Release assets for tagged versions) rather than keeping every commit's results.

**Detection:** `data.js` exceeds 1 MB. Dashboard takes >3 seconds to load. `gh-pages` branch has >500 commits.

**Phase:** GitHub Pages deployment phase. Configure `max-items-in-chart` from the start.

---

### Pitfall 7: Benchmark Workflow Runs Expensive Services Unnecessarily

**What goes wrong:** The current `tests.yml` starts MongoDB and Redis service containers for every run. If the benchmark workflow reuses this workflow or is added as a step in it, every benchmark run pays the ~30-second startup cost for MongoDB and Redis containers, even if benchmarks only test local backends (HDF5, Zarr, LMDB).

**Why it happens:** The existing workflow was designed for the full test suite. Adding benchmarks as an extra step in the same job is the path of least resistance. But benchmark runs should be fast and focused.

**Consequences:** CI time increases. Resource waste. If MongoDB/Redis service containers flake (health check timeout), the benchmark step never runs.

**Prevention:**
- Create a separate workflow file for benchmarks (`benchmarks.yml`) that does not start MongoDB/Redis service containers.
- Only run file-based backend benchmarks (HDF5, Zarr, LMDB) in CI. These are the ones where performance tracking matters most. MongoDB and Redis performance depends on network and container overhead, not on asebytes code changes.
- If network backend benchmarks are needed: run them in a separate job that starts the services, keeping the file-based benchmark job fast.

**Detection:** Benchmark CI job takes >5 minutes when benchmarks themselves complete in <60 seconds. Time is spent in service startup.

**Phase:** Workflow setup phase. Separate benchmark workflow from test workflow.

---

### Pitfall 8: pytest-benchmark `--benchmark-only` Skips Test Assertions

**What goes wrong:** Running `pytest -m benchmark --benchmark-only` skips non-benchmark tests (correct) but also skips any assertions inside benchmark test functions that are outside the `benchmark()` call. If a benchmark test includes correctness checks after the timed section, those checks are skipped in `--benchmark-only` mode.

**Why it happens:** `--benchmark-only` is designed to run only the timed portion. But developers sometimes add assertions in benchmark tests as sanity checks (e.g., "verify the read returned the correct number of frames"). These assertions provide no signal in `--benchmark-only` mode.

**Prevention:**
- Keep benchmark tests pure: they measure performance only, with no correctness assertions. Correctness belongs in the contract test suite.
- If a benchmark must verify its result (e.g., to prevent the optimizer from eliminating dead code), put the assertion inside the `benchmark.pedantic()` call's function, not after it.
- Review existing benchmark tests in `tests/benchmarks/` to verify they follow this pattern.

**Detection:** A benchmark test passes in `--benchmark-only` mode but fails when run normally (without `--benchmark-only`), revealing that the assertion was being skipped.

**Phase:** Benchmark suite review phase. Audit existing benchmarks before adding CI integration.

---

### Pitfall 9: GITHUB_TOKEN Cannot Trigger Downstream Workflows

**What goes wrong:** The benchmark workflow pushes to `gh-pages` using `GITHUB_TOKEN`. This push does not trigger the GitHub Pages deployment workflow because pushes made with `GITHUB_TOKEN` do not trigger new workflow runs (to prevent infinite loops).

**Why it happens:** GitHub's deliberate design to prevent recursive workflow triggers. If workflow A pushes a commit, and that commit would trigger workflow B, it only triggers B if the push was made with a personal access token (PAT) or a GitHub App token, not with `GITHUB_TOKEN`.

**Consequences:** Benchmark data is pushed to `gh-pages` but the Pages site is not rebuilt. The dashboard shows stale data until the next unrelated event triggers a rebuild.

**Prevention:**
- Use `actions/deploy-pages@v4` directly in the benchmark workflow instead of relying on the automatic Pages build triggered by push. This deploys explicitly.
- Or use a fine-grained PAT with `contents: write` scope stored as a repository secret. This is the approach github-action-benchmark recommends for `auto-push`.
- Or configure GitHub Pages to build from the `gh-pages` branch via Settings (not via Actions). Branch-based Pages deploys do not require a workflow trigger -- GitHub rebuilds automatically on any push to the configured branch, regardless of token type. Verify this is the configuration used.

**Detection:** `gh-pages` branch has new commits but the Pages site shows old content. Manual "Run workflow" on the Pages deployment fixes it.

**Phase:** GitHub Pages deployment phase. Verify the Pages deployment mechanism.

## Minor Pitfalls

### Pitfall 10: Benchmark Names Change Silently, Breaking Historical Comparison

**What goes wrong:** pytest-benchmark generates benchmark names from the test function name and parametrize IDs (e.g., `test_read[bench_h5md-ethanol_100]`). Renaming a fixture, reordering parameters, or changing the parametrize ID string creates a new benchmark name. github-action-benchmark treats this as a new benchmark with no history, and the old benchmark stops receiving updates.

**Prevention:**
- Use `benchmark.name` or `benchmark.extra_info` to set stable benchmark identifiers that do not depend on fixture names.
- Before renaming any benchmark fixture or parameter, check whether it will change benchmark names in the JSON output. Run locally with `--benchmark-json=test.json` and compare names.
- Document the naming convention so future contributors know that renaming breaks history.

**Phase:** Benchmark suite review phase.

---

### Pitfall 11: Benchmark Visualize Script Breaks on Schema Changes

**What goes wrong:** The current workflow runs `uv run docs/visualize_benchmarks.py benchmark_results.json` to generate PNG plots. If the benchmark JSON schema changes (new fields, renamed benchmarks, different parametrize structure), this script crashes and the `if: always()` guard means it fails silently with a non-zero exit buried in the logs.

**Prevention:**
- Make the visualize script robust to missing/extra fields. Use `.get()` with defaults instead of direct key access.
- If switching to github-action-benchmark's built-in dashboard, the custom visualize script becomes redundant for CI. Keep it as a local development tool only.
- Add a basic test for the visualize script that feeds it a minimal valid JSON.

**Phase:** Dashboard phase. Decide whether custom visualization is needed alongside the Pages dashboard.

---

### Pitfall 12: Multiple Python Versions Generate Conflicting Benchmark Names

**What goes wrong:** The current workflow runs benchmarks on Python 3.11, 3.12, and 3.13. If all three versions push results to the same benchmark namespace on `gh-pages`, the dashboard mixes results from different Python versions, making trends meaningless. Or worse, the three versions produce artifacts with different names that github-action-benchmark cannot correlate.

**Prevention:**
- Run benchmarks on a single Python version (3.12) for the dashboard. Performance differences between Python minor versions are real but orthogonal to code regression detection.
- If multi-version tracking is desired, use the `name` input of github-action-benchmark to create separate namespaces: `name: "Python ${{ matrix.python-version }}"`. This creates separate charts per version.
- Upload artifacts with version-specific names (already done: `benchmark-results-${{ matrix.python-version }}`).

**Phase:** Workflow setup phase. Decide single-version vs. multi-version tracking upfront.

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Workflow trigger design | Fork PRs cannot comment (#1) | Use two-workflow pattern (pull_request + workflow_run) or accept no fork comments |
| Workflow trigger design | GITHUB_TOKEN cannot trigger Pages rebuild (#9) | Use deploy-pages action or branch-based Pages config |
| Benchmark storage | JSON on main causes merge conflicts (#4) | Store on gh-pages or as release assets, never on main |
| Benchmark storage | Data grows unbounded (#6) | Set max-items-in-chart from day one |
| PR comments | False regressions from runner variance (#2) | Use fail-on-alert: false, track trends not individual runs |
| GitHub Pages deployment | Pages not configured (#5) | Document one-time setup, verify before implementing |
| GitHub Pages deployment | gh-pages push race condition (#3) | Use concurrency groups or single-version benchmarks |
| Benchmark suite | Names change silently (#10) | Establish naming convention before CI integration |
| Workflow structure | Unnecessary service containers (#7) | Separate benchmark workflow from test workflow |
| Multi-version matrix | Conflicting benchmark data (#12) | Single Python version for benchmarks or separate namespaces |

## Sources

- [GitHub Security Lab: Preventing pwn requests](https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/) -- definitive guide on pull_request_target security risks
- [github-action-benchmark repository](https://github.com/benchmark-action/github-action-benchmark) -- official docs, auto-push behavior, alert configuration
- [GitHub community: PR comment permissions](https://github.com/orgs/community/discussions/26644) -- GITHUB_TOKEN scoping for fork PRs
- [GitHub blog: pull_request_target changes (Nov 2025)](https://github.blog/changelog/2025-11-07-actions-pull_request_target-and-environment-branch-protections-changes/) -- recent security hardening
- [CodSpeed: Unrelated benchmark regression](https://codspeed.io/blog/unrelated-benchmark-regression) -- runner hardware variance causing false regressions
- [pytest-codspeed documentation](https://codspeed.io/docs/reference/pytest-codspeed) -- instrumentation vs. walltime modes
- [GitHub Actions Security Cheat Sheet](https://blog.gitguardian.com/github-actions-security-cheat-sheet/) -- comprehensive permissions guide
- [Continuous Benchmarks on a Budget](https://blog.martincostello.com/continuous-benchmarks-on-a-budget) -- practical gh-pages benchmark deployment patterns

---

*Pitfalls analysis: 2026-03-09 -- CI benchmark infrastructure milestone*
