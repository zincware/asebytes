"""Benchmark sequential read performance across backends.

Backends: asebytes LMDB, asebytes H5MD, aselmdb, znh5md, extxyz, sqlite.
datasets: ethanol (1000 small molecules), lemat (1000 periodic structures).
"""

import ase
import ase.io
import pytest
from ase.db import connect

from asebytes import ASEIO

datasetS = ["ethanol", "lemat"]


@pytest.fixture(params=datasetS)
def dataset(request):
    return request.param, request.getfixturevalue(request.param)


# ---------------------------------------------------------------------------
# Read benchmarks
# ---------------------------------------------------------------------------


@pytest.mark.benchmark(group="read")
def test_read_asebytes_lmdb(benchmark, dataset, tmp_path):
    name, frames = dataset
    p = tmp_path / f"r_{name}.lmdb"
    db = ASEIO(str(p))
    db.extend(frames)

    def read_all():
        return [db[i] for i in range(len(db))]

    results = benchmark(read_all)
    assert len(results) == len(frames)
    assert all(isinstance(a, ase.Atoms) for a in results)


@pytest.mark.benchmark(group="read")
def test_read_asebytes_zarr(benchmark, dataset, tmp_path):
    name, frames = dataset
    p = tmp_path / f"r_{name}.zarr"
    db_w = ASEIO(str(p))
    db_w.extend(frames)

    def read_all():
        db = ASEIO(str(p))
        return list(db[:])

    results = benchmark(read_all)
    assert len(results) == len(frames)


@pytest.mark.benchmark(group="read")
def test_read_asebytes_h5md(benchmark, dataset, tmp_path):
    name, frames = dataset
    p = tmp_path / f"r_{name}.h5"
    db_w = ASEIO(str(p))
    db_w.extend(frames)

    def read_all():
        db = ASEIO(str(p))
        return list(db[:])

    results = benchmark(read_all)
    assert len(results) == len(frames)


@pytest.mark.benchmark(group="read")
def test_read_aselmdb(benchmark, dataset, tmp_path):
    name, frames = dataset
    p = tmp_path / f"r_{name}_aselmdb.lmdb"
    db = connect(str(p), type="aselmdb")
    for mol in frames:
        db.write(mol)

    def read_all():
        return [row.toatoms() for row in db.select()]

    results = benchmark(read_all)
    assert len(results) == len(frames)


@pytest.mark.benchmark(group="read")
def test_read_znh5md(benchmark, dataset, tmp_path):
    import h5py
    import znh5md

    name, frames = dataset
    p = tmp_path / f"r_{name}_znh5md.h5"
    io_w = znh5md.IO(filename=str(p))
    io_w.extend(frames)

    def read_all():
        with h5py.File(str(p), "r") as f:
            io = znh5md.IO(file_handle=f)
            return io[:]

    results = benchmark(read_all)
    assert len(results) == len(frames)


@pytest.mark.benchmark(group="read")
def test_read_extxyz(benchmark, dataset, tmp_path):
    name, frames = dataset
    p = tmp_path / f"r_{name}.extxyz"
    ase.io.write(str(p), frames, format="extxyz")

    def read_all():
        return ase.io.read(str(p), index=":", format="extxyz")

    results = benchmark(read_all)
    assert len(results) == len(frames)


@pytest.mark.benchmark(group="read")
def test_read_sqlite(benchmark, dataset, tmp_path):
    name, frames = dataset
    p = tmp_path / f"r_{name}_sqlite.db"
    db = connect(str(p), type="db")
    for mol in frames:
        db.write(mol)

    def read_all():
        return [row.toatoms() for row in db.select()]

    results = benchmark(read_all)
    assert len(results) == len(frames)
