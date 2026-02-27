"""Tests for generic K type in RowView / ColumnView / async views.

RowView[R, K] and ColumnView[K] should accept the parent's native key type.
BlobIO uses K=bytes, ObjectIO uses K=str.
"""
from __future__ import annotations

from typing import Any, Iterator

import pytest

from asebytes._views import ColumnView, RowView


# ── Sync bytes-keyed mock parent ────────────────────────────────────────


class BytesMockParent:
    """Mock parent using bytes keys (like BlobIO)."""

    def __init__(self, rows: list[dict[bytes, bytes]]):
        self._rows = rows

    def __len__(self):
        return len(self._rows)

    def _read_row(self, index, keys=None):
        row = self._rows[index]
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    def _read_rows(self, indices, keys=None):
        return [self._read_row(i, keys) for i in indices]

    def _iter_rows(self, indices, keys=None):
        for i in indices:
            yield self._read_row(i, keys)

    def _read_column(self, key, indices):
        return [self._rows[i][key] for i in indices]

    def _build_result(self, row):
        return row

    def _write_row(self, index, data):
        self._rows[index] = data

    def _update_row(self, index, data):
        self._rows[index].update(data)

    def _delete_row(self, index):
        del self._rows[index]

    def _delete_rows(self, start, stop):
        for i in range(stop - 1, start - 1, -1):
            del self._rows[i]


@pytest.fixture
def brows():
    return [
        {b"name": b"alice", b"age": b"30"},
        {b"name": b"bob", b"age": b"25"},
        {b"name": b"carol", b"age": b"35"},
    ]


# ══════════════════════════════════════════════════════════════════════════
# Sync RowView with bytes keys
# ══════════════════════════════════════════════════════════════════════════


class TestRowViewBytesKey:
    """RowView with bytes-keyed parent should accept bytes column keys."""

    def test_bytes_key_returns_column_view(self, brows):
        parent = BytesMockParent(brows)
        rv = RowView(parent, range(3))
        cv = rv[b"name"]
        assert isinstance(cv, ColumnView)

    def test_list_bytes_key_returns_column_view(self, brows):
        parent = BytesMockParent(brows)
        rv = RowView(parent, range(3))
        cv = rv[[b"name", b"age"]]
        assert isinstance(cv, ColumnView)

    def test_bytes_column_to_list(self, brows):
        parent = BytesMockParent(brows)
        rv = RowView(parent, range(3))
        result = rv[b"name"].to_list()
        assert result == [b"alice", b"bob", b"carol"]

    def test_bytes_column_int_index(self, brows):
        parent = BytesMockParent(brows)
        rv = RowView(parent, range(3))
        result = rv[b"name"][0]
        assert result == b"alice"

    def test_multi_bytes_column_to_list(self, brows):
        parent = BytesMockParent(brows)
        rv = RowView(parent, range(3))
        result = rv[[b"name", b"age"]].to_list()
        assert result == [[b"alice", b"30"], [b"bob", b"25"], [b"carol", b"35"]]


# ══════════════════════════════════════════════════════════════════════════
# Sync ColumnView with bytes keys
# ══════════════════════════════════════════════════════════════════════════


class TestColumnViewBytesKey:
    def test_single_bytes_key(self, brows):
        parent = BytesMockParent(brows)
        cv = ColumnView(parent, b"name", range(3))
        assert cv.to_list() == [b"alice", b"bob", b"carol"]

    def test_multi_bytes_keys(self, brows):
        parent = BytesMockParent(brows)
        cv = ColumnView(parent, [b"name", b"age"], range(3))
        result = cv.to_list()
        assert result == [[b"alice", b"30"], [b"bob", b"25"], [b"carol", b"35"]]

    def test_to_dict_bytes_keys(self, brows):
        parent = BytesMockParent(brows)
        cv = ColumnView(parent, [b"name", b"age"], range(3))
        result = cv.to_dict()
        assert result == {
            b"name": [b"alice", b"bob", b"carol"],
            b"age": [b"30", b"25", b"35"],
        }

    def test_bytes_key_set(self, brows):
        parent = BytesMockParent(brows)
        cv = ColumnView(parent, b"name", range(3))
        cv.set([b"x", b"y", b"z"])
        assert parent._rows[0][b"name"] == b"x"
        assert parent._rows[2][b"name"] == b"z"


# ══════════════════════════════════════════════════════════════════════════
# Async views with bytes keys
# ══════════════════════════════════════════════════════════════════════════

