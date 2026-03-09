# Phase 8: Fix failing tests in Redis/Mongo backends (test isolation) - Context

**Gathered:** 2026-03-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix test isolation for MongoDB and Redis backends so tests don't fail due to data leaking between tests. Currently both backends share a single static URI with no per-test namespacing, unlike file-based backends which get natural isolation from `tmp_path`. Referenced PRs: zincware/asebytes#11, #12.

</domain>

<decisions>
## Implementation Decisions

### Isolation strategy
- Generate a unique group name per test (UUID-based, like `memory://` already does)
- Pass `group=` to every backend uniformly — all backends (HDF5, Zarr, LMDB, MongoDB, Redis, Memory) support the `group` parameter
- No conditional logic — always pass group, every backend gets it
- Facades (ASEIO, ObjectIO, BlobIO) already forward `**kwargs` to backend constructors, so `group=` passes through naturally

### Cleanup scope
- Keep existing per-test teardown (`db.remove()` in fixture yield)
- With unique groups, each test's `remove()` only cleans up its own data — no cross-contamination
- No session-level flush needed

### CI impact
- No changes to CI Docker service configuration
- Single MongoDB/Redis instance is sufficient — unique groups solve isolation within a single instance
- Existing Docker services in tests.yml and benchmark.yml remain as-is

### Claude's Discretion
- Exact UUID format/length for group names
- Whether to use the same group generation pattern as memory:// (`test_{uuid.uuid4().hex[:8]}`) or a different scheme
- How to handle the memory:// backend (already uses UUID in URI — may or may not also need group=)

</decisions>

<specifics>
## Specific Ideas

- "Don't do the if/else! Always pass the group!" — no conditional branching based on backend type
- The `memory://` backend pattern (`test_{uuid.uuid4().hex[:8]}`) is the model for how all backends should get unique namespacing
- The `group` parameter is part of the universal backend protocol — every backend accepts it

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/contract/conftest.py` — fixture factories (`_h5_ragged_path`, `_mongo_uri`, etc.) and parametrized facade fixtures (`aseio`, `objectio`, `blobio`, async mirrors)
- `uuid` already imported in contract conftest (used by `_memory_uri`)
- All facades accept `**kwargs` and forward to backend constructors

### Established Patterns
- `group` parameter on all backends: HDF5/Zarr (HDF5 group), LMDB (subdirectory), MongoDB (collection name), Redis (key prefix)
- `DEFAULT_GROUP` constant used when group=None
- Per-test teardown via `db.remove()` in fixture yield blocks
- `_memory_uri` already generates UUID-based unique names

### Integration Points
- `tests/contract/conftest.py` — primary file to modify (fixture factories + facade fixtures)
- Backend `__init__` signatures — no changes needed, all already accept `group=`
- Facade `__init__` signatures — no changes needed, all forward `**kwargs`

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 08-fix-failing-tests-in-redis-mongo-backends-test-isolation*
*Context gathered: 2026-03-09*
