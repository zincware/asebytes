"""Benchmark the new backend abstraction vs the current direct implementation.

Measures:
- Read overhead: ASEIO (new backend path) vs direct BytesIO + decode
- Write overhead: ASEIO (new backend path) vs direct BytesIO + encode
- Column access: db["calc.energy"] vs manual loop
- View materialization: db[0:1000] iteration vs direct loop
- Random access: new path vs old path

All benchmarks use the same 1000-ethanol dataset for comparison
with existing benchmarks in test_benchmark_read.py / test_benchmark_write.py.
"""

import random
import uuid

import numpy as np
import pytest
from ase.calculators.singlepoint import SinglePointCalculator

from asebytes import ASEIO, BytesIO, decode, encode
from asebytes._convert import atoms_to_dict, dict_to_atoms
from asebytes.lmdb import LMDBBackend


@pytest.fixture
def ethanol_with_calc(ethanol):
    """Ethanol conformers with energy and forces for column benchmarks."""
    for i, atoms in enumerate(ethanol):
        atoms.calc = SinglePointCalculator(atoms)
        atoms.calc.results = {
            "energy": float(-i * 0.1),
            "forces": np.random.RandomState(i).randn(len(atoms), 3) * 0.01,
        }
    return ethanol


# --- Conversion overhead ---


@pytest.mark.benchmark(group="conversion")
def test_encode_current(benchmark, ethanol):
    """Current: encode(atoms) -> dict[bytes, bytes] (msgpack)."""
    atoms = ethanol[0]
    benchmark(encode, atoms)


@pytest.mark.benchmark(group="conversion")
def test_atoms_to_dict_new(benchmark, ethanol):
    """New: atoms_to_dict(atoms) -> dict[str, Any] (no serialization)."""
    atoms = ethanol[0]
    benchmark(atoms_to_dict, atoms)


@pytest.mark.benchmark(group="conversion")
def test_decode_current(benchmark, ethanol):
    """Current: decode(data) -> ase.Atoms."""
    data = encode(ethanol[0])
    benchmark(decode, data)


@pytest.mark.benchmark(group="conversion")
def test_dict_to_atoms_new(benchmark, ethanol):
    """New: dict_to_atoms(data) -> ase.Atoms."""
    data = atoms_to_dict(ethanol[0])
    benchmark(dict_to_atoms, data)


# --- Sequential read: full dataset ---


@pytest.mark.benchmark(group="read_backend")
def test_read_current_aseio(benchmark, ethanol, tmp_path):
    """Current ASEIO: direct BytesIO + decode path."""
    db_path = tmp_path / "read_current.lmdb"
    bio = BytesIO(str(db_path))
    bio.extend([encode(a) for a in ethanol])

    def read_all():
        return [decode(bio[i]) for i in range(len(bio))]

    results = benchmark(read_all)
    assert len(results) == len(ethanol)


@pytest.mark.benchmark(group="read_backend")
def test_read_new_aseio(benchmark, ethanol, tmp_path):
    """New ASEIO: LMDBBackend path with atoms_to_dict/dict_to_atoms."""
    db_path = tmp_path / "read_new.lmdb"
    db = ASEIO(str(db_path))
    db.extend(ethanol)

    def read_all():
        return [db[i] for i in range(len(db))]

    results = benchmark(read_all)
    assert len(results) == len(ethanol)


# --- Sequential write: full dataset ---


@pytest.mark.benchmark(group="write_backend")
def test_write_current_aseio(benchmark, ethanol, tmp_path):
    """Current path: encode + BytesIO.extend."""

    def write_all():
        db_path = tmp_path / f"write_current_{uuid.uuid4().hex}.lmdb"
        bio = BytesIO(str(db_path))
        bio.extend([encode(a) for a in ethanol])
        return bio

    bio = benchmark(write_all)
    assert len(bio) == len(ethanol)


@pytest.mark.benchmark(group="write_backend")
def test_write_new_aseio(benchmark, ethanol, tmp_path):
    """New path: atoms_to_dict + LMDBBackend.append_rows."""

    def write_all():
        db_path = tmp_path / f"write_new_{uuid.uuid4().hex}.lmdb"
        db = ASEIO(str(db_path))
        db.extend(ethanol)
        return db

    db = benchmark(write_all)
    assert len(db) == len(ethanol)


# --- Random access ---


@pytest.mark.benchmark(group="random_access_backend")
def test_random_access_current(benchmark, ethanol, tmp_path):
    """Current path: BytesIO + decode, random indices."""
    db_path = tmp_path / "random_current.lmdb"
    bio = BytesIO(str(db_path))
    bio.extend([encode(a) for a in ethanol])

    random.seed(42)
    indices = [random.randint(0, len(ethanol) - 1) for _ in range(len(ethanol))]

    def random_access():
        return [decode(bio[i]) for i in indices]

    results = benchmark(random_access)
    assert len(results) == len(ethanol)


