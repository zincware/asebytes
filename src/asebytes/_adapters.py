"""Adapters that convert between blob-level and object-level backends.

BlobToObjectReadAdapter wraps a ReadBackend[bytes, bytes] and presents
a ReadBackend[str, Any] by deserialising values with msgpack.

BlobToObjectReadWriteAdapter extends this with write methods that
serialise dict[str, Any] -> dict[bytes, bytes] before delegating.

ObjectToBlobReadAdapter wraps a ReadBackend[str, Any] and presents
a ReadBackend[bytes, bytes] by serialising values with msgpack.

ObjectToBlobReadWriteAdapter extends this with write methods that
deserialise dict[bytes, bytes] -> dict[str, Any] before delegating.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import msgpack
import msgpack_numpy as m

from ._backends import ReadBackend, ReadWriteBackend


# ── Conversion helpers ────────────────────────────────────────────────────


def _deserialize_row(raw: dict[bytes, bytes]) -> dict[str, Any]:
    return {k.decode(): msgpack.unpackb(v, object_hook=m.decode) for k, v in raw.items()}


def _serialize_row(data: dict[str, Any]) -> dict[bytes, bytes]:
    return {k.encode(): msgpack.packb(v, default=m.encode) for k, v in data.items()}


# ── Read adapter ──────────────────────────────────────────────────────────


class BlobToObjectReadAdapter(ReadBackend[str, Any]):
    """Wraps a ReadBackend[bytes, bytes] and exposes ReadBackend[str, Any].

    Byte-keyed dicts are deserialized on read using msgpack + msgpack_numpy.
    None placeholders pass through unchanged.
    """

    def __init__(self, store: ReadBackend[bytes, bytes]) -> None:
        self._store = store

    def __len__(self) -> int:
        return len(self._store)

    def get(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any] | None:
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        raw = self._store.get(index, byte_keys)
        if raw is None:
            return None
        return _deserialize_row(raw)

    def get_many(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any] | None]:
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        raw_rows = self._store.get_many(indices, byte_keys)
        return [
            None if row is None else _deserialize_row(row)
            for row in raw_rows
        ]

    def iter_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> Iterator[dict[str, Any] | None]:
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        for raw in self._store.iter_rows(indices, byte_keys):
            if raw is None:
                yield None
            else:
                yield _deserialize_row(raw)

    def get_column(self, key: str, indices: list[int] | None = None) -> list[Any]:
        byte_key = key.encode()
        raw_col = self._store.get_column(byte_key, indices)
        return [msgpack.unpackb(v, object_hook=m.decode) for v in raw_col]

    def keys(self, index: int) -> list[str]:
        raw_keys = self._store.keys(index)
        return [k.decode() for k in raw_keys]


# ── Read-write adapter ───────────────────────────────────────────────────


class BlobToObjectReadWriteAdapter(BlobToObjectReadAdapter, ReadWriteBackend[str, Any]):
    """Wraps a ReadWriteBackend[bytes, bytes] and exposes ReadWriteBackend[str, Any].

    Inherits all read methods from BlobToObjectReadAdapter.
    Write methods serialise dict[str, Any] -> dict[bytes, bytes] via msgpack
    before delegating to the inner backend.  None placeholders pass through.
    """

    _store: ReadWriteBackend[bytes, bytes]

    def __init__(self, store: ReadWriteBackend[bytes, bytes]) -> None:
        super().__init__(store)

    def set(self, index: int, value: dict[str, Any] | None) -> None:
        if value is None:
            self._store.set(index, None)
        else:
            self._store.set(index, _serialize_row(value))

    def delete(self, index: int) -> None:
        self._store.delete(index)

    def extend(self, values: list[dict[str, Any] | None]) -> int:
        return self._store.extend([
            _serialize_row(v) if v is not None else None
            for v in values
        ])

    def insert(self, index: int, value: dict[str, Any] | None) -> None:
        if value is None:
            self._store.insert(index, None)
        else:
            self._store.insert(index, _serialize_row(value))

    def update(self, index: int, data: dict[str, Any]) -> None:
        self._store.update(index, _serialize_row(data))

    def clear(self) -> None:
        self._store.clear()

    def remove(self) -> None:
        self._store.remove()

    def drop_keys(
        self,
        keys: list[str],
        indices: list[int] | None = None,
    ) -> None:
        self._store.drop_keys(
            [k.encode() for k in keys],
            indices=indices,
        )


# ── ObjectToBlob read adapter ────────────────────────────────────────────


class ObjectToBlobReadAdapter(ReadBackend[bytes, bytes]):
    """Wraps a ReadBackend[str, Any] and exposes ReadBackend[bytes, bytes].

    Str-keyed dicts are serialized on read using msgpack + msgpack_numpy.
    None placeholders pass through unchanged.
    """

    def __init__(self, store: ReadBackend[str, Any]) -> None:
        self._store = store

    def __len__(self) -> int:
        return len(self._store)

    def get(
        self, index: int, keys: list[bytes] | None = None
    ) -> dict[bytes, bytes] | None:
        str_keys = [k.decode() for k in keys] if keys is not None else None
        row = self._store.get(index, str_keys)
        if row is None:
            return None
        return _serialize_row(row)

    def get_many(
        self, indices: list[int], keys: list[bytes] | None = None
    ) -> list[dict[bytes, bytes] | None]:
        str_keys = [k.decode() for k in keys] if keys is not None else None
        rows = self._store.get_many(indices, str_keys)
        return [
            None if row is None else _serialize_row(row)
            for row in rows
        ]

    def iter_rows(
        self, indices: list[int], keys: list[bytes] | None = None
    ) -> Iterator[dict[bytes, bytes] | None]:
        str_keys = [k.decode() for k in keys] if keys is not None else None
        for row in self._store.iter_rows(indices, str_keys):
            if row is None:
                yield None
            else:
                yield _serialize_row(row)

    def get_column(self, key: bytes, indices: list[int] | None = None) -> list[bytes]:
        str_key = key.decode()
        col = self._store.get_column(str_key, indices)
        return [msgpack.packb(v, default=m.encode) for v in col]

    def keys(self, index: int) -> list[bytes]:
        str_keys = self._store.keys(index)
        return [k.encode() for k in str_keys]


# ── ObjectToBlob read-write adapter ──────────────────────────────────────


class ObjectToBlobReadWriteAdapter(ObjectToBlobReadAdapter, ReadWriteBackend[bytes, bytes]):
    """Wraps a ReadWriteBackend[str, Any] and exposes ReadWriteBackend[bytes, bytes].

    Inherits all read methods from ObjectToBlobReadAdapter.
    Write methods deserialise dict[bytes, bytes] -> dict[str, Any] via msgpack
    before delegating to the inner backend.  None placeholders pass through.
    """

    _store: ReadWriteBackend[str, Any]

    def __init__(self, store: ReadWriteBackend[str, Any]) -> None:
        super().__init__(store)

    def set(self, index: int, value: dict[bytes, bytes] | None) -> None:
        if value is None:
            self._store.set(index, None)
        else:
            self._store.set(index, _deserialize_row(value))

    def delete(self, index: int) -> None:
        self._store.delete(index)

    def extend(self, values: list[dict[bytes, bytes] | None]) -> int:
        return self._store.extend([
            _deserialize_row(v) if v is not None else None
            for v in values
        ])

    def insert(self, index: int, value: dict[bytes, bytes] | None) -> None:
        if value is None:
            self._store.insert(index, None)
        else:
            self._store.insert(index, _deserialize_row(value))

    def update(self, index: int, data: dict[bytes, bytes]) -> None:
        self._store.update(index, _deserialize_row(data))
