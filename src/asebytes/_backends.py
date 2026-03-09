from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any, Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


# ── Generic read backend ─────────────────────────────────────────────────


class ReadBackend(Generic[K, V], ABC):
    """Abstract base for read-only storage backends.

    Type parameters:
    - K: key type (bytes for blob level, str for object level)
    - V: value type (bytes for blob level, Any for object level)

    Subclasses must implement: __len__, get, list_groups.
    Override keys, get_many, iter_rows, get_column for optimization.
    """

    _returns_mutable: bool = False

    @staticmethod
    @abstractmethod
    def list_groups(path: str, **kwargs) -> list[str]:
        """Return available group names at the given path.

        Args:
            path: File path or URI to the storage location.
            **kwargs: Backend-specific options (e.g., credentials).

        Returns:
            List of group names available at the path.
        """
        ...

    @abstractmethod
    def __len__(self) -> int: ...

    @abstractmethod
    def get(self, index: int, keys: list[K] | None = None) -> dict[K, V] | None:
        """Read one row. Returns None for placeholders."""
        ...

    def get_many(
        self, indices: list[int], keys: list[K] | None = None
    ) -> list[dict[K, V] | None]:
        """Read multiple rows. Default: loops over get."""
        return [self.get(i, keys) for i in indices]

    def iter_rows(
        self, indices: list[int], keys: list[K] | None = None
    ) -> Iterator[dict[K, V] | None]:
        """Yield rows one at a time. Default: calls get per index."""
        for i in indices:
            yield self.get(i, keys)

    def get_column(self, key: K, indices: list[int] | None = None) -> list[Any]:
        """Read a single column across rows. Default: extracts from get."""
        if indices is None:
            indices = list(range(len(self)))
        results = []
        for i in indices:
            row = self.get(i, [key])
            results.append(row[key] if row is not None else None)
        return results

    def keys(self, index: int) -> list[K]:
        """Return keys present at index WITHOUT loading values.

        Override for backends where key-existence checks are cheaper than
        full reads (e.g. LMDB cursor.getmulti).
        """
        row = self.get(index)
        if row is None:
            return []
        return list(row.keys())

    def schema(self, index: int = 0) -> dict:
        """Column names, dtypes, shapes. Override for O(1) metadata reads."""
        from ._schema import infer_schema

        row = self.get(index)
        if row is None:
            return {}
        return infer_schema(row)


# ── Generic read-write backend ───────────────────────────────────────────


class ReadWriteBackend(ReadBackend[K, V], ABC):
    """Abstract base for read-write storage backends.

    Subclasses must implement everything from ReadBackend plus:
    set, delete, extend, insert.
    """

    _returns_mutable: bool = True

    @abstractmethod
    def set(self, index: int, value: dict[K, V] | None) -> None:
        """Write or overwrite a single row."""
        ...

    @abstractmethod
    def delete(self, index: int) -> None:
        """Delete a row at index, shifting subsequent rows."""
        ...

    @abstractmethod
    def extend(self, values: list[dict[K, V] | None]) -> int:
        """Append multiple rows efficiently (bulk operation).

        Returns the new total length after the extend.
        """
        ...

    @abstractmethod
    def insert(self, index: int, value: dict[K, V] | None) -> None:
        """Insert a row at index, shifting subsequent rows."""
        ...

    def update(self, index: int, data: dict[K, V]) -> None:
        """Partial update. Default: read-modify-write."""
        row = self.get(index) or {}
        row.update(data)
        self.set(index, row)

    def delete_many(self, start: int, stop: int) -> None:
        """Delete contiguous range [start, stop). Default: loop in reverse."""
        for i in range(stop - 1, start - 1, -1):
            self.delete(i)

    def drop_keys(self, keys: list[K], indices: list[int] | None = None) -> None:
        """Remove specific keys from rows. Default: read-modify-write."""
        if indices is None:
            indices = list(range(len(self)))
        key_set = set(keys)
        for i in indices:
            row = self.get(i)
            if row is None:
                continue
            pruned = {k: v for k, v in row.items() if k not in key_set}
            self.set(i, pruned)

    def set_many(self, start: int, data: list[dict[K, V] | None]) -> None:
        """Overwrite contiguous rows [start, start+len(data)).

        Override for backends where batch writes are cheaper than
        individual set() calls (e.g. single LMDB transaction).
        """
        for i, row in enumerate(data):
            self.set(start + i, row)

    def update_many(self, start: int, data: list[dict[K, V]]) -> None:
        """Partial-merge contiguous rows [start, start+len(data)).

        Override for backends where batch partial updates are cheaper than
        individual update() calls (e.g. single LMDB transaction, Redis pipeline).
        """
        for i, d in enumerate(data):
            self.update(start + i, d)

    def set_column(self, key: K, start: int, values: list[V]) -> None:
        """Write a single key across contiguous rows [start, start+len(values)).

        Override for columnar backends (Zarr, H5MD) or network backends
        (Redis, MongoDB) where batch writes are cheaper.
        """
        for i, v in enumerate(values):
            self.update(start + i, {key: v})

    def reserve(self, count: int) -> None:
        """Append count placeholder (None) entries. Default: extend."""
        self.extend([None] * count)

    def clear(self) -> None:
        """Remove all data but keep the container. Default: delete all rows."""
        for i in range(len(self) - 1, -1, -1):
            self.delete(i)

    def remove(self) -> None:
        """Remove the entire container. No default -- backend-specific."""
        raise NotImplementedError


# ── Type aliases ─────────────────────────────────────────────────────────

BlobReadBackend = ReadBackend[bytes, bytes]
BlobReadWriteBackend = ReadWriteBackend[bytes, bytes]
ObjectReadBackend = ReadBackend[str, Any]
ObjectReadWriteBackend = ReadWriteBackend[str, Any]
