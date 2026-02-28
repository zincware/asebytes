# Upstream Package Support Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add in-memory backend with `memory://` URI, async URI registry for native async backends, and `extend() -> int` across all layers.

**Architecture:** Three independent changes applied bottom-up: (1c) extend return type first (foundational, touches all backends), then (1a) memory backend (uses the new extend signature), then (1b) async registry (uses memory backend for testing). Each change follows TDD.

**Tech Stack:** Python 3.11+, pytest, pytest-anyio, uv

**Commands:** Always use `uv run pytest`, never bare `pytest`. Always use `uv run python`, never bare `python`.

---

## Task 1: `extend() -> int` — Backend ABCs (RED)

**Files:**
- Create: `tests/test_extend_returns_length.py`

**Step 1: Write failing tests for extend return type**

```python
"""Tests that extend() returns the new length across all backend layers."""

import pytest

from asebytes import BlobIO, ObjectIO, ASEIO
from asebytes._backends import ReadWriteBackend
from asebytes.lmdb import LMDBBlobBackend, LMDBObjectBackend


class TestExtendReturnsLength:
    """extend() should return the new total length (int)."""

    def test_blob_backend_extend(self, tmp_path):
        backend = LMDBBlobBackend(str(tmp_path / "test.lmdb"))
        result = backend.extend([{b"k": b"v1"}, {b"k": b"v2"}])
        assert result == 2
        result2 = backend.extend([{b"k": b"v3"}])
        assert result2 == 3

    def test_object_backend_extend(self, tmp_path):
        backend = LMDBObjectBackend(str(tmp_path / "test.lmdb"))
        result = backend.extend([{"a": 1}, {"a": 2}])
        assert result == 2
        result2 = backend.extend([{"a": 3}])
        assert result2 == 3

    def test_blobio_extend(self, tmp_path):
        db = BlobIO(str(tmp_path / "test.lmdb"))
        result = db.extend([{b"k": b"v1"}, {b"k": b"v2"}])
        assert result == 2

    def test_objectio_extend(self, tmp_path):
        db = ObjectIO(str(tmp_path / "test.lmdb"))
        result = db.extend([{"a": 1}])
        assert result == 1

    def test_aseio_extend(self, tmp_path, ethanol):
        db = ASEIO(str(tmp_path / "test.lmdb"))
        result = db.extend(ethanol[:3])
        assert result == 3
        result2 = db.extend(ethanol[3:5])
        assert result2 == 5

    def test_extend_empty_list(self, tmp_path):
        backend = LMDBBlobBackend(str(tmp_path / "test.lmdb"))
        backend.extend([{b"k": b"v1"}])
        result = backend.extend([])
        assert result == 1  # unchanged length


@pytest.mark.anyio
class TestAsyncExtendReturnsLength:
    """Async extend() should also return new length."""

    async def test_async_blobio_extend(self, tmp_path):
        from asebytes import AsyncBlobIO
        db = AsyncBlobIO(str(tmp_path / "test.lmdb"))
        result = await db.extend([{b"k": b"v1"}, {b"k": b"v2"}])
        assert result == 2

    async def test_async_objectio_extend(self, tmp_path):
        from asebytes import AsyncObjectIO
        db = AsyncObjectIO(str(tmp_path / "test.lmdb"))
        result = await db.extend([{"a": 1}])
        assert result == 1

    async def test_async_aseio_extend(self, tmp_path, ethanol):
        from asebytes import AsyncASEIO
        db = AsyncASEIO(str(tmp_path / "test.lmdb"))
        result = await db.extend(ethanol[:3])
        assert result == 3

    async def test_sync_to_async_adapter_extend(self, tmp_path):
        from asebytes._async_backends import SyncToAsyncReadWriteAdapter
        backend = LMDBObjectBackend(str(tmp_path / "test.lmdb"))
        adapter = SyncToAsyncReadWriteAdapter(backend)
        result = await adapter.extend([{"a": 1}, {"a": 2}])
        assert result == 2
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_extend_returns_length.py -x -q`
Expected: FAIL — `assert None == 2`

**Step 3: Commit failing tests**

```
git add tests/test_extend_returns_length.py
git commit -m "test: add failing tests for extend() returning new length (RED)"
```

---

## Task 2: `extend() -> int` — Implementation (GREEN)

