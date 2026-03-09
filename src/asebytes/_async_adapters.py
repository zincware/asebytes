"""Async adapters that convert between blob-level and object-level async backends.

AsyncBlobToObjectReadAdapter wraps an AsyncReadBackend[bytes, bytes] and presents
an AsyncReadBackend[str, Any] by deserialising values with msgpack.

AsyncBlobToObjectReadWriteAdapter extends this with write methods that
serialise dict[str, Any] -> dict[bytes, bytes] before delegating.

AsyncObjectToBlobReadAdapter wraps an AsyncReadBackend[str, Any] and presents
an AsyncReadBackend[bytes, bytes] by serialising values with msgpack.

AsyncObjectToBlobReadWriteAdapter extends this with write methods that
deserialise dict[bytes, bytes] -> dict[str, Any] before delegating.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import msgpack
import msgpack_numpy as m

from ._adapters import _deserialize_row, _serialize_row
from ._async_backends import AsyncReadBackend, AsyncReadWriteBackend


# ── AsyncBlobToObject read adapter ────────────────────────────────────────


class AsyncBlobToObjectReadAdapter(AsyncReadBackend[str, Any]):
    """Wraps an AsyncReadBackend[bytes, bytes] and exposes AsyncReadBackend[str, Any].

    Byte-keyed dicts are deserialized on read using msgpack + msgpack_numpy.
    None placeholders pass through unchanged.
    """

    def __init__(self, store: AsyncReadBackend[bytes, bytes]) -> None:
        self._store = store

    @staticmethod
    def list_groups(path: str, **kwargs: Any) -> list[str]:
        """Adapters don't have direct path access; raise NotImplementedError.

        Use the underlying backend's list_groups directly instead.
        """
        raise NotImplementedError(
            "AsyncBlobToObjectReadAdapter wraps an existing backend instance. "
            "Call list_groups on the underlying backend class instead."
        )

    async def len(self) -> int:
        return await self._store.len()

    async def get(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any] | None:
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        raw = await self._store.get(index, byte_keys)
        if raw is None:
            return None
        return _deserialize_row(raw)

    async def get_many(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any] | None]:
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        raw_rows = await self._store.get_many(indices, byte_keys)
        return [None if row is None else _deserialize_row(row) for row in raw_rows]

    async def iter_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> AsyncIterator[dict[str, Any] | None]:
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        async for raw in self._store.iter_rows(indices, byte_keys):
            if raw is None:
                yield None
            else:
                yield _deserialize_row(raw)

    async def get_column(self, key: str, indices: list[int] | None = None) -> list[Any]:
        byte_key = key.encode()
        raw_col = await self._store.get_column(byte_key, indices)
        return [msgpack.unpackb(v, object_hook=m.decode) for v in raw_col]

    async def keys(self, index: int) -> list[str]:
        raw_keys = await self._store.keys(index)
        return [k.decode() for k in raw_keys]


# ── AsyncBlobToObject read-write adapter ──────────────────────────────────


class AsyncBlobToObjectReadWriteAdapter(
    AsyncBlobToObjectReadAdapter, AsyncReadWriteBackend[str, Any]
):
    """Wraps an AsyncReadWriteBackend[bytes, bytes] and exposes AsyncReadWriteBackend[str, Any].

    Inherits all read methods from AsyncBlobToObjectReadAdapter.
    Write methods serialise dict[str, Any] -> dict[bytes, bytes] via msgpack
    before delegating to the inner backend.  None placeholders pass through.
    """

    _store: AsyncReadWriteBackend[bytes, bytes]

    def __init__(self, store: AsyncReadWriteBackend[bytes, bytes]) -> None:
        super().__init__(store)

    async def set(self, index: int, value: dict[str, Any] | None) -> None:
        if value is None:
            await self._store.set(index, None)
        else:
            await self._store.set(index, _serialize_row(value))

    async def delete(self, index: int) -> None:
        await self._store.delete(index)

    async def extend(self, values: list[dict[str, Any] | None]) -> int:
        return await self._store.extend(
            [_serialize_row(v) if v is not None else None for v in values]
        )

    async def insert(self, index: int, value: dict[str, Any] | None) -> None:
        if value is None:
            await self._store.insert(index, None)
        else:
            await self._store.insert(index, _serialize_row(value))

    async def update(self, index: int, data: dict[str, Any]) -> None:
        await self._store.update(index, _serialize_row(data))

    async def update_many(self, start: int, data: list[dict[str, Any]]) -> None:
        await self._store.update_many(start, [_serialize_row(d) for d in data])

    async def set_column(self, key: str, start: int, values: list[Any]) -> None:
        await self._store.set_column(
            key.encode(),
            start,
            [msgpack.packb(v, default=m.encode) for v in values],
        )

    async def clear(self) -> None:
        await self._store.clear()

    async def remove(self) -> None:
        await self._store.remove()

    async def drop_keys(
        self,
        keys: list[str],
        indices: list[int] | None = None,
    ) -> None:
        await self._store.drop_keys(
            [k.encode() for k in keys],
            indices=indices,
        )


# ── AsyncObjectToBlob read adapter ───────────────────────────────────────


class AsyncObjectToBlobReadAdapter(AsyncReadBackend[bytes, bytes]):
    """Wraps an AsyncReadBackend[str, Any] and exposes AsyncReadBackend[bytes, bytes].

    Str-keyed dicts are serialized on read using msgpack + msgpack_numpy.
    None placeholders pass through unchanged.
    """

    def __init__(self, store: AsyncReadBackend[str, Any]) -> None:
        self._store = store

    @staticmethod
    def list_groups(path: str, **kwargs: Any) -> list[str]:
        """Adapters don't have direct path access; raise NotImplementedError.

        Use the underlying backend's list_groups directly instead.
        """
        raise NotImplementedError(
            "AsyncObjectToBlobReadAdapter wraps an existing backend instance. "
            "Call list_groups on the underlying backend class instead."
        )

    async def len(self) -> int:
        return await self._store.len()

    async def get(
        self, index: int, keys: list[bytes] | None = None
    ) -> dict[bytes, bytes] | None:
        str_keys = [k.decode() for k in keys] if keys is not None else None
        row = await self._store.get(index, str_keys)
        if row is None:
            return None
        return _serialize_row(row)

    async def get_many(
        self, indices: list[int], keys: list[bytes] | None = None
    ) -> list[dict[bytes, bytes] | None]:
        str_keys = [k.decode() for k in keys] if keys is not None else None
        rows = await self._store.get_many(indices, str_keys)
        return [None if row is None else _serialize_row(row) for row in rows]

    async def iter_rows(
        self, indices: list[int], keys: list[bytes] | None = None
    ) -> AsyncIterator[dict[bytes, bytes] | None]:
        str_keys = [k.decode() for k in keys] if keys is not None else None
        async for row in self._store.iter_rows(indices, str_keys):
            if row is None:
                yield None
            else:
                yield _serialize_row(row)

    async def get_column(
        self, key: bytes, indices: list[int] | None = None
    ) -> list[bytes]:
        str_key = key.decode()
        col = await self._store.get_column(str_key, indices)
        return [msgpack.packb(v, default=m.encode) for v in col]

    async def keys(self, index: int) -> list[bytes]:
        str_keys = await self._store.keys(index)
        return [k.encode() for k in str_keys]


# ── AsyncObjectToBlob read-write adapter ─────────────────────────────────


class AsyncObjectToBlobReadWriteAdapter(
    AsyncObjectToBlobReadAdapter, AsyncReadWriteBackend[bytes, bytes]
):
    """Wraps an AsyncReadWriteBackend[str, Any] and exposes AsyncReadWriteBackend[bytes, bytes].

    Inherits all read methods from AsyncObjectToBlobReadAdapter.
    Write methods deserialise dict[bytes, bytes] -> dict[str, Any] via msgpack
    before delegating to the inner backend.  None placeholders pass through.
    """

    _store: AsyncReadWriteBackend[str, Any]

    def __init__(self, store: AsyncReadWriteBackend[str, Any]) -> None:
        super().__init__(store)

    async def set(self, index: int, value: dict[bytes, bytes] | None) -> None:
        if value is None:
            await self._store.set(index, None)
        else:
            await self._store.set(index, _deserialize_row(value))

    async def delete(self, index: int) -> None:
        await self._store.delete(index)

    async def extend(self, values: list[dict[bytes, bytes] | None]) -> int:
        return await self._store.extend(
            [_deserialize_row(v) if v is not None else None for v in values]
        )

    async def insert(self, index: int, value: dict[bytes, bytes] | None) -> None:
        if value is None:
            await self._store.insert(index, None)
        else:
            await self._store.insert(index, _deserialize_row(value))

    async def update(self, index: int, data: dict[bytes, bytes]) -> None:
        await self._store.update(index, _deserialize_row(data))

    async def update_many(self, start: int, data: list[dict[bytes, bytes]]) -> None:
        await self._store.update_many(start, [_deserialize_row(d) for d in data])

    async def set_column(self, key: bytes, start: int, values: list[bytes]) -> None:
        await self._store.set_column(
            key.decode(),
            start,
            [msgpack.unpackb(v, object_hook=m.decode) for v in values],
        )

    async def clear(self) -> None:
        await self._store.clear()

    async def remove(self) -> None:
        await self._store.remove()

    async def drop_keys(
        self,
        keys: list[bytes],
        indices: list[int] | None = None,
    ) -> None:
        await self._store.drop_keys(
            [k.decode() for k in keys],
            indices=indices,
        )
