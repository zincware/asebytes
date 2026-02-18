import numpy as np
import pytest
from ase.calculators.singlepoint import SinglePointCalculator

import asebytes


@pytest.fixture
def io(tmp_path):
    return asebytes.ASEIO(str(tmp_path / "test.lmdb"), prefix=b"atoms/")


def test_set_get(io, ethanol):
    io[0] = ethanol[0]
    atoms = io[0]
    assert atoms == ethanol[0]


def test_set_overwrite(io, ethanol):
    atoms = ethanol[0].copy()
    atoms.info["test"] = 1
    io[0] = atoms
    # overwrite with different info
    io[0] = ethanol[1]
    atoms = io[0]
    assert "test" not in atoms.info


def test_len(io, ethanol):
    for i, atom in enumerate(ethanol):
        io[i] = atom
    assert len(io) == len(ethanol)


def test_append(io, ethanol):
    for atom in ethanol:
        io[len(io)] = atom
    assert len(io) == len(ethanol)


def test_delete(io, ethanol):
    for i, atom in enumerate(ethanol):
        io[i] = atom
    del io[1]
    assert len(io) == len(ethanol) - 1
    atoms = [io[i] for i in range(len(io))]
    expected = [ethanol[0]] + ethanol[2:]
    assert atoms == expected


def test_insert(io, ethanol):
    for i, atom in enumerate(ethanol):
        io[i] = atom
    io.insert(1, ethanol[0])
    assert len(io) == len(ethanol) + 1
    atoms = [io[i] for i in range(len(io))]
    expected = [ethanol[0], ethanol[0]] + ethanol[1:]
    assert atoms == expected


def test_iter(io, ethanol):
    for i, atom in enumerate(ethanol):
        io[i] = atom
    atoms = [atom for atom in io]
    assert atoms == list(ethanol)


def test_getitem_returns_full_atoms(io, ethanol):
    io[0] = ethanol[0]
    atoms = io[0]
    assert len(atoms) == len(ethanol[0])
    assert "smiles" in atoms.info
    assert "connectivity" in atoms.info


def test_getitem_nonexistent_index_raises_indexerror(io):
    with pytest.raises(IndexError):
        io[0]


def test_columns(io, ethanol):
    io[0] = ethanol[0]
    cols = io.columns
    assert "cell" in cols
    assert "pbc" in cols
    assert "arrays.positions" in cols
    assert "arrays.numbers" in cols
    assert "info.smiles" in cols
    assert "info.connectivity" in cols


def test_columns_empty(io):
    assert io.columns == []


def test_getitem_with_calc(io, ethanol):
    atoms = ethanol[0].copy()
    atoms.calc = SinglePointCalculator(atoms)
    atoms.calc.results = {"energy": -10.5, "forces": np.array([[0.1, 0.2, 0.3]])}
    io[0] = atoms

    retrieved = io[0]
    assert retrieved.calc is not None
    assert "energy" in retrieved.calc.results
    assert "forces" in retrieved.calc.results
