# Domain Pitfalls

**Domain:** HDF5/Zarr columnar storage backend refactoring, test restructuring, performance optimization
**Researched:** 2026-03-06

## Critical Pitfalls

Mistakes that cause rewrites or major issues.

### Pitfall 1: Metadata Cache Desync After Backend Split

**What goes wrong:** When splitting `ColumnarBackend` into separate padded and ragged variants, the internal metadata caches (`_n_frames`, `_columns`, `_per_atom_cols`, `_offsets_cache`, `_lengths_cache`, `_known_arrays`, `_array_shapes`) get duplicated across two classes. A bug in one variant's `_discover()` or `_update_attrs()` goes unnoticed because tests only exercise the other variant. Metadata stored in HDF5/Zarr group attributes (`n_frames`, `columns`, `per_atom_columns`) drifts from the actual array contents.

**Why it happens:** The current `ColumnarBackend` has ~25 lines of metadata cache management in `_discover()` and `_update_attrs()`. When duplicated into two backends, the invariants diverge silently. The ragged backend has `_offsets_cache`/`_lengths_cache` that the padded backend does not need, but both need `_n_frames` and `_columns` to stay in sync with on-disk state.

**Consequences:** Corrupted reads: wrong number of frames returned, missing columns, index-out-of-bounds on valid indices. Worst case: silent data corruption where `_offsets_cache` points to wrong flat-array positions.

**Prevention:**
- Extract a shared `ColumnarMetadata` mixin or base class that owns `_n_frames`, `_columns`, `_discover()`, and `_update_attrs()`. Both padded and ragged backends inherit this without reimplementing.
- Add an invariant assertion at the end of every `extend()` and `set()`: `assert self._n_frames == self._store.get_attrs().get("n_frames", 0)`, enabled during tests.
- Write a single parametrized "metadata consistency" test that does extend/set/update/clear and checks that `_discover()` after each operation produces identical caches.

**Detection:** Tests that do `extend()` followed by `len()` return wrong values. `get()` raises `IndexError` on the last valid index.

**Phase:** Backend splitting phase. Address before any new test infrastructure.

---

### Pitfall 2: HDF5 Chunk Cache Thrashing on Random Access

**What goes wrong:** The HDF5 chunk cache (controlled by `rdcc_nbytes`, currently 64 MB) is per-file, not per-dataset. When reading multiple columns with different access patterns (e.g., `get_many` reads columns sequentially, each doing random access), chunks evicted by one column's read are needed by the next column's read. Performance degrades from O(1) to O(N) per element.

