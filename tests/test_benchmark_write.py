"""Benchmark write performance across backends.

Backends: asebytes LMDB, asebytes H5MD, aselmdb, znh5md, extxyz, sqlite.
datasets: ethanol (1000 small molecules), lemat (1000 periodic structures).
"""

import uuid

import ase.io
import pytest
from ase.db import connect

from asebytes import ASEIO


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

datasetS = ["ethanol", "lemat"]


@pytest.fixture(params=datasetS)
def dataset(request):
    return request.param, request.getfixturevalue(request.param)


# ---------------------------------------------------------------------------
# Write benchmarks
# ---------------------------------------------------------------------------


@pytest.mark.benchmark(group="write")
def test_write_asebytes_lmdb(benchmark, dataset, tmp_path):
    name, frames = dataset

    def write_all():
        p = tmp_path / f"w_{name}_lmdb_{uuid.uuid4().hex}.lmdb"
        db = ASEIO(str(p))
        db.extend(frames)
        return db

    db = benchmark(write_all)
    assert len(db) == len(frames)


@pytest.mark.benchmark(group="write")
def test_write_asebytes_zarr(benchmark, dataset, tmp_path):
    name, frames = dataset

    def write_all():
        p = tmp_path / f"w_{name}_zarr_{uuid.uuid4().hex}.zarr"
        db = ASEIO(str(p))
        db.extend(frames)
        return db

    db = benchmark(write_all)
    assert len(db) == len(frames)


@pytest.mark.benchmark(group="write")
def test_write_asebytes_h5md(benchmark, dataset, tmp_path):
    name, frames = dataset

    def write_all():
        p = tmp_path / f"w_{name}_h5md_{uuid.uuid4().hex}.h5"
        db = ASEIO(str(p))
        db.extend(frames)
        return db

    db = benchmark(write_all)
    assert len(db) == len(frames)


@pytest.mark.benchmark(group="write")
def test_write_aselmdb(benchmark, dataset, tmp_path):
    name, frames = dataset

    def write_all():
        p = tmp_path / f"w_{name}_aselmdb_{uuid.uuid4().hex}.lmdb"
        db = connect(str(p), type="aselmdb")
        for mol in frames:
            db.write(mol)
        return db

    benchmark(write_all)


@pytest.mark.benchmark(group="write")
def test_write_znh5md(benchmark, dataset, tmp_path):
    import znh5md

    name, frames = dataset

    def write_all():
        p = tmp_path / f"w_{name}_znh5md_{uuid.uuid4().hex}.h5"
        io = znh5md.IO(filename=str(p))
        io.extend(frames)
        return p

    benchmark(write_all)


@pytest.mark.benchmark(group="write")
def test_write_extxyz(benchmark, dataset, tmp_path):
    name, frames = dataset

    def write_all():
        p = tmp_path / f"w_{name}_extxyz_{uuid.uuid4().hex}.extxyz"
        ase.io.write(str(p), frames, format="extxyz")
        return p

    benchmark(write_all)


@pytest.mark.benchmark(group="write")
def test_write_sqlite(benchmark, dataset, tmp_path):
    name, frames = dataset

    def write_all():
        p = tmp_path / f"w_{name}_sqlite_{uuid.uuid4().hex}.db"
        db = connect(str(p), type="db")
        for mol in frames:
            db.write(mol)
        return db

    benchmark(write_all)
