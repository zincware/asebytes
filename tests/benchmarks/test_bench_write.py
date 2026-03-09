"""Benchmark write performance: single-row and bulk trajectory.

write_single:      loop db.extend([mol]) — measures per-row write overhead
write_trajectory:  db.extend(frames) — measures bulk write throughput
"""

from __future__ import annotations

import uuid

import ase.io
import pytest
from ase.db import connect

from asebytes import ASEIO


# ===================================================================
# write_trajectory — bulk write
# ===================================================================


@pytest.mark.benchmark(group="write_trajectory")
def test_write_trajectory_asebytes_lmdb(benchmark, dataset, tmp_path):
    name, frames = dataset

    def fn():
        p = tmp_path / f"wt_{name}_lmdb_{uuid.uuid4().hex}.lmdb"
        db = ASEIO(str(p))
        db.extend(frames)

    benchmark(fn)


@pytest.mark.benchmark(group="write_trajectory")
def test_write_trajectory_asebytes_zarr(benchmark, dataset, tmp_path):
    name, frames = dataset

    def fn():
        p = tmp_path / f"wt_{name}_zarr_{uuid.uuid4().hex}.zarr"
        db = ASEIO(str(p))
        db.extend(frames)

    benchmark(fn)


@pytest.mark.benchmark(group="write_trajectory")
def test_write_trajectory_asebytes_h5md(benchmark, dataset, tmp_path):
    name, frames = dataset

    def fn():
        p = tmp_path / f"wt_{name}_h5md_{uuid.uuid4().hex}.h5"
        db = ASEIO(str(p))
        db.extend(frames)

    benchmark(fn)


@pytest.mark.benchmark(group="write_trajectory")
def test_write_trajectory_asebytes_mongodb(benchmark, dataset, mongo_uri):
    name, frames = dataset
    dbs = []

    def fn():
        uri = f"{mongo_uri}/bench_wt_{name}_{uuid.uuid4().hex[:8]}"
        db = ASEIO(uri)
        db.extend(frames)
        dbs.append(db)

    benchmark(fn)
    for db in dbs:
        db.remove()


@pytest.mark.benchmark(group="write_trajectory")
def test_write_trajectory_asebytes_redis(benchmark, dataset, redis_uri):
    name, frames = dataset
    dbs = []

    def fn():
        uri = f"{redis_uri}/bench_wt_{name}_{uuid.uuid4().hex[:8]}"
        db = ASEIO(uri)
        db.extend(frames)
        dbs.append(db)

    benchmark(fn)
    for db in dbs:
        db.remove()


@pytest.mark.benchmark(group="write_trajectory")
def test_write_trajectory_aselmdb(benchmark, dataset, tmp_path):
    name, frames = dataset

    def fn():
        p = tmp_path / f"wt_{name}_aselmdb_{uuid.uuid4().hex}.lmdb"
        db = connect(str(p), type="aselmdb")
        for mol in frames:
            db.write(mol)

    benchmark(fn)


@pytest.mark.benchmark(group="write_trajectory")
def test_write_trajectory_znh5md(benchmark, dataset, tmp_path):
    import znh5md

    name, frames = dataset

    def fn():
        p = tmp_path / f"wt_{name}_znh5md_{uuid.uuid4().hex}.h5"
        io = znh5md.IO(filename=str(p))
        io.extend(frames)

    benchmark(fn)


@pytest.mark.benchmark(group="write_trajectory")
def test_write_trajectory_extxyz(benchmark, dataset, tmp_path):
    name, frames = dataset

    def fn():
        p = tmp_path / f"wt_{name}_extxyz_{uuid.uuid4().hex}.extxyz"
        ase.io.write(str(p), frames, format="extxyz")

    benchmark(fn)


@pytest.mark.benchmark(group="write_trajectory")
def test_write_trajectory_sqlite(benchmark, dataset, tmp_path):
    name, frames = dataset

    def fn():
        p = tmp_path / f"wt_{name}_sqlite_{uuid.uuid4().hex}.db"
        db = connect(str(p), type="db")
        for mol in frames:
            db.write(mol)

    benchmark(fn)


# ===================================================================
# write_single — per-row write in a loop
#
# Capped to WRITE_SINGLE_FRAMES to keep CI fast. Per-row overhead is
# the signal; throughput scaling is covered by write_trajectory.
# ===================================================================

