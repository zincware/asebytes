"""Tests for adapter classes.

BlobToObject adapters wrap a ReadBackend[bytes, bytes] (or ReadWriteBackend[bytes, bytes])
and present a ReadBackend[str, Any] (or ReadWriteBackend[str, Any]) interface
by serialising/deserialising values with msgpack + msgpack_numpy.

ObjectToBlob adapters do the reverse: wrap a ReadBackend[str, Any]
(or ReadWriteBackend[str, Any]) and present a ReadBackend[bytes, bytes]
(or ReadWriteBackend[bytes, bytes]) interface.
"""

import numpy as np
import pytest

from asebytes._backends import ReadBackend, ReadWriteBackend
from asebytes._adapters import (
    BlobToObjectReadAdapter,
    BlobToObjectReadWriteAdapter,
    ObjectToBlobReadAdapter,
    ObjectToBlobReadWriteAdapter,
)
from asebytes.lmdb._blob_backend import LMDBBlobBackend


# ── Helpers ──────────────────────────────────────────────────────────────

def _make_sample_row() -> dict[str, object]:
    """Object-level row for testing."""
    return {
        "energy": -10.5,
        "forces": np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]),
        "smiles": "CCO",
        "numbers": np.array([1, 6, 8]),
    }


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def blob_rw(tmp_path):
    """Fresh LMDBBlobBackend (read-write)."""
    return LMDBBlobBackend(str(tmp_path / "test.lmdb"))


@pytest.fixture
def rw_adapter(blob_rw):
    """BlobToObjectReadWriteAdapter wrapping a fresh blob backend."""
    return BlobToObjectReadWriteAdapter(blob_rw)


@pytest.fixture
def read_adapter(blob_rw):
    """BlobToObjectReadAdapter wrapping a fresh blob backend."""
    return BlobToObjectReadAdapter(blob_rw)


# ── isinstance checks ────────────────────────────────────────────────────


class TestInstanceChecks:
    def test_read_adapter_is_read_backend(self, read_adapter):
        assert isinstance(read_adapter, ReadBackend)

    def test_read_adapter_is_not_readwrite_backend(self, read_adapter):
        assert not isinstance(read_adapter, ReadWriteBackend)

    def test_rw_adapter_is_read_backend(self, rw_adapter):
        assert isinstance(rw_adapter, ReadBackend)

    def test_rw_adapter_is_readwrite_backend(self, rw_adapter):
        assert isinstance(rw_adapter, ReadWriteBackend)


# ── ReadAdapter basic operations ──────────────────────────────────────────


