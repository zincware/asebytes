"""Tests for async protocol ABCs and SyncToAsyncAdapter.

Tests:
- AsyncRawReadableBackend / AsyncRawWritableBackend cannot be instantiated
- In-memory async implementations pass the same tests as sync
- SyncToAsyncRawAdapter wraps a sync RawWritableBackend and works correctly
- SyncToAsyncAdapter wraps a sync WritableBackend and works correctly
"""

from __future__ import annotations

from typing import Any, AsyncIterator

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

    async def get_schema(self) -> list[bytes]:
        keys: set[bytes] = set()
        for row in self._data:
            if row is not None:
                keys.update(row.keys())
        return sorted(keys)

    async def read_row(
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
    async def write_row(self, index: int, data: dict[bytes, bytes] | None) -> None:
        if index < len(self._data):
            self._data[index] = data
        elif index == len(self._data):
            self._data.append(data)
        else:
            raise IndexError(index)

    async def insert_row(self, index: int, data: dict[bytes, bytes] | None) -> None:
        self._data.insert(index, data)

    async def delete_row(self, index: int) -> None:
        del self._data[index]

    async def append_rows(self, data: list[dict[bytes, bytes] | None]) -> None:
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
    async def test_read_row(self):
        backend = MemoryAsyncRawReadable([{b"a": b"1", b"b": b"2"}])
        assert await backend.read_row(0) == {b"a": b"1", b"b": b"2"}

    @pytest.mark.anyio
    async def test_read_row_with_keys(self):
        backend = MemoryAsyncRawReadable([{b"a": b"1", b"b": b"2"}])
        assert await backend.read_row(0, keys=[b"a"]) == {b"a": b"1"}

    @pytest.mark.anyio
    async def test_read_row_none(self):
        backend = MemoryAsyncRawReadable([None])
        assert await backend.read_row(0) is None

    @pytest.mark.anyio
    async def test_get_available_keys_default(self):
        backend = MemoryAsyncRawReadable([{b"a": b"1", b"b": b"2"}])
        keys = await backend.get_available_keys(0)
        assert sorted(keys) == [b"a", b"b"]

    @pytest.mark.anyio
    async def test_get_available_keys_none(self):
        backend = MemoryAsyncRawReadable([None])
        assert await backend.get_available_keys(0) == []

    @pytest.mark.anyio
    async def test_read_rows_default(self):
        backend = MemoryAsyncRawReadable([{b"a": b"1"}, {b"a": b"2"}, {b"a": b"3"}])
        rows = await backend.read_rows([0, 2])
        assert rows == [{b"a": b"1"}, {b"a": b"3"}]

    @pytest.mark.anyio
    async def test_iter_rows_default(self):
        backend = MemoryAsyncRawReadable([{b"a": b"1"}, {b"a": b"2"}])
        result = []
        async for row in backend.iter_rows([0, 1]):
            result.append(row)
        assert result == [{b"a": b"1"}, {b"a": b"2"}]


# ── Tests: AsyncRawWritableBackend ──────────────────────────────────────


class TestAsyncRawWritable:
    @pytest.mark.anyio
    async def test_write_row(self):
        backend = MemoryAsyncRawWritable([{b"a": b"1"}])
        await backend.write_row(0, {b"a": b"99"})
        assert await backend.read_row(0) == {b"a": b"99"}

    @pytest.mark.anyio
    async def test_insert_row(self):
        backend = MemoryAsyncRawWritable([{b"a": b"1"}, {b"a": b"3"}])
        await backend.insert_row(1, {b"a": b"2"})
        assert await backend.alen() == 3
        assert await backend.read_row(1) == {b"a": b"2"}

    @pytest.mark.anyio
    async def test_delete_row(self):
        backend = MemoryAsyncRawWritable([{b"a": b"1"}, {b"a": b"2"}])
        await backend.delete_row(0)
        assert await backend.alen() == 1
        assert await backend.read_row(0) == {b"a": b"2"}

    @pytest.mark.anyio
    async def test_append_rows(self):
        backend = MemoryAsyncRawWritable([])
        await backend.append_rows([{b"a": b"1"}, {b"a": b"2"}])
        assert await backend.alen() == 2

    @pytest.mark.anyio
    async def test_update_row_default(self):
        backend = MemoryAsyncRawWritable([{b"a": b"1", b"b": b"2"}])
        await backend.update_row(0, {b"a": b"99"})
        assert await backend.read_row(0) == {b"a": b"99", b"b": b"2"}

    @pytest.mark.anyio
    async def test_update_row_none_placeholder(self):
        backend = MemoryAsyncRawWritable([None])
        await backend.update_row(0, {b"a": b"1"})
        assert await backend.read_row(0) == {b"a": b"1"}

    @pytest.mark.anyio
    async def test_delete_rows_default(self):
        backend = MemoryAsyncRawWritable([
            {b"a": b"0"}, {b"a": b"1"}, {b"a": b"2"},
            {b"a": b"3"}, {b"a": b"4"},
        ])
        await backend.delete_rows(1, 4)
        assert await backend.alen() == 2
        assert await backend.read_row(0) == {b"a": b"0"}
        assert await backend.read_row(1) == {b"a": b"4"}

    @pytest.mark.anyio
    async def test_write_rows_default(self):
        backend = MemoryAsyncRawWritable([{b"a": b"0"}, {b"a": b"1"}, {b"a": b"2"}])
        await backend.write_rows(1, [{b"a": b"99"}, {b"a": b"98"}])
        assert await backend.read_row(1) == {b"a": b"99"}
        assert await backend.read_row(2) == {b"a": b"98"}

    @pytest.mark.anyio
    async def test_drop_keys_default(self):
        backend = MemoryAsyncRawWritable([
            {b"a": b"1", b"b": b"2"},
            {b"a": b"3", b"b": b"4"},
        ])
        await backend.drop_keys([b"b"])
        assert await backend.read_row(0) == {b"a": b"1"}
        assert await backend.read_row(1) == {b"a": b"3"}

    @pytest.mark.anyio
    async def test_drop_keys_with_indices(self):
        backend = MemoryAsyncRawWritable([
            {b"a": b"1", b"b": b"2"},
            {b"a": b"3", b"b": b"4"},
            {b"a": b"5", b"b": b"6"},
        ])
        await backend.drop_keys([b"b"], indices=[0, 2])
        assert await backend.read_row(0) == {b"a": b"1"}
        assert await backend.read_row(1) == {b"a": b"3", b"b": b"4"}
        assert await backend.read_row(2) == {b"a": b"5"}

    @pytest.mark.anyio
    async def test_reserve_default(self):
        backend = MemoryAsyncRawWritable([{b"a": b"1"}])
        await backend.reserve(3)
        assert await backend.alen() == 4
        assert await backend.read_row(1) is None

    @pytest.mark.anyio
    async def test_clear_default(self):
        backend = MemoryAsyncRawWritable([{b"a": b"1"}, {b"a": b"2"}])
        await backend.clear()
        assert await backend.alen() == 0

    @pytest.mark.anyio
    async def test_remove_raises(self):
        backend = MemoryAsyncRawWritable([])
        with pytest.raises(NotImplementedError):
            await backend.remove()


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

            def get_schema(self):
                keys = set()
                for row in self._data:
                    if row is not None:
                        keys.update(row.keys())
                return sorted(keys)

            def read_row(self, index, keys=None):
                if index < 0 or index >= len(self._data):
                    raise IndexError(index)
                row = self._data[index]
                if row is None:
                    return None
                if keys is not None:
                    return {k: row[k] for k in keys if k in row}
                return dict(row)

            def write_row(self, index, data):
                if index < len(self._data):
                    self._data[index] = data
                elif index == len(self._data):
                    self._data.append(data)

            def insert_row(self, index, data):
                self._data.insert(index, data)

            def delete_row(self, index):
                del self._data[index]

            def append_rows(self, data):
                self._data.extend(data)

        return MemorySyncRaw(data)

    @pytest.mark.anyio
    async def test_alen(self):
        sync = self._make_sync_backend([{b"a": b"1"}, {b"a": b"2"}])
        adapter = SyncToAsyncRawAdapter(sync)
        assert await adapter.alen() == 2

    @pytest.mark.anyio
    async def test_read_row(self):
        sync = self._make_sync_backend([{b"a": b"1", b"b": b"2"}])
        adapter = SyncToAsyncRawAdapter(sync)
        assert await adapter.read_row(0) == {b"a": b"1", b"b": b"2"}

    @pytest.mark.anyio
    async def test_read_row_with_keys(self):
        sync = self._make_sync_backend([{b"a": b"1", b"b": b"2"}])
        adapter = SyncToAsyncRawAdapter(sync)
        assert await adapter.read_row(0, keys=[b"a"]) == {b"a": b"1"}

    @pytest.mark.anyio
    async def test_write_row(self):
        sync = self._make_sync_backend([{b"a": b"1"}])
        adapter = SyncToAsyncRawAdapter(sync)
        await adapter.write_row(0, {b"a": b"99"})
        assert await adapter.read_row(0) == {b"a": b"99"}

    @pytest.mark.anyio
    async def test_append_rows(self):
        sync = self._make_sync_backend([])
        adapter = SyncToAsyncRawAdapter(sync)
        await adapter.append_rows([{b"a": b"1"}, {b"a": b"2"}])
        assert await adapter.alen() == 2

    @pytest.mark.anyio
    async def test_delete_row(self):
        sync = self._make_sync_backend([{b"a": b"1"}, {b"a": b"2"}])
        adapter = SyncToAsyncRawAdapter(sync)
        await adapter.delete_row(0)
        assert await adapter.alen() == 1
        assert await adapter.read_row(0) == {b"a": b"2"}

    @pytest.mark.anyio
    async def test_insert_row(self):
        sync = self._make_sync_backend([{b"a": b"1"}, {b"a": b"3"}])
        adapter = SyncToAsyncRawAdapter(sync)
        await adapter.insert_row(1, {b"a": b"2"})
        assert await adapter.alen() == 3
        assert await adapter.read_row(1) == {b"a": b"2"}

    @pytest.mark.anyio
    async def test_get_schema(self):
        sync = self._make_sync_backend([{b"a": b"1"}, {b"b": b"2"}])
        adapter = SyncToAsyncRawAdapter(sync)
        assert await adapter.get_schema() == [b"a", b"b"]

    @pytest.mark.anyio
    async def test_update_row(self):
        sync = self._make_sync_backend([{b"a": b"1", b"b": b"2"}])
        adapter = SyncToAsyncRawAdapter(sync)
        await adapter.update_row(0, {b"a": b"99"})
        assert await adapter.read_row(0) == {b"a": b"99", b"b": b"2"}

    @pytest.mark.anyio
    async def test_drop_keys(self):
        sync = self._make_sync_backend([{b"a": b"1", b"b": b"2"}])
        adapter = SyncToAsyncRawAdapter(sync)
        await adapter.drop_keys([b"b"])
        assert await adapter.read_row(0) == {b"a": b"1"}

    @pytest.mark.anyio
    async def test_reserve(self):
        sync = self._make_sync_backend([])
        adapter = SyncToAsyncRawAdapter(sync)
        await adapter.reserve(3)
        assert await adapter.alen() == 3
        assert await adapter.read_row(0) is None


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

            def columns(self, index=0):
                if not self._data:
                    return []
                row = self._data[index]
                return sorted(row.keys()) if row is not None else []

            def read_row(self, index, keys=None):
                if index < 0 or index >= len(self._data):
                    raise IndexError(index)
                row = self._data[index]
                if row is None:
                    return None
                if keys is not None:
                    return {k: row[k] for k in keys if k in row}
                return dict(row)

            def write_row(self, index, data):
                if index < len(self._data):
                    self._data[index] = data
                elif index == len(self._data):
                    self._data.append(data)

            def insert_row(self, index, data):
                self._data.insert(index, data)

            def delete_row(self, index):
                del self._data[index]

            def append_rows(self, data):
                self._data.extend(data)

        return MemorySyncStr(data)

    @pytest.mark.anyio
    async def test_alen(self):
        sync = self._make_sync_backend([{"a": 1}, {"a": 2}])
        adapter = SyncToAsyncAdapter(sync)
        assert await adapter.alen() == 2

    @pytest.mark.anyio
    async def test_read_row(self):
        sync = self._make_sync_backend([{"a": 1, "b": 2}])
        adapter = SyncToAsyncAdapter(sync)
        assert await adapter.read_row(0) == {"a": 1, "b": 2}

    @pytest.mark.anyio
    async def test_write_and_read(self):
        sync = self._make_sync_backend([{"a": 1}])
        adapter = SyncToAsyncAdapter(sync)
        await adapter.write_row(0, {"a": 99})
        assert await adapter.read_row(0) == {"a": 99}

    @pytest.mark.anyio
    async def test_columns(self):
        sync = self._make_sync_backend([{"a": 1, "b": 2}])
        adapter = SyncToAsyncAdapter(sync)
        assert await adapter.columns() == ["a", "b"]

    @pytest.mark.anyio
    async def test_read_column(self):
        sync = self._make_sync_backend([{"a": 1}, {"a": 2}, {"a": 3}])
        adapter = SyncToAsyncAdapter(sync)
        assert await adapter.read_column("a") == [1, 2, 3]

    @pytest.mark.anyio
    async def test_drop_keys(self):
        sync = self._make_sync_backend([{"a": 1, "b": 2}])
        adapter = SyncToAsyncAdapter(sync)
        await adapter.drop_keys(["b"])
        assert await adapter.read_row(0) == {"a": 1}
