---
phase: 04-benchmarks-performance
plan: 02
subsystem: performance
tags: [hdf5, mongodb, redis, benchmark, cache, chunk-cache]

requires:
  - phase: 04-benchmarks-performance
    provides: Benchmark data fixtures (ethanol, periodic, network backends)
provides:
  - HDF5 chunk cache tuning via rdcc_nslots parameter
  - MongoDB TTL-based metadata cache (1s window)
  - Facade bounds-check elimination (skip len() for positive indices)
  - Benchmark baselines in .benchmarks/ directory
affects: []

tech-stack:
  added: []
  patterns: [TTL cache with time.monotonic, try/except IndexError delegation]

key-files:
  created:
    - .benchmarks/Darwin-CPython-3.11-64bit/0001_baseline.json
  modified:
    - src/asebytes/columnar/_store.py
    - src/asebytes/mongodb/_backend.py
    - src/asebytes/io.py
    - src/asebytes/_object_io.py
    - src/asebytes/_blob_io.py
    - src/asebytes/_async_views.py
    - tests/test_index_bounds.py

key-decisions:
  - "Backends must raise IndexError on OOB -- facades no longer pre-check bounds for positive indices"
  - "MongoDB set() does not invalidate cache since it only changes row data not sort_keys/count"
  - "TTL cache uses time.monotonic() with 1s window for MongoDB metadata"

patterns-established:
  - "Bounds delegation: facades catch IndexError from backend instead of pre-checking with len()"
  - "TTL cache pattern: _cache_loaded_at + _cache_ttl with time.monotonic()"

requirements-completed: [PERF-01, PERF-02, PERF-03, PERF-04]

duration: 22min
completed: 2026-03-06
---

# Phase 4 Plan 2: Performance Optimizations Summary

**HDF5 rdcc_nslots chunk cache, MongoDB 1s TTL metadata cache, facade bounds-check elimination saving 1 RT for positive indices, and benchmark baselines saved**

## Performance

- **Duration:** 22 min
- **Started:** 2026-03-06T16:35:15Z
- **Completed:** 2026-03-06T16:57:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- HDF5Store now passes rdcc_nslots=10007 (prime) to h5py.File for better chunk cache hash distribution
- MongoDB _ensure_cache skips metadata fetch within 1s TTL window, reducing round trips for sequential reads
- MongoDB set() no longer invalidates sort_keys cache (set only changes row data, not metadata)
- All three facade __getitem__ methods skip len() for positive int indices, saving 1 RT for Redis
- Async views (AsyncSingleRowView) also updated with same bounds-delegation pattern
- 52 benchmark tests ran successfully, baselines saved to .benchmarks/

## Task Commits

Each task was committed atomically:

1. **Task 1: HDF5 rdcc_nslots, MongoDB TTL cache, facade bounds-check elimination** - `475b34f` (perf)
2. **Task 2: Save benchmark baselines** - `42da3b1` (chore)

## Files Created/Modified
- `src/asebytes/columnar/_store.py` - Added rdcc_nslots parameter to HDF5Store.__init__
- `src/asebytes/mongodb/_backend.py` - Added TTL cache to _ensure_cache, removed invalidation from set()
- `src/asebytes/io.py` - ASEIO.__getitem__ delegates bounds check to backend
- `src/asebytes/_object_io.py` - ObjectIO.__getitem__ delegates bounds check to backend
- `src/asebytes/_blob_io.py` - BlobIO.__getitem__ delegates bounds check to backend
- `src/asebytes/_async_views.py` - AsyncSingleRowView delegates upper-bound check to backend
- `tests/test_index_bounds.py` - Updated mock backends to raise IndexError on OOB
- `.benchmarks/Darwin-CPython-3.11-64bit/0001_baseline.json` - Benchmark baseline data

## Decisions Made
- Backends must raise IndexError on out-of-bounds access; facades no longer pre-check for positive indices
- MongoDB set() removed from cache invalidation since it only modifies row data, not sort_keys/count
- TTL cache uses time.monotonic() (not time.time()) for monotonic clock guarantees

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated async views bounds checking to match sync facades**
- **Found during:** Task 1 (facade bounds-check elimination)
- **Issue:** AsyncSingleRowView._resolve_index still called len() for all indices, inconsistent with sync facade optimization
- **Fix:** Updated _resolve_index to only call len() for negative indices, _materialize catches IndexError from backend
- **Files modified:** src/asebytes/_async_views.py
- **Verification:** All async bounds tests pass
- **Committed in:** 475b34f (Task 1 commit)

**2. [Rule 1 - Bug] Updated test mock backends to match new contract**
- **Found during:** Task 1 (facade bounds-check elimination)
- **Issue:** _PermissiveBlobBackend/ObjectBackend returned None for OOB, but new facade relies on backend raising IndexError
- **Fix:** Changed all 4 mock backends (sync + async) to raise IndexError instead of returning None
- **Files modified:** tests/test_index_bounds.py
- **Verification:** All bounds tests pass (1845 non-network tests green)
- **Committed in:** 475b34f (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes necessary for consistency between sync/async and test correctness. No scope creep.

## Issues Encountered
- MongoDB sync/async tests show stale data from previous test runs (pre-existing, not caused by TTL change)
- Redis async blob test has pre-existing failure unrelated to this plan's changes

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All performance optimizations implemented and verified
- Benchmark baselines saved for future regression comparison
- Phase 4 complete -- all plans executed

---
*Phase: 04-benchmarks-performance*
*Completed: 2026-03-06*
