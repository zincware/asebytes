"""Tests for top-level update() on AsyncBlobIO, AsyncObjectIO, AsyncASEIO.

Each async facade should expose update() that merges data into an existing row.
Read-only backends must raise TypeError.
"""

from __future__ import annotations

from typing import Any

import pytest

from asebytes._async_backends import AsyncReadBackend, sync_to_async
from asebytes._async_blob_io import AsyncBlobIO
from asebytes._async_object_io import AsyncObjectIO
from asebytes._async_io import AsyncASEIO
from asebytes._backends import ReadBackend, ReadWriteBackend


# ── In-memory backends ────────────────────────────────────────────────


class MemoryBlobBackend(ReadWriteBackend):
    """Minimal in-memory bytes backend."""

    def __init__(self):
        self._rows: list[dict[bytes, bytes] | None] = []

    def __len__(self) -> int:
        return len(self._rows)

    def get(self, index: int, keys=None):
        if index < 0 or index >= len(self._rows):
            raise IndexError(index)
        row = self._rows[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    def set(self, index, value):
        if index < len(self._rows):
            self._rows[index] = value
        elif index == len(self._rows):
            self._rows.append(value)
        else:
            raise IndexError(index)

    def insert(self, index, value):
        self._rows.insert(index, value)

    def delete(self, index):
        del self._rows[index]

    def extend(self, values):
        self._rows.extend(values)


class MemoryObjectBackend(ReadWriteBackend):
    """Minimal in-memory str/Any backend."""

    def __init__(self):
        self._rows: list[dict[str, Any] | None] = []

    def __len__(self) -> int:
        return len(self._rows)

    def get(self, index: int, keys=None):
        if index < 0 or index >= len(self._rows):
            raise IndexError(index)
        row = self._rows[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    def set(self, index, value):
        if index < len(self._rows):
            self._rows[index] = value
        elif index == len(self._rows):
            self._rows.append(value)
        else:
            raise IndexError(index)

    def insert(self, index, value):
        self._rows.insert(index, value)

    def delete(self, index):
        del self._rows[index]

    def extend(self, values):
        self._rows.extend(values)


class ReadOnlyBlobBackend(ReadBackend):
    """Read-only bytes backend (no write methods)."""

    def __init__(self):
        self._rows: list[dict[bytes, bytes] | None] = []

    def __len__(self) -> int:
        return len(self._rows)

    def get(self, index: int, keys=None):
        if index < 0 or index >= len(self._rows):
            raise IndexError(index)
        row = self._rows[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)


class ReadOnlyObjectBackend(ReadBackend):
    """Read-only str/Any backend (no write methods)."""

    def __init__(self):
        self._rows: list[dict[str, Any] | None] = []

    def __len__(self) -> int:
        return len(self._rows)

    def get(self, index: int, keys=None):
        if index < 0 or index >= len(self._rows):
            raise IndexError(index)
        row = self._rows[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)


# ── AsyncBlobIO.update() ─────────────────────────────────────────────


class TestAsyncBlobIOUpdate:
    @pytest.mark.anyio
    async def test_update_merges_into_existing_row(self):
        """update(0, {b"a": b"99"}) merges into existing row."""
        be = MemoryBlobBackend()
        be.extend([{b"a": b"1", b"b": b"2"}])
        db = AsyncBlobIO(sync_to_async(be))

        await db.update(0, {b"a": b"99"})

        assert be._rows[0][b"a"] == b"99"
        assert be._rows[0][b"b"] == b"2"  # untouched

    @pytest.mark.anyio
    async def test_update_raises_on_read_only(self):
        """update() raises TypeError on read-only backend."""
        be = ReadOnlyBlobBackend()
        db = AsyncBlobIO(sync_to_async(be))

        with pytest.raises(TypeError, match="read-only"):
            await db.update(0, {b"a": b"99"})


# ── AsyncObjectIO.update() ──────────────────────────────────────────


class TestAsyncObjectIOUpdate:
    @pytest.mark.anyio
    async def test_update_merges_into_existing_row(self):
        """update(0, {"a": 99}) merges into existing row."""
        be = MemoryObjectBackend()
        be.extend([{"a": 1, "b": 2}])
        db = AsyncObjectIO(sync_to_async(be))

        await db.update(0, {"a": 99})

        assert be._rows[0]["a"] == 99
        assert be._rows[0]["b"] == 2  # untouched

    @pytest.mark.anyio
    async def test_update_raises_on_read_only(self):
        """update() raises TypeError on read-only backend."""
        be = ReadOnlyObjectBackend()
        db = AsyncObjectIO(sync_to_async(be))

        with pytest.raises(TypeError, match="read-only"):
            await db.update(0, {"a": 99})


# ── AsyncASEIO.update() ─────────────────────────────────────────────


class TestAsyncASEIOUpdate:
    @pytest.mark.anyio
    async def test_update_flat_dict(self):
        """update(0, {"calc.energy": -10.5}) merges via flat dict."""
        be = MemoryObjectBackend()
        be.extend([{"calc.energy": -1.0, "info.tag": "mol_0"}])
        db = AsyncASEIO(sync_to_async(be))

        await db.update(0, {"calc.energy": -10.5})

        assert be._rows[0]["calc.energy"] == -10.5
        assert be._rows[0]["info.tag"] == "mol_0"  # untouched

    @pytest.mark.anyio
    async def test_update_keyword_api(self):
        """update(0, info={...}, calc={...}) builds namespaced keys."""
        be = MemoryObjectBackend()
        be.extend([{"calc.energy": -1.0, "info.tag": "mol_0"}])
        db = AsyncASEIO(sync_to_async(be))

        await db.update(0, info={"tag": "done"}, calc={"energy": -99.0})

        assert be._rows[0]["info.tag"] == "done"
        assert be._rows[0]["calc.energy"] == -99.0

    @pytest.mark.anyio
    async def test_update_top_level_keys(self):
        """update(0, {"cell": ...}) works for valid top-level keys."""
        be = MemoryObjectBackend()
        be.extend([{"cell": [[1, 0, 0], [0, 1, 0], [0, 0, 1]], "pbc": [True, True, True]}])
        db = AsyncASEIO(sync_to_async(be))

        new_cell = [[2, 0, 0], [0, 2, 0], [0, 0, 2]]
        await db.update(0, {"cell": new_cell})

        assert be._rows[0]["cell"] == new_cell
        assert be._rows[0]["pbc"] == [True, True, True]  # untouched

    @pytest.mark.anyio
    async def test_update_invalid_key_raises(self):
        """update(0, {"bad_key": 1}) raises ValueError."""
        be = MemoryObjectBackend()
        be.extend([{"calc.energy": -1.0}])
        db = AsyncASEIO(sync_to_async(be))

        with pytest.raises(ValueError, match="Invalid key"):
            await db.update(0, {"bad_key": 1})

    @pytest.mark.anyio
    async def test_update_empty_is_noop(self):
        """update(0) with no data is a no-op."""
        be = MemoryObjectBackend()
        be.extend([{"calc.energy": -1.0}])
        db = AsyncASEIO(sync_to_async(be))

        await db.update(0)  # should not raise

        assert be._rows[0]["calc.energy"] == -1.0

    @pytest.mark.anyio
    async def test_update_raises_on_read_only(self):
        """update() raises TypeError on read-only backend."""
        be = ReadOnlyObjectBackend()
        db = AsyncASEIO(sync_to_async(be))

        with pytest.raises(TypeError, match="read-only"):
            await db.update(0, {"calc.energy": -1.0})
