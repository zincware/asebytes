"""Benchmark file size across backends.

Writes each dataset to each backend and reports the output size in bytes.
Uses pytest-benchmark extra_info to store the size alongside timing data.

Backends: asebytes LMDB, asebytes H5MD, aselmdb, znh5md, extxyz, sqlite.
Datasets: ethanol (1000 small molecules), lemat (1000 periodic structures).
"""

import os

import ase.io
import pytest
from ase.db import connect

from asebytes import ASEIO

DATASETS = ["ethanol", "lemat"]


@pytest.fixture(params=DATASETS)
def dataset(request):
    return request.param, request.getfixturevalue(request.param)


def _dir_size(path: str) -> int:
    """Total size of a file or directory in bytes."""
    total = 0
    if os.path.isfile(path):
        return os.path.getsize(path)
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            total += os.path.getsize(os.path.join(dirpath, f))
    return total


# ---------------------------------------------------------------------------
# File size benchmarks
# ---------------------------------------------------------------------------


@pytest.mark.benchmark(group="file_size")
def test_size_asebytes_lmdb(benchmark, dataset, tmp_path):
    name, frames = dataset
    p = tmp_path / f"sz_{name}.lmdb"

    def write_and_measure():
        db = ASEIO(str(p))
        db.extend(frames)
        return _dir_size(str(p))

    size = benchmark(write_and_measure)
    benchmark.extra_info["file_size_bytes"] = size


@pytest.mark.benchmark(group="file_size")
def test_size_asebytes_h5md(benchmark, dataset, tmp_path):
    name, frames = dataset
    p = tmp_path / f"sz_{name}.h5"

    def write_and_measure():
        db = ASEIO(str(p))
        db.extend(frames)
        return _dir_size(str(p))

    size = benchmark(write_and_measure)
    benchmark.extra_info["file_size_bytes"] = size


@pytest.mark.benchmark(group="file_size")
def test_size_aselmdb(benchmark, dataset, tmp_path):
    name, frames = dataset
    p = tmp_path / f"sz_{name}_aselmdb.lmdb"

    def write_and_measure():
        db = connect(str(p), type="aselmdb")
        for mol in frames:
            db.write(mol)
        return _dir_size(str(p))

    size = benchmark(write_and_measure)
    benchmark.extra_info["file_size_bytes"] = size


@pytest.mark.benchmark(group="file_size")
def test_size_znh5md(benchmark, dataset, tmp_path):
    import znh5md

    name, frames = dataset
    p = tmp_path / f"sz_{name}_znh5md.h5"

    def write_and_measure():
        io = znh5md.IO(filename=str(p))
        io.extend(frames)
        return _dir_size(str(p))

    size = benchmark(write_and_measure)
    benchmark.extra_info["file_size_bytes"] = size


@pytest.mark.benchmark(group="file_size")
def test_size_extxyz(benchmark, dataset, tmp_path):
    name, frames = dataset
    p = tmp_path / f"sz_{name}.extxyz"

    def write_and_measure():
        ase.io.write(str(p), frames, format="extxyz")
        return _dir_size(str(p))

    size = benchmark(write_and_measure)
    benchmark.extra_info["file_size_bytes"] = size


@pytest.mark.benchmark(group="file_size")
def test_size_sqlite(benchmark, dataset, tmp_path):
    name, frames = dataset
    p = tmp_path / f"sz_{name}_sqlite.db"

    def write_and_measure():
        db = connect(str(p), type="db")
        for mol in frames:
            db.write(mol)
        return _dir_size(str(p))

    size = benchmark(write_and_measure)
    benchmark.extra_info["file_size_bytes"] = size
