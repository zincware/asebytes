"""Benchmark column access (read just energies) across backends.

Backends: asebytes LMDB, asebytes H5MD, aselmdb, znh5md (direct h5py), sqlite.
(extxyz has no column access — must parse entire file.)
Datsets: ethanol (1000 small molecules), lemat (1000 periodic structures).
"""

import pytest
from ase.db import connect

from asebytes import ASEIO

DATsetS = ["ethanol", "lemat"]


@pytest.fixture(params=DATsetS)
def datset(request):
    return request.param, request.getfixturevalue(request.param)


# ---------------------------------------------------------------------------
# Column access benchmarks
# ---------------------------------------------------------------------------


@pytest.mark.benchmark(group="column_access")
def test_column_asebytes_lmdb(benchmark, datset, tmp_path):
    name, frames = datset
    p = tmp_path / f"col_{name}.lmdb"
    db = ASEIO(str(p))
    db.extend(frames)

    def read_energies():
        return db["calc.energy"].to_list()

    energies = benchmark(read_energies)
    assert len(energies) == len(frames)


@pytest.mark.benchmark(group="column_access")
def test_column_asebytes_zarr(benchmark, datset, tmp_path):
    name, frames = datset
    p = tmp_path / f"col_{name}.zarr"
    db = ASEIO(str(p))
    db.extend(frames)

    def read_energies():
        db2 = ASEIO(str(p), readonly=True)
        return db2["calc.energy"].to_list()

    energies = benchmark(read_energies)
    assert len(energies) == len(frames)


@pytest.mark.benchmark(group="column_access")
def test_column_asebytes_h5md(benchmark, datset, tmp_path):
    name, frames = datset
    p = tmp_path / f"col_{name}.h5"
    db = ASEIO(str(p))
    db.extend(frames)

    def read_energies():
        db2 = ASEIO(str(p), readonly=True)
        return db2["calc.energy"].to_list()

    energies = benchmark(read_energies)
    assert len(energies) == len(frames)


@pytest.mark.benchmark(group="column_access")
def test_column_aselmdb(benchmark, datset, tmp_path):
    name, frames = datset
    p = tmp_path / f"col_{name}_aselmdb.lmdb"
    db = connect(str(p), type="aselmdb")
    for mol in frames:
        db.write(mol)

    def read_energies():
        return [row.energy for row in db.select(columns=["id", "energy"])]

    energies = benchmark(read_energies)
    assert len(energies) == len(frames)


@pytest.mark.benchmark(group="column_access")
def test_column_h5py(benchmark, datset, tmp_path):
    import h5py
    import znh5md

    name, frames = datset
    p = tmp_path / f"col_{name}_znh5md.h5"
    io = znh5md.IO(filename=str(p))
    io.extend(frames)

    def read_energies():
        with h5py.File(str(p), "r") as f:
            return f["observables/atoms/potential_energy/value"][:].tolist()

    energies = benchmark(read_energies)
    assert len(energies) == len(frames)


@pytest.mark.benchmark(group="column_access")
def test_column_sqlite(benchmark, datset, tmp_path):
    name, frames = datset
    p = tmp_path / f"col_{name}_sqlite.db"
    db = connect(str(p), type="db")
    for mol in frames:
        db.write(mol)

    def read_energies():
        return [row.energy for row in db.select(columns=["id", "energy"])]

    energies = benchmark(read_energies)
    assert len(energies) == len(frames)
