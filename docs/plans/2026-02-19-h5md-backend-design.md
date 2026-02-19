# H5MD Backend Design

## Overview

A read-write H5MD backend for asebytes, built directly on h5py. Supports both
standard H5MD files and ZnH5MD extensions (variable particle count via NaN
padding, per-frame PBC). Append-only semantics — `insert_row` and `delete_row`
raise `NotImplementedError`.

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Access mode | Read-write | Full WritableBackend (append-only) |
| ZnH5MD extensions | Support both | Read strict H5MD and ZnH5MD. Write with extensions by default. |
| Mutability | Append-only | `append_rows`, `write_row` (overwrite). `insert_row`/`delete_row` → NotImplementedError. |
| Dependency | h5py directly | No znh5md dependency. We implement H5MD structure ourselves. |
| Connectivity | H5MD group + bond_order ext | Standard `connectivity/bonds` + custom `connectivity/bond_orders` dataset. |

## Key-to-H5MD Mapping

### Name Maps

```python
# asebytes key -> H5MD standard name within particles/<grp>/
PARTICLES_MAP = {
    "arrays.positions": "position",
    "arrays.numbers": "species",
    "arrays.velocities": "velocity",
    "calc.forces": "force",
}

# asebytes key -> H5MD standard name within observables/<grp>/
OBSERVABLES_MAP = {
    "calc.energy": "potential_energy",
    "calc.stress": "stress",
    "calc.free_energy": "free_energy",
}

# Reverse maps built automatically for reading
REVERSE_PARTICLES_MAP = {v: k for k, v in PARTICLES_MAP.items()}
REVERSE_OBSERVABLES_MAP = {v: k for k, v in OBSERVABLES_MAP.items()}
```

### Full Mapping Table

| asebytes key | H5MD path | Storage mode |
|---|---|---|
| `arrays.positions` | `particles/<grp>/position/{step,time,value}` | Always time-dependent |
| `arrays.numbers` | `particles/<grp>/species` (dataset) or `species/{step,time,value}` | Time-independent if constant across frames, else time-dependent |
| `arrays.velocities` | `particles/<grp>/velocity/{step,time,value}` | Time-dependent |
| `arrays.<custom>` | `particles/<grp>/<custom>/{step,time,value}` | Time-dependent per-atom |
| `cell` | `particles/<grp>/box/edges` (dataset) or `box/edges/{step,time,value}` | Time-independent if constant, else time-dependent |
| `pbc` | `box.attrs["boundary"]` + `box/pbc/{step,time,value}` | Attribute from first frame; ZnH5MD extension for per-frame |
| `calc.energy` | `observables/<grp>/potential_energy/{step,time,value}` | Scalar observable |
| `calc.forces` | `particles/<grp>/force/{step,time,value}` | Per-atom, time-dependent |
| `calc.stress` | `observables/<grp>/stress/{step,time,value}` | 6-component, time-dependent |
| `calc.<other>` | `observables/<grp>/<key>` (scalar) or `particles/<grp>/<key>` (per-atom) | Shape-dependent routing |
| `info.<key>` | `particles/<grp>/info/<key>/{step,time,value}` | ZnH5MD convention |
| `constraints` | `particles/<grp>/info/constraints/{step,time,value}` | JSON-serialized string |
| connectivity | `connectivity/bonds` + `connectivity/bond_orders` | Time-independent datasets |

### H5MD Element Storage Conventions

- **Time-dependent**: stored as a group with `step`, `time`, `value` sub-datasets.
  First dimension of `value` is the frame axis.
- **Time-independent**: stored as a plain dataset (no `value` sub-group).
- **Box**: `particles/<grp>/box` with `dimension` (int attr) and `boundary`
  (string array attr, e.g. `["periodic", "periodic", "periodic"]`).
  `edges` is a dataset (orthorhombic/constant) or time-dependent element (triclinic/varying).

### Read Discovery

On open, the backend does NOT assume a fixed layout. Instead it walks the HDF5
tree and builds an internal `{asebytes_key: H5Element}` map:

1. Walk `particles/<grp>/` — match known names via reverse map, anything
   unknown becomes `arrays.<name>`
2. Walk `observables/<grp>/` — match known names via reverse map, anything
   unknown becomes `calc.<name>`
3. Walk `particles/<grp>/info/` — everything becomes `info.<name>` (ZnH5MD convention)
4. Check `connectivity/` for bonds and bond_orders
5. Check `box/` for cell and PBC

This enables reading files produced by any H5MD writer.

## Class API

