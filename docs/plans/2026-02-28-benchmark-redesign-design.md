# Benchmark Suite Redesign

## Problem

The current benchmarks are unfair across backends:

- **Read**: sqlite/aselmdb use `db.select()` (1 query), while Redis/MongoDB use `[db[i] for i in range(n)]` (N round trips).
- **Write**: asebytes uses `db.extend(frames)` (bulk), while sqlite/aselmdb use `for mol: db.write(mol)` (sequential). Neither has a bulk write API, so this is inherently asymmetric.
- **No single-row benchmarks**: Can't isolate per-row overhead from bulk throughput.
- **No property-only benchmarks**: All reads reconstruct full `ase.Atoms` objects, hiding raw I/O cost.
- **No update benchmarks**.

## Approach

Each backend uses its most efficient API for each operation. Every operation is tested both single-row (latency) and bulk (throughput).

## Operation Matrix

| Operation | What it measures | asebytes API | sqlite/aselmdb API |
|---|---|---|---|
| **write_single** | Per-row write latency | `db.append(atoms)` loop | `db.write(atoms)` loop |
| **write_trajectory** | Bulk write throughput | `db.extend(frames)` | `for mol: db.write(mol)` (no bulk API) |
| **read_single** | Per-row Atoms read latency | `db[i]` loop | `db.get(id=i).toatoms()` loop |
| **read_trajectory** | Bulk Atoms read throughput | `db[:].to_list()` | `[row.toatoms() for row in db.select()]` |
| **random_single** | Random per-row Atoms read | `db[random_i]` loop | `db.get(id=random_i).toatoms()` loop |
| **random_trajectory** | Bulk random Atoms read | `db[random_indices].to_list()` | `[db.get(id=i).toatoms() for i in ids]` |
| **read_positions_single** | Per-row property read (no Atoms) | `ObjectIO(path)[i]["positions"]` loop | `db.get(id=i).positions` loop |
| **read_positions_trajectory** | Bulk property read (no Atoms) | `ObjectIO(path)["positions"].to_list()` | `[row.positions for row in db.select()]` |
| **column_energy** | Scalar column access | `ObjectIO(path)["calc.energy"].to_list()` | `[row.energy for row in db.select(columns=["id","energy"])]` |
| **update_property_trajectory** | Bulk column update | `ObjectIO(path)["calc.energy"][:].set(values)` | `for id, val: db.update(id, energy=val)` |

### Key API choices

- **`db[:].to_list()`** for bulk reads (uses `get_many` / pipelined), NOT `list(db[:])` (uses `__iter__` / per-row `get`).
- **`db[random_indices].to_list()`** for bulk random reads — passes list of indices directly, uses `get_many`.
- **`ColumnView.set()`** for bulk update — `ObjectIO["calc.energy"][:].set(values)`. Currently loops `_update_row` per row; bulk optimization deferred to a separate session.

### Backend-specific notes

- **extxyz**: Only write_trajectory and read_trajectory (no random/column access — requires full file scan).
- **znh5md**: Uses `h5py` direct for column_energy (`f["observables/.../value"][:]`), `znh5md.IO[:]` for bulk read.
- **Random indices**: `random.sample(range(n), n)` — truly random, no seed. pytest-benchmark handles statistical stability across rounds.
- **Single-row benchmarks**: Loop 100 iterations inside the benchmarked function to amortize pytest-benchmark overhead. Report per-iteration time via `benchmark.extra_info`.

## File Structure

```
tests/
  conftest.py                          # ethanol, lemat fixtures (unchanged)
  benchmarks/
    conftest.py                        # Shared fixtures: skip marks, URI constants,
                                       #   pre-populated DB fixtures per backend
    test_bench_write.py                # write_single, write_trajectory
    test_bench_read.py                 # read_single, read_trajectory
    test_bench_random_access.py        # random_single, random_trajectory
    test_bench_property_access.py      # read_positions_single, read_positions_trajectory,
                                       #   column_energy
    test_bench_update.py               # update_property_trajectory
```

## Shared Fixtures (`benchmarks/conftest.py`)

Pre-populated database fixtures so setup cost is excluded from benchmarks:

- `asebytes_lmdb_aseio` / `asebytes_lmdb_objectio` — pre-populated ASEIO and ObjectIO for LMDB
- Same pattern for zarr, h5md, redis, mongodb
- `sqlite_db` / `aselmdb_db` — pre-populated ASE database connections
- `znh5md_path` — pre-populated h5 file path + znh5md.IO handle

Each fixture creates the DB, writes the dataset, and yields it. Cleanup happens in fixture teardown (e.g. `db.remove()` for Redis/MongoDB).

## Visualization Updates

Update `docs/visualize_benchmarks.py` to handle the new operation names and grouped single/trajectory bars.

## Backends

All backends included: LMDB, Zarr, H5MD, Redis, MongoDB, aselmdb, znh5md, extxyz, sqlite.
