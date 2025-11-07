"""Benchmark random index access performance comparison across different backends.

Compare random access performance of:
- asebytes (ASEIO)
- ASE's aselmdb backend
- Raw lmdb + pickle
- XYZ file format (using index parameter)
- SQLite database
- znh5md (H5MD format)
"""

import pickle
import random

import ase
import ase.io
import pytest
from ase.db import connect

from asebytes import ASEIO


@pytest.mark.benchmark(group="random_access")
def test_random_access_asebytes(benchmark, ethanol, tmp_path):
    """Random access 1000 ethanol molecules using asebytes.ASEIO."""
    db_path = tmp_path / "random_asebytes.lmdb"
    db = ASEIO(str(db_path))
    db.extend(ethanol)

    # Generate random indices (seeded for reproducibility)
    random.seed(42)
    indices = [random.randint(0, len(ethanol) - 1) for _ in range(len(ethanol))]

    def random_access():
        return [db[i] for i in indices]

    results = benchmark(random_access)
    assert len(results) == len(ethanol)
    assert all(isinstance(mol, ase.Atoms) for mol in results)


@pytest.mark.benchmark(group="random_access")
def test_random_access_aselmdb(benchmark, ethanol, tmp_path):
    """Random access 1000 ethanol molecules using ASE aselmdb backend."""
    db_path = tmp_path / "random_aselmdb.lmdb"
    db = connect(str(db_path), type="aselmdb")

    # Setup: write data
    for mol in ethanol:
        db.write(mol)

    # Generate random indices (seeded for reproducibility)
    random.seed(42)
    indices = [
        random.randint(1, len(ethanol)) for _ in range(len(ethanol))
    ]  # ASE DB uses 1-based indexing

    def random_access():
        return [db.get(id=i).toatoms() for i in indices]

    results = benchmark(random_access)
    assert len(results) == len(ethanol)
    assert all(isinstance(mol, ase.Atoms) for mol in results)


@pytest.mark.benchmark(group="random_access")
def test_random_access_lmdb_pickle(benchmark, ethanol, tmp_path):
    """Random access 1000 ethanol molecules using raw lmdb + pickle."""
    import lmdb

    db_path = tmp_path / "random_pickle.lmdb"
    env = lmdb.open(str(db_path))

    # Setup: write data
    with env.begin(write=True) as txn:
        for i, mol in enumerate(ethanol):
            key = str(i).encode()
            value = pickle.dumps(mol)
            txn.put(key, value)

    # Generate random indices (seeded for reproducibility)
    random.seed(42)
    indices = [random.randint(0, len(ethanol) - 1) for _ in range(len(ethanol))]

    def random_access():
        results = []
        with env.begin() as txn:
            for i in indices:
                key = str(i).encode()
                value = txn.get(key)
                mol = pickle.loads(value)
                results.append(mol)
        return results

    results = benchmark(random_access)
    assert len(results) == len(ethanol)
    assert all(isinstance(mol, ase.Atoms) for mol in results)

    env.close()


@pytest.mark.skip(reason="XYZ random access is slow; enable only for specific testing")
@pytest.mark.benchmark(group="random_access")
def test_random_access_xyz(benchmark, ethanol, tmp_path):
    """Random access 1000 ethanol molecules using XYZ format with index parameter."""
    xyz_path = tmp_path / "random_xyz.xyz"

    # Setup: write data
    ase.io.write(str(xyz_path), ethanol, format="xyz")

    # Generate random indices (seeded for reproducibility)
    random.seed(42)
    indices = [random.randint(0, len(ethanol) - 1) for _ in range(len(ethanol))]

    def random_access():
        return [ase.io.read(str(xyz_path), index=i, format="xyz") for i in indices]

    results = benchmark(random_access)
    assert len(results) == len(ethanol)
    assert all(isinstance(mol, ase.Atoms) for mol in results)


@pytest.mark.benchmark(group="random_access")
def test_random_access_sqlite(benchmark, ethanol, tmp_path):
    """Random access 1000 ethanol molecules using SQLite database."""
    db_path = tmp_path / "random_sqlite.db"
    db = connect(str(db_path), type="db")

    # Setup: write data
    for mol in ethanol:
        db.write(mol)

    # Generate random indices (seeded for reproducibility)
    random.seed(42)
    indices = [
        random.randint(1, len(ethanol)) for _ in range(len(ethanol))
    ]  # ASE DB uses 1-based indexing

    def random_access():
        return [db.get(id=i).toatoms() for i in indices]

    results = benchmark(random_access)
    assert len(results) == len(ethanol)
    assert all(isinstance(mol, ase.Atoms) for mol in results)


@pytest.mark.benchmark(group="random_access")
def test_random_access_znh5md(benchmark, ethanol, tmp_path):
    """Random access 1000 ethanol molecules using znh5md (H5MD format)."""
    import h5py
    import znh5md

    h5_path = tmp_path / "random_znh5md.h5"

    # Setup: write data using filename parameter
    io_write = znh5md.IO(filename=str(h5_path))
    io_write.extend(ethanol)

    # Generate random indices (seeded for reproducibility)
    random.seed(42)
    indices = [random.randint(0, len(ethanol) - 1) for _ in range(len(ethanol))]

    def random_access():
        # Use file_handle for best read performance
        with h5py.File(str(h5_path), "r") as f:
            io = znh5md.IO(file_handle=f)
            return [io[i] for i in indices]

    results = benchmark(random_access)
    assert len(results) == len(ethanol)
    assert all(isinstance(mol, ase.Atoms) for mol in results)
