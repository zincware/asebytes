# Phase 4: Benchmarks & Performance - Research

**Researched:** 2026-03-06
**Domain:** pytest-benchmark, HDF5 chunk cache, MongoDB TTL, Redis Lua optimization
**Confidence:** HIGH

## Summary

Phase 4 builds on a well-established foundation: the existing `tests/benchmarks/` suite already has 5 benchmark files covering all backends through facades, with a `BenchDB` dataclass pattern and third-party comparisons. The primary work is (1) replacing the lemat dataset with molify-generated synthetic data, (2) adding dataset-size parametrization, (3) implementing three targeted optimizations (HDF5 rdcc_nslots, MongoDB TTL cache, Redis Lua bounds elimination), and (4) recording baselines with `--benchmark-save`.

The optimization paths are all validated by ad-hoc benchmarks in `benchmarks/proposals/RESULTS.md` with proven speedups: MongoDB TTL gives 3.5x on single reads, Redis Lua bounds elimination gives 1.9x, and HDF5 chunk cache tuning (rdcc_nslots) is a standard h5py parameter that is currently missing. All three are low-risk, well-understood changes.

**Primary recommendation:** Refactor existing benchmark fixtures (replace lemat, add pack-based periodic data, parametrize frame counts), then implement the three optimizations with before/after benchmark comparison via `--benchmark-save` and `--benchmark-compare`.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Build on existing pytest-benchmark suite at `tests/benchmarks/` (5 files, all backends, facade-level)
- Update ROADMAP to reference `uv run pytest tests/benchmarks/` instead of `benchmarks/`
- Organize by operation (existing structure: bench_read, bench_write, bench_random_access, bench_property_access, bench_update)
- Benchmark through facades (ASEIO/ObjectIO) like real users -- not direct backend access
- Cover ALL backends (file-based + MongoDB + Redis + LMDB + Memory)
- Keep third-party comparisons (aselmdb, sqlite, znh5md, extxyz) -- they are dev dependencies
- Isolate benchmarks from regular test suite via `@pytest.mark.benchmark` marker with pytest config excluding them from default runs
- Remove lemat dataset (depends on HuggingFace data, violates TEST-06)
- Replace with molify-generated data using molify.pack for periodic structures
- 2x2 parametrization matrix: frames=[100, 1000] x atoms=[small ~9 via smiles2conformers('CCO'), large ~50-100 via pack]
- Full properties per frame: positions, numbers, cell, pbc, SinglePointCalculator (energy, forces, stress), constraints, custom info/arrays
- Session-scoped fixtures for data generation
- PERF-01: HDF5 chunk cache tuning (rdcc_nbytes + rdcc_nslots) for .h5/.h5p backends
- PERF-02: MongoDB TTL cache with 1-second TTL
- PERF-03: Redis Lua-only bounds checking -- remove separate len() round-trip
- H5MD is NOT touched -- it follows the H5MD 1.1 spec
- Use pytest-benchmark `--benchmark-save=baseline` for JSON result storage
- Commit `.benchmarks/` directory to git for reproducible comparisons
- No CI regression detection for now