```python
class H5MDBackend(WritableBackend):
    """Read-write H5MD backend using h5py.

    Supports standard H5MD files and ZnH5MD extensions
    (variable particle count, per-frame PBC).
    """

    def __init__(
        self,
        file: str | Path | None = None,
        *,
        file_handle: h5py.File | None = None,  # for fsspec / external handles
        particles_group: str = "atoms",
        readonly: bool = False,
        compression: str | None = "gzip",
        compression_opts: int = 4,
        variable_shape: bool = True,
        pbc_group: bool = True,
        chunk_size: int = 64,
        rdcc_nbytes: int | None = None,   # chunk cache size
        rdcc_w0: float | None = None,      # eviction policy
    ):
        if file_handle is not None:
            self._file = file_handle
            self._owns_file = False  # don't close on exit
        elif file is not None:
            mode = "r" if readonly else "a"
            kwargs = {}
            if rdcc_nbytes is not None:
                kwargs["rdcc_nbytes"] = rdcc_nbytes
            if rdcc_w0 is not None:
                kwargs["rdcc_w0"] = rdcc_w0
            self._file = h5py.File(file, mode, **kwargs)
            self._owns_file = True
        else:
            raise ValueError("Provide either file or file_handle")

        self._grp_name = particles_group
        self._readonly = readonly
        self._compression = compression
        self._compression_opts = compression_opts
        self._variable_shape = variable_shape
        self._pbc_group = pbc_group
        self._chunk_size = chunk_size

        self._discover_layout()

    # --- ReadableBackend ---
    def __len__(self) -> int: ...
    def columns(self, index: int = 0) -> list[str]: ...
    def read_row(self, index: int, keys=None) -> dict[str, Any]: ...
    def read_rows(self, indices, keys=None) -> list[dict]: ...
    def iter_rows(self, indices, keys=None) -> Iterator[dict]: ...
    def read_column(self, key: str, indices=None) -> list[Any]: ...

    # --- WritableBackend (append-only) ---
    def append_rows(self, data_list: list[dict]) -> None: ...
    def write_row(self, index: int, data: dict) -> None: ...
    def insert_row(self, index, data):
        raise NotImplementedError("H5MD does not support insert")
    def delete_row(self, index):
        raise NotImplementedError("H5MD does not support delete")

    # --- Lifecycle ---
    def close(self):
        if self._owns_file:
            self._file.close()

    def __enter__(self): return self
    def __exit__(self, *exc): self.close()
```

### fsspec Compatibility

The `file_handle` parameter enables remote file systems:

```python
with fs.open(path, "rb") as f:
    with h5py.File(f) as h5:
        backend = H5MDBackend(file_handle=h5, readonly=True)
        frames = backend.read_rows(range(len(backend)))
```

## Read Flow

### `_discover_layout()`

Called once on open. Walks the HDF5 tree and builds an internal map of
`{asebytes_key: H5Element}` where `H5Element` is a dataclass holding the
h5py dataset reference, whether it's time-dependent, shape info, and fill value.

```python
def _discover_layout(self):
    self._elements = {}
    self._n_frames = 0
    self._max_atoms = 0
    self._connectivity = None

    if "particles" not in self._file:
        return

    grp = self._find_particles_group()

    for name in grp:
        if name == "box":
            self._discover_box(grp["box"])
            continue
        if name == "info":
            self._discover_info(grp["info"])
            continue
        asebytes_key = REVERSE_PARTICLES_MAP.get(name, f"arrays.{name}")
        self._register_element(asebytes_key, grp[name])

    if "observables" in self._file:
        obs = self._file["observables"]
        obs_grp = obs.get(self._grp_name, obs)
        for name in obs_grp:
            if not isinstance(obs_grp[name], h5py.Group):
                continue
            asebytes_key = REVERSE_OBSERVABLES_MAP.get(name, f"calc.{name}")
            self._register_element(asebytes_key, obs_grp[name])

    if "connectivity" in self._file:
        self._discover_connectivity()

    pos_elem = self._elements.get("arrays.positions")
    if pos_elem and pos_elem.is_time_dependent:
        self._n_frames = pos_elem.shape[0]
```

### `read_row(index, keys=None)`

Reads one frame by indexing into each discovered element's dataset:

```python
def read_row(self, index: int, keys=None) -> dict[str, Any]:
    result = {}
    target_keys = keys or self._elements.keys()

    for key in target_keys:
        elem = self._elements[key]
        if elem.is_time_dependent:
            val = elem.dataset[index]
        else:
            val = elem.dataset[()]
        if self._variable_shape and val.ndim >= 1:
            val = self._strip_padding(val)
        result[key] = val

    if self._connectivity is not None and (keys is None or "info.connectivity" in keys):
        result["info.connectivity"] = self._connectivity

    return result
```

### `read_column(key, indices=None)`

The performance star — reads a single HDF5 dataset directly:

```python
def read_column(self, key: str, indices=None) -> list[Any]:
    elem = self._elements[key]
    if indices is None:
        data = elem.dataset[()]
    else:
        data = elem.dataset[indices]
    if self._variable_shape:
        return [self._strip_padding(row) for row in data]
    return list(data)
```

## Write Flow

### `append_rows(data_list)`

Two phases: (1) create structure on first write, (2) resize and append.

