# Phase 1: Backend Architecture - Research

**Researched:** 2026-03-06
**Domain:** Python backend refactoring -- inheritance hierarchy, registry patterns, dead code removal
**Confidence:** HIGH

## Summary

Phase 1 is a pure refactoring phase: extract shared logic from `ColumnarBackend` (ragged, offset+flat) and `ZarrBackend` (padded, NaN-fill) into a `BaseColumnarBackend`, create two clean subclasses (`RaggedColumnarBackend`, `PaddedColumnarBackend`), update the registry for new extensions, and delete the legacy `zarr/` directory. No new external dependencies are needed. The existing `ColumnarStore` protocol (HDF5Store, ZarrStore) remains unchanged and serves both variants.

The codebase is well-structured for this refactoring. The two backends share ~80% identical code: `_postprocess`, `_serialize_value`, `_is_per_atom`, `_check_index`, `_update_attrs`, `_discover`, `_prepare_scalar_column`, `schema`, `keys`, `get_many`, `get_column`, lifecycle methods, and the `ReadWriteBackend[str, Any]` contract. The primary differences are: (1) ragged uses offset+flat arrays (`_offsets`/`_lengths`) while padded uses `(n_frames, max_atoms, ...)` arrays with `_n_atoms`; (2) the `extend` write path differs in how per-atom data is stored; (3) `_postprocess` for padded needs a `n_atoms` slice while ragged already receives pre-sliced data.

**Primary recommendation:** Extract BaseColumnarBackend into `columnar/_base.py` with all shared methods. RaggedColumnarBackend overrides `get`, `extend`, and per-atom write/read hooks. PaddedColumnarBackend overrides `get`, `extend`, and adds pad/unpad logic. Both delegate storage to the unchanged `ColumnarStore` protocol.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Extension naming: `.h5` ragged, `.h5p` padded, `.zarr` ragged, `.zarrp` padded
- Drop `.hdf5` support entirely -- only `.h5` for HDF5 ragged
- `*.h5md` remains mapped to H5MDBackend (unchanged)
- No migration utility needed -- pre-release package, clean break
- Registry patterns: `*.h5` / `*.zarr` -> RaggedColumnarBackend, `*.h5p` / `*.zarrp` -> PaddedColumnarBackend
- PaddedColumnarBackend reuses existing ColumnarStore protocol (HDF5Store, ZarrStore)
- Padded arrays stored as `(n_frames, max_atoms, ...)` with `_n_atoms` as a regular array column
- Backend handles pad/unpad logic; store protocol stays unchanged
- `maxshape=None` on all axes for both HDF5Store and ZarrStore to enable resizing when max_atoms grows
- BaseColumnarBackend in `columnar/_base.py`, RaggedColumnarBackend in `columnar/_ragged.py`, PaddedColumnarBackend in `columnar/_padded.py`
- `_postprocess` uses base + hook pattern: base handles common type coercion; variants override `_unpad_per_atom(val, index)` hook
- Identical methods shared in base: `_serialize_value`, `_is_per_atom`, `_check_index`, `_update_attrs` pattern
- Build PaddedColumnarBackend fresh using BaseColumnarBackend + ColumnarStore; reference ZarrBackend but don't copy code
- Delete `src/asebytes/zarr/` immediately once PaddedColumnarBackend passes tests
- Move `_columnar.py` helpers into `columnar/_utils.py`
- Clean dead code across ALL backend modules -- QUAL-05 scope
- H5MDBackend inheritance deferred to Phase 2