class TestBlobToObjectReadAdapter:
    def test_len_empty(self, read_adapter):
        assert len(read_adapter) == 0

    def test_len_after_blob_write(self, blob_rw, read_adapter):
        """Writing via the underlying blob backend shows up in len."""
        import msgpack
        import msgpack_numpy as m

        row = {
            b"energy": msgpack.packb(-10.5, default=m.encode),
            b"smiles": msgpack.packb("CCO", default=m.encode),
        }
        blob_rw.extend([row])
        assert len(read_adapter) == 1

    def test_get_deserializes(self, blob_rw, read_adapter):
        """get() returns deserialized str-keyed dict."""
        import msgpack
        import msgpack_numpy as m

        arr = np.array([1.0, 2.0, 3.0])
        row = {
            b"energy": msgpack.packb(-5.0, default=m.encode),
            b"vec": msgpack.packb(arr, default=m.encode),
        }
        blob_rw.extend([row])
        result = read_adapter.get(0)
        assert isinstance(result, dict)
        assert "energy" in result
        assert result["energy"] == pytest.approx(-5.0)
        np.testing.assert_array_equal(result["vec"], arr)

    def test_get_with_keys(self, blob_rw, read_adapter):
        """get() with keys filters to requested fields."""
        import msgpack
        import msgpack_numpy as m

        row = {
            b"a": msgpack.packb(1, default=m.encode),
            b"b": msgpack.packb(2, default=m.encode),
            b"c": msgpack.packb(3, default=m.encode),
        }
        blob_rw.extend([row])
        result = read_adapter.get(0, keys=["a", "c"])
        assert set(result.keys()) == {"a", "c"}
        assert result["a"] == 1
        assert result["c"] == 3

    def test_get_none_placeholder(self, blob_rw, read_adapter):
        """get() on a None placeholder returns None."""
        blob_rw.extend([None])
        result = read_adapter.get(0)
        assert result is None

    def test_get_many(self, blob_rw, read_adapter):
        """get_many returns deserialized rows."""
        import msgpack
        import msgpack_numpy as m

        rows = [
            {b"val": msgpack.packb(float(i), default=m.encode)}
            for i in range(5)
        ]
        blob_rw.extend(rows)
        result = read_adapter.get_many([0, 2, 4])
        assert len(result) == 3
        assert result[0]["val"] == pytest.approx(0.0)
        assert result[1]["val"] == pytest.approx(2.0)
        assert result[2]["val"] == pytest.approx(4.0)

    def test_get_many_with_none(self, blob_rw, read_adapter):
        """get_many correctly returns None for placeholder rows."""
        import msgpack
        import msgpack_numpy as m

        blob_rw.extend([
            {b"val": msgpack.packb(1, default=m.encode)},
            None,
            {b"val": msgpack.packb(3, default=m.encode)},
        ])
        result = read_adapter.get_many([0, 1, 2])
        assert result[0] is not None
        assert result[1] is None
        assert result[2] is not None

    def test_iter_rows(self, blob_rw, read_adapter):
        """iter_rows yields deserialized rows."""
        import msgpack
        import msgpack_numpy as m

        rows = [
            {b"val": msgpack.packb(float(i), default=m.encode)}
            for i in range(3)
        ]
        blob_rw.extend(rows)
        results = list(read_adapter.iter_rows([0, 1, 2]))
        assert len(results) == 3
        for i, r in enumerate(results):
            assert r["val"] == pytest.approx(float(i))

    def test_iter_rows_with_none(self, blob_rw, read_adapter):
        """iter_rows yields None for placeholder rows."""
        import msgpack
        import msgpack_numpy as m

        blob_rw.extend([
            {b"val": msgpack.packb(1, default=m.encode)},
            None,
        ])
        results = list(read_adapter.iter_rows([0, 1]))
        assert results[0] is not None
        assert results[1] is None

    def test_get_column(self, blob_rw, read_adapter):
        """get_column extracts a single key across rows."""
        import msgpack
        import msgpack_numpy as m

        rows = [
            {b"energy": msgpack.packb(float(-i), default=m.encode)}
            for i in range(4)
        ]
        blob_rw.extend(rows)
        col = read_adapter.get_column("energy")
        assert col == pytest.approx([0.0, -1.0, -2.0, -3.0])

    def test_get_column_with_indices(self, blob_rw, read_adapter):
        """get_column with explicit indices."""
        import msgpack
        import msgpack_numpy as m

        rows = [
            {b"x": msgpack.packb(float(i), default=m.encode)}
            for i in range(5)
        ]
        blob_rw.extend(rows)
        col = read_adapter.get_column("x", indices=[1, 3])
        assert col == pytest.approx([1.0, 3.0])

    def test_keys(self, blob_rw, read_adapter):
        """keys() returns str keys from the blob backend."""
        import msgpack
        import msgpack_numpy as m

        row = {
            b"alpha": msgpack.packb(1, default=m.encode),
            b"beta": msgpack.packb(2, default=m.encode),
        }
        blob_rw.extend([row])
        k = read_adapter.keys(0)
        assert set(k) == {"alpha", "beta"}

    def test_keys_on_none_placeholder(self, blob_rw, read_adapter):
        """keys() on None placeholder returns empty list."""
        blob_rw.extend([None])
        k = read_adapter.keys(0)
        assert k == []


# ── ReadWriteAdapter operations ───────────────────────────────────────────


