"""Shared fixtures for the benchmark suite.

Provides pre-populated database fixtures for every backend so that setup
cost is excluded from benchmarked operations.  Each fixture yields a
namespace with the relevant handles and metadata.

Datasets: ethanol (1000 small molecules), lemat (1000 periodic structures).
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from typing import Any

import ase
import ase.io
import pytest
from ase.db import connect

from asebytes import ASEIO, ObjectIO
from asebytes._convert import atoms_to_dict


# ---------------------------------------------------------------------------
# Dataset parametrisation
# ---------------------------------------------------------------------------

DATASETS = ["ethanol", "lemat"]


@pytest.fixture(params=DATASETS)
def dataset(request):
    """Yield (name, frames) for each benchmark dataset."""
    return request.param, request.getfixturevalue(request.param)


# ---------------------------------------------------------------------------
# Helper: random indices (truly random, no seed)
# ---------------------------------------------------------------------------


def random_indices(n: int) -> list[int]:
    """Return n truly random indices in [0, n)."""
    return [random.randint(0, n - 1) for _ in range(n)]


# ---------------------------------------------------------------------------
# Pre-populated DB dataclass
# ---------------------------------------------------------------------------


@dataclass
class BenchDB:
    """Container holding pre-populated database handles for one backend."""

    aseio: Any = None
    objectio: Any = None
    frames: list[ase.Atoms] = field(default_factory=list)
    name: str = ""
    # For third-party backends
    ase_db: Any = None
    znh5md_path: Any = None
    extxyz_path: Any = None


# ---------------------------------------------------------------------------
# asebytes fixtures (LMDB, Zarr, H5MD)
# ---------------------------------------------------------------------------


@pytest.fixture
def bench_lmdb(dataset, tmp_path):
    name, frames = dataset
    p = str(tmp_path / f"bench_{name}.lmdb")
    aseio = ASEIO(p)
    aseio.extend(frames)
    objectio = ObjectIO(p)
    return BenchDB(aseio=aseio, objectio=objectio, frames=frames, name=name)


@pytest.fixture
def bench_zarr(dataset, tmp_path):
    name, frames = dataset
    p = str(tmp_path / f"bench_{name}.zarr")
    aseio = ASEIO(p)
    aseio.extend(frames)
    objectio = ObjectIO(p)
    return BenchDB(aseio=aseio, objectio=objectio, frames=frames, name=name)


@pytest.fixture
def bench_h5md(dataset, tmp_path):
    name, frames = dataset
    p = str(tmp_path / f"bench_{name}.h5")
    aseio = ASEIO(p)
    aseio.extend(frames)
    objectio = ObjectIO(p)
    return BenchDB(aseio=aseio, objectio=objectio, frames=frames, name=name)


# ---------------------------------------------------------------------------
# Network backend fixtures (MongoDB, Redis)
# ---------------------------------------------------------------------------


@pytest.fixture
def bench_mongodb(dataset, mongo_uri):
    name, frames = dataset
    uri = f"{mongo_uri}/bench_{name}_{uuid.uuid4().hex[:8]}"
    aseio = ASEIO(uri)
    aseio.extend(frames)
    objectio = ObjectIO(uri)
    yield BenchDB(aseio=aseio, objectio=objectio, frames=frames, name=name)
    aseio.remove()


@pytest.fixture
def bench_redis(dataset, redis_uri):
    name, frames = dataset
    prefix = f"bench_{name}_{uuid.uuid4().hex[:8]}"
    uri = f"{redis_uri}/{prefix}"
    aseio = ASEIO(uri)
    aseio.extend(frames)
    objectio = ObjectIO(uri)
    yield BenchDB(aseio=aseio, objectio=objectio, frames=frames, name=name)
    aseio.remove()


# ---------------------------------------------------------------------------
# Third-party fixtures (aselmdb, sqlite, znh5md, extxyz)
# ---------------------------------------------------------------------------


@pytest.fixture
def bench_aselmdb(dataset, tmp_path):
    name, frames = dataset
    p = str(tmp_path / f"bench_{name}_aselmdb.lmdb")
    db = connect(p, type="aselmdb")
    for mol in frames:
        db.write(mol)
    return BenchDB(ase_db=db, frames=frames, name=name)


@pytest.fixture
def bench_sqlite(dataset, tmp_path):
    name, frames = dataset
    p = str(tmp_path / f"bench_{name}_sqlite.db")
    db = connect(p, type="db")
    for mol in frames:
        db.write(mol)
    return BenchDB(ase_db=db, frames=frames, name=name)


@pytest.fixture
def bench_znh5md(dataset, tmp_path):
    import znh5md

    name, frames = dataset
    p = tmp_path / f"bench_{name}_znh5md.h5"
    io = znh5md.IO(filename=str(p))
    io.extend(frames)
    return BenchDB(znh5md_path=p, frames=frames, name=name)


@pytest.fixture
def bench_extxyz(dataset, tmp_path):
    name, frames = dataset
    p = tmp_path / f"bench_{name}.extxyz"
    ase.io.write(str(p), frames, format="extxyz")
    return BenchDB(extxyz_path=p, frames=frames, name=name)
