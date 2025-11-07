"""Benchmark read performance comparison across different backends.

Compare read performance of:
- asebytes (ASEIO)
- ASE's aselmdb backend
- Raw lmdb + pickle
- XYZ file format
- SQLite database
- znh5md (H5MD format)
"""

import pickle

import ase
import ase.io
import pytest
from ase.db import connect

from asebytes import ASEIO


@pytest.mark.benchmark(group="read")
def test_read_asebytes(benchmark, ethanol, tmp_path):
    """Read 1000 ethanol molecules using asebytes.ASEIO."""
    db_path = tmp_path / "read_asebytes.lmdb"
    db = ASEIO(str(db_path))
    db.extend(ethanol)

    def read_all():
        # TODO: use bulk read, if available
        return [db[i] for i in range(len(db))]

    results = benchmark(read_all)
    assert len(results) == len(ethanol)
    assert all(isinstance(mol, ase.Atoms) for mol in results)


@pytest.mark.benchmark(group="read")
def test_read_aselmdb(benchmark, ethanol, tmp_path):
    """Read 1000 ethanol molecules using ASE aselmdb backend."""
    db_path = tmp_path / "read_aselmdb.lmdb"
    db = connect(str(db_path), type="aselmdb")

    # Setup: write data
    for mol in ethanol:
        db.write(mol)

    def read_all():
        results = []
        # TODO: https://ase-lib.org/ase/db/db.html#ase.db.core.Database.get_atoms (not working?)
        for row in db.select():
            mol = row.toatoms()
            results.append(mol)
        return results

    results = benchmark(read_all)
    assert len(results) == len(ethanol)
    assert all(isinstance(mol, ase.Atoms) for mol in results)


@pytest.mark.benchmark(group="read")
def test_read_lmdb_pickle(benchmark, ethanol, tmp_path):
    """Read 1000 ethanol molecules using raw lmdb + pickle."""
    import lmdb

    db_path = tmp_path / "read_pickle.lmdb"
    env = lmdb.open(str(db_path))

    # Setup: write data
    with env.begin(write=True) as txn:
        for i, mol in enumerate(ethanol):
            key = str(i).encode()
            value = pickle.dumps(mol)
            txn.put(key, value)

    def read_all():
        results = []
        with env.begin() as txn:
            cursor = txn.cursor()
            raw = cursor.getmulti(keys=[str(i).encode() for i in range(len(ethanol))])
            for _, value in raw:
                mol = pickle.loads(value)
                results.append(mol)
        return results

    results = benchmark(read_all)
    assert len(results) == len(ethanol)
    assert all(isinstance(mol, ase.Atoms) for mol in results)

    env.close()


@pytest.mark.benchmark(group="read")
def test_read_xyz(benchmark, ethanol, tmp_path):
    """Read 1000 ethanol molecules using XYZ format."""
    xyz_path = tmp_path / "read_xyz.xyz"

    ase.io.write(str(xyz_path), ethanol, format="xyz")

    def read_all():
        return ase.io.read(str(xyz_path), index=":", format="xyz")

    results = benchmark(read_all)
    assert len(results) == len(ethanol)
    assert all(isinstance(mol, ase.Atoms) for mol in results)


@pytest.mark.benchmark(group="read")
def test_read_sqlite(benchmark, ethanol, tmp_path):
    """Read 1000 ethanol molecules using SQLite database."""
    db_path = tmp_path / "read_sqlite.db"
    db = connect(str(db_path), type="db")

    for mol in ethanol:
        db.write(mol)

    def read_all():
        results = []
        # TODO: https://ase-lib.org/ase/db/db.html#ase.db.core.Database.get_atoms (not working?)
        for row in db.select():
            mol = row.toatoms()
            results.append(mol)
        return results

    results = benchmark(read_all)
    assert len(results) == len(ethanol)
    assert all(isinstance(mol, ase.Atoms) for mol in results)


@pytest.mark.benchmark(group="read")
def test_read_znh5md(benchmark, ethanol, tmp_path):
    """Read 1000 ethanol molecules using znh5md (H5MD format)."""
    import h5py
    import znh5md

    h5_path = tmp_path / "read_znh5md.h5"

    # Setup: write data using filename parameter
    io_write = znh5md.IO(filename=str(h5_path))
    io_write.extend(ethanol)

    def read_all():
        # Use file_handle for best read performance
        with h5py.File(str(h5_path), "r") as f:
            io = znh5md.IO(file_handle=f)
            return io[:]

    results = benchmark(read_all)
    assert len(results) == len(ethanol)
    assert all(isinstance(mol, ase.Atoms) for mol in results)
