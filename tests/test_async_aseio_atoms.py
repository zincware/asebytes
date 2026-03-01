"""Tests for AsyncASEIO returning Atoms from _build_result.

Phase 1: await db[0] should return ase.Atoms, not dict.
"""

from __future__ import annotations

from typing import Any

import ase
import pytest

from asebytes._async_io import AsyncASEIO
from asebytes._async_backends import SyncToAsyncAdapter
from asebytes._backends import ReadWriteBackend


class MemoryBackend(ReadWriteBackend):
    def __init__(self):
        self._rows: list[dict[str, Any] | None] = []

    def __len__(self) -> int:
        return len(self._rows)

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

    @staticmethod
    def list_groups(path: str, **kwargs) -> list[str]:
        return []


def _make_row(i: int) -> dict[str, Any]:
    return {
        "arrays.numbers": [1, 2],
        "arrays.positions": [[0.0, 0.0, float(i)], [1.0, 0.0, float(i)]],
        "cell": [[10.0, 0, 0], [0, 10.0, 0], [0, 0, 10.0]],
        "pbc": [True, True, True],
        "calc.energy": float(-i),
        "info.tag": f"mol_{i}",
    }


@pytest.fixture
def db():
    b = MemoryBackend()
    for i in range(5):
        b.extend([_make_row(i)])
    return AsyncASEIO(SyncToAsyncAdapter(b))


class TestAsyncASEIOReturnsAtoms:
    @pytest.mark.anyio
    async def test_await_single_returns_atoms(self, db):
        """await db[0] should return ase.Atoms, not dict."""
        result = await db[0]
        assert isinstance(result, ase.Atoms)

    @pytest.mark.anyio
    async def test_await_single_has_energy(self, db):
        """Atoms returned should have calculator with energy."""
        result = await db[0]
        assert result.calc is not None
        assert result.calc.results["energy"] == 0.0

    @pytest.mark.anyio
    async def test_await_single_has_tag(self, db):
        """Atoms returned should have info dict."""
        result = await db[0]
        assert result.info["tag"] == "mol_0"

    @pytest.mark.anyio
    async def test_await_none_returns_none(self, db):
        """await db[i] where row is None should still return None."""
        # Write None to slot 0
        await db[0].set(None)
        result = await db[0]
        assert result is None

    @pytest.mark.anyio
    async def test_await_slice_returns_atoms_list(self, db):
        """await db[0:3] should return list of Atoms."""
        result = await db[0:3].to_list()
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(r, ase.Atoms) for r in result)

    @pytest.mark.anyio
    async def test_aiter_yields_atoms(self, db):
        """async for row in db should yield Atoms."""
        results = []
        async for row in db:
            results.append(row)
        assert len(results) == 5
        assert all(isinstance(r, ase.Atoms) for r in results)
