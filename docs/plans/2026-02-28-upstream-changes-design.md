# Design: Upstream Package Support Changes

**Date:** 2026-02-28
**Branch:** feat/async-backends

Three changes to support an upstream package that uses asebytes as a storage layer.

---

## 1a. In-Memory Backend + `memory://` URI

### Problem

There is no zero-dependency, zero-IO backend for ephemeral storage. Upstream
needs a backend for testing and for transient in-memory data rooms without
requiring LMDB.

### Design

**New module:** `src/asebytes/memory/__init__.py` + `_backend.py`

```python
class MemoryObjectBackend(ReadWriteBackend[str, Any]):
    """In-memory backend backed by list[dict[str, Any] | None]."""
```

Backed by a plain `list`. All methods are trivial index operations. No
persistence, no threading, no locking.

**No async variant.** Use `SyncToAsyncAdapter(MemoryObjectBackend())` — the
overhead of `asyncio.to_thread` on a list lookup is negligible.

### URI Convention

Follow SQLAlchemy's authority-based URI pattern:

| SQLAlchemy | asebytes |
|---|---|
| `sqlite:///path/to/file.db` | `ObjectIO("data.lmdb")` (file path) |
| `sqlite:///:memory:` | — |
| `postgresql://user:pass@host/db` | `ObjectIO("mongodb://user:pass@host/db/col")` |

For in-memory, adopt `memory://` as a schemeless URI (no authority component):

```
memory://           → anonymous in-memory store
memory:///name      → named store (path component, three slashes like sqlite:///)
```

However: the upstream use case is always direct construction or anonymous
`memory://`. Named stores add complexity with no current need. **Start with
anonymous only** — `memory://` creates a fresh `MemoryObjectBackend()`.

**Registry entry:**
```python
_URI_REGISTRY["memory"] = ("asebytes.memory._backend", "MemoryObjectBackend", "MemoryObjectBackend")
```

**`from_uri` classmethod:**
```python
@classmethod
def from_uri(cls, uri: str, **kwargs) -> MemoryObjectBackend:
    # memory:// → fresh instance, remainder is ignored
    return cls(**kwargs)
```

### Exports

Add to `__init__.py`:
```python
from .memory import MemoryObjectBackend
__all__ += ["MemoryObjectBackend"]
```

No optional dependency — memory backend is always available.

---

## 1b. Async URI Registry

### Problem

`AsyncObjectIO("mongodb://...")` currently resolves the **sync**
`MongoObjectBackend` via `get_backend_cls()` and wraps it with
`SyncToAsyncAdapter`. This defeats native async — every MongoDB call goes
through `asyncio.to_thread` instead of using `motor`/`pymongo.AsyncMongoClient`
directly.

### Design

**New registry** in `_registry.py`:

```python
_ASYNC_URI_REGISTRY: dict[str, tuple[str, str | None, str]] = {
    "mongodb": (
        "asebytes.mongodb._async_backend",
        "AsyncMongoObjectBackend",
        "AsyncMongoObjectBackend",
    ),
}
```

**New function** `get_async_backend_cls(path, *, readonly=None)`:

1. Check `_ASYNC_URI_REGISTRY` for the scheme — if found, return the native
   async class directly.
2. Fall back to `get_backend_cls()` (sync registry) and signal "needs wrapping"
   by returning a tuple `(sync_cls, True)` or by having the caller wrap.

Actually, simpler: return the class and let the caller decide. If the class is
already an `AsyncReadBackend` subclass, use directly. If it's a sync
`ReadBackend`, wrap with `sync_to_async()`. The registry function just resolves
the class — wrapping is the facade's responsibility.

**Update all three async facades** (`AsyncBlobIO`, `AsyncObjectIO`,
`AsyncASEIO`) to use `get_async_backend_cls` when constructing from a string
path. The pattern in `__init__` becomes:

```python
if isinstance(backend, str):
    from ._registry import get_async_backend_cls, parse_uri
    from ._async_backends import sync_to_async, AsyncReadBackend as AsyncRB

    cls = get_async_backend_cls(backend, readonly=readonly)
    scheme, _ = parse_uri(backend)
    if scheme is not None:
        inst = cls.from_uri(backend, **kwargs)
    else:
        inst = cls(backend, **kwargs)

    # If we got a sync backend from fallback, wrap it
    if isinstance(inst, AsyncRB):
        self._backend = inst
    else:
        self._backend = sync_to_async(inst)
```

### `parse_uri` update

`parse_uri()` currently only checks `_URI_REGISTRY` for known schemes. It must
also check `_ASYNC_URI_REGISTRY` so that async facades can detect URI schemes
that only have async backends registered:

```python
if scheme in _URI_REGISTRY or scheme in _ASYNC_URI_REGISTRY:
    return scheme, remainder
```

---

## 1c. `extend()` Returns `int` (New Length)

### Problem

After `await storage.extend(frames)`, the upstream needs the new total length.
Currently this requires a second round-trip:

```python
await storage.extend(room_id, raw_frames)
new_total = await storage.get_length(room_id)  # extra network call
```

For remote backends (MongoDB), the `extend()` already knows the new count
internally — discarding it forces a wasteful second query. Same reasoning as
Redis `RPUSH` returning the new list length.

### Design

Change the return type of `extend()` from `None` to `int` across all layers:

| Layer | Change |
|---|---|
| `ReadWriteBackend.extend()` | `-> int` (abstract) |
| `AsyncReadWriteBackend.extend()` | `-> int` (abstract) |
| All backend implementations | Return `len(self)` after extending |
| All adapters | Propagate return value |
| All facades | Return `int` from `extend()` |
| `SyncToAsyncReadWriteAdapter` | Propagate return value |

**Backward compatibility:** Callers that ignore the return value (`db.extend(data)`)
are completely unaffected. Only callers that capture it (`n = db.extend(data)`)
see the new behavior — and those callers didn't exist before, so there's no
breakage.

**Precedent:** Redis `RPUSH` returns the length of the list after the push.

---

## Non-Goals

- Named memory stores (`memory:///name`) — no current need
- Async-specific glob registry (only URI schemes need async dispatch)
- Changing `insert()` return type (not requested by upstream)