### Claude's Discretion
- Exact rdcc_nslots value for HDF5 chunk cache (tune based on benchmark evidence)
- Whether to add a `--benchmark-only` pytest marker alias for convenience
- How to handle MongoDB/Redis service unavailability during benchmark runs (skip vs fail)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TEST-05 | Performance benchmark suite using pytest-benchmark with synthetic molify data | Existing suite in `tests/benchmarks/` needs fixture refactoring (replace lemat, add pack, parametrize sizes). pytest-benchmark 5.2.1 already installed. |
| TEST-07 | Benchmark covers sequential read, random access, bulk write, column read for each backend at multiple sizes | Existing 5 test files cover all operations. Need to add frame-count parametrization to `conftest.py` dataset fixture. |
| PERF-01 | HDF5 chunk cache tuning (rdcc_nbytes + rdcc_nslots) | HDF5Store at `_store.py:83` has rdcc_nbytes=64MB but is missing rdcc_nslots. Add rdcc_nslots parameter (recommend 10007 prime) to `h5py.File()` call. |
| PERF-02 | MongoDB TTL cache for metadata | MongoObjectBackend's `_ensure_cache()` fetches metadata on every call. Add `_cache_loaded_at` timestamp + TTL check (1s). Proven 3.5x speedup in proposals. |
| PERF-03 | Redis Lua bounds checking | Facade's `__getitem__` calls `len(self)` (LLEN RT) before `get()` (Lua RT which also does LLEN internally). Eliminate redundant `len()` call. Proven 1.9x speedup. |
| PERF-04 | Establish baselines before/after optimizations | Use `--benchmark-save=baseline` before optimizations, then `--benchmark-save=optimized` after, compare with `--benchmark-compare`. |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest-benchmark | 5.2.1 | Micro-benchmark framework | Already installed, integrates with pytest, JSON storage, comparison tools |
| molify | (installed) | Synthetic molecular data generation | Already used in `tests/conftest.py` for ethanol fixture |
| h5py | >=3.12.0 | HDF5 file access with chunk cache params | Project dependency, `rdcc_nbytes`/`rdcc_nslots` are native `h5py.File()` kwargs |
| pymongo | (installed) | MongoDB driver | Project dependency for MongoObjectBackend |
| redis | >=5.0 | Redis driver with Lua script support | Project dependency for RedisBlobBackend |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| ase | (installed) | ASE Atoms, SinglePointCalculator, constraints, build | Generate synthetic data with full properties |
| numpy | (installed) | Array generation for benchmark data | Random forces/stress/positions |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| molify.pack | ase.build.bulk * supercell | pack requires packmol executable; ase.build needs no external tool but produces crystal structures not molecular packings. For benchmarks, both yield periodic structures with known atom counts. Consider ase.build as fallback if packmol unavailable. |

**Installation:**
```bash
# All dependencies already installed -- no new packages needed
uv sync
```

## Architecture Patterns

### Existing Benchmark Structure (keep as-is)
```
tests/benchmarks/
  conftest.py                    # BenchDB dataclass, dataset fixture, per-backend fixtures
  test_bench_read.py             # sequential read (single + trajectory)
  test_bench_write.py            # bulk write (single + trajectory)
  test_bench_random_access.py    # random read (single + trajectory)
  test_bench_property_access.py  # positions/energy column access
  test_bench_update.py           # bulk column update
```

### Pattern 1: Session-Scoped Synthetic Data Fixtures
**What:** Generate molecular data once per session, reuse across all benchmarks
**When to use:** All benchmark data generation
**Example:**
```python
# tests/conftest.py -- session-scoped, no HuggingFace dependency
@pytest.fixture(scope="session")
def ethanol_100() -> list[ase.Atoms]:
    frames = molify.smiles2conformers("CCO", numConfs=100)
    _attach_full_properties(frames)
    return frames

@pytest.fixture(scope="session")
def ethanol_1000() -> list[ase.Atoms]:
    frames = molify.smiles2conformers("CCO", numConfs=1000)
    _attach_full_properties(frames)
    return frames

@pytest.fixture(scope="session")
def periodic_100() -> list[ase.Atoms]:
    # Use molify.pack or ase.build for periodic structures (~50-100 atoms)
    ...

@pytest.fixture(scope="session")
def periodic_1000() -> list[ase.Atoms]:
    ...
```

### Pattern 2: Dataset Parametrization Matrix
**What:** 2x2 matrix of (frame_count, atom_size) covering small/large molecules at 100/1000 frames
**When to use:** Benchmark conftest dataset fixture
**Example:**
```python
# tests/benchmarks/conftest.py
DATASETS = ["ethanol_100", "ethanol_1000", "periodic_100", "periodic_1000"]

@pytest.fixture(params=DATASETS)
def dataset(request):
    return request.param, request.getfixturevalue(request.param)
```

### Pattern 3: MongoDB TTL Cache
**What:** Time-based cache invalidation for metadata document
**When to use:** MongoObjectBackend._ensure_cache()
**Example:**
```python
import time

class MongoObjectBackend:
    def __init__(self, ...):
        ...
        self._cache_loaded_at: float = 0.0
        self._cache_ttl: float = 1.0  # seconds

    def _ensure_cache(self) -> None:
        now = time.monotonic()
        if (self._sort_keys is not None
                and (now - self._cache_loaded_at) < self._cache_ttl):
            return
        meta = self._col.find_one({"_id": META_ID})
        if meta is None:
            self._sort_keys = []
            self._count = 0
        else:
            self._sort_keys = meta.get("sort_keys", [])
            self._count = meta.get("count", len(self._sort_keys))
        self._cache_loaded_at = now
```

