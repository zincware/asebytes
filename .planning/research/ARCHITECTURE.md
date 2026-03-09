# Architecture Patterns

**Domain:** Multi-backend scientific IO library (columnar storage for ASE Atoms)
**Researched:** 2026-03-06
**Confidence:** HIGH (based on direct codebase analysis and established patterns in scientific Python)

## Current State Analysis

The codebase has a clean layered architecture (Facade -> Backend ABC -> Store) but suffers from one critical structural problem: **the ColumnarBackend conflates two fundamentally different storage strategies** (padded and ragged) behind a single class that uses offset+flat ragged layout for everything. Meanwhile, the H5MDBackend implements a completely separate padded strategy with NaN-fill. These two backends share significant duplicated logic (`_postprocess`, `_prepare_scalar_column`, `concat_varying`, `get_fill_value`, JSON serialization) but do not share a common base class.

### What Works Well

- **ColumnarStore protocol** successfully decouples HDF5/Zarr array I/O from backend logic
- **Backend ABCs** (`ReadBackend[K,V]`, `ReadWriteBackend[K,V]`) provide a clear contract
- **Registry** glob-pattern dispatch is simple and extensible
- **Adapter chain** (blob<->object, sync->async) is principled

### What Needs Restructuring

1. **ColumnarBackend does too much**: classification, ragged write, scalar write, postprocessing, metadata management -- 990 lines
2. **H5MDBackend duplicates ColumnarBackend logic**: both have `_postprocess`, both handle JSON serialization, both manage frame counts and column classification -- but with different implementations
3. **No shared base for columnar backends**: padded and ragged share ~60% of their logic (scalar column handling, JSON encoding/decoding, fill-value management, schema introspection) but there is no `BaseColumnarBackend` to factor it into
4. **Test structure is per-feature, not per-contract**: 40+ test files each testing specific behaviors, rather than a unified contract test suite parametrized across backends

## Recommended Architecture

### Target Component Hierarchy

```
ReadBackend[K,V] / ReadWriteBackend[K,V]     (ABC, unchanged)
    |
    +-- BaseColumnarBackend                    (NEW: shared columnar logic)
    |       |
    |       +-- RaggedColumnarBackend          (NEW: offset+flat per-atom storage)
    |       |       uses ColumnarStore
    |       |
    |       +-- PaddedColumnarBackend          (NEW: NaN-padded per-atom storage)
    |       |       uses ColumnarStore
    |       |
    |       +-- H5MDBackend                    (REFACTORED: H5MD-compliant padded, h5py direct)
    |
    +-- LMDBBlobBackend                        (unchanged)
    +-- LMDBObjectBackend                      (unchanged, wraps blob via adapter)
    +-- MemoryObjectBackend                    (unchanged)
    +-- ASEReadOnlyBackend                     (unchanged)
    +-- HuggingFaceBackend                     (unchanged)
    +-- MongoObjectBackend                     (unchanged)
    +-- RedisBlobBackend                       (unchanged)
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| **BaseColumnarBackend** | Shared columnar logic: scalar column write/read, JSON serialization, fill-value management, postprocessing, schema introspection, metadata attrs, column classification (`_is_per_atom`) | ColumnarStore (via subclass), Backend ABCs |
| **RaggedColumnarBackend** | Offset+flat ragged storage for per-atom columns; manages `_offsets`/`_lengths` arrays; contiguous flat-array reads | BaseColumnarBackend, ColumnarStore |
| **PaddedColumnarBackend** | NaN-padded per-atom storage; manages `_max_atoms` tracking; `concat_varying` for shape-varying data; NaN-stripping on read | BaseColumnarBackend, ColumnarStore |
| **H5MDBackend** | H5MD 1.1 spec compliance; maps ASE keys to H5MD paths (`particles/`, `observables/`, `connectivity/`); reads/writes `h5md` root group with author/version metadata; handles `boundary` attrs; znh5md compatibility (variable particle count via `_n_atoms` sidecar) | BaseColumnarBackend (inherits shared logic), h5py directly (not via ColumnarStore -- H5MD layout is too specific) |
| **ColumnarStore** | Array-level I/O abstraction (create, append, get_slice, write_slice, attrs) | HDF5Store (h5py), ZarrStore (zarr v3) |
| **Registry** | Map file extensions to backend classes; cross-layer adapter fallback | All backend classes (lazy import) |
| **Facades** | User-facing MutableSequence API; view dispatch; ASE conversion | Registry, Backend ABCs, Views |

### Data Flow

**Write path (ASEIO.extend -> RaggedColumnarBackend):**

```
User: db.extend([atoms1, atoms2])
  |
  v
