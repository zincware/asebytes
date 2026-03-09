# Phase 2: H5MD Compliance - Research

**Researched:** 2026-03-06
**Domain:** H5MD 1.1 file format, znh5md interop, HDF5 group layout, padded columnar storage
**Confidence:** HIGH

## Summary

The H5MD backend needs to be rewritten to inherit from PaddedColumnarBackend rather than directly from ReadWriteBackend. The current implementation is a standalone ~1470-line monolith that duplicates significant logic already available in the columnar hierarchy (padding, axis-1 resize, postprocessing, classification, metadata management). The inheritance refactoring is the core structural change; the H5MD-specific group layout (particles/observables/connectivity with step/time/value sub-elements) is what differentiates it from the generic PaddedColumnarBackend.

The existing H5MD backend already has comprehensive test coverage (51 tests passing), full znh5md cross-compatibility, and correct H5MD 1.1 structure. The refactoring is primarily about code sharing and consistency, not fixing broken behavior. The main new capabilities are: (1) generalizing file_handle/file_factory to BaseColumnarBackend, (2) auto-infer variable_shape, (3) writing ASE unit attributes, (4) constraint support via JSON in observables, and (5) dependency version fixes.

**Primary recommendation:** Rewrite H5MDBackend as a thin specialization of PaddedColumnarBackend, using an H5MDStore (implementing ColumnarStore) that handles the H5MD group layout (step/time/value structure, particles/observables/connectivity routing).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- H5MDBackend inherits from PaddedColumnarBackend (not ReadWriteBackend directly)
- Reuses base `_postprocess` with `_unpad_per_atom` hook -- drop the `_PostProc` enum entirely
- Store owns the h5py.File (consistent with existing HDF5Store pattern)
- H5MD-specific group layout (particles/step/time/value) handled via store or backend overrides -- Claude's discretion on which layer
- Generalize file_handle and file_factory parameters into BaseColumnarBackend (not H5MD-only)
- Three modes: `file` (path), `file_handle` (open h5py.File/zarr.Group), `file_factory` (Callable -> ContextManager)
- Matches znh5md's IO pattern exactly (filename, file_handle, file_factory)
- Support ALL znh5md extensions: NaN padding, pbc_group, custom info/arrays storage, connectivity
- Write ASE_ENTRY_ORIGIN attribute with same values znh5md uses ('calc.results', 'info', 'arrays')
- Write linear step/time only; read both 'time' and 'linear' modes
- Auto-infer variable_shape from data: start optimistic, upgrade retroactively
- Constraints stored as JSON string column in observables/{group}/constraints/value
- Cross-import interop tests: write with one tool, read with the other
- Root h5md group with sensible defaults: author='N/A', creator='asebytes', version from package
- Key mapping matches znh5md exactly (use existing _mapping.py)
- Particles/observables split matches znh5md
- Write ASE units as dataset attributes
- lmdb>=1.6.0 (fix from >=1.7.5)
- h5py>=3.12.0 (bump from >=3.8.0)
- Rename `[h5md]` extra to `[h5]`
- QUAL-04 already satisfied

### Claude's Discretion
- Whether to create an H5MDStore implementing ColumnarStore protocol or override at backend level
- Whether HDF5Store/ZarrStore accept open handles directly or backend creates store from handle
- Exact hook signatures for H5MD-specific _discover and extend overrides
- How much of PaddedColumnarBackend's extend path to reuse vs override for H5MD group layout

