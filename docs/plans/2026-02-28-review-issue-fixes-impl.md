# Review Issue Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix all 9 issues from the code review to achieve full API parity across all 6 facades and fix the critical SyncToAsyncAdapter bug.

**Architecture:** Split the monolithic `SyncToAsyncAdapter` into read-only and read-write variants so `isinstance` guards work correctly. Add missing `update()`, `clear()`, `remove()`, `_drop_keys()` methods to facades. Fix type annotations and minor inconsistencies.

**Tech Stack:** Python 3.10+, pytest, asyncio, uv

---

### Task 1: Split SyncToAsyncAdapter into read-only and read-write variants

The current `SyncToAsyncAdapter` inherits `AsyncReadWriteBackend` unconditionally. When a read-only backend (e.g. `ASEReadOnlyBackend`) is passed, facade write guards (`isinstance(self._backend, AsyncReadWriteBackend)`) always pass, causing `AttributeError` at runtime instead of clean `TypeError`.

**Files:**
- Modify: `src/asebytes/_async_backends.py:129-189`
- Test: `tests/test_raw_protocols.py` (existing tests, new tests for read-only adapter)

**Step 1: Write the failing test**

Create `tests/test_sync_to_async_adapter.py`:

```python
"""Tests for SyncToAsyncReadAdapter / SyncToAsyncReadWriteAdapter."""

from __future__ import annotations

import pytest
import asyncio
from typing import Any

from asebytes._backends import ReadBackend, ReadWriteBackend
from asebytes._async_backends import (
    AsyncReadBackend,
    AsyncReadWriteBackend,
    sync_to_async,
)


class MemoryReadOnly(ReadBackend):
    """Minimal read-only backend for testing."""

    def __init__(self, data: list[dict[str, Any] | None] | None = None):
        self._data = data or []

    def __len__(self) -> int:
        return len(self._data)

    def get(self, index, keys=None):
        if index < 0 or index >= len(self._data):
            raise IndexError(index)
        row = self._data[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)


class MemoryReadWrite(MemoryReadOnly, ReadWriteBackend):
    """Minimal read-write backend for testing."""

    def set(self, index, value):
        if index < len(self._data):
            self._data[index] = value
        elif index == len(self._data):
            self._data.append(value)
        else:
            raise IndexError(index)

    def delete(self, index):
        del self._data[index]

    def extend(self, values):
        self._data.extend(values)

    def insert(self, index, value):
        self._data.insert(index, value)


@pytest.mark.asyncio
class TestSyncToAsyncReadOnly:
    """Read-only adapter must NOT be an AsyncReadWriteBackend."""

    async def test_read_only_adapter_type(self):
        backend = MemoryReadOnly([{"a": 1}])
        adapter = sync_to_async(backend)
        assert isinstance(adapter, AsyncReadBackend)
        assert not isinstance(adapter, AsyncReadWriteBackend)

    async def test_read_only_adapter_get(self):
        backend = MemoryReadOnly([{"a": 1}, {"b": 2}])
        adapter = sync_to_async(backend)
        assert await adapter.get(0) == {"a": 1}
        assert await adapter.len() == 2

    async def test_read_only_adapter_keys(self):
        backend = MemoryReadOnly([{"a": 1, "b": 2}])
        adapter = sync_to_async(backend)
        assert sorted(await adapter.keys(0)) == ["a", "b"]

    async def test_read_only_adapter_no_set(self):
        backend = MemoryReadOnly([{"a": 1}])
        adapter = sync_to_async(backend)
        assert not hasattr(adapter, "set")


@pytest.mark.asyncio
class TestSyncToAsyncReadWrite:
    """Read-write adapter must be an AsyncReadWriteBackend."""

    async def test_read_write_adapter_type(self):
        backend = MemoryReadWrite([{"a": 1}])
        adapter = sync_to_async(backend)
        assert isinstance(adapter, AsyncReadBackend)
        assert isinstance(adapter, AsyncReadWriteBackend)

    async def test_read_write_adapter_set(self):
        backend = MemoryReadWrite([{"a": 1}])
        adapter = sync_to_async(backend)
        await adapter.set(0, {"a": 99})
        assert await adapter.get(0) == {"a": 99}

    async def test_read_write_adapter_update(self):
        backend = MemoryReadWrite([{"a": 1, "b": 2}])
        adapter = sync_to_async(backend)
        await adapter.update(0, {"a": 99})
        assert await adapter.get(0) == {"a": 99, "b": 2}

    async def test_read_write_adapter_extend(self):
        backend = MemoryReadWrite([])
        adapter = sync_to_async(backend)
        await adapter.extend([{"a": 1}, {"a": 2}])
        assert await adapter.len() == 2

    async def test_read_write_adapter_delete(self):
        backend = MemoryReadWrite([{"a": 1}, {"a": 2}])
        adapter = sync_to_async(backend)
        await adapter.delete(0)
        assert await adapter.len() == 1

    async def test_read_write_adapter_clear(self):
        backend = MemoryReadWrite([{"a": 1}, {"a": 2}])
        adapter = sync_to_async(backend)
        await adapter.clear()
        assert await adapter.len() == 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_sync_to_async_adapter.py -x -v`