### Claude's Discretion
- Whether to auto-detect store type (HDF5/Zarr) in base class constructor or create format-specific subclasses
- How much of the write path (extend) to share in BaseColumnarBackend vs keep in variants
- Exact hook signatures and method decomposition details

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ARCH-01 | Extract BaseColumnarBackend with shared logic | Identified 15+ methods to share; `_postprocess`, `_serialize_value`, `_prepare_scalar_column`, `_discover`, `_update_attrs`, `_is_per_atom`, `_check_index`, `schema`, `keys`, `get_many`, `get_column`, `set`, `set_column`, `update_many`, lifecycle methods |
| ARCH-02 | Create RaggedColumnarBackend with offset+flat storage | Current `ColumnarBackend` IS this -- rename + extract shared parts to base |
| ARCH-03 | Create PaddedColumnarBackend with NaN/zero-fill storage | Reference ZarrBackend's `_pad_per_atom`, `_extend_array` (axis-1 resize), `_n_atoms` tracking; build fresh on BaseColumnarBackend |
| ARCH-04 | Register dedicated file extensions for padded/ragged variants | Registry update: add `*.h5p` and `*.zarrp` entries, update `*.h5`/`*.zarr` to point to RaggedColumnarBackend |
| ARCH-05 | Remove legacy Zarr backend | Delete `src/asebytes/zarr/`, update `__init__.py`, clean `_EXTRAS_HINT`, update imports in tests |
| ARCH-06 | Update registry to avoid glob collisions | No collision risk: `*.h5` vs `*.h5p` and `*.zarr` vs `*.zarrp` use fnmatch which is suffix-based; `.h5p` won't match `*.h5` |
| QUAL-01 | Consolidate duplicated _postprocess() logic | Three nearly-identical implementations found in ColumnarBackend, ZarrBackend, H5MDBackend -- base class consolidation eliminates two |
| QUAL-05 | Remove dead code paths and unused imports | ZarrBackend is dead code (registry already routes `*.zarr` to ColumnarBackend); `.hdf5` extension checks in ColumnarBackend; `ZarrObjectBackend` alias |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| h5py | >=3.8.0 (existing) | HDF5 I/O via HDF5Store | Already in use, unchanged |
| zarr | v3 (existing) | Zarr I/O via ZarrStore | Already in use, unchanged |
| numpy | existing | Array operations | Already in use, unchanged |

### Supporting
No new dependencies needed. This is a pure refactoring phase.

### Alternatives Considered
None -- all decisions are locked. No new libraries needed.

## Architecture Patterns

### Recommended Project Structure
```
src/asebytes/columnar/
    __init__.py          # exports BaseColumnarBackend, RaggedColumnarBackend, PaddedColumnarBackend, stores
    _base.py             # BaseColumnarBackend (shared logic)
    _ragged.py           # RaggedColumnarBackend (offset+flat storage) -- renamed from _backend.py
    _padded.py           # PaddedColumnarBackend (NaN/zero-fill storage) -- new
    _store.py            # ColumnarStore protocol, HDF5Store, ZarrStore -- unchanged
    _utils.py            # moved from src/asebytes/_columnar.py (concat_varying, get_fill_value, etc.)
```

### Pattern 1: Base + Hook Inheritance
**What:** BaseColumnarBackend implements all shared methods. Variant-specific behavior uses hook methods that subclasses override.
**When to use:** When two classes share 80%+ code but differ in a few key operations.

Key hooks to define:

1. **`_read_per_atom_value(self, col_name, index)`** -- ragged uses offset+length slice, padded uses `[index, :n_atoms]`
2. **`_read_per_atom_bulk(self, col_name, indices)`** -- bulk read variant
3. **`_write_per_atom_column(self, key, values, n_atoms_values)`** -- ragged writes flat+offsets, padded writes padded 2D arrays
4. **`_discover(self)`** -- base discovers common metadata; ragged adds offset/length cache, padded adds `_n_atoms` cache
5. **`_unpad_per_atom(self, val, index)`** -- hook called by `_postprocess` for per-atom values; ragged returns as-is (already sliced), padded slices to `[:n_atoms]`

### Pattern 2: Store Auto-Detection in Constructor
**What:** BaseColumnarBackend constructor detects HDF5 vs Zarr from file extension and creates appropriate store.
**When to use:** Both ragged and padded variants need the same store auto-detection logic.

