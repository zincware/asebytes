# Facade API Parity Design

## Problem

Sync facades (BlobIO, ObjectIO, ASEIO) and async facades (AsyncBlobIO, AsyncObjectIO, AsyncASEIO) have inconsistent public APIs:

- Async facades have `drop()`, `reserve()`, `clear()`, `remove()` — sync facades don't
- Neither sync nor async has an explicit `get(index, keys=None)` for key-filtered reads
- Schema naming was inconsistent (now unified to `schema` everywhere)
- `AsyncBytesIO` was a duplicate of `AsyncBlobIO` (now deleted)

## Decisions

1. **Add `get()`, `drop()`, `reserve()` to all sync facades**
2. **Add `get()` to all async facades** for parity (key-filtered single-row read)
3. **Keep MutableSequence** inheritance on sync facades — `__setitem__`, `__delitem__`, `__iter__`, `__len__` remain
4. `clear()` and `remove()` are already inherited from MutableSequence on sync

## Methods to Add

### All sync facades (BlobIO, ObjectIO, ASEIO)

```python
def get(self, index: int, keys: list[K] | None = None) -> V:
    """Read a single row, optionally filtering to specific keys."""

def drop(self, *, keys: list[K]) -> None:
    """Remove specified columns from all rows."""

def reserve(self, count: int) -> None:
    """Pre-allocate space for `count` additional rows (hint to backend)."""
```

For ASEIO, `get()` returns `ase.Atoms` (applies `dict_to_atoms` conversion).

### All async facades (AsyncBlobIO, AsyncObjectIO, AsyncASEIO)

```python
async def get(self, index: int, keys: list[K] | None = None) -> V:
    """Read a single row, optionally filtering to specific keys."""
```

`drop()`, `clear()`, `remove()`, `reserve()` already exist on async facades.

## Unified Public API (target state)

| Method | Sync | Async | Notes |
|--------|------|-------|-------|
| `schema` | `@property` | `async schema()` | Column names |
| `get(i, keys=)` | sync | async | Key-filtered read |
| `__getitem__` | returns value/view | returns async view | Subscript access |
| `__setitem__` | sync | N/A (use views) | MutableSequence |
| `__delitem__` | sync | N/A (use views) | MutableSequence |
| `insert(i, v)` | sync | async | Insert at position |
| `extend(rows)` | sync | async | Bulk append |
| `drop(keys=)` | sync | async | Remove columns |
| `reserve(n)` | sync | async | Pre-allocate hint |
| `clear()` | MutableSequence | async | Remove all rows |
| `remove()` | MutableSequence | async | Remove backend |
| `len` | `__len__` | `async len()` | Row count |
| `__iter__`/`__aiter__` | sync iter | async iter | Iteration |
| context manager | N/A | `async with` | Cleanup |

## Files to Modify

- `src/asebytes/_blob_io.py` — add `get()`, `drop()`, `reserve()`
- `src/asebytes/_object_io.py` — add `get()`, `drop()`, `reserve()`
- `src/asebytes/io.py` — add `get()`, `drop()`, `reserve()`
- `src/asebytes/_async_blob_io.py` — add `get()`
- `src/asebytes/_async_object_io.py` — add `get()`
- `src/asebytes/_async_io.py` — add `get()`
