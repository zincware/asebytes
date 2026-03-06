"""Read-only backend contract tests.

Tests ASE file formats (.traj, .xyz, .extxyz) and HuggingFace backends
through the ASEIO facade for the read-only contract subset:
get, slice, keys, len, iteration, and write-rejection.
"""

from __future__ import annotations

import ase
import numpy as np
import pytest


# ---------------------------------------------------------------------------
# ASE read-only format tests (parametrized over .traj, .xyz, .extxyz)
# ---------------------------------------------------------------------------


class TestReadOnlyASE:
    """Contract tests for ASE file-based read-only backends."""

    def test_len(self, readonly_aseio):
        assert len(readonly_aseio) == 22

    def test_getitem_by_index(self, readonly_aseio):
        atoms = readonly_aseio[0]
        assert isinstance(atoms, ase.Atoms)
        assert len(atoms) > 0

    def test_getitem_negative_index(self, readonly_aseio):
        atoms = readonly_aseio[-1]
        assert isinstance(atoms, ase.Atoms)
        assert len(atoms) > 0

    def test_slice(self, readonly_aseio):
        result = readonly_aseio[0:5]
        items = list(result)
        assert len(items) == 5
        for atoms in items:
            assert isinstance(atoms, ase.Atoms)

    def test_iteration(self, readonly_aseio):
        count = 0
        for atoms in readonly_aseio:
            assert isinstance(atoms, ase.Atoms)
            count += 1
        assert count == 22

    def test_keys(self, readonly_aseio):
        keys = readonly_aseio.keys(0)
        assert isinstance(keys, list)
        assert all(isinstance(k, str) for k in keys)
        # All ASE formats store at least positions and numbers
        key_str = " ".join(keys)
        assert "numbers" in key_str or "arrays.numbers" in key_str
        assert "positions" in key_str or "arrays.positions" in key_str

    def test_write_rejected_extend(self, readonly_aseio):
        simple = ase.Atoms("H2", positions=[[0, 0, 0], [0, 0, 1]])
        with pytest.raises(TypeError, match="read-only"):
            readonly_aseio.extend([simple])

    def test_write_rejected_setitem(self, readonly_aseio):
        simple = ase.Atoms("H2", positions=[[0, 0, 0], [0, 0, 1]])
        with pytest.raises(TypeError, match="read-only"):
            readonly_aseio[0] = simple

    def test_positions_preserved(self, readonly_aseio, s22):
        atoms = readonly_aseio[0]
        np.testing.assert_allclose(
            atoms.positions, s22[0].positions, atol=1e-6,
            err_msg="positions not preserved through write/read cycle",
        )

    def test_numbers_preserved(self, readonly_aseio, s22):
        atoms = readonly_aseio[0]
        np.testing.assert_array_equal(
            atoms.get_atomic_numbers(), s22[0].get_atomic_numbers(),
            err_msg="atomic numbers not preserved through write/read cycle",
        )


# ---------------------------------------------------------------------------
# HuggingFace tests (synthetic dataset, no network required)
# ---------------------------------------------------------------------------


@pytest.mark.hf
class TestReadOnlyHF:
    """Contract tests for HuggingFace read-only backend (synthetic)."""

    def test_hf_len(self, hf_aseio):
        assert len(hf_aseio) == 22

    def test_hf_getitem(self, hf_aseio):
        atoms = hf_aseio[0]
        assert isinstance(atoms, ase.Atoms)
        assert len(atoms) > 0

    def test_hf_slice(self, hf_aseio):
        result = hf_aseio[0:3]
        items = list(result)
        assert len(items) == 3
        for atoms in items:
            assert isinstance(atoms, ase.Atoms)

    def test_hf_iteration(self, hf_aseio):
        count = 0
        for atoms in hf_aseio:
            assert isinstance(atoms, ase.Atoms)
            count += 1
            if count >= 5:
                break
        assert count == 5

    def test_hf_keys(self, hf_aseio):
        keys = hf_aseio.keys(0)
        assert isinstance(keys, list)
        assert all(isinstance(k, str) for k in keys)
        assert len(keys) > 0

    def test_hf_write_rejected(self, hf_aseio):
        simple = ase.Atoms("H2", positions=[[0, 0, 0], [0, 0, 1]])
        with pytest.raises(TypeError, match="read-only"):
            hf_aseio.extend([simple])