**Files:**
- Modify: `src/asebytes/_backends.py:88` — ABC signature
- Modify: `src/asebytes/_async_backends.py:77` — async ABC signature
- Modify: `src/asebytes/lmdb/_blob_backend.py:443-530` — LMDB blob backend
- Modify: `src/asebytes/zarr/_backend.py:227-265` — Zarr backend
- Modify: `src/asebytes/h5md/_backend.py:407-456` — H5MD backend
- Modify: `src/asebytes/mongodb/_backend.py:198-218` — MongoDB sync
- Modify: `src/asebytes/mongodb/_async_backend.py:195-215` — MongoDB async
- Modify: `src/asebytes/_adapters.py:118-122,214-218` — sync adapters
- Modify: `src/asebytes/_async_adapters.py:110-114,208-212` — async adapters
- Modify: `src/asebytes/_async_backends.py:172-178` — SyncToAsync adapter
- Modify: `src/asebytes/_blob_io.py:161-164` — BlobIO facade
- Modify: `src/asebytes/_object_io.py:165-168` — ObjectIO facade
- Modify: `src/asebytes/io.py:220-225` — ASEIO facade
- Modify: `src/asebytes/_async_blob_io.py:141-144` — AsyncBlobIO facade
- Modify: `src/asebytes/_async_object_io.py:150-153` — AsyncObjectIO facade
- Modify: `src/asebytes/_async_io.py:157-160` — AsyncASEIO facade

**Step 1: Update backend ABCs**

In `_backends.py`, change the abstract `extend` signature:
```python
@abstractmethod
def extend(self, values: list[dict[K, V] | None]) -> int:
    """Append multiple rows efficiently (bulk operation).

    Returns the new total length.
    """
    ...
```

In `_async_backends.py`, same change:
```python
@abstractmethod
async def extend(self, values: list[dict[K, V] | None]) -> int: ...
```

**Step 2: Update all concrete backend implementations**

Each backend must `return len(self)` (or equivalent) at the end of `extend()`.

**LMDBBlobBackend** (`lmdb/_blob_backend.py:443`): The method currently ends
with `self._invalidate_cache()`. After that line, add:
```python
return current_count + n
```
Also handle the early return for empty list — change `return` to `return len(self)`.

**ZarrBackend** (`zarr/_backend.py:227`): Ends at line ~265 with
`self._discover()`. After that, add:
```python
return self._n_frames
```
Early return: `return self._n_frames`.

**H5MDBackend** (`h5md/_backend.py:407`): Ends at line ~456 with
`self._n_frames += n_new`. After that, add:
```python
return self._n_frames
```
Early return: `return self._n_frames`.

**MongoObjectBackend** (`mongodb/_backend.py:198`): Ends at line ~218 updating
meta. After that, add:
```python
return self._count
```
Early return: `return self._count`.

**AsyncMongoObjectBackend** (`mongodb/_async_backend.py:195`): Same pattern:
```python
return self._count
```
Early return: `return self._count`.

**Step 3: Update adapters to propagate return value**

In `_adapters.py`, two adapters:

`BlobToObjectReadWriteAdapter.extend` (line 118):
```python
def extend(self, values: list[dict[str, Any] | None]) -> int:
    return self._store.extend([
        _serialize_row(v) if v is not None else None
        for v in values
    ])
```

`ObjectToBlobReadWriteAdapter.extend` (line 214):
```python
def extend(self, values: list[dict[bytes, bytes] | None]) -> int:
    return self._store.extend([
        _deserialize_row(v) if v is not None else None
        for v in values
    ])
```

In `_async_adapters.py`, same changes with `async`/`await`:

`AsyncBlobToObjectReadWriteAdapter.extend` (line 110):
```python
async def extend(self, values: list[dict[str, Any] | None]) -> int:
    return await self._store.extend([...])
```

`AsyncObjectToBlobReadWriteAdapter.extend` (line 208):
```python
async def extend(self, values: list[dict[bytes, bytes] | None]) -> int:
    return await self._store.extend([...])
```

**Step 4: Update SyncToAsync adapter**

In `_async_backends.py`, `SyncToAsyncReadWriteAdapter.extend` (line 172):
```python
async def extend(self, values) -> int:
    return await asyncio.to_thread(self._backend.extend, values)
```

**Step 5: Update sync facades**

`_blob_io.py` `BlobIO.extend` (line 161):
```python
def extend(self, values) -> int:
    if not isinstance(self._backend, ReadWriteBackend):
        raise TypeError("Backend is read-only")
    return self._backend.extend(list(values))
```

