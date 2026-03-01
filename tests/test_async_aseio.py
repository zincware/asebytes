"""Integration tests for AsyncASEIO facade.

Covers all operations from async-api.py using an in-memory ReadWriteBackend
wrapped via SyncToAsyncAdapter. No MongoDB — tests the full async stack
with a sync backend underneath.
"""

from __future__ import annotations

from typing import Any

import ase
import numpy as np
import pytest
from ase.calculators.singlepoint import SinglePointCalculator

from asebytes._async_io import AsyncASEIO
from asebytes._async_backends import SyncToAsyncAdapter
from asebytes._backends import ReadWriteBackend


# ── In-memory ReadWriteBackend ─────────────────────────────────────────


class MemoryBackend(ReadWriteBackend):
    """Minimal in-memory backend for integration testing."""

    def __init__(self):
        self._rows: list[dict[str, Any] | None] = []

    def __len__(self) -> int:
        return len(self._rows)

    def get(self, index: int, keys: list[str] | None = None) -> dict[str, Any] | None:
        if index < 0 or index >= len(self._rows):
            raise IndexError(index)
        row = self._rows[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    def set(self, index: int, data: dict[str, Any] | None) -> None:
        if index < len(self._rows):
            self._rows[index] = data
        elif index == len(self._rows):
            self._rows.append(data)
        else:
            raise IndexError(index)

    def insert(self, index: int, data: dict[str, Any] | None) -> None:
        self._rows.insert(index, data)

    def delete(self, index: int) -> None:
        del self._rows[index]

    def extend(self, data: list[dict[str, Any] | None]) -> int:
        self._rows.extend(data)
        return len(self._rows)

    @staticmethod
    def list_groups(path: str, **kwargs) -> list[str]:
        return []


def _make_row(i: int) -> dict[str, Any]:
    """Create a test row with realistic keys."""
    return {
        "arrays.numbers": [1, 2],
        "arrays.positions": [[0.0, 0.0, float(i)], [1.0, 0.0, float(i)]],
        "cell": [[10.0, 0, 0], [0, 10.0, 0], [0, 0, 10.0]],
        "pbc": [True, True, True],
        "calc.energy": float(-i),
        "calc.forces": [[0.0, 0.0, float(i)], [0.0, 0.0, float(-i)]],
        "info.tag": f"mol_{i}",
    }


def _make_atoms(i: int) -> ase.Atoms:
    """Create a test Atoms object matching _make_row(i) structure."""
    atoms = ase.Atoms(
        numbers=[1, 2],
        positions=[[0.0, 0.0, float(i)], [1.0, 0.0, float(i)]],
        cell=[[10.0, 0, 0], [0, 10.0, 0], [0, 0, 10.0]],
        pbc=[True, True, True],
    )
    atoms.info["tag"] = f"mol_{i}"
    forces = np.array([[0.0, 0.0, float(i)], [0.0, 0.0, float(-i)]])
    calc = SinglePointCalculator(atoms, energy=float(-i), forces=forces)
    atoms.calc = calc
    return atoms


@pytest.fixture
def backend():
    b = MemoryBackend()
    for i in range(10):
        b.extend([_make_row(i)])
    return b


@pytest.fixture
def db(backend):
    """AsyncASEIO wrapping a sync MemoryBackend."""
    return AsyncASEIO(SyncToAsyncAdapter(backend))


# ========================================================================
# Single-item access
# ========================================================================


class TestSingleItemAccess:
    @pytest.mark.anyio
    async def test_await_single_row(self, db, backend):
        """await db[0] → Atoms."""
        result = await db[0]
        assert isinstance(result, ase.Atoms)
        assert result.calc.results["energy"] == 0.0

    @pytest.mark.anyio
    async def test_await_negative_index(self, db):
        """await db[-1] → last row as Atoms."""
        result = await db[-1]
        assert isinstance(result, ase.Atoms)
        assert result.calc.results["energy"] == -9.0

    @pytest.mark.anyio
    async def test_await_none_placeholder(self, backend):
        """await db[i] where row is None → None."""
        backend._rows[3] = None
        db = AsyncASEIO(SyncToAsyncAdapter(backend))
        result = await db[3]
        assert result is None


# ========================================================================
# Bulk read via views
# ========================================================================


class TestBulkRead:
    @pytest.mark.anyio
    async def test_await_slice(self, db):
        """await db[0:3] → list of Atoms."""
        result = await db[0:3].to_list()
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(r, ase.Atoms) for r in result)
        assert result[0].calc.results["energy"] == 0.0
        assert result[2].calc.results["energy"] == -2.0

    @pytest.mark.anyio
    async def test_await_list_indices(self, db):
        """await db[[0, 5, 9]] → list of Atoms."""
        result = await db[[0, 5, 9]].to_list()
        assert len(result) == 3
        assert result[1].calc.results["energy"] == -5.0


