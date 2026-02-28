"""Benchmark read performance: single-row and bulk trajectory.

read_single:      loop db[i] — measures per-row read + Atoms construction
read_trajectory:  db[:].to_list() — measures bulk read throughput (pipelined)
"""

from __future__ import annotations

import ase
import ase.io
import pytest

from .conftest import skip_no_mongo, skip_no_redis

# ===================================================================
# read_trajectory — bulk read
# ===================================================================


@pytest.mark.benchmark(group="read_trajectory")
def test_read_trajectory_asebytes_lmdb(benchmark, bench_lmdb):
    db = bench_lmdb.aseio

    def fn():
        return db[:].to_list()

    results = benchmark(fn)
    assert len(results) == len(bench_lmdb.frames)
    assert all(isinstance(a, ase.Atoms) for a in results)


@pytest.mark.benchmark(group="read_trajectory")
def test_read_trajectory_asebytes_zarr(benchmark, bench_zarr):
    db = bench_zarr.aseio

    def fn():
        return db[:].to_list()

    results = benchmark(fn)
    assert len(results) == len(bench_zarr.frames)


@pytest.mark.benchmark(group="read_trajectory")
def test_read_trajectory_asebytes_h5md(benchmark, bench_h5md):
    db = bench_h5md.aseio

    def fn():
        return db[:].to_list()

    results = benchmark(fn)
    assert len(results) == len(bench_h5md.frames)


@skip_no_mongo
@pytest.mark.benchmark(group="read_trajectory")
def test_read_trajectory_asebytes_mongodb(benchmark, bench_mongodb):
    db = bench_mongodb.aseio

    def fn():
        return db[:].to_list()

    results = benchmark(fn)
    assert len(results) == len(bench_mongodb.frames)
    bench_mongodb.cleanup()


@skip_no_redis
@pytest.mark.benchmark(group="read_trajectory")
def test_read_trajectory_asebytes_redis(benchmark, bench_redis):
    db = bench_redis.aseio

    def fn():
        return db[:].to_list()

    results = benchmark(fn)
    assert len(results) == len(bench_redis.frames)
    bench_redis.cleanup()


@pytest.mark.benchmark(group="read_trajectory")
def test_read_trajectory_aselmdb(benchmark, bench_aselmdb):
    db = bench_aselmdb.ase_db

    def fn():
        return [row.toatoms() for row in db.select()]

    results = benchmark(fn)
    assert len(results) == len(bench_aselmdb.frames)


@pytest.mark.benchmark(group="read_trajectory")
def test_read_trajectory_znh5md(benchmark, bench_znh5md):
    import h5py
    import znh5md

    p = bench_znh5md.znh5md_path

    def fn():
        with h5py.File(str(p), "r") as f:
            io = znh5md.IO(file_handle=f)
            return io[:]

    results = benchmark(fn)
    assert len(results) == len(bench_znh5md.frames)


@pytest.mark.benchmark(group="read_trajectory")
def test_read_trajectory_extxyz(benchmark, bench_extxyz):
    p = str(bench_extxyz.extxyz_path)

    def fn():
        return ase.io.read(p, index=":", format="extxyz")

    results = benchmark(fn)
    assert len(results) == len(bench_extxyz.frames)


@pytest.mark.benchmark(group="read_trajectory")
def test_read_trajectory_sqlite(benchmark, bench_sqlite):
    db = bench_sqlite.ase_db

    def fn():
        return [row.toatoms() for row in db.select()]

    results = benchmark(fn)
    assert len(results) == len(bench_sqlite.frames)


# ===================================================================
# read_single — per-row read in a loop
# ===================================================================


@pytest.mark.benchmark(group="read_single")
def test_read_single_asebytes_lmdb(benchmark, bench_lmdb):
    db = bench_lmdb.aseio
    n = len(db)

    def fn():
        return [db[i] for i in range(n)]

    results = benchmark(fn)
    assert len(results) == n
    assert all(isinstance(a, ase.Atoms) for a in results)


@pytest.mark.benchmark(group="read_single")
def test_read_single_asebytes_zarr(benchmark, bench_zarr):
    db = bench_zarr.aseio
    n = len(db)

    def fn():
        return [db[i] for i in range(n)]

    results = benchmark(fn)
    assert len(results) == n


@pytest.mark.benchmark(group="read_single")
def test_read_single_asebytes_h5md(benchmark, bench_h5md):
    db = bench_h5md.aseio
    n = len(db)

    def fn():
        return [db[i] for i in range(n)]

    results = benchmark(fn)
    assert len(results) == n


@skip_no_mongo
@pytest.mark.benchmark(group="read_single")
def test_read_single_asebytes_mongodb(benchmark, bench_mongodb):
    db = bench_mongodb.aseio
    n = len(db)

    def fn():
        return [db[i] for i in range(n)]

    results = benchmark(fn)
    assert len(results) == n
    bench_mongodb.cleanup()


@skip_no_redis
@pytest.mark.benchmark(group="read_single")
def test_read_single_asebytes_redis(benchmark, bench_redis):
    db = bench_redis.aseio
    n = len(db)

    def fn():
        return [db[i] for i in range(n)]

    results = benchmark(fn)
    assert len(results) == n
    bench_redis.cleanup()


@pytest.mark.benchmark(group="read_single")
def test_read_single_aselmdb(benchmark, bench_aselmdb):
    db = bench_aselmdb.ase_db
    n = len(bench_aselmdb.frames)

    def fn():
        # aselmdb uses 1-based IDs
        return [db.get(id=i).toatoms() for i in range(1, n + 1)]

    results = benchmark(fn)
    assert len(results) == n


@pytest.mark.benchmark(group="read_single")
def test_read_single_znh5md(benchmark, bench_znh5md):
    import h5py
    import znh5md

    p = bench_znh5md.znh5md_path
    n = len(bench_znh5md.frames)

    def fn():
        with h5py.File(str(p), "r") as f:
            io = znh5md.IO(file_handle=f)
            return [io[i] for i in range(n)]

    results = benchmark(fn)
    assert len(results) == n


@pytest.mark.benchmark(group="read_single")
def test_read_single_sqlite(benchmark, bench_sqlite):
    db = bench_sqlite.ase_db
    n = len(bench_sqlite.frames)

    def fn():
        # sqlite uses 1-based IDs
        return [db.get(id=i).toatoms() for i in range(1, n + 1)]

    results = benchmark(fn)
    assert len(results) == n
