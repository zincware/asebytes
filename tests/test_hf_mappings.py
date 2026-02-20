"""Tests for asebytes.hf ColumnMapping dataclass and presets."""

from __future__ import annotations

import numpy as np
import pytest

from asebytes.hf import COLABFIT, OPTIMADE, ColumnMapping


class TestColumnMappingCreation:
    """Test ColumnMapping dataclass construction."""

    def test_minimal_creation(self):
        """Minimal valid mapping: just positions and numbers."""
        m = ColumnMapping(positions="pos", numbers="nums")
        assert m.positions == "pos"
        assert m.numbers == "nums"
        assert m.cell is None
        assert m.pbc is None
        assert m.calc == {}
        assert m.info == {}
        assert m.arrays == {}
        assert m.species_are_strings is False
        assert m.pbc_are_dimension_types is False

    def test_full_creation(self):
        """All fields explicitly set."""
        m = ColumnMapping(
            positions="cart_pos",
            numbers="species",
            cell="lattice",
            pbc="dim_types",
            calc={"energy": "total_energy"},
            info={"label": "material_id"},
            arrays={"forces": "atomic_forces"},
            species_are_strings=True,
            pbc_are_dimension_types=True,
        )
        assert m.positions == "cart_pos"
        assert m.numbers == "species"
        assert m.cell == "lattice"
        assert m.pbc == "dim_types"
        assert m.calc == {"energy": "total_energy"}
        assert m.info == {"label": "material_id"}
        assert m.arrays == {"forces": "atomic_forces"}
        assert m.species_are_strings is True
        assert m.pbc_are_dimension_types is True

    def test_frozen(self):
        """ColumnMapping is frozen (immutable)."""
        m = ColumnMapping(positions="pos", numbers="nums")
        with pytest.raises(AttributeError):
            m.positions = "other"

    def test_default_dicts_are_independent(self):
        """Default empty dicts should not be shared between instances."""
        m1 = ColumnMapping(positions="pos", numbers="nums")
        m2 = ColumnMapping(positions="pos", numbers="nums")
        # They should be equal but not the same object
        assert m1.calc == m2.calc == {}