@pytest.mark.benchmark(group="random_access_backend")
def test_random_access_new(benchmark, ethanol, tmp_path):
    """New path: LMDBBackend, random indices."""
    db_path = tmp_path / "random_new.lmdb"
    db = ASEIO(str(db_path))
    db.extend(ethanol)

    random.seed(42)
    indices = [random.randint(0, len(ethanol) - 1) for _ in range(len(ethanol))]

    def random_access():
        return [db[i] for i in indices]

    results = benchmark(random_access)
    assert len(results) == len(ethanol)


# --- Column access (new feature, no current equivalent) ---


@pytest.mark.benchmark(group="column_access")
def test_column_read_via_view(benchmark, ethanol_with_calc, tmp_path):
    """New: db["calc.energy"] column view, read 1000 energies."""
    db_path = tmp_path / "col_view.lmdb"
    db = ASEIO(str(db_path))
    db.extend(ethanol_with_calc)

    def read_energies():
        return list(db["calc.energy"])

    energies = benchmark(read_energies)
    assert len(energies) == len(ethanol_with_calc)


@pytest.mark.benchmark(group="column_access")
def test_column_read_manual_loop(benchmark, ethanol_with_calc, tmp_path):
    """Baseline: manual loop extracting energy from each Atoms object."""
    db_path = tmp_path / "col_manual.lmdb"
    db = ASEIO(str(db_path))
    db.extend(ethanol_with_calc)

    def read_energies():
        return [db[i].calc.results["energy"] for i in range(len(db))]

    energies = benchmark(read_energies)
    assert len(energies) == len(ethanol_with_calc)


@pytest.mark.benchmark(group="column_access")
def test_column_read_selective_keys(benchmark, ethanol_with_calc, tmp_path):
    """New: read_column on backend directly (skips Atoms construction)."""
    db_path = tmp_path / "col_selective.lmdb"
    backend = LMDBBackend(str(db_path))
    db = ASEIO(backend)
    db.extend(ethanol_with_calc)

    def read_energies():
        return backend.read_column("calc.energy")

    energies = benchmark(read_energies)
    assert len(energies) == len(ethanol_with_calc)


# --- View materialization ---


@pytest.mark.benchmark(group="view_materialization")
def test_row_view_iteration(benchmark, ethanol, tmp_path):
    """New: list(db[0:1000]) via RowView."""
    db_path = tmp_path / "view_iter.lmdb"
    db = ASEIO(str(db_path))
    db.extend(ethanol)

    def iterate_view():
        return list(db[0 : len(ethanol)])

    results = benchmark(iterate_view)
    assert len(results) == len(ethanol)


@pytest.mark.benchmark(group="view_materialization")
def test_direct_iteration(benchmark, ethanol, tmp_path):
    """Baseline: [db[i] for i in range(1000)]."""
    db_path = tmp_path / "direct_iter.lmdb"
    db = ASEIO(str(db_path))
    db.extend(ethanol)

    def iterate_direct():
        return [db[i] for i in range(len(db))]

    results = benchmark(iterate_direct)
    assert len(results) == len(ethanol)


# --- Multi-column access ---


@pytest.mark.benchmark(group="multi_column")
def test_multi_column_view(benchmark, ethanol_with_calc, tmp_path):
    """New: db[["calc.energy", "calc.forces"]] -> ColumnView (multi) -> to_dict()."""
    db_path = tmp_path / "multi_col.lmdb"
    db = ASEIO(str(db_path))
    db.extend(ethanol_with_calc)

    def read_multi():
        return db[["calc.energy", "calc.forces"]][: len(ethanol_with_calc)].to_dict()

    result = benchmark(read_multi)
    assert len(result["calc.energy"]) == len(ethanol_with_calc)
    assert len(result["calc.forces"]) == len(ethanol_with_calc)


@pytest.mark.benchmark(group="multi_column")
def test_multi_column_manual(benchmark, ethanol_with_calc, tmp_path):
    """Baseline: manual loop extracting energy + forces."""
    db_path = tmp_path / "multi_manual.lmdb"
    db = ASEIO(str(db_path))
    db.extend(ethanol_with_calc)

    def read_multi():
        energies = []
        forces = []
        for i in range(len(db)):
            atoms = db[i]
            energies.append(atoms.calc.results["energy"])
            forces.append(atoms.calc.results["forces"])
        return {"calc.energy": energies, "calc.forces": forces}

    result = benchmark(read_multi)
    assert len(result["calc.energy"]) == len(ethanol_with_calc)
