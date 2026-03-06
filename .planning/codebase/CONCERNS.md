# Codebase Concerns

**Analysis Date:** 2026-03-06

## Tech Debt

**Legacy ZarrBackend duplicates ColumnarBackend logic:**
- Issue: `src/asebytes/zarr/_backend.py` (831 lines) is an older NaN-padding-based Zarr backend that duplicates much of the logic now unified in `src/asebytes/columnar/_backend.py` (989 lines). Both implement `_is_per_atom()`, `_postprocess()`, `_serialize_value()`, `_prepare_column()`, and `_update_attrs()` with near-identical code. The ColumnarBackend with offset+flat layout supersedes the ZarrBackend's NaN-padding approach.
- Files: `src/asebytes/zarr/_backend.py`, `src/asebytes/columnar/_backend.py`
- Impact: Bug fixes or feature additions must be applied in multiple places. The registry routes `*.zarr` to ColumnarBackend (see `src/asebytes/_registry.py` line 39), so the old ZarrBackend is only used if instantiated directly. Users who import `ZarrBackend` get the legacy path.
- Fix approach: Deprecate and eventually remove `src/asebytes/zarr/_backend.py`. Ensure all users go through the registry (ColumnarBackend). The backward-compat alias `ZarrObjectBackend = ZarrBackend` at line 831 should redirect to ColumnarBackend.

**H5MD backend is the largest file at 1473 lines:**
- Issue: `src/asebytes/h5md/_backend.py` is a monolithic backend with complex NaN-padding logic, column classification, H5MD-specific mapping, and connectivity handling. It has its own `_is_per_atom()`, `_postprocess_typed()`, and dataset discovery that differ from both ColumnarBackend and ZarrBackend.
- Files: `src/asebytes/h5md/_backend.py`
- Impact: Maintaining three separate backends (H5MD, Zarr, Columnar) with overlapping but subtly different semantics is error-prone. The H5MD backend is registered for `*.h5md` while ColumnarBackend handles `*.h5`.
- Fix approach: Evaluate whether H5MD compatibility can be layered on top of ColumnarBackend or if it must remain separate due to the H5MD file format spec.

**Duplicated `_postprocess` logic across backends:**
- Issue: Three near-identical `_postprocess()` methods exist in `src/asebytes/zarr/_backend.py` (lines 490-560), `src/asebytes/columnar/_backend.py` (lines 907-978), and `src/asebytes/h5md/_backend.py` (via `_postprocess_typed`). All handle string decoding, NaN detection, JSON parsing, and numpy scalar conversion.
- Files: `src/asebytes/zarr/_backend.py`, `src/asebytes/columnar/_backend.py`, `src/asebytes/h5md/_backend.py`
- Impact: Inconsistencies in edge-case handling across backends. Any postprocessing fix must be applied three times.
- Fix approach: Extract shared postprocessing into `src/asebytes/_columnar.py` or a new `_postprocess.py` module. Each backend can call the shared function with backend-specific parameters.

**Two `# type: ignore` suppressions in backends:**
- Issue: Both `src/asebytes/zarr/_backend.py:265` and `src/asebytes/h5md/_backend.py:472` use `# type: ignore[return-value]` on `get_many()` return statements.
- Files: `src/asebytes/zarr/_backend.py`, `src/asebytes/h5md/_backend.py`
- Impact: Type safety is weakened. Likely caused by `list[dict | None]` vs `list[dict[str, Any] | None]` covariance.
- Fix approach: Narrow the return type annotation or restructure the deduplicated row mapping to satisfy the type checker.

**Duplicated `_is_per_atom` and `_NEVER_PER_ATOM`:**
- Issue: The per-atom classification heuristic is copy-pasted across `src/asebytes/zarr/_backend.py` (lines 567-598), `src/asebytes/columnar/_backend.py` (lines 26, 704-732), and `src/asebytes/h5md/_backend.py` (line 1164+). All use the same logic: check if first dimension matches `arrays.positions` or `arrays.numbers` length.
- Files: `src/asebytes/zarr/_backend.py`, `src/asebytes/columnar/_backend.py`, `src/asebytes/h5md/_backend.py`
- Impact: Three copies to maintain. A false positive or false negative in classification silently corrupts data storage.
- Fix approach: Move to `src/asebytes/_columnar.py` as a standalone function.

