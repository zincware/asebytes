"""Benchmark property access: positions (single/bulk) and energy column.

read_positions_single:      loop ObjectIO[i]["arrays.positions"] — per-row property read
read_positions_trajectory:  ObjectIO["arrays.positions"].to_list() — bulk property read
column_energy:              ObjectIO["calc.energy"].to_list() — scalar column access

All property benchmarks use ObjectIO (not ASEIO) to measure raw I/O
without Atoms construction overhead.

extxyz is excluded — no random/column access.
"""

from __future__ import annotations

import pytest

from asebytes import ObjectIO
from asebytes._convert import atoms_to_dict

from .conftest import skip_no_mongo, skip_no_redis

# ===================================================================
# read_positions_trajectory — bulk property read
# ===================================================================


@pytest.mark.benchmark(group="read_positions_trajectory")
def test_read_positions_trajectory_asebytes_lmdb(benchmark, bench_lmdb):
    db = bench_lmdb.objectio

    def fn():
        return db["arrays.positions"].to_list()

    results = benchmark(fn)
    assert len(results) == len(bench_lmdb.frames)


@pytest.mark.benchmark(group="read_positions_trajectory")
def test_read_positions_trajectory_asebytes_zarr(benchmark, bench_zarr):
    db = bench_zarr.objectio

    def fn():
        return db["arrays.positions"].to_list()

    results = benchmark(fn)
    assert len(results) == len(bench_zarr.frames)


@pytest.mark.benchmark(group="read_positions_trajectory")
def test_read_positions_trajectory_asebytes_h5md(benchmark, bench_h5md):
    db = bench_h5md.objectio

    def fn():
        return db["arrays.positions"].to_list()

    results = benchmark(fn)
    assert len(results) == len(bench_h5md.frames)


@skip_no_mongo
@pytest.mark.benchmark(group="read_positions_trajectory")
def test_read_positions_trajectory_asebytes_mongodb(benchmark, bench_mongodb):
    db = bench_mongodb.objectio

    def fn():
        return db["arrays.positions"].to_list()

    results = benchmark(fn)
    assert len(results) == len(bench_mongodb.frames)



@skip_no_redis
@pytest.mark.benchmark(group="read_positions_trajectory")
def test_read_positions_trajectory_asebytes_redis(benchmark, bench_redis):
    db = bench_redis.objectio

    def fn():
        return db["arrays.positions"].to_list()

    results = benchmark(fn)
    assert len(results) == len(bench_redis.frames)



@pytest.mark.benchmark(group="read_positions_trajectory")
def test_read_positions_trajectory_aselmdb(benchmark, bench_aselmdb):
    db = bench_aselmdb.ase_db

    def fn():
        return [row.positions for row in db.select()]

    results = benchmark(fn)
    assert len(results) == len(bench_aselmdb.frames)


@pytest.mark.benchmark(group="read_positions_trajectory")
def test_read_positions_trajectory_znh5md(benchmark, bench_znh5md):
    import h5py

    p = bench_znh5md.znh5md_path

    def fn():
        with h5py.File(str(p), "r") as f:
            return f["particles/atoms/position/value"][:].tolist()

    results = benchmark(fn)
    assert len(results) == len(bench_znh5md.frames)


@pytest.mark.benchmark(group="read_positions_trajectory")
def test_read_positions_trajectory_sqlite(benchmark, bench_sqlite):
    db = bench_sqlite.ase_db

    def fn():
        return [row.positions for row in db.select()]

    results = benchmark(fn)
    assert len(results) == len(bench_sqlite.frames)


# ===================================================================
# read_positions_single — per-row property read in a loop
# ===================================================================


@pytest.mark.benchmark(group="read_positions_single")
def test_read_positions_single_asebytes_lmdb(benchmark, bench_lmdb):
    db = bench_lmdb.objectio
    n = len(db)

    def fn():
        return [db[i]["arrays.positions"] for i in range(n)]

    results = benchmark(fn)
    assert len(results) == n


@pytest.mark.benchmark(group="read_positions_single")
def test_read_positions_single_asebytes_zarr(benchmark, bench_zarr):
    db = bench_zarr.objectio
    n = len(db)

    def fn():
        return [db[i]["arrays.positions"] for i in range(n)]

    results = benchmark(fn)
    assert len(results) == n


@pytest.mark.benchmark(group="read_positions_single")
def test_read_positions_single_asebytes_h5md(benchmark, bench_h5md):
    db = bench_h5md.objectio
    n = len(db)

    def fn():
        return [db[i]["arrays.positions"] for i in range(n)]

    results = benchmark(fn)
    assert len(results) == n


