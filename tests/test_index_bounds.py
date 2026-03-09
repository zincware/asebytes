"""Tests for IndexError on out-of-bounds __getitem__ access.

All 6 facades (BlobIO, ObjectIO, ASEIO + async variants) must raise
IndexError when db[i] is called with i >= len(db) or i < -len(db).
None is reserved strictly for placeholder rows from reserve().

Part 1 uses mock "permissive" backends to prove facade-level enforcement.
Part 2 uses parametrized real backends (lmdb, memory, mongo, redis) for
integration testing.
"""

from __future__ import annotations

import uuid
from typing import Any

import ase
import pytest

from asebytes import ASEIO, BlobIO, ObjectIO
from asebytes._async_blob_io import AsyncBlobIO
from asebytes._async_io import AsyncASEIO
from asebytes._async_object_io import AsyncObjectIO
from asebytes._backends import ReadWriteBackend
from asebytes._async_backends import AsyncReadWriteBackend


# ---------------------------------------------------------------------------
# Mock backend that does NOT raise IndexError on OOB -- returns None
# ---------------------------------------------------------------------------


class _PermissiveBlobBackend(ReadWriteBackend[bytes, bytes]):
    """Backend that raises IndexError for out-of-bounds get()."""

    def __init__(self, rows: list[dict[bytes, bytes] | None] | None = None):
        self._rows: list[dict[bytes, bytes] | None] = rows or []

    @staticmethod
    def list_groups(path: str, **kwargs) -> list[str]:
        return []

    def __len__(self) -> int:
        return len(self._rows)

    def get(self, index: int, keys=None) -> dict[bytes, bytes] | None:
        if 0 <= index < len(self._rows):
            return self._rows[index]
        raise IndexError(index)

    def set(self, index, data):
        self._rows[index] = data

    def delete(self, index):
        del self._rows[index]

    def insert(self, index, data):
        self._rows.insert(index, data)

    def extend(self, data):
        start = len(self._rows)
        self._rows.extend(data)
        return start

    def reserve(self, count):
        self._rows.extend([None] * count)

    def clear(self):
        self._rows.clear()

    def remove(self):
        self._rows.clear()


class _PermissiveObjectBackend(ReadWriteBackend[str, Any]):
    """Backend that raises IndexError for out-of-bounds get()."""

    def __init__(self, rows: list[dict[str, Any] | None] | None = None):
        self._rows: list[dict[str, Any] | None] = rows or []

    @staticmethod
    def list_groups(path: str, **kwargs) -> list[str]:
        return []

    def __len__(self) -> int:
        return len(self._rows)

    def get(self, index: int, keys=None) -> dict[str, Any] | None:
        if 0 <= index < len(self._rows):
            return self._rows[index]
        raise IndexError(index)

    def keys(self, index: int) -> list[str]:
        row = self.get(index)
        return list(row.keys()) if row else []

    def set(self, index, data):
        self._rows[index] = data

    def delete(self, index):
        del self._rows[index]

    def insert(self, index, data):
        self._rows.insert(index, data)

    def extend(self, data):
        start = len(self._rows)
        self._rows.extend(data)
        return start

    def reserve(self, count):
        self._rows.extend([None] * count)

    def clear(self):
        self._rows.clear()

    def remove(self):
        self._rows.clear()


class _PermissiveAsyncBlobBackend(AsyncReadWriteBackend[bytes, bytes]):
    """Async backend that silently returns None for out-of-bounds get()."""

    def __init__(self, rows: list[dict[bytes, bytes] | None] | None = None):
        self._rows: list[dict[bytes, bytes] | None] = rows or []

    @staticmethod
    def list_groups(path: str, **kwargs) -> list[str]:
        return []

    async def len(self) -> int:
        return len(self._rows)

    async def get(self, index: int, keys=None) -> dict[bytes, bytes] | None:
        if 0 <= index < len(self._rows):
            return self._rows[index]
        raise IndexError(index)

    async def set(self, index, data):
        self._rows[index] = data

    async def delete(self, index):
        del self._rows[index]

    async def insert(self, index, data):
        self._rows.insert(index, data)

    async def extend(self, data):
        start = len(self._rows)
        self._rows.extend(data)
        return start

    async def reserve(self, count):
        self._rows.extend([None] * count)

    async def clear(self):
        self._rows.clear()

    async def remove(self):
        self._rows.clear()