### Pattern 4: Redis Bounds-Check Elimination
**What:** Skip facade's `len()` call since Lua scripts already do LLEN+bounds internally
**When to use:** ASEIO/ObjectIO `__getitem__` for integer index on Redis backend
**Implementation note:** The redundancy is in `src/asebytes/io.py:235` where `n = len(self)` calls `LLEN` before the Lua script also calls `LLEN`. The fix should be at the facade level -- catch `IndexError` from the Lua script instead of pre-checking bounds. This is a change to the view/facade layer, not the Redis backend itself.

### Anti-Patterns to Avoid
- **Pre-checking bounds then checking again in Lua:** This is the current pattern. The Lua script already returns `redis.error_reply('IndexError')` for out-of-bounds access. Do not duplicate this check.
- **Caching backend data permanently:** Per project rules, NEVER cache backend data. The MongoDB TTL cache is for metadata (sort_keys), not row data, and must have a finite TTL.
- **Using lemat/HuggingFace data:** Violates TEST-06. All data must be synthetic.
- **Modifying H5MD backend:** H5MD follows the H5MD 1.1 spec. Only native asebytes formats (.h5/.h5p/.zarr/.zarrp) get optimizations.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Benchmark timing | Custom time.perf_counter loops | pytest-benchmark's `benchmark()` callable | Handles warmup, rounds, outlier detection, statistics, JSON storage |
| Benchmark comparison | Manual JSON diff scripts | `--benchmark-compare` flag | Built-in table comparison with color coding |
| Periodic structures | Manual position/cell construction | molify.pack or ase.build.bulk | Correct geometry, proper PBC handling |
| HDF5 chunk cache | Custom read-ahead buffer | h5py rdcc_nbytes + rdcc_nslots params | HDF5 library handles cache eviction, chunk mapping |

**Key insight:** pytest-benchmark already handles all the hard parts of micro-benchmarking (warmup, statistical stability, outlier rejection). The existing suite already uses it correctly. Focus implementation effort on data generation and optimizations, not benchmark infrastructure.

## Common Pitfalls

### Pitfall 1: molify.pack Requires packmol Executable
**What goes wrong:** `molify.pack()` shells out to `packmol` binary which may not be installed
**Why it happens:** packmol is an external Fortran program, not a Python package
**How to avoid:** Use `ase.build.bulk()` with supercell multiplication as a fallback for generating periodic structures. A Cu FCC 3x3x3 supercell gives 108 atoms with proper PBC. Or install packmol via Julia: `juliaup add 1.11 && julia -e 'using Pkg; Pkg.add("Packmol")'`
**Warning signs:** `FileNotFoundError: packmol` during fixture setup

### Pitfall 2: Session-Scoped Fixtures with tmp_path
**What goes wrong:** `tmp_path` is function-scoped, cannot be used in session-scoped fixtures
**Why it happens:** pytest fixture scope mismatch
**How to avoid:** Use `tmp_path_factory.mktemp()` for session-scoped fixtures, or generate data in memory (list[Atoms]) without writing to disk
**Warning signs:** `ScopeMismatch` error from pytest

