from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any


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
        row = self.read_row(index)
        row.update(data)
        self.write_row(index, row)
