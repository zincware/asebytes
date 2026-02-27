from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any


# ── Bytes-level protocols (used by BytesIO / AsyncBytesIO) ──────────────


class RawReadableBackend(ABC):
    """Abstract base for read-only storage backends at the raw bytes level.

    Subclasses must implement: __len__, get_schema, read_row.
    Override read_rows, iter_rows, get_available_keys for optimization.
    """

    @abstractmethod
    def __len__(self) -> int: ...

    @abstractmethod
    def get_schema(self) -> list[bytes]:
        """Return the global schema (union of all field names)."""
        ...

    @abstractmethod
    def read_row(
        self, index: int, keys: list[bytes] | None = None
    ) -> dict[bytes, bytes] | None:
        """Read one row. Returns None for placeholders."""
        ...

    def get_available_keys(self, index: int) -> list[bytes]:
        """Keys present at this specific index."""
        row = self.read_row(index)
        return list(row.keys()) if row is not None else []

    def read_rows(
        self, indices: list[int], keys: list[bytes] | None = None
    ) -> list[dict[bytes, bytes] | None]:
        """Read multiple rows. Default: loops over read_row."""
        return [self.read_row(i, keys) for i in indices]

    def iter_rows(
        self, indices: list[int], keys: list[bytes] | None = None
    ) -> Iterator[dict[bytes, bytes] | None]:
        """Yield rows one at a time. Default: calls read_row per index."""
        for i in indices:
            yield self.read_row(i, keys)


class RawWritableBackend(RawReadableBackend):
    """Abstract base for read-write storage backends at the raw bytes level.

    Subclasses must implement everything from RawReadableBackend plus:
    write_row, insert_row, delete_row, append_rows.
    """

    @abstractmethod
    def write_row(self, index: int, data: dict[bytes, bytes] | None) -> None:
        """Write or overwrite a single row."""
        ...

    @abstractmethod
    def insert_row(self, index: int, data: dict[bytes, bytes] | None) -> None:
        """Insert a row at index, shifting subsequent rows."""
        ...

    @abstractmethod
    def delete_row(self, index: int) -> None:
        """Delete a row at index, shifting subsequent rows."""
        ...

    @abstractmethod
    def append_rows(self, data: list[dict[bytes, bytes] | None]) -> None:
        """Append multiple rows efficiently (bulk operation)."""
        ...

    def update_row(self, index: int, data: dict[bytes, bytes]) -> None:
        """Partial update. Default: read-modify-write."""
        row = self.read_row(index) or {}
        row.update(data)
        self.write_row(index, row)

    def delete_rows(self, start: int, stop: int) -> None:
        """Delete contiguous range [start, stop). Default: loop in reverse."""
        for i in range(stop - 1, start - 1, -1):
            self.delete_row(i)

    def write_rows(
        self, start: int, data: list[dict[bytes, bytes] | None]
    ) -> None:
        """Overwrite contiguous range starting at start. Default: loop."""
        for i, d in enumerate(data):
            self.write_row(start + i, d)

    def drop_keys(
        self, keys: list[bytes], indices: list[int] | None = None
    ) -> None:
        """Remove specific keys from rows. Default: read-modify-write."""
        if indices is None:
            indices = list(range(len(self)))
        key_set = set(keys)
        for i in indices:
            row = self.read_row(i)
            if row is None:
                continue
            pruned = {k: v for k, v in row.items() if k not in key_set}
            self.write_row(i, pruned)

    def reserve(self, count: int) -> None:
        """Append count placeholder (None) entries. Default: append_rows."""
        self.append_rows([None] * count)

    def clear(self) -> None:
        """Remove all data but keep the container. Default: delete all rows."""
        for i in range(len(self) - 1, -1, -1):
            self.delete_row(i)

    def remove(self) -> None:
        """Remove the entire container. No default — backend-specific."""
        raise NotImplementedError


# ── Str-level protocols (used by ASEIO / AsyncASEIO) ────────────────────


