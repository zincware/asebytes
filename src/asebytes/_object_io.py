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
    backend : str | ReadBackend[str, Any]
        Either a file path (auto-creates backend via registry) or a
        backend instance.
    readonly : bool | None
        Force read-only or writable mode. None (default) auto-detects.
        Only used when *backend* is a string.
    **kwargs
        When backend is a str, forwarded to the backend constructor.
    """

    def __init__(
        self,
        backend: str | ReadBackend[str, Any],
        *,
        readonly: bool | None = None,
        **kwargs: Any,
    ):
        if isinstance(backend, str):
            from ._registry import get_backend_cls, parse_uri

            scheme, _remainder = parse_uri(backend)
            cls = get_backend_cls(backend, readonly=readonly)
            if scheme is not None and hasattr(cls, "from_uri"):
                self._backend: ReadBackend[str, Any] = cls.from_uri(backend, **kwargs)
            else:
                self._backend = cls(backend, **kwargs)
        else:
            self._backend = backend

    def keys(self, index: int) -> list[str]:
        """Return keys present at *index*."""
        return self._backend.keys(index)

    # --- Internal methods used by views ---

    def _read_row(self, index: int, keys: list[str] | None = None) -> dict[str, Any]:
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

    def _write_row(self, index: int, data: Any) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.set(index, data)

    def _update_row(self, index: int, data: dict[str, Any]) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.update(index, data)

    def _update_many(self, start: int, data: list) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.update_many(start, data)

    def _set_column(self, key, start: int, values: list) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.set_column(key, start, values)

    def _write_many(self, start: int, data: list) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.set_many(start, data)

    def _delete_row(self, index: int) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.delete(index)

    def _delete_rows(self, start: int, stop: int) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.delete_many(start, stop)

    def _drop_keys(self, keys: list[str], indices: list[int]) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.drop_keys(keys, indices)

    def _build_result(self, row: dict[str, Any]) -> dict[str, Any]:
        """Identity transform -- returns dict as-is.

        ASEIO overrides this to call dict_to_atoms.
        """
        return row

    # --- MutableSequence interface ---

    @overload
    def __getitem__(self, index: int) -> dict[str, Any]: ...
    @overload
    def __getitem__(self, index: slice) -> RowView[dict[str, Any]]: ...
    @overload
    def __getitem__(self, index: list[int]) -> RowView[dict[str, Any]]: ...
    @overload
    def __getitem__(self, index: str) -> ColumnView: ...
    @overload
    def __getitem__(self, index: list[str]) -> ColumnView: ...

    def __getitem__(
        self,
        index: int | slice | str | list[int] | list[str],
    ) -> dict[str, Any] | RowView[dict[str, Any]] | ColumnView:
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

    def extend(self, values) -> int:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        return self._backend.extend(list(values))

    def get(self, index: int, keys: list[str] | None = None) -> dict[str, Any] | None:
        """Read a single row, optionally filtering to specific keys."""
        return self._backend.get(index, keys)

    def update(self, index: int, data: dict[str, Any]) -> None:
        """Partial update: merge *data* into existing row at *index*."""
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.update(index, data)

    def drop(self, *, keys: list[str]) -> None:
        """Remove specified columns from all rows."""
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.drop_keys(keys)

    def reserve(self, count: int) -> None:
        """Pre-allocate space for `count` additional rows (hint to backend)."""
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.reserve(count)

    def clear(self) -> None:
        """Remove all rows but keep the container."""
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.clear()

    def remove(self) -> None:
        """Remove the entire container (backend-specific)."""
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.remove()

    def __len__(self) -> int:
        return len(self._backend)

    def __iter__(self) -> Iterator[dict[str, Any]]:
        for i in range(len(self)):
            yield self[i]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self._backend, "close"):
            self._backend.close()
        return False

    def __repr__(self) -> str:
        return f"ObjectIO(backend={self._backend!r})"
