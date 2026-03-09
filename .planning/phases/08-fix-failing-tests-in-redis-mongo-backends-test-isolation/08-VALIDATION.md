---
phase: 8
slug: fix-failing-tests-in-redis-mongo-backends-test-isolation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-09
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/contract/ -k "mongodb or redis" -x` |
| **Full suite command** | `uv run pytest tests/contract/ -x` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/contract/ -k "mongodb or redis" -x`
- **After every plan wave:** Run `uv run pytest tests/contract/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | N/A | integration | `uv run pytest tests/contract/ -k mongodb -x` | Existing tests | ⬜ pending |
| 08-01-02 | 01 | 1 | N/A | integration | `uv run pytest tests/contract/ -k redis -x` | Existing tests | ⬜ pending |
| 08-01-03 | 01 | 1 | N/A | integration | `uv run pytest tests/contract/ -x` | Existing tests | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
