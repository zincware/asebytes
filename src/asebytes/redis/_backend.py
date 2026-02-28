"""Redis blob-level backend using hashes for row storage."""

from __future__ import annotations

from typing import Any

import redis as redis_mod

from .._backends import ReadWriteBackend


class RedisBlobBackend(ReadWriteBackend[bytes, bytes]):
    """Redis-backed read-write backend for blob dictionaries.

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
        self._r = redis_mod.Redis.from_url(url, decode_responses=False)
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

    def _resolve_index(self, index: int) -> int:
        """Normalise a (possibly negative) index and return the sort key."""
        n = self._r.llen(self._sk_list_key)
        if index < 0:
            index += n
        if index < 0 or index >= n:
            raise IndexError(index)
        sk_bytes = self._r.lindex(self._sk_list_key, index)
        return int(sk_bytes)

    def _allocate_sk(self) -> int:
        """Atomically allocate the next sort key."""
        return self._r.incr(self._next_sk_key) - 1

    # ------------------------------------------------------------------
    # from_uri constructor
    # ------------------------------------------------------------------

    @classmethod
    def from_uri(cls, uri: str, **kwargs: Any) -> RedisBlobBackend:
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
    # ReadBackend implementation
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return self._r.llen(self._sk_list_key)

    def get(
        self, index: int, keys: list[bytes] | None = None
    ) -> dict[bytes, bytes] | None:
        sk = self._resolve_index(index)
        rk = self._row_key(sk)
        if not self._r.exists(rk):
            return None
        if keys is not None:
            pipe = self._r.pipeline()
            for k in keys:
                pipe.hget(rk, k)
            vals = pipe.execute()
            return {k: v for k, v in zip(keys, vals) if v is not None}
        return self._r.hgetall(rk)

    def get_many(
        self, indices: list[int], keys: list[bytes] | None = None
    ) -> list[dict[bytes, bytes] | None]:
        sks = [self._resolve_index(i) for i in indices]
        pipe = self._r.pipeline()
        for sk in sks:
            rk = self._row_key(sk)
            pipe.exists(rk)
            if keys is not None:
                for k in keys:
                    pipe.hget(rk, k)
            else:
                pipe.hgetall(rk)
        raw = pipe.execute()

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

    def get_column(
        self, key: bytes, indices: list[int] | None = None
    ) -> list[Any]:
        if indices is None:
            indices = list(range(len(self)))
        sks = [self._resolve_index(i) for i in indices]
        pipe = self._r.pipeline()
        for sk in sks:
            rk = self._row_key(sk)
            pipe.exists(rk)
            pipe.hget(rk, key)
        raw = pipe.execute()

        results: list[Any] = []
        for i in range(0, len(raw), 2):
            exists = raw[i]
            val = raw[i + 1]
            if not exists:
                results.append(None)
            else:
                results.append(val)
        return results

    def keys(self, index: int) -> list[bytes]:
        sk = self._resolve_index(index)
        rk = self._row_key(sk)
        if not self._r.exists(rk):
            return []
        return self._r.hkeys(rk)

    # ------------------------------------------------------------------
    # ReadWriteBackend implementation
    # ------------------------------------------------------------------

    def set(self, index: int, value: dict[bytes, bytes] | None) -> None:
        sk = self._resolve_index(index)
        rk = self._row_key(sk)
        pipe = self._r.pipeline()
        pipe.delete(rk)
        if value is not None:
            pipe.hset(rk, mapping=value)
        pipe.execute()

    def delete(self, index: int) -> None:
        sk = self._resolve_index(index)
        rk = self._row_key(sk)
        pipe = self._r.pipeline()
        pipe.delete(rk)
        pipe.lrem(self._sk_list_key, 1, str(sk).encode())
        pipe.execute()

    def extend(self, values: list[dict[bytes, bytes] | None]) -> int:
        if not values:
            return len(self)
        pipe = self._r.pipeline()
        sk_list: list[int] = []
        for v in values:
            sk = self._allocate_sk()
            sk_list.append(sk)
            if v is not None:
                pipe.hset(self._row_key(sk), mapping=v)
        for sk in sk_list:
            pipe.rpush(self._sk_list_key, str(sk).encode())
        pipe.execute()
        return self._r.llen(self._sk_list_key)

    def insert(self, index: int, value: dict[bytes, bytes] | None) -> None:
        n = self._r.llen(self._sk_list_key)
        if index < 0:
            index = 0
        if index > n:
            index = n

        sk = self._allocate_sk()
        if value is not None:
            self._r.hset(self._row_key(sk), mapping=value)

        sk_bytes = str(sk).encode()

        if index == n:
            # Append at end
            self._r.rpush(self._sk_list_key, sk_bytes)
        elif index == 0:
            # Prepend at beginning
            self._r.lpush(self._sk_list_key, sk_bytes)
        else:
            # Insert in the middle: read the pivot element, insert before it
            # Redis LINSERT requires a pivot value. Since sort keys are unique
            # we can use the element at `index` as the pivot.
            pivot = self._r.lindex(self._sk_list_key, index)
            self._r.linsert(self._sk_list_key, "BEFORE", pivot, sk_bytes)

    def update(self, index: int, data: dict[bytes, bytes]) -> None:
        if not data:
            return
        sk = self._resolve_index(index)
        rk = self._row_key(sk)
        # If row was None, create it
        self._r.hset(rk, mapping=data)

    def drop_keys(
        self, keys: list[bytes], indices: list[int] | None = None
    ) -> None:
        if indices is None:
            indices = list(range(len(self)))
        sks = [self._resolve_index(i) for i in indices]
        pipe = self._r.pipeline()
        for sk in sks:
            rk = self._row_key(sk)
            for k in keys:
                pipe.hdel(rk, k)
        pipe.execute()

    def clear(self) -> None:
        """Remove all row data and reset metadata."""
        # Collect all sort keys
        all_sks = self._r.lrange(self._sk_list_key, 0, -1)
        pipe = self._r.pipeline()
        for sk_bytes in all_sks:
            pipe.delete(self._row_key(int(sk_bytes)))
        pipe.delete(self._sk_list_key)
        pipe.delete(self._next_sk_key)
        pipe.execute()

    def remove(self) -> None:
        """Delete all Redis keys with this prefix."""
        cursor = 0
        pattern = f"{self._prefix}:*"
        while True:
            cursor, keys = self._r.scan(cursor=cursor, match=pattern, count=200)
            if keys:
                self._r.delete(*keys)
            if cursor == 0:
                break