class TestBlobToObjectReadWriteAdapter:
    def test_set_and_get(self, rw_adapter):
        """set() serializes, get() deserializes correctly."""
        row = _make_sample_row()
        rw_adapter.set(0, row)
        assert len(rw_adapter) == 1
        result = rw_adapter.get(0)
        assert result["energy"] == pytest.approx(-10.5)
        assert result["smiles"] == "CCO"
        np.testing.assert_array_almost_equal(
            result["forces"],
            np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]),
        )
        np.testing.assert_array_equal(result["numbers"], np.array([1, 6, 8]))

    def test_set_none_placeholder(self, rw_adapter):
        """set() with None creates a placeholder."""
        rw_adapter.set(0, {"x": 1})
        rw_adapter.set(0, None)
        assert rw_adapter.get(0) is None

    def test_extend(self, rw_adapter):
        """extend() appends multiple rows."""
        rows = [{"val": float(i)} for i in range(5)]
        rw_adapter.extend(rows)
        assert len(rw_adapter) == 5
        for i in range(5):
            assert rw_adapter.get(i)["val"] == pytest.approx(float(i))

    def test_extend_with_none(self, rw_adapter):
        """extend() handles None placeholders in the list."""
        rw_adapter.extend([{"val": 1}, None, {"val": 3}])
        assert len(rw_adapter) == 3
        assert rw_adapter.get(0)["val"] == 1
        assert rw_adapter.get(1) is None
        assert rw_adapter.get(2)["val"] == 3

    def test_insert(self, rw_adapter):
        """insert() shifts rows correctly."""
        rw_adapter.extend([{"val": 1.0}, {"val": 3.0}])
        rw_adapter.insert(1, {"val": 2.0})
        assert len(rw_adapter) == 3
        assert rw_adapter.get(0)["val"] == pytest.approx(1.0)
        assert rw_adapter.get(1)["val"] == pytest.approx(2.0)
        assert rw_adapter.get(2)["val"] == pytest.approx(3.0)

    def test_insert_none(self, rw_adapter):
        """insert() with None creates a placeholder."""
        rw_adapter.extend([{"val": 1}])
        rw_adapter.insert(0, None)
        assert len(rw_adapter) == 2
        assert rw_adapter.get(0) is None
        assert rw_adapter.get(1)["val"] == 1

    def test_delete(self, rw_adapter):
        """delete() removes and shifts."""
        rw_adapter.extend([{"val": 1.0}, {"val": 2.0}, {"val": 3.0}])
        rw_adapter.delete(1)
        assert len(rw_adapter) == 2
        assert rw_adapter.get(0)["val"] == pytest.approx(1.0)
        assert rw_adapter.get(1)["val"] == pytest.approx(3.0)

    def test_update_partial_merge(self, rw_adapter):
        """update() merges new keys into existing row."""
        rw_adapter.set(0, {"a": 1, "b": 2})
        rw_adapter.update(0, {"b": 99, "c": 100})
        row = rw_adapter.get(0)
        assert row["a"] == 1
        assert row["b"] == 99
        assert row["c"] == 100

    def test_get_with_keys_filter(self, rw_adapter):
        """get() with keys returns only requested fields."""
        rw_adapter.set(0, {"a": 1, "b": 2, "c": 3})
        result = rw_adapter.get(0, keys=["a", "c"])
        assert set(result.keys()) == {"a", "c"}
        assert result["a"] == 1
        assert result["c"] == 3

    def test_get_many_returns_deserialized(self, rw_adapter):
        """get_many returns all deserialized rows."""
        rw_adapter.extend([{"val": float(i)} for i in range(5)])
        result = rw_adapter.get_many([1, 3])
        assert len(result) == 2
        assert result[0]["val"] == pytest.approx(1.0)
        assert result[1]["val"] == pytest.approx(3.0)

    def test_get_column(self, rw_adapter):
        """get_column extracts a single field across rows."""
        rw_adapter.extend([{"energy": float(-i)} for i in range(4)])
        col = rw_adapter.get_column("energy")
        assert col == pytest.approx([0.0, -1.0, -2.0, -3.0])

    def test_keys_returns_str(self, rw_adapter):
        """keys() returns str keys."""
        rw_adapter.set(0, {"alpha": 1, "beta": 2})
        k = rw_adapter.keys(0)
        assert set(k) == {"alpha", "beta"}


# ── Numpy array roundtrip ─────────────────────────────────────────────────


