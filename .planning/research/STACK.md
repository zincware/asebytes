# Stack Research

**Domain:** High-performance HDF5/Zarr columnar storage abstraction with benchmarking and parametrized testing
**Researched:** 2026-03-06
**Confidence:** HIGH (core stack verified via PyPI/official docs; testing patterns verified via pytest docs)

## Recommended Stack

### Core Storage Libraries

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| h5py | >=3.12 | HDF5 read/write for columnar and H5MD backends | Mature, stable, only viable Python HDF5 binding. Current release 3.15.1 (Oct 2025). Keep floor at 3.12 to avoid pulling in ancient HDF5 C libs but no need to pin higher -- the API surface asebytes uses has been stable since 3.8. **Confidence: HIGH** |
| zarr | >=3.0 | Zarr v3 columnar storage | Already pinned correctly. Current release 3.1.5 (Nov 2025). Zarr v3 is a full rewrite with new chunk-sharding, async-native store layer, and Zarr v3 spec compliance. The v2->v3 migration was breaking but asebytes already targets v3, so no action needed. **Confidence: HIGH** |
| lmdb | >=1.6.0 | Embedded key-value blob backend | Current release 1.6.2. Extremely stable C library, rarely changes API. Bump floor from 1.7.5 (which doesn't exist on PyPI -- the actual latest is 1.6.2) to 1.6.0 to match reality. **Confidence: HIGH** |
| msgpack | >=1.1.0 | Binary serialization of Atoms dicts | Fast, compact, cross-language. Current 1.1.2. Outperforms JSON for decode-heavy workloads (~3x faster than json). Combined with msgpack-numpy for ndarray support. Keep -- no reason to switch. **Confidence: HIGH** |
| msgpack-numpy | >=0.4.8 | numpy ndarray packing into msgpack | Only viable msgpack+numpy bridge. Pin stays. **Confidence: HIGH** |

### Testing Stack

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| pytest | >=8.4.2 | Test runner | Current release 9.0.2 (early 2026). Keep floor at 8.4.2 for now; 9.0 has no breaking changes that affect asebytes. Upgrade when convenient. **Confidence: HIGH** |
| pytest-benchmark | >=5.2.1 | Performance benchmarking as pytest fixtures | Current release 5.2.3 (Nov 2025). Already in dev deps. The `benchmark` fixture approach is superior to the ad-hoc `time.perf_counter()` script in `benchmarks/bench_columnar.py`. Migrate benchmarks to pytest-benchmark fixtures for statistical rigor (warmup, rounds, min/max/mean/stddev). **Confidence: HIGH** |
| anyio | >=4.9 | Async test runner via built-in pytest plugin | Current release 4.12.1 (Jan 2026). Already a dependency. Use anyio's pytest plugin (`@pytest.mark.anyio`) rather than pytest-asyncio. Reasons: (1) asebytes uses `asyncio.to_thread` which is asyncio-native, anyio wraps this fine, (2) anyio's plugin is simpler -- no `asyncio_mode` config drama, (3) avoids the pytest-asyncio 1.0 migration headache with removed `event_loop` fixture. **Confidence: HIGH** |
| molify | >=0.0.1a0 | Synthetic molecular test data generation | Generates realistic ASE Atoms with conformers, calculators, constraints. Eliminates need for auth-gated datasets in CI. Already used in conftest.py. **Confidence: MEDIUM** (alpha package, but maintained by same team) |

### Benchmarking Infrastructure

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| pytest-benchmark | >=5.2.1 | Statistical microbenchmarks | Use `benchmark` fixture for per-operation timing. Group benchmarks with `@pytest.mark.benchmark(group="read")`. Store baselines with `--benchmark-save=baseline`. Compare with `--benchmark-compare`. **Confidence: HIGH** |
| pytest-codspeed | >=4.0 | CI performance regression detection (optional) | Drop-in replacement for pytest-benchmark API. Uses CPU simulation to eliminate CI noise. Free for open source. Add as optional CI enhancement, not hard dependency. **Confidence: MEDIUM** |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| uv | Package management, build, run | Mandatory per project constraints. Use `uv run pytest`, `uv sync`, `uv add`. |
| matplotlib | Benchmark visualization | Already in dev deps. Use for local perf analysis, not CI. |

## Installation

```bash
# Core (already in pyproject.toml)
uv add "ase>=3.26.0" "msgpack>=1.1.2" "msgpack-numpy>=0.4.8" "typing_extensions>=4.5.0"

# Storage backends (extras, already configured)
uv add --optional h5md "h5py>=3.12"
uv add --optional zarr "zarr>=3.0"
uv add --optional lmdb "lmdb>=1.6.0"

# Dev / testing
uv add --group dev "pytest>=8.4.2" "pytest-benchmark>=5.2.1" "anyio>=4.9" "molify>=0.0.1a0"

# Optional: CI perf regression
uv add --group dev "pytest-codspeed>=4.0"
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| msgpack + msgpack-numpy | pickle | Never for asebytes. Pickle is insecure, Python-only, and slower on decode. msgpack is cross-language and compact. |
| msgpack + msgpack-numpy | orjson | Only if you need JSON compatibility. orjson can't serialize numpy arrays natively. msgpack is ~30% smaller on wire. |
| anyio pytest plugin | pytest-asyncio | Only if you need Trio support or have a large existing pytest-asyncio codebase. For asebytes, anyio is already a dep and its plugin is simpler. |
| pytest-benchmark | asv (airspeed velocity) | Only for long-term historical tracking across git commits with HTML reports. Overkill for asebytes -- pytest-benchmark with `--benchmark-save` covers the need. |
| pytest-benchmark | ad-hoc time.perf_counter scripts | Never. The existing `benchmarks/bench_columnar.py` should be migrated to pytest-benchmark fixtures for statistical rigor, reproducibility, and CI integration. |
| h5py | pytables (tables) | Never for asebytes. pytables adds a proprietary layer over HDF5 that conflicts with H5MD compliance. h5py gives direct HDF5 access. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| pickle for serialization | Insecure (arbitrary code execution on load), Python-only, no cross-language interop | msgpack + msgpack-numpy |
| pytest-asyncio | Conflicts with anyio plugin in auto mode; 1.0 migration removed event_loop fixture; asebytes already depends on anyio | anyio's built-in pytest plugin (`@pytest.mark.anyio`) |
| zarr v2 API | Zarr v3 is a complete rewrite; v2 API is deprecated; asebytes already targets v3 | zarr >=3.0 |
| pytables / tables | Adds proprietary metadata layer; incompatible with H5MD spec; unnecessary abstraction over h5py | h5py directly |
| hypothesis (property-based testing) | Overkill for storage round-trip tests; ASE Atoms have complex invariants that make property-based generation extremely hard | Explicit parametrized fixtures with molify-generated data |
| pytest.mark.xfail | Explicitly banned by project. Masks bugs instead of fixing them. | Fix the bug or skip with clear reason |
| Backend data caching | Explicitly banned. Another client can modify data at any time. | Always read fresh from backend |

## Stack Patterns by Variant

**For parametrized backend testing:**
- Use `@pytest.fixture(params=[...])` with factory functions (already established in conftest.py with `uni_blob_backend` / `uni_object_backend`)
- Extend to cover padded vs ragged variants with separate param IDs
- Use `pytest.param(..., id="h5-ragged")` for clear test output
- Use `indirect=True` when fixture needs `tmp_path` injection

**For benchmark tests:**
- Use `@pytest.mark.benchmark` marker (already configured in pytest.ini)
- Use `benchmark` fixture from pytest-benchmark for per-operation timing
- Group related benchmarks: `@pytest.mark.benchmark(group="write")`
- Default addopts already excludes benchmarks (`-m "not benchmark"`)
- Run benchmarks explicitly: `uv run pytest -m benchmark --benchmark-only`

**For async tests:**
- Use `@pytest.mark.anyio` on async test functions
- Async fixtures: `@pytest.fixture` + `async def` (anyio plugin handles this)
- Mirror sync test structure: if `test_foo.py` exists, `test_async_foo.py` should test the same operations

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| h5py >=3.12 | Python 3.10-3.14, HDF5 1.12+ | Wheels bundle HDF5 C library |
| zarr >=3.0 | Python >=3.11 | Matches asebytes Python floor |
| lmdb >=1.6.0 | Python >=3.5 | Bundles LMDB C library |
| pytest-benchmark >=5.2.1 | pytest >=8.0 | Requires pytest 8+ for fixture protocol |
| anyio >=4.9 | Python >=3.9, pytest >=8.0 | Built-in pytest plugin since 4.x |
| msgpack >=1.1.0 | Python >=3.8 | C extension, fast |
| msgpack-numpy >=0.4.8 | msgpack >=1.0, numpy >=1.20 | Hooks into msgpack ext types |

## Version Pinning Strategy

**Floor pins (>=X.Y) for all dependencies.** Rationale:
- asebytes is a library, not an application -- tight pins cause dependency hell for consumers
- All storage backends are extras, so consumers only pull what they need
- Dev dependencies can be more aggressive since they don't affect consumers

**Exception:** `uv_build>=0.9.6,<0.10.0` in build-system is correctly ceiling-pinned because build backends can have breaking changes.

## Action Items from Stack Research

1. **Fix lmdb version floor:** `lmdb>=1.7.5` does not exist on PyPI. The latest is 1.6.2. Change to `lmdb>=1.6.0`.
2. **Migrate ad-hoc benchmarks:** Convert `benchmarks/bench_columnar.py` from raw `time.perf_counter()` to pytest-benchmark fixtures for statistical rigor.
3. **Standardize async testing:** Ensure all async tests use `@pytest.mark.anyio`, not a mix of approaches.
4. **Consider pytest-codspeed:** Add as optional CI enhancement for noise-free performance regression detection in GitHub Actions.
5. **Bump h5py floor:** From `>=3.8.0` to `>=3.12` to ensure modern HDF5 C library and avoid known bugs in older releases.

## Sources

- [h5py PyPI](https://pypi.org/project/h5py/) -- verified latest version 3.15.1, HIGH confidence
- [zarr PyPI](https://pypi.org/project/zarr/) -- verified latest version 3.1.5, HIGH confidence
- [zarr-python releases](https://github.com/zarr-developers/zarr-python/releases) -- version history, HIGH confidence
- [lmdb PyPI](https://pypi.org/project/lmdb/) -- verified latest version 1.6.2, HIGH confidence
- [pytest PyPI](https://pypi.org/project/pytest/) -- verified latest version 9.0.2, HIGH confidence
- [pytest-benchmark PyPI](https://pypi.org/project/pytest-benchmark/) -- verified latest version 5.2.3, HIGH confidence
- [pytest-benchmark docs](https://pytest-benchmark.readthedocs.io/) -- usage patterns, HIGH confidence
- [anyio PyPI](https://pypi.org/project/anyio/) -- verified latest version 4.12.1, HIGH confidence
- [anyio testing docs](https://anyio.readthedocs.io/en/stable/testing.html) -- pytest plugin usage, HIGH confidence
- [pytest-codspeed PyPI](https://pypi.org/project/pytest-codspeed/) -- verified latest version 4.2.0, MEDIUM confidence
- [pytest parametrize docs](https://docs.pytest.org/en/stable/how-to/parametrize.html) -- official patterns, HIGH confidence
- [msgspec benchmarks](https://jcristharif.com/msgspec/benchmarks.html) -- serialization performance comparison, MEDIUM confidence

---
*Stack research for: asebytes maintenance and performance overhaul*
*Researched: 2026-03-06*
