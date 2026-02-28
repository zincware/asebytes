"""Redis blob-level backend using hashes for row storage."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import redis as redis_mod

from .._backends import ReadWriteBackend
from ._lua import (
    LUA_DELETE,
    LUA_GET,
    LUA_GET_WITH_KEYS,
    LUA_KEYS,
    LUA_SET,
    LUA_UPDATE,
)


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
        self._scripts: dict[str, Any] | None = None

    # ------------------------------------------------------------------
    # Key helpers
    # ------------------------------------------------------------------

    @property
    def _sk_list_key(self) -> str:
        return f"{self._prefix}:sort_keys"

    @property
    def _next_sk_key(self) -> str:
        return f"{self._prefix}:next_sk"

    @property
    def _row_prefix(self) -> str:
        return f"{self._prefix}:row:"

    def _row_key(self, sk: int) -> str:
        return f"{self._prefix}:row:{sk}"

    # ------------------------------------------------------------------
    # Lua script helpers
    # ------------------------------------------------------------------

    def _ensure_scripts(self) -> dict[str, Any]:
        if self._scripts is None:
            self._scripts = {
                "get": self._r.register_script(LUA_GET),
                "get_with_keys": self._r.register_script(LUA_GET_WITH_KEYS),
                "keys": self._r.register_script(LUA_KEYS),
                "set": self._r.register_script(LUA_SET),
                "delete": self._r.register_script(LUA_DELETE),
                "update": self._r.register_script(LUA_UPDATE),
            }
        return self._scripts

    def _call_lua(self, name: str, args: list[Any] | None = None) -> Any:
        scripts = self._ensure_scripts()
        try:
            return scripts[name](
                keys=[self._sk_list_key],
                args=[self._row_prefix, *(args or [])],
            )
        except redis_mod.ResponseError as e:
            if "IndexError" in str(e):
                raise IndexError from None
            raise

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

    def _resolve_indices(self, indices: list[int]) -> list[int]:
        """Batch-resolve positional indices to sort keys (2 RTs)."""
        if not indices:
            return []
        n = self._r.llen(self._sk_list_key)
        # Normalise and validate all indices up-front
        normalised = []
        for idx in indices:
            i = idx + n if idx < 0 else idx
            if i < 0 or i >= n:
                raise IndexError(idx)
            normalised.append(i)
        # Pipeline LINDEX for all
        pipe = self._r.pipeline()
        for i in normalised:
            pipe.lindex(self._sk_list_key, i)
        sk_bytes_list = pipe.execute()
        return [int(sk) for sk in sk_bytes_list]

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
        if keys is not None:
            raw = self._call_lua("get_with_keys", [index, *keys])
        else:
            raw = self._call_lua("get", [index])
        if raw is None:
            return None
        # raw is a flat list [k1, v1, k2, v2, ...]
        it = iter(raw)
        return dict(zip(it, it))

    def get_many(
        self, indices: list[int], keys: list[bytes] | None = None
    ) -> list[dict[bytes, bytes] | None]:
        sks = self._resolve_indices(indices)
        pipe = self._r.pipeline()
        if keys is not None:
            for sk in sks:
                rk = self._row_key(sk)
                pipe.exists(rk)
                for k in keys:
                    pipe.hget(rk, k)
        else:
            for sk in sks:
                rk = self._row_key(sk)
                pipe.hgetall(rk)
        raw = pipe.execute()

        results: list[dict[bytes, bytes] | None] = []
        if keys is not None:
            pos = 0
            step = 1 + len(keys)
            for _ in sks:
                exists = raw[pos]
                pos += 1
                vals = raw[pos : pos + len(keys)]
                pos += len(keys)
                if not exists:
                    results.append(None)
                else:
                    results.append(
                        {k: v for k, v in zip(keys, vals) if v is not None}
                    )
        else:
            for hgetall_result in raw:
                if not hgetall_result:
                    results.append(None)
                else:
                    results.append(hgetall_result)
        return results

    def get_column(
        self, key: bytes, indices: list[int] | None = None
    ) -> list[Any]:
        if indices is None:
            indices = list(range(len(self)))
        sks = self._resolve_indices(indices)
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

    def iter_rows(
        self, indices: list[int], keys: list[bytes] | None = None
    ) -> Iterator[dict[bytes, bytes] | None]:
        """Yield rows one at a time, backed by a pipelined get_many."""
        yield from self.get_many(indices, keys)

    def keys(self, index: int) -> list[bytes]:
        result = self._call_lua("keys", [index])
        return result

    # ------------------------------------------------------------------
    # ReadWriteBackend implementation
    # ------------------------------------------------------------------

    def set(self, index: int, value: dict[bytes, bytes] | None) -> None:
        if value is None:
            # Lua SET with no kv pairs just does DEL (→ None row)
            self._call_lua("set", [index])
        else:
            flat: list[Any] = [index]
            for k, v in value.items():
                flat.append(k)
                flat.append(v)
            self._call_lua("set", flat)

    def delete(self, index: int) -> None:
        self._call_lua("delete", [index])

    def extend(self, values: list[dict[bytes, bytes] | None]) -> int:
        if not values:
            return len(self)
        n = len(values)
        # Allocate N sort keys in one INCRBY
        end_sk = self._r.incrby(self._next_sk_key, n)
        start_sk = end_sk - n

        pipe = self._r.pipeline()
        sk_list: list[int] = []
        for i, v in enumerate(values):
            sk = start_sk + i
            sk_list.append(sk)
            if v is not None:
                pipe.hset(self._row_key(sk), mapping=v)
        # RPUSH all sort keys and capture the result (= new list length)
        sk_bytes = [str(sk).encode() for sk in sk_list]
        pipe.rpush(self._sk_list_key, *sk_bytes)
        results = pipe.execute()
        # Last result is the RPUSH return value = new length
        return results[-1]

    def insert(self, index: int, value: dict[bytes, bytes] | None) -> None:
        # Pipeline LLEN + INCR together
        pipe = self._r.pipeline()
        pipe.llen(self._sk_list_key)
        pipe.incr(self._next_sk_key)
        n, sk_raw = pipe.execute()
        sk = sk_raw - 1

        if index < 0:
            index = 0
        if index > n:
            index = n

        if value is not None:
            self._r.hset(self._row_key(sk), mapping=value)

        sk_bytes = str(sk).encode()

        if index == n:
            self._r.rpush(self._sk_list_key, sk_bytes)
        elif index == 0:
            self._r.lpush(self._sk_list_key, sk_bytes)
        else:
            pivot = self._r.lindex(self._sk_list_key, index)
            self._r.linsert(self._sk_list_key, "BEFORE", pivot, sk_bytes)

    def update(self, index: int, data: dict[bytes, bytes]) -> None:
        if not data:
            return
        flat: list[Any] = [index]
        for k, v in data.items():
            flat.append(k)
            flat.append(v)
        self._call_lua("update", flat)

    def drop_keys(
        self, keys: list[bytes], indices: list[int] | None = None
    ) -> None:
        if indices is None:
            indices = list(range(len(self)))
        sks = self._resolve_indices(indices)
        pipe = self._r.pipeline()
        for sk in sks:
            rk = self._row_key(sk)
            for k in keys:
                pipe.hdel(rk, k)
        pipe.execute()

    def clear(self) -> None:
        """Remove all row data and reset metadata."""
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
