"""BlobIO -- MutableSequence facade for blob-level backends.

Delegates to a ReadBackend[bytes, bytes] or ReadWriteBackend[bytes, bytes].
"""

from __future__ import annotations

from collections.abc import Iterator, MutableSequence
from typing import Any, overload

from ._backends import ReadBackend, ReadWriteBackend
from ._views import ColumnView, RowView


class BlobIO(MutableSequence):
    """Storage-agnostic mutable sequence for dict[bytes, bytes] rows.

    Parameters
    ----------
    backend : str | ReadBackend[bytes, bytes]
        Either a file path (auto-creates blob backend via registry) or a
        backend instance.
    readonly : bool | None
        Force read-only or writable mode. None (default) auto-detects.
        Only used when *backend* is a string.
    **kwargs
        When backend is a str, forwarded to the backend constructor.
    """

    def __init__(
        self,
        backend: str | ReadBackend[bytes, bytes],
        *,
        readonly: bool | None = None,
        **kwargs: Any,
    ):
        if isinstance(backend, str):
            from ._registry import get_blob_backend_cls

            cls = get_blob_backend_cls(backend, readonly=readonly)
            self._backend: ReadBackend[bytes, bytes] = cls(backend, **kwargs)
        else:
            self._backend = backend

    def keys(self, index: int) -> list[bytes]:
        """Return keys present at *index*."""
        return self._backend.keys(index)

    # --- Internal methods used by views ---

    def _read_row(
        self, index: int, keys: list[bytes] | None = None
    ) -> dict[bytes, bytes] | None:
        return self._backend.get(index, keys)

    def _read_rows(
        self, indices: list[int], keys: list[bytes] | None = None
    ) -> list[dict[bytes, bytes] | None]:
        return self._backend.get_many(indices, keys)

    def _iter_rows(
        self, indices: list[int], keys: list[bytes] | None = None
    ) -> Iterator[dict[bytes, bytes] | None]:
        return self._backend.iter_rows(indices, keys)

    def _read_column(self, key: bytes, indices: list[int]) -> list[Any]:
        return self._backend.get_column(key, indices)

    def _write_row(self, index: int, data: Any) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.set(index, data)

    def _update_row(self, index: int, data: Any) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.update(index, data)

    def _delete_row(self, index: int) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.delete(index)

    def _delete_rows(self, start: int, stop: int) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.delete_many(start, stop)

    def _build_result(self, row: Any) -> dict[bytes, bytes]:
        """Identity transform -- returns raw dict[bytes, bytes] as-is."""
        return row

    # --- MutableSequence interface ---

    @overload
    def __getitem__(self, index: int) -> dict[bytes, bytes]: ...
    @overload
    def __getitem__(self, index: slice) -> RowView[dict[bytes, bytes]]: ...
    @overload
    def __getitem__(self, index: list[int]) -> RowView[dict[bytes, bytes]]: ...
    @overload
    def __getitem__(self, index: str) -> ColumnView: ...
    @overload
    def __getitem__(self, index: bytes) -> ColumnView: ...
    @overload
    def __getitem__(self, index: list[str]) -> ColumnView: ...
    @overload
    def __getitem__(self, index: list[bytes]) -> ColumnView: ...

    def __getitem__(
        self,
        index: int | slice | str | bytes | list[int] | list[str] | list[bytes],
    ) -> dict[bytes, bytes] | RowView[dict[bytes, bytes]] | ColumnView:
        if isinstance(index, int):
            return self._backend.get(index)
        if isinstance(index, slice):
            indices = range(len(self))[index]
            return RowView(self, list(indices))
        if isinstance(index, (bytes, str)):
            return ColumnView(self, index, list(range(len(self))))
        if isinstance(index, list):
            if not index:
                return RowView(self, [])
            if isinstance(index[0], int):
                return RowView(self, index)
            if isinstance(index[0], (bytes, str)):
                return ColumnView(self, index, list(range(len(self))))
        raise TypeError(f"Unsupported index type: {type(index)}")

    def __setitem__(self, index: int, value: dict[bytes, bytes]) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.set(index, value)

    def __delitem__(self, index: int) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.delete(index)

    def insert(self, index: int, value: dict[bytes, bytes]) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.insert(index, value)

    def extend(self, values) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.extend(list(values))

    def get(
        self, index: int, keys: list[bytes] | None = None
    ) -> dict[bytes, bytes] | None:
        """Read a single row, optionally filtering to specific keys."""
        return self._backend.get(index, keys)

    def update(self, index: int, data: dict[bytes, bytes]) -> None:
        """Partial update: merge *data* into existing row at *index*."""
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.update(index, data)

    def drop(self, *, keys: list[bytes]) -> None:
        """Remove specified columns from all rows."""
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.drop_keys(keys)

    def reserve(self, count: int) -> None:
        """Pre-allocate space for `count` additional rows (hint to backend)."""
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.reserve(count)

    def __len__(self) -> int:
        return len(self._backend)

    def __iter__(self) -> Iterator[dict[bytes, bytes]]:
        for i in range(len(self)):
            yield self[i]
