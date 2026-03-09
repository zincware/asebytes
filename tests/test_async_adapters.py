"""Tests for async adapter classes.

AsyncBlobToObject adapters wrap an AsyncReadBackend[bytes, bytes]
(or AsyncReadWriteBackend[bytes, bytes]) and present an
AsyncReadBackend[str, Any] (or AsyncReadWriteBackend[str, Any]) interface
by serialising/deserialising values with msgpack + msgpack_numpy.

AsyncObjectToBlob adapters do the reverse.

Tests use SyncToAsyncReadWriteAdapter wrapping LMDBBlobBackend to provide
the underlying async blob backend.
"""

from __future__ import annotations

import numpy as np
import pytest

from asebytes._async_backends import (
    AsyncReadBackend,
    AsyncReadWriteBackend,
    SyncToAsyncReadWriteAdapter,
)
from asebytes._async_adapters import (
    AsyncBlobToObjectReadAdapter,
    AsyncBlobToObjectReadWriteAdapter,
    AsyncObjectToBlobReadAdapter,
    AsyncObjectToBlobReadWriteAdapter,
)
from asebytes.lmdb._blob_backend import LMDBBlobBackend


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def async_blob_backend(tmp_path):
    """Async blob backend: SyncToAsync wrapping LMDBBlobBackend."""
    blob = LMDBBlobBackend(str(tmp_path / "async_test.lmdb"))
    return SyncToAsyncReadWriteAdapter(blob)


@pytest.fixture
def async_bto_read_adapter(async_blob_backend):
    """AsyncBlobToObjectReadAdapter wrapping async blob backend."""
    return AsyncBlobToObjectReadAdapter(async_blob_backend)


@pytest.fixture
def async_bto_rw_adapter(async_blob_backend):
    """AsyncBlobToObjectReadWriteAdapter wrapping async blob backend."""
    return AsyncBlobToObjectReadWriteAdapter(async_blob_backend)


@pytest.fixture
def async_object_backend(tmp_path):
    """Async object backend built by wrapping LMDB blob backend with BlobToObject."""
    blob = LMDBBlobBackend(str(tmp_path / "async_obj_test.lmdb"))
    async_blob = SyncToAsyncReadWriteAdapter(blob)
    return AsyncBlobToObjectReadWriteAdapter(async_blob)


@pytest.fixture
def async_otb_read_adapter(async_object_backend):
    """AsyncObjectToBlobReadAdapter wrapping async object backend."""
    return AsyncObjectToBlobReadAdapter(async_object_backend)


@pytest.fixture
def async_otb_rw_adapter(async_object_backend):
    """AsyncObjectToBlobReadWriteAdapter wrapping async object backend."""
    return AsyncObjectToBlobReadWriteAdapter(async_object_backend)


# ═══════════════════════════════════════════════════════════════════════════
# AsyncBlobToObject adapter tests
# ═══════════════════════════════════════════════════════════════════════════


# ── isinstance checks ────────────────────────────────────────────────────


class TestAsyncBlobToObjectInstanceChecks:
    def test_read_adapter_is_async_read_backend(self, async_bto_read_adapter):
        assert isinstance(async_bto_read_adapter, AsyncReadBackend)

    def test_read_adapter_is_not_async_readwrite_backend(self, async_bto_read_adapter):
        assert not isinstance(async_bto_read_adapter, AsyncReadWriteBackend)

    def test_rw_adapter_is_async_read_backend(self, async_bto_rw_adapter):
        assert isinstance(async_bto_rw_adapter, AsyncReadBackend)

    def test_rw_adapter_is_async_readwrite_backend(self, async_bto_rw_adapter):
        assert isinstance(async_bto_rw_adapter, AsyncReadWriteBackend)


# ── AsyncBlobToObjectReadAdapter ──────────────────────────────────────────