```python
# In BaseColumnarBackend.__init__
ext = Path(file).suffix.lower()
if ext in (".h5", ".h5p"):
    self._store = HDF5Store(file, self.group, ...)
elif ext in (".zarr", ".zarrp"):
    self._store = ZarrStore(file, self.group, ...)
```

This is recommended over format-specific subclasses (e.g., HDF5RaggedBackend) because the store protocol already encapsulates format differences.

### Pattern 3: Registry Extension Mapping
**What:** File extensions map directly to backend classes via `_REGISTRY` patterns.
**When to use:** Dispatch by file extension with no ambiguity.

```python
# Updated _REGISTRY entries
_RegistryEntry("pattern", "*.h5", "object", "asebytes.columnar", "RaggedColumnarBackend", "RaggedColumnarBackend", False),
_RegistryEntry("pattern", "*.zarr", "object", "asebytes.columnar", "RaggedColumnarBackend", "RaggedColumnarBackend", False),
_RegistryEntry("pattern", "*.h5p", "object", "asebytes.columnar", "PaddedColumnarBackend", "PaddedColumnarBackend", False),
_RegistryEntry("pattern", "*.zarrp", "object", "asebytes.columnar", "PaddedColumnarBackend", "PaddedColumnarBackend", False),
```

### Anti-Patterns to Avoid
- **Copying code from ZarrBackend into PaddedColumnarBackend:** Build PaddedColumnarBackend fresh on BaseColumnarBackend; reference ZarrBackend for the pad/unpad logic only.
- **Caching backend data:** Memory project note says "NEVER cache backend data -- another client can modify." However, offset/length caches and `_n_atoms` are structural metadata reloaded via `_discover()` after writes. This is acceptable as long as `_discover()` is called after every mutation.
- **Mixing storage format concerns into backend logic:** Keep HDF5 vs Zarr differences inside the `ColumnarStore` implementations, not in the backend classes.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Varying-shape array concatenation | Custom padding loop | `concat_varying()` from `_columnar.py` (moving to `_utils.py`) | Handles arbitrary trailing dimensions, dtype-aware fill values |
| Store abstraction | Direct h5py/zarr calls in backend | `ColumnarStore` protocol (HDF5Store, ZarrStore) | Already exists, battle-tested, encapsulates format differences |
| Fill value selection | Inline if/else chains | `get_fill_value()` from `_columnar.py` | Handles float (NaN), int (0), bool (False) correctly |
| JSON serialization of numpy types | `json.dumps(val)` | `jsonable()` from `_columnar.py` | Recursively converts numpy scalars/arrays to JSON-safe types |

## Common Pitfalls

### Pitfall 1: HDF5Store maxshape Must Enable All-Axis Resize for Padded
**What goes wrong:** Current `HDF5Store.create_array` uses `maxshape=(None,) + arr.shape[1:]` which fixes trailing dimensions. PaddedColumnarBackend needs to resize axis-1 when `max_atoms` grows.
**Why it happens:** The ragged backend never needs axis-1 resize (flat arrays are 1D per-atom).
**How to avoid:** Change `HDF5Store.create_array` to use `maxshape=tuple(None for _ in arr.shape)` for all arrays, OR pass a `maxshape` parameter and let the backend specify it.
**Warning signs:** `ValueError: Unable to resize dataset` when extending with more atoms than previous max.

### Pitfall 2: fnmatch Pattern Collision Between `.h5` and `.h5p`
**What goes wrong:** `*.h5` could potentially match `file.h5p` since fnmatch works character by character.
**Why it happens:** Misunderstanding fnmatch behavior.
**How to avoid:** Verify: `fnmatch.fnmatch("file.h5p", "*.h5")` returns `False`. It does -- fnmatch requires exact suffix match after the `*`. No collision. But test this explicitly in a unit test.
**Warning signs:** Wrong backend class returned for `.h5p` files.

