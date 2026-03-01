from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import msgpack
import msgpack_numpy as m

from ._blob_backend import LMDBBlobBackend
from .._adapters import (
    BlobToObjectReadAdapter,
    BlobToObjectReadWriteAdapter,
    _deserialize_row,
)


class LMDBObjectReadBackend(BlobToObjectReadAdapter):
    """Read-only LMDB storage backend using msgpack serialization.

    Wraps LMDBBlobBackend for LMDB operations, converting between
    dict[str, Any] (logical) and dict[bytes, bytes] (storage).

    Inherits generic ser/de logic from BlobToObjectReadAdapter and
    overrides iter_rows, get_many, get_column to use single-transaction
    LMDB reads via get_with_txn for efficiency.

    Parameters
    ----------
    file : str
        Path to LMDB database directory.
    group : str | None
        Group name for namespacing. If None, uses "default".
    map_size : int
        Maximum LMDB size in bytes (default 10GB).
    **lmdb_kwargs
        Additional kwargs for lmdb.open().
    """

    def __init__(
        self,
        file: str,
        group: str | None = None,
        map_size: int = 10737418240,
        **lmdb_kwargs,
    ):
        super().__init__(
            LMDBBlobBackend(file, group, map_size, readonly=True, **lmdb_kwargs)
        )

    @staticmethod
    def list_groups(path: str, **kwargs) -> list[str]:
        """Return available group names at the given path."""
        return LMDBBlobBackend.list_groups(path, **kwargs)

    @property
    def env(self):
        """Expose the LMDB environment for configuration inspection."""
        return self._store.env

    def _check_index(self, index: int) -> None:
        if index < 0 or index >= len(self._store):
            raise IndexError(index)

    # -- LMDB-specific overrides -------------------------------------------

    def get(self, index: int, keys: list[str] | None = None) -> dict[str, Any] | None:
        self._check_index(index)
        return super().get(index, keys)

    def iter_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> Iterator[dict[str, Any] | None]:
        """Stream rows within a single LMDB read transaction."""
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        with self._store.env.begin() as txn:
            for i in indices:
                raw = self._store.get_with_txn(txn, i, byte_keys)
                yield None if raw is None else _deserialize_row(raw)

    def get_many(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any] | None]:
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        with self._store.env.begin() as txn:
            return [
                None
                if (raw := self._store.get_with_txn(txn, i, byte_keys)) is None
                else _deserialize_row(raw)
                for i in indices
            ]

    def get_column(self, key: str, indices: list[int] | None = None) -> list[Any]:
        if indices is None:
            indices = list(range(len(self)))
        byte_key = key.encode()
        result = []
        with self._store.env.begin() as txn:
            for i in indices:
                try:
                    raw = self._store.get_with_txn(txn, i, [byte_key])
                except KeyError:
                    result.append(None)
                    continue
                if raw is None or byte_key not in raw:
                    result.append(None)
                else:
                    result.append(msgpack.unpackb(raw[byte_key], object_hook=m.decode))
        return result


class LMDBObjectBackend(BlobToObjectReadWriteAdapter):
    """Read-write LMDB storage backend using msgpack serialization.

    Inherits generic ser/de and CRUD logic from BlobToObjectReadWriteAdapter
    and overrides iter_rows, get_many, get_column for single-transaction
    efficiency, plus update for optimised partial writes.

    Parameters
    ----------
    file : str
        Path to LMDB database directory.
    group : str | None
        Group name for namespacing. If None, uses "default".
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
        group: str | None = None,
        map_size: int = 10737418240,
        readonly: bool = False,
        **lmdb_kwargs,
    ):
        super().__init__(
            LMDBBlobBackend(file, group, map_size, readonly, **lmdb_kwargs)
        )

    @staticmethod
    def list_groups(path: str, **kwargs) -> list[str]:
        """Return available group names at the given path."""
        return LMDBBlobBackend.list_groups(path, **kwargs)

    @property
    def env(self):
        """Expose the LMDB environment for configuration inspection."""
        return self._store.env

    def _check_index(self, index: int) -> None:
        if index < 0 or index >= len(self._store):
            raise IndexError(index)

    # -- LMDB-specific overrides -------------------------------------------

    def get(self, index: int, keys: list[str] | None = None) -> dict[str, Any] | None:
        self._check_index(index)
        return super().get(index, keys)

    def iter_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> Iterator[dict[str, Any] | None]:
        """Stream rows within a single LMDB read transaction."""
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        with self._store.env.begin() as txn:
            for i in indices:
                raw = self._store.get_with_txn(txn, i, byte_keys)
                yield None if raw is None else _deserialize_row(raw)

    def get_many(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any] | None]:
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        with self._store.env.begin() as txn:
            return [
                None
                if (raw := self._store.get_with_txn(txn, i, byte_keys)) is None
                else _deserialize_row(raw)
                for i in indices
            ]

    def get_column(self, key: str, indices: list[int] | None = None) -> list[Any]:
        if indices is None:
            indices = list(range(len(self)))
        byte_key = key.encode()
        result = []
        with self._store.env.begin() as txn:
            for i in indices:
                try:
                    raw = self._store.get_with_txn(txn, i, [byte_key])
                except KeyError:
                    result.append(None)
                    continue
                if raw is None or byte_key not in raw:
                    result.append(None)
                else:
                    result.append(msgpack.unpackb(raw[byte_key], object_hook=m.decode))
        return result

    # -- Optimised partial update ------------------------------------------

    def update(self, index: int, data: dict[str, Any]) -> None:
        """Optimized partial update -- only serializes and writes changed keys."""
        raw = {k.encode(): msgpack.packb(v, default=m.encode) for k, v in data.items()}
        self._check_index(index)
        self._store.update(index, raw)