### Pitfall 3: MongoDB/Redis Unavailability During Benchmarks
**What goes wrong:** Benchmarks fail hard when network services are unavailable
**Why it happens:** Services may not be running locally
**How to avoid:** Use `pytest.importorskip` or connection-check skip for benchmark fixtures. The benchmark marker already excludes them from default runs, so skipping when services are down is acceptable (unlike contract tests which must fail per TEST-09).
**Recommendation (Claude's discretion):** Skip benchmarks when services unavailable. Rationale: benchmarks are not correctness tests -- they measure performance. Running them with missing services produces no useful data. This is different from TEST-09 (contract tests must fail, not skip).

### Pitfall 4: HDF5 rdcc_nslots Must Be Prime
**What goes wrong:** Poor chunk cache utilization with non-prime slot counts
**Why it happens:** HDF5 chunk cache uses hash table with open addressing. Non-prime slot counts cause more collisions.
**How to avoid:** Use a prime number for rdcc_nslots. Standard choices: 10007, 50021, 100003. The value should be ~100x the number of chunks that will be accessed concurrently.
**Warning signs:** Random access benchmark shows no improvement despite large rdcc_nbytes

### Pitfall 5: Benchmark Noise from Setup Cost
**What goes wrong:** Benchmark measures data generation + IO instead of just IO
**Why it happens:** Setup code inside the benchmarked function
**How to avoid:** Current BenchDB pattern correctly pre-populates data outside the benchmark function. For write benchmarks, each iteration creates a new file (current pattern is correct).
**Warning signs:** Write benchmarks showing unusually high variance

### Pitfall 6: MongoDB `set()` Incorrectly Invalidates Cache
**What goes wrong:** `set()` calls `_invalidate_cache()` even though it doesn't change sort_keys
**Why it happens:** Overly conservative invalidation
**How to avoid:** Per RESULTS.md, fix `set()` to not invalidate the sort_keys cache since it only changes row data, not the ordering metadata. Only `extend()`, `delete()`, `insert()`, and `clear()` should invalidate.
**Warning signs:** TTL cache showing less improvement than expected because cache is invalidated by non-metadata operations

## Code Examples

### HDF5 rdcc_nslots Addition
```python
# src/asebytes/columnar/_store.py -- HDF5Store.__init__
def __init__(
    self,
    path: str | Path | None = None,
    group: str = "default",
    *,
    readonly: bool = False,
    file_handle: Any = None,
    compression: str | None = "gzip",
    compression_opts: int | None = None,
    chunk_frames: int = 64,
    rdcc_nbytes: int = 64 * 1024 * 1024,
    rdcc_nslots: int = 10007,  # NEW: prime number for hash table
):
    ...
    if file_handle is None and path is None:
        ...
    if file_handle is not None:
        ...
    else:
        mode = "r" if readonly else "a"
        self._file = h5py.File(
            str(path), mode,
            rdcc_nbytes=rdcc_nbytes,
            rdcc_nslots=rdcc_nslots,  # NEW
        )
```

### MongoDB TTL Cache Implementation
```python
# src/asebytes/mongodb/_backend.py
import time

class MongoObjectBackend:
    def __init__(self, uri, database, group, cache_ttl=1.0):
        ...
        self._cache_loaded_at: float = 0.0
        self._cache_ttl: float = cache_ttl

    def _ensure_cache(self) -> None:
        now = time.monotonic()
        if (self._sort_keys is not None
                and (now - self._cache_loaded_at) < self._cache_ttl):
            return
        meta = self._col.find_one({"_id": META_ID})
        if meta is None:
            self._sort_keys = []
            self._count = 0
        else:
            self._sort_keys = meta.get("sort_keys", [])
            self._count = meta.get("count", len(self._sort_keys))
        self._cache_loaded_at = now

    def _invalidate_cache(self) -> None:
        self._sort_keys = None
        self._count = None
        self._cache_loaded_at = 0.0  # Force re-fetch on next _ensure_cache

    def set(self, index, data):
        self._ensure_cache()
        # ... perform set ...
        # Do NOT call _invalidate_cache() -- set() doesn't change sort_keys
```

### Redis Bounds-Check Elimination
```python
# The fix is in the facade layer (io.py / _object_io.py / _blob_io.py)
# Currently __getitem__ does:
#   n = len(self)        # RT1: LLEN for Redis
#   row = self._read_row(index)  # RT2: Lua GET (which also does LLEN)

# Proposed: for backends whose get() does its own bounds checking,
# skip the len() pre-check and catch IndexError from get() directly.
# The Lua scripts already raise redis.error_reply('IndexError').
```

### Benchmark Data Generation with Full Properties
```python
def _attach_full_properties(frames: list[ase.Atoms], seed: int = 42) -> None:
    """Attach calculator results, constraints, custom info/arrays to frames."""
    rng = np.random.RandomState(seed)
    for i, atoms in enumerate(frames):
        n = len(atoms)
        # Calculator results
        atoms.calc = SinglePointCalculator(atoms)
        atoms.calc.results = {
            "energy": float(-i * 0.1),
            "forces": rng.randn(n, 3) * 0.01,
            "stress": rng.randn(6) * 0.001,
        }
        # Custom info
        atoms.info["step"] = i
        atoms.info["label"] = f"frame_{i}"
        # Custom arrays
        atoms.new_array("charges", rng.randn(n))
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| lemat HuggingFace dataset | molify synthetic generation | Phase 4 | No auth wall, reproducible, configurable sizes |
| Always-fetch MongoDB metadata | TTL-cached metadata | Phase 4 | 3.5x single-read speedup |
| 2-RT Redis (LLEN + Lua) | 1-RT Redis (Lua only) | Phase 4 | 1.9x single-read speedup |
| rdcc_nbytes only | rdcc_nbytes + rdcc_nslots | Phase 4 | Better HDF5 chunk cache utilization |

**Deprecated/outdated:**
- lemat dataset: Depends on HuggingFace authentication, violates TEST-06. Being removed.
- `benchmarks/` top-level directory: Ad-hoc scripts. Official suite lives in `tests/benchmarks/`.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-benchmark 5.2.1 |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `uv run pytest tests/benchmarks/ -m benchmark --benchmark-only -x` |
| Full suite command | `uv run pytest tests/benchmarks/ -m benchmark --benchmark-enable` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TEST-05 | Benchmark suite with synthetic data | benchmark | `uv run pytest tests/benchmarks/ -m benchmark --benchmark-enable -x` | Partial (lemat needs replacing) |
| TEST-07 | All operations x all backends x multiple sizes | benchmark | `uv run pytest tests/benchmarks/ -m benchmark --benchmark-enable` | Partial (single size currently) |
| PERF-01 | HDF5 rdcc_nslots improvement | benchmark | `uv run pytest tests/benchmarks/test_bench_random_access.py -m benchmark --benchmark-enable -k h5md` | File exists, need before/after comparison |
| PERF-02 | MongoDB TTL speedup | benchmark | `uv run pytest tests/benchmarks/test_bench_read.py -m benchmark --benchmark-enable -k mongodb` | File exists, need before/after comparison |
| PERF-03 | Redis Lua bounds speedup | benchmark | `uv run pytest tests/benchmarks/test_bench_read.py -m benchmark --benchmark-enable -k redis` | File exists, need before/after comparison |
| PERF-04 | Baselines recorded | manual | `--benchmark-save=baseline` then `--benchmark-compare` | No saved baselines yet |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/ -x -m "not benchmark"` (contract tests only)
- **Per wave merge:** `uv run pytest tests/benchmarks/ -m benchmark --benchmark-enable`
- **Phase gate:** Contract tests green + benchmark baselines saved

### Wave 0 Gaps
- [ ] Replace `lemat` fixture in `tests/conftest.py` with molify/ase.build periodic data
- [ ] Add frame-count parametrization to `tests/benchmarks/conftest.py` DATASETS
- [ ] Add `_attach_full_properties` helper for consistent data generation
- [ ] Verify `--benchmark-save` creates `.benchmarks/` directory correctly

## Open Questions

1. **packmol availability in CI**
   - What we know: molify.pack requires packmol binary. It exists in another venv locally.
   - What's unclear: Whether CI has packmol installed or if it needs to be added to CI setup.
   - Recommendation: Use `ase.build.bulk()` with supercell as primary method for periodic structures (no external dependency). Reserve molify.pack for cases where molecular packing specifically matters.

2. **Exact rdcc_nslots value**
   - What we know: Must be prime. Common values: 10007, 50021. HDF5 docs recommend ~100x number of chunks.
   - What's unclear: Optimal value depends on dataset chunk layout.
   - Recommendation: Start with 10007 (standard h5py recommendation), benchmark, adjust if needed. This is marked as Claude's discretion.

3. **Memory backend benchmarks**
   - What we know: CONTEXT says "Cover ALL backends" including Memory.
   - What's unclear: Existing benchmarks don't include memory backend fixtures.
   - Recommendation: Add `bench_memory` fixture. Memory backend is trivially fast but useful as a baseline reference.

## Sources

### Primary (HIGH confidence)
- Existing codebase: `tests/benchmarks/` (5 files + conftest.py) -- full working benchmark suite
- Existing codebase: `benchmarks/proposals/RESULTS.md` -- proven optimization speedups
- Existing codebase: `src/asebytes/columnar/_store.py:83` -- HDF5Store constructor with rdcc_nbytes
- Existing codebase: `src/asebytes/mongodb/_backend.py` -- MongoObjectBackend with _ensure_cache
- Existing codebase: `src/asebytes/redis/_lua.py` -- Lua scripts with built-in bounds checking
- Existing codebase: `src/asebytes/io.py:235` -- facade len() call before get()
- pyproject.toml:70 -- pytest config with `addopts = ["-m", "not benchmark"]`

### Secondary (MEDIUM confidence)
- h5py docs: rdcc_nslots is a standard h5py.File parameter for chunk cache hash table size
- HDF5 docs: Prime number recommended for rdcc_nslots to reduce hash collisions

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already installed and in use
- Architecture: HIGH -- existing benchmark suite provides clear patterns, optimizations are well-documented in proposals
- Pitfalls: HIGH -- based on direct code inspection and proposal results
- Optimizations: HIGH -- all three have proven speedup numbers from ad-hoc benchmarks

**Research date:** 2026-03-06
**Valid until:** 2026-04-06 (stable domain, project-specific findings)