### Pitfall 3: Backward Compatibility of `ColumnarBackend` Name
**What goes wrong:** Existing code imports `from asebytes.columnar import ColumnarBackend` or `from asebytes import ColumnarBackend`.
**Why it happens:** Renaming the class breaks imports.
**How to avoid:** Keep `ColumnarBackend` as an alias for `RaggedColumnarBackend` in `columnar/__init__.py`. Also keep `ColumnarObjectBackend` alias. Update `__init__.py` to export both old and new names.
**Warning signs:** `ImportError` in downstream code.

### Pitfall 4: `_discover()` Cache Consistency After Extend
**What goes wrong:** PaddedColumnarBackend's `extend` might not refresh `_n_atoms` cache properly.
**Why it happens:** The old ZarrBackend caches `_col_cache` dict with zarr.Array references. The new PaddedColumnarBackend uses ColumnarStore which doesn't cache array references the same way.
**How to avoid:** Always call `self._discover()` at the end of `extend()`, just like the current ColumnarBackend does.
**Warning signs:** Stale n_atoms values when reading after extend.

### Pitfall 5: Test Import Paths After Deletion
**What goes wrong:** Tests that import `from asebytes.zarr._backend import ZarrBackend` will break.
**Why it happens:** Deleting `src/asebytes/zarr/` removes the module entirely.
**How to avoid:** Update or delete these test files: `test_zarr_backend.py`, `test_reserve_none.py` (imports ZarrBackend), `test_n_atoms_zarr.py`. Zarr-specific tests should be converted to test PaddedColumnarBackend instead.
**Warning signs:** `ModuleNotFoundError: No module named 'asebytes.zarr'`.

### Pitfall 6: `.hdf5` Extension Removal
**What goes wrong:** Code that opens `.hdf5` files breaks silently.
**Why it happens:** The CONTEXT.md says "Drop `.hdf5` support entirely."
**How to avoid:** Remove all `.hdf5` checks from `ColumnarBackend` (3 occurrences at lines 68, 147, 679 of current `_backend.py`). The registry never had a `*.hdf5` entry, so only direct constructor calls are affected.
**Warning signs:** `ValueError: Unsupported extension: .hdf5`.

## Code Examples

### Shared _postprocess (base class)
```python
# Source: Compared ColumnarBackend._postprocess and ZarrBackend._postprocess
# They are ~95% identical. Key difference: padded variant needs n_atoms slice.

class BaseColumnarBackend(ReadWriteBackend[str, Any]):
    def _postprocess(self, val, col_name, *, is_per_atom=False):
        """Common postprocessing. Subclasses override _unpad_per_atom hook."""
        # bytes -> str
        if isinstance(val, (bytes, np.bytes_)):
            val = val.decode() if isinstance(val, bytes) else str(val)

        # zarr v3 0-d StringDType
        if isinstance(val, np.ndarray) and val.ndim == 0 and val.dtype.kind in ("U", "T"):
            val = str(val)

        # string -> JSON decode
        if isinstance(val, str):
            if val == "":
                return None
            try:
                return json.loads(val)
            except (json.JSONDecodeError, ValueError):
                return val

        # numpy scalars
        if isinstance(val, np.floating):
            return None if np.isnan(val) else val.item()
        if isinstance(val, np.integer):
            return val.item()

        if isinstance(val, np.ndarray):
            # String arrays
            if val.dtype.kind in ("S", "U", "O"):
                return self._postprocess_string_array(val)

            # Per-atom hook (subclass-specific)
            if is_per_atom:
                val = self._unpad_per_atom(val, col_name)
                if val is None or (isinstance(val, np.ndarray) and val.size == 0):
                    return None
                if isinstance(val, np.ndarray) and val.dtype.kind == "f" and np.all(np.isnan(val)):
                    return None
                return val

            # Multi-element float NaN check
            if val.ndim >= 1 and val.dtype.kind == "f" and np.all(np.isnan(val)):
                return None

            # Scalar ndarray
            if val.ndim == 0:
                v = val.item()
                if isinstance(v, float) and np.isnan(v):
                    return None
                return v

        return val

    def _unpad_per_atom(self, val, col_name):
        """Hook: subclasses handle per-atom unpadding differently."""
        return val  # base: return as-is
```

