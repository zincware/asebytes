# Redis Blob Backend Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Redis-backed blob-level storage with sync and async variants, accessible via `redis://` URIs through BlobIO, ObjectIO, and ASEIO facades.

**Architecture:** Two classes (`RedisBlobBackend`, `AsyncRedisBlobBackend`) implementing the blob-level ABCs (`ReadWriteBackend[bytes, bytes]`, `AsyncReadWriteBackend[bytes, bytes]`). Uses Redis hashes for row storage and a Redis LIST for positional indexing. Registry extended with `_BLOB_URI_REGISTRY` for URI-based blob backend lookup.

**Tech Stack:** `redis>=5.0` (both `redis.Redis` and `redis.asyncio.Redis`), pytest, anyio

**Design doc:** `docs/plans/2026-02-28-redis-backend-design.md`

---

### Task 1: Add redis dependency and install

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add optional dependency group**

In `pyproject.toml`, after the `mongodb` entry (line 59), add:

```toml
redis = [
    "redis>=5.0",
]
```

**Step 2: Add to dev dependencies**

In the `[dependency-groups]` `dev` list, add `"asebytes[redis]"` after `"asebytes[mongodb]"` (line 36).

**Step 3: Install**

Run: `uv sync --all-extras --dev`
Expected: Successful install, `redis` package available.

**Step 4: Verify**

Run: `uv run python -c "import redis; print(redis.__version__)"`
Expected: Version >= 5.0

**Step 5: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add redis>=5.0 optional dependency"
```

---

### Task 2: Create package skeleton and write failing tests for sync backend

**Files:**
- Create: `src/asebytes/redis/__init__.py`
- Create: `src/asebytes/redis/_backend.py`
- Create: `tests/test_redis.py`

**Step 1: Create empty package**

`src/asebytes/redis/__init__.py`:
```python
from ._backend import RedisBlobBackend

__all__ = ["RedisBlobBackend"]
```

`src/asebytes/redis/_backend.py`:
```python
"""Sync Redis blob backend — placeholder for TDD."""
```

**Step 2: Write failing tests**

`tests/test_redis.py` — this file will contain all Redis tests. Start with the sync backend:

```python
import os
import uuid

import pytest

redis_mod = pytest.importorskip("redis")

REDIS_URI = os.environ.get("REDIS_URI", "redis://localhost:6379")


def _redis_available():
    try:
        r = redis_mod.Redis.from_url(REDIS_URI, socket_connect_timeout=1)
        r.ping()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _redis_available(), reason=f"Redis not available at {REDIS_URI}"
)


@pytest.fixture
def backend():
    """Create a backend with a unique prefix, clean up after."""
    from asebytes.redis import RedisBlobBackend

    prefix = f"test_{uuid.uuid4().hex[:8]}"
    b = RedisBlobBackend(url=REDIS_URI, prefix=prefix)
    yield b
    b.remove()


# ── Core CRUD ────────────────────────────────────────────────────────────


class TestRedisBlobBackendCRUD:
    def test_empty_on_creation(self, backend):
        assert len(backend) == 0

    def test_extend_returns_length(self, backend):
        result = backend.extend([{b"x": b"1"}, {b"y": b"2"}])
        assert result == 2
        assert len(backend) == 2

    def test_extend_empty_returns_zero(self, backend):
        result = backend.extend([])
        assert result == 0

    def test_get_single_row(self, backend):
        backend.extend([{b"a": b"1", b"b": b"2"}])
        row = backend.get(0)
        assert row == {b"a": b"1", b"b": b"2"}

    def test_get_with_key_filter(self, backend):
        backend.extend([{b"a": b"1", b"b": b"2", b"c": b"3"}])
        row = backend.get(0, keys=[b"a", b"c"])
        assert row == {b"a": b"1", b"c": b"3"}

    def test_get_negative_index(self, backend):
        backend.extend([{b"x": b"1"}, {b"x": b"2"}])
        row = backend.get(-1)
        assert row == {b"x": b"2"}

    def test_get_out_of_bounds_raises(self, backend):
        with pytest.raises(IndexError):
            backend.get(0)

    def test_set_replaces_row(self, backend):
        backend.extend([{b"a": b"1"}])
        backend.set(0, {b"b": b"2"})
        assert backend.get(0) == {b"b": b"2"}

    def test_set_none_placeholder(self, backend):
        backend.extend([{b"a": b"1"}])
        backend.set(0, None)
        assert backend.get(0) is None

    def test_delete_shifts_indices(self, backend):
        backend.extend([{b"x": b"0"}, {b"x": b"1"}, {b"x": b"2"}])
        backend.delete(1)
        assert len(backend) == 2
        assert backend.get(0) == {b"x": b"0"}
        assert backend.get(1) == {b"x": b"2"}

    def test_insert_at_beginning(self, backend):
        backend.extend([{b"x": b"1"}, {b"x": b"2"}])
        backend.insert(0, {b"x": b"0"})
        assert len(backend) == 3
        assert backend.get(0) == {b"x": b"0"}
        assert backend.get(1) == {b"x": b"1"}

    def test_insert_at_end(self, backend):
        backend.extend([{b"x": b"1"}])
        backend.insert(1, {b"x": b"2"})
        assert len(backend) == 2
        assert backend.get(1) == {b"x": b"2"}

    def test_insert_none_placeholder(self, backend):
        backend.extend([{b"x": b"1"}])
        backend.insert(0, None)
        assert len(backend) == 2
        assert backend.get(0) is None
        assert backend.get(1) == {b"x": b"1"}

    def test_extend_with_none_placeholder(self, backend):
        backend.extend([{b"x": b"1"}, None, {b"x": b"3"}])
        assert len(backend) == 3
        assert backend.get(0) == {b"x": b"1"}
        assert backend.get(1) is None
        assert backend.get(2) == {b"x": b"3"}


