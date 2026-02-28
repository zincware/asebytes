"""Integration tests for AsyncObjectIO facade.

Covers all object-level operations from the async API using LMDB
backends (via string path auto-creation with SyncToAsyncAdapter).
Mirrors the test_async_blob_io.py structure for consistency.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from asebytes._async_object_io import AsyncObjectIO


# ── Helpers ──────────────────────────────────────────────────────────────


def _make_row(i: int) -> dict[str, Any]:
    """Create a sample object-level row for testing."""
    return {
        "energy": float(-i * 0.1),
        "forces": np.array([[i, i + 1, i + 2]], dtype=np.float64),
        "tag": f"mol_{i}",
    }


@pytest.fixture
def io(tmp_path):
    """AsyncObjectIO backed by a fresh LMDB file with 10 rows."""
    path = str(tmp_path / "test.lmdb")
    # Seed 10 rows via sync ObjectIO so we have data to test
    from asebytes._object_io import ObjectIO

    sync_io = ObjectIO(path)
    sync_io.extend([_make_row(i) for i in range(10)])
    # Now open async facade on the same path
    return AsyncObjectIO(path)


@pytest.fixture
def empty_io(tmp_path):
    """AsyncObjectIO backed by an empty LMDB file."""
    path = str(tmp_path / "empty.lmdb")
    return AsyncObjectIO(path)


# ========================================================================
# Single-item access
# ========================================================================


class TestSingleItemAccess:
    @pytest.mark.anyio
    async def test_await_single_row(self, io):
        """await io[0] returns dict[str, Any]."""
        result = await io[0]
        assert isinstance(result, dict)
        assert "energy" in result
        assert result["tag"] == "mol_0"

    @pytest.mark.anyio
    async def test_await_negative_index(self, io):
        """await io[-1] returns the last row."""
        result = await io[-1]
        assert result["tag"] == "mol_9"

    @pytest.mark.anyio
    async def test_await_returns_correct_types(self, io):
        """Values maintain their types through round-trip."""
        result = await io[0]
        assert isinstance(result["energy"], float)
        assert isinstance(result["tag"], str)
        assert isinstance(result["forces"], np.ndarray)

    @pytest.mark.anyio
    async def test_await_none_placeholder(self, tmp_path):
        """await io[i] where row is a None placeholder returns None."""
        path = str(tmp_path / "none.lmdb")
        io = AsyncObjectIO(path)
        await io.extend([None])
        result = await io[0]
        assert result is None


# ========================================================================
# get() method
# ========================================================================


class TestGet:
    @pytest.mark.anyio
    async def test_get_full_row(self, io):
        """get(index) returns the full dict."""
        result = await io.get(0)
        assert isinstance(result, dict)
        assert "energy" in result
        assert "forces" in result
        assert "tag" in result

    @pytest.mark.anyio
    async def test_get_with_key_filter(self, io):
        """get(index, keys=[...]) returns only requested keys."""
        result = await io.get(0, keys=["energy", "tag"])
        assert "energy" in result
        assert "tag" in result
        assert "forces" not in result

    @pytest.mark.anyio
    async def test_get_single_key(self, io):
        """get(index, keys=[single]) returns dict with one key."""
        result = await io.get(0, keys=["energy"])
        assert list(result.keys()) == ["energy"]

    @pytest.mark.anyio
    async def test_get_values_correct(self, io):
        """Values from get() match the inserted data."""
        result = await io.get(3)
        assert result["tag"] == "mol_3"
        assert result["energy"] == pytest.approx(-0.3)


# ========================================================================
# Bulk read (slice / list of indices)
# ========================================================================


class TestBulkRead:
    @pytest.mark.anyio
    async def test_await_slice(self, io):
        """io[0:3].to_list() returns 3 rows."""
        result = await io[0:3].to_list()
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0]["tag"] == "mol_0"
        assert result[2]["tag"] == "mol_2"

    @pytest.mark.anyio
    async def test_await_list_indices(self, io):
        """io[[0, 5, 9]].to_list() returns rows at those indices."""
        result = await io[[0, 5, 9]].to_list()
        assert len(result) == 3
        assert result[0]["tag"] == "mol_0"
        assert result[1]["tag"] == "mol_5"
        assert result[2]["tag"] == "mol_9"

    @pytest.mark.anyio
    async def test_empty_list_indices(self, io):
        """io[[]].to_list() returns empty list."""
        result = await io[[]].to_list()
        assert result == []

    @pytest.mark.anyio
    async def test_slice_step(self, io):
        """io[0:6:2].to_list() returns every other row."""
        result = await io[0:6:2].to_list()
        assert len(result) == 3
        assert result[0]["tag"] == "mol_0"
        assert result[1]["tag"] == "mol_2"
        assert result[2]["tag"] == "mol_4"


# ========================================================================
# Length
# ========================================================================


class TestLength:
    @pytest.mark.anyio
    async def test_len(self, io):
        """await io.len() returns the number of rows."""
        n = await io.len()
        assert n == 10

    @pytest.mark.anyio
    async def test_len_empty(self, empty_io):
        """await io.len() returns 0 for empty database."""
        n = await empty_io.len()
        assert n == 0

    def test_sync_len_raises(self, io):
        """len(io) raises TypeError with helpful message."""
        with pytest.raises(TypeError, match="await"):
            len(io)


# ========================================================================
# Write operations
# ========================================================================


class TestWriteOps:
    @pytest.mark.anyio
    async def test_extend(self, io):
        """extend() appends rows."""
        await io.extend([_make_row(100), _make_row(101)])
        n = await io.len()
        assert n == 12

    @pytest.mark.anyio
    async def test_extend_empty(self, io):
        """extend([]) is a no-op."""
        await io.extend([])
        n = await io.len()
        assert n == 10

    @pytest.mark.anyio
    async def test_set_single(self, io):
        """io[0].set(data) overwrites the row."""
        new_row = _make_row(99)
        await io[0].set(new_row)
        result = await io.get(0)
        assert result["tag"] == "mol_99"

    @pytest.mark.anyio
    async def test_set_slice(self, io):
        """io[0:3].set(rows) overwrites a contiguous range."""
        new_rows = [_make_row(90 + i) for i in range(3)]
        await io[0:3].set(new_rows)
        result = await io.get(0)
        assert result["tag"] == "mol_90"
        result = await io.get(2)
        assert result["tag"] == "mol_92"

    @pytest.mark.anyio
    async def test_insert(self, io):
        """insert(0, data) inserts at the beginning."""
        await io.insert(0, _make_row(55))
        n = await io.len()
        assert n == 11
        result = await io.get(0)
        assert result["tag"] == "mol_55"

    @pytest.mark.anyio
    async def test_insert_at_end(self, io):
        """insert(len, data) appends to the end."""
        n_before = await io.len()
        await io.insert(n_before, _make_row(77))
        n_after = await io.len()
        assert n_after == n_before + 1

    @pytest.mark.anyio
    async def test_delete_single(self, io):
        """io[0].delete() removes one row."""
        await io[0].delete()
        n = await io.len()
        assert n == 9

    @pytest.mark.anyio
    async def test_delete_contiguous(self, io):
        """io[0:3].delete() removes a contiguous range."""
        await io[0:3].delete()
        n = await io.len()
        assert n == 7

    @pytest.mark.anyio
    async def test_delete_non_contiguous_raises(self, io):
        """io[[2, 5, 8]].delete() raises TypeError."""
        with pytest.raises(TypeError, match="contiguous"):
            await io[[2, 5, 8]].delete()

    @pytest.mark.anyio
    async def test_set_none_empties_slots(self, io):
        """io[[2, 5, 8]].set([None]*3) empties slots without shifting."""
        await io[[2, 5, 8]].set([None, None, None])
        n = await io.len()
        assert n == 10  # count unchanged
        assert await io[2] is None
        assert await io[5] is None
        assert await io[8] is None
        # Untouched rows remain
        assert (await io[0])["tag"] == "mol_0"


# ========================================================================
# Partial update
# ========================================================================


class TestUpdate:
    @pytest.mark.anyio
    async def test_update_single_via_method(self, io):
        """update(index, data) merges into existing row."""
        await io.update(0, {"energy": -999.0})
        result = await io.get(0)
        assert result["energy"] == pytest.approx(-999.0)
        assert result["tag"] == "mol_0"  # untouched

    @pytest.mark.anyio
    async def test_update_single_via_view(self, io):
        """io[0].update(data) merges into existing row."""
        await io[0].update({"tag": "updated"})
        result = await io.get(0)
        assert result["tag"] == "updated"
        assert result["energy"] == pytest.approx(0.0)  # untouched

    @pytest.mark.anyio
    async def test_update_adds_new_key(self, io):
        """update() can add keys not present in original row."""
        await io.update(0, {"new_key": 42})
        result = await io.get(0)
        assert result["new_key"] == 42


# ========================================================================
# Drop keys
# ========================================================================


class TestDrop:
    @pytest.mark.anyio
    async def test_drop_all_rows(self, io):
        """drop(keys=[...]) removes the key from every row."""
        await io.drop(keys=["energy"])
        for i in range(10):
            row = await io.get(i)
            if row is not None:
                assert "energy" not in row
                assert "tag" in row  # other keys remain

    @pytest.mark.anyio
    async def test_drop_slice(self, io):
        """io[5:10].drop(keys=[...]) only affects the slice."""
        await io[5:10].drop(keys=["energy"])
        # Row 0 still has energy
        row0 = await io.get(0)
        assert "energy" in row0
        # Row 5 does not
        row5 = await io.get(5)
        assert "energy" not in row5


# ========================================================================
# Keys inspection
# ========================================================================


class TestKeys:
    @pytest.mark.anyio
    async def test_keys_via_method(self, io):
        """keys(index) returns key names as strings."""
        key_list = await io.keys(0)
        assert "energy" in key_list
        assert "forces" in key_list
        assert "tag" in key_list

    @pytest.mark.anyio
    async def test_keys_via_view(self, io):
        """io[0].keys() returns key names."""
        key_list = await io[0].keys()
        assert "energy" in key_list

    @pytest.mark.anyio
    async def test_keys_returns_strings(self, io):
        """All keys are strings (not bytes)."""
        key_list = await io.keys(0)
        for k in key_list:
            assert isinstance(k, str)


# ========================================================================
# None / placeholder entries
# ========================================================================


class TestPlaceholders:
    @pytest.mark.anyio
    async def test_extend_none(self, io):
        """extend([None, None, None]) adds placeholder rows."""
        await io.extend([None, None, None])
        n = await io.len()
        assert n == 13
        assert await io[10] is None

    @pytest.mark.anyio
    async def test_insert_none(self, io):
        """insert(0, None) inserts a placeholder at the start."""
        await io.insert(0, None)
        assert await io[0] is None

    @pytest.mark.anyio
    async def test_set_none(self, io):
        """io[0].set(None) replaces with placeholder."""
        await io[0].set(None)
        assert await io[0] is None

    @pytest.mark.anyio
    async def test_read_none_returns_none(self, tmp_path):
        """Reading a placeholder row returns None."""
        path = str(tmp_path / "ph.lmdb")
        io = AsyncObjectIO(path)
        await io.extend([None, _make_row(1)])
        assert await io[0] is None
        assert (await io[1])["tag"] == "mol_1"


# ========================================================================
# Column access via views
# ========================================================================


class TestColumnAccess:
    @pytest.mark.anyio
    async def test_column_access_via_row_view(self, io):
        """io[[0, 1, 2]]["energy"].to_list() returns column values."""
        view = io[[0, 1, 2]]
        col_view = view["energy"]
        values = await col_view.to_list()
        assert len(values) == 3
        assert values[0] == pytest.approx(0.0)
        assert values[1] == pytest.approx(-0.1)
        assert values[2] == pytest.approx(-0.2)

    @pytest.mark.anyio
    async def test_string_index_returns_column_view(self, io):
        """io["energy"] returns an AsyncColumnView."""
        col_view = io["energy"]
        values = await col_view.to_list()
        assert len(values) == 10

    @pytest.mark.anyio
    async def test_list_string_index_returns_column_view(self, io):
        """io[["energy", "tag"]] returns multi-key AsyncColumnView."""
        col_view = io[["energy", "tag"]]
        values = await col_view.to_list()
        assert len(values) == 10
        # Each item is [energy_val, tag_val]
        assert len(values[0]) == 2


# ========================================================================
# Async iteration
# ========================================================================


class TestAsyncIteration:
    @pytest.mark.anyio
    async def test_aiter_full(self, io):
        """async for row in io yields all rows."""
        results = []
        async for row in io:
            results.append(row)
        assert len(results) == 10
        assert results[0]["tag"] == "mol_0"
        assert results[9]["tag"] == "mol_9"

    @pytest.mark.anyio
    async def test_aiter_slice(self, io):
        """async for row in io[2:5] yields 3 rows."""
        results = []
        async for row in io[2:5]:
            results.append(row)
        assert len(results) == 3
        assert results[0]["tag"] == "mol_2"

    @pytest.mark.anyio
    async def test_aiter_with_mixed_none(self, tmp_path):
        """async for handles None placeholders inline."""
        path = str(tmp_path / "mixed.lmdb")
        io = AsyncObjectIO(path)
        await io.extend([_make_row(0), None, _make_row(2)])
        results = []
        async for item in io:
            results.append(item)
        assert results[0] is not None
        assert results[1] is None
        assert results[2] is not None
        assert results[2]["tag"] == "mol_2"

    @pytest.mark.anyio
    async def test_aiter_list_indices(self, io):
        """async for row in io[[0, 5, 9]] yields specific rows."""
        results = []
        async for row in io[[0, 5, 9]]:
            results.append(row)
        assert len(results) == 3
        assert results[1]["tag"] == "mol_5"


# ========================================================================
# Context manager
# ========================================================================


class TestContextManager:
    @pytest.mark.anyio
    async def test_async_context_manager(self, tmp_path):
        """async with AsyncObjectIO(...) as io: works."""
        path = str(tmp_path / "ctx.lmdb")
        async with AsyncObjectIO(path) as io:
            await io.extend([_make_row(0)])
            result = await io[0]
            assert result["tag"] == "mol_0"


# ========================================================================
# Clear / Remove / Reserve
# ========================================================================


class TestLifecycle:
    @pytest.mark.anyio
    async def test_clear(self, io):
        """clear() removes all rows."""
        await io.clear()
        n = await io.len()
        assert n == 0

    @pytest.mark.anyio
    async def test_reserve(self, io):
        """reserve(5) adds 5 placeholder rows."""
        await io.reserve(5)
        n = await io.len()
        assert n == 15
        # Reserved rows are None
        assert await io[10] is None

    @pytest.mark.anyio
    async def test_remove(self, io):
        """remove() raises NotImplementedError (LMDB doesn't support it)."""
        with pytest.raises(NotImplementedError):
            await io.remove()


# ========================================================================
# String path auto-creation
# ========================================================================


class TestStringPathCreation:
    @pytest.mark.anyio
    async def test_create_from_string_path(self, tmp_path):
        """AsyncObjectIO(str_path) auto-creates LMDB backend."""
        path = str(tmp_path / "auto.lmdb")
        io = AsyncObjectIO(path)
        n = await io.len()
        assert n == 0
        await io.extend([_make_row(0)])
        n = await io.len()
        assert n == 1

    @pytest.mark.anyio
    async def test_data_persists_across_instances(self, tmp_path):
        """Data written via one instance is readable from another."""
        path = str(tmp_path / "persist.lmdb")
        io1 = AsyncObjectIO(path)
        await io1.extend([_make_row(42)])

        io2 = AsyncObjectIO(path)
        n = await io2.len()
        assert n == 1
        result = await io2.get(0)
        assert result["tag"] == "mol_42"


# ========================================================================
# __repr__
# ========================================================================


class TestRepr:
    def test_repr(self, io):
        """repr(io) returns a meaningful string."""
        r = repr(io)
        assert "AsyncObjectIO" in r
        assert "backend=" in r
