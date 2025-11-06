import ase
import molify
import pytest


@pytest.fixture
def ethanol() -> list[ase.Atoms]:
    """Return a list of ethanol molecules."""
    frames = molify.smiles2conformers("CCO", numConfs=1000)
    return frames
