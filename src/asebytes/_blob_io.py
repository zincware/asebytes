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
    backend : ReadBackend[bytes, bytes] | ReadWriteBackend[bytes, bytes]
        A blob-level backend instance.
    """

    def __init__(self, backend: ReadBackend[bytes, bytes]):
        self._backend = backend

    @property
    def schema(self) -> list[bytes]:
        """Return the global schema (union of all field names)."""
        return self._backend.schema()

    # --- Internal methods used by views ---

    def _read_row(
        self, index: int, keys: list[str] | None = None
    ) -> dict[bytes, bytes] | None:
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        return self._backend.get(index, byte_keys)

    def _read_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[bytes, bytes] | None]:
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        return self._backend.get_many(indices, byte_keys)

    def _iter_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> Iterator[dict[bytes, bytes] | None]:
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        return self._backend.iter_rows(indices, byte_keys)

    def _read_column(self, key: str, indices: list[int]) -> list[Any]:
        byte_key = key.encode()
        return self._backend.get_column(byte_key, indices)

    def _build_atoms(self, row: Any) -> Any:
        """Identity transform -- returns raw dict[bytes, bytes] as-is."""
        return row

    # --- MutableSequence interface ---

    def __getitem__(self, index: int) -> dict[bytes, bytes]:
        return self._backend.get(index)

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

    def __len__(self) -> int:
        return len(self._backend)

    def __iter__(self) -> Iterator[dict[bytes, bytes]]:
        for i in range(len(self)):
            yield self[i]
