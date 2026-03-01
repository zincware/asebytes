"""ObjectIO / AsyncObjectIO: interleaved None placeholders + IndexError.

Verifies that for db = [data, None, data2]:
  db[0] == data
  db[1] is None
  db[2] == data2
  db[3] -> IndexError
"""

from __future__ import annotations

import uuid

import pytest

from asebytes._object_io import ObjectIO
from asebytes._async_object_io import AsyncObjectIO
from asebytes.lmdb import LMDBObjectBackend
from asebytes.memory._backend import MemoryObjectBackend
from asebytes.mongodb import AsyncMongoObjectBackend, MongoObjectBackend

ROW_A = {"x": 1, "tag": "a"}
ROW_B = {"x": 2, "tag": "b"}


def _lmdb(tmp_path, **_kw):
    return ObjectIO(LMDBObjectBackend(str(tmp_path / "test.lmdb")))


def _memory(tmp_path, **_kw):
    return ObjectIO(MemoryObjectBackend(group=f"test_{uuid.uuid4().hex[:8]}"))


def _mongo(tmp_path, *, mongo_uri, **_kw):
    return ObjectIO(
        MongoObjectBackend(
            uri=mongo_uri, database="asebytes_test",
            group=f"test_{uuid.uuid4().hex[:8]}",
        )
    )


def _redis(tmp_path, *, redis_uri, **_kw):
    return ObjectIO(redis_uri, group=f"test_{uuid.uuid4().hex[:8]}")


@pytest.fixture(
    params=[_lmdb, _memory, _mongo, _redis],
    ids=["lmdb", "memory", "mongo", "redis"],
)
def sync_io(tmp_path, mongo_uri, redis_uri, request):
    return request.param(tmp_path, mongo_uri=mongo_uri, redis_uri=redis_uri)


def _async_lmdb(tmp_path, **_kw):
    return AsyncObjectIO(str(tmp_path / "test.lmdb"))


def _async_memory(tmp_path, **_kw):
    return AsyncObjectIO("memory://", group=f"test_{uuid.uuid4().hex[:8]}")


def _async_mongo(tmp_path, *, mongo_uri, **_kw):
    return AsyncObjectIO(
        AsyncMongoObjectBackend(
            uri=mongo_uri, database="asebytes_test",
            group=f"test_async_{uuid.uuid4().hex[:8]}",
        )
    )


def _async_redis(tmp_path, *, redis_uri, **_kw):
    return AsyncObjectIO(redis_uri, group=f"test_async_{uuid.uuid4().hex[:8]}")


@pytest.fixture(
    params=[_async_lmdb, _async_memory, _async_mongo, _async_redis],
    ids=["lmdb", "memory", "mongo", "redis"],
)
def async_io(tmp_path, mongo_uri, redis_uri, request):
    return request.param(tmp_path, mongo_uri=mongo_uri, redis_uri=redis_uri)


# ======================================================================
# Sync
# ======================================================================


class TestSyncNoneIndexing:
    def test_interleaved_none(self, sync_io):
        sync_io.extend([ROW_A, None, ROW_B])

        assert sync_io[0] == ROW_A
        assert sync_io[1] is None
        assert sync_io[2] == ROW_B

        with pytest.raises(IndexError):
            sync_io[3]

    def test_negative_index(self, sync_io):
        sync_io.extend([ROW_A, None, ROW_B])

        assert sync_io[-1] == ROW_B
        assert sync_io[-2] is None
        assert sync_io[-3] == ROW_A

        with pytest.raises(IndexError):
            sync_io[-4]

    def test_column_view(self, sync_io):
        sync_io.extend([ROW_A, None, ROW_B])

        assert sync_io["tag"].to_list() == ["a", None, "b"]
        assert sync_io["x"].to_list() == [1, None, 2]

    def test_row_view_slice(self, sync_io):
        sync_io.extend([ROW_A, None, ROW_B])

        assert list(sync_io[:]) == [ROW_A, None, ROW_B]

    def test_column_view_index_error(self, sync_io):
        sync_io.extend([ROW_A, None, ROW_B])

        with pytest.raises(IndexError):
            sync_io["tag"][3]

        with pytest.raises(IndexError):
            sync_io["tag"][-4]

    def test_column_view_keyerror(self, sync_io):
        sync_io.extend([ROW_A, None, ROW_B])

        with pytest.raises(KeyError):
            sync_io["nonexistent"].to_list()


