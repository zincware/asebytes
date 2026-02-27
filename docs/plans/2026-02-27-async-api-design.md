# Async API Design for asebytes

## Summary

Add async support to asebytes with backend-agnostic protocols at both the raw bytes
(`dict[bytes, bytes]`) and logical (`dict[str, Any]`) levels. This enables natively
async backends (MongoDB/motor) alongside existing sync backends (LMDB, Zarr, H5MD)
which get auto-wrapped via `asyncio.to_thread`.

## Design Decisions

1. **Separate classes**: `AsyncASEIO` / `ASEIO`, `AsyncBytesIO` / `BytesIO` — no mixed sync/async.
2. **Awaitable views**: `__getitem__` is always sync (returns a view). Views implement `__await__` for smart materialization and `__aiter__` for async iteration.
3. **`__await__` semantics**: single row view → unwrapped item, multi row view → list, column view → list of values.
4. **Naming**: async method = sync method + `a` prefix (`extend` → `extend`).
5. **`drop()`** for column/key removal (pandas-style), scoped via views.
6. **None placeholders** for reserving slots without data.
7. **Non-contiguous delete is TypeError**: `delete`/`insert` require contiguous slices or single int. Non-shifting ops (`set`, `update`, `drop`) work on arbitrary index lists.
8. **Bytes-level protocol**: new `RawReadableBackend` / `RawWritableBackend` ABCs (BytesIO currently has no ABC).
9. **Serialization adapter**: generalizes the LMDBBackend pattern of "raw bytes + msgpack" so any `RawBackend` can be lifted to str-level.

## Protocol Hierarchy

```
Bytes-level (BytesIO)              Str-level (ASEIO)
─────────────────────              ──────────────────
RawReadableBackend                 ReadableBackend         (exists, extended)
RawWritableBackend                 WritableBackend         (exists, extended)
AsyncRawReadableBackend            AsyncReadableBackend
AsyncRawWritableBackend            AsyncWritableBackend

Adapters:
  SyncToAsyncRawAdapter   — wraps sync Raw*Backend via to_thread
  SyncToAsyncAdapter      — wraps sync *Backend via to_thread
  SerializingBackend      — wraps Raw*Backend + serializer → *Backend
  AsyncSerializingBackend — async version of above
```

## New Backend Operations

All have default implementations; backends override for optimization.

| Method | Level | Description |
|--------|-------|-------------|
| `drop_keys(keys, indices?)` | Both | Remove specific keys from rows |
| `delete_rows(start, stop)` | Both | Delete contiguous range, shift down |
| `write_rows(start, data)` | Both | Overwrite contiguous range |
| `reserve(count)` | Both | Append `count` None placeholders |
| `clear()` | Both | Remove all data, keep container |
| `remove()` | Both | Destroy container entirely (no default) |

## Changes to Existing Protocols

- Row data type: `dict[str, Any]` → `dict[str, Any] | None` (None = placeholder)
- `WritableBackend` gains: `delete_rows`, `write_rows`, `drop_keys`, `reserve`, `clear`, `remove`

## RawReadableBackend (NEW)

```python
class RawReadableBackend(ABC):
    @abstractmethod
    def __len__(self) -> int: ...
    @abstractmethod
    def get_schema(self) -> list[bytes]: ...
    @abstractmethod
    def read_row(self, index: int, keys: list[bytes] | None = None) -> dict[bytes, bytes] | None: ...
    def keys(self, index: int) -> list[bytes]: ...   # default
    def read_rows(self, indices, keys=None) -> list[...]: ...      # default: loop
    def iter_rows(self, indices, keys=None) -> Iterator[...]: ...  # default: loop
```

## RawWritableBackend (NEW)

```python
class RawWritableBackend(RawReadableBackend):
    @abstractmethod
    def write_row(self, index: int, data: dict[bytes, bytes] | None) -> None: ...
    @abstractmethod
    def insert_row(self, index: int, data: dict[bytes, bytes] | None) -> None: ...
    @abstractmethod
    def delete_row(self, index: int) -> None: ...
    @abstractmethod
    def append_rows(self, data: list[dict[bytes, bytes] | None]) -> None: ...
    def update_row(self, index, data): ...       # default: read-modify-write
    def delete_rows(self, start, stop): ...      # default: loop reverse
    def write_rows(self, start, data): ...       # default: loop
    def drop_keys(self, keys, indices=None): ... # default: read-modify-write
    def reserve(self, count): ...                # default: append_rows([None]*count)
    def clear(self): ...                         # default: delete all
    def remove(self): ...                        # no default (NotImplementedError)
```

## Async Protocols

Mirror the sync protocols with all methods async. `__len__` becomes `async def len()`.

## View Types

```
AsyncASEIO.__getitem__
  int        → AsyncSingleRowView   (__await__ → Atoms | None)
  slice      → AsyncRowView         (__await__ → list, __aiter__, chunked)
  list[int]  → AsyncRowView
  str        → AsyncColumnView      (__await__ → list[values])
  list[str]  → AsyncColumnView

AsyncBytesIO.__getitem__
  int          → AsyncSingleRowView (__await__ → dict[bytes, bytes] | None)
  slice        → AsyncRowView
  list[int]    → AsyncRowView
  list[bytes]  → AsyncColumnFilterView (further [int]/[slice])
```

View methods: `set`, `delete` (contiguous only), `update`, `drop`, `keys`.
Sync views get matching methods: `set`, `delete`, `update`, `drop`, `keys`.

## SyncToAsyncAdapter

Wraps any sync backend for async use. Every method delegates via `asyncio.to_thread`:

```python
class SyncToAsyncAdapter(AsyncWritableBackend):
    def __init__(self, sync_backend: WritableBackend): ...
    async def read_row(self, index, keys=None):
        return await asyncio.to_thread(self._sync.read_row, index, keys)
```

Used automatically when `AsyncASEIO("data.lmdb")` detects a sync-only backend.

## Context Manager

```python
async with AsyncASEIO("mongodb://...") as db:
    atoms = await db[0]
# connection cleaned up via __aexit__

with ASEIO("data.lmdb") as db:   # optional, LMDB auto-opens
    atoms = db[0]
```

## API Reference

See `async-api.py` for complete usage examples with sync equivlents annotated.
