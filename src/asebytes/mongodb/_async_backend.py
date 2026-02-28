from __future__ import annotations

from typing import Any

from pymongo import AsyncMongoClient

from .._async_backends import AsyncReadWriteBackend

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

        return cls(uri=connection_uri, database=database, collection=collection, **kwargs)

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

    async def get_column(
        self, key: str, indices: list[int] | None = None
    ) -> list[Any]:
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

    async def extend(self, values: list[dict[str, Any] | None]) -> None:
        if not values:
            return
        await self._ensure_cache()
        meta = await self._col.find_one({"_id": META_ID})
        next_sk = meta["next_sort_key"] if meta else 0
        new_sks = list(range(next_sk, next_sk + len(values)))

        docs = [self._row_to_doc(sk, v) for sk, v in zip(new_sks, values)]
        await self._col.insert_many(docs)

        self._sort_keys.extend(new_sks)
        self._count += len(values)
        await self._col.update_one(
            {"_id": META_ID},
            {
                "$push": {"sort_keys": {"$each": new_sks}},
                "$set": {
                    "count": self._count,
                    "next_sort_key": next_sk + len(values),
                },
            },
            upsert=True,
        )

    async def insert(self, index: int, value: dict[str, Any] | None) -> None:
        await self._ensure_cache()
        n = len(self._sort_keys)
        if index < 0:
            index = 0
        if index > n:
            index = n

        meta = await self._col.find_one({"_id": META_ID})
        next_sk = meta["next_sort_key"] if meta else 0

        await self._col.insert_one(self._row_to_doc(next_sk, value))

        self._sort_keys.insert(index, next_sk)
        self._count += 1
        await self._col.update_one(
            {"_id": META_ID},
            {
                "$set": {
                    "sort_keys": self._sort_keys,
                    "count": self._count,
                    "next_sort_key": next_sk + 1,
                },
            },
            upsert=True,
        )

    async def update(self, index: int, data: dict[str, Any]) -> None:
        if not data:
            return
        await self._ensure_cache()
        sk = self._resolve_sort_key(index)
        update_fields = {f"data.{k}": v for k, v in data.items()}
        await self._col.update_one({"_id": sk}, {"$set": update_fields})

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