class TestNumpyRoundtrip:
    def test_1d_array(self, rw_adapter):
        arr = np.array([1.0, 2.0, 3.0])
        rw_adapter.set(0, {"data": arr})
        result = rw_adapter.get(0)
        np.testing.assert_array_equal(result["data"], arr)

    def test_2d_array(self, rw_adapter):
        arr = np.array([[1, 2], [3, 4], [5, 6]])
        rw_adapter.set(0, {"matrix": arr})
        result = rw_adapter.get(0)
        np.testing.assert_array_equal(result["matrix"], arr)

    def test_int_array(self, rw_adapter):
        arr = np.array([1, 6, 8], dtype=np.int64)
        rw_adapter.set(0, {"numbers": arr})
        result = rw_adapter.get(0)
        np.testing.assert_array_equal(result["numbers"], arr)
        assert result["numbers"].dtype == np.int64

    def test_bool_array(self, rw_adapter):
        arr = np.array([True, False, True])
        rw_adapter.set(0, {"pbc": arr})
        result = rw_adapter.get(0)
        np.testing.assert_array_equal(result["pbc"], arr)

    def test_mixed_row_with_arrays(self, rw_adapter):
        """Row mixing scalars, strings, and numpy arrays."""
        row = {
            "energy": -10.5,
            "forces": np.array([[0.1, 0.2], [0.3, 0.4]]),
            "name": "water",
            "count": 42,
        }
        rw_adapter.set(0, row)
        result = rw_adapter.get(0)
        assert result["energy"] == pytest.approx(-10.5)
        np.testing.assert_array_almost_equal(
            result["forces"], np.array([[0.1, 0.2], [0.3, 0.4]])
        )
        assert result["name"] == "water"
        assert result["count"] == 42


# ── Reserve / None placeholder through adapter ────────────────────────────


class TestReserveThroughAdapter:
    def test_reserve_increases_len(self, rw_adapter):
        rw_adapter.extend([{"x": 1}])
        rw_adapter.reserve(3)
        assert len(rw_adapter) == 4

    def test_reserve_slots_are_none(self, rw_adapter):
        rw_adapter.extend([{"x": 1}])
        rw_adapter.reserve(2)
        assert rw_adapter.get(0) is not None
        assert rw_adapter.get(1) is None
        assert rw_adapter.get(2) is None

    def test_set_on_reserved_slot(self, rw_adapter):
        rw_adapter.reserve(2)
        rw_adapter.set(0, {"x": 42})
        assert rw_adapter.get(0)["x"] == 42
        assert rw_adapter.get(1) is None

    def test_get_many_with_reserved(self, rw_adapter):
        rw_adapter.extend([{"x": 1}])
        rw_adapter.reserve(2)
        results = rw_adapter.get_many([0, 1, 2])
        assert results[0] is not None
        assert results[1] is None
        assert results[2] is None


# ═══════════════════════════════════════════════════════════════════════════
# ObjectToBlob adapter tests
# ═══════════════════════════════════════════════════════════════════════════


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def object_backend(tmp_path):
    """Object-level ReadWriteBackend[str, Any] built by wrapping LMDB blob backend."""
    blob = LMDBBlobBackend(str(tmp_path / "obj.lmdb"))
    return BlobToObjectReadWriteAdapter(blob)


@pytest.fixture
def otb_read_adapter(object_backend):
    """ObjectToBlobReadAdapter wrapping an object backend."""
    return ObjectToBlobReadAdapter(object_backend)


@pytest.fixture
def otb_rw_adapter(object_backend):
    """ObjectToBlobReadWriteAdapter wrapping an object backend."""
    return ObjectToBlobReadWriteAdapter(object_backend)


# ── isinstance checks ────────────────────────────────────────────────────


class TestObjectToBlobInstanceChecks:
    def test_read_adapter_is_read_backend(self, otb_read_adapter):
        assert isinstance(otb_read_adapter, ReadBackend)

    def test_read_adapter_is_not_readwrite_backend(self, otb_read_adapter):
        assert not isinstance(otb_read_adapter, ReadWriteBackend)

    def test_rw_adapter_is_read_backend(self, otb_rw_adapter):
        assert isinstance(otb_rw_adapter, ReadBackend)

    def test_rw_adapter_is_readwrite_backend(self, otb_rw_adapter):
        assert isinstance(otb_rw_adapter, ReadWriteBackend)


# ── ObjectToBlobReadAdapter operations ────────────────────────────────────


