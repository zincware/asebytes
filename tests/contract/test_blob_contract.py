"""BlobIO facade contract tests.

Every read-write backend must satisfy the same blob-level contract when
accessed through the BlobIO facade.

Values must be msgpack-serialized because non-native blob backends use
the ObjectToBlobReadWriteAdapter which deserializes/serializes via msgpack.
"""

from __future__ import annotations

import msgpack
import pytest
import msgpack_numpy as m


def _pack(val) -> bytes:
    """Serialize a value to msgpack bytes."""
    return msgpack.packb(val, default=m.encode)


def _unpack(raw: bytes):
    """Deserialize msgpack bytes."""
    return msgpack.unpackb(raw, object_hook=m.decode)


class TestBlobContract:
    """Core CRUD contract for BlobIO facade."""

    def test_extend_and_len(self, blobio):
        rows = [
            {b"key1": _pack("value1")},
            {b"key2": _pack("value2")},
            {b"key3": _pack("value3")},
        ]
        blobio.extend(rows)
        assert len(blobio) == 3

    def test_get_by_index(self, blobio):
        rows = [{b"k": _pack("v1")}, {b"k": _pack("v2")}]
        blobio.extend(rows)
        row = blobio[0]
        assert b"k" in row
        assert _unpack(row[b"k"]) == "v1"

    def test_get_by_index_second(self, blobio):
        rows = [{b"k": _pack("v1")}, {b"k": _pack("v2")}]
        blobio.extend(rows)
        row = blobio[1]
        assert _unpack(row[b"k"]) == "v2"

    def test_slice(self, blobio):
        rows = [{b"k": _pack("v1")}, {b"k": _pack("v2")}, {b"k": _pack("v3")}]
        blobio.extend(rows)
        result = blobio[0:2]
        assert len(result) == 2

    def test_negative_index(self, blobio):
        rows = [{b"k": _pack("v1")}, {b"k": _pack("v2")}, {b"k": _pack("v3")}]
        blobio.extend(rows)
        row = blobio[-1]
        assert _unpack(row[b"k"]) == "v3"

    def test_iteration(self, blobio):
        rows = [{b"k": _pack("v1")}, {b"k": _pack("v2")}]
        blobio.extend(rows)
        items = list(blobio)
        assert len(items) == 2
        for item in items:
            assert isinstance(item, dict)

    def test_keys(self, blobio):
        rows = [{b"k1": _pack(1), b"k2": _pack(2)}]
        blobio.extend(rows)
        k = blobio.keys(0)
        assert isinstance(k, list)
        assert len(k) > 0

    def test_set_overwrite(self, blobio):
        rows = [{b"k": _pack("old")}]
        blobio.extend(rows)
        blobio[0] = {b"k": _pack("new")}
        row = blobio[0]
        assert _unpack(row[b"k"]) == "new"

    def test_remove(self, blobio):
        rows = [{b"k": _pack("v1")}]
        blobio.extend(rows)
        assert len(blobio) >= 1
        try:
            blobio.remove()
        except NotImplementedError:
            pytest.skip("Backend does not implement remove()")
