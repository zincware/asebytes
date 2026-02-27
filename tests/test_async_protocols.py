"""Tests for async protocol ABCs and SyncToAsyncAdapter.

Tests:
- AsyncRawReadableBackend / AsyncRawWritableBackend cannot be instantiated
- In-memory async implementations pass the same tests as sync
- SyncToAsyncRawAdapter wraps a sync RawWritableBackend and works correctly
- SyncToAsyncAdapter wraps a sync WritableBackend and works correctly
"""

from __future__ import annotations

from typing import Any

import pytest

from asebytes._async_protocols import (
    AsyncRawReadableBackend,
    AsyncRawWritableBackend,
    AsyncReadableBackend,
    AsyncWritableBackend,
    SyncToAsyncRawAdapter,
    SyncToAsyncAdapter,
)


# ── In-memory async implementations ────────────────────────────────────


class MemoryAsyncRawReadable(AsyncRawReadableBackend):
    def __init__(self, data: list[dict[bytes, bytes] | None] | None = None):
        self._data: list[dict[bytes, bytes] | None] = data or []

    async def alen(self) -> int:
        return len(self._data)

    async def aschema(self) -> list[bytes]:
        keys: set[bytes] = set()
        for row in self._data:
            if row is not None:
                keys.update(row.keys())
        return sorted(keys)

    async def aget(
        self, index: int, keys: list[bytes] | None = None
    ) -> dict[bytes, bytes] | None:
        if index < 0 or index >= len(self._data):
            raise IndexError(index)
        row = self._data[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)


class MemoryAsyncRawWritable(MemoryAsyncRawReadable, AsyncRawWritableBackend):
    async def aset(self, index: int, data: dict[bytes, bytes] | None) -> None:
        if index < len(self._data):
            self._data[index] = data
        elif index == len(self._data):
            self._data.append(data)
        else:
            raise IndexError(index)

    async def ainsert(self, index: int, data: dict[bytes, bytes] | None) -> None:
        self._data.insert(index, data)

    async def adelete(self, index: int) -> None:
        del self._data[index]

    async def aextend(self, data: list[dict[bytes, bytes] | None]) -> None:
        self._data.extend(data)


# ── Tests: cannot instantiate abstract classes ──────────────────────────


class TestAbstractInstantiation:
    def test_cannot_instantiate_async_raw_readable(self):
        with pytest.raises(TypeError):
            AsyncRawReadableBackend()

    def test_cannot_instantiate_async_raw_writable(self):
        with pytest.raises(TypeError):
            AsyncRawWritableBackend()

    def test_cannot_instantiate_async_readable(self):
        with pytest.raises(TypeError):
            AsyncReadableBackend()

    def test_cannot_instantiate_async_writable(self):
        with pytest.raises(TypeError):
            AsyncWritableBackend()


# ── Tests: AsyncRawReadableBackend ──────────────────────────────────────


class TestAsyncRawReadable:
    @pytest.mark.anyio
    async def test_alen(self):
        backend = MemoryAsyncRawReadable([{b"a": b"1"}, {b"b": b"2"}])
        assert await backend.alen() == 2

    @pytest.mark.anyio
    async def test_aget(self):
        backend = MemoryAsyncRawReadable([{b"a": b"1", b"b": b"2"}])
        assert await backend.aget(0) == {b"a": b"1", b"b": b"2"}

    @pytest.mark.anyio
    async def test_aget_with_keys(self):
        backend = MemoryAsyncRawReadable([{b"a": b"1", b"b": b"2"}])
        assert await backend.aget(0, keys=[b"a"]) == {b"a": b"1"}

    @pytest.mark.anyio
    async def test_aget_none(self):
        backend = MemoryAsyncRawReadable([None])
        assert await backend.aget(0) is None

    @pytest.mark.anyio
    async def test_aget_keys_from_row(self):
        backend = MemoryAsyncRawReadable([{b"a": b"1", b"b": b"2"}])
        row = await backend.aget(0)
        assert sorted(row.keys()) == [b"a", b"b"]

    @pytest.mark.anyio
    async def test_aget_keys_from_none_row(self):
        backend = MemoryAsyncRawReadable([None])
        row = await backend.aget(0)
        assert row is None

    @pytest.mark.anyio
    async def test_aget_many_default(self):
        backend = MemoryAsyncRawReadable([{b"a": b"1"}, {b"a": b"2"}, {b"a": b"3"}])
        rows = await backend.aget_many([0, 2])
        assert rows == [{b"a": b"1"}, {b"a": b"3"}]

    @pytest.mark.anyio
    async def test_aiter_rows_default(self):
        backend = MemoryAsyncRawReadable([{b"a": b"1"}, {b"a": b"2"}])
        result = []
        async for row in backend.aiter_rows([0, 1]):
            result.append(row)
        assert result == [{b"a": b"1"}, {b"a": b"2"}]


