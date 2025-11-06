import asebytes
import pytest

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