```python
def append_rows(self, data_list: list[dict]) -> None:
    if not data_list:
        return

    n_new = len(data_list)

    if self._n_frames == 0:
        self._init_h5md_structure()

    # Determine max_atoms for this batch
    atom_counts = []
    for row in data_list:
        if "arrays.positions" in row:
            atom_counts.append(len(row["arrays.positions"]))
    new_max = max(atom_counts) if atom_counts else 0

    if new_max > self._max_atoms:
        self._resize_atom_dim(new_max)
        self._max_atoms = new_max

    all_keys = set().union(*(row.keys() for row in data_list))
    for key in all_keys:
        if key not in self._elements:
            self._create_element(key, data_list)
        self._append_to_element(key, data_list, n_new)

    # Write connectivity once from first frame that has it
    if self._connectivity is None:
        self._write_connectivity(data_list)

    self._n_frames += n_new
```

### `_init_h5md_structure()`

Creates the mandatory H5MD skeleton:

```python
def _init_h5md_structure(self):
    h5md = self._file.create_group("h5md")
    h5md.attrs["version"] = np.array([1, 1], dtype=np.int32)
    h5md.create_group("author")
    h5md.create_group("creator")

    grp = self._file.create_group(f"particles/{self._grp_name}")
    box = grp.create_group("box")
    box.attrs["dimension"] = 3
    # boundary attr set from first frame's pbc
```

### `_create_element(key, data_list)`

Routes each asebytes key to the correct H5MD location and creates the dataset
with appropriate shape, compression, and chunking.

Per-atom datasets: `(0, max_atoms, D)` with `maxshape=(None, None, D)`.
Scalar datasets: `(0,)` with `maxshape=(None,)`.

New datasets appearing after the first frame are backfilled with NaN/defaults
for the already-written frames.

### `write_row(index, data)`

Overwrites an existing frame in-place via HDF5 dataset indexing.

## Connectivity

### Writing (molify → H5MD)

```python
def _write_connectivity(self, data_list):
    for row in data_list:
        if "info.connectivity" not in row:
            continue
        conn = row["info.connectivity"]
        bonds = np.array([(a, b) for a, b, _ in conn], dtype=np.int32)
        bond_orders = np.array([bo for _, _, bo in conn], dtype=np.float64)

        grp = self._file.require_group("connectivity")
        grp.create_dataset("bonds", data=bonds)
        grp["bonds"].attrs["particles_group"] = self._particles_grp.ref
        grp.create_dataset("bond_orders", data=bond_orders)
        break  # time-independent, write once
```

### Reading (H5MD → molify format)

```python
def _discover_connectivity(self):
    conn = self._file["connectivity"]
    if "bonds" in conn:
        bonds = conn["bonds"][()]
        bond_orders = conn.get("bond_orders", None)
        if bond_orders is not None:
            bond_orders = bond_orders[()]
            self._connectivity = [
                (int(a), int(b), float(bo))
                for (a, b), bo in zip(bonds, bond_orders)
            ]
        else:
            self._connectivity = [(int(a), int(b), None) for a, b in bonds]
```

## Performance

### Chunking Strategy

Chunk shape balances row-oriented and column-oriented access:

```python
# Per-atom data: (N_frames, max_atoms, D)
chunks = (min(chunk_size, n_frames), max_atoms, D)

# Scalar observables: (N_frames,)
chunks = (min(chunk_size, n_frames),)
```

Default `chunk_size=64`. Constructor exposes `rdcc_nbytes` and `rdcc_w0` for
h5py chunk cache tuning.

### h5py Chunk Cache

- `rdcc_nbytes`: total chunk cache size (default 1 MiB). Increase for large
  datasets with random access.
- `rdcc_w0`: eviction policy. `1.0` for sequential iteration, `0.0` for
  random access (LRU). Default `0.75`.
- `rdcc_nslots`: hash table size (prime, ~100x chunks in cache).

Per-dataset chunk cache available since h5py 3.8 via
`create_dataset(..., rdcc_nbytes=...)`.

## Registration

Add to `_registry.py`:

```python
_BACKEND_REGISTRY = {
    "*.lmdb": ("asebytes.lmdb", "LMDBBackend", "LMDBReadOnlyBackend"),
    "*.h5":   ("asebytes.h5md", "H5MDBackend", "H5MDBackend"),
    "*.h5md": ("asebytes.h5md", "H5MDBackend", "H5MDBackend"),
    "*.traj": ("asebytes.ase", None, "ASEReadOnlyBackend"),
    ...
}
```

## File Structure

```
src/asebytes/h5md/
    __init__.py      # exports H5MDBackend
    _backend.py      # H5MDBackend class
    _mapping.py      # PARTICLES_MAP, OBSERVABLES_MAP, reverse maps
    _elements.py     # H5Element dataclass, discover/create helpers
```

## Testing

1. **Round-trip** — write atoms via H5MDBackend, read back, compare all fields
2. **Variable shape** — write frames with different atom counts, verify padding/stripping
3. **ZnH5MD compat** — write with znh5md, read with our backend (and vice versa)
4. **Column reads** — verify `read_column("calc.energy")` returns correct values
5. **Connectivity** — write molify atoms with bonds, verify H5MD connectivity group, read back
6. **Foreign files** — read H5MD files from other tools
7. **Append after close** — open existing file, append more frames, verify continuity
8. **fsspec** — test with `file_handle` parameter using a mock file-like object
