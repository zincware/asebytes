"""Benchmark random-index access performance across backends.

Backends: asebytes LMDB, asebytes H5MD, aselmdb, znh5md, sqlite.
(extxyz skipped — requires full file scan per access.)
Datsets: ethanol (1000 small molecules), lemat (1000 periodic structures).
"""

import random

import ase
import pytest
from ase.db import connect

from asebytes import ASEIO

DATsetS = ["ethanol", "lemat"]


@pytest.fixture(params=DATsetS)
def datset(request):
    return request.param, request.getfixturevalue(request.param)


def _random_indices(n: int, seed: int = 42) -> list[int]:
    rng = random.Random(seed)
    return [rng.randint(0, n - 1) for _ in range(n)]


# ---------------------------------------------------------------------------
# Random access benchmarks
# ---------------------------------------------------------------------------


@pytest.mark.benchmark(group="random_access")
def test_random_access_asebytes_lmdb(benchmark, datset, tmp_path):
    name, frames = datset
    p = tmp_path / f"ra_{name}.lmdb"
    db = ASEIO(str(p))
    db.extend(frames)
    indices = _random_indices(len(frames))

    def access():
        return [db[i] for i in indices]

    results = benchmark(access)
    assert len(results) == len(frames)
    assert all(isinstance(a, ase.Atoms) for a in results)


@pytest.mark.benchmark(group="random_access")
def test_random_access_asebytes_zarr(benchmark, datset, tmp_path):
    name, frames = datset
    p = tmp_path / f"ra_{name}.zarr"
    db_w = ASEIO(str(p))
    db_w.extend(frames)
    indices = _random_indices(len(frames))

    def access():
        db = ASEIO(str(p))
        return list(db[indices])

    results = benchmark(access)
    assert len(results) == len(frames)


@pytest.mark.benchmark(group="random_access")
def test_random_access_asebytes_h5md(benchmark, datset, tmp_path):
    name, frames = datset
    p = tmp_path / f"ra_{name}.h5"
    db_w = ASEIO(str(p))
    db_w.extend(frames)
    indices = _random_indices(len(frames))

    def access():
        db = ASEIO(str(p))
        return list(db[indices])

    results = benchmark(access)
    assert len(results) == len(frames)


@pytest.mark.benchmark(group="random_access")
def test_random_access_aselmdb(benchmark, datset, tmp_path):
    name, frames = datset
    p = tmp_path / f"ra_{name}_aselmdb.lmdb"
    db = connect(str(p), type="aselmdb")
    for mol in frames:
        db.write(mol)
    # aselmdb uses 1-based indexing
    indices = [i + 1 for i in _random_indices(len(frames))]

    def access():
        return [db.get(id=i).toatoms() for i in indices]

    results = benchmark(access)
    assert len(results) == len(frames)


@pytest.mark.benchmark(group="random_access")
def test_random_access_znh5md(benchmark, datset, tmp_path):
    import h5py
    import znh5md

    name, frames = datset
    p = tmp_path / f"ra_{name}_znh5md.h5"
    io_w = znh5md.IO(filename=str(p))
    io_w.extend(frames)
    indices = _random_indices(len(frames))

    def access():
        with h5py.File(str(p), "r") as f:
            io = znh5md.IO(file_handle=f)
            return [io[i] for i in indices]

    results = benchmark(access)
    assert len(results) == len(frames)


@pytest.mark.benchmark(group="random_access")
def test_random_access_sqlite(benchmark, datset, tmp_path):
    name, frames = datset
    p = tmp_path / f"ra_{name}_sqlite.db"
    db = connect(str(p), type="db")
    for mol in frames:
        db.write(mol)
    # sqlite uses 1-based indexing
    indices = [i + 1 for i in _random_indices(len(frames))]

    def access():
        return [db.get(id=i).toatoms() for i in indices]

    results = benchmark(access)
    assert len(results) == len(frames)
