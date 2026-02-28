"""Benchmark update performance: bulk column update.

update_property_trajectory:  ObjectIO["calc.energy"][:].set(values) — bulk column overwrite

extxyz is excluded — no update support.
znh5md is excluded — no per-field update support.
"""

from __future__ import annotations

import pytest

from .conftest import skip_no_mongo, skip_no_redis

# ===================================================================
# update_property_trajectory — bulk column update
# ===================================================================


@pytest.mark.benchmark(group="update_property_trajectory")
def test_update_property_trajectory_asebytes_lmdb(benchmark, bench_lmdb):
    db = bench_lmdb.objectio
    n = len(db)
    new_energies = [float(i) * 0.01 for i in range(n)]

    def fn():
        db["calc.energy"][:].set(new_energies)

    benchmark(fn)


@pytest.mark.benchmark(group="update_property_trajectory")
def test_update_property_trajectory_asebytes_zarr(benchmark, bench_zarr):
    db = bench_zarr.objectio
    n = len(db)
    new_energies = [float(i) * 0.01 for i in range(n)]

    def fn():
        db["calc.energy"][:].set(new_energies)

    benchmark(fn)


@pytest.mark.benchmark(group="update_property_trajectory")
def test_update_property_trajectory_asebytes_h5md(benchmark, bench_h5md):
    db = bench_h5md.objectio
    n = len(db)
    new_energies = [float(i) * 0.01 for i in range(n)]

    def fn():
        db["calc.energy"][:].set(new_energies)

    benchmark(fn)


@skip_no_mongo
@pytest.mark.benchmark(group="update_property_trajectory")
def test_update_property_trajectory_asebytes_mongodb(benchmark, bench_mongodb):
    db = bench_mongodb.objectio
    n = len(db)
    new_energies = [float(i) * 0.01 for i in range(n)]

    def fn():
        db["calc.energy"][:].set(new_energies)

    benchmark(fn)
    bench_mongodb.cleanup()


@skip_no_redis
@pytest.mark.benchmark(group="update_property_trajectory")
def test_update_property_trajectory_asebytes_redis(benchmark, bench_redis):
    db = bench_redis.objectio
    n = len(db)
    new_energies = [float(i) * 0.01 for i in range(n)]

    def fn():
        db["calc.energy"][:].set(new_energies)

    benchmark(fn)
    bench_redis.cleanup()


@pytest.mark.benchmark(group="update_property_trajectory")
def test_update_property_trajectory_aselmdb(benchmark, bench_aselmdb):
    db = bench_aselmdb.ase_db
    n = len(bench_aselmdb.frames)
    new_energies = [float(i) * 0.01 for i in range(n)]

    def fn():
        # aselmdb uses 1-based IDs
        for i, e in enumerate(new_energies, 1):
            db.update(i, energy=e)

    benchmark(fn)


@pytest.mark.benchmark(group="update_property_trajectory")
def test_update_property_trajectory_sqlite(benchmark, bench_sqlite):
    db = bench_sqlite.ase_db
    n = len(bench_sqlite.frames)
    new_energies = [float(i) * 0.01 for i in range(n)]

    def fn():
        # sqlite uses 1-based IDs
        for i, e in enumerate(new_energies, 1):
            db.update(i, energy=e)

    benchmark(fn)
