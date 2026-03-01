from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import numpy as np
from pymongo import MongoClient

from .._backends import ReadWriteBackend

META_ID = "__meta__"
DEFAULT_GROUP = "default"


def _bson_safe(value: Any) -> Any:
    """Convert a value to a BSON-serialisable form.

    numpy arrays → list, numpy scalars → Python scalar.
    """
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    return value


class MongoObjectBackend(ReadWriteBackend[str, Any]):
    """MongoDB-backed read-write backend for object dictionaries.

    Uses a sort-key array in a metadata document for O(1) positional access.
    Each row is a separate document with ``_id`` = sort_key (int) and a
    ``data`` subdocument holding the field values.

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
        self._client = MongoClient(uri)
        self.group = group if group is not None else DEFAULT_GROUP
        self._col = self._client[database][self.group]
        self._sort_keys: list[int] | None = None
        self._count: int | None = None

    @classmethod
    def from_uri(
        cls, uri: str, group: str | None = None, **kwargs
    ) -> MongoObjectBackend:
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
        # Extract path from URI: mongodb://host:port/database
        _, after_scheme = uri.split("://", 1)
        # Split host from path
        if "/" in after_scheme:
            host_part, path_part = after_scheme.split("/", 1)
        else:
            host_part, path_part = after_scheme, ""

        parts = [p for p in path_part.split("/") if p]
        if len(parts) >= 1:
            database = parts[0]
            # Rebuild connection URI without database path
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

        Parameters
        ----------
        path : str
            MongoDB connection URI (e.g. ``mongodb://localhost:27017``
            or ``mongodb://host:port/mydb``).  When the URI contains a
            database path, it is used instead of the *database* parameter.
        database : str
            Database name to list collections from.  Ignored when the
            URI already contains a database path.
        **kwargs
            Unused, for API compatibility.

        Returns
        -------
        list[str]
            List of group names (collection names) in the database.
        """
        # Parse database from URI path, consistent with from_uri()
        connection_uri = path
        if "://" in path:
            _, after_scheme = path.split("://", 1)
            if "/" in after_scheme:
                host_part, path_part = after_scheme.split("/", 1)
                parts = [p for p in path_part.split("/") if p]
                if parts:
                    database = parts[0]
                    connection_uri = path.split("://")[0] + "://" + host_part

        client = MongoClient(connection_uri)
        try:
            db = client[database]
            # Get all collection names, excluding system collections
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

    def _ensure_cache(self) -> None:
        if self._sort_keys is not None:
            return
        meta = self._col.find_one({"_id": META_ID})
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
    # ReadBackend implementation
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        self._ensure_cache()
        return self._count

    def get(self, index: int, keys: list[str] | None = None) -> dict[str, Any] | None:
        self._ensure_cache()
        sk = self._resolve_sort_key(index)
        doc = self._col.find_one({"_id": sk}, self._projection(keys))
        return self._doc_to_row(doc)

    def get_many(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any] | None]:
        self._ensure_cache()
        sks = [self._resolve_sort_key(i) for i in indices]
        proj = self._projection(keys)
        # Batch fetch
        docs = {doc["_id"]: doc for doc in self._col.find({"_id": {"$in": sks}}, proj)}
        return [self._doc_to_row(docs.get(sk)) for sk in sks]

    def iter_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> Iterator[dict[str, Any] | None]:
        """Yield rows one at a time, backed by a batched get_many."""
        yield from self.get_many(indices, keys)

    def get_column(self, key: str, indices: list[int] | None = None) -> list[Any]:
        self._ensure_cache()
        if indices is None:
            indices = list(range(self._count))
        sks = [self._resolve_sort_key(i) for i in indices]
        proj = {f"data.{key}": 1}
        docs = {doc["_id"]: doc for doc in self._col.find({"_id": {"$in": sks}}, proj)}
        results = []
        for sk in sks:
            doc = docs.get(sk)
            if doc is not None and doc.get("data") is not None:
                results.append(doc["data"].get(key))
            else:
                results.append(None)
        return results

    # ------------------------------------------------------------------
    # ReadWriteBackend implementation
    # ------------------------------------------------------------------

    def set(self, index: int, data: dict[str, Any] | None) -> None:
        self._ensure_cache()
        n = len(self._sort_keys)
        if index < 0:
            index += n
        if index < 0 or index >= n:
            raise IndexError(index)
        sk = self._sort_keys[index]
        self._col.replace_one({"_id": sk}, self._row_to_doc(sk, data), upsert=True)
        self._invalidate_cache()

    def delete(self, index: int) -> None:
        self._ensure_cache()
        sk = self._resolve_sort_key(index)
        # Normalize negative index for array position
        n = len(self._sort_keys)
        pos = index if index >= 0 else index + n
        self._col.delete_one({"_id": sk})
        # Remove from sort_keys array and decrement count
        self._sort_keys.pop(pos)
        self._count -= 1
        self._col.update_one(
            {"_id": META_ID},
            {
                "$set": {
                    "sort_keys": self._sort_keys,
                    "count": self._count,
                },
            },
        )

    def extend(self, values: list[dict[str, Any] | None]) -> int:
        if not values:
            return self._count if self._count is not None else len(self)
        self._ensure_cache()
        meta = self._col.find_one({"_id": META_ID})
        next_sk = meta.get("next_sort_key", 0) if meta else 0
        new_sks = list(range(next_sk, next_sk + len(values)))

        docs = [self._row_to_doc(sk, v) for sk, v in zip(new_sks, values)]
        self._col.insert_many(docs)

        self._sort_keys.extend(new_sks)
        self._count += len(values)
        self._col.update_one(
            {"_id": META_ID},
            {
                "$push": {"sort_keys": {"$each": new_sks}},
                "$set": {"count": self._count, "next_sort_key": next_sk + len(values)},
            },
            upsert=True,
        )
        return self._count

    def insert(self, index: int, value: dict[str, Any] | None) -> None:
        self._ensure_cache()
        n = len(self._sort_keys)
        if index < 0:
            index = 0
        if index > n:
            index = n

        meta = self._col.find_one({"_id": META_ID})
        next_sk = meta.get("next_sort_key", 0) if meta else 0

        self._col.insert_one(self._row_to_doc(next_sk, value))

        self._sort_keys.insert(index, next_sk)
        self._count += 1
        self._col.update_one(
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

    def update(self, index: int, data: dict[str, Any]) -> None:
        if not data:
            return
        self._ensure_cache()
        sk = self._resolve_sort_key(index)
        update_fields = {f"data.{k}": _bson_safe(v) for k, v in data.items()}
        self._col.update_one({"_id": sk}, {"$set": update_fields})

    def update_many(self, start: int, data: list[dict[str, Any]]) -> None:
        if not data:
            return
        from pymongo import UpdateOne

        self._ensure_cache()
        ops = []
        for i, row_data in enumerate(data):
            if not row_data:
                continue
            sk = self._resolve_sort_key(start + i)
            update_fields = {f"data.{k}": _bson_safe(v) for k, v in row_data.items()}
            ops.append(UpdateOne({"_id": sk}, {"$set": update_fields}))
        if ops:
            self._col.bulk_write(ops, ordered=False)

    def set_column(self, key: str, start: int, values: list[Any]) -> None:
        if not values:
            return
        from pymongo import UpdateOne

        self._ensure_cache()
        ops = []
        for i, value in enumerate(values):
            sk = self._resolve_sort_key(start + i)
            ops.append(
                UpdateOne({"_id": sk}, {"$set": {f"data.{key}": _bson_safe(value)}})
            )
        if ops:
            self._col.bulk_write(ops, ordered=False)

    def drop_keys(self, keys: list[str], indices: list[int] | None = None) -> None:
        unset_fields = {f"data.{k}": "" for k in keys}
        if indices is None:
            self._col.update_many(
                {"_id": {"$ne": META_ID}},
                {"$unset": unset_fields},
            )
        else:
            self._ensure_cache()
            sks = [self._resolve_sort_key(i) for i in indices]
            self._col.update_many(
                {"_id": {"$in": sks}},
                {"$unset": unset_fields},
            )

    def clear(self) -> None:
        self._col.delete_many({"_id": {"$ne": META_ID}})
        self._col.update_one(
            {"_id": META_ID},
            {"$set": {"sort_keys": [], "count": 0, "next_sort_key": 0}},
            upsert=True,
        )
        self._invalidate_cache()

    def remove(self) -> None:
        self._col.drop()
        self._invalidate_cache()

    def close(self) -> None:
        """Close the MongoDB client connection."""
        self._client.close()

    def __enter__(self) -> MongoObjectBackend:
        return self

    def __exit__(self, *args) -> None:
        self.close()