class ReadableBackend(ABC):
    """Abstract base for read-only storage backends.

    Subclasses must implement: __len__, columns, read_row.
    Override read_rows and read_column for backend-specific optimization.
    """

    @abstractmethod
    def __len__(self) -> int: ...

    @abstractmethod
    def columns(self, index: int = 0) -> list[str]:
        """Return available column names.

        Parameters
        ----------
        index : int
            Row index to inspect for available keys. Defaults to 0.
        """
        ...

    @abstractmethod
    def read_row(self, index: int, keys: list[str] | None = None) -> dict[str, Any]:
        """Read a single row, optionally filtering to specific keys.

        Parameters
        ----------
        index : int
            Row index.
        keys : list[str] | None
            If provided, only return these keys. If None, return all.

        Raises
        ------
        IndexError
            If ``index`` is out of bounds.
        """
        ...

    def read_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Read multiple rows. Default: loops over read_row."""
        return [self.read_row(i, keys) for i in indices]

    def iter_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> Iterator[dict[str, Any]]:
        """Yield rows one at a time. Default: calls read_row per index.

        Override for transaction-scoped streaming (e.g. single LMDB read txn).
        """
        for i in indices:
            yield self.read_row(i, keys)

    def read_column(
        self, key: str, indices: list[int] | None = None
    ) -> list[Any]:
        """Read a single column across rows. Default: extracts from read_row."""
        if indices is None:
            indices = list(range(len(self)))
        return [self.read_row(i, [key])[key] for i in indices]


class WritableBackend(ReadableBackend):
    """Abstract base for read-write storage backends.

    Subclasses must implement everything from ReadableBackend plus:
    write_row, insert_row, delete_row, append_rows.
    """

    @abstractmethod
    def write_row(self, index: int, data: dict[str, Any]) -> None:
        """Write or overwrite a single row."""
        ...

    @abstractmethod
    def insert_row(self, index: int, data: dict[str, Any]) -> None:
        """Insert a row at index, shifting subsequent rows."""
        ...

    @abstractmethod
    def delete_row(self, index: int) -> None:
        """Delete a row at index, shifting subsequent rows."""
        ...

    @abstractmethod
    def append_rows(self, data: list[dict[str, Any]]) -> None:
        """Append multiple rows efficiently (bulk operation)."""
        ...

    def update_row(self, index: int, data: dict[str, Any]) -> None:
        """Partial update of specific keys at index.

        Default implementation performs read-modify-write.
        Backends may override for optimized partial updates.
        """
        row = self.read_row(index) or {}
        row.update(data)
        self.write_row(index, row)

    def delete_rows(self, start: int, stop: int) -> None:
        """Delete contiguous range [start, stop). Default: loop in reverse."""
        for i in range(stop - 1, start - 1, -1):
            self.delete_row(i)

    def write_rows(
        self, start: int, data: list[dict[str, Any] | None]
    ) -> None:
        """Overwrite contiguous range starting at start. Default: loop."""
        for i, d in enumerate(data):
            self.write_row(start + i, d)

    def drop_keys(
        self, keys: list[str], indices: list[int] | None = None
    ) -> None:
        """Remove specific keys from rows. Default: read-modify-write."""
        if indices is None:
            indices = list(range(len(self)))
        key_set = set(keys)
        for i in indices:
            row = self.read_row(i)
            if row is None:
                continue
            pruned = {k: v for k, v in row.items() if k not in key_set}
            self.write_row(i, pruned)

    def reserve(self, count: int) -> None:
        """Append count placeholder (None) entries. Default: append_rows."""
        self.append_rows([None] * count)

    def clear(self) -> None:
        """Remove all data but keep the container. Default: delete all rows."""
        for i in range(len(self) - 1, -1, -1):
            self.delete_row(i)

    def remove(self) -> None:
        """Remove the entire container. No default — backend-specific."""
        raise NotImplementedError