# ========================================================================
# Length
# ========================================================================


class TestLength:
    @pytest.mark.anyio
    async def test_len(self, db):
        n = await db.len()
        assert n == 10


# ========================================================================
# Write operations
# ========================================================================


class TestWriteOps:
    @pytest.mark.anyio
    async def test_extend(self, db, backend):
        new_atoms = [_make_atoms(100), _make_atoms(101)]
        result = await db.extend(new_atoms)
        assert len(backend._rows) == 12
        assert result == 12

    @pytest.mark.anyio
    async def test_set_single(self, db, backend):
        """await db[0].set(row)."""
        new_row = _make_row(99)
        await db[0].set(new_row)
        assert backend._rows[0]["calc.energy"] == -99.0

    @pytest.mark.anyio
    async def test_set_slice(self, db, backend):
        """await db[0:3].set([row, row, row])."""
        new_rows = [_make_row(90 + i) for i in range(3)]
        await db[0:3].set(new_rows)
        assert backend._rows[0]["calc.energy"] == -90.0
        assert backend._rows[2]["calc.energy"] == -92.0

    @pytest.mark.anyio
    async def test_insert(self, db, backend):
        import ase

        atoms = ase.Atoms("H2", positions=[[0, 0, 0], [0, 0, 0.74]])
        atoms.calc = ase.calculators.singlepoint.SinglePointCalculator(
            atoms,
            energy=-55.0,
        )
        await db.insert(0, atoms)
        assert len(backend._rows) == 11
        assert backend._rows[0]["calc.energy"] == -55.0

    @pytest.mark.anyio
    async def test_delete_single(self, db, backend):
        """await db[0].delete()."""
        await db[0].delete()
        assert len(backend._rows) == 9

    @pytest.mark.anyio
    async def test_delete_contiguous_slice(self, db, backend):
        """await db[0:3].delete()."""
        await db[0:3].delete()
        assert len(backend._rows) == 7

    @pytest.mark.anyio
    async def test_delete_non_contiguous_raises(self, db):
        """await db[[2, 5, 8]].delete() → TypeError."""
        with pytest.raises(TypeError, match="contiguous"):
            await db[[2, 5, 8]].delete()

    @pytest.mark.anyio
    async def test_set_none_empties_slots(self, db, backend):
        """await db[[2, 5, 8]].set([None]*3) — empties without shifting."""
        await db[[2, 5, 8]].set([None] * 3)
        assert backend._rows[2] is None
        assert backend._rows[5] is None
        assert backend._rows[8] is None
        assert len(backend._rows) == 10  # no shifting


# ========================================================================
# Partial update
# ========================================================================


class TestUpdate:
    @pytest.mark.anyio
    async def test_update_single(self, db, backend):
        await db[0].update({"calc.energy": -10.5})
        assert backend._rows[0]["calc.energy"] == -10.5
        assert backend._rows[0]["info.tag"] == "mol_0"  # untouched


# ========================================================================
# Drop keys
# ========================================================================