`_object_io.py` `ObjectIO.extend` (line 165):
```python
def extend(self, values) -> int:
    if not isinstance(self._backend, ReadWriteBackend):
        raise TypeError("Backend is read-only")
    return self._backend.extend(list(values))
```

`io.py` `ASEIO.extend` (line 220):
```python
def extend(self, values: list[ase.Atoms]) -> int:
    """Efficiently extend with multiple Atoms objects using bulk operations."""
    if not isinstance(self._backend, ReadWriteBackend):
        raise TypeError("Backend is read-only")
    data_list = [atoms_to_dict(atoms) for atoms in values]
    return self._backend.extend(data_list)
```

**Step 6: Update async facades**

`_async_blob_io.py` `AsyncBlobIO.extend` (line 141):
```python
async def extend(self, data: list[dict[bytes, bytes] | None]) -> int:
    if not isinstance(self._backend, AsyncReadWriteBackend):
        raise TypeError("Backend is read-only")
    return await self._backend.extend(data)
```

`_async_object_io.py` `AsyncObjectIO.extend` (line 150):
```python
async def extend(self, data: list[Any]) -> int:
    if not isinstance(self._backend, AsyncReadWriteBackend):
        raise TypeError("Backend is read-only")
    return await self._backend.extend(data)
```

`_async_io.py` `AsyncASEIO.extend` (line 157):
```python
async def extend(self, data: list[Any]) -> int:
    if not isinstance(self._backend, AsyncReadWriteBackend):
        raise TypeError("Backend is read-only")
    return await self._backend.extend(data)
```

**Step 7: Run tests to verify GREEN**

Run: `uv run pytest tests/test_extend_returns_length.py -x -q`
Expected: all PASS

**Step 8: Run full suite to verify no regressions**

Run: `uv run pytest -x -q --ignore=tests/test_mongodb.py`
Expected: all PASS (callers that ignored return value are unaffected)

**Step 9: Commit**

```
git add -u
git commit -m "feat: extend() returns new length across all backends and facades"
```

---

## Task 3: In-Memory Backend (RED)

**Files:**
- Create: `tests/test_memory_backend.py`

**Step 1: Write failing tests**

```python
"""Tests for the in-memory backend."""

import pytest

from asebytes.memory._backend import MemoryObjectBackend


class TestMemoryObjectBackend:
    def test_empty_on_creation(self):
        backend = MemoryObjectBackend()
        assert len(backend) == 0

    def test_extend_and_get(self):
        backend = MemoryObjectBackend()
        backend.extend([{"a": 1}, {"a": 2}])
        assert len(backend) == 2
        assert backend.get(0) == {"a": 1}
        assert backend.get(1) == {"a": 2}

    def test_extend_returns_length(self):
        backend = MemoryObjectBackend()
        assert backend.extend([{"a": 1}]) == 1
        assert backend.extend([{"a": 2}, {"a": 3}]) == 3

    def test_set(self):
        backend = MemoryObjectBackend()
        backend.extend([{"a": 1}])
        backend.set(0, {"a": 99})
        assert backend.get(0) == {"a": 99}

    def test_delete(self):
        backend = MemoryObjectBackend()
        backend.extend([{"a": 1}, {"a": 2}, {"a": 3}])
        backend.delete(1)
        assert len(backend) == 2
        assert backend.get(1) == {"a": 3}

    def test_insert(self):
        backend = MemoryObjectBackend()
        backend.extend([{"a": 1}, {"a": 3}])
        backend.insert(1, {"a": 2})
        assert len(backend) == 3
        assert backend.get(1) == {"a": 2}
        assert backend.get(2) == {"a": 3}

    def test_get_with_keys(self):
        backend = MemoryObjectBackend()
        backend.extend([{"a": 1, "b": 2, "c": 3}])
        result = backend.get(0, keys=["a", "c"])
        assert result == {"a": 1, "c": 3}

    def test_get_none_placeholder(self):
        backend = MemoryObjectBackend()
        backend.extend([None])
        assert backend.get(0) is None

    def test_clear(self):
        backend = MemoryObjectBackend()
        backend.extend([{"a": 1}, {"a": 2}])
        backend.clear()
        assert len(backend) == 0

    def test_reserve(self):
        backend = MemoryObjectBackend()
        backend.reserve(3)
        assert len(backend) == 3
        assert backend.get(0) is None
        assert backend.get(2) is None

    def test_remove(self):
        backend = MemoryObjectBackend()
        backend.extend([{"a": 1}])
        backend.remove()
        assert len(backend) == 0

    def test_keys(self):
        backend = MemoryObjectBackend()
        backend.extend([{"x": 1, "y": 2}])
        assert sorted(backend.keys(0)) == ["x", "y"]

    def test_keys_none_placeholder(self):
        backend = MemoryObjectBackend()
        backend.extend([None])
        assert backend.keys(0) == []

    def test_update(self):
        backend = MemoryObjectBackend()
        backend.extend([{"a": 1, "b": 2}])
        backend.update(0, {"b": 99, "c": 3})
        assert backend.get(0) == {"a": 1, "b": 99, "c": 3}

    def test_get_column(self):
        backend = MemoryObjectBackend()
        backend.extend([{"a": 1}, {"a": 2}, {"a": 3}])
        assert backend.get_column("a") == [1, 2, 3]

    def test_index_error(self):
        backend = MemoryObjectBackend()
        with pytest.raises(IndexError):
            backend.get(0)

    def test_from_uri(self):
        backend = MemoryObjectBackend.from_uri("memory://")
        assert isinstance(backend, MemoryObjectBackend)
        assert len(backend) == 0

    def test_from_uri_with_path(self):
        backend = MemoryObjectBackend.from_uri("memory:///my-store")
        assert isinstance(backend, MemoryObjectBackend)
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_memory_backend.py -x -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'asebytes.memory'`