**Why it happens:** HDF5 uses a single hash-table-based chunk cache per file handle. The default cache holds `rdcc_nslots` (521) slots. With many columns and random-access patterns (fancy indexing), the number of active chunks exceeds cache capacity. This is documented as a [critical HDF5 performance issue](https://support.hdfgroup.org/documentation/hdf5/latest/improve_compressed_perf.html) -- a misconfigured cache caused a 1000x slowdown in HDF Group benchmarks.

**Consequences:** `get_many()` with non-contiguous indices becomes catastrophically slow (100x+ slower than contiguous reads). Users who do `db[[0, 500, 1000]]` see multi-second waits on files that load in milliseconds with sequential access.

**Prevention:**
- In `get_many()`, the current implementation already sorts indices (`np.argsort(checked)`) -- keep this.
- Set `rdcc_nslots` to a prime number >= 100 * number_of_datasets (HDF Group recommendation). Current code only sets `rdcc_nbytes` but not `rdcc_nslots`.
- For the ragged backend: offset+flat layout means per-atom columns are always accessed with contiguous slices (good). But scalar columns still use fancy indexing -- consider reading contiguous ranges and discarding unwanted rows instead.
- Benchmark random vs. sequential access patterns in the performance suite. If random access is >10x slower, it is a chunk cache problem.

**Detection:** Benchmarks show non-linear scaling of `get_many()` time with number of indices. Random-access reads are orders of magnitude slower than sequential reads of the same data volume.

**Phase:** Performance optimization phase. Must be measured before and after any chunking changes.

---

### Pitfall 3: Duplicated Postprocessing Logic Across Backends

**What goes wrong:** The `_postprocess()` method contains ~70 lines of type-dependent deserialization (NaN-to-None, JSON string parsing, numpy scalar unwrapping, zarr v3 StringDType handling). This logic is duplicated nearly identically in `ColumnarBackend._postprocess()`, `ZarrBackend._postprocess()`, and `H5MDBackend._postprocess()` (with minor variations). When splitting backends further, the duplication multiplies. A bug fix in one copy gets missed in others.

**Why it happens:** Each backend was developed semi-independently. The `_postprocess()` method looks simple enough to copy-paste, but the edge cases (0-d StringDType arrays, all-NaN detection, bytes vs. str decoding) are subtle and backend-specific variations creep in.

**Consequences:** Inconsistent behavior across backends: the same data round-trips correctly through HDF5 but produces wrong types through Zarr (or vice versa). Users discover this only after switching backends in production.

**Prevention:**
- Extract `_postprocess()` into `_columnar.py` (or a new `_postprocess.py`) as a standalone function. Each backend calls it with a flag for backend-specific quirks (e.g., `zarr_string_dtype=True`).
- Write a parametrized round-trip test that checks type identity (not just value equality) of every output: `assert type(out["calc.energy"]) is float`, `assert isinstance(out["arrays.positions"], np.ndarray)`.
- The `_serialize_value()` / `_prepare_scalar_column()` methods have the same duplication problem -- extract those too.

**Detection:** Type-sensitive assertions in round-trip tests (e.g., `int` vs. `np.int64`, `list` vs. `np.ndarray`). A test that stores `{"key": [1, 2, 3]}` and checks `isinstance(result["key"], list)` across all backends.

**Phase:** Declutter/abstraction phase. Must happen before backend split to avoid quadrupling the duplication.

---

### Pitfall 4: Zarr v3 API Surface Instability

**What goes wrong:** The codebase uses zarr-python v3 APIs (`zarr.codecs.BloscCodec`, `zarr.codecs.BloscShuffle`, `zarr.open_group`, `create_array` with `compressors=` kwarg). Zarr v3 has been releasing breaking changes rapidly (v3.0.0 through v3.1.3+ in under a year). Code that works on 3.0.x breaks on 3.1.x because keyword names change (`compressor` vs `compressors`), codec constructors change, and store APIs change.

**Why it happens:** Zarr v3 was a ground-up rewrite. The [migration guide](https://zarr.readthedocs.io/en/stable/user-guide/v3_migration/) documents dozens of breaking changes. The project is still stabilizing, with multiple releases in 2025 fixing v3 migration issues ([issue #2689](https://github.com/zarr-developers/zarr-python/issues/2689)).

**Consequences:** CI breaks after `uv sync` pulls a new zarr minor version. Debugging zarr API changes is time-consuming because error messages are often generic (`TypeError: unexpected keyword argument`).

**Prevention:**
- Pin zarr to a specific minor version range in `pyproject.toml` (e.g., `zarr>=3.1,<3.2`).
- Isolate all zarr API calls inside `ZarrStore` (already done). Never use zarr APIs outside this class.
- Add a zarr version smoke test: `import zarr; assert zarr.__version__.startswith("3.")`.
- Before upgrading zarr, run the full test suite against the new version in a branch.

**Detection:** CI failures after dependency updates. `AttributeError` or `TypeError` in `ZarrStore` methods.

**Phase:** All phases. Pin immediately before any refactoring begins.

---

### Pitfall 5: Registry Collision When Adding File Extension Variants

**What goes wrong:** The plan is to register `.h5-padded`, `.h5-ragged`, `.zarr-padded`, `.zarr-ragged` as separate registry patterns. The glob-based registry (`fnmatch.fnmatch`) matches `*.h5` against `data.h5-ragged` because `fnmatch` treats `-ragged` as part of the match. Existing `*.h5` patterns silently intercept the new extensions.

**Why it happens:** `fnmatch.fnmatch("data.h5-ragged", "*.h5")` returns `False` (good), but `fnmatch.fnmatch("data.h5-ragged", "*.h5*")` returns `True`. If anyone introduces a wildcard pattern like `*.h5*` or if the extension format changes, the registry silently routes to the wrong backend. The registry uses first-match semantics (`candidates[0]`), so ordering matters.

**Consequences:** Wrong backend instantiated silently. Data written in ragged format but read with padded backend (or vice versa), producing corrupt output without errors.

**Prevention:**
- Use exact suffix matching instead of glob for the new extensions. Add a `Path(path).suffixes` check or use more specific patterns like `*.h5-ragged` (not `*.h5*`).
- Add registry order tests: `assert resolve_backend("data.h5-ragged", layer="object") is RaggedH5Backend`.
- Add a "no ambiguity" test: for every registered pattern pair, verify no path can match both.
- Put more-specific patterns BEFORE less-specific ones in `_REGISTRY` (`.h5-ragged` before `.h5`).

**Detection:** A test that creates a file with each new extension and asserts the correct backend class is returned by `resolve_backend()`.

**Phase:** Backend splitting phase. Design the extension scheme before implementing the backends.

## Moderate Pitfalls

### Pitfall 6: h5py Dataset Reference Caching Violates "Never Cache" Rule

**What goes wrong:** `HDF5Store._ds_cache` caches `h5py.Dataset` references (not data). This seems safe because a Dataset reference is just a handle. But if another process truncates or restructures the HDF5 file, the cached Dataset reference can point to stale metadata (shape, dtype). Reads return wrong shapes or crash with `OSError`.

**Why it happens:** The project rule is "NEVER cache backend data -- another client can modify the data at any time." Dataset references are technically handles, not data, but they cache the dataset's shape internally. The `ColumnarBackend` also caches `_array_shapes` and `_offsets_cache`, which are actual data.

**Prevention:**
- Distinguish between "handle caching" (acceptable within a single open file session) and "data caching" (forbidden). Document this distinction.
- For `_offsets_cache`/`_lengths_cache` in `ColumnarBackend`: these are full numpy array copies of on-disk data, violating the cache rule. Either re-read on every access (slow) or accept the tradeoff with explicit documentation that multi-client concurrent writes are not supported for offset arrays.
- Add a `refresh()` method that re-runs `_discover()` for users who need to pick up external changes.

**Detection:** Integration test: write with one backend instance, modify file externally, read with the same instance. If stale data is returned, the cache is a problem.

**Phase:** Declutter phase. Decide and document the caching policy before proceeding.

---

### Pitfall 7: Test Suite Explosion from Cartesian Parametrization

**What goes wrong:** The plan is to parametrize tests across all backends (LMDB, HDF5-padded, HDF5-ragged, Zarr-padded, Zarr-ragged, H5MD, Memory) x all facades (BlobIO, ObjectIO, ASEIO) x all data fixtures (s22, ethanol, edge cases). The Cartesian product creates thousands of test cases. CI takes 30+ minutes. Developers stop running the full suite locally.

**Why it happens:** Parametrization is additive by default. Each `@pytest.fixture(params=...)` multiplies the total test count. With 7 backends, 3 facades, and 10 fixtures, a single test function generates 210 cases.

**Prevention:**
- Layer the test pyramid: unit tests (per-backend, no facade), integration tests (per-facade with 1-2 backends), and a small "full matrix" smoke test.
- Use `pytest.mark.slow` for the full matrix and run it only in CI, not locally.
- Group backends by capability (appendable, insertable, read-only) and test each capability group once, not each backend individually.
- Use `indirect` parametrization with factory fixtures (the `conftest.py` already does this partially with `uni_blob_backend` and `uni_object_backend` -- extend this pattern).

**Detection:** CI time exceeds 10 minutes. Test count exceeds 2000. Developers report skipping tests locally.

**Phase:** Test restructuring phase.

---

### Pitfall 8: Ragged-to-Padded Migration Breaks Per-Atom Column Detection

**What goes wrong:** The `_is_per_atom()` heuristic determines whether a column is per-atom by checking if `val.shape[0] == n_atoms` for every row. When splitting into padded vs. ragged backends, this heuristic is no longer needed for the ragged backend (all per-atom columns use offset+flat) but is critical for the padded backend. If the heuristic is removed prematurely from the shared code or left in the wrong backend, columns get misclassified.

**Why it happens:** The padded backend stores per-atom data as `(n_frames, max_atoms, ...)` with NaN padding. The ragged backend stores it as flat `(total_atoms, ...)` with offsets. The classification matters because it determines the storage layout. A column classified as "scalar" in the padded backend gets shape `(n_frames, ...)` instead of `(n_frames, max_atoms, ...)`, silently truncating data.

**Consequences:** Data loss: per-atom arrays stored as scalars lose all but the first element. This is not caught by simple length checks because `_n_frames` is still correct.

**Prevention:**
- In the padded backend: make per-atom classification explicit at write time (require the caller or schema to declare it). Do not rely on heuristic shape matching.
- In the ragged backend: the offset+flat layout inherently handles variable-length data, so classification is less error-prone.
- Test with a 3-atom and a 3-frame dataset (where `n_atoms == n_frames == 3`) to verify the heuristic does not misclassify.

**Detection:** Round-trip test with `n_atoms == n_frames` (e.g., 3 frames of 3-atom molecules). If `arrays.positions` comes back as `(3, 3)` instead of `(3, 3, 3)`, it was misclassified.

**Phase:** Backend splitting phase. Design the API contract before implementation.

---

### Pitfall 9: H5MD Compliance Tested Against Wrong Spec Version

**What goes wrong:** The H5MD spec has multiple versions (1.0, 1.1) and znh5md adds non-standard extensions (NaN padding for variable particle count, per-frame PBC). Tests written against the "H5MD spec" may test features that are znh5md extensions, not standard H5MD. Or they may test H5MD 1.0 behavior that was changed in 1.1.

**Why it happens:** The H5MD backend docstring says "Produces files compatible with znh5md and standard H5MD readers" but these are sometimes contradictory goals. znh5md's NaN-padding approach is not part of the H5MD spec -- it is a convention.

**Prevention:**
- Separate test categories: "H5MD 1.1 spec compliance" and "znh5md interop". Label each test clearly.
- For spec compliance: generate a reference file with an independent H5MD writer (e.g., pyh5md) and verify asebytes can read it.
- For znh5md interop: generate a reference file with `znh5md>=0.4.8` and verify asebytes can read it. Store these as small test fixtures in `tests/data/`.
- The `_PostProc` enum dispatch in `H5MDBackend` has 7 code paths -- each needs a specific test.

**Detection:** A test that opens a genuine znh5md-written file and verifies all fields round-trip correctly. If this test does not exist, H5MD compliance is untested.

**Phase:** H5MD compliance phase.

---

### Pitfall 10: Performance Benchmarks Measuring Setup, Not I/O

**What goes wrong:** Benchmarks that create `ColumnarBackend("file.h5")` inside the timed region measure file open time, HDF5 metadata parsing, and `_discover()` overhead in addition to actual read/write time. Results are misleading -- "read performance" includes 50ms of file open overhead on a 1ms read.

**Why it happens:** HDF5 file opening is expensive (especially with gzip-compressed datasets). `_discover()` reads all array shapes and loads `_offsets`/`_lengths` into memory. For small benchmarks (few rows), setup dominates.

**Prevention:**
- Separate benchmarks into "cold start" (includes file open) and "warm path" (pre-opened backend).
- Use `pytest-benchmark` or `timeit` with explicit setup phases.
- Benchmark at multiple dataset sizes: 10, 100, 1000, 10000 rows. Report per-row time to detect non-linear scaling.
- Benchmark `get_many()` with both contiguous and random index patterns.

**Detection:** Benchmark results where read time does not scale with dataset size (constant overhead dominates).

**Phase:** Performance optimization phase. Establish benchmark methodology before measuring.

## Minor Pitfalls

### Pitfall 11: String Serialization Asymmetry (JSON Encode, Raw Decode)

**What goes wrong:** `_serialize_value()` wraps dicts/lists in `json.dumps()`. `_postprocess()` tries `json.loads()` on every string. But if a user stores a plain string like `"hello"`, it gets stored as `"\"hello\""` (JSON-encoded) and decoded back to `"hello"` -- this works. But if a legacy file has raw strings (not JSON-encoded), `json.loads("hello")` raises `JSONDecodeError`, caught by the except clause, and returns the raw string. This asymmetry means old and new files behave differently.

**Prevention:** Decide on a string storage convention and document it. Either always JSON-encode (and always JSON-decode), or use a prefix/marker to distinguish JSON from raw strings.

**Phase:** Declutter phase.

---

### Pitfall 12: `concat_varying()` Memory Explosion on Mixed-Size Molecules

**What goes wrong:** `concat_varying()` pads all arrays to the maximum shape. If one frame has 1000 atoms and the rest have 3 atoms, every frame gets padded to shape `(1000, 3)`. For 10000 frames, this creates a 240 MB array instead of ~1 MB of actual data.

**Prevention:** This is exactly why the ragged (offset+flat) layout exists. Ensure the padded backend warns or errors when the padding ratio exceeds a threshold (e.g., >10x waste). The ragged backend should be the default recommendation for variable-size molecular data.

**Phase:** Backend splitting phase. Document guidance on when to use padded vs. ragged.

---

### Pitfall 13: Async `SyncToAsyncAdapter` Starves Thread Pool on Bulk Reads

**What goes wrong:** `SyncToAsyncAdapter` wraps every sync call in `asyncio.to_thread()`. For `get_many()` with 1000 indices, this runs the entire bulk read in a single thread, blocking the default thread pool executor (8 threads). Other async tasks cannot proceed.

**Prevention:** Keep bulk operations as single `to_thread()` calls (do not parallelize individual reads). But document that the async adapter is for convenience, not performance -- true async requires native async backends (MongoDB, Redis).

**Phase:** Async test coverage phase.

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Backend splitting | Registry collision on new extensions (#5) | Design extension scheme first, write registry tests before implementing backends |
| Backend splitting | Metadata cache desync (#1) | Extract shared base class before splitting |
| Backend splitting | Per-atom misclassification (#8) | Test with `n_atoms == n_frames` edge case |
| Declutter/abstraction | Breaking postprocess behavior (#3) | Extract shared function, add type-identity tests |
| Declutter/abstraction | String serialization asymmetry (#11) | Decide convention, document it |
| H5MD compliance | Wrong spec version (#9) | Separate spec vs. znh5md interop tests |
| Performance optimization | Chunk cache thrashing (#2) | Benchmark random access specifically |
| Performance optimization | Benchmarks measuring setup (#10) | Separate cold-start from warm-path benchmarks |
| Test restructuring | Test explosion (#7) | Layer the test pyramid, mark slow tests |
| Zarr maintenance | API breakage on version bump (#4) | Pin zarr version immediately |

## Sources

- [HDF5 Chunk Cache Performance](https://support.hdfgroup.org/documentation/hdf5/latest/improve_compressed_perf.html) -- HDF Group documentation on chunk cache tuning, 1000x slowdown from misconfigured cache
- [HDF5 Chunking Guide](https://support.hdfgroup.org/documentation/hdf5-docs/advanced_topics/chunking_in_hdf5.html) -- official chunking best practices
- [Zarr v3 Migration Guide](https://zarr.readthedocs.io/en/stable/user-guide/v3_migration/) -- comprehensive list of breaking changes
- [Zarr v3 Migration Issues](https://github.com/zarr-developers/zarr-python/issues/2689) -- community-reported migration problems
- [h5py Thread Safety](https://docs.h5py.org/en/latest/threads.html) -- global lock behavior, concurrent access limitations
- [h5py Single Index Performance](https://github.com/h5py/h5py/issues/994) -- fancy indexing performance issues
- [NASA HDF5 Compression Pitfalls](https://ntrs.nasa.gov/api/citations/20180008456/downloads/20180008456.pdf) -- overcoming compression performance issues

---

*Pitfalls analysis: 2026-03-06*