class TestObjectToBlobReadAdapter:
    def test_len_empty(self, otb_read_adapter):
        assert len(otb_read_adapter) == 0

    def test_len_after_object_write(self, object_backend, otb_read_adapter):
        """Writing via the underlying object backend shows up in len."""
        object_backend.extend([{"energy": -10.5, "smiles": "CCO"}])
        assert len(otb_read_adapter) == 1

    def test_get_serializes(self, object_backend, otb_read_adapter):
        """get() returns serialized bytes-keyed dict."""
        import msgpack
        import msgpack_numpy as m

        arr = np.array([1.0, 2.0, 3.0])
        object_backend.extend([{"energy": -5.0, "vec": arr}])
        result = otb_read_adapter.get(0)
        assert isinstance(result, dict)
        # Keys should be bytes
        assert all(isinstance(k, bytes) for k in result.keys())
        # Values should be bytes (msgpack-packed)
        assert all(isinstance(v, bytes) for v in result.values())
        # Deserialize and verify
        assert msgpack.unpackb(result[b"energy"], object_hook=m.decode) == pytest.approx(-5.0)
        np.testing.assert_array_equal(
            msgpack.unpackb(result[b"vec"], object_hook=m.decode), arr
        )

    def test_get_with_keys(self, object_backend, otb_read_adapter):
        """get() with bytes keys filters to requested fields."""
        object_backend.extend([{"a": 1, "b": 2, "c": 3}])
        result = otb_read_adapter.get(0, keys=[b"a", b"c"])
        assert set(result.keys()) == {b"a", b"c"}
        import msgpack
        import msgpack_numpy as m
        assert msgpack.unpackb(result[b"a"], object_hook=m.decode) == 1
        assert msgpack.unpackb(result[b"c"], object_hook=m.decode) == 3

    def test_get_none_placeholder(self, object_backend, otb_read_adapter):
        """get() on a None placeholder returns None."""
        object_backend.extend([None])
        result = otb_read_adapter.get(0)
        assert result is None

    def test_get_many(self, object_backend, otb_read_adapter):
        """get_many returns serialized rows."""
        import msgpack
        import msgpack_numpy as m

        rows = [{"val": float(i)} for i in range(5)]
        object_backend.extend(rows)
        result = otb_read_adapter.get_many([0, 2, 4])
        assert len(result) == 3
        assert msgpack.unpackb(result[0][b"val"], object_hook=m.decode) == pytest.approx(0.0)
        assert msgpack.unpackb(result[1][b"val"], object_hook=m.decode) == pytest.approx(2.0)
        assert msgpack.unpackb(result[2][b"val"], object_hook=m.decode) == pytest.approx(4.0)

    def test_get_many_with_none(self, object_backend, otb_read_adapter):
        """get_many correctly returns None for placeholder rows."""
        object_backend.extend([{"val": 1}, None, {"val": 3}])
        result = otb_read_adapter.get_many([0, 1, 2])
        assert result[0] is not None
        assert result[1] is None
        assert result[2] is not None

    def test_iter_rows(self, object_backend, otb_read_adapter):
        """iter_rows yields serialized rows."""
        import msgpack
        import msgpack_numpy as m

        rows = [{"val": float(i)} for i in range(3)]
        object_backend.extend(rows)
        results = list(otb_read_adapter.iter_rows([0, 1, 2]))
        assert len(results) == 3
        for i, r in enumerate(results):
            assert msgpack.unpackb(r[b"val"], object_hook=m.decode) == pytest.approx(float(i))

    def test_iter_rows_with_none(self, object_backend, otb_read_adapter):
        """iter_rows yields None for placeholder rows."""
        object_backend.extend([{"val": 1}, None])
        results = list(otb_read_adapter.iter_rows([0, 1]))
        assert results[0] is not None
        assert results[1] is None

    def test_get_column(self, object_backend, otb_read_adapter):
        """get_column extracts a single key across rows as serialized bytes."""
        import msgpack
        import msgpack_numpy as m

        rows = [{"energy": float(-i)} for i in range(4)]
        object_backend.extend(rows)
        col = otb_read_adapter.get_column(b"energy")
        deserialized = [msgpack.unpackb(v, object_hook=m.decode) for v in col]
        assert deserialized == pytest.approx([0.0, -1.0, -2.0, -3.0])

    def test_get_column_with_indices(self, object_backend, otb_read_adapter):
        """get_column with explicit indices."""
        import msgpack
        import msgpack_numpy as m

        rows = [{"x": float(i)} for i in range(5)]
        object_backend.extend(rows)
        col = otb_read_adapter.get_column(b"x", indices=[1, 3])
        deserialized = [msgpack.unpackb(v, object_hook=m.decode) for v in col]
        assert deserialized == pytest.approx([1.0, 3.0])

    def test_keys(self, object_backend, otb_read_adapter):
        """keys() returns bytes keys from the object backend."""
        object_backend.extend([{"alpha": 1, "beta": 2}])
        k = otb_read_adapter.keys(0)
        assert set(k) == {b"alpha", b"beta"}

    def test_keys_on_none_placeholder(self, object_backend, otb_read_adapter):
        """keys() on None placeholder returns empty list."""
        object_backend.extend([None])
        k = otb_read_adapter.keys(0)
        assert k == []