class TestApplyBasic:
    """Test ColumnMapping.apply() basic functionality."""

    def test_apply_full_row(self):
        """Apply with all mapped columns present."""
        m = ColumnMapping(
            positions="pos",
            numbers="nums",
            cell="unit_cell",
            pbc="periodic",
            calc={"energy": "total_energy", "forces": "atomic_forces"},
            info={"label": "material_id"},
        )
        row = {
            "pos": [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
            "nums": [6, 8],
            "unit_cell": [[10.0, 0.0, 0.0], [0.0, 10.0, 0.0], [0.0, 0.0, 10.0]],
            "periodic": [True, True, False],
            "total_energy": -42.5,
            "atomic_forces": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
            "material_id": "mp-1234",
        }
        result = m.apply(row)

        # Positions
        assert "arrays.positions" in result
        np.testing.assert_array_equal(
            result["arrays.positions"],
            np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]),
        )

        # Numbers
        assert "arrays.numbers" in result
        np.testing.assert_array_equal(result["arrays.numbers"], np.array([6, 8]))

        # Cell
        assert "cell" in result
        np.testing.assert_array_equal(
            result["cell"],
            np.array([[10.0, 0.0, 0.0], [0.0, 10.0, 0.0], [0.0, 0.0, 10.0]]),
        )

        # PBC
        assert "pbc" in result
        np.testing.assert_array_equal(
            result["pbc"], np.array([True, True, False])
        )

        # Calc
        assert result["calc.energy"] == -42.5
        np.testing.assert_array_equal(
            result["calc.forces"],
            np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]),
        )

        # Info
        assert result["info.label"] == "mp-1234"

    def test_apply_missing_optional_cell(self):
        """When cell mapping is None, default to zeros."""
        m = ColumnMapping(positions="pos", numbers="nums", cell=None)
        row = {"pos": [[0.0, 0.0, 0.0]], "nums": [1]}
        result = m.apply(row)

        assert "cell" in result
        np.testing.assert_array_equal(result["cell"], np.zeros((3, 3)))

    def test_apply_missing_optional_pbc(self):
        """When pbc mapping is None, default to [False, False, False]."""
        m = ColumnMapping(positions="pos", numbers="nums", pbc=None)
        row = {"pos": [[0.0, 0.0, 0.0]], "nums": [1]}
        result = m.apply(row)

        assert "pbc" in result
        np.testing.assert_array_equal(
            result["pbc"], np.array([False, False, False])
        )

    def test_apply_cell_column_missing_from_row(self):
        """Cell column is mapped but not present in row => zeros."""
        m = ColumnMapping(positions="pos", numbers="nums", cell="unit_cell")
        row = {"pos": [[0.0, 0.0, 0.0]], "nums": [1]}
        result = m.apply(row)

        np.testing.assert_array_equal(result["cell"], np.zeros((3, 3)))

    def test_apply_pbc_column_missing_from_row(self):
        """PBC column is mapped but not present in row => default False."""
        m = ColumnMapping(positions="pos", numbers="nums", pbc="periodic")
        row = {"pos": [[0.0, 0.0, 0.0]], "nums": [1]}
        result = m.apply(row)

        np.testing.assert_array_equal(
            result["pbc"], np.array([False, False, False])
        )

    def test_apply_cell_none_value_in_row(self):
        """Cell column exists in row but is None => zeros."""
        m = ColumnMapping(positions="pos", numbers="nums", cell="unit_cell")
        row = {"pos": [[0.0, 0.0, 0.0]], "nums": [1], "unit_cell": None}
        result = m.apply(row)

        np.testing.assert_array_equal(result["cell"], np.zeros((3, 3)))

    def test_apply_pbc_none_value_in_row(self):
        """PBC column exists in row but is None => default False."""
        m = ColumnMapping(positions="pos", numbers="nums", pbc="periodic")
        row = {"pos": [[0.0, 0.0, 0.0]], "nums": [1], "periodic": None}
        result = m.apply(row)

        np.testing.assert_array_equal(
            result["pbc"], np.array([False, False, False])
        )


class TestApplyUnmapped:
    """Test that unmapped columns become info.* entries."""

    def test_unmapped_columns_go_to_info(self):
        m = ColumnMapping(positions="pos", numbers="nums")
        row = {
            "pos": [[0.0, 0.0, 0.0]],
            "nums": [1],
            "description": "water molecule",
            "source_id": 42,
        }
        result = m.apply(row)

        assert result["info.description"] == "water molecule"
        assert result["info.source_id"] == 42

    def test_unmapped_does_not_duplicate_mapped(self):
        """Mapped columns should not also appear as info.*."""
        m = ColumnMapping(
            positions="pos",
            numbers="nums",
            cell="unit_cell",
            pbc="periodic",
            calc={"energy": "total_energy"},
            info={"label": "material_id"},
        )
        row = {
            "pos": [[0.0, 0.0, 0.0]],
            "nums": [1],
            "unit_cell": [[10, 0, 0], [0, 10, 0], [0, 0, 10]],
            "periodic": [True, True, True],
            "total_energy": -5.0,
            "material_id": "mp-1",
            "extra_col": "should be info",
        }
        result = m.apply(row)

        # extra_col should be info
        assert result["info.extra_col"] == "should be info"
        # Mapped columns should not appear as info.* (double-check)
        assert "info.pos" not in result
        assert "info.nums" not in result
        assert "info.unit_cell" not in result
        assert "info.periodic" not in result
        assert "info.total_energy" not in result
        assert "info.material_id" not in result

    def test_explicit_info_overrides_unmapped(self):
        """Explicitly mapped info columns should map to the correct key."""
        m = ColumnMapping(
            positions="pos",
            numbers="nums",
            info={"formula": "chemical_formula"},
        )
        row = {
            "pos": [[0.0, 0.0, 0.0]],
            "nums": [1],
            "chemical_formula": "H2O",
            "extra": "value",
        }
        result = m.apply(row)

        assert result["info.formula"] == "H2O"
        # chemical_formula is already consumed by info mapping, should NOT be info.chemical_formula
        assert "info.chemical_formula" not in result
        assert result["info.extra"] == "value"