from asebytes._async_views import (
    AsyncColumnView,
    AsyncRowView,
    AsyncSingleRowView,
)


class AsyncBytesMockParent:
    """Async mock parent using bytes keys (like AsyncBlobIO)."""

    def __init__(self, rows: list[dict[bytes, bytes]]):
        self._rows = rows

    def __len__(self):
        return len(self._rows)

    async def len(self):
        return len(self._rows)

    async def _read_row(self, index, keys=None):
        row = self._rows[index]
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    async def _read_rows(self, indices, keys=None):
        return [await self._read_row(i, keys) for i in indices]

    async def _read_column(self, key, indices):
        return [self._rows[i][key] for i in indices]

    async def _write_row(self, index, data):
        self._rows[index] = data

    async def _delete_row(self, index):
        del self._rows[index]

    async def _delete_rows(self, start, stop):
        for i in range(stop - 1, start - 1, -1):
            del self._rows[i]

    async def _update_row(self, index, data):
        self._rows[index].update(data)

    async def _drop_keys(self, keys, indices):
        pass

    async def _get_available_keys(self, index):
        return list(self._rows[index].keys())

    def _build_result(self, row):
        return row


class TestAsyncRowViewBytesKey:
    @pytest.mark.anyio
    async def test_bytes_key_returns_column_view(self, brows):
        parent = AsyncBytesMockParent(brows)
        rv = AsyncRowView(parent, list(range(3)))
        cv = rv[b"name"]
        assert isinstance(cv, AsyncColumnView)

    @pytest.mark.anyio
    async def test_bytes_column_to_list(self, brows):
        parent = AsyncBytesMockParent(brows)
        rv = AsyncRowView(parent, list(range(3)))
        result = await rv[b"name"].to_list()
        assert result == [b"alice", b"bob", b"carol"]

    @pytest.mark.anyio
    async def test_bytes_column_int_index(self, brows):
        parent = AsyncBytesMockParent(brows)
        rv = AsyncRowView(parent, list(range(3)))
        result = await rv[b"name"][0]
        assert result == b"alice"

    @pytest.mark.anyio
    async def test_list_bytes_key(self, brows):
        parent = AsyncBytesMockParent(brows)
        rv = AsyncRowView(parent, list(range(3)))
        result = await rv[[b"name", b"age"]].to_list()
        assert result == [[b"alice", b"30"], [b"bob", b"25"], [b"carol", b"35"]]


class TestAsyncSingleRowViewBytesKey:
    @pytest.mark.anyio
    async def test_bytes_key_subscript(self, brows):
        parent = AsyncBytesMockParent(brows)
        view = AsyncSingleRowView(parent, 0)
        result = await view[b"name"]
        assert result == b"alice"

    @pytest.mark.anyio
    async def test_list_bytes_key_subscript(self, brows):
        parent = AsyncBytesMockParent(brows)
        view = AsyncSingleRowView(parent, 0)
        result = await view[[b"name", b"age"]]
        assert result == [b"alice", b"30"]


class TestAsyncColumnViewBytesKey:
    @pytest.mark.anyio
    async def test_single_bytes_key(self, brows):
        parent = AsyncBytesMockParent(brows)
        cv = AsyncColumnView(parent, b"name", list(range(3)))
        result = await cv.to_list()
        assert result == [b"alice", b"bob", b"carol"]

    @pytest.mark.anyio
    async def test_multi_bytes_keys(self, brows):
        parent = AsyncBytesMockParent(brows)
        cv = AsyncColumnView(parent, [b"name", b"age"], list(range(3)))
        result = await cv.to_list()
        assert result == [[b"alice", b"30"], [b"bob", b"25"], [b"carol", b"35"]]

    @pytest.mark.anyio
    async def test_to_dict_bytes_keys(self, brows):
        parent = AsyncBytesMockParent(brows)
        cv = AsyncColumnView(parent, [b"name", b"age"], list(range(3)))
        result = await cv.to_dict()
        assert result == {
            b"name": [b"alice", b"bob", b"carol"],
            b"age": [b"30", b"25", b"35"],
        }

    @pytest.mark.anyio
    async def test_bytes_column_set(self, brows):
        parent = AsyncBytesMockParent(brows)
        cv = AsyncColumnView(parent, b"name", list(range(3)))
        await cv.set([b"x", b"y", b"z"])
        assert parent._rows[0][b"name"] == b"x"
        assert parent._rows[2][b"name"] == b"z"
