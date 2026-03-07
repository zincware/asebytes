# Phase 3: Contract Test Suite - Research

**Researched:** 2026-03-06
**Domain:** Pytest parametrized contract testing across 9+ storage backends
**Confidence:** HIGH

## Summary

Phase 3 creates a unified parametrized contract test suite under `tests/contract/` that validates every backend through BlobIO, ObjectIO, and ASEIO facades. The existing codebase already has extensive per-backend tests (90+ test files), a rich fixture library in `conftest.py`, and established patterns for backend parametrization via `uni_blob_backend` / `uni_object_backend` fixtures that cover 3 backends each. The contract suite expands this to 9 read-write backends plus read-only backends, consolidates duplicate per-backend tests, and adds async mirrors.

The key technical challenges are: (1) designing a fixture matrix that handles backends with different capabilities (blob vs object layer, scheme vs path, variable particle support), (2) ensuring MongoDB and Redis tests fail instead of skip when services are unavailable (removing `pytest.importorskip` patterns), and (3) structuring async tests to use `SyncToAsyncAdapter` for all backends while also testing native async backends (MongoDB, Redis) directly.

**Primary recommendation:** Build the contract `conftest.py` first with the full backend parametrization matrix, then write facade-level contract tests (not backend-level), and finally delete overlapping existing tests.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Fresh `tests/contract/` directory alongside existing tests
- Organized by facade: `test_blob_contract.py`, `test_object_contract.py`, `test_ase_contract.py`, `test_h5md_compliance.py`
- Async tests in separate files: `test_async_blob_contract.py`, `test_async_object_contract.py`, `test_async_ase_contract.py`
- Contract-specific `conftest.py` in `tests/contract/` owns all backend parametrization fixtures
- Root `conftest.py` keeps shared atom fixtures -- contract tests access them via pytest fixture mechanism (no direct imports from conftest)
- Existing tests that overlap with contract suite are deleted in this phase
- Full matrix: every backend tested through every facade it supports (Blob, Object, ASE) via adapters where needed
- Read-write backends in matrix: HDF5 ragged (.h5), HDF5 padded (.h5p), Zarr ragged (.zarr), Zarr padded (.zarrp), H5MD (.h5md), LMDB (.lmdb), MongoDB (mongodb://), Redis (redis://), Memory (memory://)
- Read-only backends get a read-only contract subset: ASE .traj/.xyz/.extxyz, HuggingFace
- H5MD compliance tests in dedicated `test_h5md_compliance.py`; H5MD also participates in ASEIO contract tests
- All backends tested through async facades via SyncToAsyncAdapter
- MongoDB and Redis tests always fail (not skip) when services are unavailable
- `@pytest.mark.mongodb` and `@pytest.mark.redis` marks for selective running
- `@pytest.mark.hf` mark for HuggingFace tests -- skipped in CI, run locally
- Minimal `docker-compose.yml` at project root with MongoDB + Redis
- Reuse s22/ethanol/atoms_with_* fixtures from root conftest.py
- Backend capabilities as pytest.param marks for edge case skipping
- Round-trip verification via np.allclose / equality

### Claude's Discretion
- Which existing test files to delete (overlap analysis during planning)
- Exact capability marks and which backends get which marks
- Test helper utilities for Atoms comparison
- How to structure read-only contract tests for ASE/HF backends
- Fixture file generation for read-only backend tests

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TEST-01 | Contract test suite with parametrized fixtures testing every backend through BlobIO, ObjectIO, and ASEIO facades | Backend matrix in conftest.py with 9 RW + read-only backends; facade-level test files |
| TEST-02 | Edge case tests: empty datasets, single-frame, variable particle counts, large arrays, NaN/inf, empty strings, nested info dicts | Capability marks on pytest.param entries; edge case tests skip unsupported backends |
| TEST-03 | Async test suite mirroring sync contract tests using @pytest.mark.anyio | Separate async test files using SyncToAsyncAdapter for all backends |
| TEST-04 | H5MD spec compliance tests + znh5md interop | Dedicated test_h5md_compliance.py; H5MD also in normal ASEIO contract |
| TEST-06 | No test data behind authentication walls | All fixtures synthetic (s22, ethanol, molify-generated); no network-fetched data |
| TEST-08 | All backend tests run against real services via CI containers | docker-compose.yml for MongoDB+Redis; no mocking |
| TEST-09 | Tests must fail (not skip) when required service unavailable | Remove pytest.importorskip for pymongo/redis; use direct import |
| QUAL-06 | Standardize async test markers to @pytest.mark.anyio | All async contract tests use @pytest.mark.anyio consistently |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | >=8.4.2 | Test framework | Already in dev deps |
| anyio | >=4.0 | Async test backend for pytest-anyio | Already in dev deps |
| numpy | (from ase) | Array comparison in round-trip tests | np.allclose, np.array_equal |
| molify | >=0.0.1a0 | Synthetic test data generation | Already in dev deps |
| znh5md | >=0.4.8 | H5MD interop testing | Already in dev deps |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| h5py | >=3.12.0 | H5MD compliance structure inspection | test_h5md_compliance.py only |
| docker-compose | any | MongoDB + Redis CI services | CI and local development |

### Alternatives Considered
None -- all libraries already in project dev dependencies.

**Installation:**
```bash
uv sync  # All deps already declared in pyproject.toml
```

## Architecture Patterns

### Recommended Project Structure
```
tests/
  conftest.py              # Shared atom fixtures (s22, ethanol, atoms_with_*)
  contract/
    __init__.py
    conftest.py            # Backend parametrization fixtures
    test_blob_contract.py  # BlobIO facade contract tests
    test_object_contract.py # ObjectIO facade contract tests
    test_ase_contract.py   # ASEIO facade contract tests
    test_h5md_compliance.py # H5MD spec + znh5md interop
    test_async_blob_contract.py
    test_async_object_contract.py
    test_async_ase_contract.py
docker-compose.yml         # MongoDB + Redis services
```

### Pattern 1: Backend Parametrization via Factory Functions

**What:** Each backend gets a factory function in `tests/contract/conftest.py` that creates a fresh backend instance. Factories are used as `pytest.param` values with descriptive `id` strings and capability `marks`.

**When to use:** For all contract test parametrization.

**Example:**
```python
import pytest
from asebytes import ASEIO, ObjectIO, BlobIO

# Capability marks
supports_variable_particles = pytest.mark.supports_variable_particles
supports_per_atom_arrays = pytest.mark.supports_per_atom_arrays
supports_constraints = pytest.mark.supports_constraints
supports_nested_info = pytest.mark.supports_nested_info

def _h5_ragged_path(tmp_path):
    return str(tmp_path / "test.h5")

def _h5_padded_path(tmp_path):
    return str(tmp_path / "test.h5p")

def _zarr_ragged_path(tmp_path):
    return str(tmp_path / "test.zarr")

def _zarr_padded_path(tmp_path):
    return str(tmp_path / "test.zarrp")

def _h5md_path(tmp_path):
    return str(tmp_path / "test.h5md")

def _lmdb_path(tmp_path):
    return str(tmp_path / "test.lmdb")

def _mongo_uri():
    import os
    return os.environ.get("MONGO_URI", "mongodb://root:example@localhost:27017")

def _redis_uri():
    import os
    return os.environ.get("REDIS_URI", "redis://localhost:6379")

# ASEIO backends (object-level, produces Atoms)
ASEIO_BACKENDS = [
    pytest.param(_h5_ragged_path, id="h5-ragged",
                 marks=[supports_variable_particles, supports_per_atom_arrays,
                        supports_constraints, supports_nested_info]),
    pytest.param(_h5_padded_path, id="h5-padded",
                 marks=[supports_per_atom_arrays, supports_constraints,
                        supports_nested_info]),
    pytest.param(_zarr_ragged_path, id="zarr-ragged",
                 marks=[supports_variable_particles, supports_per_atom_arrays,
                        supports_constraints, supports_nested_info]),
    pytest.param(_zarr_padded_path, id="zarr-padded",
                 marks=[supports_per_atom_arrays, supports_constraints,
                        supports_nested_info]),
    pytest.param(_h5md_path, id="h5md",
                 marks=[supports_variable_particles, supports_per_atom_arrays,
                        supports_constraints, supports_nested_info]),
    pytest.param(_lmdb_path, id="lmdb",
                 marks=[supports_variable_particles, supports_per_atom_arrays,
                        supports_constraints, supports_nested_info]),
    # ... mongodb, memory
]

@pytest.fixture(params=ASEIO_BACKENDS)
def aseio(tmp_path, request):
    """Parametrized ASEIO instance for contract testing."""
    factory = request.param
    path = factory(tmp_path) if callable(factory) else factory
    return ASEIO(path)
```

### Pattern 2: Capability-Based Edge Case Skipping

**What:** Edge case tests that only apply to certain backends use capability marks. Tests check for the mark and skip if the backend lacks the capability.

**When to use:** For TEST-02 edge cases where not all backends support the feature.

**Example:**
```python
@pytest.mark.supports_variable_particles
def test_variable_particle_count_roundtrip(aseio, s22):
    """s22 has variable particle counts across frames."""
    aseio.extend(s22)
    for i, original in enumerate(s22):
        retrieved = aseio[i]
        assert len(retrieved) == len(original)
        assert np.allclose(retrieved.positions, original.positions)
```

Note: In `pyproject.toml`, register these marks and configure `filterwarnings` or `--strict-markers`. Use `pytest.ini_options` to handle unknown marks.

### Pattern 3: Service-Dependent Backend Failure

**What:** MongoDB and Redis backends must fail (not skip) when services are unavailable. Use direct `import` instead of `pytest.importorskip`.

**When to use:** For TEST-08 and TEST-09 compliance.

**Example:**
```python
# In tests/contract/conftest.py -- NO importorskip
import pymongo  # Will ImportError if not installed -- that's correct, it's a dev dep
import redis

# MongoDB fixture: always tries to connect, fails with ConnectionError if unavailable
@pytest.fixture
def mongo_backend():
    """MongoDB backend -- FAILS if MongoDB is unavailable."""
    group = f"test_{uuid.uuid4().hex[:8]}"
    b = MongoObjectBackend(uri=MONGO_URI, database="asebytes_test", group=group)
    yield b
    b.remove()
```

### Pattern 4: Async Contract Mirror

**What:** Async contract tests mirror sync tests but use `@pytest.mark.anyio` and `await`. All backends are wrapped via `SyncToAsyncAdapter` for async testing.

**When to use:** For TEST-03 (async mirrors).

**Example:**
```python
from asebytes._async_io import AsyncASEIO
from asebytes._async_backends import sync_to_async

@pytest.fixture(params=ASYNC_ASEIO_BACKENDS)
async def async_aseio(tmp_path, request):
    """Parametrized AsyncASEIO for contract testing."""
    factory = request.param
    path = factory(tmp_path)
    return AsyncASEIO(path)  # auto-wraps sync backend with SyncToAsyncAdapter

class TestAsyncASEIOContract:
    @pytest.mark.anyio
    async def test_extend_and_read(self, async_aseio, s22):
        await async_aseio.extend(s22)
        n = await async_aseio.len()
        assert n == len(s22)
        result = await async_aseio[0]
        assert isinstance(result, ase.Atoms)
```

### Pattern 5: Atoms Comparison Helper

**What:** A reusable helper function for comparing two Atoms objects field-by-field with appropriate tolerance.

**When to use:** Every ASEIO contract test that verifies round-trip fidelity.

**Example:**
```python
def assert_atoms_equal(actual: ase.Atoms, expected: ase.Atoms, *, rtol=1e-7, atol=0):
    """Assert two Atoms objects are equivalent for round-trip testing."""
    assert len(actual) == len(expected)
    np.testing.assert_array_equal(actual.numbers, expected.numbers)
    np.testing.assert_allclose(actual.positions, expected.positions, rtol=rtol, atol=atol)
    np.testing.assert_allclose(actual.cell.array, expected.cell.array, rtol=rtol, atol=atol)
    np.testing.assert_array_equal(actual.pbc, expected.pbc)

    # Info
    for key in expected.info:
        assert key in actual.info, f"Missing info key: {key}"
        if isinstance(expected.info[key], np.ndarray):
            np.testing.assert_allclose(actual.info[key], expected.info[key], rtol=rtol, atol=atol)
        else:
            assert actual.info[key] == expected.info[key], f"info[{key}] mismatch"

    # Arrays (custom, beyond positions/numbers)
    for key in expected.arrays:
        if key in ("positions", "numbers"):
            continue  # already checked
        assert key in actual.arrays, f"Missing arrays key: {key}"
        np.testing.assert_allclose(actual.arrays[key], expected.arrays[key], rtol=rtol, atol=atol)

    # Calc results
    if expected.calc is not None:
        assert actual.calc is not None, "Missing calculator"
        for key, val in expected.calc.results.items():
            assert key in actual.calc.results, f"Missing calc result: {key}"
            if isinstance(val, np.ndarray):
                np.testing.assert_allclose(actual.calc.results[key], val, rtol=rtol, atol=atol)
            else:
                assert actual.calc.results[key] == pytest.approx(val), f"calc.{key} mismatch"

    # Constraints
    if expected.constraints:
        assert len(actual.constraints) == len(expected.constraints)
```

### Anti-Patterns to Avoid
- **Testing at backend level instead of facade level:** Contract tests go through BlobIO/ObjectIO/ASEIO, not raw backend methods. The facades handle dict conversion, adapter wrapping, etc.
- **Using `pytest.importorskip` for required dependencies:** MongoDB (pymongo) and Redis (redis) are dev dependencies. Use direct `import` -- if not installed, tests should error, not skip.
- **Importing from conftest.py directly:** All fixture data must flow through the pytest fixture mechanism, not `from tests.conftest import s22`.
- **Hardcoding service URIs:** Use `os.environ.get()` with defaults matching docker-compose.yml.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Atoms comparison | Manual field-by-field assertions in each test | Shared `assert_atoms_equal` helper | Consistent tolerance handling, DRY |
| Backend parametrization | Copy-paste fixtures per backend | pytest.param with factory functions | Maintainable, extensible matrix |
| Docker services | Manual docker run commands | docker-compose.yml | Reproducible, CI-friendly |
| Async backend wrapping | Manual SyncToAsyncAdapter calls in tests | AsyncASEIO(path) auto-wrapping | Facades already handle this |

## Common Pitfalls

### Pitfall 1: Padded Backend Variable Particle Count
**What goes wrong:** Padded backends (.h5p, .zarrp) cannot store variable particle counts natively -- they pad to max size. Tests with s22 (variable particle counts) will work but the semantics differ from ragged.
**Why it happens:** Padded storage fills shorter frames with NaN/zero.
**How to avoid:** Mark padded backends without `supports_variable_particles` only if you want to test that padding is transparent. Actually, padded backends DO support variable particle counts via padding -- the round-trip should still work because `_n_atoms` metadata tracks original sizes. Test both but be aware of the padding mechanism.
**Warning signs:** Positions showing NaN values for padded atoms slots.

### Pitfall 2: BlobIO vs ObjectIO Layer Differences
**What goes wrong:** Redis is blob-level (bytes,bytes), MongoDB is object-level (str,Any). Testing through facades that don't match the native layer requires adapter wrapping, which the registry handles automatically.
**Why it happens:** Registry cross-layer fallback creates BlobToObject or ObjectToBlob adapters.
**How to avoid:** In the contract conftest, use facade constructors with path/URI strings (e.g., `BlobIO("redis://...")`, `ObjectIO("mongodb://...")`). The registry handles adapter wrapping.
**Warning signs:** Tests that directly instantiate backends and pass to facades -- let facades auto-resolve.

### Pitfall 3: MongoDB/Redis Connection Failures in CI
**What goes wrong:** Tests fail with `ConnectionRefusedError` when Docker services aren't running.
**Why it happens:** Services need to be started before tests run.
**How to avoid:** docker-compose.yml at project root + CI workflow starts services before test step. Use `@pytest.mark.mongodb` / `@pytest.mark.redis` for local runs without services (`pytest -m 'not mongodb and not redis'`).
**Warning signs:** ConnectionError on first MongoDB/Redis test.

### Pitfall 4: HuggingFace Network Dependency
**What goes wrong:** HF tests require network access to download datasets.
**Why it happens:** HuggingFace backend reads from remote API.
**How to avoid:** Mark with `@pytest.mark.hf`, skip in CI. For read-only contract tests, consider creating a local .traj fixture instead and only testing HF separately.
**Warning signs:** TimeoutError or network errors in CI.

### Pitfall 5: Memory Backend Global State
**What goes wrong:** Memory backend uses `_GLOBAL_STORAGE` dict -- tests can leak state across test cases.
**Why it happens:** `MemoryObjectBackend` with the same group shares data.
**How to avoid:** Use unique group names (uuid) per test, and call `remove()` in fixture teardown.
**Warning signs:** Tests passing individually but failing when run together.

### Pitfall 6: Existing Test Deletion Scope
**What goes wrong:** Deleting test files that cover functionality NOT in the contract suite (e.g., race condition tests, stale cache tests, URI parsing tests).
**Why it happens:** Over-eager deletion during cleanup.
**How to avoid:** Only delete test files whose functionality is fully subsumed by the contract suite. Keep backend-specific tests that cover unique backend features (URI parsing, race conditions, group isolation, etc.).
**Warning signs:** Test coverage decrease after deletion.

## Code Examples

### Backend Registry Entries (source of truth)
```python
# From src/asebytes/_registry.py -- these define what backends exist
# Object-level, pattern-based:
#   *.lmdb -> LMDBObjectBackend (via BlobToObject adapter)
#   *.h5   -> RaggedColumnarBackend
#   *.h5p  -> PaddedColumnarBackend
#   *.h5md -> H5MDBackend
#   *.zarr -> RaggedColumnarBackend
#   *.zarrp -> PaddedColumnarBackend
#   *.traj/xyz/extxyz -> ASEReadOnlyBackend (read-only)
# Scheme-based:
#   mongodb:// -> MongoObjectBackend
#   memory://  -> MemoryObjectBackend
#   hf://      -> HuggingFaceBackend (read-only)
# Blob-level:
#   *.lmdb -> LMDBBlobBackend
#   redis:// -> RedisBlobBackend
```

### Existing Fixture Library (root conftest.py)
```python
# Available fixtures from root conftest.py:
# - s22: 22 frames, variable particle counts (2-24 atoms), no calc
# - s22_energy: s22 with energy
# - s22_energy_forces: s22 with energy + forces
# - s22_all_properties: s22 with ALL calc properties (12 properties)
# - s22_info_arrays_calc: s22 with info, custom arrays, calc
# - s22_mixed_pbc_cell: s22 with random pbc + cell
# - s22_info_arrays_calc_missing_inbetween: s22 with sporadic info/arrays/calc
# - ethanol: 1000 frames, fixed-size (9 atoms), with energy+forces+stress
# - water: single frame, no positions
# - full_water: single frame with calc+info+arrays
# - atoms_with_info: H2 with diverse info types (str, int, float, bool, list, dict, ndarray)
# - atoms_with_calc: H2 with energy+forces
# - atoms_with_pbc: H with mixed pbc and cell
# - atoms_with_constraints: H2O with FixAtoms
# - empty_atoms: Atoms() with no atoms
# - mongo_uri, redis_uri: service connection strings
```

### Docker Compose for Services
```yaml
# docker-compose.yml
services:
  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: root
      MONGO_INITDB_ROOT_PASSWORD: example

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### pytest.ini_options Additions
```toml
# pyproject.toml additions needed
markers = [
    "benchmark: marks tests as benchmark tests",
    "mongodb: marks tests requiring MongoDB",
    "redis: marks tests requiring Redis",
    "hf: marks tests requiring HuggingFace network access",
    "supports_variable_particles: backend supports variable particle counts",
    "supports_per_atom_arrays: backend supports per-atom custom arrays",
    "supports_constraints: backend supports constraint round-trip",
    "supports_nested_info: backend supports nested dict info values",
]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Per-backend test files | Parametrized contract suite | This phase | Single source of truth for correctness |
| `pytest.importorskip("pymongo")` | Direct import, fail on missing | This phase | TEST-09 compliance |
| 3 backends in `uni_*` fixtures | 9+ backends in contract fixtures | This phase | Full coverage |
| Mixed `@pytest.mark.anyio` usage | Consistent `@pytest.mark.anyio` everywhere | This phase | QUAL-06 compliance |

## Open Questions

1. **Which existing test files to delete?**
   - What we know: Many test files overlap with contract suite scope (test_aseio.py, test_mongodb.py, test_redis.py, test_universal_*.py, test_bytesio.py, etc.)
   - What's unclear: Some files test features beyond the contract scope (race conditions, URI parsing, stale cache). Need per-file overlap analysis during planning.
   - Recommendation: Conservative approach -- delete only files fully subsumed. Keep specialized tests.

2. **HuggingFace read-only testing strategy?**
   - What we know: HF requires network. TEST-06 says no auth-wall data.
   - What's unclear: Whether to include HF in contract suite at all or test separately.
   - Recommendation: Include with `@pytest.mark.hf` mark, skip in CI. HF tests are read-only and use public datasets.

3. **Padded backend capability marks?**
   - What we know: Padded backends store variable particle data via NaN padding + `_n_atoms` metadata.
   - What's unclear: Whether to mark padded as "not supporting variable particles" or to test that padding is transparent.
   - Recommendation: Padded backends DO support variable particles (via padding). Give them the mark. The round-trip should be transparent. Only withhold the mark if a specific edge case genuinely fails.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=8.4.2 + anyio >=4.0 |
| Config file | pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `uv run pytest tests/contract/ -x` |
| Full suite command | `uv run pytest tests/contract/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TEST-01 | Every backend through every facade | integration | `uv run pytest tests/contract/test_ase_contract.py tests/contract/test_object_contract.py tests/contract/test_blob_contract.py -x` | Wave 0 |
| TEST-02 | Edge cases (empty, single-frame, NaN, etc.) | integration | `uv run pytest tests/contract/ -k "edge" -x` | Wave 0 |
| TEST-03 | Async mirrors | integration | `uv run pytest tests/contract/test_async_*.py -x` | Wave 0 |
| TEST-04 | H5MD compliance + interop | integration | `uv run pytest tests/contract/test_h5md_compliance.py -x` | Wave 0 |
| TEST-06 | No auth-wall data | manual-only | Verify fixtures are synthetic | N/A |
| TEST-08 | Real services, no mocking | integration | `uv run pytest tests/contract/ -m mongodb -x` | Wave 0 |
| TEST-09 | Fail not skip on missing service | integration | `uv run pytest tests/contract/ -m mongodb --co` (verify no skip markers) | Wave 0 |
| QUAL-06 | Consistent @pytest.mark.anyio | manual-only | Grep for async test functions, verify all use anyio marker | N/A |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/contract/ -x --timeout=60`
- **Per wave merge:** `uv run pytest tests/ -x` (full suite including contract)
- **Phase gate:** Full suite green before verify-work

### Wave 0 Gaps
- [ ] `tests/contract/__init__.py` -- package init
- [ ] `tests/contract/conftest.py` -- backend parametrization fixtures
- [ ] `docker-compose.yml` -- MongoDB + Redis services
- [ ] `pyproject.toml` marker registration -- mongodb, redis, hf, capability marks

## Sources

### Primary (HIGH confidence)
- Project codebase: `src/asebytes/_registry.py` -- complete backend registry (9 RW + 3 read-only entries)
- Project codebase: `tests/conftest.py` -- 20+ fixture definitions, existing parametrization patterns
- Project codebase: `pyproject.toml` -- dev dependencies, pytest config
- Project codebase: existing test files (`test_mongodb.py`, `test_redis.py`, `test_h5md_backend.py`, etc.) -- established patterns

### Secondary (MEDIUM confidence)
- pytest documentation for parametrize + marks: well-established patterns
- docker-compose for MongoDB + Redis: standard approach

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in project dependencies
- Architecture: HIGH -- patterns derived from existing codebase conventions
- Pitfalls: HIGH -- identified from actual code review (global state, layer mismatches, importorskip patterns)

**Research date:** 2026-03-06
**Valid until:** 2026-04-06 (stable domain, project-internal)