### Deferred Ideas (OUT OF SCOPE)
None
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| H5MD-01 | Read/write H5MD 1.1 compliant files (particles, observables, step/time/value) | Architecture patterns section: H5MDStore handles group layout; existing `_init_h5md`, `_create_dataset`, `_extend_dataset` logic is the foundation |
| H5MD-02 | znh5md extensions: NaN padding, pbc_group, custom info/arrays, connectivity | Code examples: origin attributes, padding pattern, connectivity storage. PaddedColumnarBackend already handles NaN padding |
| H5MD-03 | Cross-tool interop (asebytes writes <-> znh5md reads and vice versa) | Existing 51 tests include interop tests; auto-infer variable_shape ensures compatibility |
| H5MD-04 | Round-trip ASE Atoms without data loss | _convert.py atoms_to_dict/dict_to_atoms already handles full ASE conversion; constraint JSON serialization needed |
| H5MD-05 | Share logic with PaddedColumnarBackend | Architecture patterns: inherit from PaddedColumnarBackend, override _discover_variant, extend, and store delegation |
| QUAL-02 | Fix lmdb version pin (>=1.6.0) | pyproject.toml line 47: change `>=1.7.5` to `>=1.6.0` |
| QUAL-03 | Bump h5py floor to >=3.12.0 | pyproject.toml line 53: change `>=3.8.0` to `>=3.12.0` |
| QUAL-04 | Remove unnecessary upper bounds | Already satisfied -- no upper bounds exist in current deps |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| h5py | >=3.12.0 | HDF5 I/O, H5MD file read/write | Only Python HDF5 binding; already in use |
| numpy | (existing dep) | Array operations, padding, dtype handling | Required by h5py |
| ase | >=3.26.0 | Atoms objects, constraint serialization | Core dependency |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| znh5md | >=0.4.8 | Cross-compatibility testing | Test-only dependency, already in dev group |
| molify | >=0.0.1a0 | Generate test molecules with connectivity | Test-only, already in dev group |

### Alternatives Considered
None -- all libraries are locked decisions from Phase 1 and CONTEXT.md.

## Architecture Patterns

### Recommended: H5MDStore implementing ColumnarStore

