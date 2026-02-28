# Redis Blob Backend Design

**Date**: 2026-02-28
**Branch**: `feat/async-backends`

## Summary

Add a Redis-backed blob-level backend (`ReadWriteBackend[bytes, bytes]`) with native sync and async variants using `redis.Redis` and `redis.asyncio.Redis`.

## Decisions

- **Data model**: Redis hashes — one hash per row, fields = column names (bytes), values = bytes
- **Positional indexing**: Redis LIST for sort-key array (`LLEN`, `LINDEX`, `RPUSH`, `LREM`)
- **Backend level**: Blob-level only. ObjectIO/ASEIO access via `BlobToObjectAdapter` fallback
- **Namespacing**: Prefix-based within a Redis database
- **Async strategy**: Native async class using `redis.asyncio.Redis`, registered in async URI registry

## URI Format

```
redis://[user:password@]host:port[/db][/prefix]
```

- `redis://localhost:6379` → db=0, prefix=`default`
- `redis://localhost:6379/0/mydata` → db=0, prefix=`mydata`
- `redis://localhost:6379/2` → db=2, prefix=`default`

`from_uri()` extracts the connection URI (scheme + credentials + host + port + db) and the prefix from the trailing path segment.

## Redis Key Layout

| Key | Type | Purpose |
|-----|------|---------|
| `{prefix}:sort_keys` | LIST | Ordered sort keys for positional access |
| `{prefix}:next_sk` | STRING | Counter for allocating new sort keys |
| `{prefix}:row:{sort_key}` | HASH | Row data: field(bytes) → value(bytes) |

## Classes

### `RedisBlobBackend(ReadWriteBackend[bytes, bytes])`

Sync backend using `redis.Redis`.

**Constructor**: `__init__(self, url="redis://localhost:6379", prefix="default")`
- Creates `redis.Redis.from_url(url, decode_responses=False)`
- Stores prefix for key namespacing

**`from_uri(cls, uri, **kwargs)`**: Parses `redis://host:port/db/prefix`, extracts connection URL and prefix.

### `AsyncRedisBlobBackend(AsyncReadWriteBackend[bytes, bytes])`

Async backend using `redis.asyncio.Redis`.

Same interface with `async`/`await`. Uses `redis.asyncio.from_url()`.

## Key Operations

| Method | Redis Commands |
|--------|---------------|
| `__len__` | `LLEN {prefix}:sort_keys` |
| `get(i)` | `LINDEX` → sort_key, then `HGETALL {prefix}:row:{sk}` |
| `get(i, keys)` | `LINDEX` → sk, then `HMGET {prefix}:row:{sk} k1 k2 ...` |
| `get_many(indices)` | Pipeline: LINDEX per index + HGETALL per sort_key |
| `get_column(key, indices)` | Pipeline: LINDEX per index + HGET per sort_key |
| `keys(index)` | `LINDEX` → sk, then `HKEYS {prefix}:row:{sk}` |
| `set(i, data)` | `LINDEX` → sk, `DEL` old hash, `HSET` new (or DEL only for None) |
| `extend(values)` | `GET next_sk`, pipeline: HSET rows + RPUSH sort_keys + SET next_sk |
| `insert(i, val)` | `GET next_sk`, HSET row, get full list + insert + replace (LSET loop or DEL+RPUSH) |
| `delete(i)` | `LINDEX` → sk, pipeline: DEL hash + reconstruct list without sk |
| `update(i, data)` | `LINDEX` → sk, `HSET {prefix}:row:{sk} field1 val1 field2 val2` |
| `drop_keys(keys)` | Pipeline: `HDEL` per row for specified fields |
| `clear()` | SCAN `{prefix}:row:*` + DEL, DEL sort_keys, SET next_sk=0 |
| `remove()` | SCAN `{prefix}:*` + DEL all |

## Insert Implementation Note

Redis LIST lacks positional insert-by-index. Options:
1. Read full list → Python insert → DEL + RPUSH (simple, O(N))
2. Use LINSERT BEFORE pivot (requires knowing the value at position)

Option 1 is simpler and consistent with MongoDB's approach. For large datasets, the sort_keys list is already O(N) on mutations.

## Package Structure

```
src/asebytes/redis/
├── __init__.py           # exports RedisBlobBackend, AsyncRedisBlobBackend
├── _backend.py           # sync implementation
└── _async_backend.py     # async implementation
```

## Registry Changes

Four changes needed:

1. **Add `_BLOB_URI_REGISTRY`** in `_registry.py` — new dict for blob-level URI schemes (currently only glob patterns exist for blob backends)
2. **Add `_ASYNC_BLOB_URI_REGISTRY`** in `_registry.py` — async counterpart
3. **Update `get_blob_backend_cls()`** — check `_BLOB_URI_REGISTRY` before the object-adapter fallback
4. **Update `parse_uri()`** — recognize `redis` as a known scheme (also check blob URI registries)
5. **Update `get_backend_cls()`** — add fallback: if scheme not in `_URI_REGISTRY`, check `_BLOB_URI_REGISTRY` and wrap with `BlobToObjectAdapter`

```python
_BLOB_URI_REGISTRY = {
    "redis": ("asebytes.redis._backend", "RedisBlobBackend", "RedisBlobBackend"),
}
_ASYNC_BLOB_URI_REGISTRY = {
    "redis": ("asebytes.redis._async_backend", "AsyncRedisBlobBackend", "AsyncRedisBlobBackend"),
}
```

This gives us:
- `BlobIO("redis://...")` → `get_blob_backend_cls` finds `RedisBlobBackend` directly
- `ObjectIO("redis://...")` → `get_backend_cls` fallback wraps `RedisBlobBackend` in `BlobToObjectReadWriteAdapter`
- `AsyncBlobIO("redis://...")` → native `AsyncRedisBlobBackend`
- `AsyncObjectIO("redis://...")` → async blob backend wrapped in async `BlobToObjectAdapter`

## Dependencies

```toml
[project.optional-dependencies]
redis = ["redis>=5.0"]
```

Add `"asebytes[redis]"` to dev dependency group.

## CI

Add Redis service to `.github/workflows/tests.yml`:

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

## Testing

- Local Redis available at `localhost:6379` (Docker)
- Tests use `REDIS_URI` env var (default `redis://localhost:6379`)
- Each test creates a unique prefix (uuid) and cleans up via `remove()`
- Skip tests if Redis not available (same pattern as MongoDB tests)

## Error Handling

- `IndexError` on out-of-bounds (required by ABC contract)
- Redis `ConnectionError` propagates naturally
- `None` rows: sort key in list but no hash → `get()` returns None