# ── Batch & column operations ────────────────────────────────────────────


class TestRedisBlobBackendBatch:
    def test_get_many(self, backend):
        backend.extend([{b"x": b"0"}, {b"x": b"1"}, {b"x": b"2"}])
        rows = backend.get_many([0, 2])
        assert rows == [{b"x": b"0"}, {b"x": b"2"}]

    def test_get_column(self, backend):
        backend.extend([{b"x": b"1"}, {b"x": b"2"}, {b"x": b"3"}])
        col = backend.get_column(b"x", [0, 1, 2])
        assert col == [b"1", b"2", b"3"]

    def test_get_column_with_none_rows(self, backend):
        backend.extend([{b"x": b"1"}, None, {b"x": b"3"}])
        col = backend.get_column(b"x", [0, 1, 2])
        assert col == [b"1", None, b"3"]

    def test_keys_returns_field_names(self, backend):
        backend.extend([{b"a": b"1", b"b": b"2"}])
        k = backend.keys(0)
        assert set(k) == {b"a", b"b"}

    def test_update_partial(self, backend):
        backend.extend([{b"a": b"1", b"b": b"2"}])
        backend.update(0, {b"b": b"99", b"c": b"3"})
        row = backend.get(0)
        assert row == {b"a": b"1", b"b": b"99", b"c": b"3"}

    def test_drop_keys(self, backend):
        backend.extend([{b"a": b"1", b"b": b"2"}, {b"a": b"3", b"b": b"4"}])
        backend.drop_keys([b"b"])
        assert backend.get(0) == {b"a": b"1"}
        assert backend.get(1) == {b"a": b"3"}


# ── Lifecycle ────────────────────────────────────────────────────────────


class TestRedisBlobBackendLifecycle:
    def test_clear(self, backend):
        backend.extend([{b"x": b"1"}, {b"x": b"2"}])
        backend.clear()
        assert len(backend) == 0

    def test_clear_then_extend(self, backend):
        backend.extend([{b"x": b"1"}])
        backend.clear()
        result = backend.extend([{b"y": b"2"}])
        assert result == 1
        assert backend.get(0) == {b"y": b"2"}

    def test_remove(self):
        """remove() cleans up all keys with the prefix."""
        from asebytes.redis import RedisBlobBackend

        prefix = f"test_{uuid.uuid4().hex[:8]}"
        b = RedisBlobBackend(url=REDIS_URI, prefix=prefix)
        b.extend([{b"x": b"1"}])
        b.remove()
        # After remove, creating a new backend with same prefix should be empty
        b2 = RedisBlobBackend(url=REDIS_URI, prefix=prefix)
        assert len(b2) == 0


# ── from_uri ─────────────────────────────────────────────────────────────


class TestRedisBlobFromURI:
    def test_from_uri_basic(self):
        from asebytes.redis import RedisBlobBackend

        prefix = f"test_{uuid.uuid4().hex[:8]}"
        uri = f"{REDIS_URI}/0/{prefix}"
        b = RedisBlobBackend.from_uri(uri)
        try:
            b.extend([{b"x": b"1"}])
            assert len(b) == 1
        finally:
            b.remove()

    def test_from_uri_default_prefix(self):
        from asebytes.redis import RedisBlobBackend

        b = RedisBlobBackend.from_uri(REDIS_URI)
        assert b._prefix == "default"

    def test_from_uri_with_db_and_prefix(self):
        from asebytes.redis import RedisBlobBackend

        b = RedisBlobBackend.from_uri(f"{REDIS_URI}/0/myprefix")
        assert b._prefix == "myprefix"