class TestAsyncBlobToObjectReadAdapter:
    @pytest.mark.anyio
    async def test_len_empty(self, async_bto_read_adapter):
        assert await async_bto_read_adapter.len() == 0

    @pytest.mark.anyio
    async def test_len_after_blob_write(self, async_blob_backend, async_bto_read_adapter):
        """Writing via the underlying blob backend shows up in len."""
        import msgpack
        import msgpack_numpy as m

        row = {
            b"energy": msgpack.packb(-10.5, default=m.encode),
            b"smiles": msgpack.packb("CCO", default=m.encode),
        }
        await async_blob_backend.extend([row])
        assert await async_bto_read_adapter.len() == 1

    @pytest.mark.anyio
    async def test_get_deserializes(self, async_blob_backend, async_bto_read_adapter):
        """get() returns deserialized str-keyed dict."""
        import msgpack
        import msgpack_numpy as m

        arr = np.array([1.0, 2.0, 3.0])
        row = {
            b"energy": msgpack.packb(-5.0, default=m.encode),
            b"vec": msgpack.packb(arr, default=m.encode),
        }
        await async_blob_backend.extend([row])
        result = await async_bto_read_adapter.get(0)
        assert isinstance(result, dict)
        assert "energy" in result
        assert result["energy"] == pytest.approx(-5.0)
        np.testing.assert_array_equal(result["vec"], arr)

    @pytest.mark.anyio
    async def test_get_with_keys(self, async_blob_backend, async_bto_read_adapter):
        """get() with keys filters to requested fields."""
        import msgpack
        import msgpack_numpy as m

        row = {
            b"a": msgpack.packb(1, default=m.encode),
            b"b": msgpack.packb(2, default=m.encode),
            b"c": msgpack.packb(3, default=m.encode),
        }
        await async_blob_backend.extend([row])
        result = await async_bto_read_adapter.get(0, keys=["a", "c"])
        assert set(result.keys()) == {"a", "c"}
        assert result["a"] == 1
        assert result["c"] == 3

    @pytest.mark.anyio
    async def test_get_none_placeholder(self, async_blob_backend, async_bto_read_adapter):
        """get() on a None placeholder returns None."""
        await async_blob_backend.extend([None])
        result = await async_bto_read_adapter.get(0)
        assert result is None

    @pytest.mark.anyio
    async def test_get_many(self, async_blob_backend, async_bto_read_adapter):
        """get_many returns deserialized rows."""
        import msgpack
        import msgpack_numpy as m

        rows = [
            {b"val": msgpack.packb(float(i), default=m.encode)}
            for i in range(5)
        ]
        await async_blob_backend.extend(rows)
        result = await async_bto_read_adapter.get_many([0, 2, 4])
        assert len(result) == 3
        assert result[0]["val"] == pytest.approx(0.0)
        assert result[1]["val"] == pytest.approx(2.0)
        assert result[2]["val"] == pytest.approx(4.0)

    @pytest.mark.anyio
    async def test_get_many_with_none(self, async_blob_backend, async_bto_read_adapter):
        """get_many correctly returns None for placeholder rows."""
        import msgpack
        import msgpack_numpy as m

        await async_blob_backend.extend([
            {b"val": msgpack.packb(1, default=m.encode)},
            None,
            {b"val": msgpack.packb(3, default=m.encode)},
        ])
        result = await async_bto_read_adapter.get_many([0, 1, 2])
        assert result[0] is not None
        assert result[1] is None
        assert result[2] is not None

    @pytest.mark.anyio
    async def test_iter_rows(self, async_blob_backend, async_bto_read_adapter):
        """iter_rows yields deserialized rows."""
        import msgpack
        import msgpack_numpy as m

        rows = [
            {b"val": msgpack.packb(float(i), default=m.encode)}
            for i in range(3)
        ]
        await async_blob_backend.extend(rows)
        results = []
        async for row in async_bto_read_adapter.iter_rows([0, 1, 2]):
            results.append(row)
        assert len(results) == 3
        for i, r in enumerate(results):
            assert r["val"] == pytest.approx(float(i))

    @pytest.mark.anyio
    async def test_iter_rows_with_none(self, async_blob_backend, async_bto_read_adapter):
        """iter_rows yields None for placeholder rows."""
        import msgpack
        import msgpack_numpy as m

        await async_blob_backend.extend([
            {b"val": msgpack.packb(1, default=m.encode)},
            None,
        ])
        results = []
        async for row in async_bto_read_adapter.iter_rows([0, 1]):
            results.append(row)
        assert results[0] is not None
        assert results[1] is None

    @pytest.mark.anyio
    async def test_get_column(self, async_blob_backend, async_bto_read_adapter):
        """get_column extracts a single key across rows."""
        import msgpack
        import msgpack_numpy as m

        rows = [
            {b"energy": msgpack.packb(float(-i), default=m.encode)}
            for i in range(4)
        ]
        await async_blob_backend.extend(rows)
        col = await async_bto_read_adapter.get_column("energy")
        assert col == pytest.approx([0.0, -1.0, -2.0, -3.0])

    @pytest.mark.anyio
    async def test_get_column_with_indices(self, async_blob_backend, async_bto_read_adapter):
        """get_column with explicit indices."""
        import msgpack
        import msgpack_numpy as m

        rows = [
            {b"x": msgpack.packb(float(i), default=m.encode)}
            for i in range(5)
        ]
        await async_blob_backend.extend(rows)
        col = await async_bto_read_adapter.get_column("x", indices=[1, 3])
        assert col == pytest.approx([1.0, 3.0])

    @pytest.mark.anyio
    async def test_keys(self, async_blob_backend, async_bto_read_adapter):
        """keys() returns str keys from the blob backend."""
        import msgpack
        import msgpack_numpy as m

        row = {
            b"alpha": msgpack.packb(1, default=m.encode),
            b"beta": msgpack.packb(2, default=m.encode),
        }
        await async_blob_backend.extend([row])
        k = await async_bto_read_adapter.keys(0)
        assert set(k) == {"alpha", "beta"}

    @pytest.mark.anyio
    async def test_keys_on_none_placeholder(self, async_blob_backend, async_bto_read_adapter):
        """keys() on None placeholder returns empty list."""
        await async_blob_backend.extend([None])
        k = await async_bto_read_adapter.keys(0)
        assert k == []


