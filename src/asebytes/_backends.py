from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any, Generic, TypeVar

from typing_extensions import deprecated

K = TypeVar("K")
V = TypeVar("V")


# ── Generic read backend ─────────────────────────────────────────────────


class ReadBackend(Generic[K, V], ABC):
    """Abstract base for read-only storage backends.

    Type parameters:
    - K: key type (bytes for blob level, str for object level)
    - V: value type (bytes for blob level, Any for object level)

    Subclasses must implement: __len__, get, schema.
    Override get_many, iter_rows, get_column for optimization.
    """

    @abstractmethod
    def __len__(self) -> int: ...

    @abstractmethod
    def get(
        self, index: int, keys: list[K] | None = None
    ) -> dict[K, V] | None:
        """Read one row. Returns None for placeholders."""
        ...

    @abstractmethod
    def schema(self) -> list[K]:
        """Return the global schema (union of all field names)."""
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
        return [self.get(i, [key])[key] for i in indices]

    def get_available_keys(self, index: int) -> list[K]:
        """Return keys present at index WITHOUT loading values.

        Override for backends where key-existence checks are cheaper than
        full reads (e.g. LMDB cursor.getmulti).
        """
        row = self.get(index)
        if row is None:
            return []
        return list(row.keys())

    # -- Backward compatibility aliases ------------------------------------

    @deprecated("Use get() instead", category=DeprecationWarning, stacklevel=2)
    def read_row(self, index: int, keys=None):
        return self.get(index, keys)

    @deprecated("Use get_many() instead", category=DeprecationWarning, stacklevel=2)
    def read_rows(self, indices, keys=None):
        return self.get_many(indices, keys)

    @deprecated("Use get_column() instead", category=DeprecationWarning, stacklevel=2)
    def read_column(self, key, indices=None):
        return self.get_column(key, indices)

    @deprecated("Use schema() instead", category=DeprecationWarning, stacklevel=2)
    def columns(self, index: int = 0) -> list:
        return self.schema()

    @deprecated("Use schema() instead", category=DeprecationWarning, stacklevel=2)
    def get_schema(self):
        return self.schema()


# ── Generic read-write backend ───────────────────────────────────────────


class ReadWriteBackend(ReadBackend[K, V], ABC):
    """Abstract base for read-write storage backends.

    Subclasses must implement everything from ReadBackend plus:
    set, delete, extend, insert.
    """

    @abstractmethod
    def set(self, index: int, value: dict[K, V] | None) -> None:
        """Write or overwrite a single row."""
        ...

    @abstractmethod
    def delete(self, index: int) -> None:
        """Delete a row at index, shifting subsequent rows."""
        ...

    @abstractmethod
    def extend(self, values: list[dict[K, V] | None]) -> None:
        """Append multiple rows efficiently (bulk operation)."""
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

    def drop_keys(
        self, keys: list[K], indices: list[int] | None = None
    ) -> None:
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

    # -- Backward compatibility aliases ------------------------------------

    @deprecated("Use set() instead", category=DeprecationWarning, stacklevel=2)
    def write_row(self, index: int, data) -> None:
        self.set(index, data)

    @deprecated("Use delete() instead", category=DeprecationWarning, stacklevel=2)
    def delete_row(self, index: int) -> None:
        self.delete(index)

    @deprecated("Use insert() instead", category=DeprecationWarning, stacklevel=2)
    def insert_row(self, index: int, data) -> None:
        self.insert(index, data)

    @deprecated("Use extend() instead", category=DeprecationWarning, stacklevel=2)
    def append_rows(self, data) -> None:
        self.extend(data)

    @deprecated("Use update() instead", category=DeprecationWarning, stacklevel=2)
    def update_row(self, index: int, data) -> None:
        self.update(index, data)

    @deprecated("Use delete_many() instead", category=DeprecationWarning, stacklevel=2)
    def delete_rows(self, start: int, stop: int) -> None:
        self.delete_many(start, stop)

    @deprecated("Use set_many() instead", category=DeprecationWarning, stacklevel=2)
    def write_rows(self, start: int, data: list) -> None:
        self.set_many(start, data)


# ── Type aliases ─────────────────────────────────────────────────────────

BlobReadBackend = ReadBackend[bytes, bytes]
BlobReadWriteBackend = ReadWriteBackend[bytes, bytes]
ObjectReadBackend = ReadBackend[str, Any]
ObjectReadWriteBackend = ReadWriteBackend[str, Any]
