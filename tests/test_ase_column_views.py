"""Tests for ASEIO column access always returning Atoms.

- db["calc.energy"][0] → Atoms with energy
- db["calc.energy"][:3] → [Atoms, Atoms, Atoms]
- db[["calc.energy","info.tag"]][0] → Atoms with energy + tag
- db[["calc.energy","info.tag"]][:3] → [Atoms, Atoms, Atoms]

ASEIO column access wraps ObjectIO's dimensionality through dict_to_atoms().
"""
from __future__ import annotations

from typing import Any

import ase
import numpy as np
import pytest

from asebytes._backends import ReadWriteBackend
from asebytes._async_backends import SyncToAsyncAdapter
from asebytes.io import ASEIO
from asebytes._async_io import AsyncASEIO


# ── In-memory backend ───────────────────────────────────────────────────


class MemoryBackend(ReadWriteBackend):
    def __init__(self):
        self._rows: list[dict[str, Any] | None] = []

    def __len__(self):
        return len(self._rows)

    def schema(self):
        if not self._rows or self._rows[0] is None:
            return []
        return sorted(self._rows[0].keys())

    def get(self, index, keys=None):
        if index < 0 or index >= len(self._rows):
            raise IndexError(index)
        row = self._rows[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    def set(self, index, data):
        if index < len(self._rows):
            self._rows[index] = data
        elif index == len(self._rows):
            self._rows.append(data)
        else:
            raise IndexError(index)

    def insert(self, index, data):
        self._rows.insert(index, data)

    def delete(self, index):
        del self._rows[index]

    def extend(self, data):
        self._rows.extend(data)

    def get_column(self, key, indices=None):
        if indices is None:
            indices = list(range(len(self)))
        return [self.get(i, [key]).get(key) for i in indices]


def _make_row(i: int) -> dict[str, Any]:
    return {
        "arrays.numbers": np.array([1, 8]),
        "arrays.positions": np.array([[0.0, 0.0, float(i)], [1.0, 0.0, float(i)]]),
        "cell": np.zeros((3, 3)),
        "pbc": np.array([False, False, False]),
        "calc.energy": float(-i),
        "calc.forces": np.zeros((2, 3)),
        "info.tag": f"mol_{i}",
    }


@pytest.fixture
def backend():
    b = MemoryBackend()
    for i in range(5):
        b.extend([_make_row(i)])
    return b


@pytest.fixture
def db(backend):
    return ASEIO(backend)


@pytest.fixture
def async_db(backend):
    return AsyncASEIO(SyncToAsyncAdapter(backend))


# ── Sync ASEIO column access → Atoms ────────────────────────────────────


class TestASEIOSingleKeyColumnReturnsAtoms:
    def test_single_key_int_returns_atoms(self, db):
        """db["calc.energy"][0] → Atoms with energy."""
        result = db["calc.energy"][0]
        assert isinstance(result, ase.Atoms)

    def test_single_key_int_has_requested_data(self, db):
        result = db["calc.energy"][0]
        assert result.calc is not None
        assert result.calc.results["energy"] == 0.0

    def test_single_key_slice_returns_atoms_list(self, db):
        """db["calc.energy"][:3] → [Atoms, Atoms, Atoms]."""
        result = db["calc.energy"][:3].to_list()
        assert len(result) == 3
        assert all(isinstance(r, ase.Atoms) for r in result)
        assert result[1].calc.results["energy"] == -1.0

    def test_single_key_iter_yields_atoms(self, db):
        result = list(db["calc.energy"][:3])
        assert all(isinstance(r, ase.Atoms) for r in result)


class TestASEIOMultiKeyColumnReturnsAtoms:
    def test_multi_key_int_returns_atoms(self, db):
        """db[["calc.energy","info.tag"]][0] → Atoms with energy + tag."""
        result = db[["calc.energy", "info.tag"]][0]
        assert isinstance(result, ase.Atoms)

    def test_multi_key_int_has_both_fields(self, db):
        result = db[["calc.energy", "info.tag"]][0]
        assert result.calc.results["energy"] == 0.0
        assert result.info["tag"] == "mol_0"

    def test_multi_key_slice_returns_atoms_list(self, db):
        """db[["calc.energy","info.tag"]][:3] → [Atoms, Atoms, Atoms]."""
        result = db[["calc.energy", "info.tag"]][:3].to_list()
        assert len(result) == 3
        assert all(isinstance(r, ase.Atoms) for r in result)


# ── Async ASEIO column access → Atoms ───────────────────────────────────


class TestASEIORowViewColumnChaining:
    def test_rowview_to_column_returns_atoms(self, db):
        """db[0:3]["calc.energy"][0] → Atoms."""
        result = db[0:3]["calc.energy"][0]
        assert isinstance(result, ase.Atoms)

    def test_rowview_to_multi_column_returns_atoms(self, db):
        """db[0:3][["calc.energy","info.tag"]][0] → Atoms."""
        result = db[0:3][["calc.energy", "info.tag"]][0]
        assert isinstance(result, ase.Atoms)


class TestAsyncASEIORowViewColumnChaining:
    @pytest.mark.anyio
    async def test_rowview_to_column_returns_atoms(self, async_db):
        """await db[0:3]["calc.energy"] → [Atoms, Atoms, Atoms]."""
        result = await async_db[0:3]["calc.energy"].to_list()
        assert len(result) == 3
        assert all(isinstance(r, ase.Atoms) for r in result)


class TestAsyncASEIOSingleKeyColumn:
    @pytest.mark.anyio
    async def test_single_key_to_list_returns_atoms(self, async_db):
        result = await async_db["calc.energy"][:3].to_list()
        assert len(result) == 3
        assert all(isinstance(r, ase.Atoms) for r in result)
        assert result[0].calc.results["energy"] == 0.0

    @pytest.mark.anyio
    async def test_single_key_aiter_yields_atoms(self, async_db):
        result = []
        async for item in async_db["calc.energy"][:3]:
            result.append(item)
        assert all(isinstance(r, ase.Atoms) for r in result)


class TestAsyncASEIOMultiKeyColumn:
    @pytest.mark.anyio
    async def test_multi_key_to_list_returns_atoms(self, async_db):
        result = await async_db[["calc.energy", "info.tag"]][:3].to_list()
        assert len(result) == 3
        assert all(isinstance(r, ase.Atoms) for r in result)
        assert result[0].calc.results["energy"] == 0.0
        assert result[0].info["tag"] == "mol_0"

    @pytest.mark.anyio
    async def test_multi_key_aiter_yields_atoms(self, async_db):
        result = []
        async for item in async_db[["calc.energy", "info.tag"]][:3]:
            result.append(item)
        assert all(isinstance(r, ase.Atoms) for r in result)


# ── ASEColumnView.to_dict() is not available ────────────────────────────


class TestASEColumnViewNoToDict:
    """to_dict() must raise TypeError on ASE column views.

    ASEIO only deals in ase.Atoms — there are no dicts in this world.
    """

    def test_sync_single_key_to_dict_raises(self, db):
        with pytest.raises(TypeError, match="to_dict.*not available"):
            db["calc.energy"].to_dict()

    def test_sync_multi_key_to_dict_raises(self, db):
        with pytest.raises(TypeError, match="to_dict.*not available"):
            db[["calc.energy", "info.tag"]].to_dict()

    @pytest.mark.anyio
    async def test_async_single_key_to_dict_raises(self, async_db):
        with pytest.raises(TypeError, match="to_dict.*not available"):
            await async_db["calc.energy"].to_dict()

    @pytest.mark.anyio
    async def test_async_multi_key_to_dict_raises(self, async_db):
        with pytest.raises(TypeError, match="to_dict.*not available"):
            await async_db[["calc.energy", "info.tag"]].to_dict()