## Known Bugs

**No known bugs identified from code analysis.** The codebase has extensive test coverage (80+ test files, 23k+ lines of tests).

## Security Considerations

**LMDB map_size default is 10GB:**
- Risk: Default `map_size=10737418240` in `src/asebytes/lmdb/_blob_backend.py` (line 41) could allow disk exhaustion if data is written without limits.
- Files: `src/asebytes/lmdb/_blob_backend.py`
- Current mitigation: None. The parameter is user-configurable.
- Recommendations: Document the map_size parameter prominently. Consider a warning when approaching the limit.

**Registry error message suggests `pip install` instead of `uv add`:**
- Risk: Not a security issue, but `src/asebytes/_registry.py` line 97 and `src/asebytes/__init__.py` line 206 both suggest `pip install asebytes[{hint}]` in error messages. This is inconsistent with the project's uv-based tooling.
- Files: `src/asebytes/_registry.py`, `src/asebytes/__init__.py`
- Current mitigation: None.
- Recommendations: Change to a generic message or use `pip install` since end users may not use uv.

**Broad `except Exception` swallows errors:**
- Risk: Several locations use bare `except Exception` or `except:` + `pass`, hiding real failures:
  - `src/asebytes/io.py:135` - cache write silently fails
  - `src/asebytes/mongodb/_backend.py:36` - connection error silenced
  - `src/asebytes/columnar/_store.py:218` - HDF5 list_groups error silenced
  - `src/asebytes/_columnar.py:35` - version retrieval error silenced
- Files: See above
- Current mitigation: None.
- Recommendations: Use specific exception types. For cache writes, at minimum log the failure.

## Performance Bottlenecks

**ColumnarBackend caches offsets/lengths in memory but re-discovers on every `extend()`:**
- Problem: After every `extend()` call, `_discover()` is called (line 517 of `src/asebytes/columnar/_backend.py`), which re-reads all array metadata from the store. For incremental appends this is O(n_columns) I/O per extend.
- Files: `src/asebytes/columnar/_backend.py` lines 96, 102-122, 517
- Cause: `_discover()` re-reads `_offsets` and `_lengths` arrays in full every time. For large datasets, these arrays grow proportionally.
- Improvement path: After `extend()`, update the caches incrementally by appending the new offsets/lengths to the existing cache arrays in memory instead of re-reading from store.

**LMDB cache is invalidated on every single write:**
- Problem: Every `set()`, `update()`, `extend()`, and `set_column()` call in `src/asebytes/lmdb/_blob_backend.py` ends with `self._invalidate_cache()` (e.g., lines 397, 441, 498, 578, 604, 628, 646), forcing a full cache rebuild on the next read.
- Files: `src/asebytes/lmdb/_blob_backend.py`
- Cause: Conservative cache invalidation strategy. The cache (blocks, schema, count) could be updated in-place during writes instead of invalidated.
- Improvement path: After successful writes, update `_blocks`, `_schema_cache`, `_block_sizes`, and `_count_cache` in-place rather than setting them all to `None`. The data is already computed during the write transaction.

**ConcatView `_locate()` is O(n_sources) per index:**
- Problem: `_locate()` in `src/asebytes/_concat.py` (lines 49-57) performs a linear scan through all sources for every index lookup. For `_read_rows()` with many indices across many sources, this is O(n_indices * n_sources).
- Files: `src/asebytes/_concat.py`
- Cause: No precomputed cumulative offset array.
- Improvement path: Precompute a cumulative length array in `__init__` and use `np.searchsorted` for O(log n) lookups.

