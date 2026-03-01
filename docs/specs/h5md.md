# H5MD Backend

**Layer:** Object (`ReadWriteBackend[str, Any]`)
**Async:** `SyncToAsyncAdapter` only (no native async)
**File:** `src/asebytes/h5md/_backend.py`

## Storage Layout

```mermaid
graph TD
    subgraph "HDF5 File"
        subgraph "/particles/{group}/"
            subgraph "Per-atom datasets"
                POS["positions/value<br>shape: (N_frames, max_atoms, 3)<br>NaN-padded"]
                NUM["numbers/value<br>shape: (N_frames, max_atoms)<br>species integers"]
            end
            subgraph "box/"
                EDGES["edges/value → (N_frames, 3, 3)"]
                BOUND["boundary/value → (3,) bool"]
            end
        end
        subgraph "/observables/{group}/"
            E["calc.energy/value → (N_frames,)"]
            F["calc.forces/value → (N_frames, max_atoms, 3)"]
            INFO["info.tag/value → (N_frames,) string"]
        end
        subgraph "/asebytes/{group}/"
            NA["_n_atoms → (N_frames,) int32"]
        end
        subgraph "/connectivity/{group}/"
            BONDS["bonds → (N_frames, max_bonds, 2)"]
        end
    end
```

**Placement rules:**
- Per-atom arrays (positions, numbers, forces) → `/particles/`
- Scalars and non-per-atom → `/observables/`
- `_n_atoms` auxiliary → `/asebytes/`
- Variable particle count: per-atom arrays padded with NaN to `max_atoms`

## Column Cache

```mermaid
graph LR
    subgraph "_col_cache: dict[str, tuple]"
        C1["'arrays.positions' → (Dataset, 'positions', PER_ATOM, True)"]
        C2["'calc.energy' → (Dataset, 'calc.energy', SCALAR_FLOAT, False)"]
        C3["'info.tag' → (Dataset, 'info.tag', STRING_JSON, False)"]
    end
    subgraph "_box_cache"
        B1["'cell' → ('td', Dataset)"]
        B2["'pbc' → ('boundary', Dataset)"]
    end
```

Each entry: `(h5py.Dataset, h5_name, _PostProc enum, is_per_atom: bool)`

## Read/Write Flow

```mermaid
sequenceDiagram
    participant F as Facade
    participant B as H5MDBackend
    participant H as h5py File

    Note over F,H: Bulk Read: db[:].to_list()
    F->>B: get_many(indices)
    B->>B: sort + deduplicate indices
    B->>H: _n_atoms[sorted_indices] (if per-atom cols needed)
    loop each column in _col_cache
        B->>H: dataset[sorted_indices] (fancy indexing)
    end
    B->>B: postprocess (slice per-atom, decode strings)
    B-->>F: list[dict[str, Any]]

    Note over F,H: Extend: db.extend(frames)
    F->>B: extend(data_dicts)
    B->>H: resize all datasets (N += len(data))
    loop each column
        B->>H: dataset[old_N:new_N] = values
    end
    B->>H: _n_atoms[old_N:new_N] = counts
```

## Performance

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| `len()` | O(1) | First dataset shape[0] |
| `get(i)` | O(C) | C = number of columns, one HDF5 read each |
| `get_many(N)` | O(C) | Fancy indexing per column, h5py optimizes contiguous ranges |
| `get_column(key)` | O(1) | Direct dataset slice |
| `extend(N)` | O(C×N) | Resize + write per column |
| `schema()` | O(C) | O(1) per column — reads dtype/shape from Dataset metadata |
| `insert/delete` | — | Not supported (append-only) |

**Benchmark (1000 ethanol, local):**

| Operation | Time |
|-----------|------|
| Trajectory read | 28ms |
| Single read ×1000 | 139ms |
| Column energy | 0.4ms |
| Write trajectory | 23ms |
| Write single ×1000 | 1527ms |

**Single-row overhead:** Each `db[i]` reads every column dataset independently. 139ms / 1000 = 0.14ms/row. Acceptable but slower than LMDB due to per-column HDF5 seeks.

## Sync/Async Consistency

No native async backend. Async via `SyncToAsyncAdapter` + `asyncio.to_thread()`.

h5py is not thread-safe by default. `SyncToAsyncAdapter` uses `asyncio.to_thread` which runs in a thread pool — must ensure only one thread accesses the file at a time.

## Potential Optimizations

- **O(1) schema:** Already implemented — reads dtype/shape from dataset metadata without loading data.
- **Conditional `_n_atoms`:** Already implemented — `_needs_n_atoms()` skips reading `_n_atoms` when no per-atom columns are requested.
- **Single-row reads:** Inherent overhead from per-column HDF5 seek. Could batch column reads with a single `h5py.File` context, but already doing so.
- **Write single:** 1527ms for 1000 single writes. Each `extend([frame])` resizes all datasets. Consider documenting that bulk `extend()` is 66× faster than single writes.
