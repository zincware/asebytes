# Phase 2: H5MD Compliance - Context

**Gathered:** 2026-03-06
**Status:** Ready for planning

<domain>
## Phase Boundary

H5MDBackend reads and writes H5MD 1.1 compliant files with full znh5md interop, sharing logic with PaddedColumnarBackend via inheritance. Also fixes dependency versions (lmdb, h5py) and renames the h5md extra to h5.

</domain>

<decisions>
## Implementation Decisions

### Inheritance strategy
- H5MDBackend inherits from PaddedColumnarBackend (not ReadWriteBackend directly)
- Reuses base `_postprocess` with `_unpad_per_atom` hook — drop the `_PostProc` enum entirely
- Store owns the h5py.File (consistent with existing HDF5Store pattern)
- H5MD-specific group layout (particles/step/time/value) handled via store or backend overrides — Claude's discretion on which layer

### File handle / factory protocol
- Generalize file_handle and file_factory parameters into BaseColumnarBackend (not H5MD-only)
- Three modes: `file` (path), `file_handle` (open h5py.File/zarr.Group), `file_factory` (Callable → ContextManager)
- Matches znh5md's IO pattern exactly (filename, file_handle, file_factory)
- Whether HDF5Store/ZarrStore accept handles directly or backend translates — Claude's discretion

### znh5md interop scope
- Support ALL znh5md extensions: NaN padding (variable particle count), pbc_group (per-frame PBC), custom info/arrays storage, connectivity (bonds/bond_orders)
- Write ASE_ENTRY_ORIGIN attribute with same values znh5md uses ('calc.results', 'info', 'arrays') — exact match for file interchangeability
- Write linear step/time only (step=1, offset=0); read both 'time' and 'linear' modes for compatibility
- Auto-infer variable_shape from data: start optimistic (fixed-shape, no padding overhead), upgrade to variable-shape retroactively if a later batch has different particle counts (one-time resize cost)
- Constraints stored as JSON string column in observables/{group}/constraints/value using ASE's todict()/dict2constraint()
- Cross-import interop tests: import both znh5md.IO and asebytes.H5MDBackend, write with one, read with the other. znh5md is already a test dependency.

### H5MD metadata & structure
- Root h5md group with sensible defaults: author='N/A', creator='asebytes', version from package. Overridable via __init__ params (author_name, author_email)
- Key mapping matches znh5md exactly (use existing _mapping.py: ASE_TO_H5MD / H5MD_TO_ASE)
- Particles/observables split matches znh5md: per-atom data in particles/, per-frame scalars (energy, stress, info items, constraints) in observables/
- Write ASE units as dataset attributes (positions: Angstrom, forces: eV/Angstrom, etc.)

### Dependency version fixes
- lmdb>=1.6.0 (current >=1.7.5 does not exist on PyPI; latest stable is 1.6.2)
- h5py>=3.12.0 (bumped from >=3.8.0 for modern HDF5 C library and bug fixes)
- Rename `[h5md]` optional-dependency extra to `[h5]` — all HDF5-based backends (h5, h5p, h5md) share the same h5py dependency
- QUAL-04 (remove unnecessary upper bounds) already satisfied — no upper bounds in current deps

### Claude's Discretion
- Whether to create an H5MDStore implementing ColumnarStore protocol or override at backend level
- Whether HDF5Store/ZarrStore accept open handles directly or backend creates store from handle
- Exact hook signatures for H5MD-specific _discover and extend overrides
- How much of PaddedColumnarBackend's extend path to reuse vs override for H5MD group layout

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `PaddedColumnarBackend` (`columnar/_padded.py`): Padded storage with _n_atoms tracking, axis-1 resize, pad/unpad — H5MD inherits this
- `BaseColumnarBackend` (`columnar/_base.py`): _postprocess, _serialize_value, _prepare_scalar_column, _discover, _update_attrs — shared via inheritance chain
- `_mapping.py` (`h5md/_mapping.py`): ASE_TO_H5MD / H5MD_TO_ASE key mappings, KNOWN_PARTICLE_ELEMENTS, ORIGIN_ATTR — already correct
- `_convert.py`: Constraint serialization via ASE todict()/dict2constraint() — reuse for H5MD constraint storage
- `ColumnarStore` protocol (`columnar/_store.py`): HDF5Store and ZarrStore — may need extension for H5MD group layout

### Established Patterns
- Backend registration in `_registry.py`: `*.h5md` → H5MDBackend already registered
- Store protocol delegates I/O, backend handles business logic (classification, padding, metadata)
- `_discover()` → metadata cache pattern on init
- znh5md reference: `file_factory` pattern for read-only access via context manager

### Integration Points
- `_registry.py` line 39: H5MDBackend entry already exists
- `pyproject.toml` line 46-48: lmdb version fix, line 52-54: h5py version bump + extra rename
- `_EXTRAS_HINT` in registry: update 'asebytes.h5md' hint from 'h5md' to 'h5'
- BaseColumnarBackend `__init__`: add file_handle and file_factory parameters

</code_context>

<specifics>
## Specific Ideas

- znh5md's IO class (znh5md/interface/io.py) is the reference implementation for file_handle/file_factory/filename triple pattern
- Auto-infer variable_shape: track whether all frames seen so far have identical particle counts. Cache this flag. If a mismatch is detected, upgrade storage by resizing and padding existing data (one-time cost). This avoids unnecessary NaN padding overhead for the common fixed-shape case.
- znh5md's `fill_dataset` function shows the axis-1 resize pattern — PaddedColumnarBackend's `_resize_per_atom_axis1` already implements this

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-h5md-compliance*
*Context gathered: 2026-03-06*
