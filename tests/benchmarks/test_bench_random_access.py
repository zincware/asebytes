"""Benchmark random access performance: single-row and bulk trajectory.

random_single:      loop db[random_i] — measures per-row random read
random_trajectory:  db[random_indices].to_list() — measures bulk random read (pipelined)

Random indices are truly random (no seed). pytest-benchmark handles
statistical stability across rounds.

extxyz is excluded — requires full file scan per access.
"""

from __future__ import annotations

import ase
import pytest

from .conftest import random_indices

# ===================================================================
# random_trajectory — bulk random read
# ===================================================================


@pytest.mark.benchmark(group="random_trajectory")
def test_random_trajectory_asebytes_lmdb(benchmark, bench_lmdb):
    db = bench_lmdb.aseio
    n = len(db)
    indices = random_indices(n)

    def fn():
        return db[indices].to_list()

    results = benchmark(fn)
    assert len(results) == n
    assert all(isinstance(a, ase.Atoms) for a in results)


@pytest.mark.benchmark(group="random_trajectory")
def test_random_trajectory_asebytes_zarr(benchmark, bench_zarr):
    db = bench_zarr.aseio
    n = len(db)
    indices = random_indices(n)

    def fn():
        return db[indices].to_list()

    results = benchmark(fn)
    assert len(results) == n


@pytest.mark.benchmark(group="random_trajectory")
def test_random_trajectory_asebytes_h5md(benchmark, bench_h5md):
    db = bench_h5md.aseio
    n = len(db)
    indices = random_indices(n)

    def fn():
        return db[indices].to_list()

    results = benchmark(fn)
    assert len(results) == n


@pytest.mark.benchmark(group="random_trajectory")
def test_random_trajectory_asebytes_mongodb(benchmark, bench_mongodb):
    db = bench_mongodb.aseio
    n = len(db)
    indices = random_indices(n)

    def fn():
        return db[indices].to_list()

    results = benchmark(fn)
    assert len(results) == n



@pytest.mark.benchmark(group="random_trajectory")
def test_random_trajectory_asebytes_redis(benchmark, bench_redis):
    db = bench_redis.aseio
    n = len(db)
    indices = random_indices(n)

    def fn():
        return db[indices].to_list()

    results = benchmark(fn)
    assert len(results) == n



@pytest.mark.benchmark(group="random_trajectory")
def test_random_trajectory_aselmdb(benchmark, bench_aselmdb):
    db = bench_aselmdb.ase_db
    n = len(bench_aselmdb.frames)
    # aselmdb uses 1-based IDs
    indices = [i + 1 for i in random_indices(n)]

    def fn():
        return [db.get(id=i).toatoms() for i in indices]

    results = benchmark(fn)
    assert len(results) == n


@pytest.mark.benchmark(group="random_trajectory")
def test_random_trajectory_znh5md(benchmark, bench_znh5md):
    import h5py
    import znh5md

    p = bench_znh5md.znh5md_path
    n = len(bench_znh5md.frames)
    indices = random_indices(n)

    def fn():
        with h5py.File(str(p), "r") as f:
            io = znh5md.IO(file_handle=f)
            return [io[i] for i in indices]

    results = benchmark(fn)
    assert len(results) == n


@pytest.mark.benchmark(group="random_trajectory")
def test_random_trajectory_sqlite(benchmark, bench_sqlite):
    db = bench_sqlite.ase_db
    n = len(bench_sqlite.frames)
    # sqlite uses 1-based IDs
    indices = [i + 1 for i in random_indices(n)]

    def fn():
        return [db.get(id=i).toatoms() for i in indices]

    results = benchmark(fn)
    assert len(results) == n


# ===================================================================
# random_single — per-row random read in a loop
# ===================================================================


@pytest.mark.benchmark(group="random_single")
def test_random_single_asebytes_lmdb(benchmark, bench_lmdb):
    db = bench_lmdb.aseio
    n = len(db)
    indices = random_indices(n)

    def fn():
        return [db[i] for i in indices]

    results = benchmark(fn)
    assert len(results) == n
    assert all(isinstance(a, ase.Atoms) for a in results)


@pytest.mark.benchmark(group="random_single")
def test_random_single_asebytes_zarr(benchmark, bench_zarr):
    db = bench_zarr.aseio
    n = len(db)
    indices = random_indices(n)

    def fn():
        return [db[i] for i in indices]

    results = benchmark(fn)
    assert len(results) == n


@pytest.mark.benchmark(group="random_single")
def test_random_single_asebytes_h5md(benchmark, bench_h5md):
    db = bench_h5md.aseio
    n = len(db)
    indices = random_indices(n)

    def fn():
        return [db[i] for i in indices]

    results = benchmark(fn)
    assert len(results) == n


@pytest.mark.benchmark(group="random_single")
def test_random_single_asebytes_mongodb(benchmark, bench_mongodb):
    db = bench_mongodb.aseio
    n = len(db)
    indices = random_indices(n)

    def fn():
        return [db[i] for i in indices]

    results = benchmark(fn)
    assert len(results) == n



@pytest.mark.benchmark(group="random_single")
def test_random_single_asebytes_redis(benchmark, bench_redis):
    db = bench_redis.aseio
    n = len(db)
    indices = random_indices(n)

    def fn():
        return [db[i] for i in indices]

    results = benchmark(fn)
    assert len(results) == n



@pytest.mark.benchmark(group="random_single")
def test_random_single_aselmdb(benchmark, bench_aselmdb):
    db = bench_aselmdb.ase_db
    n = len(bench_aselmdb.frames)
    # aselmdb uses 1-based IDs
    indices = [i + 1 for i in random_indices(n)]

    def fn():
        return [db.get(id=i).toatoms() for i in indices]

    results = benchmark(fn)
    assert len(results) == n


@pytest.mark.benchmark(group="random_single")
def test_random_single_znh5md(benchmark, bench_znh5md):
    import h5py
    import znh5md

    p = bench_znh5md.znh5md_path
    n = len(bench_znh5md.frames)
    indices = random_indices(n)

    def fn():
        with h5py.File(str(p), "r") as f:
            io = znh5md.IO(file_handle=f)
            return [io[i] for i in indices]

    results = benchmark(fn)
    assert len(results) == n


@pytest.mark.benchmark(group="random_single")
def test_random_single_sqlite(benchmark, bench_sqlite):
    db = bench_sqlite.ase_db
    n = len(bench_sqlite.frames)
    # sqlite uses 1-based IDs
    indices = [i + 1 for i in random_indices(n)]

    def fn():
        return [db.get(id=i).toatoms() for i in indices]

    results = benchmark(fn)
    assert len(results) == n
