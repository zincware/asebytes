"""Integration tests for AsyncBlobIO facade.

Covers all bytes-level operations from async-api.py using an in-memory
ReadWriteBackend wrapped via SyncToAsyncAdapter.
"""

from __future__ import annotations

import pytest

from asebytes._async_blob_io import AsyncBlobIO
from asebytes._async_backends import SyncToAsyncAdapter
from asebytes._backends import ReadWriteBackend


# ── In-memory ReadWriteBackend ────────────────────────────────────────


class MemoryRawBackend(ReadWriteBackend):
    """Minimal in-memory raw bytes backend for integration testing."""

    def __init__(self):
        self._rows: list[dict[bytes, bytes] | None] = []
        self._schema: set[bytes] = set()

    def __len__(self) -> int:
        return len(self._rows)

    def get(
        self, index: int, keys: list[bytes] | None = None
    ) -> dict[bytes, bytes] | None:
        if index < 0 or index >= len(self._rows):
            raise IndexError(index)
        row = self._rows[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    def set(self, index: int, data: dict[bytes, bytes] | None) -> None:
        if data is not None:
            self._schema |= set(data.keys())
        if index < len(self._rows):
            self._rows[index] = data
        elif index == len(self._rows):
            self._rows.append(data)
        else:
            raise IndexError(index)

    def insert(self, index: int, data: dict[bytes, bytes] | None) -> None:
        if data is not None:
            self._schema |= set(data.keys())
        self._rows.insert(index, data)

    def delete(self, index: int) -> None:
        del self._rows[index]

    def extend(self, data: list[dict[bytes, bytes] | None]) -> int:
        for d in data:
            if d is not None:
                self._schema |= set(d.keys())
        self._rows.extend(data)
        return len(self._rows)

    @staticmethod
    def list_groups(path: str, **kwargs) -> list[str]:
        return []


def _make_raw_row(i: int) -> dict[bytes, bytes]:
    return {
        b"calc.energy": bytes([i]),
        b"arrays.positions": bytes([i, i + 1]),
        b"info.tag": f"mol_{i}".encode(),
    }


@pytest.fixture
def raw_backend():
    b = MemoryRawBackend()
    for i in range(10):
        b.extend([_make_raw_row(i)])
    return b


@pytest.fixture
def io(raw_backend):
    """AsyncBlobIO wrapping a sync MemoryRawBackend."""
    return AsyncBlobIO(SyncToAsyncAdapter(raw_backend))


# ========================================================================
# Single-item access
# ========================================================================


class TestSingleItemAccess:
    @pytest.mark.anyio
    async def test_await_single_row(self, io, raw_backend):
        """await io[0] → dict[bytes, bytes]."""
        result = await io[0]
        assert isinstance(result, dict)
        assert b"calc.energy" in result

    @pytest.mark.anyio
    async def test_await_negative_index(self, io):
        """await io[-1] → last row."""
        result = await io[-1]
        assert result[b"info.tag"] == b"mol_9"

    @pytest.mark.anyio
    async def test_await_none_placeholder(self, raw_backend):
        """await io[i] where row is None → None."""
        raw_backend._rows[3] = None
        io = AsyncBlobIO(SyncToAsyncAdapter(raw_backend))
        result = await io[3]
        assert result is None


# ========================================================================
# Bulk read
# ========================================================================


class TestBulkRead:
    @pytest.mark.anyio
    async def test_await_slice(self, io):
        result = await io[0:3].to_list()
        assert isinstance(result, list)
        assert len(result) == 3

    @pytest.mark.anyio
    async def test_await_list_indices(self, io):
        result = await io[[0, 5, 9]].to_list()
        assert len(result) == 3


# ========================================================================
# Length
# ========================================================================


class TestLength:
    @pytest.mark.anyio
    async def test_len(self, io):
        n = await io.len()
        assert n == 10


# ========================================================================
# Write operations
# ========================================================================


class TestWriteOps:
    @pytest.mark.anyio
    async def test_extend(self, io, raw_backend):
        await io.extend([_make_raw_row(100), _make_raw_row(101)])
        assert len(raw_backend._rows) == 12

    @pytest.mark.anyio
    async def test_set_single(self, io, raw_backend):
        new = _make_raw_row(99)
        await io[0].set(new)
        assert raw_backend._rows[0][b"calc.energy"] == bytes([99])

    @pytest.mark.anyio
    async def test_set_slice(self, io, raw_backend):
        new_rows = [_make_raw_row(90 + i) for i in range(3)]
        await io[0:3].set(new_rows)
        assert raw_backend._rows[0][b"calc.energy"] == bytes([90])

    @pytest.mark.anyio
    async def test_insert(self, io, raw_backend):
        await io.insert(0, _make_raw_row(55))
        assert len(raw_backend._rows) == 11

    @pytest.mark.anyio
    async def test_delete_single(self, io, raw_backend):
        await io[0].delete()
        assert len(raw_backend._rows) == 9

    @pytest.mark.anyio
    async def test_delete_contiguous(self, io, raw_backend):
        await io[0:3].delete()
        assert len(raw_backend._rows) == 7

    @pytest.mark.anyio
    async def test_delete_non_contiguous_raises(self, io):
        with pytest.raises(TypeError, match="contiguous"):
            await io[[2, 5, 8]].delete()

    @pytest.mark.anyio
    async def test_set_none_empties_slots(self, io, raw_backend):
        await io[[2, 5, 8]].set([None] * 3)
        assert raw_backend._rows[2] is None
        assert raw_backend._rows[5] is None
        assert raw_backend._rows[8] is None
        assert len(raw_backend._rows) == 10


# ========================================================================
# Partial update
# ========================================================================


class TestUpdate:
    @pytest.mark.anyio
    async def test_update_single(self, io, raw_backend):
        await io[0].update({b"calc.energy": b"\x99"})
        assert raw_backend._rows[0][b"calc.energy"] == b"\x99"
        assert raw_backend._rows[0][b"info.tag"] == b"mol_0"  # untouched


# ========================================================================
# Drop keys
# ========================================================================


class TestDrop:
    @pytest.mark.anyio
    async def test_drop_all_rows(self, io, raw_backend):
        await io.drop(keys=[b"calc.energy"])
        for row in raw_backend._rows:
            if row is not None:
                assert b"calc.energy" not in row

    @pytest.mark.anyio
    async def test_drop_slice(self, io, raw_backend):
        await io[5:10].drop(keys=[b"calc.energy"])
        assert b"calc.energy" in raw_backend._rows[0]
        assert b"calc.energy" not in raw_backend._rows[5]


# ========================================================================
# Schema inspection
# ========================================================================


class TestSchema:
    @pytest.mark.anyio
    async def test_get_keys(self, io):
        keys = await io.keys(0)
        assert b"calc.energy" in keys

    @pytest.mark.anyio
    async def test_keys_single_row(self, io):
        keys = await io[0].keys()
        assert b"calc.energy" in keys


# ========================================================================
# None / placeholder entries
# ========================================================================


class TestPlaceholders:
    @pytest.mark.anyio
    async def test_extend_none(self, io, raw_backend):
        await io.extend([None, None, None])
        assert len(raw_backend._rows) == 13
        assert raw_backend._rows[10] is None

    @pytest.mark.anyio
    async def test_insert_none(self, io, raw_backend):
        await io.insert(0, None)
        assert raw_backend._rows[0] is None

    @pytest.mark.anyio
    async def test_set_none(self, io, raw_backend):
        await io[0].set(None)
        assert raw_backend._rows[0] is None

    @pytest.mark.anyio
    async def test_read_none_returns_none(self, raw_backend):
        raw_backend._rows[0] = None
        io = AsyncBlobIO(SyncToAsyncAdapter(raw_backend))
        result = await io[0]
        assert result is None


# ========================================================================
# Async iteration
# ========================================================================


class TestColumnAccessViaRowView:
    @pytest.mark.anyio
    async def test_column_access_via_row_view(self, io):
        view = io[[0, 1, 2]]  # concrete indices (slices defer resolution)
        col_view = view[b"calc.energy"]
        values = await col_view.to_list()
        assert len(values) == 3


class TestAsyncIteration:
    @pytest.mark.anyio
    async def test_aiter_full(self, io):
        results = []
        async for row in io:
            results.append(row)
        assert len(results) == 10

    @pytest.mark.anyio
    async def test_aiter_slice(self, io):
        results = []
        async for row in io[2:5]:
            results.append(row)
        assert len(results) == 3

    @pytest.mark.anyio
    async def test_aiter_with_mixed_none(self, raw_backend):
        raw_backend._rows[1] = None
        io = AsyncBlobIO(SyncToAsyncAdapter(raw_backend))
        results = []
        async for item in io:
            results.append(item)
        assert results[1] is None
        assert results[0] is not None


# ========================================================================
# Context manager
# ========================================================================


class TestContextManager:
    @pytest.mark.anyio
    async def test_async_context_manager(self, raw_backend):
        async with AsyncBlobIO(SyncToAsyncAdapter(raw_backend)) as io:
            result = await io[0]
            assert result is not None


# ========================================================================
# Clear / Remove / Reserve
# ========================================================================


class TestLifecycle:
    @pytest.mark.anyio
    async def test_clear(self, io, raw_backend):
        await io.clear()
        assert len(raw_backend._rows) == 0

    @pytest.mark.anyio
    async def test_reserve(self, io, raw_backend):
        await io.reserve(5)
        assert len(raw_backend._rows) == 15

    @pytest.mark.anyio
    async def test_remove(self, io):
        with pytest.raises(NotImplementedError):
            await io.remove()