# ── ObjectToBlobReadWriteAdapter operations ───────────────────────────────


class TestObjectToBlobReadWriteAdapter:
    def test_roundtrip_write_blob_read_blob(self, otb_rw_adapter):
        """Write blob data via adapter, read back as blob, verify correctness."""
        import msgpack
        import msgpack_numpy as m

        blob_row = {
            b"energy": msgpack.packb(-10.5, default=m.encode),
            b"smiles": msgpack.packb("CCO", default=m.encode),
        }
        otb_rw_adapter.extend([blob_row])
        assert len(otb_rw_adapter) == 1
        result = otb_rw_adapter.get(0)
        assert msgpack.unpackb(result[b"energy"], object_hook=m.decode) == pytest.approx(-10.5)
        assert msgpack.unpackb(result[b"smiles"], object_hook=m.decode) == "CCO"

    def test_set_and_get(self, otb_rw_adapter):
        """set() deserializes blob to object, get() serializes back."""
        import msgpack
        import msgpack_numpy as m

        blob_row = {
            b"energy": msgpack.packb(-10.5, default=m.encode),
            b"name": msgpack.packb("water", default=m.encode),
        }
        otb_rw_adapter.set(0, blob_row)
        assert len(otb_rw_adapter) == 1
        result = otb_rw_adapter.get(0)
        assert msgpack.unpackb(result[b"energy"], object_hook=m.decode) == pytest.approx(-10.5)
        assert msgpack.unpackb(result[b"name"], object_hook=m.decode) == "water"

    def test_set_none_placeholder(self, otb_rw_adapter):
        """set() with None creates a placeholder."""
        import msgpack
        import msgpack_numpy as m

        otb_rw_adapter.set(0, {b"x": msgpack.packb(1, default=m.encode)})
        otb_rw_adapter.set(0, None)
        assert otb_rw_adapter.get(0) is None

    def test_extend(self, otb_rw_adapter):
        """extend() appends multiple blob rows."""
        import msgpack
        import msgpack_numpy as m

        rows = [
            {b"val": msgpack.packb(float(i), default=m.encode)}
            for i in range(5)
        ]
        otb_rw_adapter.extend(rows)
        assert len(otb_rw_adapter) == 5
        for i in range(5):
            result = otb_rw_adapter.get(i)
            assert msgpack.unpackb(result[b"val"], object_hook=m.decode) == pytest.approx(float(i))

    def test_extend_with_none(self, otb_rw_adapter):
        """extend() handles None placeholders in the list."""
        import msgpack
        import msgpack_numpy as m

        otb_rw_adapter.extend([
            {b"val": msgpack.packb(1, default=m.encode)},
            None,
            {b"val": msgpack.packb(3, default=m.encode)},
        ])
        assert len(otb_rw_adapter) == 3
        assert otb_rw_adapter.get(0) is not None
        assert otb_rw_adapter.get(1) is None
        assert otb_rw_adapter.get(2) is not None

    def test_insert(self, otb_rw_adapter):
        """insert() shifts rows correctly."""
        import msgpack
        import msgpack_numpy as m

        otb_rw_adapter.extend([
            {b"val": msgpack.packb(1.0, default=m.encode)},
            {b"val": msgpack.packb(3.0, default=m.encode)},
        ])
        otb_rw_adapter.insert(1, {b"val": msgpack.packb(2.0, default=m.encode)})
        assert len(otb_rw_adapter) == 3
        assert msgpack.unpackb(otb_rw_adapter.get(0)[b"val"], object_hook=m.decode) == pytest.approx(1.0)
        assert msgpack.unpackb(otb_rw_adapter.get(1)[b"val"], object_hook=m.decode) == pytest.approx(2.0)
        assert msgpack.unpackb(otb_rw_adapter.get(2)[b"val"], object_hook=m.decode) == pytest.approx(3.0)

    def test_insert_none(self, otb_rw_adapter):
        """insert() with None creates a placeholder."""
        import msgpack
        import msgpack_numpy as m

        otb_rw_adapter.extend([{b"val": msgpack.packb(1, default=m.encode)}])
        otb_rw_adapter.insert(0, None)
        assert len(otb_rw_adapter) == 2
        assert otb_rw_adapter.get(0) is None
        assert otb_rw_adapter.get(1) is not None

    def test_delete(self, otb_rw_adapter):
        """delete() removes and shifts."""
        import msgpack
        import msgpack_numpy as m

        otb_rw_adapter.extend([
            {b"val": msgpack.packb(1.0, default=m.encode)},
            {b"val": msgpack.packb(2.0, default=m.encode)},
            {b"val": msgpack.packb(3.0, default=m.encode)},
        ])
        otb_rw_adapter.delete(1)
        assert len(otb_rw_adapter) == 2
        assert msgpack.unpackb(otb_rw_adapter.get(0)[b"val"], object_hook=m.decode) == pytest.approx(1.0)
        assert msgpack.unpackb(otb_rw_adapter.get(1)[b"val"], object_hook=m.decode) == pytest.approx(3.0)

    def test_update_partial_merge(self, otb_rw_adapter):
        """update() merges new keys into existing row."""
        import msgpack
        import msgpack_numpy as m

        otb_rw_adapter.set(0, {
            b"a": msgpack.packb(1, default=m.encode),
            b"b": msgpack.packb(2, default=m.encode),
        })
        otb_rw_adapter.update(0, {
            b"b": msgpack.packb(99, default=m.encode),
            b"c": msgpack.packb(100, default=m.encode),
        })
        row = otb_rw_adapter.get(0)
        assert msgpack.unpackb(row[b"a"], object_hook=m.decode) == 1
        assert msgpack.unpackb(row[b"b"], object_hook=m.decode) == 99
        assert msgpack.unpackb(row[b"c"], object_hook=m.decode) == 100

    def test_get_with_keys_filter(self, otb_rw_adapter):
        """get() with bytes keys returns only requested fields."""
        import msgpack
        import msgpack_numpy as m

        otb_rw_adapter.set(0, {
            b"a": msgpack.packb(1, default=m.encode),
            b"b": msgpack.packb(2, default=m.encode),
            b"c": msgpack.packb(3, default=m.encode),
        })
        result = otb_rw_adapter.get(0, keys=[b"a", b"c"])
        assert set(result.keys()) == {b"a", b"c"}
        assert msgpack.unpackb(result[b"a"], object_hook=m.decode) == 1
        assert msgpack.unpackb(result[b"c"], object_hook=m.decode) == 3

    def test_get_many_returns_serialized(self, otb_rw_adapter):
        """get_many returns all serialized rows."""
        import msgpack
        import msgpack_numpy as m

        rows = [
            {b"val": msgpack.packb(float(i), default=m.encode)}
            for i in range(5)
        ]
        otb_rw_adapter.extend(rows)
        result = otb_rw_adapter.get_many([1, 3])
        assert len(result) == 2
        assert msgpack.unpackb(result[0][b"val"], object_hook=m.decode) == pytest.approx(1.0)
        assert msgpack.unpackb(result[1][b"val"], object_hook=m.decode) == pytest.approx(3.0)

    def test_keys_returns_bytes(self, otb_rw_adapter):
        """keys() returns bytes keys."""
        import msgpack
        import msgpack_numpy as m

        otb_rw_adapter.set(0, {
            b"alpha": msgpack.packb(1, default=m.encode),
            b"beta": msgpack.packb(2, default=m.encode),
        })
        k = otb_rw_adapter.keys(0)
        assert set(k) == {b"alpha", b"beta"}


