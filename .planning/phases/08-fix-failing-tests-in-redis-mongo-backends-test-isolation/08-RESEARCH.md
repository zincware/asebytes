# Phase 8: Fix failing tests in Redis/Mongo backends (test isolation) - Research

**Researched:** 2026-03-09
**Domain:** pytest fixture isolation for shared-instance backends
**Confidence:** HIGH

## Summary

The test isolation problem is straightforward and well-scoped. MongoDB and Redis backends share a single server instance across all tests. Unlike file-based backends (HDF5, Zarr, LMDB) which get natural per-test isolation via pytest's `tmp_path`, network backends (`_mongo_uri`, `_redis_uri`) return the same static URI for every test and rely on `DEFAULT_GROUP = "default"`. This means all tests read/write the same MongoDB collection or Redis key prefix, causing data leakage between tests.

The fix is purely in `tests/contract/conftest.py`: pass a unique `group=test_{uuid4.hex[:8]}` kwarg when constructing each facade instance. Every backend already accepts `group` in its constructor and `from_uri`. Facades already forward `**kwargs` to backends. No production code changes are needed.

**Primary recommendation:** Add a unique `group=` kwarg to every facade construction in conftest fixtures. Single file change, ~20 lines modified.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Generate a unique group name per test (UUID-based, like `memory://` already does)
- Pass `group=` to every backend uniformly -- all backends support the `group` parameter
- No conditional logic -- always pass group, every backend gets it
- Keep existing per-test teardown (`db.remove()` in fixture yield)
- No changes to CI Docker service configuration
- Single MongoDB/Redis instance is sufficient

### Claude's Discretion
- Exact UUID format/length for group names
- Whether to use the same group generation pattern as memory:// (`test_{uuid.uuid4().hex[:8]}`) or a different scheme
- How to handle the memory:// backend (already uses UUID in URI -- may or may not also need group=)

### Deferred Ideas (OUT OF SCOPE)
None
</user_constraints>

## Architecture Patterns

### Current Flow (broken)

```
_mongo_uri(tmp_path) -> "mongodb://root:example@localhost:27017"  (static)
_redis_uri(tmp_path) -> "redis://localhost:6379"                   (static)

ASEIO(path)  ->  MongoObjectBackend.from_uri(uri, group=None)  ->  group = "default"
                 All tests share collection "default" -> DATA LEAKAGE
```

### Fixed Flow

```
_mongo_uri(tmp_path) -> "mongodb://root:example@localhost:27017"  (static, unchanged)
_redis_uri(tmp_path) -> "redis://localhost:6379"                   (static, unchanged)

group = f"test_{uuid.uuid4().hex[:8]}"
ASEIO(path, group=group)  ->  MongoObjectBackend.from_uri(uri, group="test_a1b2c3d4")
                               Unique collection per test -> ISOLATED
```

### Key Mechanism: kwargs Pass-Through

All facades accept `**kwargs` and forward them:

```python
# ASEIO.__init__ (src/asebytes/io.py:38-56)
def __init__(self, backend: str | ReadBackend, *, readonly=None, cache_to=None, **kwargs):
    ...
    cls.from_uri(backend, **kwargs)  # group= passes through here
```

Same pattern in `ObjectIO`, `BlobIO`, and all async mirrors.

### Group Semantics Per Backend

| Backend | `group` maps to | Isolation mechanism |
|---------|-----------------|---------------------|
| MongoDB | Collection name (`self._client[database][self.group]`) | Separate collection per test |
| Redis | Key prefix (`self._prefix = self.group`) | Keys namespaced by prefix |
| LMDB | Subdirectory under file path | Already isolated via `tmp_path` |
| HDF5/Zarr | HDF5 group path | Already isolated via `tmp_path` |
| Memory | N/A -- URI itself is unique (`memory://test_{uuid}`) | Already isolated |

### Cleanup: `remove()` is group-scoped

- MongoDB: `self._col.drop()` -- drops only this collection (group)
- Redis: `scan(match=f"{self._prefix}:*")` then delete -- only keys with this prefix

This means with unique groups, each test's `remove()` only cleans its own data. No risk of one test's teardown wiping another test's data during parallel execution.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Test isolation for shared backends | Custom session-level DB flush, conditional cleanup logic | `group=uuid` parameter already supported by all backends | Existing protocol, zero production code changes |
| Unique test identifiers | Custom test name hashing, node-id parsing | `uuid.uuid4().hex[:8]` | Simple, collision-resistant, already used by memory backend |

## Common Pitfalls

