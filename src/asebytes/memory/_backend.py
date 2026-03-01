"""In-memory backend backed by a plain list. No persistence, no threading."""

from __future__ import annotations

from typing import Any, ClassVar

from .._backends import ReadWriteBackend

# Global storage for all memory backends, organized by group
# This allows multiple MemoryObjectBackend instances with the same group to share data
_GLOBAL_STORAGE: dict[str, list[dict[str, Any] | None]] = {}


class MemoryObjectBackend(ReadWriteBackend[str, Any]):
    """In-memory ReadWriteBackend backed by list[dict[str, Any] | None].

    No persistence — data exists only for the lifetime of the object.
    Suitable for testing, ephemeral storage, and transient data rooms.

    Parameters
    ----------
    group : str or None, optional
        The group name for this backend. Multiple backends with the same
        group share the same underlying data. Defaults to "default".
    """

    def __init__(self, group: str | None = None) -> None:
        self._group = group if group is not None else "default"
        # Ensure the group exists in global storage
        if self._group not in _GLOBAL_STORAGE:
            _GLOBAL_STORAGE[self._group] = []

    @property
    def group(self) -> str:
        """Return the group name for this backend."""
        return self._group

    @property
    def _data(self) -> list[dict[str, Any] | None]:
        """Return the data list for this group."""
        if self._group not in _GLOBAL_STORAGE:
            _GLOBAL_STORAGE[self._group] = []
        return _GLOBAL_STORAGE[self._group]

    @classmethod
    def from_uri(cls, uri: str, **kwargs: Any) -> MemoryObjectBackend:
        """Create from a ``memory://`` URI. The path is ignored."""
        return cls(**kwargs)

    @staticmethod
    def list_groups(path: str, **kwargs: Any) -> list[str]:
        """List all groups in the global memory storage.

        Parameters
        ----------
        path : str
            The path (ignored for memory backend, but required by interface).
        **kwargs : Any
            Additional arguments (ignored).

        Returns
        -------
        list[str]
            List of group names that have been created.
        """
        return list(_GLOBAL_STORAGE.keys())

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
        if index < 0 or index >= len(self._data):
            raise IndexError(index)
        del self._data[index]

    def extend(self, values: list[dict[str, Any] | None]) -> int:
        self._data.extend(values)
        return len(self._data)

    def insert(self, index: int, value: dict[str, Any] | None) -> None:
        if index < 0 or index > len(self._data):
            raise IndexError(index)
        self._data.insert(index, value)

    def clear(self) -> None:
        self._data.clear()

    def remove(self) -> None:
        """Remove this group from global storage entirely."""
        if self._group in _GLOBAL_STORAGE:
            del _GLOBAL_STORAGE[self._group]
