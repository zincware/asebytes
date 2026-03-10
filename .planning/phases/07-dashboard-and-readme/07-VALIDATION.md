---
phase: 7
slug: dashboard-and-readme
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-10
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual verification + grep smoke checks (docs/CI config phase) |
| **Config file** | N/A |
| **Quick run command** | `grep 'max-items-in-chart' .github/workflows/benchmark.yml` |
| **Full suite command** | Manual: visit `https://zincware.github.io/asebytes/` and verify dashboard loads |
| **Estimated runtime** | ~5 seconds (grep checks) |

---

## Sampling Rate

- **After every task commit:** Run grep-based smoke checks on modified files
- **After every plan wave:** N/A (single wave expected)
- **Before `/gsd:verify-work`:** Full manual verification of GitHub Pages URL after gh-pages push
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | DASH-03 | smoke | `grep 'max-items-in-chart' .github/workflows/benchmark.yml` | N/A | ⬜ pending |
| 07-01-02 | 01 | 1 | DASH-01 | manual-only | Visit `https://zincware.github.io/asebytes/` | N/A | ⬜ pending |
| 07-01-03 | 01 | 1 | DASH-02 | smoke | `grep -c '\.png' README.md` (Benchmarks section should be 0) | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements. No test infrastructure needed — this phase is documentation and configuration only.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| GitHub Pages serves dashboard at root URL | DASH-01 | Requires browser/network access to verify live site | Visit `https://zincware.github.io/asebytes/`, confirm Chart.js dashboard loads with project description, usage, and links |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