# ── AsyncBlobToObjectReadWriteAdapter ─────────────────────────────────────


class TestAsyncBlobToObjectReadWriteAdapter:
    @pytest.mark.anyio
    async def test_set_and_get(self, async_bto_rw_adapter):
        """set() serializes, get() deserializes correctly."""
        row = {
            "energy": -10.5,
            "forces": np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]),
            "smiles": "CCO",
            "numbers": np.array([1, 6, 8]),
        }
        await async_bto_rw_adapter.set(0, row)
        assert await async_bto_rw_adapter.len() == 1
        result = await async_bto_rw_adapter.get(0)
        assert result["energy"] == pytest.approx(-10.5)
        assert result["smiles"] == "CCO"
        np.testing.assert_array_almost_equal(
            result["forces"],
            np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]),
        )
        np.testing.assert_array_equal(result["numbers"], np.array([1, 6, 8]))

    @pytest.mark.anyio
    async def test_set_none_placeholder(self, async_bto_rw_adapter):
        """set() with None creates a placeholder."""
        await async_bto_rw_adapter.set(0, {"x": 1})
        await async_bto_rw_adapter.set(0, None)
        assert await async_bto_rw_adapter.get(0) is None

    @pytest.mark.anyio
    async def test_extend(self, async_bto_rw_adapter):
        """extend() appends multiple rows."""
        rows = [{"val": float(i)} for i in range(5)]
        await async_bto_rw_adapter.extend(rows)
        assert await async_bto_rw_adapter.len() == 5
        for i in range(5):
            result = await async_bto_rw_adapter.get(i)
            assert result["val"] == pytest.approx(float(i))

    @pytest.mark.anyio
    async def test_extend_with_none(self, async_bto_rw_adapter):
        """extend() handles None placeholders in the list."""
        await async_bto_rw_adapter.extend([{"val": 1}, None, {"val": 3}])
        assert await async_bto_rw_adapter.len() == 3
        assert (await async_bto_rw_adapter.get(0))["val"] == 1
        assert await async_bto_rw_adapter.get(1) is None
        assert (await async_bto_rw_adapter.get(2))["val"] == 3

    @pytest.mark.anyio
    async def test_insert(self, async_bto_rw_adapter):
        """insert() shifts rows correctly."""
        await async_bto_rw_adapter.extend([{"val": 1.0}, {"val": 3.0}])
        await async_bto_rw_adapter.insert(1, {"val": 2.0})
        assert await async_bto_rw_adapter.len() == 3
        assert (await async_bto_rw_adapter.get(0))["val"] == pytest.approx(1.0)
        assert (await async_bto_rw_adapter.get(1))["val"] == pytest.approx(2.0)
        assert (await async_bto_rw_adapter.get(2))["val"] == pytest.approx(3.0)

    @pytest.mark.anyio
    async def test_insert_none(self, async_bto_rw_adapter):
        """insert() with None creates a placeholder."""
        await async_bto_rw_adapter.extend([{"val": 1}])
        await async_bto_rw_adapter.insert(0, None)
        assert await async_bto_rw_adapter.len() == 2
        assert await async_bto_rw_adapter.get(0) is None
        assert (await async_bto_rw_adapter.get(1))["val"] == 1

    @pytest.mark.anyio
    async def test_delete(self, async_bto_rw_adapter):
        """delete() removes and shifts."""
        await async_bto_rw_adapter.extend(
            [{"val": 1.0}, {"val": 2.0}, {"val": 3.0}]
        )
        await async_bto_rw_adapter.delete(1)
        assert await async_bto_rw_adapter.len() == 2
        assert (await async_bto_rw_adapter.get(0))["val"] == pytest.approx(1.0)
        assert (await async_bto_rw_adapter.get(1))["val"] == pytest.approx(3.0)

    @pytest.mark.anyio
    async def test_update_partial_merge(self, async_bto_rw_adapter):
        """update() merges new keys into existing row."""
        await async_bto_rw_adapter.set(0, {"a": 1, "b": 2})
        await async_bto_rw_adapter.update(0, {"b": 99, "c": 100})
        row = await async_bto_rw_adapter.get(0)
        assert row["a"] == 1
        assert row["b"] == 99
        assert row["c"] == 100

    @pytest.mark.anyio
    async def test_get_column(self, async_bto_rw_adapter):
        """get_column extracts a single field across rows."""
        await async_bto_rw_adapter.extend(
            [{"energy": float(-i)} for i in range(4)]
        )
        col = await async_bto_rw_adapter.get_column("energy")
        assert col == pytest.approx([0.0, -1.0, -2.0, -3.0])

    @pytest.mark.anyio
    async def test_keys_returns_str(self, async_bto_rw_adapter):
        """keys() returns str keys."""
        await async_bto_rw_adapter.set(0, {"alpha": 1, "beta": 2})
        k = await async_bto_rw_adapter.keys(0)
        assert set(k) == {"alpha", "beta"}


