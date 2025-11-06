import pytest

import asebytes


@pytest.fixture
def io(tmp_path):
    return asebytes.ASEIO(str(tmp_path / "test.db"), prefix=b"atoms/")


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


def test_get_all_keys(io, ethanol):
    # Test that get() without keys parameter returns full Atoms object
    io[0] = ethanol[0]
    atoms_from_getitem = io[0]
    atoms_from_get = io.get(0)
    assert atoms_from_get == atoms_from_getitem


def test_get_specific_keys(io, ethanol):
    # Test that get() with keys parameter returns partial Atoms object
    io[0] = ethanol[0]
    # Request only positions and numbers, but not info keys
    atoms = io.get(0, keys=[b"cell", b"pbc", b"arrays.positions", b"arrays.numbers"])
    assert len(atoms) == len(ethanol[0])
    # Info should be empty since we didn't request info keys
    assert len(atoms.info) == 0


def test_get_with_info_keys(io, ethanol):
    # Test that get() includes requested info keys
    io[0] = ethanol[0]
    atoms = io.get(
        0,
        keys=[
            b"cell",
            b"pbc",
            b"arrays.positions",
            b"arrays.numbers",
            b"info.smiles",
        ],
    )
    assert "smiles" in atoms.info
    # connectivity should not be present since we didn't request it
    assert "connectivity" not in atoms.info


def test_get_with_calc_keys(io, ethanol):
    # Test that get() includes requested calc keys
    import numpy as np
    from ase.calculators.singlepoint import SinglePointCalculator

    atoms = ethanol[0].copy()
    atoms.calc = SinglePointCalculator(atoms)
    atoms.calc.results = {"energy": -10.5, "forces": np.array([[0.1, 0.2, 0.3]])}
    io[0] = atoms

    # Get with calc keys
    retrieved = io.get(
        0,
        keys=[
            b"cell",
            b"pbc",
            b"arrays.positions",
            b"arrays.numbers",
            b"calc.energy",
        ],
    )
    assert retrieved.calc is not None
    assert "energy" in retrieved.calc.results
    # forces should not be present since we didn't request it
    assert "forces" not in retrieved.calc.results


def test_get_nonexistent_index(io):
    # Test that get() raises KeyError for non-existent index
    with pytest.raises(KeyError, match="Index 0 not found"):
        io.get(0)


def test_get_available_keys(io, ethanol):
    # Test that get_available_keys() returns all keys for an index
    io[0] = ethanol[0]
    keys = io.get_available_keys(0)
    assert b"cell" in keys
    assert b"pbc" in keys
    assert b"arrays.positions" in keys
    assert b"arrays.numbers" in keys
    assert b"info.smiles" in keys
    assert b"info.connectivity" in keys


def test_get_available_keys_nonexistent_index(io):
    # Test that get_available_keys() raises KeyError for non-existent index
    with pytest.raises(KeyError, match="Index 0 not found"):
        io.get_available_keys(0)