@skip_no_mongo
@pytest.mark.benchmark(group="read_positions_single")
def test_read_positions_single_asebytes_mongodb(benchmark, bench_mongodb):
    db = bench_mongodb.objectio
    n = len(db)

    def fn():
        return [db[i]["arrays.positions"] for i in range(n)]

    results = benchmark(fn)
    assert len(results) == n



@skip_no_redis
@pytest.mark.benchmark(group="read_positions_single")
def test_read_positions_single_asebytes_redis(benchmark, bench_redis):
    db = bench_redis.objectio
    n = len(db)

    def fn():
        return [db[i]["arrays.positions"] for i in range(n)]

    results = benchmark(fn)
    assert len(results) == n



@pytest.mark.benchmark(group="read_positions_single")
def test_read_positions_single_aselmdb(benchmark, bench_aselmdb):
    db = bench_aselmdb.ase_db
    n = len(bench_aselmdb.frames)

    def fn():
        # aselmdb uses 1-based IDs
        return [db.get(id=i).positions for i in range(1, n + 1)]

    results = benchmark(fn)
    assert len(results) == n


@pytest.mark.benchmark(group="read_positions_single")
def test_read_positions_single_znh5md(benchmark, bench_znh5md):
    import h5py
    import znh5md

    p = bench_znh5md.znh5md_path
    n = len(bench_znh5md.frames)

    def fn():
        with h5py.File(str(p), "r") as f:
            io = znh5md.IO(file_handle=f)
            return [io[i].positions for i in range(n)]

    results = benchmark(fn)
    assert len(results) == n


@pytest.mark.benchmark(group="read_positions_single")
def test_read_positions_single_sqlite(benchmark, bench_sqlite):
    db = bench_sqlite.ase_db
    n = len(bench_sqlite.frames)

    def fn():
        # sqlite uses 1-based IDs
        return [db.get(id=i).positions for i in range(1, n + 1)]

    results = benchmark(fn)
    assert len(results) == n


# ===================================================================
# column_energy — scalar column access
# ===================================================================


@pytest.mark.benchmark(group="column_energy")
def test_column_energy_asebytes_lmdb(benchmark, bench_lmdb):
    db = bench_lmdb.objectio

    def fn():
        return db["calc.energy"].to_list()

    results = benchmark(fn)
    assert len(results) == len(bench_lmdb.frames)


@pytest.mark.benchmark(group="column_energy")
def test_column_energy_asebytes_zarr(benchmark, bench_zarr):
    db = bench_zarr.objectio

    def fn():
        return db["calc.energy"].to_list()

    results = benchmark(fn)
    assert len(results) == len(bench_zarr.frames)


@pytest.mark.benchmark(group="column_energy")
def test_column_energy_asebytes_h5md(benchmark, bench_h5md):
    db = bench_h5md.objectio

    def fn():
        return db["calc.energy"].to_list()

    results = benchmark(fn)
    assert len(results) == len(bench_h5md.frames)


@skip_no_mongo
@pytest.mark.benchmark(group="column_energy")
def test_column_energy_asebytes_mongodb(benchmark, bench_mongodb):
    db = bench_mongodb.objectio

    def fn():
        return db["calc.energy"].to_list()

    results = benchmark(fn)
    assert len(results) == len(bench_mongodb.frames)



@skip_no_redis
@pytest.mark.benchmark(group="column_energy")
def test_column_energy_asebytes_redis(benchmark, bench_redis):
    db = bench_redis.objectio

    def fn():
        return db["calc.energy"].to_list()

    results = benchmark(fn)
    assert len(results) == len(bench_redis.frames)



@pytest.mark.benchmark(group="column_energy")
def test_column_energy_aselmdb(benchmark, bench_aselmdb):
    db = bench_aselmdb.ase_db

    def fn():
        return [row.energy for row in db.select(columns=["id", "energy"])]

    results = benchmark(fn)
    assert len(results) == len(bench_aselmdb.frames)


@pytest.mark.benchmark(group="column_energy")
def test_column_energy_znh5md(benchmark, bench_znh5md):
    import h5py

    p = bench_znh5md.znh5md_path

    def fn():
        with h5py.File(str(p), "r") as f:
            return f["observables/atoms/potential_energy/value"][:].tolist()

    results = benchmark(fn)
    assert len(results) == len(bench_znh5md.frames)


@pytest.mark.benchmark(group="column_energy")
def test_column_energy_sqlite(benchmark, bench_sqlite):
    db = bench_sqlite.ase_db

    def fn():
        return [row.energy for row in db.select(columns=["id", "energy"])]

    results = benchmark(fn)
    assert len(results) == len(bench_sqlite.frames)
