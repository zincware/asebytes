---
phase: 5
slug: benchmark-pipeline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-09
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + pytest-benchmark >=5.2.1 |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `python -c "import yaml; yaml.safe_load(open('.github/workflows/benchmark.yml'))"` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~5 seconds (YAML lint), ~30 seconds (full suite) |

---

## Sampling Rate

- **After every task commit:** Run `python -c "import yaml; yaml.safe_load(open('.github/workflows/benchmark.yml'))"` to catch YAML syntax errors
- **After every plan wave:** Run `uv run pytest` to ensure no regressions
- **Before `/gsd:verify-work`:** Full suite must be green + push to main to observe workflow_run trigger
- **Max feedback latency:** 5 seconds (local lint), 120 seconds (full suite)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | CI-01 | manual-only | `gh api repos/{owner}/{repo}/pages` after first main push | N/A | ⬜ pending |
| 05-01-02 | 01 | 1 | CI-02 | manual-only | Check workflow run in Actions tab after merge | N/A | ⬜ pending |
| 05-01-03 | 01 | 1 | CI-03 | manual-only | Open test PR, verify no gh-pages push | N/A | ⬜ pending |
| 05-01-04 | 01 | 1 | CI-04 | manual-only | Verify documentation in workflow comments | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements.* Existing test infrastructure (pytest-benchmark tests, pyproject.toml config) covers all benchmark execution needs. No new test files needed; this phase is purely CI infrastructure.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| gh-pages branch exists with dashboard | CI-01 | GitHub infrastructure, not local testable | After first main push, verify `gh api repos/{owner}/{repo}/pages` returns 200 |
| Benchmark job runs on main push | CI-02 | Workflow trigger behavior | Push commit to main, check Actions tab for benchmark workflow run |
| No gh-pages push on PRs | CI-03 | Workflow trigger filtering | Open test PR, verify no gh-pages commit appears |
| Release benchmarks documented as skipped | CI-04 | User decision, documentation only | Verify workflow YAML has comment explaining decision |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