class TestApplyExtraArrays:
    """Test extra arrays mapping."""

    def test_extra_arrays_mapping(self):
        m = ColumnMapping(
            positions="pos",
            numbers="nums",
            arrays={"forces": "atomic_forces", "charges": "mulliken_charges"},
        )
        row = {
            "pos": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
            "nums": [1, 1],
            "atomic_forces": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
            "mulliken_charges": [0.1, -0.1],
        }
        result = m.apply(row)

        assert "arrays.forces" in result
        np.testing.assert_array_equal(
            result["arrays.forces"],
            np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]),
        )
        assert "arrays.charges" in result
        np.testing.assert_array_equal(
            result["arrays.charges"], np.array([0.1, -0.1])
        )
        # These columns should not appear as unmapped info
        assert "info.atomic_forces" not in result
        assert "info.mulliken_charges" not in result


class TestColabfitPreset:
    """Test COLABFIT preset values and apply."""

    def test_field_values(self):
        assert COLABFIT.positions == "positions"
        assert COLABFIT.numbers == "atomic_numbers"
        assert COLABFIT.cell == "cell"
        assert COLABFIT.pbc == "pbc"
        assert COLABFIT.calc == {
            "energy": "energy",
            "forces": "atomic_forces",
            "stress": "cauchy_stress",
        }
        assert COLABFIT.species_are_strings is False
        assert COLABFIT.pbc_are_dimension_types is False

    def test_apply_sample_row(self):
        row = {
            "positions": [[0.0, 0.0, 0.0], [1.5, 1.5, 1.5]],
            "atomic_numbers": [14, 14],
            "cell": [[5.43, 0, 0], [0, 5.43, 0], [0, 0, 5.43]],
            "pbc": [True, True, True],
            "energy": -10.8,
            "atomic_forces": [[0.01, -0.02, 0.03], [-0.01, 0.02, -0.03]],
            "cauchy_stress": [0.1, 0.2, 0.3, 0.0, 0.0, 0.0],
            "configuration_name": "silicon-diamond",
        }
        result = COLABFIT.apply(row)

        np.testing.assert_array_equal(
            result["arrays.positions"],
            np.array([[0.0, 0.0, 0.0], [1.5, 1.5, 1.5]]),
        )
        np.testing.assert_array_equal(
            result["arrays.numbers"], np.array([14, 14])
        )
        np.testing.assert_array_equal(
            result["cell"],
            np.array([[5.43, 0, 0], [0, 5.43, 0], [0, 0, 5.43]]),
        )
        np.testing.assert_array_equal(
            result["pbc"], np.array([True, True, True])
        )
        assert result["calc.energy"] == -10.8
        np.testing.assert_array_equal(
            result["calc.forces"],
            np.array([[0.01, -0.02, 0.03], [-0.01, 0.02, -0.03]]),
        )
        np.testing.assert_array_equal(
            result["calc.stress"],
            np.array([0.1, 0.2, 0.3, 0.0, 0.0, 0.0]),
        )
        # Unmapped column goes to info
        assert result["info.configuration_name"] == "silicon-diamond"


