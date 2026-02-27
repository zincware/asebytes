"""Integration tests for AsyncASEIO facade.

Covers all operations from async-api.py using an in-memory WritableBackend
wrapped via SyncToAsyncAdapter. No MongoDB — tests the full async stack
with a sync backend underneath.
"""

from __future__ import annotations

from typing import Any

import pytest

from asebytes._async_io import AsyncASEIO
from asebytes._async_protocols import SyncToAsyncAdapter
from asebytes._protocols import WritableBackend


# ── In-memory WritableBackend ─────────────────────────────────────────


class MemoryBackend(WritableBackend):
    """Minimal in-memory backend for integration testing."""

    def __init__(self):
        self._rows: list[dict[str, Any] | None] = []

    def __len__(self) -> int:
        return len(self._rows)

    def schema(self) -> list[str]:
        if not self._rows:
            return []
        row = self._rows[0]
        return sorted(row.keys()) if row is not None else []

    def get(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any] | None:
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

    def extend(self, data: list[dict[str, Any] | None]) -> None:
        self._rows.extend(data)


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


@pytest.fixture
def backend():
    b = MemoryBackend()
    for i in range(10):
        b.append_rows([_make_row(i)])
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
        """await db[0] → dict (or Atoms if convert enabled)."""
        result = await db[0]
        assert isinstance(result, dict)
        assert result["calc.energy"] == 0.0

    @pytest.mark.anyio
    async def test_await_negative_index(self, db):
        """await db[-1] → last row."""
        result = await db[-1]
        assert result["calc.energy"] == -9.0

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
        """await db[0:3] → list."""
        result = await db[0:3]
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0]["calc.energy"] == 0.0
        assert result[2]["calc.energy"] == -2.0

    @pytest.mark.anyio
    async def test_await_list_indices(self, db):
        """await db[[0, 5, 9]] → list."""
        result = await db[[0, 5, 9]]
        assert len(result) == 3
        assert result[1]["calc.energy"] == -5.0


# ========================================================================
# Length
# ========================================================================


class TestLength:
    @pytest.mark.anyio
    async def test_alen(self, db):
        n = await db.alen()
        assert n == 10


# ========================================================================
# Write operations
# ========================================================================


class TestWriteOps:
    @pytest.mark.anyio
    async def test_aextend(self, db, backend):
        new_rows = [_make_row(100), _make_row(101)]
        await db.aextend(new_rows)
        assert len(backend._rows) == 12

    @pytest.mark.anyio
    async def test_aset_single(self, db, backend):
        """await db[0].aset(row)."""
        new_row = _make_row(99)
        await db[0].aset(new_row)
        assert backend._rows[0]["calc.energy"] == -99.0

    @pytest.mark.anyio
    async def test_aset_slice(self, db, backend):
        """await db[0:3].aset([row, row, row])."""
        new_rows = [_make_row(90 + i) for i in range(3)]
        await db[0:3].aset(new_rows)
        assert backend._rows[0]["calc.energy"] == -90.0
        assert backend._rows[2]["calc.energy"] == -92.0

    @pytest.mark.anyio
    async def test_ainsert(self, db, backend):
        new_row = _make_row(55)
        await db.ainsert(0, new_row)
        assert len(backend._rows) == 11
        assert backend._rows[0]["calc.energy"] == -55.0

    @pytest.mark.anyio
    async def test_adelete_single(self, db, backend):
        """await db[0].adelete()."""
        await db[0].adelete()
        assert len(backend._rows) == 9

    @pytest.mark.anyio
    async def test_adelete_contiguous_slice(self, db, backend):
        """await db[0:3].adelete()."""
        await db[0:3].adelete()
        assert len(backend._rows) == 7

    @pytest.mark.anyio
    async def test_adelete_non_contiguous_raises(self, db):
        """await db[[2, 5, 8]].adelete() → TypeError."""
        with pytest.raises(TypeError, match="contiguous"):
            await db[[2, 5, 8]].adelete()

    @pytest.mark.anyio
    async def test_aset_none_empties_slots(self, db, backend):
        """await db[[2, 5, 8]].aset([None]*3) — empties without shifting."""
        await db[[2, 5, 8]].aset([None] * 3)
        assert backend._rows[2] is None
        assert backend._rows[5] is None
        assert backend._rows[8] is None
        assert len(backend._rows) == 10  # no shifting


# ========================================================================
# Partial update
# ========================================================================