# ═══════════════════════════════════════════════════════════════════════════
# AsyncObjectToBlob adapter tests
# ═══════════════════════════════════════════════════════════════════════════


# ── isinstance checks ────────────────────────────────────────────────────


class TestAsyncObjectToBlobInstanceChecks:
    def test_read_adapter_is_async_read_backend(self, async_otb_read_adapter):
        assert isinstance(async_otb_read_adapter, AsyncReadBackend)

    def test_read_adapter_is_not_async_readwrite_backend(self, async_otb_read_adapter):
        assert not isinstance(async_otb_read_adapter, AsyncReadWriteBackend)

    def test_rw_adapter_is_async_read_backend(self, async_otb_rw_adapter):
        assert isinstance(async_otb_rw_adapter, AsyncReadBackend)

    def test_rw_adapter_is_async_readwrite_backend(self, async_otb_rw_adapter):
        assert isinstance(async_otb_rw_adapter, AsyncReadWriteBackend)


# ── AsyncObjectToBlobReadAdapter ──────────────────────────────────────────


class TestAsyncObjectToBlobReadAdapter:
    @pytest.mark.anyio
    async def test_len_empty(self, async_otb_read_adapter):
        assert await async_otb_read_adapter.len() == 0

    @pytest.mark.anyio
    async def test_len_after_object_write(self, async_object_backend, async_otb_read_adapter):
        """Writing via the underlying object backend shows up in len."""
        await async_object_backend.extend([{"energy": -10.5, "smiles": "CCO"}])
        assert await async_otb_read_adapter.len() == 1

    @pytest.mark.anyio
    async def test_get_serializes(self, async_object_backend, async_otb_read_adapter):
        """get() returns serialized bytes-keyed dict."""
        import msgpack
        import msgpack_numpy as m

        arr = np.array([1.0, 2.0, 3.0])
        await async_object_backend.extend([{"energy": -5.0, "vec": arr}])
        result = await async_otb_read_adapter.get(0)
        assert isinstance(result, dict)
        assert all(isinstance(k, bytes) for k in result.keys())
        assert all(isinstance(v, bytes) for v in result.values())
        assert msgpack.unpackb(result[b"energy"], object_hook=m.decode) == pytest.approx(-5.0)
        np.testing.assert_array_equal(
            msgpack.unpackb(result[b"vec"], object_hook=m.decode), arr
        )

    @pytest.mark.anyio
    async def test_get_with_keys(self, async_object_backend, async_otb_read_adapter):
        """get() with bytes keys filters to requested fields."""
        import msgpack
        import msgpack_numpy as m

        await async_object_backend.extend([{"a": 1, "b": 2, "c": 3}])
        result = await async_otb_read_adapter.get(0, keys=[b"a", b"c"])
        assert set(result.keys()) == {b"a", b"c"}
        assert msgpack.unpackb(result[b"a"], object_hook=m.decode) == 1
        assert msgpack.unpackb(result[b"c"], object_hook=m.decode) == 3

    @pytest.mark.anyio
    async def test_get_none_placeholder(self, async_object_backend, async_otb_read_adapter):
        """get() on a None placeholder returns None."""
        await async_object_backend.extend([None])
        result = await async_otb_read_adapter.get(0)
        assert result is None

    @pytest.mark.anyio
    async def test_get_many(self, async_object_backend, async_otb_read_adapter):
        """get_many returns serialized rows."""
        import msgpack
        import msgpack_numpy as m

        rows = [{"val": float(i)} for i in range(5)]
        await async_object_backend.extend(rows)
        result = await async_otb_read_adapter.get_many([0, 2, 4])
        assert len(result) == 3
        assert msgpack.unpackb(result[0][b"val"], object_hook=m.decode) == pytest.approx(0.0)
        assert msgpack.unpackb(result[1][b"val"], object_hook=m.decode) == pytest.approx(2.0)
        assert msgpack.unpackb(result[2][b"val"], object_hook=m.decode) == pytest.approx(4.0)

    @pytest.mark.anyio
    async def test_get_many_with_none(self, async_object_backend, async_otb_read_adapter):
        """get_many correctly returns None for placeholder rows."""
        await async_object_backend.extend([{"val": 1}, None, {"val": 3}])
        result = await async_otb_read_adapter.get_many([0, 1, 2])
        assert result[0] is not None
        assert result[1] is None
        assert result[2] is not None

    @pytest.mark.anyio
    async def test_iter_rows(self, async_object_backend, async_otb_read_adapter):
        """iter_rows yields serialized rows."""
        import msgpack
        import msgpack_numpy as m

        rows = [{"val": float(i)} for i in range(3)]
        await async_object_backend.extend(rows)
        results = []
        async for row in async_otb_read_adapter.iter_rows([0, 1, 2]):
            results.append(row)
        assert len(results) == 3
        for i, r in enumerate(results):
            assert msgpack.unpackb(r[b"val"], object_hook=m.decode) == pytest.approx(float(i))

    @pytest.mark.anyio
    async def test_iter_rows_with_none(self, async_object_backend, async_otb_read_adapter):
        """iter_rows yields None for placeholder rows."""
        await async_object_backend.extend([{"val": 1}, None])
        results = []
        async for row in async_otb_read_adapter.iter_rows([0, 1]):
            results.append(row)
        assert results[0] is not None
        assert results[1] is None

    @pytest.mark.anyio
    async def test_get_column(self, async_object_backend, async_otb_read_adapter):
        """get_column extracts a single key across rows as serialized bytes."""
        import msgpack
        import msgpack_numpy as m

        rows = [{"energy": float(-i)} for i in range(4)]
        await async_object_backend.extend(rows)
        col = await async_otb_read_adapter.get_column(b"energy")
        deserialized = [msgpack.unpackb(v, object_hook=m.decode) for v in col]
        assert deserialized == pytest.approx([0.0, -1.0, -2.0, -3.0])

    @pytest.mark.anyio
    async def test_get_column_with_indices(self, async_object_backend, async_otb_read_adapter):
        """get_column with explicit indices."""
        import msgpack
        import msgpack_numpy as m

        rows = [{"x": float(i)} for i in range(5)]
        await async_object_backend.extend(rows)
        col = await async_otb_read_adapter.get_column(b"x", indices=[1, 3])
        deserialized = [msgpack.unpackb(v, object_hook=m.decode) for v in col]
        assert deserialized == pytest.approx([1.0, 3.0])

    @pytest.mark.anyio
    async def test_keys(self, async_object_backend, async_otb_read_adapter):
        """keys() returns bytes keys from the object backend."""
        await async_object_backend.extend([{"alpha": 1, "beta": 2}])
        k = await async_otb_read_adapter.keys(0)
        assert set(k) == {b"alpha", b"beta"}

    @pytest.mark.anyio
    async def test_keys_on_none_placeholder(self, async_object_backend, async_otb_read_adapter):
        """keys() on None placeholder returns empty list."""
        await async_object_backend.extend([None])
        k = await async_otb_read_adapter.keys(0)
        assert k == []