### RaggedColumnarBackend per-atom read
```python
# Source: Current ColumnarBackend.get() lines 193-201
# Ragged: offset+length already pre-slices the flat array
class RaggedColumnarBackend(BaseColumnarBackend):
    def _unpad_per_atom(self, val, col_name):
        # Already sliced by offset+length before _postprocess is called
        return val
```

### PaddedColumnarBackend per-atom read
```python
# Source: Current ZarrBackend._postprocess() lines 540-551
# Padded: slice (n_frames, max_atoms, ...) -> (n_atoms, ...)
class PaddedColumnarBackend(BaseColumnarBackend):
    def _get_n_atoms(self, index):
        """Read n_atoms for a single frame."""
        return int(self._store.get_slice("_n_atoms", index))

    def _unpad_per_atom(self, val, col_name):
        # val is already the padded row (max_atoms, ...)
        # n_atoms context must be passed via instance state or parameter
        if self._current_n_atoms is not None:
            val = val[:self._current_n_atoms]
        return val
```

### HDF5Store maxshape change for padded support
```python
# Source: Current HDF5Store.create_array() line 153
# BEFORE: maxshape = (None,) + arr.shape[1:]
# AFTER:  maxshape = tuple(None for _ in arr.shape)
# This allows axis-1 resize when max_atoms grows
```

