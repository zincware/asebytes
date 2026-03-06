---
phase: 3
slug: contract-test-suite
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-06
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=8.4.2 + anyio >=4.0 |
| **Config file** | pyproject.toml [tool.pytest.ini_options] |
| **Quick run command** | `uv run pytest tests/contract/ -x --timeout=60` |
| **Full suite command** | `uv run pytest tests/contract/ -v` |
| **Estimated runtime** | ~30 seconds (excluding MongoDB/Redis/HF) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/contract/ -x --timeout=60`
- **After every plan wave:** Run `uv run pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-T1 | 01 | 1 | TEST-01, TEST-08, TEST-09 | integration | `uv run pytest tests/contract/ --collect-only` | tests/contract/conftest.py | pending |
| 03-01-T2 | 01 | 1 | TEST-01, TEST-02, TEST-06 | integration | `uv run pytest tests/contract/test_blob_contract.py tests/contract/test_object_contract.py tests/contract/test_ase_contract.py -x -m "not mongodb and not redis"` | tests/contract/test_*_contract.py | pending |
| 03-02-T1 | 02 | 2 | TEST-03, QUAL-06 | integration | `uv run pytest tests/contract/test_async_*.py -x -m "not mongodb and not redis"` | tests/contract/test_async_*_contract.py | pending |
| 03-02-T2 | 02 | 2 | TEST-04 | integration | `uv run pytest tests/contract/test_h5md_compliance.py -x` | tests/contract/test_h5md_compliance.py | pending |
| 03-03-T1 | 03 | 3 | TEST-01, TEST-09 | integration | `uv run pytest tests/ -x -m "not mongodb and not redis and not benchmark and not hf"` | tests/ (cleaned) | pending |
| 03-04-T1 | 04 | 2 | TEST-01, TEST-02, TEST-06 | integration | `uv run pytest tests/contract/test_readonly_contract.py -x -m "not hf"` | tests/contract/test_readonly_contract.py | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/contract/__init__.py` — package init
- [ ] `tests/contract/conftest.py` — backend parametrization fixtures
- [ ] `docker-compose.yml` — MongoDB + Redis services
- [ ] `pyproject.toml` marker registration — mongodb, redis, hf, capability marks

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| No auth-wall test data | TEST-06 | Requires reviewing fixture sources | Verify all fixtures are synthetic (s22, ethanol, molify-generated) |
| Consistent @pytest.mark.anyio | QUAL-06 | Requires grep verification | `grep -r "async def test_" tests/contract/ \| grep -v anyio` should return nothing |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