# ── Tests: AsyncRawWritableBackend ──────────────────────────────────────


class TestAsyncRawWritable:
    @pytest.mark.anyio
    async def test_aset(self):
        backend = MemoryAsyncRawWritable([{b"a": b"1"}])
        await backend.aset(0, {b"a": b"99"})
        assert await backend.aget(0) == {b"a": b"99"}

    @pytest.mark.anyio
    async def test_ainsert(self):
        backend = MemoryAsyncRawWritable([{b"a": b"1"}, {b"a": b"3"}])
        await backend.ainsert(1, {b"a": b"2"})
        assert await backend.alen() == 3
        assert await backend.aget(1) == {b"a": b"2"}

    @pytest.mark.anyio
    async def test_adelete(self):
        backend = MemoryAsyncRawWritable([{b"a": b"1"}, {b"a": b"2"}])
        await backend.adelete(0)
        assert await backend.alen() == 1
        assert await backend.aget(0) == {b"a": b"2"}

    @pytest.mark.anyio
    async def test_aextend(self):
        backend = MemoryAsyncRawWritable([])
        await backend.aextend([{b"a": b"1"}, {b"a": b"2"}])
        assert await backend.alen() == 2

    @pytest.mark.anyio
    async def test_aupdate_default(self):
        backend = MemoryAsyncRawWritable([{b"a": b"1", b"b": b"2"}])
        await backend.aupdate(0, {b"a": b"99"})
        assert await backend.aget(0) == {b"a": b"99", b"b": b"2"}

    @pytest.mark.anyio
    async def test_aupdate_none_placeholder(self):
        backend = MemoryAsyncRawWritable([None])
        await backend.aupdate(0, {b"a": b"1"})
        assert await backend.aget(0) == {b"a": b"1"}

    @pytest.mark.anyio
    async def test_adelete_many_default(self):
        backend = MemoryAsyncRawWritable([
            {b"a": b"0"}, {b"a": b"1"}, {b"a": b"2"},
            {b"a": b"3"}, {b"a": b"4"},
        ])
        await backend.adelete_many(1, 4)
        assert await backend.alen() == 2
        assert await backend.aget(0) == {b"a": b"0"}
        assert await backend.aget(1) == {b"a": b"4"}

    @pytest.mark.anyio
    async def test_aset_many_default(self):
        backend = MemoryAsyncRawWritable([{b"a": b"0"}, {b"a": b"1"}, {b"a": b"2"}])
        for offset, row in enumerate([{b"a": b"99"}, {b"a": b"98"}]):
            await backend.aset(1 + offset, row)
        assert await backend.aget(1) == {b"a": b"99"}
        assert await backend.aget(2) == {b"a": b"98"}

    @pytest.mark.anyio
    async def test_adrop_keys_default(self):
        backend = MemoryAsyncRawWritable([
            {b"a": b"1", b"b": b"2"},
            {b"a": b"3", b"b": b"4"},
        ])
        await backend.adrop_keys([b"b"])
        assert await backend.aget(0) == {b"a": b"1"}
        assert await backend.aget(1) == {b"a": b"3"}

    @pytest.mark.anyio
    async def test_adrop_keys_with_indices(self):
        backend = MemoryAsyncRawWritable([
            {b"a": b"1", b"b": b"2"},
            {b"a": b"3", b"b": b"4"},
            {b"a": b"5", b"b": b"6"},
        ])
        await backend.adrop_keys([b"b"], indices=[0, 2])
        assert await backend.aget(0) == {b"a": b"1"}
        assert await backend.aget(1) == {b"a": b"3", b"b": b"4"}
        assert await backend.aget(2) == {b"a": b"5"}

    @pytest.mark.anyio
    async def test_areserve_default(self):
        backend = MemoryAsyncRawWritable([{b"a": b"1"}])
        await backend.areserve(3)
        assert await backend.alen() == 4
        assert await backend.aget(1) is None

    @pytest.mark.anyio
    async def test_aclear_default(self):
        backend = MemoryAsyncRawWritable([{b"a": b"1"}, {b"a": b"2"}])
        await backend.aclear()
        assert await backend.alen() == 0

    @pytest.mark.anyio
    async def test_aremove_raises(self):
        backend = MemoryAsyncRawWritable([])
        with pytest.raises(NotImplementedError):
            await backend.aremove()


