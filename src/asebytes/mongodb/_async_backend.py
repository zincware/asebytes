from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from pymongo import AsyncMongoClient

from .._async_backends import AsyncReadWriteBackend
from ._backend import _bson_safe

META_ID = "__meta__"


class AsyncMongoObjectBackend(AsyncReadWriteBackend[str, Any]):
    """Async MongoDB-backed read-write backend for object dictionaries.

    Uses ``pymongo.AsyncMongoClient`` (GA since PyMongo 4.13) for native
    non-blocking I/O.  Same sort-key array design as :class:`MongoObjectBackend`.

    Parameters
    ----------
    uri : str
        MongoDB connection URI.
    database : str
        Database name.
    collection : str
        Collection name (one collection = one dataset).
    """

    def __init__(
        self,
        uri: str = "mongodb://localhost:27017",
        database: str = "asebytes",
        collection: str = "default",
    ):
        self._client = AsyncMongoClient(uri)
        self._col = self._client[database][collection]
        self._sort_keys: list[int] | None = None
        self._count: int | None = None

    @classmethod
    def from_uri(cls, uri: str, **kwargs) -> AsyncMongoObjectBackend:
        """Construct from a URI like ``mongodb://host:port/database/collection``."""
        if "://" not in uri:
            raise ValueError(f"Invalid URI: {uri!r}")
        _, after_scheme = uri.split("://", 1)
        if "/" in after_scheme:
            host_part, path_part = after_scheme.split("/", 1)
        else:
            host_part, path_part = after_scheme, ""

        parts = [p for p in path_part.split("/") if p]
        if len(parts) >= 2:
            database = parts[0]
            collection = parts[1]
            connection_uri = uri.split("://")[0] + "://" + host_part
        elif len(parts) == 1:
            database = parts[0]
            collection = "default"
            connection_uri = uri.split("://")[0] + "://" + host_part
        else:
            database = "asebytes"
            collection = "default"
            connection_uri = uri

        return cls(
            uri=connection_uri, database=database, collection=collection, **kwargs
        )

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------

    def _invalidate_cache(self) -> None:
        self._sort_keys = None
        self._count = None

    async def _ensure_cache(self) -> None:
        if self._sort_keys is not None:
            return
        meta = await self._col.find_one({"_id": META_ID})
        if meta is None:
            self._sort_keys = []
            self._count = 0
        else:
            self._sort_keys = meta.get("sort_keys", [])
            self._count = meta.get("count", len(self._sort_keys))

    def _resolve_sort_key(self, index: int) -> int:
        n = len(self._sort_keys)
        if index < 0:
            index += n
        if index < 0 or index >= n:
            raise IndexError(index)
        return self._sort_keys[index]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _doc_to_row(self, doc: dict | None) -> dict[str, Any] | None:
        if doc is None:
            return None
        data = doc.get("data")
        if data is None:
            return None
        return dict(data)

    def _row_to_doc(self, sort_key: int, data: dict[str, Any] | None) -> dict:
        if data is not None:
            data = {k: _bson_safe(v) for k, v in data.items()}
        return {"_id": sort_key, "data": data}

    def _projection(self, keys: list[str] | None) -> dict | None:
        if keys is None:
            return None
        return {f"data.{k}": 1 for k in keys}

    # ------------------------------------------------------------------
    # AsyncReadBackend implementation
    # ------------------------------------------------------------------

    async def len(self) -> int:
        await self._ensure_cache()
        return self._count

    async def get(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any] | None:
        await self._ensure_cache()
        sk = self._resolve_sort_key(index)
        doc = await self._col.find_one({"_id": sk}, self._projection(keys))
        return self._doc_to_row(doc)

    async def get_many(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any] | None]:
        await self._ensure_cache()
        sks = [self._resolve_sort_key(i) for i in indices]
        proj = self._projection(keys)
        docs = {}
        async for doc in self._col.find({"_id": {"$in": sks}}, proj):
            docs[doc["_id"]] = doc
        return [self._doc_to_row(docs.get(sk)) for sk in sks]

    async def iter_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> AsyncIterator[dict[str, Any] | None]:
        """Yield rows one at a time, backed by a batched get_many."""
        for row in await self.get_many(indices, keys):
            yield row

    async def get_column(self, key: str, indices: list[int] | None = None) -> list[Any]:
        await self._ensure_cache()
        if indices is None:
            indices = list(range(self._count))
        sks = [self._resolve_sort_key(i) for i in indices]
        proj = {f"data.{key}": 1}
        docs = {}
        async for doc in self._col.find({"_id": {"$in": sks}}, proj):
            docs[doc["_id"]] = doc
        results = []
        for sk in sks:
            doc = docs.get(sk)
            if doc is not None and doc.get("data") is not None:
                results.append(doc["data"].get(key))
            else:
                results.append(None)
        return results

    # ------------------------------------------------------------------
    # AsyncReadWriteBackend implementation
    # ------------------------------------------------------------------

    async def set(self, index: int, data: dict[str, Any] | None) -> None:
        await self._ensure_cache()
        n = len(self._sort_keys)
        if index < 0:
            index += n
        if index < 0 or index >= n:
            raise IndexError(index)
        sk = self._sort_keys[index]
        await self._col.replace_one(
            {"_id": sk}, self._row_to_doc(sk, data), upsert=True
        )
        self._invalidate_cache()

    async def delete(self, index: int) -> None:
        await self._ensure_cache()
        sk = self._resolve_sort_key(index)
        n = len(self._sort_keys)
        pos = index if index >= 0 else index + n
        await self._col.delete_one({"_id": sk})
        self._sort_keys.pop(pos)
        self._count -= 1
        await self._col.update_one(
            {"_id": META_ID},
            {
                "$set": {
                    "sort_keys": self._sort_keys,
                    "count": self._count,
                },
            },
        )

    async def extend(self, values: list[dict[str, Any] | None]) -> int:
        if not values:
            return self._count if self._count is not None else await self.len()
        await self._ensure_cache()

        # Atomically allocate sort keys using find_one_and_update with $inc
        # This prevents race conditions where concurrent extend() calls
        # could read the same next_sort_key and create duplicate _id values
        from pymongo import ReturnDocument

        num_values = len(values)
        meta = await self._col.find_one_and_update(
            {"_id": META_ID},
            {"$inc": {"next_sort_key": num_values}},
            upsert=True,
            return_document=ReturnDocument.BEFORE,
        )
        next_sk = meta.get("next_sort_key", 0) if meta else 0
        new_sks = list(range(next_sk, next_sk + num_values))

        docs = [self._row_to_doc(sk, v) for sk, v in zip(new_sks, values)]
        await self._col.insert_many(docs)

        self._sort_keys.extend(new_sks)
        self._count += num_values
        await self._col.update_one(
            {"_id": META_ID},
            {
                "$push": {"sort_keys": {"$each": new_sks}},
                "$set": {"count": self._count},
            },
        )
        return self._count

    async def insert(self, index: int, value: dict[str, Any] | None) -> None:
        await self._ensure_cache()
        n = len(self._sort_keys)
        if index < 0:
            index = 0
        if index > n:
            index = n

        # Atomically allocate a single sort key using find_one_and_update with $inc
        # This prevents race conditions where concurrent insert() calls
        # could read the same next_sort_key and create duplicate _id values
        from pymongo import ReturnDocument

        meta = await self._col.find_one_and_update(
            {"_id": META_ID},
            {"$inc": {"next_sort_key": 1}},
            upsert=True,
            return_document=ReturnDocument.BEFORE,
        )
        next_sk = meta.get("next_sort_key", 0) if meta else 0

        await self._col.insert_one(self._row_to_doc(next_sk, value))

        self._sort_keys.insert(index, next_sk)
        self._count += 1
        await self._col.update_one(
            {"_id": META_ID},
            {
                "$set": {
                    "sort_keys": self._sort_keys,
                    "count": self._count,
                },
            },
        )

    async def update(self, index: int, data: dict[str, Any]) -> None:
        if not data:
            return
        await self._ensure_cache()
        sk = self._resolve_sort_key(index)
        update_fields = {f"data.{k}": _bson_safe(v) for k, v in data.items()}
        # If `data` is null (placeholder row), $set on data.key fails.
        # First ensure data is a dict by conditionally setting it to {}.
        await self._col.update_one(
            {"_id": sk, "data": None},
            {"$set": {"data": {}}},
        )
        await self._col.update_one({"_id": sk}, {"$set": update_fields})

    async def update_many(self, start: int, data: list[dict[str, Any]]) -> None:
        if not data:
            return
        from pymongo import UpdateOne

        await self._ensure_cache()
        # Collect sort keys for rows we'll update
        sks_to_update = []
        ops = []
        for i, row_data in enumerate(data):
            if not row_data:
                continue
            sk = self._resolve_sort_key(start + i)
            sks_to_update.append(sk)
            update_fields = {f"data.{k}": _bson_safe(v) for k, v in row_data.items()}
            ops.append(UpdateOne({"_id": sk}, {"$set": update_fields}))

        if not ops:
            return

        # First, convert any placeholder rows (data: null) to data: {}
        # This prevents MongoDB error when $set on nested fields of null
        if sks_to_update:
            await self._col.update_many(
                {"_id": {"$in": sks_to_update}, "data": None},
                {"$set": {"data": {}}},
            )
        # Now do the actual updates
        await self._col.bulk_write(ops, ordered=False)

    async def set_column(self, key: str, start: int, values: list[Any]) -> None:
        if not values:
            return
        from pymongo import UpdateOne

        await self._ensure_cache()
        sks_to_update = []
        ops = []
        for i, value in enumerate(values):
            sk = self._resolve_sort_key(start + i)
            sks_to_update.append(sk)
            ops.append(
                UpdateOne({"_id": sk}, {"$set": {f"data.{key}": _bson_safe(value)}})
            )

        if not ops:
            return

        # First, convert any placeholder rows (data: null) to data: {}
        # This prevents MongoDB error when $set on nested fields of null
        if sks_to_update:
            await self._col.update_many(
                {"_id": {"$in": sks_to_update}, "data": None},
                {"$set": {"data": {}}},
            )
        # Now do the actual updates
        await self._col.bulk_write(ops, ordered=False)

    async def drop_keys(
        self, keys: list[str], indices: list[int] | None = None
    ) -> None:
        unset_fields = {f"data.{k}": "" for k in keys}
        if indices is None:
            await self._col.update_many(
                {"_id": {"$ne": META_ID}},
                {"$unset": unset_fields},
            )
        else:
            await self._ensure_cache()
            sks = [self._resolve_sort_key(i) for i in indices]
            await self._col.update_many(
                {"_id": {"$in": sks}},
                {"$unset": unset_fields},
            )

    async def clear(self) -> None:
        await self._col.delete_many({"_id": {"$ne": META_ID}})
        await self._col.update_one(
            {"_id": META_ID},
            {"$set": {"sort_keys": [], "count": 0, "next_sort_key": 0}},
            upsert=True,
        )
        self._invalidate_cache()

    async def remove(self) -> None:
        await self._col.drop()
        self._invalidate_cache()

    def close(self) -> None:
        """Close the MongoDB client connection (sync wrapper for compatibility)."""
        # Note: AsyncMongoClient.close() is async, but we provide a sync method
        # for consistency with other backends. Use aclose() for proper async cleanup.
        import asyncio

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._client.close())
        except RuntimeError:
            # No running loop - just close synchronously (best effort)
            pass

    async def aclose(self) -> None:
        """Close the MongoDB client connection asynchronously."""
        await self._client.close()

    async def __aenter__(self) -> AsyncMongoObjectBackend:
        return self

    async def __aexit__(self, *args) -> None:
        await self.aclose()