**Step 3: Commit**

```
git add tests/test_memory_backend.py
git commit -m "test: add failing tests for in-memory backend (RED)"
```

---

## Task 4: In-Memory Backend (GREEN)

**Files:**
- Create: `src/asebytes/memory/__init__.py`
- Create: `src/asebytes/memory/_backend.py`

**Step 1: Create the backend module**

`src/asebytes/memory/__init__.py`:
```python
from ._backend import MemoryObjectBackend

__all__ = ["MemoryObjectBackend"]
```

`src/asebytes/memory/_backend.py`:
```python
"""In-memory backend backed by a plain list. No persistence, no threading."""

from __future__ import annotations

from typing import Any

from .._backends import ReadWriteBackend


class MemoryObjectBackend(ReadWriteBackend[str, Any]):
    """In-memory ReadWriteBackend backed by list[dict[str, Any] | None].

    No persistence — data exists only for the lifetime of the object.
    Suitable for testing, ephemeral storage, and transient data rooms.
    """

    def __init__(self) -> None:
        self._data: list[dict[str, Any] | None] = []

    @classmethod
    def from_uri(cls, uri: str, **kwargs: Any) -> MemoryObjectBackend:
        """Create from a ``memory://`` URI. The path is ignored."""
        return cls(**kwargs)

    def __len__(self) -> int:
        return len(self._data)

    def get(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any] | None:
        if index < 0 or index >= len(self._data):
            raise IndexError(index)
        row = self._data[index]
        if row is None or keys is None:
            return row
        return {k: row[k] for k in keys if k in row}

    def set(self, index: int, value: dict[str, Any] | None) -> None:
        self._data[index] = value

    def delete(self, index: int) -> None:
        del self._data[index]

    def extend(self, values: list[dict[str, Any] | None]) -> int:
        self._data.extend(values)
        return len(self._data)

    def insert(self, index: int, value: dict[str, Any] | None) -> None:
        self._data.insert(index, value)

    def clear(self) -> None:
        self._data.clear()

    def remove(self) -> None:
        self._data.clear()
```

**Step 2: Run tests to verify GREEN**

Run: `uv run pytest tests/test_memory_backend.py -x -q`
Expected: all PASS

**Step 3: Commit**

```
git add src/asebytes/memory/
git commit -m "feat: add in-memory backend (MemoryObjectBackend)"
```

---

## Task 5: Register `memory://` URI + exports (RED then GREEN)

**Files:**
- Create: `tests/test_memory_uri.py`
- Modify: `src/asebytes/_registry.py:26-31` — add memory to `_URI_REGISTRY`
- Modify: `src/asebytes/_registry.py:33-43` — add hint
- Modify: `src/asebytes/__init__.py` — export `MemoryObjectBackend`

**Step 1: Write failing tests**