### Pitfall 1: Conditional group logic
**What goes wrong:** Adding `if backend_type == "mongo": pass group` creates maintenance burden and violates the uniform protocol.
**How to avoid:** Always pass `group=` regardless of backend type. File-based backends accept it and use it as an HDF5 group or subdirectory -- harmless.

### Pitfall 2: Forgetting async fixtures
**What goes wrong:** Fixing only sync fixtures (`aseio`, `objectio`, `blobio`) but not async fixtures (`async_aseio`, `async_objectio`, `async_blobio`).
**How to avoid:** All 6 facade fixtures must pass `group=`. The async fixtures use the same backend factories.

### Pitfall 3: Memory backend double-isolation
**What goes wrong:** `_memory_uri` already generates a unique URI per test (`memory://test_{uuid}`). Adding `group=` on top is unnecessary but harmless.
**How to avoid:** Pass `group=` uniformly to all backends including memory. The memory backend will use the group, and the unique URI also provides isolation. No conflict.

### Pitfall 4: Group collisions in parallel test runs
**What goes wrong:** If tests run in parallel (pytest-xdist), UUID collision is astronomically unlikely with 8 hex chars (4 billion possibilities).
**How to avoid:** 8 hex chars is sufficient. The memory backend already uses this length successfully.

## Code Examples

### The Fix (conftest.py fixture pattern)

```python
# Before (broken for mongo/redis):
@pytest.fixture(params=ASEIO_BACKENDS)
def aseio(tmp_path, request):
    factory = request.param
    path = factory(tmp_path)
    db = ASEIO(path)                    # no group -> DEFAULT_GROUP = "default"
    yield db
    ...

# After (isolated):
@pytest.fixture(params=ASEIO_BACKENDS)
def aseio(tmp_path, request):
    factory = request.param
    path = factory(tmp_path)
    group = f"test_{uuid.uuid4().hex[:8]}"
    db = ASEIO(path, group=group)       # unique group per test
    yield db
    ...
```

### All fixtures that need updating

1. `aseio` (line 152-165)
2. `objectio` (line 167-179)
3. `blobio` (line 181-193)
4. `async_aseio` (line 214-221)
5. `async_objectio` (line 223-230)
6. `async_blobio` (line 232-240)

Total: 6 fixtures, each needs 2 lines changed (add `group=` variable + pass to constructor).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 |
| Config file | pyproject.toml |
| Quick run command | `uv run pytest tests/contract/ -k "mongodb or redis" -x` |
| Full suite command | `uv run pytest tests/contract/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| N/A | MongoDB tests pass in isolation | integration | `uv run pytest tests/contract/ -k mongodb -x` | Existing tests |
| N/A | Redis tests pass in isolation | integration | `uv run pytest tests/contract/ -k redis -x` | Existing tests |
| N/A | All other backends unbroken | integration | `uv run pytest tests/contract/ -x` | Existing tests |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/contract/ -k "mongodb or redis" -x`
- **Per wave merge:** `uv run pytest tests/contract/ -x`
- **Phase gate:** Full suite green (requires MongoDB and Redis services running)

### Wave 0 Gaps
None -- existing test infrastructure covers all phase requirements. The fix is in fixture setup, not in test code.

## Open Questions

1. **Should file-based backends also get explicit group= for consistency?**
   - What we know: File-based backends already get isolation from `tmp_path`. Passing `group=` to them is harmless (creates a subgroup in HDF5, subdirectory in LMDB).
   - Recommendation: YES, pass `group=` uniformly to all backends. This matches the locked decision "no conditional logic" and adds defense-in-depth.

2. **Can this be verified locally without Docker services?**
   - What we know: MongoDB and Redis tests require running services. CI has Docker services configured.
   - Recommendation: If services unavailable locally, verify file-based and memory backends pass, then rely on CI for mongo/redis verification.

## Sources

### Primary (HIGH confidence)
- `tests/contract/conftest.py` -- current fixture implementations, line-by-line analysis
- `src/asebytes/mongodb/_backend.py` -- MongoObjectBackend.from_uri accepts group=, uses as collection name
- `src/asebytes/redis/_backend.py` -- RedisBlobBackend.from_uri accepts group=, uses as key prefix
- `src/asebytes/io.py` -- ASEIO.__init__ forwards **kwargs to from_uri
- `src/asebytes/mongodb/_async_backend.py`, `src/asebytes/redis/_async_backend.py` -- async mirrors confirm same group= protocol

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new libraries needed, pure fixture change
- Architecture: HIGH - direct code inspection confirms kwargs pass-through and group semantics
- Pitfalls: HIGH - failure mode is well understood (shared DEFAULT_GROUP)

**Research date:** 2026-03-09
**Valid until:** Indefinite - this is a test infrastructure fix, not dependent on external library versions
