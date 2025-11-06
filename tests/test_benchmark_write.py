"""Benchmark write performance comparison across different backends.

Compare write performance of:
- asebytes (ASEIO)
- ASE's aselmdb backend
- Raw lmdb + pickle
- XYZ file format
- SQLite database
"""

import pickle
import uuid

import ase.io
import pytest
from ase.db import connect

from asebytes import ASEIO


@pytest.mark.benchmark(group="write")
def test_write_asebytes(benchmark, ethanol, tmp_path):
    """Write 1000 ethanol molecules using asebytes.ASEIO."""

    def write_all():
        db_path = tmp_path / f"write_asebytes_{uuid.uuid4().hex}.lmdb"
        db = ASEIO(str(db_path))
        db.extend(ethanol)
        return db

    db = benchmark(write_all)
    assert len(db) == len(ethanol)


@pytest.mark.benchmark(group="write")
def test_write_aselmdb(benchmark, ethanol, tmp_path):
    """Write 1000 ethanol molecules using ASE aselmdb backend."""

    def write_all():
        db_path = tmp_path / f"write_aselmdb_{uuid.uuid4().hex}.lmdb"
        db = connect(str(db_path), type="aselmdb")
        for mol in ethanol:
            db.write(mol)
        return db

    benchmark(write_all)


@pytest.mark.benchmark(group="write")
def test_write_lmdb_pickle(benchmark, ethanol, tmp_path):
    """Write 1000 ethanol molecules using raw lmdb + pickle."""
    import lmdb

    def write_all():
        db_path = tmp_path / f"write_pickle_{uuid.uuid4().hex}.lmdb"
        env = lmdb.open(str(db_path))

        with env.begin(write=True) as txn:
            for i, mol in enumerate(ethanol):
                key = str(i).encode()
                value = pickle.dumps(mol)
                txn.put(key, value)

        return env

    env = benchmark(write_all)
    env.close()


@pytest.mark.benchmark(group="write")
def test_write_xyz(benchmark, ethanol, tmp_path):
    """Write 1000 ethanol molecules using XYZ format."""

    def write_all():
        xyz_path = tmp_path / f"write_xyz_{uuid.uuid4().hex}.xyz"
        ase.io.write(str(xyz_path), ethanol, format="xyz")
        return xyz_path

    benchmark(write_all)


@pytest.mark.benchmark(group="write")
def test_write_sqlite(benchmark, ethanol, tmp_path):
    """Write 1000 ethanol molecules using SQLite database."""

    def write_all():
        db_path = tmp_path / f"write_sqlite_{uuid.uuid4().hex}.db"
        db = connect(str(db_path), type="db")
        for mol in ethanol:
            db.write(mol)
        return db

    benchmark(write_all)