# ── ObjectToBlob: roundtrip through object backend ────────────────────────


class TestObjectToBlobRoundtrip:
    """Write object data to object_backend, read through ObjectToBlobReadAdapter."""

    def test_roundtrip_object_to_blob(self, object_backend, otb_read_adapter):
        """Object data written directly is readable as blob data."""
        import msgpack
        import msgpack_numpy as m

        object_backend.extend([{"energy": -10.5, "smiles": "CCO"}])
        result = otb_read_adapter.get(0)
        assert msgpack.unpackb(result[b"energy"], object_hook=m.decode) == pytest.approx(-10.5)
        assert msgpack.unpackb(result[b"smiles"], object_hook=m.decode) == "CCO"

    def test_roundtrip_blob_rw_write_then_read(self, otb_rw_adapter, object_backend):
        """Write via ObjectToBlobReadWriteAdapter, verify object_backend got the right data."""
        import msgpack
        import msgpack_numpy as m

        blob_row = {
            b"energy": msgpack.packb(-42.0, default=m.encode),
            b"name": msgpack.packb("methane", default=m.encode),
        }
        otb_rw_adapter.extend([blob_row])
        # Read from underlying object backend directly
        obj_row = object_backend.get(0)
        assert obj_row["energy"] == pytest.approx(-42.0)
        assert obj_row["name"] == "methane"


