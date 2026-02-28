"""Async Redis blob-level backend using hashes for row storage."""

from __future__ import annotations

from typing import Any

import redis.asyncio as aioredis

from .._async_backends import AsyncReadWriteBackend


class AsyncRedisBlobBackend(AsyncReadWriteBackend[bytes, bytes]):
    """Async Redis-backed read-write backend for blob dictionaries.

    Storage layout (all keys share a ``{prefix}:`` namespace):

    * ``{prefix}:sort_keys``  -- LIST of sort-key integers (positional index)
    * ``{prefix}:next_sk``    -- STRING, monotonically increasing counter
    * ``{prefix}:row:{sk}``   -- HASH, one per row (field=bytes, value=bytes)

    A *None* row is represented by having its sort key in the list but
    **no** corresponding hash key.

    Parameters
    ----------
    url : str
        Redis connection URI, e.g. ``redis://localhost:6379/0``.
    prefix : str
        Namespace prefix (default ``"default"``).
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379",
        prefix: str = "default",
    ) -> None:
        self._r = aioredis.from_url(url, decode_responses=False)
        self._prefix = prefix

    # ------------------------------------------------------------------
    # Key helpers
    # ------------------------------------------------------------------

    @property
    def _sk_list_key(self) -> str:
        return f"{self._prefix}:sort_keys"

    @property
    def _next_sk_key(self) -> str:
        return f"{self._prefix}:next_sk"

    def _row_key(self, sk: int) -> str:
        return f"{self._prefix}:row:{sk}"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _resolve_index(self, index: int) -> int:
        """Normalise a (possibly negative) index and return the sort key."""
        n = await self._r.llen(self._sk_list_key)
        if index < 0:
            index += n
        if index < 0 or index >= n:
            raise IndexError(index)
        sk_bytes = await self._r.lindex(self._sk_list_key, index)
        return int(sk_bytes)

    async def _allocate_sk(self) -> int:
        """Atomically allocate the next sort key."""
        return await self._r.incr(self._next_sk_key) - 1

    # ------------------------------------------------------------------
    # from_uri constructor
    # ------------------------------------------------------------------

    @classmethod
    def from_uri(cls, uri: str, **kwargs: Any) -> AsyncRedisBlobBackend:
        """Construct from ``redis://host:port/db/prefix``.

        If only ``redis://host:port`` is given, db defaults to 0 and
        prefix defaults to ``"default"``.
        """
        if "://" not in uri:
            raise ValueError(f"Invalid URI: {uri!r}")
        scheme, after_scheme = uri.split("://", 1)
        if "/" in after_scheme:
            host_part, path_part = after_scheme.split("/", 1)
        else:
            host_part, path_part = after_scheme, ""

        parts = [p for p in path_part.split("/") if p]
        if len(parts) >= 2:
            db = parts[0]
            prefix = parts[1]
            connection_url = f"{scheme}://{host_part}/{db}"
        elif len(parts) == 1:
            db = parts[0]
            prefix = "default"
            connection_url = f"{scheme}://{host_part}/{db}"
        else:
            prefix = "default"
            connection_url = uri

        return cls(url=connection_url, prefix=prefix, **kwargs)

    # ------------------------------------------------------------------
    # AsyncReadBackend implementation
    # ------------------------------------------------------------------

    async def len(self) -> int:
        return await self._r.llen(self._sk_list_key)

    async def get(
        self, index: int, keys: list[bytes] | None = None
    ) -> dict[bytes, bytes] | None:
        sk = await self._resolve_index(index)
        rk = self._row_key(sk)
        if not await self._r.exists(rk):
            return None
        if keys is not None:
            pipe = self._r.pipeline(transaction=False)
            for k in keys:
                pipe.hget(rk, k)
            vals = await pipe.execute()
            return {k: v for k, v in zip(keys, vals) if v is not None}
        return await self._r.hgetall(rk)

    async def get_many(
        self, indices: list[int], keys: list[bytes] | None = None
    ) -> list[dict[bytes, bytes] | None]:
        sks = [await self._resolve_index(i) for i in indices]
        pipe = self._r.pipeline(transaction=False)
        for sk in sks:
            rk = self._row_key(sk)
            pipe.exists(rk)
            if keys is not None:
                for k in keys:
                    pipe.hget(rk, k)
            else:
                pipe.hgetall(rk)
        raw = await pipe.execute()

        results: list[dict[bytes, bytes] | None] = []
        pos = 0
        for _ in sks:
            exists = raw[pos]
            pos += 1
            if not exists:
                if keys is not None:
                    pos += len(keys)
                else:
                    pos += 1
                results.append(None)
            else:
                if keys is not None:
                    vals = raw[pos : pos + len(keys)]
                    pos += len(keys)
                    results.append(
                        {k: v for k, v in zip(keys, vals) if v is not None}
                    )
                else:
                    results.append(raw[pos])
                    pos += 1
        return results

    async def get_column(
        self, key: bytes, indices: list[int] | None = None
    ) -> list[Any]:
        if indices is None:
            indices = list(range(await self.len()))
        sks = [await self._resolve_index(i) for i in indices]
        pipe = self._r.pipeline(transaction=False)
        for sk in sks:
            rk = self._row_key(sk)
            pipe.exists(rk)
            pipe.hget(rk, key)
        raw = await pipe.execute()

        results: list[Any] = []
        for i in range(0, len(raw), 2):
            exists = raw[i]
            val = raw[i + 1]
            if not exists:
                results.append(None)
            else:
                results.append(val)
        return results

    async def keys(self, index: int) -> list[bytes]:
        sk = await self._resolve_index(index)
        rk = self._row_key(sk)
        if not await self._r.exists(rk):
            return []
        return await self._r.hkeys(rk)

    # ------------------------------------------------------------------
    # AsyncReadWriteBackend implementation
    # ------------------------------------------------------------------

    async def set(self, index: int, value: dict[bytes, bytes] | None) -> None:
        sk = await self._resolve_index(index)
        rk = self._row_key(sk)
        pipe = self._r.pipeline(transaction=False)
        pipe.delete(rk)
        if value is not None:
            pipe.hset(rk, mapping=value)
        await pipe.execute()

    async def delete(self, index: int) -> None:
        sk = await self._resolve_index(index)
        rk = self._row_key(sk)
        pipe = self._r.pipeline(transaction=False)
        pipe.delete(rk)
        pipe.lrem(self._sk_list_key, 1, str(sk).encode())
        await pipe.execute()

    async def extend(self, values: list[dict[bytes, bytes] | None]) -> int:
        if not values:
            return await self.len()
        pipe = self._r.pipeline(transaction=False)
        sk_list: list[int] = []
        for v in values:
            sk = await self._allocate_sk()
            sk_list.append(sk)
            if v is not None:
                pipe.hset(self._row_key(sk), mapping=v)
        for sk in sk_list:
            pipe.rpush(self._sk_list_key, str(sk).encode())
        await pipe.execute()
        return await self._r.llen(self._sk_list_key)

    async def insert(self, index: int, value: dict[bytes, bytes] | None) -> None:
        n = await self._r.llen(self._sk_list_key)
        if index < 0:
            index = 0
        if index > n:
            index = n

        sk = await self._allocate_sk()
        if value is not None:
            await self._r.hset(self._row_key(sk), mapping=value)

        sk_bytes = str(sk).encode()

        if index == n:
            # Append at end
            await self._r.rpush(self._sk_list_key, sk_bytes)
        elif index == 0:
            # Prepend at beginning
            await self._r.lpush(self._sk_list_key, sk_bytes)
        else:
            # Insert in the middle: read the pivot element, insert before it
            pivot = await self._r.lindex(self._sk_list_key, index)
            await self._r.linsert(self._sk_list_key, "BEFORE", pivot, sk_bytes)

    async def update(self, index: int, data: dict[bytes, bytes]) -> None:
        if not data:
            return
        sk = await self._resolve_index(index)
        rk = self._row_key(sk)
        # If row was None, create it
        await self._r.hset(rk, mapping=data)

    async def drop_keys(
        self, keys: list[bytes], indices: list[int] | None = None
    ) -> None:
        if indices is None:
            indices = list(range(await self.len()))
        sks = [await self._resolve_index(i) for i in indices]
        pipe = self._r.pipeline(transaction=False)
        for sk in sks:
            rk = self._row_key(sk)
            for k in keys:
                pipe.hdel(rk, k)
        await pipe.execute()

    async def clear(self) -> None:
        """Remove all row data and reset metadata."""
        all_sks = await self._r.lrange(self._sk_list_key, 0, -1)
        pipe = self._r.pipeline(transaction=False)
        for sk_bytes in all_sks:
            pipe.delete(self._row_key(int(sk_bytes)))
        pipe.delete(self._sk_list_key)
        pipe.delete(self._next_sk_key)
        await pipe.execute()

    async def remove(self) -> None:
        """Delete all Redis keys with this prefix."""
        cursor = 0
        pattern = f"{self._prefix}:*"
        while True:
            cursor, keys = await self._r.scan(
                cursor=cursor, match=pattern, count=200
            )
            if keys:
                await self._r.delete(*keys)
            if cursor == 0:
                break