class TestUpdate:
    @pytest.mark.anyio
    async def test_aupdate_single(self, db, backend):
        await db[0].aupdate({"calc.energy": -10.5})
        assert backend._rows[0]["calc.energy"] == -10.5
        assert backend._rows[0]["info.tag"] == "mol_0"  # untouched


# ========================================================================
# Drop keys
# ========================================================================


class TestDrop:
    @pytest.mark.anyio
    async def test_adrop_all_rows(self, db, backend):
        """await db.adrop(keys=["calc.energy"])."""
        await db.adrop(keys=["calc.energy"])
        for row in backend._rows:
            if row is not None:
                assert "calc.energy" not in row

    @pytest.mark.anyio
    async def test_adrop_slice(self, db, backend):
        """await db[5:10].adrop(keys=["calc.energy"])."""
        await db[5:10].adrop(keys=["calc.energy"])
        # Rows 0-4 untouched
        assert "calc.energy" in backend._rows[0]
        # Rows 5-9 have key removed
        assert "calc.energy" not in backend._rows[5]
        assert "calc.energy" not in backend._rows[9]

    @pytest.mark.anyio
    async def test_adrop_multi_keys(self, db, backend):
        """await db.adrop(keys=["calc.energy", "calc.forces"])."""
        await db.adrop(keys=["calc.energy", "calc.forces"])
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
        """await db["calc.energy"] → list of values."""
        result = await db["calc.energy"]
        assert isinstance(result, list)
        assert len(result) == 10
        assert result[0] == 0.0
        assert result[9] == -9.0

    @pytest.mark.anyio
    async def test_await_column_slice(self, db):
        """await db["calc.energy"][0:3] → list of 3 values."""
        result = await db["calc.energy"][0:3]
        assert result == [0.0, -1.0, -2.0]

    @pytest.mark.anyio
    async def test_await_multi_column(self, db):
        """await db[["calc.energy", "info.tag"]] → list of dicts."""
        result = await db[["calc.energy", "info.tag"]]
        assert len(result) == 10
        assert result[0] == {"calc.energy": 0.0, "info.tag": "mol_0"}

    @pytest.mark.anyio
    async def test_column_to_dict(self, db):
        """await db["calc.energy"].to_dict()."""
        result = await db["calc.energy"].to_dict()
        assert "calc.energy" in result
        assert result["calc.energy"][0] == 0.0


# ========================================================================
# None / placeholder entries
# ========================================================================


class TestPlaceholders:
    @pytest.mark.anyio
    async def test_extend_none(self, db, backend):
        await db.aextend([None, None, None])
        assert len(backend._rows) == 13
        assert backend._rows[10] is None

    @pytest.mark.anyio
    async def test_insert_none(self, db, backend):
        await db.ainsert(0, None)
        assert backend._rows[0] is None
        assert len(backend._rows) == 11

    @pytest.mark.anyio
    async def test_set_none_single(self, db, backend):
        await db[0].aset(None)
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
        result = await db[0:3]
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
        assert results[0]["calc.energy"] == -2.0

    @pytest.mark.anyio
    async def test_aiter_column(self, db):
        """async for val in db["calc.energy"][0:3]."""
        results = []
        async for val in db["calc.energy"][0:3]:
            results.append(val)
        assert results == [0.0, -1.0, -2.0]

    @pytest.mark.anyio
    async def test_aiter_multi_column(self, db):
        """async for row in db[["calc.energy", "info.tag"]]."""
        results = []
        async for row in db[["calc.energy", "info.tag"]]:
            results.append(row)
        assert len(results) == 10
        assert results[0] == {"calc.energy": 0.0, "info.tag": "mol_0"}


# ========================================================================
# Chunked async iteration
# ========================================================================


class TestChunkedIteration:
    @pytest.mark.anyio
    async def test_achunked(self, db):
        """async for row in db[0:10].achunked(3)."""
        results = []
        async for row in db[0:10].achunked(3):
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
    async def test_aclear(self, db, backend):
        await db.aclear()
        assert len(backend._rows) == 0

    @pytest.mark.anyio
    async def test_areserve(self, db, backend):
        await db.areserve(5)
        assert len(backend._rows) == 15
        assert backend._rows[10] is None

    @pytest.mark.anyio
    async def test_aremove(self, db):
        """aremove delegates to backend; default raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await db.aremove()


# ========================================================================
# View akeys
# ========================================================================


class TestKeys:
    @pytest.mark.anyio
    async def test_akeys_single_row(self, db):
        keys = await db[0].akeys()
        assert "calc.energy" in keys
        assert "info.tag" in keys