class TestSyncAllNone:
    """db = [None, None, None] — all placeholders."""

    def test_all_none_access(self, sync_io):
        sync_io.extend([None, None, None])

        assert sync_io[0] is None
        assert sync_io[1] is None
        assert sync_io[2] is None

        with pytest.raises(IndexError):
            sync_io[3]

    def test_all_none_row_view_slice(self, sync_io):
        sync_io.extend([None, None, None])

        assert list(sync_io[:]) == [None, None, None]

    def test_all_none_keyerror(self, sync_io):
        """All rows are None placeholders — no column exists."""
        sync_io.extend([None, None, None])

        with pytest.raises(KeyError):
            sync_io["nonexistent"].to_list()

        with pytest.raises(KeyError):
            sync_io[:]["nonexistent"].to_list()


# ======================================================================
# Async
# ======================================================================


class TestAsyncNoneIndexing:
    @pytest.mark.anyio
    async def test_interleaved_none(self, async_io):
        await async_io.extend([ROW_A, None, ROW_B])

        assert await async_io[0] == ROW_A
        assert await async_io[1] is None
        assert await async_io[2] == ROW_B

        with pytest.raises(IndexError):
            await async_io[3]

    @pytest.mark.anyio
    async def test_negative_index(self, async_io):
        await async_io.extend([ROW_A, None, ROW_B])

        assert await async_io[-1] == ROW_B
        assert await async_io[-2] is None
        assert await async_io[-3] == ROW_A

        with pytest.raises(IndexError):
            await async_io[-4]

    @pytest.mark.anyio
    async def test_column_view(self, async_io):
        await async_io.extend([ROW_A, None, ROW_B])

        assert await async_io["tag"].to_list() == ["a", None, "b"]
        assert await async_io["x"].to_list() == [1, None, 2]

    @pytest.mark.anyio
    async def test_row_view_slice(self, async_io):
        await async_io.extend([ROW_A, None, ROW_B])

        assert await async_io[:].to_list() == [ROW_A, None, ROW_B]

    @pytest.mark.anyio
    async def test_column_view_keyerror(self, async_io):
        await async_io.extend([ROW_A, None, ROW_B])

        with pytest.raises(KeyError):
            await async_io["nonexistent"].to_list()

    @pytest.mark.anyio
    async def test_column_view_index_error(self, async_io):
        await async_io.extend([ROW_A, None, ROW_B])

        with pytest.raises(IndexError):
            await async_io["tag"][3]

        with pytest.raises(IndexError):
            await async_io["tag"][-4]


class TestAsyncAllNone:
    """db = [None, None, None] — all placeholders."""

    @pytest.mark.anyio
    async def test_all_none_access(self, async_io):
        await async_io.extend([None, None, None])

        assert await async_io[0] is None
        assert await async_io[1] is None
        assert await async_io[2] is None

        with pytest.raises(IndexError):
            await async_io[3]

    @pytest.mark.anyio
    async def test_all_none_row_view_slice(self, async_io):
        await async_io.extend([None, None, None])

        assert await async_io[:].to_list() == [None, None, None]

    @pytest.mark.anyio
    async def test_all_none_keyerror(self, async_io):
        """All rows are None placeholders — no column exists."""
        await async_io.extend([None, None, None])

        with pytest.raises(KeyError):
            await async_io["x"].to_list()

        with pytest.raises(KeyError):
            await async_io["nonexistent"].to_list()