Expected: FAIL — `ImportError` because `sync_to_async` doesn't exist yet.

**Step 3: Write minimal implementation**

In `src/asebytes/_async_backends.py`, replace `SyncToAsyncAdapter` (lines 129–189) with:

```python
# ── Sync-to-async adapters ──────────────────────────────────────────────


class SyncToAsyncReadAdapter(AsyncReadBackend[K, V]):
    """Wraps a sync ReadBackend[K,V] → AsyncReadBackend[K,V].

    Uses asyncio.to_thread for all calls.
    """

    def __init__(self, backend: ReadBackend[K, V]):
        self._backend = backend

    async def len(self) -> int:
        return await asyncio.to_thread(len, self._backend)

    async def get(self, index, keys=None):
        return await asyncio.to_thread(self._backend.get, index, keys)

    async def get_many(self, indices, keys=None):
        return await asyncio.to_thread(self._backend.get_many, indices, keys)

    async def get_column(self, key, indices=None):
        return await asyncio.to_thread(self._backend.get_column, key, indices)

    async def keys(self, index):
        return await asyncio.to_thread(self._backend.keys, index)


class SyncToAsyncReadWriteAdapter(SyncToAsyncReadAdapter[K, V], AsyncReadWriteBackend[K, V]):
    """Wraps a sync ReadWriteBackend[K,V] → AsyncReadWriteBackend[K,V].

    Inherits all read methods from SyncToAsyncReadAdapter.
    """

    def __init__(self, backend: ReadWriteBackend[K, V]):
        super().__init__(backend)

    async def set(self, index, value):
        return await asyncio.to_thread(self._backend.set, index, value)

    async def delete(self, index):
        return await asyncio.to_thread(self._backend.delete, index)

    async def extend(self, values):
        return await asyncio.to_thread(self._backend.extend, values)

    async def insert(self, index, value):
        return await asyncio.to_thread(self._backend.insert, index, value)

    async def update(self, index, data):
        return await asyncio.to_thread(self._backend.update, index, data)

    async def delete_many(self, start, stop):
        return await asyncio.to_thread(self._backend.delete_many, start, stop)

    async def drop_keys(self, keys, indices=None):
        return await asyncio.to_thread(self._backend.drop_keys, keys, indices)

    async def set_many(self, start, data):
        return await asyncio.to_thread(self._backend.set_many, start, data)

    async def reserve(self, count):
        return await asyncio.to_thread(self._backend.reserve, count)

    async def clear(self):
        return await asyncio.to_thread(self._backend.clear)

    async def remove(self):
        return await asyncio.to_thread(self._backend.remove)


def sync_to_async(backend: ReadBackend[K, V]) -> AsyncReadBackend[K, V]:
    """Wrap a sync backend as an async backend, choosing the right adapter."""
    if isinstance(backend, ReadWriteBackend):
        return SyncToAsyncReadWriteAdapter(backend)
    return SyncToAsyncReadAdapter(backend)


# Backward-compat alias
SyncToAsyncAdapter = SyncToAsyncReadWriteAdapter
```

Also add `from ._backends import ReadBackend` to the import at line 8 (currently only imports `ReadWriteBackend`).

**Step 4: Update async facade `__init__` methods**

In each of the 3 async facades, replace `SyncToAsyncAdapter(sync_backend)` with `sync_to_async(sync_backend)`:

- `src/asebytes/_async_blob_io.py:40-44` — change `from ._async_backends import SyncToAsyncAdapter` to `from ._async_backends import sync_to_async`, and `SyncToAsyncAdapter(sync_backend)` to `sync_to_async(sync_backend)`.
- `src/asebytes/_async_object_io.py:40-48` — same change.
- `src/asebytes/_async_io.py:44-52` — same change.

