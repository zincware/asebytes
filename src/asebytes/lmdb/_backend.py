from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import msgpack
import msgpack_numpy as m

from ._bytesio import BytesIO
from .._protocols import ReadableBackend, WritableBackend


class LMDBReadOnlyBackend(ReadableBackend):
    """Read-only LMDB storage backend using msgpack serialization.

    Wraps BytesIO for LMDB operations, converting between
    dict[str, Any] (logical) and dict[bytes, bytes] (storage).

    Parameters
    ----------
    file : str
        Path to LMDB database file.
    prefix : bytes
        Key prefix for namespacing.
    map_size : int
        Maximum LMDB size in bytes (default 10GB).
    **lmdb_kwargs
        Additional kwargs for lmdb.open().
    """

    def __init__(
        self,
        file: str,
        prefix: bytes = b"",
        map_size: int = 10737418240,
        **lmdb_kwargs,
    ):
        self._store = BytesIO(file, prefix, map_size, readonly=True, **lmdb_kwargs)

    @property
    def env(self):
        """Expose the LMDB environment for configuration inspection."""
        return self._store.env

    def _deserialize_row(self, raw: dict[bytes, bytes]) -> dict[str, Any]:
        return {
            k.decode(): msgpack.unpackb(v, object_hook=m.decode)
            for k, v in raw.items()
        }

    def __len__(self) -> int:
        return len(self._store)

    def _check_index(self, index: int) -> None:
        if index < 0 or index >= len(self._store):
            raise IndexError(index)

    def columns(self, index: int = 0) -> list[str]:
        self._check_index(index)
        keys = self._store.get_available_keys(index)
        return [k.decode() for k in keys]

    def read_row(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any]:
        self._check_index(index)
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        raw = self._store.get(index, keys=byte_keys)
        return self._deserialize_row(raw)

    def iter_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> Iterator[dict[str, Any]]:
        """Stream rows within a single LMDB read transaction."""
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        with self._store.env.begin() as txn:
            for i in indices:
                yield self._deserialize_row(
                    self._store.get_with_txn(txn, i, byte_keys)
                )

    def read_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any]]:
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        with self._store.env.begin() as txn:
            return [
                self._deserialize_row(self._store.get_with_txn(txn, i, byte_keys))
                for i in indices
            ]

    def read_column(
        self, key: str, indices: list[int] | None = None
    ) -> list[Any]:
        if indices is None:
            indices = list(range(len(self)))
        byte_key = key.encode()
        with self._store.env.begin() as txn:
            return [
                msgpack.unpackb(
                    self._store.get_with_txn(txn, i, [byte_key])[byte_key],
                    object_hook=m.decode,
                )
                for i in indices
            ]


class LMDBBackend(LMDBReadOnlyBackend, WritableBackend):
    """Read-write LMDB storage backend using msgpack serialization.

    Extends LMDBReadOnlyBackend with write operations.

    Parameters
    ----------
    file : str
        Path to LMDB database file.
    prefix : bytes
        Key prefix for namespacing.
    map_size : int
        Maximum LMDB size in bytes (default 10GB).
    readonly : bool
        Open in read-only mode.
    **lmdb_kwargs
        Additional kwargs for lmdb.open().
    """

    def __init__(
        self,
        file: str,
        prefix: bytes = b"",
        map_size: int = 10737418240,
        readonly: bool = False,
        **lmdb_kwargs,
    ):
        self._store = BytesIO(file, prefix, map_size, readonly, **lmdb_kwargs)

    def _serialize_row(self, data: dict[str, Any]) -> dict[bytes, bytes]:
        return {
            k.encode(): msgpack.packb(v, default=m.encode)
            for k, v in data.items()
        }

    def write_row(self, index: int, data: dict[str, Any]) -> None:
        self._store[index] = self._serialize_row(data)

    def insert_row(self, index: int, data: dict[str, Any]) -> None:
        self._store.insert(index, self._serialize_row(data))

    def delete_row(self, index: int) -> None:
        del self._store[index]

    def append_rows(self, data: list[dict[str, Any]]) -> None:
        self._store.extend([self._serialize_row(d) for d in data])

    def update_row(self, index: int, data: dict[str, Any]) -> None:
        """Optimized partial update — only serializes and writes changed keys."""
        raw = {k.encode(): msgpack.packb(v, default=m.encode) for k, v in data.items()}
        self._check_index(index)
        self._store.update(index, raw)
