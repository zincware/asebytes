"""Tests for auto copy semantics based on backend mutability."""
from __future__ import annotations

import numpy as np
import pytest

from asebytes._backends import ReadBackend, ReadWriteBackend
from asebytes._async_backends import AsyncReadBackend, AsyncReadWriteBackend


class TestBackendMutabilityFlag:
    def test_read_backend_not_mutable(self):
        assert ReadBackend._returns_mutable is False

    def test_readwrite_backend_mutable(self):
        assert ReadWriteBackend._returns_mutable is True

    def test_async_read_backend_not_mutable(self):
        assert AsyncReadBackend._returns_mutable is False

    def test_async_readwrite_backend_mutable(self):
        assert AsyncReadWriteBackend._returns_mutable is True


class TestCopyOnReadWrite:
    """ReadWriteBackends copy arrays so mutations don't corrupt storage."""

    def test_returned_positions_are_copies(self, tmp_path, simple_atoms):
        from asebytes import ASEIO
        db = ASEIO(str(tmp_path / "test.lmdb"))
        db.extend([simple_atoms])
        atoms = db[0]
        original = atoms.positions.copy()
        atoms.positions[:] = 999.0
        atoms2 = db[0]
        np.testing.assert_array_equal(atoms2.positions, original)


class TestDictToAtomsCopyParameter:
    """Direct tests for the copy parameter."""

    def test_copy_true_makes_independent_arrays(self):
        from asebytes._convert import dict_to_atoms
        data = {
            "arrays.numbers": np.array([1, 8]),
            "arrays.positions": np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]),
            "cell": np.zeros((3, 3)),
            "pbc": np.array([False, False, False]),
        }
        atoms = dict_to_atoms(data, copy=True)
        atoms.positions[:] = 999.0
        np.testing.assert_array_equal(data["arrays.positions"], [[0, 0, 0], [1, 0, 0]])

    def test_copy_false_shares_arrays(self):
        from asebytes._convert import dict_to_atoms
        pos = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
        data = {
            "arrays.numbers": np.array([1, 8]),
            "arrays.positions": pos,
            "cell": np.zeros((3, 3)),
            "pbc": np.array([False, False, False]),
        }
        atoms = dict_to_atoms(data, copy=False)
        atoms.positions[:] = 999.0
        # With copy=False, modifying atoms.positions also modifies the original
        assert pos[0, 0] == 999.0