Update `src/asebytes/__init__.py`:
- Add `sync_to_async` to the imports from `._async_backends` (line 14-22).
- Add `SyncToAsyncReadAdapter`, `SyncToAsyncReadWriteAdapter`, `sync_to_async` to `__all__`.

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_sync_to_async_adapter.py -x -v`
Expected: PASS

**Step 6: Run full test suite to check for regressions**

Run: `uv run pytest tests/ -x -q`
Expected: All tests pass.

**Step 7: Commit**

```bash
git add src/asebytes/_async_backends.py src/asebytes/_async_blob_io.py \
  src/asebytes/_async_object_io.py src/asebytes/_async_io.py \
  src/asebytes/__init__.py tests/test_sync_to_async_adapter.py
git commit -m "fix: split SyncToAsyncAdapter into read-only and read-write variants"
```

---

### Task 2: Add `update()` to async facades

Sync facades have `update()`. Async facades don't.

**Files:**
- Modify: `src/asebytes/_async_blob_io.py`
- Modify: `src/asebytes/_async_object_io.py`
- Modify: `src/asebytes/_async_io.py`
- Test: `tests/test_async_facade_update.py` (new)

**Step 1: Write the failing test**

Create `tests/test_async_facade_update.py`:

```python
"""Tests for update() on async facades."""

from __future__ import annotations

import pytest
from typing import Any

from asebytes._backends import ReadBackend, ReadWriteBackend
from asebytes._async_backends import sync_to_async, AsyncReadWriteBackend
from asebytes._async_blob_io import AsyncBlobIO
from asebytes._async_object_io import AsyncObjectIO