```

**Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_redis.py -v --no-header 2>&1 | head -30`
Expected: FAIL (ImportError or AttributeError since RedisBlobBackend doesn't exist yet)

**Step 4: Commit RED tests**

```bash
git add src/asebytes/redis/ tests/test_redis.py
git commit -m "test: add failing tests for sync Redis blob backend (RED)"
```

---

### Task 3: Implement sync RedisBlobBackend (GREEN)

**Files:**
- Modify: `src/asebytes/redis/_backend.py`

**Step 1: Implement the full sync backend**

`src/asebytes/redis/_backend.py`:
```python
"""Sync Redis blob backend using redis.Redis."""

from __future__ import annotations

from typing import Any

import redis as redis_mod

from .._backends import ReadWriteBackend


class RedisBlobBackend(ReadWriteBackend[bytes, bytes]):
    """Redis-backed read-write backend for blob dictionaries.

    Uses Redis hashes for row storage and a Redis LIST for positional
    indexing via sort keys.

    Parameters
    ----------
    url : str
        Redis connection URL.
    prefix : str
        Key prefix for namespacing within a database.
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379",
        prefix: str = "default",
    ):
        self._r = redis_mod.Redis.from_url(url, decode_responses=False)
        self._prefix = prefix

    @classmethod
    def from_uri(cls, uri: str, **kwargs) -> RedisBlobBackend:
        """Construct from ``redis://host:port/db/prefix``."""
        if "://" not in uri:
            raise ValueError(f"Invalid URI: {uri!r}")
        scheme, after_scheme = uri.split("://", 1)
        # Split host[:port] from path
        if "/" in after_scheme:
            host_part, path_part = after_scheme.split("/", 1)
        else:
            host_part, path_part = after_scheme, ""

        parts = [p for p in path_part.split("/") if p]
        if len(parts) >= 2:
            # /db/prefix
            db = parts[0]
            prefix = parts[1]
            url = f"{scheme}://{host_part}/{db}"
        elif len(parts) == 1:
            # Could be just /db or /prefix — treat as /db
            db = parts[0]
            prefix = "default"
            url = f"{scheme}://{host_part}/{db}"
        else:
            prefix = "default"
            url = uri

        return cls(url=url, prefix=prefix, **kwargs)

    # -- Key helpers --------------------------------------------------------

    def _sk_list_key(self) -> str:
        return f"{self._prefix}:sort_keys"

    def _next_sk_key(self) -> str:
        return f"{self._prefix}:next_sk"

    def _row_key(self, sort_key: int) -> str:
        return f"{self._prefix}:row:{sort_key}"

    def _resolve_sort_key(self, index: int) -> int:
        n = self._r.llen(self._sk_list_key())
        if index < 0:
            index += n
        if index < 0 or index >= n:
            raise IndexError(index)
        raw = self._r.lindex(self._sk_list_key(), index)
        return int(raw)

    def _get_next_sk(self) -> int:
        raw = self._r.get(self._next_sk_key())
        return int(raw) if raw is not None else 0

    # -- ReadBackend implementation -----------------------------------------

    def __len__(self) -> int:
        return self._r.llen(self._sk_list_key())

    def get(
        self, index: int, keys: list[bytes] | None = None
    ) -> dict[bytes, bytes] | None:
        sk = self._resolve_sort_key(index)
        rk = self._row_key(sk)
        if keys is None:
            data = self._r.hgetall(rk)
            return data if data else None
        else:
            vals = self._r.hmget(rk, *keys)
            if all(v is None for v in vals):
                # Check if row exists at all
                if not self._r.exists(rk):
                    return None
            return {k: v for k, v in zip(keys, vals) if v is not None}

    def get_many(
        self, indices: list[int], keys: list[bytes] | None = None
    ) -> list[dict[bytes, bytes] | None]:
        if not indices:
            return []
        pipe = self._r.pipeline(transaction=False)
        sk_list_key = self._sk_list_key()
        for i in indices:
            pipe.lindex(sk_list_key, i)
        raw_sks = pipe.execute()

        # Validate indices and resolve sort keys
        n = self._r.llen(sk_list_key)
        sks = []
        for i, raw in zip(indices, raw_sks):
            idx = i if i >= 0 else i + n
            if raw is None or idx < 0 or idx >= n:
                raise IndexError(i)
            sks.append(int(raw))

        pipe = self._r.pipeline(transaction=False)
        for sk in sks:
            if keys is None:
                pipe.hgetall(self._row_key(sk))
            else:
                pipe.hmget(self._row_key(sk), *keys)
        results_raw = pipe.execute()

        results = []
        for sk, raw in zip(sks, results_raw):
            if keys is None:
                results.append(raw if raw else None)
            else:
                if all(v is None for v in raw):
                    if not self._r.exists(self._row_key(sk)):
                        results.append(None)
                    else:
                        results.append({})
                else:
                    results.append(
                        {k: v for k, v in zip(keys, raw) if v is not None}
                    )
        return results

    def get_column(
        self, key: bytes, indices: list[int] | None = None
    ) -> list[Any]:
        n = len(self)
        if indices is None:
            indices = list(range(n))
        if not indices:
            return []

        pipe = self._r.pipeline(transaction=False)
        sk_list_key = self._sk_list_key()
        for i in indices:
            pipe.lindex(sk_list_key, i)
        raw_sks = pipe.execute()

        sks = []
        for i, raw in zip(indices, raw_sks):
            idx = i if i >= 0 else i + n
            if raw is None or idx < 0 or idx >= n:
                raise IndexError(i)
            sks.append(int(raw))

        pipe = self._r.pipeline(transaction=False)
        for sk in sks:
            pipe.hget(self._row_key(sk), key)
        vals = pipe.execute()
        return vals  # None for missing keys/rows

    def keys(self, index: int) -> list[bytes]:
        sk = self._resolve_sort_key(index)
        return self._r.hkeys(self._row_key(sk))

    # -- ReadWriteBackend implementation ------------------------------------

    def set(self, index: int, value: dict[bytes, bytes] | None) -> None:
        sk = self._resolve_sort_key(index)
        rk = self._row_key(sk)
        self._r.delete(rk)
        if value is not None:
            self._r.hset(rk, mapping=value)

    def delete(self, index: int) -> None:
        sk = self._resolve_sort_key(index)
        rk = self._row_key(sk)
        self._r.delete(rk)
        # Rebuild sort_keys list without this entry
        sk_key = self._sk_list_key()
        all_sks = self._r.lrange(sk_key, 0, -1)
        n = len(all_sks)
        pos = index if index >= 0 else index + n
        all_sks.pop(pos)
        pipe = self._r.pipeline()
        pipe.delete(sk_key)
        if all_sks:
            pipe.rpush(sk_key, *all_sks)
        pipe.execute()

    def extend(self, values: list[dict[bytes, bytes] | None]) -> int:
        if not values:
            return len(self)
        next_sk = self._get_next_sk()
        new_sks = list(range(next_sk, next_sk + len(values)))

        pipe = self._r.pipeline(transaction=False)
        for sk, val in zip(new_sks, values):
            if val is not None:
                pipe.hset(self._row_key(sk), mapping=val)
        # Push sort keys to list
        sk_key = self._sk_list_key()
        encoded_sks = [str(sk).encode() for sk in new_sks]
        pipe.rpush(sk_key, *encoded_sks)
        pipe.set(self._next_sk_key(), str(next_sk + len(values)).encode())
        pipe.execute()
        return self._r.llen(sk_key)

    def insert(self, index: int, value: dict[bytes, bytes] | None) -> None:
        sk_key = self._sk_list_key()
        n = self._r.llen(sk_key)
        if index < 0:
            index = 0
        if index > n:
            index = n

        next_sk = self._get_next_sk()
        rk = self._row_key(next_sk)
        if value is not None:
            self._r.hset(rk, mapping=value)

        # Rebuild sort_keys list with new entry inserted
        all_sks = self._r.lrange(sk_key, 0, -1)
        all_sks.insert(index, str(next_sk).encode())
        pipe = self._r.pipeline()
        pipe.delete(sk_key)
        pipe.rpush(sk_key, *all_sks)
        pipe.set(self._next_sk_key(), str(next_sk + 1).encode())
        pipe.execute()

    def update(self, index: int, data: dict[bytes, bytes]) -> None:
        if not data:
            return
        sk = self._resolve_sort_key(index)
        self._r.hset(self._row_key(sk), mapping=data)

    def drop_keys(
        self, keys: list[bytes], indices: list[int] | None = None
    ) -> None:
        if indices is None:
            # All rows: scan for row keys
            cursor = 0
            pattern = f"{self._prefix}:row:*"
            while True:
                cursor, found_keys = self._r.scan(cursor, match=pattern)
                if found_keys:
                    pipe = self._r.pipeline(transaction=False)
                    for rk in found_keys:
                        pipe.hdel(rk, *keys)
                    pipe.execute()
                if cursor == 0:
                    break
        else:
            n = len(self)
            pipe = self._r.pipeline(transaction=False)
            for i in indices:
                idx = i if i >= 0 else i + n
                raw = self._r.lindex(self._sk_list_key(), idx)
                if raw is None:
                    raise IndexError(i)
                pipe.hdel(self._row_key(int(raw)), *keys)
            pipe.execute()

    def clear(self) -> None:
        # Delete all row hashes
        cursor = 0
        pattern = f"{self._prefix}:row:*"
        while True:
            cursor, found_keys = self._r.scan(cursor, match=pattern)
            if found_keys:
                self._r.delete(*found_keys)
            if cursor == 0:
                break
        # Reset metadata
        self._r.delete(self._sk_list_key())
        self._r.set(self._next_sk_key(), b"0")

    def remove(self) -> None:
        """Remove all keys with this prefix."""
        cursor = 0
        pattern = f"{self._prefix}:*"
        while True:
            cursor, found_keys = self._r.scan(cursor, match=pattern)
            if found_keys:
                self._r.delete(*found_keys)
            if cursor == 0:
                break
```

**Step 2: Run tests**

Run: `uv run pytest tests/test_redis.py -v --no-header 2>&1 | tail -20`
Expected: All tests PASS

**Step 3: Commit GREEN**

```bash
git add src/asebytes/redis/_backend.py
git commit -m "feat: implement sync RedisBlobBackend (GREEN)"
```

---

### Task 4: Write failing tests for async backend, then implement (RED + GREEN)

**Files:**
- Modify: `tests/test_redis.py`
- Create: `src/asebytes/redis/_async_backend.py`
- Modify: `src/asebytes/redis/__init__.py`

**Step 1: Add async tests to `tests/test_redis.py`**

Append to the end of `tests/test_redis.py`:

```python
# ── Async backend tests ──────────────────────────────────────────────────


@pytest.fixture
async def async_backend():
    from asebytes.redis import AsyncRedisBlobBackend

    prefix = f"test_{uuid.uuid4().hex[:8]}"
    b = AsyncRedisBlobBackend(url=REDIS_URI, prefix=prefix)
    yield b
    await b.remove()


@pytest.mark.anyio
class TestAsyncRedisBlobBackend:
    async def test_empty_on_creation(self, async_backend):
        assert await async_backend.len() == 0

    async def test_extend_and_get(self, async_backend):
        result = await async_backend.extend([{b"x": b"1"}, {b"y": b"2"}])
        assert result == 2
        row = await async_backend.get(0)
        assert row == {b"x": b"1"}

    async def test_extend_empty(self, async_backend):
        result = await async_backend.extend([])
        assert result == 0

    async def test_get_with_key_filter(self, async_backend):
        await async_backend.extend([{b"a": b"1", b"b": b"2", b"c": b"3"}])
        row = await async_backend.get(0, keys=[b"a", b"c"])
        assert row == {b"a": b"1", b"c": b"3"}

    async def test_set_replaces_row(self, async_backend):
        await async_backend.extend([{b"a": b"1"}])
        await async_backend.set(0, {b"b": b"2"})
        assert await async_backend.get(0) == {b"b": b"2"}

    async def test_delete_shifts_indices(self, async_backend):
        await async_backend.extend([{b"x": b"0"}, {b"x": b"1"}, {b"x": b"2"}])
        await async_backend.delete(1)
        assert await async_backend.len() == 2
        assert await async_backend.get(1) == {b"x": b"2"}

    async def test_insert_at_beginning(self, async_backend):
        await async_backend.extend([{b"x": b"1"}])
        await async_backend.insert(0, {b"x": b"0"})
        assert await async_backend.len() == 2
        assert await async_backend.get(0) == {b"x": b"0"}
        assert await async_backend.get(1) == {b"x": b"1"}

    async def test_get_many(self, async_backend):
        await async_backend.extend([{b"x": b"0"}, {b"x": b"1"}, {b"x": b"2"}])
        rows = await async_backend.get_many([0, 2])
        assert rows == [{b"x": b"0"}, {b"x": b"2"}]

    async def test_get_column(self, async_backend):
        await async_backend.extend([{b"x": b"1"}, {b"x": b"2"}])
        col = await async_backend.get_column(b"x", [0, 1])
        assert col == [b"1", b"2"]

    async def test_update_partial(self, async_backend):
        await async_backend.extend([{b"a": b"1", b"b": b"2"}])
        await async_backend.update(0, {b"b": b"99"})
        assert await async_backend.get(0) == {b"a": b"1", b"b": b"99"}

    async def test_clear(self, async_backend):
        await async_backend.extend([{b"x": b"1"}])
        await async_backend.clear()
        assert await async_backend.len() == 0

    async def test_remove(self):
        from asebytes.redis import AsyncRedisBlobBackend

        prefix = f"test_{uuid.uuid4().hex[:8]}"
        b = AsyncRedisBlobBackend(url=REDIS_URI, prefix=prefix)
        await b.extend([{b"x": b"1"}])
        await b.remove()
        b2 = AsyncRedisBlobBackend(url=REDIS_URI, prefix=prefix)
        assert await b2.len() == 0

    async def test_from_uri(self):
        from asebytes.redis import AsyncRedisBlobBackend

        prefix = f"test_{uuid.uuid4().hex[:8]}"
        uri = f"{REDIS_URI}/0/{prefix}"
        b = AsyncRedisBlobBackend.from_uri(uri)
        try:
            await b.extend([{b"x": b"1"}])
            assert await b.len() == 1
        finally:
            await b.remove()
```

**Step 2: Run tests to verify async tests fail**

Run: `uv run pytest tests/test_redis.py::TestAsyncRedisBlobBackend -v --no-header 2>&1 | head -10`
Expected: FAIL (ImportError — `AsyncRedisBlobBackend` doesn't exist)

**Step 3: Implement async backend**

`src/asebytes/redis/_async_backend.py`:
```python
"""Async Redis blob backend using redis.asyncio."""

from __future__ import annotations

from typing import Any

import redis.asyncio as aioredis

from .._async_backends import AsyncReadWriteBackend


class AsyncRedisBlobBackend(AsyncReadWriteBackend[bytes, bytes]):
    """Async Redis-backed read-write backend for blob dictionaries.

    Uses ``redis.asyncio.Redis`` for native non-blocking I/O.
    Same key layout as :class:`RedisBlobBackend`.

    Parameters
    ----------
    url : str
        Redis connection URL.
    prefix : str
        Key prefix for namespacing within a database.
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379",
        prefix: str = "default",
    ):
        self._r = aioredis.from_url(url, decode_responses=False)
        self._prefix = prefix

    @classmethod
    def from_uri(cls, uri: str, **kwargs) -> AsyncRedisBlobBackend:
        """Construct from ``redis://host:port/db/prefix``."""
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
            url = f"{scheme}://{host_part}/{db}"
        elif len(parts) == 1:
            db = parts[0]
            prefix = "default"
            url = f"{scheme}://{host_part}/{db}"
        else:
            prefix = "default"
            url = uri

        return cls(url=url, prefix=prefix, **kwargs)

    # -- Key helpers --------------------------------------------------------

    def _sk_list_key(self) -> str:
        return f"{self._prefix}:sort_keys"

    def _next_sk_key(self) -> str:
        return f"{self._prefix}:next_sk"

    def _row_key(self, sort_key: int) -> str:
        return f"{self._prefix}:row:{sort_key}"

    async def _resolve_sort_key(self, index: int) -> int:
        n = await self._r.llen(self._sk_list_key())
        if index < 0:
            index += n
        if index < 0 or index >= n:
            raise IndexError(index)
        raw = await self._r.lindex(self._sk_list_key(), index)
        return int(raw)

    async def _get_next_sk(self) -> int:
        raw = await self._r.get(self._next_sk_key())
        return int(raw) if raw is not None else 0

    # -- AsyncReadBackend implementation ------------------------------------

    async def len(self) -> int:
        return await self._r.llen(self._sk_list_key())

    async def get(
        self, index: int, keys: list[bytes] | None = None
    ) -> dict[bytes, bytes] | None:
        sk = await self._resolve_sort_key(index)
        rk = self._row_key(sk)
        if keys is None:
            data = await self._r.hgetall(rk)
            return data if data else None
        else:
            vals = await self._r.hmget(rk, *keys)
            if all(v is None for v in vals):
                if not await self._r.exists(rk):
                    return None
            return {k: v for k, v in zip(keys, vals) if v is not None}

    async def get_many(
        self, indices: list[int], keys: list[bytes] | None = None
    ) -> list[dict[bytes, bytes] | None]:
        if not indices:
            return []
        pipe = self._r.pipeline(transaction=False)
        sk_list_key = self._sk_list_key()
        for i in indices:
            pipe.lindex(sk_list_key, i)
        raw_sks = await pipe.execute()

        n = await self._r.llen(sk_list_key)
        sks = []
        for i, raw in zip(indices, raw_sks):
            idx = i if i >= 0 else i + n
            if raw is None or idx < 0 or idx >= n:
                raise IndexError(i)
            sks.append(int(raw))

        pipe = self._r.pipeline(transaction=False)
        for sk in sks:
            if keys is None:
                pipe.hgetall(self._row_key(sk))
            else:
                pipe.hmget(self._row_key(sk), *keys)
        results_raw = await pipe.execute()

        results = []
        for sk, raw in zip(sks, results_raw):
            if keys is None:
                results.append(raw if raw else None)
            else:
                if all(v is None for v in raw):
                    if not await self._r.exists(self._row_key(sk)):
                        results.append(None)
                    else:
                        results.append({})
                else:
                    results.append(
                        {k: v for k, v in zip(keys, raw) if v is not None}
                    )
        return results

    async def get_column(
        self, key: bytes, indices: list[int] | None = None
    ) -> list[Any]:
        n = await self.len()
        if indices is None:
            indices = list(range(n))
        if not indices:
            return []

        pipe = self._r.pipeline(transaction=False)
        sk_list_key = self._sk_list_key()
        for i in indices:
            pipe.lindex(sk_list_key, i)
        raw_sks = await pipe.execute()

        sks = []
        for i, raw in zip(indices, raw_sks):
            idx = i if i >= 0 else i + n
            if raw is None or idx < 0 or idx >= n:
                raise IndexError(i)
            sks.append(int(raw))

        pipe = self._r.pipeline(transaction=False)
        for sk in sks:
            pipe.hget(self._row_key(sk), key)
        vals = await pipe.execute()
        return vals

    async def keys(self, index: int) -> list[bytes]:
        sk = await self._resolve_sort_key(index)
        return await self._r.hkeys(self._row_key(sk))

    # -- AsyncReadWriteBackend implementation --------------------------------

    async def set(self, index: int, value: dict[bytes, bytes] | None) -> None:
        sk = await self._resolve_sort_key(index)
        rk = self._row_key(sk)
        await self._r.delete(rk)
        if value is not None:
            await self._r.hset(rk, mapping=value)

    async def delete(self, index: int) -> None:
        sk = await self._resolve_sort_key(index)
        rk = self._row_key(sk)
        await self._r.delete(rk)
        sk_key = self._sk_list_key()
        all_sks = await self._r.lrange(sk_key, 0, -1)
        n = len(all_sks)
        pos = index if index >= 0 else index + n
        all_sks.pop(pos)
        pipe = self._r.pipeline()
        pipe.delete(sk_key)
        if all_sks:
            pipe.rpush(sk_key, *all_sks)
        await pipe.execute()

    async def extend(self, values: list[dict[bytes, bytes] | None]) -> int:
        if not values:
            return await self.len()
        next_sk = await self._get_next_sk()
        new_sks = list(range(next_sk, next_sk + len(values)))

        pipe = self._r.pipeline(transaction=False)
        for sk, val in zip(new_sks, values):
            if val is not None:
                pipe.hset(self._row_key(sk), mapping=val)
        sk_key = self._sk_list_key()
        encoded_sks = [str(sk).encode() for sk in new_sks]
        pipe.rpush(sk_key, *encoded_sks)
        pipe.set(self._next_sk_key(), str(next_sk + len(values)).encode())
        await pipe.execute()
        return await self._r.llen(sk_key)

    async def insert(
        self, index: int, value: dict[bytes, bytes] | None
    ) -> None:
        sk_key = self._sk_list_key()
        n = await self._r.llen(sk_key)
        if index < 0:
            index = 0
        if index > n:
            index = n

        next_sk = await self._get_next_sk()
        if value is not None:
            await self._r.hset(self._row_key(next_sk), mapping=value)

        all_sks = await self._r.lrange(sk_key, 0, -1)
        all_sks.insert(index, str(next_sk).encode())
        pipe = self._r.pipeline()
        pipe.delete(sk_key)
        pipe.rpush(sk_key, *all_sks)
        pipe.set(self._next_sk_key(), str(next_sk + 1).encode())
        await pipe.execute()

    async def update(self, index: int, data: dict[bytes, bytes]) -> None:
        if not data:
            return
        sk = await self._resolve_sort_key(index)
        await self._r.hset(self._row_key(sk), mapping=data)

    async def drop_keys(
        self, keys: list[bytes], indices: list[int] | None = None
    ) -> None:
        if indices is None:
            cursor = 0
            pattern = f"{self._prefix}:row:*"
            while True:
                cursor, found_keys = await self._r.scan(cursor, match=pattern)
                if found_keys:
                    pipe = self._r.pipeline(transaction=False)
                    for rk in found_keys:
                        pipe.hdel(rk, *keys)
                    await pipe.execute()
                if cursor == 0:
                    break
        else:
            n = await self.len()
            pipe = self._r.pipeline(transaction=False)
            for i in indices:
                idx = i if i >= 0 else i + n
                raw = await self._r.lindex(self._sk_list_key(), idx)
                if raw is None:
                    raise IndexError(i)
                pipe.hdel(self._row_key(int(raw)), *keys)
            await pipe.execute()

    async def clear(self) -> None:
        cursor = 0
        pattern = f"{self._prefix}:row:*"
        while True:
            cursor, found_keys = await self._r.scan(cursor, match=pattern)
            if found_keys:
                await self._r.delete(*found_keys)
            if cursor == 0:
                break
        await self._r.delete(self._sk_list_key())
        await self._r.set(self._next_sk_key(), b"0")

    async def remove(self) -> None:
        cursor = 0
        pattern = f"{self._prefix}:*"
        while True:
            cursor, found_keys = await self._r.scan(cursor, match=pattern)
            if found_keys:
                await self._r.delete(*found_keys)
            if cursor == 0:
                break
```

**Step 4: Update `__init__.py`**

`src/asebytes/redis/__init__.py`:
```python
from ._backend import RedisBlobBackend
from ._async_backend import AsyncRedisBlobBackend

__all__ = ["RedisBlobBackend", "AsyncRedisBlobBackend"]
```

**Step 5: Run all Redis tests**

Run: `uv run pytest tests/test_redis.py -v --no-header 2>&1 | tail -25`
Expected: All tests PASS (both sync and async)

**Step 6: Commit**

```bash
git add src/asebytes/redis/ tests/test_redis.py
git commit -m "feat: implement async RedisBlobBackend (GREEN)"
```

---

### Task 5: Registry changes — blob URI registries and parse_uri

**Files:**
- Modify: `src/asebytes/_registry.py`
- Create: `tests/test_redis_registry.py`

**Step 1: Write failing tests for registry integration**

`tests/test_redis_registry.py`:
```python
"""Tests for Redis URI registry integration."""

import os
import uuid

import pytest

redis_mod = pytest.importorskip("redis")

REDIS_URI = os.environ.get("REDIS_URI", "redis://localhost:6379")


def _redis_available():
    try:
        r = redis_mod.Redis.from_url(REDIS_URI, socket_connect_timeout=1)
        r.ping()
        return True
    except Exception:
        return False


_skip_no_redis = pytest.mark.skipif(
    not _redis_available(), reason=f"Redis not available at {REDIS_URI}"
)


def test_parse_uri_recognizes_redis():
    from asebytes._registry import parse_uri

    scheme, remainder = parse_uri("redis://localhost:6379/0/myprefix")
    assert scheme == "redis"


def test_get_blob_backend_cls_returns_redis():
    from asebytes._registry import get_blob_backend_cls
    from asebytes.redis import RedisBlobBackend

    cls = get_blob_backend_cls("redis://localhost:6379")
    assert cls is RedisBlobBackend


def test_get_backend_cls_returns_adapter_for_redis():
    """ObjectIO('redis://...') should get a BlobToObject adapter."""
    from asebytes._registry import get_backend_cls

    cls = get_backend_cls("redis://localhost:6379")
    # Should be a callable that produces an adapter, not raise KeyError
    assert callable(cls)


@_skip_no_redis
def test_blobio_redis_uri():
    from asebytes import BlobIO

    prefix = f"test_{uuid.uuid4().hex[:8]}"
    uri = f"{REDIS_URI}/0/{prefix}"
    db = BlobIO(uri)
    try:
        db.extend([{b"x": b"1"}, {b"y": b"2"}])
        assert len(db) == 2
        assert db[0] == {b"x": b"1"}
    finally:
        db.remove()


@_skip_no_redis
def test_objectio_redis_uri():
    from asebytes import ObjectIO

    prefix = f"test_{uuid.uuid4().hex[:8]}"
    uri = f"{REDIS_URI}/0/{prefix}"
    db = ObjectIO(uri)
    try:
        db.extend([{"x": 1, "y": 2.5}])
        assert len(db) == 1
        row = db[0]
        assert row["x"] == 1
        assert row["y"] == 2.5
    finally:
        db.remove()


@_skip_no_redis
@pytest.mark.anyio
async def test_async_blobio_redis_uri():
    from asebytes import AsyncBlobIO

    prefix = f"test_{uuid.uuid4().hex[:8]}"
    uri = f"{REDIS_URI}/0/{prefix}"
    db = AsyncBlobIO(uri)
    try:
        await db.extend([{b"x": b"1"}])
        assert await db.len() == 1
    finally:
        await db.remove()


@_skip_no_redis
@pytest.mark.anyio
async def test_async_objectio_redis_uri():
    from asebytes import AsyncObjectIO

    prefix = f"test_{uuid.uuid4().hex[:8]}"
    uri = f"{REDIS_URI}/0/{prefix}"
    db = AsyncObjectIO(uri)
    try:
        await db.extend([{"x": 1}])
        assert await db.len() == 1
    finally:
        await db.remove()
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_redis_registry.py -v --no-header 2>&1 | head -15`
Expected: FAIL (`parse_uri` doesn't recognize `redis`)

**Step 3: Modify `_registry.py`**

Add `_BLOB_URI_REGISTRY` and `_ASYNC_BLOB_URI_REGISTRY` after `_ASYNC_URI_REGISTRY` (after line 55):

```python
# Blob-level URI scheme -> (module_path, writable_cls_name | None, readonly_cls_name)
# Used by get_blob_backend_cls() for blob-level URI backends.
_BLOB_URI_REGISTRY: dict[str, tuple[str, str | None, str]] = {
    "redis": ("asebytes.redis._backend", "RedisBlobBackend", "RedisBlobBackend"),
}

# Async blob-level URI scheme -> native async blob backend.
_ASYNC_BLOB_URI_REGISTRY: dict[str, tuple[str, str | None, str]] = {
    "redis": (
        "asebytes.redis._async_backend",
        "AsyncRedisBlobBackend",
        "AsyncRedisBlobBackend",
    ),
}
```

Add to `_EXTRAS_HINT`:
```python
    "asebytes.redis._backend": "redis",
    "asebytes.redis._async_backend": "redis",
```

Update `parse_uri()` to also check blob URI registries (line 77):

Change:
```python
    if scheme in _URI_REGISTRY or scheme in _ASYNC_URI_REGISTRY:
```
To:
```python
    if (
        scheme in _URI_REGISTRY
        or scheme in _ASYNC_URI_REGISTRY
        or scheme in _BLOB_URI_REGISTRY
        or scheme in _ASYNC_BLOB_URI_REGISTRY
    ):
```

Update `get_blob_backend_cls()` to check `_BLOB_URI_REGISTRY` before the object-adapter fallback. Insert this block at the top of the function, before the glob loop (before line 213):

```python
    # --- Blob-level URI lookup ---
    scheme, _remainder = parse_uri(path)
    if scheme is not None and scheme in _BLOB_URI_REGISTRY:
        module_path, writable, read_only = _BLOB_URI_REGISTRY[scheme]
        try:
            mod = importlib.import_module(module_path)
        except ImportError:
            hint = _EXTRAS_HINT.get(module_path, module_path)
            raise ImportError(
                f"Backend '{module_path}' requires additional dependencies. "
                f"Install them with: pip install asebytes[{hint}]"
            ) from None
        if readonly is True:
            return getattr(mod, read_only)
        if readonly is False:
            if writable is None:
                raise TypeError(
                    f"Backend for '{path}' is read-only, "
                    "no writable variant available"
                )
            return getattr(mod, writable)
        if writable is not None:
            return getattr(mod, writable)
        return getattr(mod, read_only)
```

Update `get_backend_cls()` to fall back to blob-level URI with BlobToObject adapter. Add before the `raise KeyError` at line 161:

```python
    # --- Fallback: wrap blob URI backend with BlobToObjectAdapter ---
    if scheme is not None and scheme in _BLOB_URI_REGISTRY:
        from ._adapters import BlobToObjectReadAdapter, BlobToObjectReadWriteAdapter
        blob_cls = get_blob_backend_cls(path, readonly=readonly)

        if readonly is True:
            def _make_read_adapter(*args, **kwargs):
                return BlobToObjectReadAdapter(blob_cls.from_uri(*args, **kwargs))
            return _make_read_adapter

        def _make_readwrite_adapter(*args, **kwargs):
            return BlobToObjectReadWriteAdapter(blob_cls.from_uri(*args, **kwargs))
        return _make_readwrite_adapter
```

Update `get_async_backend_cls()` to check `_ASYNC_BLOB_URI_REGISTRY`. Add after the `_ASYNC_URI_REGISTRY` check but before the fallback to sync (before line 196):

```python
    # Check async blob URI registry
    if scheme is not None and scheme in _ASYNC_BLOB_URI_REGISTRY:
        module_path, writable, read_only = _ASYNC_BLOB_URI_REGISTRY[scheme]
        try:
            mod = importlib.import_module(module_path)
        except ImportError:
            hint = _EXTRAS_HINT.get(module_path, module_path)
            raise ImportError(
                f"Backend '{module_path}' requires additional dependencies. "
                f"Install them with: pip install asebytes[{hint}]"
            ) from None
        if readonly is True:
            return getattr(mod, read_only)
        if readonly is False:
            if writable is None:
                raise TypeError(
                    f"Backend for '{path}' is read-only, "
                    "no writable variant available"
                )
            return getattr(mod, writable)
        if writable is not None:
            return getattr(mod, writable)
        return getattr(mod, read_only)
```

**Step 4: Run all registry tests**

Run: `uv run pytest tests/test_redis_registry.py -v --no-header`
Expected: All PASS

**Step 5: Run full test suite**

Run: `uv run pytest --no-header 2>&1 | tail -5`
Expected: No regressions

**Step 6: Commit**

```bash
git add src/asebytes/_registry.py tests/test_redis_registry.py
git commit -m "feat: add blob URI registries for redis:// scheme"
```

---

### Task 6: Top-level exports and extras hint

**Files:**
- Modify: `src/asebytes/__init__.py`

**Step 1: Add optional import block**

After the MongoDB block (after line 167), add:

```python
try:
    from .redis import RedisBlobBackend, AsyncRedisBlobBackend
except ImportError:
    pass
else:
    __all__ += ["RedisBlobBackend", "AsyncRedisBlobBackend"]
```

Add to `_OPTIONAL_ATTRS` dict:
```python
    "RedisBlobBackend": "redis",
    "AsyncRedisBlobBackend": "redis",
```

**Step 2: Verify imports**

Run: `uv run python -c "from asebytes import RedisBlobBackend, AsyncRedisBlobBackend; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add src/asebytes/__init__.py
git commit -m "feat: export Redis backends from top-level package"
```

---

### Task 7: CI — add Redis service to GitHub Actions

**Files:**
- Modify: `.github/workflows/tests.yml`

**Step 1: Add Redis service container**

The current workflow has no `services` section. Add a `services` block under the `test` job, after the `fail-fast: false` line (after line 15):

```yaml
    services:
      redis:
        image: redis:7
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
```

**Step 2: Commit**

```bash
git add .github/workflows/tests.yml
git commit -m "ci: add Redis service for integration tests"
```

---

### Task 8: Run full test suite and verify

**Step 1: Run all tests**

Run: `uv run pytest --no-header 2>&1 | tail -10`
Expected: All tests pass, including new Redis tests

**Step 2: Run Redis tests specifically**

Run: `uv run pytest tests/test_redis.py tests/test_redis_registry.py -v --no-header`
Expected: All PASS

**Step 3: Quick smoke test — ASEIO through Redis**

Run:
```bash
uv run python -c "
import ase
from asebytes import ASEIO
db = ASEIO('redis://localhost:6379/0/smoke_test')
atoms = ase.Atoms('H2', positions=[[0,0,0],[0,0,0.74]])
db.extend([atoms])
print(f'len={len(db)}, formula={db[0].get_chemical_formula()}')
db.remove()
print('ASEIO redis:// roundtrip OK')
"
```
Expected: `len=1, formula=H2` then `ASEIO redis:// roundtrip OK`

---

Plan complete and saved to `docs/plans/2026-02-28-redis-backend-impl.md`. Two execution options:

**1. Subagent-Driven (this session)** — I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** — Open new session with executing-plans, batch execution with checkpoints

Which approach?