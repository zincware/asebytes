# Bulk Write Optimization Design

**Date:** 2026-02-28
**Status:** Approved

## Problem

`ColumnView.set()` and `RowView.set()`/`update()` loop N individual `_update_row` / `_write_row` calls — one per row. For network backends (Redis, MongoDB) this means N round-trips. For file backends (LMDB) it means N transactions. For columnar backends (Zarr, H5MD) it means N read-modify-write cycles instead of a single slice write.

## Solution: Two New ABC Methods + View Wiring

### ABC Changes

Add two non-abstract methods to `ReadWriteBackend` (sync) and `AsyncReadWriteBackend` (async):

```python
def update_many(self, start: int, data: list[dict[K, V]]) -> None:
    """Partial-merge contiguous rows [start, start+len(data)).
    Override for backends where batch partial updates are cheaper."""
    for i, d in enumerate(data):
        self.update(start + i, d)

def set_column(self, key: K, start: int, values: list[V]) -> None:
    """Write a single key across contiguous rows [start, start+len(values)).
    Override for columnar backends (Zarr, H5MD) or network backends (Redis, Mongo)."""
    for i, v in enumerate(values):
        self.update(start + i, {key: v})
```

Both have loop-based defaults — **zero breakage** for existing backends.

### ViewParent Protocol Extension

```python
# Sync
def _update_many(self, start: int, data: list[dict]) -> None: ...
def _set_column(self, key: str, start: int, values: list) -> None: ...
def _write_many(self, start: int, data: list) -> None: ...

# Async mirrors
async def _update_many(self, start: int, data: list[dict]) -> None: ...
async def _set_column(self, key: str, start: int, values: list) -> None: ...
async def _write_many(self, start: int, data: list) -> None: ...
```

### Facade Wiring

All 6 facades (ObjectIO, BlobIO, ASEIO + async mirrors) get thin delegation methods:

```python
def _update_many(self, start, data):
    self._backend.update_many(start, data)

def _set_column(self, key, start, values):
    self._backend.set_column(key, start, values)

def _write_many(self, start, data):
    self._backend.set_many(start, data)
```

### View Changes

**ColumnView.set()** — contiguous indices use bulk path:
- Single-key: `_set_column(key, start, values)`
- Multi-key: `_update_many(start, list_of_dicts)`
- Non-contiguous: fallback to individual `_update_row` calls

**RowView.set()** — contiguous indices use `_write_many(start, data)`
**RowView.update()** — contiguous indices use `_update_many(start, [data] * N)`
Same for all async view counterparts.

### SyncToAsyncAdapter

Forward `update_many` and `set_column` via `asyncio.to_thread`.

### Adapter Classes

`BlobToObjectReadWriteAdapter` and `ObjectToBlobReadWriteAdapter` forward with serialization.

## Backend Overrides (All in Initial PR)

| Backend | `update_many` | `set_column` |
|---------|:---:|:---:|
| MemoryObjectBackend | skip (already fast) | skip |
| LMDBBlobBackend | single write txn | single write txn |
| RedisBlobBackend | pipeline N HSET | pipeline N HSET |
| AsyncRedisBlobBackend | async pipeline | async pipeline |
| MongoObjectBackend | bulk_write([UpdateOne...]) | bulk_write |
| AsyncMongoObjectBackend | async bulk_write | async bulk_write |
| ZarrBackend | per-key slice write | `array[start:stop] = values` |
| H5MDBackend | per-key slice write | `ds[start:stop] = values` |

## Edge Cases

- Empty data list: no-op (early return)
- Single-element list: still goes through bulk path (equivalent to individual call)
- Non-contiguous indices: fallback to individual calls (no bulk path)
- Read-only backend: existing TypeError checks in facades prevent reaching bulk methods
- None/placeholder rows: `update_many` merges into None rows (creates new dict), same as `update()`

## Testing Strategy

- Existing `test_column_writes.py` must pass unchanged (behavioral equivalence)
- New tests verify bulk methods are called for contiguous indices
- New tests verify fallback for non-contiguous indices
- Each backend with overrides gets specific bulk operation tests
- Verify correctness of batch operations (partial failure, atomicity)