ASEIO.extend() -- calls atoms_to_dict() on each Atoms
  |
  v
RaggedColumnarBackend.extend(dicts)
  |
  +-- BaseColumnarBackend._classify_columns(dicts) -- sorts keys into per-atom vs scalar
  +-- BaseColumnarBackend._write_scalar_columns(keys, values) -- delegates to ColumnarStore
  +-- RaggedColumnarBackend._write_per_atom_columns(keys, values) -- builds flat arrays, updates _offsets/_lengths
  +-- BaseColumnarBackend._update_attrs() -- writes metadata to ColumnarStore
  |
  v
ColumnarStore.create_array() / .append_array()
  |
  v
HDF5Store (h5py) or ZarrStore (zarr v3)
```

**Write path (ASEIO.extend -> PaddedColumnarBackend):**

```
Same as above, but PaddedColumnarBackend._write_per_atom_columns():
  +-- Determines max atom count across batch + existing _max_atoms
  +-- Pads all per-atom arrays to (n_frames, max_atoms, ...) with fill values
  +-- If max_atoms grew, resizes existing per-atom datasets to new max_atoms
  +-- No _offsets/_lengths arrays needed
```

**Write path (ASEIO.extend -> H5MDBackend):**

```
User: db.extend([atoms1, atoms2])
  |
  v
ASEIO.extend() -- calls atoms_to_dict()
  |
  v
H5MDBackend.extend(dicts)
  |
  +-- BaseColumnarBackend._classify_columns() -- reused
  +-- H5MDBackend._map_keys_to_h5md() -- translates "arrays.positions" -> "particles/{grp}/position/value"
  +-- H5MDBackend._write_h5md_groups() -- creates H5MD-spec-compliant group structure with step/time datasets
  +-- Padded per-atom storage (NaN fill, tracks _n_atoms sidecar for znh5md compat)
  +-- BaseColumnarBackend._write_scalar_columns() for observables
  |
  v