class TestDrop:
    @pytest.mark.anyio
    async def test_drop_all_rows(self, db, backend):
        """await db.drop(keys=["calc.energy"])."""
        await db.drop(keys=["calc.energy"])
        for row in backend._rows:
            if row is not None:
                assert "calc.energy" not in row

    @pytest.mark.anyio
    async def test_drop_slice(self, db, backend):
        """await db[5:10].drop(keys=["calc.energy"])."""
        await db[5:10].drop(keys=["calc.energy"])
        # Rows 0-4 untouched
        assert "calc.energy" in backend._rows[0]
        # Rows 5-9 have key removed
        assert "calc.energy" not in backend._rows[5]
        assert "calc.energy" not in backend._rows[9]

    @pytest.mark.anyio
    async def test_drop_multi_keys(self, db, backend):
        """await db.drop(keys=["calc.energy", "calc.forces"])."""
        await db.drop(keys=["calc.energy", "calc.forces"])
        for row in backend._rows:
            if row is not None:
                assert "calc.energy" not in row
                assert "calc.forces" not in row


# ========================================================================
# Column access
# ========================================================================


class TestColumnAccess:
    @pytest.mark.anyio
    async def test_await_column(self, db):
        """await db["calc.energy"] → list of Atoms."""
        result = await db["calc.energy"].to_list()
        assert isinstance(result, list)
        assert len(result) == 10
        assert all(isinstance(r, ase.Atoms) for r in result)
        assert result[0].calc.results["energy"] == 0.0
        assert result[9].calc.results["energy"] == -9.0

    @pytest.mark.anyio
    async def test_await_column_slice(self, db):
        """await db["calc.energy"][0:3] → list of 3 Atoms."""
        result = await db["calc.energy"][0:3].to_list()
        assert len(result) == 3
        assert all(isinstance(r, ase.Atoms) for r in result)
        energies = [r.calc.results["energy"] for r in result]
        assert energies == [0.0, -1.0, -2.0]

    @pytest.mark.anyio
    async def test_await_multi_column(self, db):
        """await db[["calc.energy", "info.tag"]] → list of Atoms."""
        result = await db[["calc.energy", "info.tag"]].to_list()
        assert len(result) == 10
        assert all(isinstance(r, ase.Atoms) for r in result)
        assert result[0].calc.results["energy"] == 0.0
        assert result[0].info["tag"] == "mol_0"

    @pytest.mark.anyio
    async def test_column_to_dict_raises(self, db):
        """await db["calc.energy"].to_dict() raises TypeError."""
        with pytest.raises(TypeError, match="to_dict.*not available"):
            await db["calc.energy"].to_dict()


# ========================================================================
# None / placeholder entries
# ========================================================================


class TestPlaceholders:
    @pytest.mark.anyio
    async def test_reserve_none_placeholders(self, db, backend):
        """reserve() adds None placeholders (extend requires ase.Atoms)."""
        await db.reserve(3)
        assert len(backend._rows) == 13
        assert backend._rows[10] is None

    @pytest.mark.anyio
    async def test_insert_none(self, db, backend):
        await db.insert(0, None)
        assert backend._rows[0] is None
        assert len(backend._rows) == 11

    @pytest.mark.anyio
    async def test_set_none_single(self, db, backend):
        await db[0].set(None)
        assert backend._rows[0] is None

    @pytest.mark.anyio
    async def test_read_none_returns_none(self, backend):
        backend._rows[0] = None
        db = AsyncASEIO(SyncToAsyncAdapter(backend))
        result = await db[0]
        assert result is None

    @pytest.mark.anyio
    async def test_read_slice_with_nones(self, backend):
        backend._rows[0] = None
        backend._rows[2] = None
        db = AsyncASEIO(SyncToAsyncAdapter(backend))
        result = await db[0:3].to_list()
        assert result[0] is None
        assert result[1] is not None
        assert result[2] is None


