from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import msgpack
import msgpack_numpy as m
from ._blob_backend import LMDBBlobBackend
from .._backends import ReadBackend, ReadWriteBackend


class LMDBObjectReadBackend(ReadBackend[str, Any]):
    """Read-only LMDB storage backend using msgpack serialization.

    Wraps LMDBBlobBackend for LMDB operations, converting between
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
        self._store = LMDBBlobBackend(file, prefix, map_size, readonly=True, **lmdb_kwargs)

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

    def get(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any] | None:
        self._check_index(index)
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        raw = self._store.get(index, keys=byte_keys)
        if raw is None:
            return None
        return self._deserialize_row(raw)

    def iter_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> Iterator[dict[str, Any] | None]:
        """Stream rows within a single LMDB read transaction."""
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        with self._store.env.begin() as txn:
            for i in indices:
                raw = self._store.get_with_txn(txn, i, byte_keys)
                yield None if raw is None else self._deserialize_row(raw)

    def get_many(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any] | None]:
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        with self._store.env.begin() as txn:
            return [
                None if (raw := self._store.get_with_txn(txn, i, byte_keys)) is None
                else self._deserialize_row(raw)
                for i in indices
            ]

    def get_column(
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


class LMDBObjectBackend(LMDBObjectReadBackend, ReadWriteBackend[str, Any]):
    """Read-write LMDB storage backend using msgpack serialization.

    Extends LMDBObjectReadBackend with write operations.

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
        self._store = LMDBBlobBackend(file, prefix, map_size, readonly, **lmdb_kwargs)

    def _serialize_row(self, data: dict[str, Any]) -> dict[bytes, bytes]:
        return {
            k.encode(): msgpack.packb(v, default=m.encode)
            for k, v in data.items()
        }

    def set(self, index: int, data: dict[str, Any] | None) -> None:
        if data is None:
            self._store.set(index, None)
        else:
            self._store.set(index, self._serialize_row(data))

    def insert(self, index: int, data: dict[str, Any] | None) -> None:
        if data is None:
            self._store.insert(index, None)
        else:
            self._store.insert(index, self._serialize_row(data))

    def delete(self, index: int) -> None:
        self._store.delete(index)

    def extend(self, data: list[dict[str, Any] | None]) -> None:
        self._store.extend([
            self._serialize_row(d) if d is not None else None
            for d in data
        ])

    def update(self, index: int, data: dict[str, Any]) -> None:
        """Optimized partial update -- only serializes and writes changed keys."""
        raw = {k.encode(): msgpack.packb(v, default=m.encode) for k, v in data.items()}
        self._check_index(index)
        self._store.update(index, raw)
