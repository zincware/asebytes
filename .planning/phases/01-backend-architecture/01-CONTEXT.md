# Phase 1: Backend Architecture - Context

**Gathered:** 2026-03-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Extract BaseColumnarBackend with shared logic, create dedicated RaggedColumnarBackend and PaddedColumnarBackend variants dispatched by file extension, remove legacy Zarr backend, and clean dead code across all backend modules. H5MDBackend refactoring is deferred to Phase 2.

</domain>

<decisions>
## Implementation Decisions

### Extension naming
- Suffix letter convention: `.h5` ragged, `.h5p` padded, `.zarr` ragged, `.zarrp` padded
- Drop `.hdf5` support entirely — only `.h5` for HDF5 ragged
- `*.h5md` remains mapped to H5MDBackend (unchanged)
- No migration utility needed — pre-release package, clean break
- Registry patterns: `*.h5` / `*.zarr` → RaggedColumnarBackend, `*.h5p` / `*.zarrp` → PaddedColumnarBackend

### Padded store design
- PaddedColumnarBackend reuses the existing ColumnarStore protocol (HDF5Store, ZarrStore)
- Padded arrays stored as `(n_frames, max_atoms, ...)` with `_n_atoms` as a regular array column
- Backend handles pad/unpad logic; store protocol stays unchanged
- `maxshape=None` on all axes (both HDF5Store and ZarrStore) to enable resizing when max_atoms grows
- When new batch has more atoms than existing max_atoms: resize all per-atom arrays (consistent with znh5md approach via `fill_dataset` which resizes axis-1)

### Shared base extraction
- BaseColumnarBackend lives in `columnar/_base.py`
- RaggedColumnarBackend in `columnar/_ragged.py` (current `_backend.py` renamed)
- PaddedColumnarBackend in `columnar/_padded.py` (new)
- `_postprocess` uses base + hook pattern: base handles common type coercion (bytes→str, JSON decode, NaN scalar→None, string arrays); variants override `_unpad_per_atom(val, index)` hook
- Identical methods shared in base: `_serialize_value`, `_is_per_atom`, `_check_index`, `_update_attrs` pattern
- Write path (extend): Claude's discretion on how much to share vs keep variant-specific
- H5MDBackend inheritance deferred to Phase 2

### Legacy migration
- Build PaddedColumnarBackend fresh using BaseColumnarBackend + ColumnarStore; reference ZarrBackend but don't copy code
- Delete `src/asebytes/zarr/` immediately once PaddedColumnarBackend passes tests
- Move `_columnar.py` helpers (concat_varying, get_fill_value, jsonable) into `columnar/_utils.py`
- Clean dead code across ALL backend modules (not just columnar) — QUAL-05 scope

### Claude's Discretion
- Whether to auto-detect store type (HDF5/Zarr) in base class constructor or create format-specific subclasses
- How much of the write path (extend) to share in BaseColumnarBackend vs keep in variants
- Exact hook signatures and method decomposition details

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ColumnarStore` protocol (`columnar/_store.py`): HDF5Store and ZarrStore already implement create/append/slice/attrs — reusable for both ragged and padded
- `_columnar.py` utilities: `concat_varying`, `get_fill_value`, `get_version`, `jsonable` — shared helpers to move into `columnar/_utils.py`
- `ReadWriteBackend[str, Any]` ABC (`_backends.py`): base contract all columnar backends inherit

### Established Patterns
- Backend registration via `_REGISTRY` list in `_registry.py` with pattern/scheme matching
- `ColumnarStore` protocol delegates I/O while backend handles business logic (classification, padding, metadata)
- All columnar backends use `_discover()` → metadata cache pattern on init
- znh5md uses `maxshape=tuple(None for _ in data.shape)` for all-axis resizability and `fill_dataset()` for axis-1 resize on variable particle counts

### Integration Points
- Registry (`_registry.py`): needs new entries for `*.h5p` and `*.zarrp` pointing to PaddedColumnarBackend
- Remove `*.zarr` entry pointing to legacy ZarrBackend (already superseded by ColumnarBackend)
- `_EXTRAS_HINT` dict needs updating to remove `asebytes.zarr` entries
- HDF5Store `create_array` currently uses `maxshape=(None,) + arr.shape[1:]` — needs change to `tuple(None for _ in arr.shape)` for padded support

</code_context>

<specifics>
## Specific Ideas

- znh5md's `concatenate_varying_shape_arrays` and `decompose_varying_shape_arrays` in `misc.py` serve as reference for the padded storage strategy — asebytes already has `concat_varying` which does similar work
- znh5md's `fill_dataset` function shows the axis-1 resize pattern: determine max shape, resize dataset, pad new data if narrower than max — PaddedColumnarBackend's extend should follow this pattern

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-backend-architecture*
*Context gathered: 2026-03-06*
