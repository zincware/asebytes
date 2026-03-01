"""Tests for async backend ABCs and SyncToAsyncAdapter.

Tests:
- AsyncReadBackend / AsyncReadWriteBackend cannot be instantiated
- In-memory async implementations pass the same tests as sync
- SyncToAsyncAdapter wraps a sync ReadWriteBackend and works correctly
- SyncToAsyncAdapter wraps a sync ReadWriteBackend and works correctly
"""

from __future__ import annotations

from typing import Any

import pytest

from asebytes._async_backends import (
    AsyncReadBackend,
    AsyncReadWriteBackend,
    SyncToAsyncAdapter,
)


# ── In-memory async implementations ────────────────────────────────────


class MemoryAsyncRawReadable(AsyncReadBackend):
    def __init__(self, data: list[dict[bytes, bytes] | None] | None = None):
        self._data: list[dict[bytes, bytes] | None] = data or []

    async def len(self) -> int:
        return len(self._data)

    async def keys(self, index: int) -> list[bytes]:
        row = self._data[index] if index < len(self._data) else None
        if row is None:
            return []
        return sorted(row.keys())

    async def get(
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

    @staticmethod
    def list_groups(path: str, **kwargs) -> list[str]:
        return []


class MemoryAsyncRawWritable(MemoryAsyncRawReadable, AsyncReadWriteBackend):
    async def set(self, index: int, data: dict[bytes, bytes] | None) -> None:
        if index < len(self._data):
            self._data[index] = data
        elif index == len(self._data):
            self._data.append(data)
        else:
            raise IndexError(index)

    async def insert(self, index: int, data: dict[bytes, bytes] | None) -> None:
        self._data.insert(index, data)

    async def delete(self, index: int) -> None:
        del self._data[index]

    async def extend(self, data: list[dict[bytes, bytes] | None]) -> None:
        self._data.extend(data)


# ── Tests: cannot instantiate abstract classes ──────────────────────────


class TestAbstractInstantiation:
    def test_cannot_instantiate_async_read(self):
        with pytest.raises(TypeError):
            AsyncReadBackend()

    def test_cannot_instantiate_async_read_write(self):
        with pytest.raises(TypeError):
            AsyncReadWriteBackend()


# ── Tests: AsyncReadBackend ──────────────────────────────────────────────


class TestAsyncRawReadable:
    @pytest.mark.anyio
    async def test_len(self):
        backend = MemoryAsyncRawReadable([{b"a": b"1"}, {b"b": b"2"}])
        assert await backend.len() == 2

    @pytest.mark.anyio
    async def test_get(self):
        backend = MemoryAsyncRawReadable([{b"a": b"1", b"b": b"2"}])
        assert await backend.get(0) == {b"a": b"1", b"b": b"2"}

    @pytest.mark.anyio
    async def test_get_with_keys(self):
        backend = MemoryAsyncRawReadable([{b"a": b"1", b"b": b"2"}])
        assert await backend.get(0, keys=[b"a"]) == {b"a": b"1"}

    @pytest.mark.anyio
    async def test_get_none(self):
        backend = MemoryAsyncRawReadable([None])
        assert await backend.get(0) is None

    @pytest.mark.anyio
    async def test_get_keys_from_row(self):
        backend = MemoryAsyncRawReadable([{b"a": b"1", b"b": b"2"}])
        row = await backend.get(0)
        assert sorted(row.keys()) == [b"a", b"b"]

    @pytest.mark.anyio
    async def test_get_keys_from_none_row(self):
        backend = MemoryAsyncRawReadable([None])
        row = await backend.get(0)
        assert row is None

    @pytest.mark.anyio
    async def test_get_many_default(self):
        backend = MemoryAsyncRawReadable([{b"a": b"1"}, {b"a": b"2"}, {b"a": b"3"}])
        rows = await backend.get_many([0, 2])
        assert rows == [{b"a": b"1"}, {b"a": b"3"}]

    @pytest.mark.anyio
    async def test_iter_rows_default(self):
        backend = MemoryAsyncRawReadable([{b"a": b"1"}, {b"a": b"2"}])
        result = []
        async for row in backend.iter_rows([0, 1]):
            result.append(row)
        assert result == [{b"a": b"1"}, {b"a": b"2"}]


# ── Tests: AsyncReadWriteBackend ──────────────────────────────────────────


class TestAsyncRawWritable:
    @pytest.mark.anyio
    async def test_set(self):
        backend = MemoryAsyncRawWritable([{b"a": b"1"}])
        await backend.set(0, {b"a": b"99"})
        assert await backend.get(0) == {b"a": b"99"}

    @pytest.mark.anyio
    async def test_insert(self):
        backend = MemoryAsyncRawWritable([{b"a": b"1"}, {b"a": b"3"}])
        await backend.insert(1, {b"a": b"2"})
        assert await backend.len() == 3
        assert await backend.get(1) == {b"a": b"2"}

    @pytest.mark.anyio
    async def test_delete(self):
        backend = MemoryAsyncRawWritable([{b"a": b"1"}, {b"a": b"2"}])
        await backend.delete(0)
        assert await backend.len() == 1
        assert await backend.get(0) == {b"a": b"2"}

    @pytest.mark.anyio
    async def test_extend(self):
        backend = MemoryAsyncRawWritable([])
        await backend.extend([{b"a": b"1"}, {b"a": b"2"}])
        assert await backend.len() == 2

    @pytest.mark.anyio
    async def test_update_default(self):
        backend = MemoryAsyncRawWritable([{b"a": b"1", b"b": b"2"}])
        await backend.update(0, {b"a": b"99"})
        assert await backend.get(0) == {b"a": b"99", b"b": b"2"}

    @pytest.mark.anyio
    async def test_update_none_placeholder(self):
        backend = MemoryAsyncRawWritable([None])
        await backend.update(0, {b"a": b"1"})
        assert await backend.get(0) == {b"a": b"1"}

    @pytest.mark.anyio
    async def test_delete_many_default(self):
        backend = MemoryAsyncRawWritable(
            [
                {b"a": b"0"},
                {b"a": b"1"},
                {b"a": b"2"},
                {b"a": b"3"},
                {b"a": b"4"},
            ]
        )
        await backend.delete_many(1, 4)
        assert await backend.len() == 2
        assert await backend.get(0) == {b"a": b"0"}
        assert await backend.get(1) == {b"a": b"4"}

    @pytest.mark.anyio
    async def test_set_many_default(self):
        backend = MemoryAsyncRawWritable([{b"a": b"0"}, {b"a": b"1"}, {b"a": b"2"}])
        for offset, row in enumerate([{b"a": b"99"}, {b"a": b"98"}]):
            await backend.set(1 + offset, row)
        assert await backend.get(1) == {b"a": b"99"}
        assert await backend.get(2) == {b"a": b"98"}

    @pytest.mark.anyio
    async def test_drop_keys_default(self):
        backend = MemoryAsyncRawWritable(
            [
                {b"a": b"1", b"b": b"2"},
                {b"a": b"3", b"b": b"4"},
            ]
        )
        await backend.drop_keys([b"b"])
        assert await backend.get(0) == {b"a": b"1"}
        assert await backend.get(1) == {b"a": b"3"}

    @pytest.mark.anyio
    async def test_drop_keys_with_indices(self):
        backend = MemoryAsyncRawWritable(
            [
                {b"a": b"1", b"b": b"2"},
                {b"a": b"3", b"b": b"4"},
                {b"a": b"5", b"b": b"6"},
            ]
        )
        await backend.drop_keys([b"b"], indices=[0, 2])
        assert await backend.get(0) == {b"a": b"1"}
        assert await backend.get(1) == {b"a": b"3", b"b": b"4"}
        assert await backend.get(2) == {b"a": b"5"}

    @pytest.mark.anyio
    async def test_reserve_default(self):
        backend = MemoryAsyncRawWritable([{b"a": b"1"}])
        await backend.reserve(3)
        assert await backend.len() == 4
        assert await backend.get(1) is None

    @pytest.mark.anyio
    async def test_clear_default(self):
        backend = MemoryAsyncRawWritable([{b"a": b"1"}, {b"a": b"2"}])
        await backend.clear()
        assert await backend.len() == 0

    @pytest.mark.anyio
    async def test_remove_raises(self):
        backend = MemoryAsyncRawWritable([])
        with pytest.raises(NotImplementedError):
            await backend.remove()


# ── Tests: SyncToAsyncAdapter ──────────────────────────────────────────


class TestSyncToAsyncAdapter:
    """Test that a sync ReadWriteBackend works correctly when wrapped."""

    def _make_sync_backend(self, data=None):
        """Create a sync MemoryReadWritable for wrapping."""
        from asebytes._backends import ReadWriteBackend

        class MemorySyncRaw(ReadWriteBackend):
            def __init__(self, data=None):
                self._data = data or []

            def __len__(self):
                return len(self._data)

            def keys(self, index):
                row = self._data[index] if index < len(self._data) else None
                if row is None:
                    return []
                return sorted(row.keys())

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

            @staticmethod
            def list_groups(path: str, **kwargs) -> list[str]:
                return []

        return MemorySyncRaw(data)

    @pytest.mark.anyio
    async def test_len(self):
        sync = self._make_sync_backend([{b"a": b"1"}, {b"a": b"2"}])
        adapter = SyncToAsyncAdapter(sync)
        assert await adapter.len() == 2

    @pytest.mark.anyio
    async def test_get(self):
        sync = self._make_sync_backend([{b"a": b"1", b"b": b"2"}])
        adapter = SyncToAsyncAdapter(sync)
        assert await adapter.get(0) == {b"a": b"1", b"b": b"2"}

    @pytest.mark.anyio
    async def test_get_with_keys(self):
        sync = self._make_sync_backend([{b"a": b"1", b"b": b"2"}])
        adapter = SyncToAsyncAdapter(sync)
        assert await adapter.get(0, keys=[b"a"]) == {b"a": b"1"}

    @pytest.mark.anyio
    async def test_set(self):
        sync = self._make_sync_backend([{b"a": b"1"}])
        adapter = SyncToAsyncAdapter(sync)
        await adapter.set(0, {b"a": b"99"})
        assert await adapter.get(0) == {b"a": b"99"}

    @pytest.mark.anyio
    async def test_extend(self):
        sync = self._make_sync_backend([])
        adapter = SyncToAsyncAdapter(sync)
        await adapter.extend([{b"a": b"1"}, {b"a": b"2"}])
        assert await adapter.len() == 2

    @pytest.mark.anyio
    async def test_delete(self):
        sync = self._make_sync_backend([{b"a": b"1"}, {b"a": b"2"}])
        adapter = SyncToAsyncAdapter(sync)
        await adapter.delete(0)
        assert await adapter.len() == 1
        assert await adapter.get(0) == {b"a": b"2"}

    @pytest.mark.anyio
    async def test_insert(self):
        sync = self._make_sync_backend([{b"a": b"1"}, {b"a": b"3"}])
        adapter = SyncToAsyncAdapter(sync)
        await adapter.insert(1, {b"a": b"2"})
        assert await adapter.len() == 3
        assert await adapter.get(1) == {b"a": b"2"}

    @pytest.mark.anyio
    async def test_keys(self):
        sync = self._make_sync_backend([{b"a": b"1"}, {b"b": b"2"}])
        adapter = SyncToAsyncAdapter(sync)
        assert await adapter.keys(0) == [b"a"]

    @pytest.mark.anyio
    async def test_update(self):
        sync = self._make_sync_backend([{b"a": b"1", b"b": b"2"}])
        adapter = SyncToAsyncAdapter(sync)
        await adapter.update(0, {b"a": b"99"})
        assert await adapter.get(0) == {b"a": b"99", b"b": b"2"}

    @pytest.mark.anyio
    async def test_drop_keys(self):
        sync = self._make_sync_backend([{b"a": b"1", b"b": b"2"}])
        adapter = SyncToAsyncAdapter(sync)
        await adapter.drop_keys([b"b"])
        assert await adapter.get(0) == {b"a": b"1"}

    @pytest.mark.anyio
    async def test_reserve(self):
        sync = self._make_sync_backend([])
        adapter = SyncToAsyncAdapter(sync)
        await adapter.reserve(3)
        assert await adapter.len() == 3
        assert await adapter.get(0) is None


# ── Tests: SyncToAsyncAdapter (str-level) ───────────────────────────────


class TestSyncToAsyncAdapter:
    """Test that a sync ReadWriteBackend works correctly when wrapped."""

    def _make_sync_backend(self, data=None):
        from asebytes._backends import ReadWriteBackend

        class MemorySyncStr(ReadWriteBackend):
            def __init__(self, data=None):
                self._data = data or []

            def __len__(self):
                return len(self._data)

            def keys(self, index):
                if not self._data or index >= len(self._data):
                    return []
                row = self._data[index]
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

            @staticmethod
            def list_groups(path: str, **kwargs) -> list[str]:
                return []

        return MemorySyncStr(data)

    @pytest.mark.anyio
    async def test_len(self):
        sync = self._make_sync_backend([{"a": 1}, {"a": 2}])
        adapter = SyncToAsyncAdapter(sync)
        assert await adapter.len() == 2

    @pytest.mark.anyio
    async def test_get(self):
        sync = self._make_sync_backend([{"a": 1, "b": 2}])
        adapter = SyncToAsyncAdapter(sync)
        assert await adapter.get(0) == {"a": 1, "b": 2}

    @pytest.mark.anyio
    async def test_set_and_get(self):
        sync = self._make_sync_backend([{"a": 1}])
        adapter = SyncToAsyncAdapter(sync)
        await adapter.set(0, {"a": 99})
        assert await adapter.get(0) == {"a": 99}

    @pytest.mark.anyio
    async def test_keys(self):
        sync = self._make_sync_backend([{"a": 1, "b": 2}])
        adapter = SyncToAsyncAdapter(sync)
        assert await adapter.keys(0) == ["a", "b"]

    @pytest.mark.anyio
    async def test_get_column(self):
        sync = self._make_sync_backend([{"a": 1}, {"a": 2}, {"a": 3}])
        adapter = SyncToAsyncAdapter(sync)
        assert await adapter.get_column("a") == [1, 2, 3]

    @pytest.mark.anyio
    async def test_drop_keys(self):
        sync = self._make_sync_backend([{"a": 1, "b": 2}])
        adapter = SyncToAsyncAdapter(sync)
        await adapter.drop_keys(["b"])
        assert await adapter.get(0) == {"a": 1}
