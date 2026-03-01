"""In-memory backend backed by a plain list. No persistence, no threading."""

from __future__ import annotations

from typing import Any

from .._backends import ReadWriteBackend


class MemoryObjectBackend(ReadWriteBackend[str, Any]):
    """In-memory ReadWriteBackend backed by list[dict[str, Any] | None].

    No persistence — data exists only for the lifetime of the object.
    Suitable for testing, ephemeral storage, and transient data rooms.
    """

    def __init__(self) -> None:
        self._data: list[dict[str, Any] | None] = []

    @classmethod
    def from_uri(cls, uri: str, **kwargs: Any) -> MemoryObjectBackend:
        """Create from a ``memory://`` URI. The path is ignored."""
        return cls(**kwargs)

    def __len__(self) -> int:
        return len(self._data)

    def get(self, index: int, keys: list[str] | None = None) -> dict[str, Any] | None:
        if index < 0 or index >= len(self._data):
            raise IndexError(index)
        row = self._data[index]
        if row is None or keys is None:
            return row
        return {k: row[k] for k in keys if k in row}

    def set(self, index: int, value: dict[str, Any] | None) -> None:
        if index < 0 or index >= len(self._data):
            raise IndexError(index)
        self._data[index] = value

    def delete(self, index: int) -> None:
        del self._data[index]

    def extend(self, values: list[dict[str, Any] | None]) -> int:
        self._data.extend(values)
        return len(self._data)

    def insert(self, index: int, value: dict[str, Any] | None) -> None:
        self._data.insert(index, value)

    def clear(self) -> None:
        self._data.clear()

    def remove(self) -> None:
        self._data.clear()