```python
"""Tests for memory:// URI integration."""

import pytest


def test_objectio_memory_uri():
    from asebytes import ObjectIO
    db = ObjectIO("memory://")
    db.extend([{"a": 1}, {"a": 2}])
    assert len(db) == 2
    assert db[0] == {"a": 1}


def test_aseio_memory_uri(ethanol):
    from asebytes import ASEIO
    db = ASEIO("memory://")
    db.extend(ethanol[:2])
    assert len(db) == 2


def test_blobio_memory_uri():
    """BlobIO("memory://") should work via ObjectToBlob adapter fallback."""
    from asebytes import BlobIO
    db = BlobIO("memory://")
    db.extend([{b"k": b"v"}])
    assert len(db) == 1


@pytest.mark.anyio
async def test_async_objectio_memory_uri():
    from asebytes import AsyncObjectIO
    db = AsyncObjectIO("memory://")
    await db.extend([{"a": 1}])
    assert await db.len() == 1


def test_memory_backend_importable():
    from asebytes import MemoryObjectBackend
    backend = MemoryObjectBackend()
    assert len(backend) == 0
```

**Step 2: Run to verify FAIL**

Run: `uv run pytest tests/test_memory_uri.py -x -q`
Expected: FAIL — `KeyError: No backend registered for 'memory://'`

**Step 3: Implement**

In `_registry.py`, add to `_URI_REGISTRY`:
```python
"memory": ("asebytes.memory._backend", "MemoryObjectBackend", "MemoryObjectBackend"),
```

In `__init__.py`, add (no try/except — memory backend has no optional deps):
```python
from .memory import MemoryObjectBackend
```

And add `"MemoryObjectBackend"` to `__all__`.

**Step 4: Run to verify GREEN**

Run: `uv run pytest tests/test_memory_uri.py -x -q`
Expected: all PASS

**Step 5: Run full suite**

Run: `uv run pytest -x -q --ignore=tests/test_mongodb.py`
Expected: all PASS

**Step 6: Commit**

```
git add src/asebytes/_registry.py src/asebytes/__init__.py tests/test_memory_uri.py
git commit -m "feat: register memory:// URI and export MemoryObjectBackend"
```

---

## Task 6: Async URI Registry (RED)

**Files:**
- Create: `tests/test_async_uri_registry.py`

**Step 1: Write failing tests**

These test that `get_async_backend_cls` exists and returns native async classes.

```python
"""Tests for async URI registry — native async backends for URI schemes."""

import pytest


def test_get_async_backend_cls_exists():
    from asebytes._registry import get_async_backend_cls
    assert callable(get_async_backend_cls)


def test_async_mongodb_returns_native_class():
    """mongodb:// should resolve to AsyncMongoObjectBackend, not sync wrapper."""
    from asebytes._registry import get_async_backend_cls
    cls = get_async_backend_cls("mongodb://localhost/db/col")
    assert cls.__name__ == "AsyncMongoObjectBackend"


def test_async_memory_falls_back_to_sync():
    """memory:// has no async-specific entry, should return sync class."""
    from asebytes._registry import get_async_backend_cls
    cls = get_async_backend_cls("memory://")
    # Returns sync MemoryObjectBackend (caller wraps with sync_to_async)
    assert cls.__name__ == "MemoryObjectBackend"


def test_async_lmdb_falls_back_to_sync():
    """*.lmdb has no async-specific entry, should return sync class."""
    from asebytes._registry import get_async_backend_cls
    cls = get_async_backend_cls("data.lmdb")
    assert cls.__name__ == "LMDBObjectBackend"


def test_parse_uri_recognises_async_only_schemes():
    """parse_uri should recognise schemes from _ASYNC_URI_REGISTRY too."""
    from asebytes._registry import parse_uri
    # If a scheme is only in _ASYNC_URI_REGISTRY (hypothetical),
    # parse_uri should still recognise it
    scheme, remainder = parse_uri("mongodb://localhost/db")
    assert scheme == "mongodb"  # already in sync registry, but test anyway


@pytest.mark.anyio
async def test_async_objectio_uses_native_backend_for_memory():
    """AsyncObjectIO("memory://") should work (sync fallback + wrap)."""
    from asebytes import AsyncObjectIO
    db = AsyncObjectIO("memory://")
    await db.extend([{"a": 1}])
    n = await db.len()
    assert n == 1
```

**Step 2: Run to verify FAIL**

Run: `uv run pytest tests/test_async_uri_registry.py -x -q`
Expected: FAIL — `ImportError: cannot import name 'get_async_backend_cls'`

**Step 3: Commit**

```
git add tests/test_async_uri_registry.py
git commit -m "test: add failing tests for async URI registry (RED)"
```

---

## Task 7: Async URI Registry (GREEN)