**`dict_to_atoms` fast path relies on ASE private attributes:**
- Problem: The fast path in `src/asebytes/_convert.py` (lines 97-111) sets `atoms._cellobj`, `atoms._pbc`, `atoms._celldisp`, `atoms._calc` directly, bypassing ASE's public API. This gives ~6x speedup but breaks if ASE changes its internals.
- Files: `src/asebytes/_convert.py`
- Cause: ASE's `Atoms.__init__` does unnecessary copies and validation for deserialization use cases.
- Improvement path: Pin to tested ASE versions. Add a regression test that verifies the fast path produces identical results to the slow path. Consider contributing a `from_dict()` classmethod upstream.

## Fragile Areas

**Per-atom column classification heuristic:**
- Files: `src/asebytes/columnar/_backend.py` lines 704-732, `src/asebytes/zarr/_backend.py` lines 569-598
- Why fragile: The `_is_per_atom()` heuristic determines whether a column is stored in flat ragged layout (per-atom) or as a regular array. It checks if `array.shape[0] == n_atoms` for each frame. This can produce false positives for columns that happen to have the same first dimension as the atom count (e.g., a 3-element array when there are 3 atoms). The `_NEVER_PER_ATOM = frozenset({"cell", "pbc"})` safelist only covers two known cases.
- Safe modification: Always add new known scalar columns to `_NEVER_PER_ATOM`. If adding new array types, test with atom counts that could collide with array dimensions.
- Test coverage: Covered by `tests/test_columnar_backend.py`, `tests/test_column_dimensionality.py`, but edge cases with coincidental dimension matches may not be covered.

**`dict_to_atoms` fast path coupling to ASE internals:**
- Files: `src/asebytes/_convert.py` lines 97-111, 129-139
- Why fragile: Uses `ase.Atoms.__new__()` and directly sets private attributes (`_cellobj`, `_pbc`, `_celldisp`, `_calc`). Also uses `SinglePointCalculator.__new__()` with manual attribute initialization. Any ASE version that adds, removes, or renames an internal attribute will cause silent data corruption or AttributeError.
- Safe modification: Always test against the minimum supported ASE version (3.26.0) and the latest release. The `fast=False` path provides a safe fallback.
- Test coverage: `tests/test_convert.py`, `tests/test_copy_semantics.py`

**Columnar backend metadata caching violates "never cache backend data" rule:**
- Files: `src/asebytes/columnar/_backend.py` lines 92-122
- Why fragile: The backend caches `_n_frames`, `_columns`, `_per_atom_cols`, `_known_arrays`, `_array_shapes`, `_offsets_cache`, and `_lengths_cache` in memory. The MEMORY.md project rule states "NEVER cache backend data -- another client can modify the data at any time." If another process writes to the same HDF5/Zarr file, the cached metadata becomes stale. The `_discover()` method is only called on `__init__` and after `extend()`.
- Safe modification: For single-writer scenarios, the cache is correct. For multi-writer, add a `refresh()` method or re-discover on every read.
- Test coverage: Single-process tests pass, but multi-process scenarios are untested.

**Adapter closures in `_cross_layer_fallback`:**
- Files: `src/asebytes/_registry.py` lines 246-335
- Why fragile: The `_cross_layer_fallback()` function creates closures (`_make_rw`, `_make_ro`) that capture `blob_cls` or `obj_cls` in their scope. These closures return adapter-wrapped instances but are returned as the "class" from `resolve_backend()`. This means `isinstance()` checks against backend base classes will fail, and the returned callable has a different signature than a real backend class constructor.
- Safe modification: Ensure callers only use the returned value as a factory, never for isinstance checks or class introspection.
- Test coverage: `tests/test_adapters.py` covers basic cross-layer resolution.

## Scaling Limits

**HDF5 file locking prevents concurrent readers in some configurations:**
- Current capacity: Single reader/writer per HDF5 file by default.
- Limit: HDF5 default file locking (POSIX fcntl) prevents multiple processes from opening the same file for reading on some filesystems (NFS, parallel FS).
- Scaling path: Use `HDF5_USE_FILE_LOCKING=FALSE` environment variable, or switch to SWMR mode for concurrent read during write. Alternatively, prefer Zarr for multi-reader scenarios.