# ── Tests: SyncToAsyncRawAdapter ────────────────────────────────────────


class TestSyncToAsyncRawAdapter:
    """Test that a sync RawWritableBackend works correctly when wrapped."""

    def _make_sync_backend(self, data=None):
        """Create a sync MemoryRawWritable for wrapping."""
        from asebytes._protocols import RawWritableBackend

        class MemorySyncRaw(RawWritableBackend):
            def __init__(self, data=None):
                self._data = data or []

            def __len__(self):
                return len(self._data)

            def schema(self):
                keys = set()
                for row in self._data:
                    if row is not None:
                        keys.update(row.keys())
                return sorted(keys)

            def get(self, index, keys=None):
                if index < 0 or index >= len(self._data):
                    raise IndexError(index)
                row = self._data[index]
                if row is None:
                    return None
                if keys is not None:
                    return {k: row[k] for k in keys if k in row}
                return dict(row)

            def set(self, index, data):
                if index < len(self._data):
                    self._data[index] = data
                elif index == len(self._data):
                    self._data.append(data)

            def insert(self, index, data):
                self._data.insert(index, data)

            def delete(self, index):
                del self._data[index]

            def extend(self, data):
                self._data.extend(data)

        return MemorySyncRaw(data)

    @pytest.mark.anyio
    async def test_alen(self):
        sync = self._make_sync_backend([{b"a": b"1"}, {b"a": b"2"}])
        adapter = SyncToAsyncRawAdapter(sync)
        assert await adapter.alen() == 2

    @pytest.mark.anyio
    async def test_aget(self):
        sync = self._make_sync_backend([{b"a": b"1", b"b": b"2"}])
        adapter = SyncToAsyncRawAdapter(sync)
        assert await adapter.aget(0) == {b"a": b"1", b"b": b"2"}

    @pytest.mark.anyio
    async def test_aget_with_keys(self):
        sync = self._make_sync_backend([{b"a": b"1", b"b": b"2"}])
        adapter = SyncToAsyncRawAdapter(sync)
        assert await adapter.aget(0, keys=[b"a"]) == {b"a": b"1"}

    @pytest.mark.anyio
    async def test_aset(self):
        sync = self._make_sync_backend([{b"a": b"1"}])
        adapter = SyncToAsyncRawAdapter(sync)
        await adapter.aset(0, {b"a": b"99"})
        assert await adapter.aget(0) == {b"a": b"99"}

    @pytest.mark.anyio
    async def test_aextend(self):
        sync = self._make_sync_backend([])
        adapter = SyncToAsyncRawAdapter(sync)
        await adapter.aextend([{b"a": b"1"}, {b"a": b"2"}])
        assert await adapter.alen() == 2

    @pytest.mark.anyio
    async def test_adelete(self):
        sync = self._make_sync_backend([{b"a": b"1"}, {b"a": b"2"}])
        adapter = SyncToAsyncRawAdapter(sync)
        await adapter.adelete(0)
        assert await adapter.alen() == 1
        assert await adapter.aget(0) == {b"a": b"2"}

    @pytest.mark.anyio
    async def test_ainsert(self):
        sync = self._make_sync_backend([{b"a": b"1"}, {b"a": b"3"}])
        adapter = SyncToAsyncRawAdapter(sync)
        await adapter.ainsert(1, {b"a": b"2"})
        assert await adapter.alen() == 3
        assert await adapter.aget(1) == {b"a": b"2"}

    @pytest.mark.anyio
    async def test_aschema(self):
        sync = self._make_sync_backend([{b"a": b"1"}, {b"b": b"2"}])
        adapter = SyncToAsyncRawAdapter(sync)
        assert await adapter.aschema() == [b"a", b"b"]

    @pytest.mark.anyio
    async def test_aupdate(self):
        sync = self._make_sync_backend([{b"a": b"1", b"b": b"2"}])
        adapter = SyncToAsyncRawAdapter(sync)
        await adapter.aupdate(0, {b"a": b"99"})
        assert await adapter.aget(0) == {b"a": b"99", b"b": b"2"}

    @pytest.mark.anyio
    async def test_adrop_keys(self):
        sync = self._make_sync_backend([{b"a": b"1", b"b": b"2"}])
        adapter = SyncToAsyncRawAdapter(sync)
        await adapter.adrop_keys([b"b"])
        assert await adapter.aget(0) == {b"a": b"1"}

    @pytest.mark.anyio
    async def test_areserve(self):
        sync = self._make_sync_backend([])
        adapter = SyncToAsyncRawAdapter(sync)
        await adapter.areserve(3)
        assert await adapter.alen() == 3
        assert await adapter.aget(0) is None


