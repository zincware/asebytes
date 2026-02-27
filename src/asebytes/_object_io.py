"""ObjectIO -- MutableSequence facade for object-level backends.

Delegates to a ReadBackend[str, Any] or ReadWriteBackend[str, Any].
Supports lazy views (RowView / ColumnView) via __getitem__.
"""

from __future__ import annotations

from collections.abc import Iterator, MutableSequence
from typing import Any, overload

from ._backends import ReadBackend, ReadWriteBackend
from ._views import ColumnView, RowView


class ObjectIO(MutableSequence):
    """Storage-agnostic mutable sequence for dict[str, Any] rows.

    Parameters
    ----------
    backend : ReadBackend[str, Any] | ReadWriteBackend[str, Any]
        An object-level backend instance.
    """

    def __init__(self, backend: ReadBackend[str, Any]):
        self._backend = backend

    @property
    def columns(self) -> list[str]:
        """Available column names (from schema)."""
        try:
            n = len(self._backend)
        except TypeError:
            pass
        else:
            if n == 0:
                return []
        return self._backend.schema()

    # --- Internal methods used by views ---

    def _read_row(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any]:
        return self._backend.get(index, keys)

    def _read_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any]]:
        return self._backend.get_many(indices, keys)

    def _iter_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> Iterator[dict[str, Any]]:
        return self._backend.iter_rows(indices, keys)

    def _read_column(self, key: str, indices: list[int]) -> list[Any]:
        return self._backend.get_column(key, indices)

    def _build_atoms(self, row: dict[str, Any]) -> dict[str, Any]:
        """Identity transform -- returns dict as-is.

        ASEIO overrides this to call dict_to_atoms.
        """
        return row

    # --- MutableSequence interface ---

    @overload
    def __getitem__(self, index: int) -> dict[str, Any]: ...
    @overload
    def __getitem__(self, index: slice) -> RowView: ...
    @overload
    def __getitem__(self, index: list[int]) -> RowView: ...
    @overload
    def __getitem__(self, index: str) -> ColumnView: ...
    @overload
    def __getitem__(self, index: list[str]) -> ColumnView: ...

    def __getitem__(
        self,
        index: int | slice | str | list[int] | list[str],
    ) -> dict[str, Any] | RowView | ColumnView:
        if isinstance(index, int):
            if index < 0:
                index += len(self)
            if index < 0:
                raise IndexError(index)
            return self._backend.get(index)
        if isinstance(index, slice):
            indices = range(len(self))[index]
            return RowView(self, list(indices))
        if isinstance(index, str):
            return ColumnView(self, index)
        if isinstance(index, list):
            if not index:
                return RowView(self, [])
            if isinstance(index[0], int):
                n = len(self)
                normalized = []
                for i in index:
                    idx = i + n if i < 0 else i
                    if idx < 0 or idx >= n:
                        raise IndexError(i)
                    normalized.append(idx)
                return RowView(self, normalized)
            if isinstance(index[0], str):
                return ColumnView(self, index)
        raise TypeError(f"Unsupported index type: {type(index)}")

    def __setitem__(self, index: int, value: dict[str, Any]) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.set(index, value)

    def __delitem__(self, index: int) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.delete(index)

    def insert(self, index: int, value: dict[str, Any]) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.insert(index, value)

    def extend(self, values) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.extend(list(values))

    def __len__(self) -> int:
        return len(self._backend)

    def __iter__(self) -> Iterator[dict[str, Any]]:
        i = 0
        while True:
            try:
                yield self[i]
                i += 1
            except IndexError:
                return