**Recommendation (Claude's discretion):** Create an H5MDStore class that implements the ColumnarStore protocol but maps flat column names to H5MD group paths internally.

**Rationale:**
1. The ColumnarStore protocol is thin (list_arrays, get_array, get_slice, create_array, append_array, write_slice, get_attrs, set_attrs, get_shape, get_dtype, close, list_groups) -- 12 methods.
2. H5MD's layout (particles/{grp}/{element}/value, observables/{grp}/{element}/value) is fundamentally different from flat HDF5 groups. An H5MDStore translates between flat column names and H5MD paths.
3. This keeps the backend layer thin -- it only adds H5MD metadata initialization, origin attributes, and unit attributes.
4. PaddedColumnarBackend's extend, get, get_many, set, etc. can be reused almost entirely -- the store handles the layout translation.

### H5MDStore Responsibilities
```
H5MDStore (implements ColumnarStore):
  - Owns h5py.File (or wraps file_handle/file_factory)
  - Maps column names <-> H5MD paths via _mapping.py
  - Creates step/time/value sub-elements automatically
  - Handles particles vs observables routing
  - Manages box group (edges, pbc, boundary attrs)
  - Manages connectivity group
  - Stores/reads ASE_ENTRY_ORIGIN attributes
  - Writes unit attributes on datasets
```

### H5MDBackend Responsibilities (thin layer over PaddedColumnarBackend)
```
H5MDBackend(PaddedColumnarBackend):
  - __init__: creates H5MDStore, passes to super()
  - _init_h5md(): create mandatory H5MD skeleton (h5md group, author, creator)
  - Override extend() to call _init_h5md() on first write, then super().extend()
  - Override _discover_variant(): read n_frames from species/value shape[0]
  - Handle connectivity separately (not a regular column)
  - Handle constraints (JSON in observables)
  - Auto-infer variable_shape
```

### File Handle / Factory Pattern in BaseColumnarBackend

```python
class BaseColumnarBackend:
    def __init__(
        self,
        file: str | Path | None = None,
        *,
        file_handle: Any | None = None,   # h5py.File or zarr.Group
        file_factory: Callable[..., ContextManager] | None = None,
        ...
    ):
        # Priority: store > file_handle > file_factory > file
        if store is not None:
            self._store = store
        elif file_handle is not None:
            self._store = self._store_from_handle(file_handle, ...)
        elif file_factory is not None:
            self._store = self._store_from_factory(file_factory, ...)
        elif file is not None:
            self._store = self._store_from_path(file, ...)
```

**Whether stores accept handles directly:** Yes -- HDF5Store and ZarrStore should accept an open handle. HDF5Store already has `_owns_file` tracking; this extends naturally. Add `file_handle` param to HDF5Store.__init__ and ZarrStore.__init__.

### Auto-Infer Variable Shape Pattern

```python
class H5MDBackend(PaddedColumnarBackend):
    def __init__(self, ...):
        self._variable_shape: bool | None = None  # None = auto-detect
        self._fixed_n_atoms: int | None = None     # set after first batch
        ...

    def extend(self, data):
        n_atoms_values = [...]  # determine per-frame atom counts
        unique_counts = set(n_atoms_values)

        if self._variable_shape is None:
            # First batch: check if all same
            if len(unique_counts) == 1:
                self._fixed_n_atoms = unique_counts.pop()
                self._variable_shape = False
            else:
                self._variable_shape = True
        elif not self._variable_shape:
            # Subsequent batch: check if still consistent
            if unique_counts != {self._fixed_n_atoms}:
                self._variable_shape = True
                # One-time resize cost: pad existing data
                self._upgrade_to_variable_shape()

        # Proceed with padded write (PaddedColumnarBackend.extend handles padding)
```

### Key Mapping (existing, reuse as-is)

The `_mapping.py` module already provides:
- `ASE_TO_H5MD`: positions->position, forces->force, numbers->species, etc.
- `H5MD_TO_ASE`: reverse mapping
- `KNOWN_PARTICLE_ELEMENTS`: elements that go in particles/ group
- `ORIGIN_ATTR`: "ASE_ENTRY_ORIGIN"

### H5MD Group Layout (matches znh5md)

```
/h5md/
  attrs: version=[1,1]
  /author/
    attrs: name="...", email="..."
  /creator/
    attrs: name="asebytes", version="0.3.0"
/particles/{group}/
  /species/
    value: float64[n_frames, max_atoms]  # NaN-padded
    step: int (scalar=1 for linear)
    time: float (scalar=1.0 for linear)
    attrs: ASE_ENTRY_ORIGIN="atoms"
  /position/
    value: float64[n_frames, max_atoms, 3]  # NaN-padded
    step, time
    attrs: ASE_ENTRY_ORIGIN="atoms", unit="Angstrom"
  /force/
    value: float64[n_frames, max_atoms, 3]
    attrs: ASE_ENTRY_ORIGIN="calc", unit="eV/Angstrom"
  /box/
    attrs: dimension=3, boundary=["periodic"|"none", ...]
    /edges/
      value: float64[n_frames, 3, 3]
      attrs: unit="Angstrom"
    /pbc/  (znh5md extension)
      value: bool[n_frames, 3]
/observables/{group}/
  /potential_energy/
    value: float64[n_frames]
    attrs: ASE_ENTRY_ORIGIN="calc", unit="eV"
  /constraints/
    value: string[n_frames]  # JSON
    attrs: ASE_ENTRY_ORIGIN="info"
/connectivity/{group}/
  /bonds/
    value: int32[n_frames, max_bonds, 2]  # -1 padded
    step, time
    attrs: particles_group=<ref>
  /bond_orders/
    value: float64[n_frames, max_bonds]  # NaN padded
/asebytes/{group}/
  _n_atoms: int32[n_frames]  # internal metadata
```

### ASE Units (from znh5md/units)

| Property | Unit |
|----------|------|
| positions | Angstrom |
| forces | eV/Angstrom |
| stress | eV/Angstrom^3 |
| velocities | Angstrom/fs |
| cell | Angstrom |
| energy | eV |
| time | fs |

Write as `ds.attrs["unit"] = "..."` on the `value` dataset.

### Origin Attribute Values

| Key prefix | Origin value |
|------------|-------------|
| arrays.positions, arrays.numbers | "atoms" |
| arrays.* (other) | "arrays" |
| calc.* | "calc" |
| info.* | "info" |

Note: znh5md writes origin as `"calc"` (not `"calc.results"`). The CONTEXT.md mentions `'calc.results'` but the actual znh5md code uses `ORIGIN_TYPE = Literal["calc", "info", "arrays", "atoms"]`. The existing asebytes backend already matches this correctly. Use the values from the actual znh5md code: "calc", "info", "arrays", "atoms".

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| NaN padding for variable atoms | Custom padding logic | PaddedColumnarBackend._write_per_atom_column | Already handles pad, stack, backfill, axis-1 resize |
| Constraint serialization | Custom format | ASE's todict()/dict2constraint() via _convert.py | Standard ASE round-trip pattern |
| Varying-shape array concat | Manual loop | concat_varying() from columnar/_utils.py | Handles arbitrary trailing shapes |
| Fill value selection | Hardcoded values | get_fill_value() from columnar/_utils.py | dtype-aware (NaN for float, 0 for int, False for bool) |
| File open/close management | Manual h5py.File management | znh5md's open_file pattern (contextmanager) | Handles file/file_handle/file_factory uniformly |

## Common Pitfalls

### Pitfall 1: Species stored as float64, not int
**What goes wrong:** H5MD stores species (atomic numbers) as float64 with NaN fill for variable particle count. On read, they must be converted to int.
**Why it happens:** NaN padding requires float dtype; integers can't be NaN.
**How to avoid:** The existing `force_float=True` parameter in `_prepare_column` handles this. On read, `_postprocess_typed` with SPECIES tag casts float->int.
**Warning signs:** Atomic numbers come back as float64 arrays.

### Pitfall 2: znh5md expects all particle elements to be H5MD time-dependent groups
**What goes wrong:** If _n_atoms is stored inside the particles/ group, znh5md fails to read the file because it expects every child of particles/{group} to be an H5MD element (group with step/time/value).
**Why it happens:** _n_atoms is asebytes-internal metadata, not an H5MD element.
**How to avoid:** Store _n_atoms under `asebytes/{group}/_n_atoms` (already done in existing implementation).
**Warning signs:** znh5md throws errors when reading asebytes-written files.

### Pitfall 3: Axis-1 resize when upgrading to variable shape
**What goes wrong:** When auto-inferring variable_shape and the first batch is fixed-size, then a later batch has different particle counts, all existing per-atom datasets need axis-1 expansion.
**Why it happens:** Initial datasets were created without padding room.
**How to avoid:** PaddedColumnarBackend._resize_per_atom_axis1 already handles this. The auto-infer logic just needs to trigger it.
**Warning signs:** IndexError or shape mismatch on second extend with different atom count.

### Pitfall 4: h5py string dataset handling
**What goes wrong:** h5py string datasets use variable-length strings with special dtype (h5py.string_dtype()). Element-by-element writes are needed, not slice assignment.
**Why it happens:** HDF5 variable-length strings are fundamentally different from fixed-width types.
**How to avoid:** HDF5Store.append_array already handles this with the `ds.dtype.metadata` check.
**Warning signs:** TypeError or garbled strings on read.

### Pitfall 5: `boundary` attribute vs `pbc` group
**What goes wrong:** H5MD spec requires `boundary` attribute on box group. znh5md extension adds per-frame `pbc` group inside box. Both must be present for full compatibility.
**Why it happens:** H5MD 1.1 only supports static boundary (attribute). znh5md adds the per-frame extension.
**How to avoid:** Write `boundary` attribute on box group (from first frame), AND write pbc group with time-dependent values when pbc_group=True.
**Warning signs:** znh5md reads wrong PBC values; H5MD validators complain about missing boundary.

### Pitfall 6: Registry extras hint stale after rename
**What goes wrong:** After renaming `[h5md]` to `[h5]`, the `_EXTRAS_HINT` in _registry.py still says "h5md".
**Why it happens:** Forgot to update the hint string.
**How to avoid:** Update `_EXTRAS_HINT` entries for "asebytes.h5md" and "asebytes.h5md._backend" from "h5md" to "h5".
**Warning signs:** User gets "pip install asebytes[h5md]" error message when the extra is now named "h5".

## Code Examples

### H5MDStore: Column name to H5MD path translation

```python
# Source: existing _backend.py _key_to_h5 method, adapted for store
def _column_to_h5_path(self, key: str) -> tuple[str, str | None]:
    """Map asebytes column name to H5MD group path and origin."""
    grp = self._particles_group

    if key == "cell":
        return f"/particles/{grp}/box/edges", "atoms"
    if key == "pbc":
        return f"/particles/{grp}/box/pbc", "atoms"

    prefix, sep, name = key.partition(".")
    if not sep:
        return None, None

    h5md_name = ASE_TO_H5MD.get(name, name)

    if prefix == "arrays":
        origin = "atoms" if name in ("positions", "numbers") else "arrays"
        return f"/particles/{grp}/{h5md_name}", origin
    if prefix == "calc":
        if h5md_name in KNOWN_PARTICLE_ELEMENTS:
            return f"/particles/{grp}/{h5md_name}", "calc"
        return f"/observables/{grp}/{h5md_name}", "calc"
    if prefix == "info":
        return f"/observables/{grp}/{name}", "info"

    return None, None
```

### Constraint storage in observables

```python
# Source: CONTEXT.md decision + ASE constraint API
import json
from ase.constraints import dict2constraint

# Write: serialize constraints as JSON string per frame
def _serialize_constraints(atoms):
    if not atoms.constraints:
        return ""
    return json.dumps([c.todict() for c in atoms.constraints])

# Read: reconstruct constraints from JSON string
def _deserialize_constraints(json_str):
    if not json_str:
        return []
    return [dict2constraint(d) for d in json.loads(json_str)]
```

### Unit attribute writing

```python
# Source: znh5md/units/__init__.py
_UNITS = {
    "positions": "Angstrom",
    "forces": "eV/Angstrom",
    "stress": "eV/Angstrom^3",
    "velocities": "Angstrom/fs",
    "cell": "Angstrom",
    "energy": "eV",
    "time": "fs",
}

def _write_unit_attr(ds, ase_name: str) -> None:
    """Write unit attribute on a value dataset if known."""
    unit = _UNITS.get(ase_name)
    if unit is not None:
        ds.attrs["unit"] = unit
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| H5MDBackend inherits ReadWriteBackend directly | Inherit PaddedColumnarBackend | Phase 2 | ~1000 lines of duplicated logic removed |
| `_PostProc` enum for type dispatch | Use base `_postprocess` with `_unpad_per_atom` hook | Phase 2 | Consistent with all columnar backends |
| `variable_shape=True` always | Auto-infer from data | Phase 2 | No NaN overhead for fixed-shape datasets |
| No file_handle/file_factory on base | Generalized to BaseColumnarBackend | Phase 2 | All columnar backends support open handles |

## Open Questions

1. **H5MDStore list_arrays scope**
   - What we know: ColumnarStore.list_arrays returns flat array names. H5MDStore must walk particles/ and observables/ groups recursively.
   - What's unclear: Should list_arrays return H5MD path names or translated asebytes column names?
   - Recommendation: Return translated asebytes column names (arrays.positions, calc.energy, etc.) since the rest of BaseColumnarBackend works with these names.

2. **Connectivity: regular column or special handling?**
   - What we know: Connectivity uses `/connectivity/{group}/bonds` with time-dependent structure, separate from particles and observables.
   - What's unclear: Can connectivity be treated as a regular column through H5MDStore, or does it need special handling?
   - Recommendation: Keep connectivity as special handling in H5MDBackend (override extend), since the bonds/bond_orders dual-dataset pattern doesn't fit the single-column model.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 |
| Config file | pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `uv run pytest tests/test_h5md_backend.py -x -q` |
| Full suite command | `uv run pytest tests/ -x -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| H5MD-01 | Read/write H5MD 1.1 structure | unit+integration | `uv run pytest tests/test_h5md_backend.py::TestH5MDStructure -x` | Existing (6 tests) |
| H5MD-02 | znh5md extensions (NaN padding, pbc_group, custom info/arrays, connectivity) | integration | `uv run pytest tests/test_h5md_backend.py::TestVariableShape tests/test_h5md_backend.py::TestPBCAndCell tests/test_h5md_backend.py::TestConnectivity -x` | Existing (13+ tests) |
| H5MD-03 | Cross-tool interop | integration | `uv run pytest tests/test_h5md_backend.py::TestZnH5MDCompat -x` | Existing (6 tests) |
| H5MD-04 | ASE Atoms round-trip | integration | `uv run pytest tests/test_h5md_backend.py::TestBasicRoundTrip -x` | Existing (4 tests) |
| H5MD-05 | Logic sharing with PaddedColumnarBackend | unit | `uv run pytest tests/test_h5md_backend.py -x` | Existing -- all tests validate behavior after refactoring |
| QUAL-02 | lmdb version fix | smoke | `uv run python -c "import lmdb"` | N/A (pyproject.toml change) |
| QUAL-03 | h5py version bump | smoke | `uv run python -c "import h5py; assert tuple(int(x) for x in h5py.__version__.split('.')[:2]) >= (3,12)"` | N/A (pyproject.toml change) |
| QUAL-04 | No upper bounds | manual | Check pyproject.toml | N/A (already satisfied) |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_h5md_backend.py -x -q`
- **Per wave merge:** `uv run pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_h5md_backend.py` -- needs new tests for: auto-infer variable_shape, constraint round-trip, unit attributes on datasets, file_handle/file_factory parameters
- [ ] Existing tests must all pass after refactoring (regression check)

*(Existing test infrastructure covers most phase requirements; new tests needed for new features only)*

## Sources

### Primary (HIGH confidence)
- Existing codebase: `src/asebytes/h5md/_backend.py` (1474 lines, current implementation)
- Existing codebase: `src/asebytes/columnar/_padded.py` (target parent class)
- Existing codebase: `src/asebytes/columnar/_base.py` (shared base)
- Existing codebase: `src/asebytes/columnar/_store.py` (ColumnarStore protocol, HDF5Store, ZarrStore)
- Existing codebase: `src/asebytes/h5md/_mapping.py` (key mappings)
- Installed znh5md source: `znh5md/interface/write.py`, `znh5md/path/__init__.py`, `znh5md/units/__init__.py`, `znh5md/misc.py`
- Existing tests: `tests/test_h5md_backend.py` (51 passing tests)

### Secondary (MEDIUM confidence)
- H5MD 1.1 specification (https://www.nongnu.org/h5md/h5md.html) -- referenced in REQUIREMENTS.md as ground truth; confirmed by matching structures in existing code
- znh5md serialization model (ORIGIN_TYPE values: "calc", "info", "arrays", "atoms")

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all libraries already in use, versions confirmed from pyproject.toml and PyPI
- Architecture: HIGH - PaddedColumnarBackend and existing H5MDBackend thoroughly analyzed; inheritance path clear
- Pitfalls: HIGH - derived from existing code patterns, actual bug patterns in codebase, and znh5md interop requirements

**Research date:** 2026-03-06
**Valid until:** 2026-04-06 (stable domain, no fast-moving dependencies)