WRITE_SINGLE_FRAMES = 10


@pytest.mark.benchmark(group="write_single")
def test_write_single_asebytes_lmdb(benchmark, dataset, tmp_path):
    name, frames = dataset
    frames = frames[:WRITE_SINGLE_FRAMES]

    def fn():
        p = tmp_path / f"ws_{name}_lmdb_{uuid.uuid4().hex}.lmdb"
        db = ASEIO(str(p))
        for mol in frames:
            db.extend([mol])

    benchmark(fn)


@pytest.mark.benchmark(group="write_single")
def test_write_single_asebytes_zarr(benchmark, dataset, tmp_path):
    name, frames = dataset
    frames = frames[:WRITE_SINGLE_FRAMES]

    def fn():
        p = tmp_path / f"ws_{name}_zarr_{uuid.uuid4().hex}.zarr"
        db = ASEIO(str(p))
        for mol in frames:
            db.extend([mol])

    benchmark(fn)


@pytest.mark.benchmark(group="write_single")
def test_write_single_asebytes_h5md(benchmark, dataset, tmp_path):
    name, frames = dataset
    frames = frames[:WRITE_SINGLE_FRAMES]

    def fn():
        p = tmp_path / f"ws_{name}_h5md_{uuid.uuid4().hex}.h5"
        db = ASEIO(str(p))
        for mol in frames:
            db.extend([mol])

    benchmark(fn)


@pytest.mark.benchmark(group="write_single")
def test_write_single_asebytes_mongodb(benchmark, dataset, mongo_uri):
    name, frames = dataset
    frames = frames[:WRITE_SINGLE_FRAMES]
    dbs = []

    def fn():
        uri = f"{mongo_uri}/bench_ws_{name}_{uuid.uuid4().hex[:8]}"
        db = ASEIO(uri)
        for mol in frames:
            db.extend([mol])
        dbs.append(db)

    benchmark(fn)
    for db in dbs:
        db.remove()


@pytest.mark.benchmark(group="write_single")
def test_write_single_asebytes_redis(benchmark, dataset, redis_uri):
    name, frames = dataset
    frames = frames[:WRITE_SINGLE_FRAMES]
    dbs = []

    def fn():
        uri = f"{redis_uri}/bench_ws_{name}_{uuid.uuid4().hex[:8]}"
        db = ASEIO(uri)
        for mol in frames:
            db.extend([mol])
        dbs.append(db)

    benchmark(fn)
    for db in dbs:
        db.remove()


@pytest.mark.benchmark(group="write_single")
def test_write_single_aselmdb(benchmark, dataset, tmp_path):
    name, frames = dataset
    frames = frames[:WRITE_SINGLE_FRAMES]

    def fn():
        p = tmp_path / f"ws_{name}_aselmdb_{uuid.uuid4().hex}.lmdb"
        db = connect(str(p), type="aselmdb")
        for mol in frames:
            db.write(mol)

    benchmark(fn)


@pytest.mark.benchmark(group="write_single")
def test_write_single_znh5md(benchmark, dataset, tmp_path):
    import znh5md

    name, frames = dataset
    frames = frames[:WRITE_SINGLE_FRAMES]

    def fn():
        p = tmp_path / f"ws_{name}_znh5md_{uuid.uuid4().hex}.h5"
        io = znh5md.IO(filename=str(p))
        for mol in frames:
            io.extend([mol])

    benchmark(fn)


@pytest.mark.benchmark(group="write_single")
def test_write_single_extxyz(benchmark, dataset, tmp_path):
    name, frames = dataset
    frames = frames[:WRITE_SINGLE_FRAMES]

    def fn():
        p = str(tmp_path / f"ws_{name}_extxyz_{uuid.uuid4().hex}.extxyz")
        for mol in frames:
            ase.io.write(p, mol, format="extxyz", append=True)

    benchmark(fn)


@pytest.mark.benchmark(group="write_single")
def test_write_single_sqlite(benchmark, dataset, tmp_path):
    name, frames = dataset
    frames = frames[:WRITE_SINGLE_FRAMES]

    def fn():
        p = tmp_path / f"ws_{name}_sqlite_{uuid.uuid4().hex}.db"
        db = connect(str(p), type="db")
        for mol in frames:
            db.write(mol)

    benchmark(fn)