class TestOptimadePreset:
    """Test OPTIMADE preset values and apply with species strings and dimension_types."""

    def test_field_values(self):
        assert OPTIMADE.positions == "cartesian_site_positions"
        assert OPTIMADE.numbers == "species_at_sites"
        assert OPTIMADE.cell == "lattice_vectors"
        assert OPTIMADE.pbc == "dimension_types"
        assert OPTIMADE.species_are_strings is True
        assert OPTIMADE.pbc_are_dimension_types is True

    def test_apply_with_species_strings(self):
        """Species strings like 'C', 'O' should be converted to atomic numbers."""
        row = {
            "cartesian_site_positions": [[0.0, 0.0, 0.0], [1.2, 0.0, 0.0]],
            "species_at_sites": ["C", "O"],
            "lattice_vectors": [[10, 0, 0], [0, 10, 0], [0, 0, 10]],
            "dimension_types": [1, 1, 1],
        }
        result = OPTIMADE.apply(row)

        # C=6, O=8
        np.testing.assert_array_equal(
            result["arrays.numbers"], np.array([6, 8])
        )

    def test_apply_with_dimension_types(self):
        """dimension_types [1, 1, 0] should become pbc [True, True, False]."""
        row = {
            "cartesian_site_positions": [[0.0, 0.0, 0.0]],
            "species_at_sites": ["H"],
            "lattice_vectors": [[10, 0, 0], [0, 10, 0], [0, 0, 10]],
            "dimension_types": [1, 1, 0],
        }
        result = OPTIMADE.apply(row)

        np.testing.assert_array_equal(
            result["pbc"], np.array([True, True, False])
        )

    def test_apply_non_periodic(self):
        """dimension_types [0, 0, 0] should become pbc [False, False, False]."""
        row = {
            "cartesian_site_positions": [[0.0, 0.0, 0.0]],
            "species_at_sites": ["H"],
            "lattice_vectors": None,
            "dimension_types": [0, 0, 0],
        }
        result = OPTIMADE.apply(row)

        np.testing.assert_array_equal(
            result["pbc"], np.array([False, False, False])
        )
        np.testing.assert_array_equal(result["cell"], np.zeros((3, 3)))

    def test_apply_unmapped_columns(self):
        """Unmapped OPTIMADE columns should go to info.*."""
        row = {
            "cartesian_site_positions": [[0.0, 0.0, 0.0]],
            "species_at_sites": ["H"],
            "lattice_vectors": [[10, 0, 0], [0, 10, 0], [0, 0, 10]],
            "dimension_types": [1, 1, 1],
            "chemical_formula_descriptive": "H",
            "nelements": 1,
        }
        result = OPTIMADE.apply(row)

        assert result["info.chemical_formula_descriptive"] == "H"
        assert result["info.nelements"] == 1


class TestApplyEdgeCases:
    """Edge cases for apply."""

    def test_apply_empty_calc_dict(self):
        """No calc columns mapped, none in row."""
        m = ColumnMapping(positions="pos", numbers="nums")
        row = {"pos": [[0, 0, 0]], "nums": [1]}
        result = m.apply(row)

        # Should have no calc.* keys
        calc_keys = [k for k in result if k.startswith("calc.")]
        assert calc_keys == []

    def test_apply_calc_column_missing_from_row(self):
        """Calc column mapped but not in row => skip it."""
        m = ColumnMapping(
            positions="pos",
            numbers="nums",
            calc={"energy": "total_energy"},
        )
        row = {"pos": [[0, 0, 0]], "nums": [1]}
        result = m.apply(row)

        assert "calc.energy" not in result

    def test_apply_positions_are_numpy(self):
        """Positions should always be returned as numpy array."""
        m = ColumnMapping(positions="pos", numbers="nums")
        row = {"pos": [[1.0, 2.0, 3.0]], "nums": [1]}
        result = m.apply(row)

        assert isinstance(result["arrays.positions"], np.ndarray)
        assert result["arrays.positions"].dtype == np.float64 or np.issubdtype(
            result["arrays.positions"].dtype, np.floating
        )

    def test_apply_numbers_are_numpy(self):
        """Numbers should always be returned as numpy array."""
        m = ColumnMapping(positions="pos", numbers="nums")
        row = {"pos": [[0, 0, 0]], "nums": [6]}
        result = m.apply(row)

        assert isinstance(result["arrays.numbers"], np.ndarray)
