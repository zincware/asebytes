"""AsyncBlobIO facade contract tests.

Every read-write backend must satisfy the same blob-level contract when
accessed through the AsyncBlobIO facade. All tests use @pytest.mark.anyio.

Values must be msgpack-serialized because non-native blob backends use
the ObjectToBlobReadWriteAdapter which deserializes/serializes via msgpack.
"""

from __future__ import annotations

import msgpack
import msgpack_numpy as m
import pytest


def _pack(val) -> bytes:
    """Serialize a value to msgpack bytes."""
    return msgpack.packb(val, default=m.encode)


def _unpack(raw: bytes):
    """Deserialize msgpack bytes."""
    return msgpack.unpackb(raw, object_hook=m.decode)


@pytest.mark.anyio
class TestAsyncBlobContract:
    """Core CRUD contract for AsyncBlobIO facade."""

    async def test_extend_and_len(self, async_blobio):
        rows = [
            {b"key1": _pack("value1")},
            {b"key2": _pack("value2")},
            {b"key3": _pack("value3")},
        ]
        await async_blobio.extend(rows)
        assert await async_blobio.len() == 3

    async def test_get_by_index(self, async_blobio):
        rows = [{b"k": _pack("v1")}, {b"k": _pack("v2")}]
        await async_blobio.extend(rows)
        row = await async_blobio[0]
        assert b"k" in row
        assert _unpack(row[b"k"]) == "v1"

    async def test_slice(self, async_blobio):
        rows = [{b"k": _pack("v1")}, {b"k": _pack("v2")}, {b"k": _pack("v3")}]
        await async_blobio.extend(rows)
        result = await async_blobio[0:2].to_list()
        assert len(result) == 2

    async def test_negative_index(self, async_blobio):
        rows = [{b"k": _pack("v1")}, {b"k": _pack("v2")}, {b"k": _pack("v3")}]
        await async_blobio.extend(rows)
        row = await async_blobio[-1]
        assert _unpack(row[b"k"]) == "v3"

    async def test_iteration(self, async_blobio):
        rows = [{b"k": _pack("v1")}, {b"k": _pack("v2")}]
        await async_blobio.extend(rows)
        items = []
        async for item in async_blobio:
            items.append(item)
        assert len(items) == 2
        for item in items:
            assert isinstance(item, dict)

    async def test_keys(self, async_blobio):
        rows = [{b"k1": _pack(1), b"k2": _pack(2)}]
        await async_blobio.extend(rows)
        k = await async_blobio.keys(0)
        assert isinstance(k, list)
        assert len(k) > 0
