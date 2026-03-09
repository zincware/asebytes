---
phase: 6
slug: pr-feedback
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-09
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | GitHub Actions workflow (YAML validation + live PR test) |
| **Config file** | `.github/workflows/benchmark.yml` |
| **Quick run command** | `yamllint .github/workflows/benchmark.yml` |
| **Full suite command** | Open a test PR with a known benchmark regression |
| **Estimated runtime** | ~5 seconds (YAML lint); ~10 minutes (live PR test) |

---

## Sampling Rate

- **After every task commit:** Run `yamllint .github/workflows/benchmark.yml`
- **After every plan wave:** N/A (single-plan phase)
- **Before `/gsd:verify-work`:** Open a real PR to verify comparison table renders and fail-on-alert works
- **Max feedback latency:** 5 seconds (YAML lint)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | PR-01 | manual | Verify Job Summary table on test PR | N/A | ⬜ pending |
| 06-01-02 | 01 | 1 | PR-02 | manual | Verify `alert-threshold: "150%"` in YAML | N/A | ⬜ pending |
| 06-01-03 | 01 | 1 | PR-03 | manual | Open PR with slow benchmark, verify red check | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No test framework or stub files needed — this phase modifies an existing workflow YAML file.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| PR receives full benchmark comparison table in Job Summary | PR-01 | Requires actual GitHub Actions runner with gh-pages data | Open PR, navigate to Actions tab, check Job Summary |
| Alert threshold is configurable at 150% | PR-02 | Configuration verification in YAML | Read `alert-threshold` value in workflow file |
| Regression beyond threshold fails the workflow | PR-03 | Requires actual benchmark run with regression | Open PR with intentionally slow benchmark, verify status check fails |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
