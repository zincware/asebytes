from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import numpy as np
from pymongo import AsyncMongoClient

from .._async_backends import AsyncReadWriteBackend
from ._backend import _bson_safe, DEFAULT_GROUP

META_ID = "__meta__"


class AsyncMongoObjectBackend(AsyncReadWriteBackend[str, Any]):
    """Async MongoDB-backed read-write backend for object dictionaries.

    Uses ``pymongo.AsyncMongoClient`` (GA since PyMongo 4.13) for native
    non-blocking I/O.  Same sort-key array design as :class:`MongoObjectBackend`.

    Each group is stored in a separate MongoDB collection within the database.

    Parameters
    ----------
    uri : str
        MongoDB connection URI (e.g. ``mongodb://localhost:27017``).
        Should NOT include database or collection in the path.
    database : str
        Database name.
    group : str | None
        Group name (maps to MongoDB collection). Defaults to ``"default"``.
    """

    def __init__(
        self,
        uri: str = "mongodb://localhost:27017",
        database: str = "asebytes",
        group: str | None = None,
    ):
        self._client = AsyncMongoClient(uri)
        self.group = group if group is not None else DEFAULT_GROUP
        self._col = self._client[database][self.group]
        self._sort_keys: list[int] | None = None
        self._count: int | None = None

    @classmethod
    def from_uri(
        cls, uri: str, group: str | None = None, **kwargs
    ) -> AsyncMongoObjectBackend:
        """Construct from a URI like ``mongodb://host:port/database``.

        The path after the host is the database name. Group (collection) is
        passed separately via the ``group`` parameter.

        Parameters
        ----------
        uri : str
            MongoDB URI with database path (e.g. ``mongodb://host:port/mydb``).
        group : str | None
            Group name (maps to collection). Defaults to ``"default"``.
        **kwargs
            Additional arguments passed to the constructor.
        """
        if "://" not in uri:
            raise ValueError(f"Invalid URI: {uri!r}")
        _, after_scheme = uri.split("://", 1)
        if "/" in after_scheme:
            host_part, path_part = after_scheme.split("/", 1)
        else:
            host_part, path_part = after_scheme, ""

        parts = [p for p in path_part.split("/") if p]
        if len(parts) >= 1:
            database = parts[0]
            connection_uri = uri.split("://")[0] + "://" + host_part
        else:
            database = "asebytes"
            connection_uri = uri

        return cls(uri=connection_uri, database=database, group=group, **kwargs)

    @staticmethod
    def list_groups(
        path: str = "mongodb://localhost:27017", database: str = "asebytes", **kwargs
    ) -> list[str]:
        """Return available group names (collections) in the given database.

        Note: This is a synchronous method that uses a sync client internally,
        as listing groups is typically done outside of async contexts.

        Parameters
        ----------
        path : str
            MongoDB connection URI (e.g. ``mongodb://localhost:27017``).
        database : str
            Database name to list collections from.
        **kwargs
            Unused, for API compatibility.

        Returns
        -------
        list[str]
            List of group names (collection names) in the database.
        """
        from pymongo import MongoClient

        client = MongoClient(path)
        try:
            db = client[database]
            collections = db.list_collection_names()
            return sorted(collections)
        finally:
            client.close()

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------

    def _invalidate_cache(self) -> None:
        self._sort_keys = None
        self._count = None

    async def _ensure_cache(self) -> None:
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
        # Atomically reserve a range of sort keys via $inc
        meta = await self._col.find_one_and_update(
            {"_id": META_ID},
            {"$inc": {"next_sort_key": len(values)}},
            upsert=True,
            return_document=False,  # BEFORE the increment
        )
        next_sk = meta.get("next_sort_key", 0) if meta else 0
        new_sks = list(range(next_sk, next_sk + len(values)))

        docs = [self._row_to_doc(sk, v) for sk, v in zip(new_sks, values)]
        await self._col.insert_many(docs)

        await self._col.update_one(
            {"_id": META_ID},
            {
                "$push": {"sort_keys": {"$each": new_sks}},
                "$inc": {"count": len(values)},
            },
        )
        self._invalidate_cache()
        await self._ensure_cache()
        return self._count

    async def insert(self, index: int, value: dict[str, Any] | None) -> None:
        await self._ensure_cache()
        n = len(self._sort_keys)
        if index < 0:
            index = 0
        if index > n:
            index = n

        # Atomically reserve one sort key via $inc
        meta = await self._col.find_one_and_update(
            {"_id": META_ID},
            {"$inc": {"next_sort_key": 1}},
            upsert=True,
            return_document=False,  # BEFORE the increment
        )
        next_sk = meta.get("next_sort_key", 0) if meta else 0

        await self._col.insert_one(self._row_to_doc(next_sk, value))

        # Use atomic $push with $position and $inc for count
        await self._col.update_one(
            {"_id": META_ID},
            {
                "$push": {"sort_keys": {"$each": [next_sk], "$position": index}},
                "$inc": {"count": 1},
            },
        )
        self._invalidate_cache()

    async def update(self, index: int, data: dict[str, Any]) -> None:
        if not data:
            return
        await self._ensure_cache()
        sk = self._resolve_sort_key(index)
        update_fields = {f"data.{k}": _bson_safe(v) for k, v in data.items()}
        await self._col.update_one({"_id": sk}, {"$set": update_fields})

    async def update_many(self, start: int, data: list[dict[str, Any]]) -> None:
        if not data:
            return
        from pymongo import UpdateOne

        await self._ensure_cache()
        ops = []
        for i, row_data in enumerate(data):
            if not row_data:
                continue
            sk = self._resolve_sort_key(start + i)
            update_fields = {f"data.{k}": _bson_safe(v) for k, v in row_data.items()}
            ops.append(UpdateOne({"_id": sk}, {"$set": update_fields}))
        if ops:
            await self._col.bulk_write(ops, ordered=False)

    async def set_column(self, key: str, start: int, values: list[Any]) -> None:
        if not values:
            return
        from pymongo import UpdateOne

        await self._ensure_cache()
        ops = []
        for i, value in enumerate(values):
            sk = self._resolve_sort_key(start + i)
            ops.append(
                UpdateOne({"_id": sk}, {"$set": {f"data.{key}": _bson_safe(value)}})
            )
        if ops:
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
        """Close the MongoDB client connection."""
        self._client.close()

    async def __aenter__(self) -> AsyncMongoObjectBackend:
        return self

    async def __aexit__(self, *args) -> None:
        self.close()