**Files:**
- Modify: `src/asebytes/_registry.py` — add `_ASYNC_URI_REGISTRY`, `get_async_backend_cls`, update `parse_uri`
- Modify: `src/asebytes/_async_blob_io.py:36-46` — use async registry
- Modify: `src/asebytes/_async_object_io.py:39-49` — use async registry
- Modify: `src/asebytes/_async_io.py:43-53` — use async registry

**Step 1: Add async registry to `_registry.py`**

After `_URI_REGISTRY`, add:
```python
# Async URI scheme → native async backend class.
# Checked first by get_async_backend_cls(); if no entry, falls back to sync.
_ASYNC_URI_REGISTRY: dict[str, tuple[str, str | None, str]] = {
    "mongodb": (
        "asebytes.mongodb._async_backend",
        "AsyncMongoObjectBackend",
        "AsyncMongoObjectBackend",
    ),
}
```

Add `_EXTRAS_HINT` entry:
```python
"asebytes.mongodb._async_backend": "mongodb",
```

Update `parse_uri` to recognise async-only schemes:
```python
if scheme in _URI_REGISTRY or scheme in _ASYNC_URI_REGISTRY:
    return scheme, remainder
```

Add `get_async_backend_cls`:
```python
def get_async_backend_cls(path: str, *, readonly: bool | None = None):
    """Resolve a path/URI to a backend class, preferring native async.

    Checks _ASYNC_URI_REGISTRY first for URI schemes. If no async-specific
    entry exists, falls back to get_backend_cls (sync registry). The caller
    is responsible for wrapping sync backends with sync_to_async().
    """
    scheme, _remainder = parse_uri(path)
    if scheme is not None and scheme in _ASYNC_URI_REGISTRY:
        module_path, writable, read_only = _ASYNC_URI_REGISTRY[scheme]
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

    # Fall back to sync registry
    return get_backend_cls(path, readonly=readonly)
```

**Step 2: Update async facade `__init__` methods**

All three async facades (`AsyncBlobIO`, `AsyncObjectIO`, `AsyncASEIO`)
currently do:
```python
cls = get_backend_cls(backend, readonly=readonly)
# ... construct sync backend ...
self._backend = sync_to_async(sync_backend)
```

Change to:
```python
from ._registry import get_async_backend_cls, parse_uri
from ._async_backends import sync_to_async, AsyncReadBackend

cls = get_async_backend_cls(backend, readonly=readonly)
scheme, _ = parse_uri(backend)
if scheme is not None:
    inst = cls.from_uri(backend, **kwargs)
else:
    inst = cls(backend, **kwargs)

# If the registry returned a native async class, use directly
if isinstance(inst, AsyncReadBackend):
    self._backend = inst
else:
    self._backend = sync_to_async(inst)
```

For `AsyncBlobIO`, the pattern is slightly different since it uses
`get_blob_backend_cls`. Update it to also try `get_async_backend_cls` first
for URI schemes, then fall back to blob registry for file paths:
```python
from ._registry import get_async_backend_cls, get_blob_backend_cls, parse_uri
from ._async_backends import sync_to_async, AsyncReadBackend

scheme, _ = parse_uri(backend)
if scheme is not None:
    cls = get_async_backend_cls(backend, readonly=readonly)
    inst = cls.from_uri(backend, **kwargs)
else:
    cls = get_blob_backend_cls(backend, readonly=readonly)
    inst = cls(backend, **kwargs)

if isinstance(inst, AsyncReadBackend):
    self._backend = inst
else:
    self._backend = sync_to_async(inst)
```

**Step 3: Run tests to verify GREEN**

Run: `uv run pytest tests/test_async_uri_registry.py -x -q`
Expected: all PASS

**Step 4: Run full suite**

Run: `uv run pytest -x -q --ignore=tests/test_mongodb.py`
Expected: all PASS

**Step 5: Commit**

```
git add -u
git commit -m "feat: async URI registry for native async backend dispatch"
```

---

## Task 8: Final validation

**Step 1: Run full test suite**

Run: `uv run pytest -x -q --ignore=tests/test_mongodb.py`
Expected: all PASS, no regressions

**Step 2: Verify exports**

Run: `uv run python -c "from asebytes import MemoryObjectBackend; print(MemoryObjectBackend())"`

**Step 3: Verify async registry**

Run: `uv run python -c "from asebytes._registry import get_async_backend_cls; print(get_async_backend_cls('memory://'))""`

**Step 4: Verify extend return type**

Run: `uv run python -c "from asebytes import ObjectIO; db = ObjectIO('memory://'); print(db.extend([{'a': 1}]))"`
Expected: prints `1`