### Registry update
```python
# Source: Current _registry.py lines 37-39
# Remove:
#   _RegistryEntry("pattern", "*.h5", "object", "asebytes.columnar", "ColumnarBackend", ...)
# Replace with:
_RegistryEntry("pattern", "*.h5", "object", "asebytes.columnar", "RaggedColumnarBackend", "RaggedColumnarBackend", False),
_RegistryEntry("pattern", "*.zarr", "object", "asebytes.columnar", "RaggedColumnarBackend", "RaggedColumnarBackend", False),
_RegistryEntry("pattern", "*.h5p", "object", "asebytes.columnar", "PaddedColumnarBackend", "PaddedColumnarBackend", False),
_RegistryEntry("pattern", "*.zarrp", "object", "asebytes.columnar", "PaddedColumnarBackend", "PaddedColumnarBackend", False),
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Separate ZarrBackend class | ColumnarBackend with ZarrStore | Already done (pre-phase) | ZarrBackend is dead code for registry users |
| `*.zarr` -> ZarrBackend | `*.zarr` -> ColumnarBackend | Already in registry | Legacy ZarrBackend only used via direct import |
| Padded storage in ZarrBackend | Will move to PaddedColumnarBackend | This phase | Clean separation of storage strategies |

**Deprecated/outdated:**
- `ZarrBackend` / `ZarrObjectBackend`: Dead code -- registry already routes `*.zarr` to `ColumnarBackend`
- `.hdf5` extension handling: Being dropped (CONTEXT.md decision)
- `ColumnarBackend` name: Will become alias for `RaggedColumnarBackend`

## Open Questions

1. **How to pass n_atoms context to `_unpad_per_atom` in padded backend?**
   - What we know: ZarrBackend passes `n_atoms` as parameter to `_postprocess`. ColumnarBackend passes `is_per_atom` flag instead.
   - What's unclear: Whether to use a thread-local/instance variable pattern or change the `_postprocess` signature.
   - Recommendation: Add optional `n_atoms` parameter to `_postprocess` and pass through to `_unpad_per_atom`. Ragged ignores it, padded uses it. This avoids instance state mutation.

2. **How much of `extend()` can be shared?**
   - What we know: Both variants share atom-count detection, column classification, scalar column writing, alignment padding, metadata update, and `_discover()` call. They differ only in per-atom column writing and offset/n_atoms tracking.
   - What's unclear: Whether a template method pattern (base `extend` calling hooks) is cleaner than separate implementations.
   - Recommendation: Use template method: base `extend` handles iteration, classification, scalar columns, alignment; calls `_write_per_atom_column` (abstract) and `_write_atom_tracking` (abstract) hooks for variant-specific parts.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 + pytest-benchmark 5.2.1 |
| Config file | pyproject.toml |
| Quick run command | `uv run pytest tests/test_columnar_backend.py -x -q` |
| Full suite command | `uv run pytest tests/ -x -q --ignore=tests/benchmarks` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ARCH-01 | BaseColumnarBackend has shared methods | unit | `uv run pytest tests/test_columnar_backend.py -x` | Yes (tests exist but test ColumnarBackend, will need updating to test both variants) |
| ARCH-02 | RaggedColumnarBackend offset+flat storage | unit | `uv run pytest tests/test_columnar_backend.py -x` | Yes (current tests cover ragged behavior) |
| ARCH-03 | PaddedColumnarBackend NaN-fill storage | unit | `uv run pytest tests/test_columnar_backend.py -x` | Partial (test_zarr_backend.py tests padded via ZarrBackend -- needs migration) |
| ARCH-04 | Registry maps extensions correctly | unit | `uv run pytest tests/test_unified_registry.py -x` | Yes (existing registry tests) |
| ARCH-05 | Legacy zarr/ deleted, no references | smoke | `uv run python -c "import asebytes.zarr"` should fail | No -- Wave 0 |
| ARCH-06 | No glob collisions | unit | `uv run pytest tests/test_unified_registry.py -x` | Yes (extend existing) |
| QUAL-01 | Single _postprocess in base | unit | `uv run pytest tests/test_columnar_backend.py -x` | Yes (covered by read tests) |
| QUAL-05 | Dead code removed | smoke | `uv run python -c "from asebytes.zarr import ZarrBackend"` should fail | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_columnar_backend.py tests/test_columnar_store.py -x -q`
- **Per wave merge:** `uv run pytest tests/ -x -q --ignore=tests/benchmarks`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_columnar_backend.py` -- needs parameterization to test BOTH RaggedColumnarBackend and PaddedColumnarBackend
- [ ] Update `tests/test_zarr_backend.py` -- convert to test PaddedColumnarBackend OR delete (tests are mostly redundant with columnar tests)
- [ ] Update `tests/test_reserve_none.py` -- imports ZarrBackend directly, needs update
- [ ] Add registry tests for `*.h5p` and `*.zarrp` extensions in `tests/test_unified_registry.py`
- [ ] Add smoke test that `import asebytes.zarr` raises ImportError after deletion

## Sources

### Primary (HIGH confidence)
- Source code analysis of `src/asebytes/columnar/_backend.py` (ColumnarBackend -- 989 lines)
- Source code analysis of `src/asebytes/zarr/_backend.py` (ZarrBackend -- 831 lines)
- Source code analysis of `src/asebytes/columnar/_store.py` (ColumnarStore protocol, HDF5Store, ZarrStore)
- Source code analysis of `src/asebytes/_registry.py` (registry patterns)
- Source code analysis of `src/asebytes/_backends.py` (ReadWriteBackend ABC)
- Source code analysis of `src/asebytes/h5md/_backend.py` (_postprocess comparison)
- Test execution: 67 columnar tests pass, 29 zarr tests pass (2026-03-06)

### Secondary (MEDIUM confidence)
- CONTEXT.md decisions from user discussion session (2026-03-06)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, pure refactoring
- Architecture: HIGH -- direct source code analysis of both backends reveals clear extraction points
- Pitfalls: HIGH -- identified from reading actual code, verified test runs, checked fnmatch behavior

**Research date:** 2026-03-06
**Valid until:** 2026-04-06 (stable -- internal refactoring, no external dependency risk)
