"""ObjectIO / AsyncObjectIO: interleaved None placeholders + IndexError.

Verifies that for db = [data, None, data2]:
  db[0] == data
  db[1] is None
  db[2] == data2
  db[3] -> IndexError
"""

from __future__ import annotations

import os
import uuid

import pytest

from asebytes._object_io import ObjectIO
from asebytes._async_object_io import AsyncObjectIO
from asebytes.lmdb import LMDBObjectBackend
from asebytes.memory._backend import MemoryObjectBackend
from asebytes.mongodb import AsyncMongoObjectBackend, MongoObjectBackend

ROW_A = {"x": 1, "tag": "a"}
ROW_B = {"x": 2, "tag": "b"}

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://root:example@localhost:27017")
REDIS_URI = os.environ.get("REDIS_URI", "redis://localhost:6379")


def _lmdb(tmp_path):
    return ObjectIO(LMDBObjectBackend(str(tmp_path / "test.lmdb")))


def _memory(tmp_path):
    return ObjectIO(MemoryObjectBackend(group=f"test_{uuid.uuid4().hex[:8]}"))


def _mongo(tmp_path):
    return ObjectIO(
        MongoObjectBackend(
            uri=MONGO_URI, database="asebytes_test",
            group=f"test_{uuid.uuid4().hex[:8]}",
        )
    )


def _redis(tmp_path):
    return ObjectIO(REDIS_URI, group=f"test_{uuid.uuid4().hex[:8]}")


@pytest.fixture(
    params=[_lmdb, _memory, _mongo, _redis],
    ids=["lmdb", "memory", "mongo", "redis"],
)
def sync_io(tmp_path, request):
    return request.param(tmp_path)


def _async_lmdb(tmp_path):
    return AsyncObjectIO(str(tmp_path / "test.lmdb"))


def _async_memory(tmp_path):
    return AsyncObjectIO("memory://", group=f"test_{uuid.uuid4().hex[:8]}")


def _async_mongo(tmp_path):
    return AsyncObjectIO(
        AsyncMongoObjectBackend(
            uri=MONGO_URI, database="asebytes_test",
            group=f"test_async_{uuid.uuid4().hex[:8]}",
        )
    )


def _async_redis(tmp_path):
    return AsyncObjectIO(REDIS_URI, group=f"test_async_{uuid.uuid4().hex[:8]}")


@pytest.fixture(
    params=[_async_lmdb, _async_memory, _async_mongo, _async_redis],
    ids=["lmdb", "memory", "mongo", "redis"],
)
def async_io(tmp_path, request):
    return request.param(tmp_path)


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
