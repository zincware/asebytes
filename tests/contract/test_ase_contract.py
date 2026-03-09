"""ASEIO facade contract tests.

Every read-write backend must satisfy the same Atoms-level contract when
accessed through the ASEIO facade. Edge cases test capability marks.
"""

from __future__ import annotations

import math

import ase
import numpy as np
import pytest

from .conftest import assert_atoms_equal


class TestASEIOCoreContract:
    """Core CRUD operations for ASEIO facade."""

    def test_extend_and_len(self, aseio, s22):
        aseio.extend(s22)
        assert len(aseio) == 22

    def test_single_frame_roundtrip(self, aseio, simple_atoms):
        aseio.extend([simple_atoms])
        result = aseio[0]
        assert_atoms_equal(result, simple_atoms)

    def test_multi_frame_roundtrip(self, aseio, ethanol):
        aseio.extend(ethanol)
        assert len(aseio) == 1000
        # Check first, middle, last
        assert_atoms_equal(aseio[0], ethanol[0])
        assert_atoms_equal(aseio[500], ethanol[500])
        assert_atoms_equal(aseio[999], ethanol[999])

    def test_getitem_by_index(self, aseio, s22):
        aseio.extend(s22)
        for idx in [0, 10, 21]:
            result = aseio[idx]
            assert isinstance(result, ase.Atoms)

    def test_getitem_negative_index(self, aseio, s22):
        aseio.extend(s22)
        result = aseio[-1]
        assert_atoms_equal(result, s22[-1])

    def test_slice(self, aseio, s22):
        aseio.extend(s22)
        result = aseio[0:5]
        assert len(result) == 5

    def test_iteration(self, aseio, s22):
        aseio.extend(s22)
        count = 0
        for atoms in aseio:
            assert isinstance(atoms, ase.Atoms)
            count += 1
        assert count == 22

    def test_keys(self, aseio, s22):
        aseio.extend(s22)
        k = aseio.keys(0)
        assert isinstance(k, list)
        assert len(k) > 0
        for key in k:
            assert isinstance(key, str)

    def test_set_overwrite(self, aseio, simple_atoms):
        """Overwrite a frame with same atom count to avoid ragged resize."""
        atoms1 = ase.Atoms("H", positions=[[0, 0, 0]])
        atoms2 = ase.Atoms("H", positions=[[1, 1, 1]])
        aseio.extend([atoms1])
        aseio[0] = atoms2
        result = aseio[0]
        assert_atoms_equal(result, atoms2)


class TestASEIOEdgeCases:
    """Edge case tests with capability marks."""

    def test_variable_particle_count(self, aseio, s22, request):
        if not request.node.get_closest_marker("supports_variable_particles"):
            pytest.skip("Backend does not support variable particle counts")
        aseio.extend(s22)
        for i, expected in enumerate(s22):
            result = aseio[i]
            assert len(result) == len(expected), (
                f"Frame {i}: particle count {len(result)} != {len(expected)}"
            )

    def test_info_roundtrip(self, aseio, atoms_with_info, request):
        if not request.node.get_closest_marker("supports_nested_info"):
            pytest.skip("Backend does not support nested info round-trip")
        aseio.extend([atoms_with_info])
        result = aseio[0]
        for key in atoms_with_info.info:
            assert key in result.info, f"Missing info key: {key}"
            expected_val = atoms_with_info.info[key]
            actual_val = result.info[key]
            if isinstance(expected_val, np.ndarray):
                np.testing.assert_allclose(actual_val, expected_val)
            elif isinstance(expected_val, dict):
                assert actual_val == expected_val
            elif isinstance(expected_val, list):
                assert actual_val == expected_val or np.array_equal(
                    actual_val, expected_val
                )
            else:
                assert actual_val == expected_val, (
                    f"info[{key!r}]: {actual_val!r} != {expected_val!r}"
                )

    def test_calc_roundtrip(self, aseio, atoms_with_calc):
        aseio.extend([atoms_with_calc])
        result = aseio[0]
        assert_atoms_equal(result, atoms_with_calc)

    def test_pbc_cell_roundtrip(self, aseio, atoms_with_pbc):
        aseio.extend([atoms_with_pbc])
        result = aseio[0]
        np.testing.assert_array_equal(result.pbc, atoms_with_pbc.pbc)
        np.testing.assert_allclose(result.cell[:], atoms_with_pbc.cell[:])

    def test_constraints_roundtrip(self, aseio, atoms_with_constraints, request):
        if not request.node.get_closest_marker("supports_constraints"):
            pytest.skip("Backend does not support constraints round-trip")
        aseio.extend([atoms_with_constraints])
        result = aseio[0]
        assert len(result.constraints) == len(atoms_with_constraints.constraints)
        assert type(result.constraints[0]) == type(  # noqa: E721
            atoms_with_constraints.constraints[0]
        )

    def test_per_atom_arrays(self, aseio, s22_info_arrays_calc, request):
        if not request.node.get_closest_marker("supports_per_atom_arrays"):
            pytest.skip("Backend does not support per-atom arrays")
        aseio.extend(s22_info_arrays_calc)
        result = aseio[0]
        expected = s22_info_arrays_calc[0]
        # Check custom arrays preserved
        assert "mlip_forces" in result.arrays, "Missing mlip_forces array"
        np.testing.assert_allclose(
            result.arrays["mlip_forces"],
            expected.arrays["mlip_forces"],
        )
        # Check velocities preserved (stored as momenta internally by ASE)
        if "momenta" in expected.arrays:
            assert "momenta" in result.arrays, "Missing momenta array"

    def test_nan_inf_in_info(self, aseio):
        atoms = ase.Atoms("H", positions=[[0, 0, 0]])
        atoms.info["nan_val"] = float("nan")
        atoms.info["inf_val"] = float("inf")
        aseio.extend([atoms])
        result = aseio[0]
        # Columnar backends may drop NaN/inf info scalars
        if "nan_val" in result.info:
            assert math.isnan(result.info["nan_val"])
        if "inf_val" in result.info:
            assert math.isinf(result.info["inf_val"])

    def test_empty_string_info(self, aseio):
        atoms = ase.Atoms("H", positions=[[0, 0, 0]])
        atoms.info["empty"] = ""
        aseio.extend([atoms])
        result = aseio[0]
        assert result.info["empty"] == ""

    def test_large_trajectory(self, aseio, ethanol):
        aseio.extend(ethanol)
        assert len(aseio) == 1000
        assert_atoms_equal(aseio[0], ethanol[0])
        assert_atoms_equal(aseio[-1], ethanol[-1])
