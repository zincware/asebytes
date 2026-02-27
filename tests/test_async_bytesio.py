"""Integration tests for AsyncBytesIO facade.

Covers all bytes-level operations from async-api.py using an in-memory
RawWritableBackend wrapped via SyncToAsyncRawAdapter.
"""

from __future__ import annotations

import pytest

from asebytes._async_bytesio import AsyncBytesIO
from asebytes._async_protocols import SyncToAsyncRawAdapter
from asebytes._protocols import RawWritableBackend


# ── In-memory RawWritableBackend ──────────────────────────────────────


class MemoryRawBackend(RawWritableBackend):
    """Minimal in-memory raw bytes backend for integration testing."""

    def __init__(self):
        self._rows: list[dict[bytes, bytes] | None] = []
        self._schema: set[bytes] = set()

    def __len__(self) -> int:
        return len(self._rows)

    def schema(self) -> list[bytes]:
        return sorted(self._schema)

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

    def extend(self, data: list[dict[bytes, bytes] | None]) -> None:
        for d in data:
            if d is not None:
                self._schema |= set(d.keys())
        self._rows.extend(data)


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
        b.append_rows([_make_raw_row(i)])
    return b


@pytest.fixture
def io(raw_backend):
    """AsyncBytesIO wrapping a sync MemoryRawBackend."""
    return AsyncBytesIO(SyncToAsyncRawAdapter(raw_backend))


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
        io = AsyncBytesIO(SyncToAsyncRawAdapter(raw_backend))
        result = await io[3]
        assert result is None


# ========================================================================
# Bulk read
# ========================================================================


class TestBulkRead:
    @pytest.mark.anyio
    async def test_await_slice(self, io):
        result = await io[0:3]
        assert isinstance(result, list)
        assert len(result) == 3

    @pytest.mark.anyio
    async def test_await_list_indices(self, io):
        result = await io[[0, 5, 9]]
        assert len(result) == 3


# ========================================================================
# Length
# ========================================================================


class TestLength:
    @pytest.mark.anyio
    async def test_alen(self, io):
        n = await io.alen()
        assert n == 10


# ========================================================================
# Write operations
# ========================================================================


class TestWriteOps:
    @pytest.mark.anyio
    async def test_aextend(self, io, raw_backend):
        await io.aextend([_make_raw_row(100), _make_raw_row(101)])
        assert len(raw_backend._rows) == 12

    @pytest.mark.anyio
    async def test_aset_single(self, io, raw_backend):
        new = _make_raw_row(99)
        await io[0].aset(new)
        assert raw_backend._rows[0][b"calc.energy"] == bytes([99])

    @pytest.mark.anyio
    async def test_aset_slice(self, io, raw_backend):
        new_rows = [_make_raw_row(90 + i) for i in range(3)]
        await io[0:3].aset(new_rows)
        assert raw_backend._rows[0][b"calc.energy"] == bytes([90])

    @pytest.mark.anyio
    async def test_ainsert(self, io, raw_backend):
        await io.ainsert(0, _make_raw_row(55))
        assert len(raw_backend._rows) == 11

    @pytest.mark.anyio
    async def test_adelete_single(self, io, raw_backend):
        await io[0].adelete()
        assert len(raw_backend._rows) == 9

    @pytest.mark.anyio
    async def test_adelete_contiguous(self, io, raw_backend):
        await io[0:3].adelete()
        assert len(raw_backend._rows) == 7

    @pytest.mark.anyio
    async def test_adelete_non_contiguous_raises(self, io):
        with pytest.raises(TypeError, match="contiguous"):
            await io[[2, 5, 8]].adelete()

    @pytest.mark.anyio
    async def test_aset_none_empties_slots(self, io, raw_backend):
        await io[[2, 5, 8]].aset([None] * 3)
        assert raw_backend._rows[2] is None
        assert raw_backend._rows[5] is None
        assert raw_backend._rows[8] is None
        assert len(raw_backend._rows) == 10


# ========================================================================
# Partial update
# ========================================================================


class TestUpdate:
    @pytest.mark.anyio
    async def test_aupdate_single(self, io, raw_backend):
        await io[0].aupdate({b"calc.energy": b"\x99"})
        assert raw_backend._rows[0][b"calc.energy"] == b"\x99"
        assert raw_backend._rows[0][b"info.tag"] == b"mol_0"  # untouched


# ========================================================================
# Drop keys
# ========================================================================


class TestDrop:
    @pytest.mark.anyio
    async def test_adrop_all_rows(self, io, raw_backend):
        await io.adrop(keys=[b"calc.energy"])
        for row in raw_backend._rows:
            if row is not None:
                assert b"calc.energy" not in row

    @pytest.mark.anyio
    async def test_adrop_slice(self, io, raw_backend):
        await io[5:10].adrop(keys=[b"calc.energy"])
        assert b"calc.energy" in raw_backend._rows[0]
        assert b"calc.energy" not in raw_backend._rows[5]


# ========================================================================
# Schema inspection
# ========================================================================


class TestSchema:
    @pytest.mark.anyio
    async def test_get_schema(self, io):
        schema = await io.aget_schema()
        assert b"calc.energy" in schema

    @pytest.mark.anyio
    async def test_akeys_single_row(self, io):
        keys = await io[0].akeys()
        assert b"calc.energy" in keys


# ========================================================================
# None / placeholder entries
# ========================================================================


class TestPlaceholders:
    @pytest.mark.anyio
    async def test_extend_none(self, io, raw_backend):
        await io.aextend([None, None, None])
        assert len(raw_backend._rows) == 13
        assert raw_backend._rows[10] is None

    @pytest.mark.anyio
    async def test_insert_none(self, io, raw_backend):
        await io.ainsert(0, None)
        assert raw_backend._rows[0] is None

    @pytest.mark.anyio
    async def test_set_none(self, io, raw_backend):
        await io[0].aset(None)
        assert raw_backend._rows[0] is None

    @pytest.mark.anyio
    async def test_read_none_returns_none(self, raw_backend):
        raw_backend._rows[0] = None
        io = AsyncBytesIO(SyncToAsyncRawAdapter(raw_backend))
        result = await io[0]
        assert result is None


# ========================================================================
# Async iteration
# ========================================================================


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


# ========================================================================
# Context manager
# ========================================================================


class TestContextManager:
    @pytest.mark.anyio
    async def test_async_context_manager(self, raw_backend):
        async with AsyncBytesIO(SyncToAsyncRawAdapter(raw_backend)) as io:
            result = await io[0]
            assert result is not None


# ========================================================================
# Clear / Remove / Reserve
# ========================================================================


class TestLifecycle:
    @pytest.mark.anyio
    async def test_aclear(self, io, raw_backend):
        await io.aclear()
        assert len(raw_backend._rows) == 0

    @pytest.mark.anyio
    async def test_areserve(self, io, raw_backend):
        await io.areserve(5)
        assert len(raw_backend._rows) == 15

    @pytest.mark.anyio
    async def test_aremove(self, io):
        with pytest.raises(NotImplementedError):
            await io.aremove()
