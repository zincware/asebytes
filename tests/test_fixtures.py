"""Test that shared fixtures work correctly."""

import numpy as np
import pytest

import asebytes


def test_simple_atoms_fixture(simple_atoms):
    """Test the simple_atoms fixture."""
    assert len(simple_atoms) == 1
    assert simple_atoms.get_chemical_symbols() == ["H"]


def test_h2o_atoms_fixture(h2o_atoms):
    """Test the h2o_atoms fixture."""
    assert len(h2o_atoms) == 3
    assert h2o_atoms.get_chemical_symbols() == ["H", "H", "O"]


def test_atoms_with_info_fixture(atoms_with_info):
    """Test the atoms_with_info fixture."""
    assert atoms_with_info.info["string_data"] == "test"
    assert atoms_with_info.info["int_data"] == 42
    assert atoms_with_info.info["float_data"] == 3.14
    assert atoms_with_info.info["bool_data"] is True
    assert atoms_with_info.info["list_data"] == [1, 2, 3]
    assert atoms_with_info.info["dict_data"] == {"key": "value"}
    assert np.array_equal(atoms_with_info.info["numpy_data"], np.array([1, 2, 3]))


def test_atoms_with_calc_fixture(atoms_with_calc):
    """Test the atoms_with_calc fixture."""
    assert atoms_with_calc.calc is not None
    assert "energy" in atoms_with_calc.calc.results
    assert atoms_with_calc.calc.results["energy"] == -10.5
    assert "forces" in atoms_with_calc.calc.results


def test_empty_atoms_fixture(empty_atoms):
    """Test the empty_atoms fixture."""
    assert len(empty_atoms) == 0


def test_atoms_with_pbc_fixture(atoms_with_pbc):
    """Test the atoms_with_pbc fixture."""
    assert list(atoms_with_pbc.pbc) == [True, True, False]
    assert atoms_with_pbc.cell[0, 0] == 10


def test_atoms_with_constraints_fixture(atoms_with_constraints):
    """Test the atoms_with_constraints fixture."""
    assert len(atoms_with_constraints.constraints) == 1


def test_bytesio_instance_fixture(bytesio_instance):
    """Test the bytesio_instance fixture."""
    assert len(bytesio_instance) == 0
    bytesio_instance[0] = {b"test": b"data"}
    assert len(bytesio_instance) == 1


def test_aseio_instance_fixture(aseio_instance, simple_atoms):
    """Test the aseio_instance fixture."""
    assert len(aseio_instance) == 0
    aseio_instance[0] = simple_atoms
    assert len(aseio_instance) == 1


def test_fixture_roundtrip_simple(simple_atoms):
    """Test roundtrip with simple_atoms fixture."""
    byte_data = asebytes.encode(simple_atoms)
    recovered = asebytes.decode(byte_data)
    assert recovered == simple_atoms


def test_fixture_roundtrip_with_info(atoms_with_info):
    """Test roundtrip with atoms_with_info fixture."""
    byte_data = asebytes.encode(atoms_with_info)
    recovered = asebytes.decode(byte_data)
    assert recovered == atoms_with_info


def test_fixture_roundtrip_with_calc(atoms_with_calc):
    """Test roundtrip with atoms_with_calc fixture."""
    byte_data = asebytes.encode(atoms_with_calc)
    recovered = asebytes.decode(byte_data)
    assert recovered.calc.results["energy"] == atoms_with_calc.calc.results["energy"]


def test_fixture_in_bytesio(bytesio_instance, h2o_atoms):
    """Test using fixture with BytesIO."""
    byte_data = asebytes.encode(h2o_atoms)
    bytesio_instance[0] = byte_data
    recovered_data = bytesio_instance[0]
    recovered_atoms = asebytes.decode(recovered_data)
    assert recovered_atoms == h2o_atoms


def test_fixture_in_aseio(aseio_instance, atoms_with_constraints):
    """Test using fixture with ASEIO."""
    aseio_instance[0] = atoms_with_constraints
    recovered = aseio_instance[0]
    assert len(recovered.constraints) == 1