# ── Tests: SyncToAsyncAdapter (str-level) ───────────────────────────────


class TestSyncToAsyncAdapter:
    """Test that a sync WritableBackend works correctly when wrapped."""

    def _make_sync_backend(self, data=None):
        from asebytes._protocols import WritableBackend

        class MemorySyncStr(WritableBackend):
            def __init__(self, data=None):
                self._data = data or []

            def __len__(self):
                return len(self._data)

            def schema(self):
                if not self._data:
                    return []
                row = self._data[0]
                return sorted(row.keys()) if row is not None else []

            def get(self, index, keys=None):
                if index < 0 or index >= len(self._data):
                    raise IndexError(index)
                row = self._data[index]
                if row is None:
                    return None
                if keys is not None:
                    return {k: row[k] for k in keys if k in row}
                return dict(row)

            def set(self, index, data):
                if index < len(self._data):
                    self._data[index] = data
                elif index == len(self._data):
                    self._data.append(data)

            def insert(self, index, data):
                self._data.insert(index, data)

            def delete(self, index):
                del self._data[index]

            def extend(self, data):
                self._data.extend(data)

        return MemorySyncStr(data)

    @pytest.mark.anyio
    async def test_alen(self):
        sync = self._make_sync_backend([{"a": 1}, {"a": 2}])
        adapter = SyncToAsyncAdapter(sync)
        assert await adapter.alen() == 2

    @pytest.mark.anyio
    async def test_aget(self):
        sync = self._make_sync_backend([{"a": 1, "b": 2}])
        adapter = SyncToAsyncAdapter(sync)
        assert await adapter.aget(0) == {"a": 1, "b": 2}

    @pytest.mark.anyio
    async def test_aset_and_aget(self):
        sync = self._make_sync_backend([{"a": 1}])
        adapter = SyncToAsyncAdapter(sync)
        await adapter.aset(0, {"a": 99})
        assert await adapter.aget(0) == {"a": 99}

    @pytest.mark.anyio
    async def test_aschema(self):
        sync = self._make_sync_backend([{"a": 1, "b": 2}])
        adapter = SyncToAsyncAdapter(sync)
        assert await adapter.aschema() == ["a", "b"]

    @pytest.mark.anyio
    async def test_aget_column(self):
        sync = self._make_sync_backend([{"a": 1}, {"a": 2}, {"a": 3}])
        adapter = SyncToAsyncAdapter(sync)
        assert await adapter.aget_column("a") == [1, 2, 3]

    @pytest.mark.anyio
    async def test_adrop_keys(self):
        sync = self._make_sync_backend([{"a": 1, "b": 2}])
        adapter = SyncToAsyncAdapter(sync)
        await adapter.adrop_keys(["b"])
        assert await adapter.aget(0) == {"a": 1}