# ── AsyncObjectToBlobReadWriteAdapter ─────────────────────────────────────


class TestAsyncObjectToBlobReadWriteAdapter:
    @pytest.mark.anyio
    async def test_roundtrip_write_blob_read_blob(self, async_otb_rw_adapter):
        """Write blob data via adapter, read back as blob, verify correctness."""
        import msgpack
        import msgpack_numpy as m

        blob_row = {
            b"energy": msgpack.packb(-10.5, default=m.encode),
            b"smiles": msgpack.packb("CCO", default=m.encode),
        }
        await async_otb_rw_adapter.extend([blob_row])
        assert await async_otb_rw_adapter.len() == 1
        result = await async_otb_rw_adapter.get(0)
        assert msgpack.unpackb(result[b"energy"], object_hook=m.decode) == pytest.approx(-10.5)
        assert msgpack.unpackb(result[b"smiles"], object_hook=m.decode) == "CCO"

    @pytest.mark.anyio
    async def test_set_and_get(self, async_otb_rw_adapter):
        """set() deserializes blob to object, get() serializes back."""
        import msgpack
        import msgpack_numpy as m

        blob_row = {
            b"energy": msgpack.packb(-10.5, default=m.encode),
            b"name": msgpack.packb("water", default=m.encode),
        }
        await async_otb_rw_adapter.set(0, blob_row)
        assert await async_otb_rw_adapter.len() == 1
        result = await async_otb_rw_adapter.get(0)
        assert msgpack.unpackb(result[b"energy"], object_hook=m.decode) == pytest.approx(-10.5)
        assert msgpack.unpackb(result[b"name"], object_hook=m.decode) == "water"

    @pytest.mark.anyio
    async def test_set_none_placeholder(self, async_otb_rw_adapter):
        """set() with None creates a placeholder."""
        import msgpack
        import msgpack_numpy as m

        await async_otb_rw_adapter.set(0, {b"x": msgpack.packb(1, default=m.encode)})
        await async_otb_rw_adapter.set(0, None)
        assert await async_otb_rw_adapter.get(0) is None

    @pytest.mark.anyio
    async def test_extend(self, async_otb_rw_adapter):
        """extend() appends multiple blob rows."""
        import msgpack
        import msgpack_numpy as m

        rows = [
            {b"val": msgpack.packb(float(i), default=m.encode)}
            for i in range(5)
        ]
        await async_otb_rw_adapter.extend(rows)
        assert await async_otb_rw_adapter.len() == 5
        for i in range(5):
            result = await async_otb_rw_adapter.get(i)
            assert msgpack.unpackb(result[b"val"], object_hook=m.decode) == pytest.approx(float(i))

    @pytest.mark.anyio
    async def test_extend_with_none(self, async_otb_rw_adapter):
        """extend() handles None placeholders in the list."""
        import msgpack
        import msgpack_numpy as m

        await async_otb_rw_adapter.extend([
            {b"val": msgpack.packb(1, default=m.encode)},
            None,
            {b"val": msgpack.packb(3, default=m.encode)},
        ])
        assert await async_otb_rw_adapter.len() == 3
        assert await async_otb_rw_adapter.get(0) is not None
        assert await async_otb_rw_adapter.get(1) is None
        assert await async_otb_rw_adapter.get(2) is not None

    @pytest.mark.anyio
    async def test_insert(self, async_otb_rw_adapter):
        """insert() shifts rows correctly."""
        import msgpack
        import msgpack_numpy as m

        await async_otb_rw_adapter.extend([
            {b"val": msgpack.packb(1.0, default=m.encode)},
            {b"val": msgpack.packb(3.0, default=m.encode)},
        ])
        await async_otb_rw_adapter.insert(1, {b"val": msgpack.packb(2.0, default=m.encode)})
        assert await async_otb_rw_adapter.len() == 3
        import msgpack
        assert msgpack.unpackb((await async_otb_rw_adapter.get(0))[b"val"], object_hook=m.decode) == pytest.approx(1.0)
        assert msgpack.unpackb((await async_otb_rw_adapter.get(1))[b"val"], object_hook=m.decode) == pytest.approx(2.0)
        assert msgpack.unpackb((await async_otb_rw_adapter.get(2))[b"val"], object_hook=m.decode) == pytest.approx(3.0)

    @pytest.mark.anyio
    async def test_insert_none(self, async_otb_rw_adapter):
        """insert() with None creates a placeholder."""
        import msgpack
        import msgpack_numpy as m

        await async_otb_rw_adapter.extend([{b"val": msgpack.packb(1, default=m.encode)}])
        await async_otb_rw_adapter.insert(0, None)
        assert await async_otb_rw_adapter.len() == 2
        assert await async_otb_rw_adapter.get(0) is None
        assert await async_otb_rw_adapter.get(1) is not None

    @pytest.mark.anyio
    async def test_delete(self, async_otb_rw_adapter):
        """delete() removes and shifts."""
        import msgpack
        import msgpack_numpy as m

        await async_otb_rw_adapter.extend([
            {b"val": msgpack.packb(1.0, default=m.encode)},
            {b"val": msgpack.packb(2.0, default=m.encode)},
            {b"val": msgpack.packb(3.0, default=m.encode)},
        ])
        await async_otb_rw_adapter.delete(1)
        assert await async_otb_rw_adapter.len() == 2
        assert msgpack.unpackb((await async_otb_rw_adapter.get(0))[b"val"], object_hook=m.decode) == pytest.approx(1.0)
        assert msgpack.unpackb((await async_otb_rw_adapter.get(1))[b"val"], object_hook=m.decode) == pytest.approx(3.0)

    @pytest.mark.anyio
    async def test_update_partial_merge(self, async_otb_rw_adapter):
        """update() merges new keys into existing row."""
        import msgpack
        import msgpack_numpy as m

        await async_otb_rw_adapter.set(0, {
            b"a": msgpack.packb(1, default=m.encode),
            b"b": msgpack.packb(2, default=m.encode),
        })
        await async_otb_rw_adapter.update(0, {
            b"b": msgpack.packb(99, default=m.encode),
            b"c": msgpack.packb(100, default=m.encode),
        })
        row = await async_otb_rw_adapter.get(0)
        assert msgpack.unpackb(row[b"a"], object_hook=m.decode) == 1
        assert msgpack.unpackb(row[b"b"], object_hook=m.decode) == 99
        assert msgpack.unpackb(row[b"c"], object_hook=m.decode) == 100

    @pytest.mark.anyio
    async def test_keys_returns_bytes(self, async_otb_rw_adapter):
        """keys() returns bytes keys."""
        import msgpack
        import msgpack_numpy as m

        await async_otb_rw_adapter.set(0, {
            b"alpha": msgpack.packb(1, default=m.encode),
            b"beta": msgpack.packb(2, default=m.encode),
        })
        k = await async_otb_rw_adapter.keys(0)
        assert set(k) == {b"alpha", b"beta"}