# ── ObjectToBlob: numpy array through double conversion ───────────────────


class TestObjectToBlobNumpyDoubleConversion:
    """Numpy arrays survive object -> blob -> object roundtrip."""

    def test_1d_array_through_double_adapter(self, object_backend, otb_read_adapter):
        """1D array written to object backend, read as blob, deserialized back."""
        import msgpack
        import msgpack_numpy as m

        arr = np.array([1.0, 2.0, 3.0])
        object_backend.extend([{"data": arr}])
        blob_row = otb_read_adapter.get(0)
        recovered = msgpack.unpackb(blob_row[b"data"], object_hook=m.decode)
        np.testing.assert_array_equal(recovered, arr)

    def test_2d_array_through_double_adapter(self, object_backend, otb_read_adapter):
        """2D array written to object backend, read as blob, deserialized back."""
        import msgpack
        import msgpack_numpy as m

        arr = np.array([[1, 2], [3, 4], [5, 6]])
        object_backend.extend([{"matrix": arr}])
        blob_row = otb_read_adapter.get(0)
        recovered = msgpack.unpackb(blob_row[b"matrix"], object_hook=m.decode)
        np.testing.assert_array_equal(recovered, arr)

    def test_int_array_preserves_dtype(self, object_backend, otb_read_adapter):
        """int64 array dtype survives the double conversion."""
        import msgpack
        import msgpack_numpy as m

        arr = np.array([1, 6, 8], dtype=np.int64)
        object_backend.extend([{"numbers": arr}])
        blob_row = otb_read_adapter.get(0)
        recovered = msgpack.unpackb(blob_row[b"numbers"], object_hook=m.decode)
        np.testing.assert_array_equal(recovered, arr)
        assert recovered.dtype == np.int64

    def test_numpy_through_rw_adapter(self, otb_rw_adapter):
        """Write blob-encoded numpy via RW adapter, read back and verify."""
        import msgpack
        import msgpack_numpy as m

        arr = np.array([[0.1, 0.2], [0.3, 0.4]])
        blob_row = {
            b"forces": msgpack.packb(arr, default=m.encode),
            b"energy": msgpack.packb(-10.5, default=m.encode),
        }
        otb_rw_adapter.set(0, blob_row)
        result = otb_rw_adapter.get(0)
        recovered_forces = msgpack.unpackb(result[b"forces"], object_hook=m.decode)
        np.testing.assert_array_almost_equal(recovered_forces, arr)
        assert msgpack.unpackb(result[b"energy"], object_hook=m.decode) == pytest.approx(-10.5)