h5py direct (H5MD layout is incompatible with ColumnarStore's flat namespace)
```

**Read path (ASEIO[0] -> RaggedColumnarBackend):**

```
ASEIO.__getitem__(0)
  |
  v
ASEIO._read_row(0) -> backend.get(0)
  |
  v
RaggedColumnarBackend.get(0):
  +-- Read offset/length from cached _offsets/_lengths
  +-- For each per-atom column: store.get_slice(col, slice(offset, offset+length))
  +-- For each scalar column: store.get_slice(col, index)
  +-- BaseColumnarBackend._postprocess() on each value
  |
  v
ASEIO._build_result(dict) -> dict_to_atoms(dict) -> Atoms
```

### Registry Extension for Padded vs Ragged

The registry should dispatch based on file extension to separate padded from ragged:

```python
_REGISTRY = [
    # Ragged (default for new files)
    _RegistryEntry("pattern", "*.h5", "object", "asebytes.columnar", "RaggedColumnarBackend", ...),
    _RegistryEntry("pattern", "*.zarr", "object", "asebytes.columnar", "RaggedColumnarBackend", ...),

    # Padded (explicit opt-in via extension suffix)
    _RegistryEntry("pattern", "*.h5p", "object", "asebytes.columnar", "PaddedColumnarBackend", ...),
    _RegistryEntry("pattern", "*.zarrp", "object", "asebytes.columnar", "PaddedColumnarBackend", ...),

    # H5MD (spec-compliant, always padded)
    _RegistryEntry("pattern", "*.h5md", "object", "asebytes.h5md", "H5MDBackend", ...),
]
```

**Rationale for `.h5p`/`.zarrp` over `.h5-padded`:** File extensions with hyphens break shell glob patterns and confuse some filesystem tools. Single-suffix extensions are conventional. The `p` suffix is short for "padded" and unambiguous in context. However, the exact naming is a user decision -- what matters architecturally is that padded and ragged are separate registry entries pointing to separate backend classes.

**Alternative considered: parameter-based dispatch** (`ASEIO("data.h5", strategy="padded")`). Rejected because: (1) the registry is extension-based and adding constructor parameters would require registry protocol changes, (2) a file's storage strategy is an intrinsic property of the file, not a user preference at open time, (3) re-opening a file should auto-detect its strategy without user knowledge.

## Patterns to Follow

### Pattern 1: Template Method for Columnar Backends

**What:** `BaseColumnarBackend` implements the full `ReadWriteBackend` contract. Subclasses override only the per-atom-specific methods.

**When:** Any columnar backend (ragged, padded, H5MD).

**Why:** The current ColumnarBackend and H5MDBackend duplicate ~300 lines of scalar column handling, JSON serialization, and postprocessing. A Template Method base class eliminates this.

```python
class BaseColumnarBackend(ReadWriteBackend[str, Any], ABC):
    """Shared logic for all columnar backends."""

    _returns_mutable: bool = True

    # --- Concrete methods (shared) ---

    def _postprocess(self, val, col_name, *, is_per_atom=False):
        """Shared read postprocessing: NaN->None, JSON decode, numpy scalar unwrap."""
        ...

    def _prepare_scalar_column(self, values):
        """Shared scalar column serialization."""
        ...

    def _write_scalar_columns(self, keys, batch_values):
        """Write non-per-atom columns to store."""
        ...

    def _classify_columns(self, data):
        """Determine which columns are per-atom vs scalar."""
        ...

    def _serialize_value(self, val):
        """JSON-encode dicts/lists/strings."""
        ...

    # --- Abstract methods (per-atom strategy) ---

    @abstractmethod
    def _write_per_atom_columns(self, keys, batch_values, n_atoms_list):
        """Write per-atom columns using strategy-specific layout."""
        ...

    @abstractmethod
    def _read_per_atom_value(self, col_name, index):
        """Read a single per-atom value for one frame."""
        ...

    @abstractmethod
    def _read_per_atom_bulk(self, col_name, indices):
        """Read per-atom values for multiple frames."""
        ...
```

### Pattern 2: Contract Test Suite with pytest Parametrization

**What:** A single `tests/contract/` directory containing test classes that define the behavioral contract for each backend level. Backend-specific fixtures inject the backend under test.

**When:** Testing any backend implementation.

**Why:** The current 40+ test files duplicate assertions across backends. A contract suite guarantees every backend satisfies identical invariants.

```python
# tests/contract/test_object_backend_contract.py
class TestObjectBackendContract:
    """Every ObjectReadWriteBackend must pass these tests."""

    def test_extend_and_len(self, rw_backend, sample_rows):
        rw_backend.extend(sample_rows)
        assert len(rw_backend) == len(sample_rows)

    def test_roundtrip_single_row(self, rw_backend, sample_rows):
        rw_backend.extend(sample_rows)
        row = rw_backend.get(0)
        # assert structural equality...

    def test_get_column(self, rw_backend, sample_rows):
        ...

    def test_ragged_atom_counts(self, rw_backend, ragged_rows):
        ...

# tests/conftest.py
@pytest.fixture(params=[
    pytest.param("h5-ragged", id="h5-ragged"),
    pytest.param("h5-padded", id="h5-padded"),
    pytest.param("zarr-ragged", id="zarr-ragged"),
    pytest.param("zarr-padded", id="zarr-padded"),
    pytest.param("lmdb", id="lmdb"),
    pytest.param("memory", id="memory"),
    pytest.param("h5md", id="h5md"),
])
def rw_backend(tmp_path, request):
    """Yield a fresh ReadWriteBackend for contract testing."""
    ...
```

### Pattern 3: Strategy via ColumnarStore (Keep What Works)

**What:** The existing ColumnarStore protocol cleanly separates array I/O from backend logic. Keep this boundary.

**When:** Any backend that stores data as named arrays (HDF5 datasets, Zarr arrays).

**Why:** It already works. HDF5Store and ZarrStore implementations are clean and complete. Adding a third store implementation (e.g., for N5 or TileDB) would require zero changes to backend logic.

**Exception:** H5MDBackend should NOT use ColumnarStore because H5MD's layout (nested `particles/{group}/{element}/value` with companion `step`/`time` datasets) is fundamentally incompatible with ColumnarStore's flat namespace assumption.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Single Backend Class with Strategy Flag

**What:** `ColumnarBackend(path, strategy="ragged"|"padded")` instead of separate classes.

**Why bad:** (1) Violates Single Responsibility -- one class doing two things. (2) Every method needs `if self._strategy == "ragged": ... else: ...` branches. (3) The current 990-line ColumnarBackend is already too large. (4) File re-opening requires reading metadata to determine strategy, which a registry entry cannot do.

**Instead:** Separate `RaggedColumnarBackend` and `PaddedColumnarBackend` inheriting from `BaseColumnarBackend`.

### Anti-Pattern 2: Duplicating H5MD Logic in PaddedColumnarBackend

**What:** Making PaddedColumnarBackend handle H5MD-specific layout (nested groups, step/time datasets, boundary attrs, connectivity groups, ASE_TO_H5MD name mapping).

**Why bad:** H5MD compliance is a spec concern, not a storage strategy concern. PaddedColumnarBackend should use asebytes's native flat-key namespace (`arrays.positions`, `calc.energy`) with ColumnarStore. H5MDBackend should handle spec-mandated layout transformations on top of the shared base class.

**Instead:** `H5MDBackend` extends `BaseColumnarBackend` and overrides the store-interaction methods to use h5py directly with H5MD-compliant paths. It inherits `_postprocess`, `_classify_columns`, `_serialize_value` from the base.

### Anti-Pattern 3: Per-Test-File Backend Fixtures

**What:** Each of 40+ test files defining its own `@pytest.fixture(params=[...])` for backend selection.

**Why bad:** Adding a new backend requires touching every test file. Missing one file means missing test coverage for that backend. No guarantee of consistent parametrization.

**Instead:** Central `conftest.py` fixtures (`rw_backend`, `ro_backend`, `blob_backend`) with all backends parametrized once. Contract tests import and use these fixtures. Backend-specific edge-case tests live in `tests/backends/test_{backend}_specifics.py`.

### Anti-Pattern 4: Caching Offsets/Lengths at __init__ Time

**What:** The current `ColumnarBackend._discover()` loads `_offsets` and `_lengths` into numpy arrays at construction time and keeps them in memory.

**Why bad per project rules:** The MEMORY.md explicitly states "NEVER cache backend data -- another client can modify the data at any time; always read from backend." The offsets/lengths cache violates this rule. If another process extends the file, the cached offsets are stale.

**Nuance:** For performance, reading offsets every single `get()` call is expensive. The right approach is to re-read offsets at the start of each `get()`/`get_many()` call (one extra I/O per operation, not per frame). This is similar to how the `_n_frames` metadata should be re-read. Since HDF5 datasets are memory-mapped, re-reading the offset array is effectively free after the first access within a process.

**Recommendation:** Flag this as a known tension between the "never cache" rule and performance. The pragmatic path: keep the offset cache but add a `refresh()` method and document that concurrent multi-process writes require calling `refresh()`. Single-process usage (the 99% case) is safe because only one writer exists.

## Suggested Build Order

The dependency chain dictates this build order:

```
1. BaseColumnarBackend (extract from ColumnarBackend)
   |
   +---> 2a. RaggedColumnarBackend (move ragged logic from ColumnarBackend)
   +---> 2b. PaddedColumnarBackend (new, padded strategy using ColumnarStore)
   +---> 2c. H5MDBackend refactor (inherit from BaseColumnarBackend, keep h5py direct)
   |
   +---> 3. Registry updates (new extensions, remove legacy)
   |
   +---> 4. Contract test suite (tests/contract/)
   |
   +---> 5. Delete legacy Zarr backend, remove old ColumnarBackend alias
```

**Why this order:**

1. **BaseColumnarBackend first** because both ragged and padded depend on it. Extracting it from the existing ColumnarBackend is a pure refactor -- no behavior changes, just moving shared methods to a parent class. This is low-risk and unblocks everything else.

2. **Ragged + Padded + H5MD in parallel** because they only depend on BaseColumnarBackend, not on each other. RaggedColumnarBackend is essentially renaming the existing ColumnarBackend minus shared code. PaddedColumnarBackend is new but the padding logic already exists in `concat_varying` and H5MDBackend. H5MDBackend refactor means changing its inheritance from `ReadWriteBackend` to `BaseColumnarBackend` and deleting duplicated methods.

3. **Registry updates after backends exist** because registry entries need the classes to import.

4. **Contract tests after all backends are stable** because the test fixtures need to instantiate all backend variants. However, keeping existing tests passing throughout steps 1-3 is essential -- the contract suite augments, not replaces, existing tests during the transition.

5. **Legacy cleanup last** because it is the lowest-risk, highest-satisfaction step and has no downstream dependencies.

### Cross-Cutting Dependency: Shared Test Fixtures

The `conftest.py` already has universal fixtures (`uni_blob_backend`, `uni_object_backend`) parametrized across LMDB/Zarr/HDF5. These should be extended to include:
- `h5md` (H5MD backend)
- `h5-padded` / `zarr-padded` (padded columnar)
- `memory` (in-memory backend)

Fixture shape:

```python
@pytest.fixture(params=[
    "lmdb", "h5-ragged", "h5-padded", "zarr-ragged", "zarr-padded", "h5md", "memory"
])
def rw_object_backend(tmp_path, request):
    """Instantiate any writable object-level backend."""
    ...
```

## Scalability Considerations

| Concern | At 1K frames | At 100K frames | At 10M frames |
|---------|-------------|----------------|---------------|
| Offset array size (ragged) | 24 KB | 2.4 MB | 240 MB -- fits in RAM |
| Padded waste (10% size variance) | Negligible | ~10% disk overhead | Significant -- use ragged |
| Padded waste (10x size variance) | ~5x disk overhead | ~5x disk overhead | Unacceptable -- ragged only |
| H5MD read perf | Fine | NaN-stripping is O(max_atoms) per frame | Slow for ragged data |
| Ragged random-access | 1 seek + 1 read per frame | Same | Same (offset array is in memory) |
| Schema evolution (new column) | Backfill is instant | Backfill takes seconds | Backfill takes minutes -- pre-allocate |

**Key insight:** Ragged is strictly better for data with highly variable atom counts (molecular datasets). Padded is better for uniform-size data (crystals, bulk materials) because it avoids the offset indirection and enables simpler vectorized reads. H5MD padded is necessary for interop with znh5md but should not be the default for new data.

## Sources

- Direct codebase analysis of `src/asebytes/` (PRIMARY)
- H5MD specification: https://www.nongnu.org/h5md/h5md.html (MEDIUM confidence -- verified against codebase implementation)
- znh5md repository conventions (referenced in `_mapping.py` and `ORIGIN_ATTR`)
- pytest parametrize documentation for contract testing patterns

---

*Architecture analysis: 2026-03-06*
