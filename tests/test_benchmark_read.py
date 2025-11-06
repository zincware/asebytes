"""Benchmark read performance comparison across different backends.

Compare read performance of:
- asebytes (ASEIO)
- ASE's aselmdb backend
- Raw lmdb + pickle
"""

import pickle

import ase
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
            for i in range(len(ethanol)):
                key = str(i).encode()
                value = txn.get(key)
                mol = pickle.loads(value)
                results.append(mol)
        return results

    results = benchmark(read_all)
    assert len(results) == len(ethanol)
    assert all(isinstance(mol, ase.Atoms) for mol in results)

    env.close()