class MemoryRW(ReadWriteBackend):
    def __init__(self, data=None):
        self._data = data or []

    def __len__(self):
        return len(self._data)

    def get(self, index, keys=None):
        row = self._data[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    def set(self, index, value):
        if index < len(self._data):
            self._data[index] = value
        elif index == len(self._data):
            self._data.append(value)
        else:
            raise IndexError(index)

    def delete(self, index):
        del self._data[index]

    def extend(self, values):
        self._data.extend(values)

    def insert(self, index, value):
        self._data.insert(index, value)


class MemoryRO(ReadBackend):
    def __init__(self):
        self._data = []

    def __len__(self):
        return 0

    def get(self, index, keys=None):
        raise IndexError(index)


@pytest.mark.asyncio
class TestAsyncBlobIOUpdate:
    async def test_update(self):
        backend = sync_to_async(MemoryRW([{b"a": b"1", b"b": b"2"}]))
        io = AsyncBlobIO(backend)
        await io.update(0, {b"a": b"99"})
        assert await io.get(0) == {b"a": b"99", b"b": b"2"}

    async def test_update_readonly_raises(self):
        backend = sync_to_async(MemoryRO())
        io = AsyncBlobIO(backend)
        with pytest.raises(TypeError, match="read-only"):
            await io.update(0, {b"a": b"1"})


@pytest.mark.asyncio
class TestAsyncObjectIOUpdate:
    async def test_update(self):
        backend = sync_to_async(MemoryRW([{"a": 1, "b": 2}]))
        io = AsyncObjectIO(backend)
        await io.update(0, {"a": 99})
        assert await io.get(0) == {"a": 99, "b": 2}

    async def test_update_readonly_raises(self):
        backend = sync_to_async(MemoryRO())
        io = AsyncObjectIO(backend)
        with pytest.raises(TypeError, match="read-only"):
            await io.update(0, {"a": 1})
```

Note: `AsyncASEIO.update()` will be tested with ase.Atoms, but for simplicity we test the namespace-aware version in a separate test or the existing test files. The pattern is the same.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_async_facade_update.py -x -v`
Expected: FAIL — `AttributeError: 'AsyncBlobIO' object has no attribute 'update'`

**Step 3: Write minimal implementation**

In `src/asebytes/_async_blob_io.py`, add after `reserve()` (around line 179):

```python
    async def update(self, index: int, data: dict[bytes, bytes]) -> None:
        """Partial update: merge *data* into existing row at *index*."""
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.update(index, data)
```

In `src/asebytes/_async_object_io.py`, add after `reserve()` (around line 183):

```python
    async def update(self, index: int, data: dict[str, Any]) -> None:
        """Partial update: merge *data* into existing row at *index*."""
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.update(index, data)
```

In `src/asebytes/_async_io.py`, add after `reserve()` (around line 194), mirroring the sync ASEIO namespace-aware signature:

```python
    _VALID_PREFIXES = ("arrays.", "info.", "calc.")
    _VALID_TOP_LEVEL = ("cell", "pbc", "constraints")

    def _validate_keys(self, data: dict[str, Any]) -> None:
        for key in data:
            if key in self._VALID_TOP_LEVEL:
                continue
            if any(key.startswith(p) for p in self._VALID_PREFIXES):
                continue
            raise ValueError(
                f"Invalid key {key!r}. Keys must start with "
                f"{', '.join(self._VALID_PREFIXES)} or be one of "
                f"{', '.join(self._VALID_TOP_LEVEL)}."
            )

    async def update(
        self,
        index: int,
        data: dict[str, Any] | None = None,
        *,
        info: dict[str, Any] | None = None,
        arrays: dict[str, Any] | None = None,
        calc: dict[str, Any] | None = None,
    ) -> None:
        """Update specific keys at index.

        Keys must follow the namespace convention: ``calc.*``, ``info.*``,
        ``arrays.*``, or top-level keys (``cell``, ``pbc``, ``constraints``).
        """
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")

        flat_data: dict[str, Any] = {}
        if data is not None:
            flat_data.update(data)
        if info:
            for k, v in info.items():
                flat_data[f"info.{k}"] = v
        if arrays:
            for k, v in arrays.items():
                flat_data[f"arrays.{k}"] = v
        if calc:
            for k, v in calc.items():
                flat_data[f"calc.{k}"] = v

        if not flat_data:
            return

        self._validate_keys(flat_data)
        await self._backend.update(index, flat_data)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_async_facade_update.py -x -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/asebytes/_async_blob_io.py src/asebytes/_async_object_io.py \
  src/asebytes/_async_io.py tests/test_async_facade_update.py
git commit -m "feat: add update() to AsyncBlobIO, AsyncObjectIO, AsyncASEIO"
```

---

### Task 3: Add `clear()` and `remove()` to sync facades

Async facades have `clear()` and `remove()`. Sync facades don't.

**Files:**
- Modify: `src/asebytes/_blob_io.py`
- Modify: `src/asebytes/_object_io.py`
- Modify: `src/asebytes/io.py`
- Test: `tests/test_sync_facade_clear_remove.py` (new)

**Step 1: Write the failing test**

Create `tests/test_sync_facade_clear_remove.py`:

```python
"""Tests for clear() and remove() on sync facades."""

from __future__ import annotations

import pytest
from typing import Any

from asebytes._backends import ReadBackend, ReadWriteBackend
from asebytes._blob_io import BlobIO
from asebytes._object_io import ObjectIO


class MemoryRW(ReadWriteBackend):
    def __init__(self, data=None):
        self._data = data or []

    def __len__(self):
        return len(self._data)

    def get(self, index, keys=None):
        row = self._data[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    def set(self, index, value):
        if index < len(self._data):
            self._data[index] = value
        elif index == len(self._data):
            self._data.append(value)
        else:
            raise IndexError(index)

    def delete(self, index):
        del self._data[index]

    def extend(self, values):
        self._data.extend(values)

    def insert(self, index, value):
        self._data.insert(index, value)


class MemoryRO(ReadBackend):
    def __init__(self):
        pass

    def __len__(self):
        return 0

    def get(self, index, keys=None):
        raise IndexError(index)


class TestBlobIOClearRemove:
    def test_clear(self):
        io = BlobIO(MemoryRW([{b"a": b"1"}, {b"a": b"2"}]))
        io.clear()
        assert len(io) == 0

    def test_clear_readonly_raises(self):
        io = BlobIO(MemoryRO())
        with pytest.raises(TypeError, match="read-only"):
            io.clear()

    def test_remove_raises_not_implemented(self):
        io = BlobIO(MemoryRW([]))
        with pytest.raises(NotImplementedError):
            io.remove()

    def test_remove_readonly_raises(self):
        io = BlobIO(MemoryRO())
        with pytest.raises(TypeError, match="read-only"):
            io.remove()


class TestObjectIOClearRemove:
    def test_clear(self):
        io = ObjectIO(MemoryRW([{"a": 1}, {"a": 2}]))
        io.clear()
        assert len(io) == 0

    def test_clear_readonly_raises(self):
        io = ObjectIO(MemoryRO())
        with pytest.raises(TypeError, match="read-only"):
            io.clear()

    def test_remove_raises_not_implemented(self):
        io = ObjectIO(MemoryRW([]))
        with pytest.raises(NotImplementedError):
            io.remove()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_sync_facade_clear_remove.py -x -v`
Expected: FAIL — `AttributeError: 'BlobIO' object has no attribute 'clear'`

**Step 3: Write minimal implementation**

Add to each of `BlobIO`, `ObjectIO`, and `ASEIO` (before `__len__`):

```python
    def clear(self) -> None:
        """Remove all rows but keep the container."""
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.clear()

    def remove(self) -> None:
        """Remove the entire container (backend-specific)."""
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.remove()
```

In `src/asebytes/_blob_io.py`: add before line 174 (`__len__`).
In `src/asebytes/_object_io.py`: add before line 189 (`__len__`).
In `src/asebytes/io.py`: add before line 244 (`__len__`).

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_sync_facade_clear_remove.py -x -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/asebytes/_blob_io.py src/asebytes/_object_io.py \
  src/asebytes/io.py tests/test_sync_facade_clear_remove.py
git commit -m "feat: add clear() and remove() to BlobIO, ObjectIO, ASEIO"
```

---

### Task 4: Fix BlobIO negative index normalization

`ObjectIO` and `ASEIO` normalize negative indices in `__getitem__`. `BlobIO` doesn't.

**Files:**
- Modify: `src/asebytes/_blob_io.py:114-115`
- Test: `tests/test_blob_negative_index.py` (new)

**Step 1: Write the failing test**

Create `tests/test_blob_negative_index.py`:

```python
"""Test BlobIO negative index handling."""

from __future__ import annotations

import pytest
from typing import Any

from asebytes._backends import ReadWriteBackend
from asebytes._blob_io import BlobIO


class MemoryRW(ReadWriteBackend):
    def __init__(self, data=None):
        self._data = data or []

    def __len__(self):
        return len(self._data)

    def get(self, index, keys=None):
        if index < 0 or index >= len(self._data):
            raise IndexError(index)
        row = self._data[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    def set(self, index, value):
        if index < len(self._data):
            self._data[index] = value
        elif index == len(self._data):
            self._data.append(value)
        else:
            raise IndexError(index)

    def delete(self, index):
        del self._data[index]

    def extend(self, values):
        self._data.extend(values)

    def insert(self, index, value):
        self._data.insert(index, value)


class TestBlobIONegativeIndex:
    def test_getitem_negative_one(self):
        io = BlobIO(MemoryRW([{b"a": b"1"}, {b"b": b"2"}, {b"c": b"3"}]))
        assert io[-1] == {b"c": b"3"}

    def test_getitem_negative_two(self):
        io = BlobIO(MemoryRW([{b"a": b"1"}, {b"b": b"2"}, {b"c": b"3"}]))
        assert io[-2] == {b"b": b"2"}

    def test_getitem_negative_out_of_bounds(self):
        io = BlobIO(MemoryRW([{b"a": b"1"}]))
        with pytest.raises(IndexError):
            io[-5]

    def test_getitem_list_negative(self):
        io = BlobIO(MemoryRW([{b"a": b"1"}, {b"b": b"2"}, {b"c": b"3"}]))
        view = io[[-1, -2]]
        assert view.to_list() == [{b"c": b"3"}, {b"b": b"2"}]

    def test_getitem_list_negative_out_of_bounds(self):
        io = BlobIO(MemoryRW([{b"a": b"1"}]))
        with pytest.raises(IndexError):
            io[[-5]]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_blob_negative_index.py -x -v`
Expected: FAIL — `IndexError: -1` (raw negative index passed to backend)

**Step 3: Write minimal implementation**

In `src/asebytes/_blob_io.py`, modify the `__getitem__` method at lines 114-115.

Change:
```python
        if isinstance(index, int):
            return self._backend.get(index)
```

To:
```python
        if isinstance(index, int):
            if index < 0:
                index += len(self)
            if index < 0:
                raise IndexError(index)
            return self._backend.get(index)
```

Also add negative index normalization for `list[int]` indices (around line 121-125).

Change:
```python
            if isinstance(index[0], int):
                return RowView(self, index)
```

To:
```python
            if isinstance(index[0], int):
                n = len(self)
                normalized = []
                for i in index:
                    idx = i + n if i < 0 else i
                    if idx < 0 or idx >= n:
                        raise IndexError(i)
                    normalized.append(idx)
                return RowView(self, normalized)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_blob_negative_index.py -x -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/asebytes/_blob_io.py tests/test_blob_negative_index.py
git commit -m "fix: normalize negative indices in BlobIO.__getitem__"
```

---

### Task 5: Add `drop()` to sync RowView and `_drop_keys` to ViewParent

`AsyncRowView` has `drop(keys)`. Sync `RowView` doesn't. The sync `ViewParent` protocol also lacks `_drop_keys`.

**Files:**
- Modify: `src/asebytes/_views.py:10-22` (ViewParent protocol) and `src/asebytes/_views.py:41-167` (RowView)
- Modify: `src/asebytes/_blob_io.py` — add `_drop_keys` method
- Modify: `src/asebytes/_object_io.py` — add `_drop_keys` method
- Modify: `src/asebytes/io.py` — add `_drop_keys` method
- Test: `tests/test_sync_rowview_drop.py` (new)

**Step 1: Write the failing test**

Create `tests/test_sync_rowview_drop.py`:

```python
"""Tests for RowView.drop() on sync facades."""

from __future__ import annotations

import pytest
from typing import Any

from asebytes._backends import ReadWriteBackend
from asebytes._blob_io import BlobIO
from asebytes._object_io import ObjectIO


class MemoryRW(ReadWriteBackend):
    def __init__(self, data=None):
        self._data = data or []

    def __len__(self):
        return len(self._data)

    def get(self, index, keys=None):
        row = self._data[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    def set(self, index, value):
        if index < len(self._data):
            self._data[index] = value
        elif index == len(self._data):
            self._data.append(value)
        else:
            raise IndexError(index)

    def delete(self, index):
        del self._data[index]

    def extend(self, values):
        self._data.extend(values)

    def insert(self, index, value):
        self._data.insert(index, value)


class TestObjectIORowViewDrop:
    def test_drop_on_slice(self):
        io = ObjectIO(MemoryRW([
            {"a": 1, "b": 2, "c": 3},
            {"a": 4, "b": 5, "c": 6},
            {"a": 7, "b": 8, "c": 9},
        ]))
        view = io[0:2]
        view.drop(["b", "c"])
        assert io.get(0) == {"a": 1}
        assert io.get(1) == {"a": 4}
        # Row 2 untouched
        assert io.get(2) == {"a": 7, "b": 8, "c": 9}

    def test_drop_on_list_indices(self):
        io = ObjectIO(MemoryRW([
            {"a": 1, "b": 2},
            {"a": 3, "b": 4},
            {"a": 5, "b": 6},
        ]))
        view = io[[0, 2]]
        view.drop(["b"])
        assert io.get(0) == {"a": 1}
        assert io.get(1) == {"a": 3, "b": 4}  # untouched
        assert io.get(2) == {"a": 5}


class TestBlobIORowViewDrop:
    def test_drop_on_slice(self):
        io = BlobIO(MemoryRW([
            {b"a": b"1", b"b": b"2"},
            {b"a": b"3", b"b": b"4"},
        ]))
        view = io[0:2]
        view.drop([b"b"])
        assert io.get(0) == {b"a": b"1"}
        assert io.get(1) == {b"a": b"3"}
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_sync_rowview_drop.py -x -v`
Expected: FAIL — `AttributeError: 'RowView' object has no attribute 'drop'`

**Step 3: Write minimal implementation**

1. Add `_drop_keys` to `ViewParent` protocol in `src/asebytes/_views.py` (after line 22):

```python
    def _drop_keys(self, keys: list, indices: list[int]) -> None: ...
```

2. Add `drop()` to `RowView` in `src/asebytes/_views.py` (after the `delete()` method, around line 164):

```python
    def drop(self, keys: list) -> None:
        """Remove specified keys from all rows in this view."""
        self._parent._drop_keys(keys, self._indices)
```

3. Add `_drop_keys` to each sync facade:

In `src/asebytes/_blob_io.py` (after `_delete_rows`, around line 88):

```python
    def _drop_keys(self, keys: list[bytes], indices: list[int]) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.drop_keys(keys, indices)
```

In `src/asebytes/_object_io.py` (after `_delete_rows`, around line 93):

```python
    def _drop_keys(self, keys: list[str], indices: list[int]) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.drop_keys(keys, indices)
```

In `src/asebytes/io.py` (after `_delete_rows`, around line 149):

```python
    def _drop_keys(self, keys: list[str], indices: list[int]) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.drop_keys(keys, indices)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_sync_rowview_drop.py -x -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/asebytes/_views.py src/asebytes/_blob_io.py \
  src/asebytes/_object_io.py src/asebytes/io.py \
  tests/test_sync_rowview_drop.py
git commit -m "feat: add drop() to sync RowView with _drop_keys on ViewParent"
```

---

### Task 6: Fix ColumnView type annotation for bytes keys

`ColumnView.__init__` annotates `keys` as `str | list[str]` but `BlobIO` passes `bytes | list[bytes]`.

**Files:**
- Modify: `src/asebytes/_views.py:185-189`

**Step 1: Write the failing test**

This is a type annotation fix. The runtime already works. We verify by confirming BlobIO column access works with bytes keys (should already pass):

Run: `uv run pytest tests/test_blob_column_access.py -x -v`
Expected: PASS (runtime works, just annotations wrong)

**Step 2: Fix the type annotation**

In `src/asebytes/_views.py`, change lines 185-189 of `ColumnView.__init__`:

```python
    def __init__(
        self,
        parent: ViewParent[Any],
        keys: str | bytes | list[str] | list[bytes],
        indices: range | list[int] | None = None,
    ):
```

**Step 3: Run full test suite**

Run: `uv run pytest tests/ -x -q`
Expected: All pass

**Step 4: Commit**

```bash
git add src/asebytes/_views.py
git commit -m "fix: ColumnView type annotation to accept bytes keys"
```

---

### Task 7: Consolidate `_DeferredSliceRowView` into `_async_views.py`

Two nearly identical `_DeferredSliceRowView` classes exist in `_async_object_io.py` and `_async_io.py`.

**Files:**
- Modify: `src/asebytes/_async_views.py` — add generic `_DeferredSliceRowView`
- Modify: `src/asebytes/_async_object_io.py` — delete local class, import from `_async_views`
- Modify: `src/asebytes/_async_io.py` — thin subclass only
- Modify: `src/asebytes/_async_blob_io.py` — update import

**Step 1: Move shared class to `_async_views.py`**

Add at the end of `src/asebytes/_async_views.py` (after existing `_DeferredSliceASEColumnView` class):

```python
class _DeferredSliceRowView(AsyncRowView[R]):
    """AsyncRowView that resolves a slice lazily via len().

    When __getitem__ receives a slice, we can't call len() synchronously
    on an async object. This subclass stores the raw slice and resolves
    it to concrete indices on first await / aiter.
    """

    def __init__(self, parent, slc: slice, *, column_view_cls=None):
        super().__init__(parent, [], contiguous=True, column_view_cls=column_view_cls)
        self._slice = slc
        self._resolved = False

    async def _ensure_resolved(self) -> None:
        if not self._resolved:
            n = await self._parent.len()
            self._indices = list(range(n))[self._slice]
            self._resolved = True

    def __getitem__(self, key):
        if isinstance(key, (str, bytes)):
            cv_cls = self._column_view_cls or AsyncColumnView
            if cv_cls is AsyncColumnView:
                return _DeferredSliceColumnView(self._parent, key, self._slice)
        if isinstance(key, list) and key and isinstance(key[0], (str, bytes)):
            cv_cls = self._column_view_cls or AsyncColumnView
            if cv_cls is AsyncColumnView:
                return _DeferredSliceColumnView(self._parent, key, self._slice)
        return super().__getitem__(key)

    def __len__(self) -> int:
        if not self._resolved:
            raise TypeError(
                "len() not available until slice is resolved. "
                "Use 'to_list()' or 'async for' first."
            )
        return len(self._indices)

    async def to_list(self) -> list[Any]:
        await self._ensure_resolved()
        return await super().to_list()

    async def __aiter__(self):
        await self._ensure_resolved()
        async for item in super().__aiter__():
            yield item

    async def chunked(self, chunk_size: int = 1000):
        await self._ensure_resolved()
        async for item in super().chunked(chunk_size):
            yield item

    async def delete(self) -> None:
        await self._ensure_resolved()
        await super().delete()

    async def set(self, data: list[Any]) -> None:
        await self._ensure_resolved()
        await super().set(data)

    async def update(self, data: dict) -> None:
        await self._ensure_resolved()
        await super().update(data)

    async def drop(self, keys: list) -> None:
        await self._ensure_resolved()
        await super().drop(keys)
```

**Step 2: Delete the class from `_async_object_io.py`**

Remove lines 205–274 (the entire `_DeferredSliceRowView` class) from `src/asebytes/_async_object_io.py`.

Add import at top:
```python
from ._async_views import _DeferredSliceRowView
```

(This is where `_async_blob_io.py` already imports it from, so that import at line 18 needs updating too.)

**Step 3: Replace the ASEIO version with a thin subclass**

In `src/asebytes/_async_io.py`, replace lines 297–369 (the full duplicate `_DeferredSliceRowView` and keep only the ASEIO-specific `__getitem__` override):

```python
class _ASEIODeferredSliceRowView(_DeferredSliceRowView[ase.Atoms | None]):
    """ASEIO variant that defers column access to _DeferredColumnFromSlice."""

    def __getitem__(self, key):
        if isinstance(key, str):
            return _DeferredColumnFromSlice(self, key)
        if isinstance(key, list) and key and isinstance(key[0], str):
            return _DeferredColumnFromSlice(self, key)
        if self._resolved:
            return super().__getitem__(key)
        raise TypeError(
            "Cannot sub-select by int/slice from unresolved slice. "
            "Use 'to_list()' or 'async for' first, or index by column key."
        )
```

And add the import:
```python
from ._async_views import _DeferredSliceRowView
```

Update the `__getitem__` in `AsyncASEIO` (line 142) to use `_ASEIODeferredSliceRowView`:
```python
            return _ASEIODeferredSliceRowView(self, index, column_view_cls=AsyncASEColumnView)
```

**Step 4: Update `_async_blob_io.py` import**

Change line 18:
```python
from ._async_object_io import _DeferredSliceRowView
```
To:
```python
from ._async_views import _DeferredSliceRowView
```

**Step 5: Run full test suite**

Run: `uv run pytest tests/ -x -q`
Expected: All pass (pure refactor, no behavior change).

**Step 6: Commit**

```bash
git add src/asebytes/_async_views.py src/asebytes/_async_object_io.py \
  src/asebytes/_async_io.py src/asebytes/_async_blob_io.py
git commit -m "refactor: consolidate _DeferredSliceRowView into _async_views.py"
```

---

### Task 8: Standardize `__iter__` patterns

`BlobIO` uses `for i in range(len(self)): yield self[i]`. `ObjectIO` and `ASEIO` use `while True / try-except IndexError`.

**Files:**
- Modify: `src/asebytes/_object_io.py:192-199`
- Modify: `src/asebytes/io.py:247-256`

**Step 1: Change ObjectIO `__iter__`**

In `src/asebytes/_object_io.py`, replace lines 192-199:

```python
    def __iter__(self) -> Iterator[dict[str, Any]]:
        for i in range(len(self)):
            yield self[i]
```

**Step 2: Change ASEIO `__iter__`**

In `src/asebytes/io.py`, replace lines 247-256:

```python
    def __iter__(self) -> Iterator[ase.Atoms]:
        for i in range(len(self)):
            yield self[i]
```

**Step 3: Run full test suite**

Run: `uv run pytest tests/ -x -q`
Expected: All pass.

**Step 4: Commit**

```bash
git add src/asebytes/_object_io.py src/asebytes/io.py
git commit -m "refactor: standardize __iter__ to range(len(self)) pattern"
```

---

### Task 9: Fix stale comments and delete scratch file

**Files:**
- Modify: `src/asebytes/h5md/_backend.py:222,405`
- Modify: `src/asebytes/zarr/_backend.py:107,224`
- Modify: `src/asebytes/hf/_backend.py:196`
- Modify: `tests/test_raw_protocols.py:4`
- Modify: `tests/test_blob_column_access.py:138`
- Modify: `tests/test_string_path_constructors.py:206`
- Delete: `async-api.py`

**Step 1: Fix stale comments in backends**

In `src/asebytes/h5md/_backend.py`:
- Line 222: `# ReadableBackend` → `# ReadBackend`
- Line 405: `# WritableBackend (append-only)` → `# ReadWriteBackend (append-only)`

In `src/asebytes/zarr/_backend.py`:
- Line 107: `# ReadableBackend` → `# ReadBackend`
- Line 224: `# WritableBackend (append-only)` → `# ReadWriteBackend (append-only)`

In `src/asebytes/hf/_backend.py`:
- Line 196: `# ── ReadableBackend interface` → `# ── ReadBackend interface`

**Step 2: Fix stale comments in tests**

In `tests/test_raw_protocols.py`:
- Line 4: `BlobIO and AsyncBytesIO delegate to.` → `BlobIO and AsyncBlobIO delegate to.`

In `tests/test_blob_column_access.py`:
- Line 138: `# ── AsyncBlobIO column access (migrated from AsyncBytesIO) ──` → `# ── AsyncBlobIO column access ──`

In `tests/test_string_path_constructors.py`:
- Line 206: `# ── Async: AsyncBlobIO from string path (migrated from AsyncBytesIO) ──` → `# ── Async: AsyncBlobIO from string path ──`

**Step 3: Delete scratch file**

```bash
rm async-api.py
```

**Step 4: Run full test suite**

Run: `uv run pytest tests/ -x -q`
Expected: All pass.

**Step 5: Commit**

```bash
git add -u src/asebytes/h5md/_backend.py src/asebytes/zarr/_backend.py \
  src/asebytes/hf/_backend.py tests/test_raw_protocols.py \
  tests/test_blob_column_access.py tests/test_string_path_constructors.py
git rm async-api.py
git commit -m "chore: fix stale comments and delete scratch file"
```

---

### Final Verification

Run the full test suite one last time:

```bash
uv run pytest tests/ -x -q
```

Expected: All tests pass.

Then grep for any remaining inconsistencies:

```bash
grep -rn "SyncToAsyncAdapter\b" src/ --include="*.py"  # Should only find alias
grep -rn "ReadableBackend\|WritableBackend\|AsyncBytesIO" src/ tests/ --include="*.py"  # Should find nothing
```