**LMDB single-writer limitation:**
- Current capacity: One writer at a time (LMDB enforces this at the OS level).
- Limit: Multiple concurrent writers will block. Database size is bounded by `map_size` (default 10GB).
- Scaling path: Increase `map_size` for larger datasets. For write concurrency, shard across multiple LMDB files.

## Dependencies at Risk

**`msgpack-numpy` is a thin bridge package:**
- Risk: `msgpack-numpy>=0.4.8` is a small package that patches msgpack to handle numpy arrays. It has infrequent updates and may lag behind numpy/msgpack version bumps.
- Impact: Serialization of numpy arrays in the LMDB blob layer (via `src/asebytes/_adapters.py`) depends on it. A numpy dtype change not supported by msgpack-numpy would break blob-level storage.
- Migration plan: Consider replacing with a custom msgpack ext type handler or switching to a different serialization format for the blob layer.

**ASE private API dependency:**
- Risk: `src/asebytes/_convert.py` depends on ASE internal attributes (`_cellobj`, `_pbc`, `_celldisp`, `_calc`) and `SinglePointCalculator` internals (`results`, `atoms`, `parameters`, `_directory`, `prefix`, `use_cache`).
- Impact: Any ASE release that refactors Atoms or SinglePointCalculator internals will break the fast path.
- Migration plan: The `fast=False` fallback exists. Monitor ASE changelogs. Pin `ase>=3.26.0` and test against latest.

## Missing Critical Features

**No `insert` or `delete` for columnar backends:**
- Problem: `ColumnarBackend`, `ZarrBackend`, and `H5MDBackend` all raise `NotImplementedError` for `insert()` and `delete()` (see `src/asebytes/columnar/_backend.py` lines 651-654, `src/asebytes/zarr/_backend.py` lines 461-464, `src/asebytes/h5md/_backend.py` lines 652-655).
- Blocks: Users cannot remove or reorder data in columnar files without rewriting the entire dataset. The `ReadWriteBackend` ABC declares these as abstract methods, but three of the most important backends do not implement them.

**No async ColumnarBackend:**
- Problem: The ColumnarBackend (HDF5/Zarr) has no native async implementation. Async access goes through `SyncToAsyncAdapter` which wraps every call in `asyncio.to_thread`.
- Blocks: For I/O-heavy async workloads, the thread pool becomes a bottleneck. Zarr v3 has async support that could be leveraged.

## Test Coverage Gaps

**No multi-process concurrency tests:**
- What's not tested: Concurrent reads/writes to the same HDF5, Zarr, or LMDB file from multiple processes.
- Files: `src/asebytes/columnar/_backend.py`, `src/asebytes/lmdb/_blob_backend.py`
- Risk: Metadata caching in ColumnarBackend could serve stale data. LMDB writer contention behavior is untested.
- Priority: Medium -- single-process is the primary use case, but multi-process is a documented concern in project memory.

**Cross-layer adapter fallback closures lack comprehensive tests:**
- What's not tested: The closure-based factories returned by `_cross_layer_fallback()` for all combinations of (blob<->object) x (sync/async) x (writable/readonly) x (URI/path).
- Files: `src/asebytes/_registry.py` lines 246-335
- Risk: A specific combination could fail silently or return the wrong adapter type.
- Priority: Low -- basic happy paths are tested.

**ZarrBackend (legacy) may have diverged from ColumnarBackend behavior:**
- What's not tested: Side-by-side behavior comparison between `ZarrBackend` and `ColumnarBackend` for the same Zarr file.
- Files: `src/asebytes/zarr/_backend.py`, `src/asebytes/columnar/_backend.py`
- Risk: Users who import `ZarrBackend` directly get different behavior than those going through the registry (which returns `ColumnarBackend`).
- Priority: High -- this inconsistency could cause data issues for existing users upgrading.

---

*Concerns audit: 2026-03-06*