# ========================================================================
# Async iteration
# ========================================================================


class TestAsyncIteration:
    @pytest.mark.anyio
    async def test_aiter_full(self, db):
        """async for row in db."""
        results = []
        async for row in db:
            results.append(row)
        assert len(results) == 10

    @pytest.mark.anyio
    async def test_aiter_slice(self, db):
        """async for row in db[2:5]."""
        results = []
        async for row in db[2:5]:
            results.append(row)
        assert len(results) == 3
        assert isinstance(results[0], ase.Atoms)
        assert results[0].calc.results["energy"] == -2.0

    @pytest.mark.anyio
    async def test_aiter_column(self, db):
        """async for val in db["calc.energy"][0:3] → Atoms."""
        results = []
        async for val in db["calc.energy"][0:3]:
            results.append(val)
        assert len(results) == 3
        assert all(isinstance(r, ase.Atoms) for r in results)
        energies = [r.calc.results["energy"] for r in results]
        assert energies == [0.0, -1.0, -2.0]

    @pytest.mark.anyio
    async def test_aiter_multi_column(self, db):
        """async for row in db[["calc.energy", "info.tag"]] → Atoms."""
        results = []
        async for row in db[["calc.energy", "info.tag"]]:
            results.append(row)
        assert len(results) == 10
        assert all(isinstance(r, ase.Atoms) for r in results)
        assert results[0].calc.results["energy"] == 0.0
        assert results[0].info["tag"] == "mol_0"


# ========================================================================
# Chunked async iteration
# ========================================================================


class TestChunkedIteration:
    @pytest.mark.anyio
    async def test_chunked(self, db):
        """async for row in db[0:10].chunked(3)."""
        results = []
        async for row in db[0:10].chunked(3):
            results.append(row)
        assert len(results) == 10  # yields individual items


# ========================================================================
# Context manager
# ========================================================================


class TestContextManager:
    @pytest.mark.anyio
    async def test_async_context_manager(self, backend):
        async with AsyncASEIO(SyncToAsyncAdapter(backend)) as db:
            result = await db[0]
            assert result is not None


# ========================================================================
# Clear / Remove / Reserve
# ========================================================================


class TestLifecycle:
    @pytest.mark.anyio
    async def test_clear(self, db, backend):
        await db.clear()
        assert len(backend._rows) == 0

    @pytest.mark.anyio
    async def test_reserve(self, db, backend):
        await db.reserve(5)
        assert len(backend._rows) == 15
        assert backend._rows[10] is None

    @pytest.mark.anyio
    async def test_remove(self, db):
        """remove delegates to backend; default raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await db.remove()


# ========================================================================
# View keys
# ========================================================================


class TestKeys:
    @pytest.mark.anyio
    async def test_keys_single_row(self, db):
        keys = await db[0].keys()
        assert "calc.energy" in keys
        assert "info.tag" in keys

    @pytest.mark.anyio
    async def test_keys_returns_per_row_keys(self, db):
        """keys() returns keys for that specific row, not global schema."""
        keys = await db[0].keys()
        assert "calc.energy" in keys
        assert "arrays.positions" in keys

    @pytest.mark.anyio
    async def test_keys_none_placeholder(self, backend):
        """keys() on a None placeholder returns empty list."""
        backend._rows[0] = None
        db = AsyncASEIO(SyncToAsyncAdapter(backend))
        keys = await db[0].keys()
        assert keys == []


# ========================================================================
# Async iteration with None placeholders
# ========================================================================


class TestAsyncIterationWithNone:
    @pytest.mark.anyio
    async def test_aiter_with_mixed_none(self, backend):
        """Async iteration preserves None placeholders."""
        backend._rows[1] = None
        backend._rows[3] = None
        db = AsyncASEIO(SyncToAsyncAdapter(backend))
        results = []
        async for item in db:
            results.append(item)
        assert len(results) == 10
        assert results[1] is None
        assert results[3] is None
        assert results[0] is not None