class _PermissiveAsyncObjectBackend(AsyncReadWriteBackend[str, Any]):
    """Async backend that silently returns None for out-of-bounds get()."""

    def __init__(self, rows: list[dict[str, Any] | None] | None = None):
        self._rows: list[dict[str, Any] | None] = rows or []

    @staticmethod
    def list_groups(path: str, **kwargs) -> list[str]:
        return []

    async def len(self) -> int:
        return len(self._rows)

    async def get(self, index: int, keys=None) -> dict[str, Any] | None:
        if 0 <= index < len(self._rows):
            return self._rows[index]
        raise IndexError(index)

    async def keys(self, index: int) -> list[str]:
        row = await self.get(index)
        return list(row.keys()) if row else []

    async def set(self, index, data):
        self._rows[index] = data

    async def delete(self, index):
        del self._rows[index]

    async def insert(self, index, data):
        self._rows.insert(index, data)

    async def extend(self, data):
        start = len(self._rows)
        self._rows.extend(data)
        return start

    async def reserve(self, count):
        self._rows.extend([None] * count)

    async def clear(self):
        self._rows.clear()

    async def remove(self):
        self._rows.clear()


# ===========================================================================
# Sync facades -- mock backends (facade-level bounds enforcement)
# ===========================================================================


class TestBlobIOBoundsFacade:
    """BlobIO facade-level bounds checking with a permissive backend."""

    def _make(self, n: int = 2) -> BlobIO:
        rows = [{b"k": f"v{i}".encode()} for i in range(n)]
        return BlobIO(backend=_PermissiveBlobBackend(rows))

    def test_valid_positive_index(self):
        db = self._make(2)
        assert db[0] is not None
        assert db[1] is not None

    def test_valid_negative_index(self):
        db = self._make(2)
        assert db[-1] is not None
        assert db[-2] is not None

    def test_upper_bound_exact(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            db[2]

    def test_upper_bound_far(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            db[100]

    def test_lower_bound(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            db[-3]

    def test_empty_db(self):
        db = self._make(0)
        with pytest.raises(IndexError):
            db[0]

    def test_reserve_placeholder_returns_none(self):
        db = self._make(1)
        db.reserve(2)
        assert len(db) == 3
        # Placeholder rows via .get() return None (bypasses __getitem__)
        assert db.get(1) is None
        assert db.get(2) is None


class TestObjectIOBoundsFacade:
    """ObjectIO facade-level bounds checking with a permissive backend."""

    def _make(self, n: int = 2) -> ObjectIO:
        rows = [{"k": f"v{i}"} for i in range(n)]
        return ObjectIO(backend=_PermissiveObjectBackend(rows))

    def test_valid_positive_index(self):
        db = self._make(2)
        assert db[0] is not None
        assert db[1] is not None

    def test_valid_negative_index(self):
        db = self._make(2)
        assert db[-1] is not None
        assert db[-2] is not None

    def test_upper_bound_exact(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            db[2]

    def test_upper_bound_far(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            db[100]

    def test_lower_bound(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            db[-3]

    def test_empty_db(self):
        db = self._make(0)
        with pytest.raises(IndexError):
            db[0]

    def test_reserve_placeholder_returns_none(self):
        db = self._make(1)
        db.reserve(2)
        assert len(db) == 3
        assert db.get(1) is None
        assert db.get(2) is None


class TestASEIOBoundsFacade:
    """ASEIO facade-level bounds checking with a permissive backend.

    ASEIO wraps an object-level backend so we use _PermissiveObjectBackend.
    We store atoms_to_dict(simple_atoms) dicts so dict_to_atoms succeeds.
    """

    @staticmethod
    def _atoms_dict() -> dict[str, Any]:
        """Minimal dict that dict_to_atoms can reconstruct."""
        from asebytes._convert import atoms_to_dict
        return atoms_to_dict(ase.Atoms("H", positions=[[0, 0, 0]]))

    def _make(self, n: int = 2) -> ASEIO:
        rows = [self._atoms_dict() for _ in range(n)]
        return ASEIO(backend=_PermissiveObjectBackend(rows))

    def test_valid_positive_index(self):
        db = self._make(2)
        assert db[0] is not None
        assert db[1] is not None

    def test_valid_negative_index(self):
        db = self._make(2)
        assert db[-1] is not None
        assert db[-2] is not None

    def test_upper_bound_exact(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            db[2]

    def test_upper_bound_far(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            db[100]

    def test_lower_bound(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            db[-3]

    def test_empty_db(self):
        db = self._make(0)
        with pytest.raises(IndexError):
            db[0]

    def test_reserve_placeholder_returns_none(self):
        db = self._make(1)
        db.reserve(2)
        assert len(db) == 3
        assert db.get(1) is None
        assert db.get(2) is None


# ===========================================================================
# Async facades -- mock backends (facade-level bounds enforcement)
# ===========================================================================


class TestAsyncBlobIOBoundsFacade:
    """AsyncBlobIO facade-level bounds checking with a permissive backend."""

    def _make(self, n: int = 2) -> AsyncBlobIO:
        rows = [{b"k": f"v{i}".encode()} for i in range(n)]
        return AsyncBlobIO(backend=_PermissiveAsyncBlobBackend(rows))

    @pytest.mark.anyio
    async def test_valid_positive_index(self):
        db = self._make(2)
        assert await db[0] is not None
        assert await db[1] is not None

    @pytest.mark.anyio
    async def test_valid_negative_index(self):
        db = self._make(2)
        assert await db[-1] is not None
        assert await db[-2] is not None

    @pytest.mark.anyio
    async def test_upper_bound_exact(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            await db[2]

    @pytest.mark.anyio
    async def test_upper_bound_far(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            await db[100]

    @pytest.mark.anyio
    async def test_lower_bound(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            await db[-3]

    @pytest.mark.anyio
    async def test_empty_db(self):
        db = self._make(0)
        with pytest.raises(IndexError):
            await db[0]

    @pytest.mark.anyio
    async def test_reserve_placeholder_returns_none(self):
        db = self._make(1)
        await db.reserve(2)
        assert await db.len() == 3
        assert await db.get(1) is None
        assert await db.get(2) is None


class TestAsyncObjectIOBoundsFacade:
    """AsyncObjectIO facade-level bounds checking with a permissive backend."""

    def _make(self, n: int = 2) -> AsyncObjectIO:
        rows = [{"k": f"v{i}"} for i in range(n)]
        return AsyncObjectIO(backend=_PermissiveAsyncObjectBackend(rows))

    @pytest.mark.anyio
    async def test_valid_positive_index(self):
        db = self._make(2)
        assert await db[0] is not None
        assert await db[1] is not None

    @pytest.mark.anyio
    async def test_valid_negative_index(self):
        db = self._make(2)
        assert await db[-1] is not None
        assert await db[-2] is not None

    @pytest.mark.anyio
    async def test_upper_bound_exact(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            await db[2]

    @pytest.mark.anyio
    async def test_upper_bound_far(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            await db[100]

    @pytest.mark.anyio
    async def test_lower_bound(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            await db[-3]

    @pytest.mark.anyio
    async def test_empty_db(self):
        db = self._make(0)
        with pytest.raises(IndexError):
            await db[0]

    @pytest.mark.anyio
    async def test_reserve_placeholder_returns_none(self):
        db = self._make(1)
        await db.reserve(2)
        assert await db.len() == 3
        assert await db.get(1) is None
        assert await db.get(2) is None


class TestAsyncASEIOBoundsFacade:
    """AsyncASEIO facade-level bounds checking with a permissive backend."""

    @staticmethod
    def _atoms_dict() -> dict[str, Any]:
        from asebytes._convert import atoms_to_dict
        return atoms_to_dict(ase.Atoms("H", positions=[[0, 0, 0]]))

    def _make(self, n: int = 2) -> AsyncASEIO:
        rows = [self._atoms_dict() for _ in range(n)]
        return AsyncASEIO(backend=_PermissiveAsyncObjectBackend(rows))

    @pytest.mark.anyio
    async def test_valid_positive_index(self):
        db = self._make(2)
        assert await db[0] is not None
        assert await db[1] is not None

    @pytest.mark.anyio
    async def test_valid_negative_index(self):
        db = self._make(2)
        assert await db[-1] is not None
        assert await db[-2] is not None

    @pytest.mark.anyio
    async def test_upper_bound_exact(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            await db[2]

    @pytest.mark.anyio
    async def test_upper_bound_far(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            await db[100]

    @pytest.mark.anyio
    async def test_lower_bound(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            await db[-3]

    @pytest.mark.anyio
    async def test_empty_db(self):
        db = self._make(0)
        with pytest.raises(IndexError):
            await db[0]

    @pytest.mark.anyio
    async def test_reserve_placeholder_returns_none(self):
        db = self._make(1)
        await db.reserve(2)
        assert await db.len() == 3
        assert await db.get(1) is None
        assert await db.get(2) is None


# ===========================================================================
# Real-backend integration tests — parametrized across backends
# ===========================================================================

from asebytes.lmdb import LMDBObjectBackend
from asebytes.memory._backend import MemoryObjectBackend
from asebytes.mongodb import AsyncMongoObjectBackend, MongoObjectBackend


# -- BlobIO factory helpers (only LMDB supports native blob) ----------------

def _blob_lmdb(tmp_path, **_kw):
    return BlobIO(str(tmp_path / f"bounds_blob_{uuid.uuid4().hex[:8]}.lmdb"))


@pytest.fixture(params=[_blob_lmdb], ids=["lmdb"])
def blob_io(tmp_path, request):
    """BlobIO instance across available blob backends."""
    return request.param(tmp_path)


# -- ObjectIO factory helpers -----------------------------------------------

def _obj_lmdb(tmp_path, **_kw):
    return ObjectIO(LMDBObjectBackend(str(tmp_path / f"bounds_{uuid.uuid4().hex[:8]}.lmdb")))


def _obj_memory(tmp_path, **_kw):
    return ObjectIO(MemoryObjectBackend(group=f"bounds_{uuid.uuid4().hex[:8]}"))


def _obj_mongo(tmp_path, *, mongo_uri, **_kw):
    return ObjectIO(
        MongoObjectBackend(
            uri=mongo_uri, database="asebytes_test",
            group=f"bounds_{uuid.uuid4().hex[:8]}",
        )
    )


def _obj_redis(tmp_path, *, redis_uri, **_kw):
    return ObjectIO(redis_uri, group=f"bounds_{uuid.uuid4().hex[:8]}")


@pytest.fixture(
    params=[_obj_lmdb, _obj_memory, _obj_mongo, _obj_redis],
    ids=["lmdb", "memory", "mongo", "redis"],
)
def object_io(tmp_path, mongo_uri, redis_uri, request):
    """ObjectIO instance across all available backends."""
    return request.param(tmp_path, mongo_uri=mongo_uri, redis_uri=redis_uri)


# -- ASEIO factory helpers --------------------------------------------------

def _ase_lmdb(tmp_path, **_kw):
    return ASEIO(str(tmp_path / f"bounds_ase_{uuid.uuid4().hex[:8]}.lmdb"))


def _ase_memory(tmp_path, **_kw):
    return ASEIO(MemoryObjectBackend(group=f"bounds_ase_{uuid.uuid4().hex[:8]}"))


def _ase_mongo(tmp_path, *, mongo_uri, **_kw):
    return ASEIO(
        MongoObjectBackend(
            uri=mongo_uri, database="asebytes_test",
            group=f"bounds_ase_{uuid.uuid4().hex[:8]}",
        )
    )


def _ase_redis(tmp_path, *, redis_uri, **_kw):
    return ASEIO(redis_uri, group=f"bounds_ase_{uuid.uuid4().hex[:8]}")


@pytest.fixture(
    params=[_ase_lmdb, _ase_memory, _ase_mongo, _ase_redis],
    ids=["lmdb", "memory", "mongo", "redis"],
)
def ase_io(tmp_path, mongo_uri, redis_uri, request):
    """ASEIO instance across all available backends."""
    return request.param(tmp_path, mongo_uri=mongo_uri, redis_uri=redis_uri)


# -- AsyncObjectIO factory helpers ------------------------------------------

def _async_obj_lmdb(tmp_path, **_kw):
    return AsyncObjectIO(str(tmp_path / f"bounds_async_{uuid.uuid4().hex[:8]}.lmdb"))


def _async_obj_memory(tmp_path, **_kw):
    return AsyncObjectIO("memory://", group=f"bounds_async_{uuid.uuid4().hex[:8]}")


def _async_obj_mongo(tmp_path, *, mongo_uri, **_kw):
    return AsyncObjectIO(
        AsyncMongoObjectBackend(
            uri=mongo_uri, database="asebytes_test",
            group=f"bounds_async_{uuid.uuid4().hex[:8]}",
        )
    )


def _async_obj_redis(tmp_path, *, redis_uri, **_kw):
    return AsyncObjectIO(redis_uri, group=f"bounds_async_{uuid.uuid4().hex[:8]}")


@pytest.fixture(
    params=[_async_obj_lmdb, _async_obj_memory, _async_obj_mongo, _async_obj_redis],
    ids=["lmdb", "memory", "mongo", "redis"],
)
def async_object_io(tmp_path, mongo_uri, redis_uri, request):
    """AsyncObjectIO instance across all available backends."""
    return request.param(tmp_path, mongo_uri=mongo_uri, redis_uri=redis_uri)


# ===========================================================================
# BlobIO integration tests
# ===========================================================================


class TestBlobIOBoundsIntegration:
    """BlobIO bounds checking with real backends."""

    def test_valid_positive_index(self, blob_io):
        blob_io.extend([{b"k": b"v0"}, {b"k": b"v1"}])
        assert blob_io[0] is not None
        assert blob_io[1] is not None

    def test_valid_negative_index(self, blob_io):
        blob_io.extend([{b"k": b"v0"}, {b"k": b"v1"}])
        assert blob_io[-1] is not None
        assert blob_io[-2] is not None

    def test_upper_bound_exact(self, blob_io):
        blob_io.extend([{b"k": b"v0"}, {b"k": b"v1"}])
        with pytest.raises(IndexError):
            blob_io[2]

    def test_upper_bound_far(self, blob_io):
        blob_io.extend([{b"k": b"v0"}, {b"k": b"v1"}])
        with pytest.raises(IndexError):
            blob_io[100]

    def test_lower_bound(self, blob_io):
        blob_io.extend([{b"k": b"v0"}, {b"k": b"v1"}])
        with pytest.raises(IndexError):
            blob_io[-3]

    def test_empty_db(self, blob_io):
        with pytest.raises(IndexError):
            blob_io[0]

    def test_reserve_placeholder_returns_none(self, blob_io):
        blob_io.extend([{b"k": b"v0"}])
        blob_io.reserve(2)
        assert len(blob_io) == 3
        assert blob_io.get(1) is None
        assert blob_io.get(2) is None


# ===========================================================================
# ObjectIO integration tests (parametrized: lmdb, memory, mongo, redis)
# ===========================================================================


class TestObjectIOBoundsIntegration:
    """ObjectIO bounds checking across all backends."""

    def test_valid_positive_index(self, object_io):
        object_io.extend([{"k": "v0"}, {"k": "v1"}])
        assert object_io[0] is not None
        assert object_io[1] is not None

    def test_valid_negative_index(self, object_io):
        object_io.extend([{"k": "v0"}, {"k": "v1"}])
        assert object_io[-1] is not None
        assert object_io[-2] is not None

    def test_upper_bound_exact(self, object_io):
        object_io.extend([{"k": "v0"}, {"k": "v1"}])
        with pytest.raises(IndexError):
            object_io[2]

    def test_upper_bound_far(self, object_io):
        object_io.extend([{"k": "v0"}, {"k": "v1"}])
        with pytest.raises(IndexError):
            object_io[100]

    def test_lower_bound(self, object_io):
        object_io.extend([{"k": "v0"}, {"k": "v1"}])
        with pytest.raises(IndexError):
            object_io[-3]

    def test_empty_db(self, object_io):
        with pytest.raises(IndexError):
            object_io[0]

    def test_reserve_placeholder_returns_none(self, object_io):
        object_io.extend([{"k": "v0"}])
        object_io.reserve(2)
        assert len(object_io) == 3
        assert object_io.get(1) is None
        assert object_io.get(2) is None


# ===========================================================================
# ASEIO integration tests (parametrized: lmdb, memory, mongo, redis)
# ===========================================================================


class TestASEIOBoundsIntegration:
    """ASEIO bounds checking across all backends."""

    def test_valid_positive_index(self, ase_io, simple_atoms):
        ase_io.extend([simple_atoms, simple_atoms])
        assert ase_io[0] is not None
        assert ase_io[1] is not None

    def test_valid_negative_index(self, ase_io, simple_atoms):
        ase_io.extend([simple_atoms, simple_atoms])
        assert ase_io[-1] is not None
        assert ase_io[-2] is not None

    def test_upper_bound_exact(self, ase_io, simple_atoms):
        ase_io.extend([simple_atoms, simple_atoms])
        with pytest.raises(IndexError):
            ase_io[2]

    def test_lower_bound(self, ase_io, simple_atoms):
        ase_io.extend([simple_atoms, simple_atoms])
        with pytest.raises(IndexError):
            ase_io[-3]

    def test_empty_db(self, ase_io):
        with pytest.raises(IndexError):
            ase_io[0]

    def test_reserve_placeholder_returns_none(self, ase_io, simple_atoms):
        ase_io.extend([simple_atoms])
        ase_io.reserve(2)
        assert len(ase_io) == 3
        assert ase_io.get(1) is None
        assert ase_io.get(2) is None


# ===========================================================================
# AsyncObjectIO integration tests (parametrized: lmdb, memory, mongo, redis)
# ===========================================================================


class TestAsyncObjectIOBoundsIntegration:
    """AsyncObjectIO bounds checking across all backends."""

    @pytest.mark.anyio
    async def test_valid_positive_index(self, async_object_io):
        await async_object_io.extend([{"k": "v0"}, {"k": "v1"}])
        assert await async_object_io[0] is not None
        assert await async_object_io[1] is not None

    @pytest.mark.anyio
    async def test_valid_negative_index(self, async_object_io):
        await async_object_io.extend([{"k": "v0"}, {"k": "v1"}])
        assert await async_object_io[-1] is not None
        assert await async_object_io[-2] is not None

    @pytest.mark.anyio
    async def test_upper_bound_exact(self, async_object_io):
        await async_object_io.extend([{"k": "v0"}, {"k": "v1"}])
        with pytest.raises(IndexError):
            await async_object_io[2]

    @pytest.mark.anyio
    async def test_upper_bound_far(self, async_object_io):
        await async_object_io.extend([{"k": "v0"}, {"k": "v1"}])
        with pytest.raises(IndexError):
            await async_object_io[100]

    @pytest.mark.anyio
    async def test_lower_bound(self, async_object_io):
        await async_object_io.extend([{"k": "v0"}, {"k": "v1"}])
        with pytest.raises(IndexError):
            await async_object_io[-3]

    @pytest.mark.anyio
    async def test_empty_db(self, async_object_io):
        with pytest.raises(IndexError):
            await async_object_io[0]
