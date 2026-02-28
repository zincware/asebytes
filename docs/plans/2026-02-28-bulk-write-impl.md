# Bulk Write Optimization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `update_many()` and `set_column()` to backend ABCs, wire views to use bulk paths for contiguous indices, and implement optimized overrides for all backends.

**Architecture:** Two new non-abstract methods on `ReadWriteBackend` / `AsyncReadWriteBackend` with loop-based defaults. Views detect contiguous indices and dispatch to new `_update_many` / `_set_column` / `_write_many` facade methods. Each backend optionally overrides for performance. TDD: tests first, then implementation.

**Tech Stack:** Python 3.10+, pytest, anyio, lmdb, redis, pymongo, zarr, h5py

---

### Task 1: Write failing tests for ABC default methods

**Files:**
- Create: `tests/test_bulk_write_abc.py`

**Step 1: Write the failing test**

```python
"""Tests for update_many / set_column ABC defaults on ReadWriteBackend."""
from __future__ import annotations
from typing import Any
from collections.abc import Iterator

import pytest

from asebytes._backends import ReadWriteBackend


class InMemoryBackend(ReadWriteBackend[str, Any]):
    """Minimal concrete backend for testing ABC defaults."""

    def __init__(self, rows: list[dict[str, Any] | None]):
        self._rows = list(rows)

    def __len__(self) -> int:
        return len(self._rows)

    def get(self, index, keys=None):
        row = self._rows[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    def set(self, index, value):
        self._rows[index] = value

    def delete(self, index):
        del self._rows[index]

    def extend(self, values):
        self._rows.extend(values)
        return len(self._rows)

    def insert(self, index, value):
        self._rows.insert(index, value)


@pytest.fixture
def backend():
    return InMemoryBackend([
        {"a": 1, "b": 10},
        {"a": 2, "b": 20},
        {"a": 3, "b": 30},
        {"a": 4, "b": 40},
        {"a": 5, "b": 50},
    ])


class TestUpdateMany:
    def test_basic(self, backend):
        backend.update_many(1, [{"a": 20}, {"a": 30}])
        assert backend._rows[0] == {"a": 1, "b": 10}   # untouched
        assert backend._rows[1] == {"a": 20, "b": 20}   # merged
        assert backend._rows[2] == {"a": 30, "b": 30}   # merged
        assert backend._rows[3] == {"a": 4, "b": 40}    # untouched

    def test_empty_data(self, backend):
        backend.update_many(0, [])
        assert backend._rows[0] == {"a": 1, "b": 10}

    def test_single_element(self, backend):
        backend.update_many(2, [{"a": 99}])
        assert backend._rows[2] == {"a": 99, "b": 30}

    def test_adds_new_keys(self, backend):
        backend.update_many(0, [{"c": 100}, {"c": 200}])
        assert backend._rows[0] == {"a": 1, "b": 10, "c": 100}
        assert backend._rows[1] == {"a": 2, "b": 20, "c": 200}

    def test_none_row_becomes_dict(self, backend):
        """update_many on a None placeholder creates a new dict."""
        backend._rows[0] = None
        backend.update_many(0, [{"a": 99}])
        assert backend._rows[0] == {"a": 99}


class TestSetColumn:
    def test_basic(self, backend):
        backend.set_column("a", 1, [20, 30, 40])
        assert backend._rows[0] == {"a": 1, "b": 10}   # untouched
        assert backend._rows[1] == {"a": 20, "b": 20}   # updated
        assert backend._rows[2] == {"a": 30, "b": 30}   # updated
        assert backend._rows[3] == {"a": 40, "b": 40}   # updated
        assert backend._rows[4] == {"a": 5, "b": 50}    # untouched

    def test_empty_values(self, backend):
        backend.set_column("a", 0, [])
        assert backend._rows[0] == {"a": 1, "b": 10}

    def test_single_value(self, backend):
        backend.set_column("a", 3, [99])
        assert backend._rows[3] == {"a": 99, "b": 40}

    def test_adds_new_column(self, backend):
        backend.set_column("c", 0, [100, 200, 300, 400, 500])
        assert backend._rows[0]["c"] == 100
        assert backend._rows[4]["c"] == 500

    def test_none_row_becomes_dict(self, backend):
        backend._rows[0] = None
        backend.set_column("a", 0, [99])
        assert backend._rows[0] == {"a": 99}
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_bulk_write_abc.py -v`
Expected: FAIL — `AttributeError: 'InMemoryBackend' object has no attribute 'update_many'`

**Step 3: Write minimal implementation**

In `src/asebytes/_backends.py`, add to `ReadWriteBackend` (after `set_many`, around line 137):

```python
def update_many(self, start: int, data: list[dict[K, V]]) -> None:
    """Partial-merge contiguous rows [start, start+len(data)).

    Override for backends where batch partial updates are cheaper than
    individual update() calls (e.g. single LMDB transaction, Redis pipeline).
    """
    for i, d in enumerate(data):
        self.update(start + i, d)

def set_column(self, key: K, start: int, values: list[V]) -> None:
    """Write a single key across contiguous rows [start, start+len(values)).

    Override for columnar backends (Zarr, H5MD) or network backends
    (Redis, MongoDB) where batch writes are cheaper.
    """
    for i, v in enumerate(values):
        self.update(start + i, {key: v})
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_bulk_write_abc.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add tests/test_bulk_write_abc.py src/asebytes/_backends.py
git commit -m "feat: add update_many/set_column to sync ReadWriteBackend ABC"
```

---

### Task 2: Add async ABC methods + adapter forwarding

**Files:**
- Create: `tests/test_bulk_write_async_abc.py`
- Modify: `src/asebytes/_async_backends.py:67-127` (AsyncReadWriteBackend)
- Modify: `src/asebytes/_async_backends.py:162-203` (SyncToAsyncReadWriteAdapter)

**Step 1: Write the failing test**

```python
"""Tests for async update_many / set_column ABC defaults + SyncToAsync adapter."""
from __future__ import annotations
from typing import Any

import pytest

from asebytes._async_backends import AsyncReadWriteBackend, SyncToAsyncReadWriteAdapter
from asebytes._backends import ReadWriteBackend


# Reuse the sync InMemoryBackend from test_bulk_write_abc
class InMemoryBackend(ReadWriteBackend[str, Any]):
    def __init__(self, rows):
        self._rows = list(rows)

    def __len__(self):
        return len(self._rows)

    def get(self, index, keys=None):
        row = self._rows[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    def set(self, index, value):
        self._rows[index] = value

    def delete(self, index):
        del self._rows[index]

    def extend(self, values):
        self._rows.extend(values)
        return len(self._rows)

    def insert(self, index, value):
        self._rows.insert(index, value)


class AsyncInMemoryBackend(AsyncReadWriteBackend[str, Any]):
    def __init__(self, rows):
        self._rows = list(rows)

    async def len(self):
        return len(self._rows)

    async def get(self, index, keys=None):
        row = self._rows[index]
        if row is None:
            return None
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    async def set(self, index, value):
        self._rows[index] = value

    async def delete(self, index):
        del self._rows[index]

    async def extend(self, values):
        self._rows.extend(values)
        return len(self._rows)

    async def insert(self, index, value):
        self._rows.insert(index, value)


ROWS = [
    {"a": 1, "b": 10},
    {"a": 2, "b": 20},
    {"a": 3, "b": 30},
    {"a": 4, "b": 40},
    {"a": 5, "b": 50},
]


class TestAsyncUpdateMany:
    @pytest.mark.anyio
    async def test_basic(self):
        be = AsyncInMemoryBackend([dict(r) for r in ROWS])
        await be.update_many(1, [{"a": 20}, {"a": 30}])
        assert be._rows[1] == {"a": 20, "b": 20}
        assert be._rows[2] == {"a": 30, "b": 30}

    @pytest.mark.anyio
    async def test_empty(self):
        be = AsyncInMemoryBackend([dict(r) for r in ROWS])
        await be.update_many(0, [])
        assert be._rows[0] == {"a": 1, "b": 10}


class TestAsyncSetColumn:
    @pytest.mark.anyio
    async def test_basic(self):
        be = AsyncInMemoryBackend([dict(r) for r in ROWS])
        await be.set_column("a", 1, [20, 30])
        assert be._rows[1] == {"a": 20, "b": 20}
        assert be._rows[2] == {"a": 30, "b": 30}

    @pytest.mark.anyio
    async def test_empty(self):
        be = AsyncInMemoryBackend([dict(r) for r in ROWS])
        await be.set_column("a", 0, [])
        assert be._rows[0] == {"a": 1, "b": 10}


class TestSyncToAsyncAdapter:
    @pytest.mark.anyio
    async def test_update_many_delegates(self):
        sync_be = InMemoryBackend([dict(r) for r in ROWS])
        adapter = SyncToAsyncReadWriteAdapter(sync_be)
        await adapter.update_many(0, [{"a": 10}, {"a": 20}])
        assert sync_be._rows[0] == {"a": 10, "b": 10}
        assert sync_be._rows[1] == {"a": 20, "b": 20}

    @pytest.mark.anyio
    async def test_set_column_delegates(self):
        sync_be = InMemoryBackend([dict(r) for r in ROWS])
        adapter = SyncToAsyncReadWriteAdapter(sync_be)
        await adapter.set_column("a", 2, [30, 40])
        assert sync_be._rows[2] == {"a": 30, "b": 30}
        assert sync_be._rows[3] == {"a": 40, "b": 40}
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_bulk_write_async_abc.py -v`
Expected: FAIL — `AttributeError`

**Step 3: Write implementation**

In `src/asebytes/_async_backends.py`, add to `AsyncReadWriteBackend` (after `set_many`, around line 116):

```python
async def update_many(self, start: int, data: list[dict[K, V]]) -> None:
    """Partial-merge contiguous rows [start, start+len(data)).

    Override for backends where batch partial updates are cheaper.
    """
    for i, d in enumerate(data):
        await self.update(start + i, d)

async def set_column(self, key: K, start: int, values: list[V]) -> None:
    """Write a single key across contiguous rows [start, start+len(values)).

    Override for columnar or network backends where batch writes are cheaper.
    """
    for i, v in enumerate(values):
        await self.update(start + i, {key: v})
```

In `SyncToAsyncReadWriteAdapter`, add (after `set_many`, around line 194):

```python
async def update_many(self, start, data):
    return await asyncio.to_thread(self._backend.update_many, start, data)

async def set_column(self, key, start, values):
    return await asyncio.to_thread(self._backend.set_column, key, start, values)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_bulk_write_async_abc.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add tests/test_bulk_write_async_abc.py src/asebytes/_async_backends.py
git commit -m "feat: add update_many/set_column to async ABC + SyncToAsync adapter"
```

---

### Task 3: Wire sync views (ColumnView + RowView) to use bulk paths

**Files:**
- Create: `tests/test_bulk_write_views.py`
- Modify: `src/asebytes/_views.py:10-23` (ViewParent protocol)
- Modify: `src/asebytes/_views.py:124-152` (RowView.set, RowView.update)
- Modify: `src/asebytes/_views.py:278-313` (ColumnView.set)

**Step 1: Write the failing tests**

```python
"""Tests that views dispatch to bulk methods for contiguous indices."""
from __future__ import annotations
from typing import Any
from unittest.mock import MagicMock

import pytest

from asebytes._views import ColumnView, RowView


class BulkMockParent:
    """Mock parent that tracks both individual and bulk calls."""

    def __init__(self, rows):
        self._rows = [dict(r) for r in rows]
        # Tracking
        self.update_row_calls = []
        self.update_many_calls = []
        self.set_column_calls = []
        self.write_row_calls = []
        self.write_many_calls = []

    def __len__(self):
        return len(self._rows)

    def _read_row(self, index, keys=None):
        return dict(self._rows[index])

    def _read_rows(self, indices, keys=None):
        return [dict(self._rows[i]) for i in indices]

    def _iter_rows(self, indices, keys=None):
        for i in indices:
            yield dict(self._rows[i])

    def _read_column(self, key, indices):
        return [self._rows[i][key] for i in indices]

    def _build_result(self, row):
        return row

    def _write_row(self, index, data):
        self.write_row_calls.append((index, data))
        self._rows[index] = data

    def _update_row(self, index, data):
        self.update_row_calls.append((index, data))
        self._rows[index].update(data)

    def _update_many(self, start, data):
        self.update_many_calls.append((start, data))
        for i, d in enumerate(data):
            self._rows[start + i].update(d)

    def _set_column(self, key, start, values):
        self.set_column_calls.append((key, start, values))
        for i, v in enumerate(values):
            self._rows[start + i][key] = v

    def _write_many(self, start, data):
        self.write_many_calls.append((start, data))
        for i, d in enumerate(data):
            self._rows[start + i] = d

    def _delete_row(self, index):
        del self._rows[index]

    def _delete_rows(self, start, stop):
        del self._rows[start:stop]

    def _drop_keys(self, keys, indices):
        pass


ROWS = [
    {"a": 1, "b": 10},
    {"a": 2, "b": 20},
    {"a": 3, "b": 30},
    {"a": 4, "b": 40},
    {"a": 5, "b": 50},
]


class TestColumnViewBulkDispatch:
    def test_single_key_contiguous_uses_set_column(self):
        parent = BulkMockParent(ROWS)
        view = ColumnView(parent, "a", list(range(5)))
        view[:3].set([10, 20, 30])
        # Should use _set_column, NOT _update_row
        assert len(parent.set_column_calls) == 1
        assert parent.set_column_calls[0] == ("a", 0, [10, 20, 30])
        assert len(parent.update_row_calls) == 0
        # Verify data correctness
        assert parent._rows[0]["a"] == 10
        assert parent._rows[2]["a"] == 30

    def test_multi_key_contiguous_uses_update_many(self):
        parent = BulkMockParent(ROWS)
        view = ColumnView(parent, ["a", "b"], list(range(5)))
        view[:2].set([[10, 100], [20, 200]])
        assert len(parent.update_many_calls) == 1
        assert parent.update_many_calls[0] == (0, [{"a": 10, "b": 100}, {"a": 20, "b": 200}])
        assert len(parent.update_row_calls) == 0

    def test_non_contiguous_falls_back_to_individual(self):
        parent = BulkMockParent(ROWS)
        view = ColumnView(parent, "a", [0, 2, 4])  # non-contiguous
        view.set([10, 30, 50])
        assert len(parent.set_column_calls) == 0
        assert len(parent.update_row_calls) == 3

    def test_empty_data_no_calls(self):
        parent = BulkMockParent(ROWS)
        view = ColumnView(parent, "a", [])
        view.set([])
        assert len(parent.set_column_calls) == 0
        assert len(parent.update_row_calls) == 0

    def test_single_element_contiguous(self):
        parent = BulkMockParent(ROWS)
        view = ColumnView(parent, "a", [3])
        view.set([99])
        # Single element is contiguous — should use bulk path
        assert len(parent.set_column_calls) == 1
        assert parent.set_column_calls[0] == ("a", 3, [99])


class TestRowViewBulkDispatch:
    def test_set_contiguous_uses_write_many(self):
        parent = BulkMockParent(ROWS)
        view = RowView(parent, list(range(3)))
        view.set([{"a": 10}, {"a": 20}, {"a": 30}])
        assert len(parent.write_many_calls) == 1
        assert parent.write_many_calls[0] == (0, [{"a": 10}, {"a": 20}, {"a": 30}])
        assert len(parent.write_row_calls) == 0

    def test_set_non_contiguous_falls_back(self):
        parent = BulkMockParent(ROWS)
        view = RowView(parent, [0, 2, 4])
        view.set([{"a": 10}, {"a": 30}, {"a": 50}])
        assert len(parent.write_many_calls) == 0
        assert len(parent.write_row_calls) == 3

    def test_update_contiguous_uses_update_many(self):
        parent = BulkMockParent(ROWS)
        view = RowView(parent, [1, 2, 3])
        view.update({"x": 999})
        assert len(parent.update_many_calls) == 1
        assert parent.update_many_calls[0] == (1, [{"x": 999}] * 3)
        assert len(parent.update_row_calls) == 0

    def test_update_non_contiguous_falls_back(self):
        parent = BulkMockParent(ROWS)
        view = RowView(parent, [0, 2])
        view.update({"x": 999})
        assert len(parent.update_many_calls) == 0
        assert len(parent.update_row_calls) == 2

    def test_set_empty_no_calls(self):
        parent = BulkMockParent(ROWS)
        view = RowView(parent, [])
        view.set([])
        assert len(parent.write_many_calls) == 0
        assert len(parent.write_row_calls) == 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_bulk_write_views.py -v`
Expected: FAIL — `AttributeError: 'BulkMockParent' object has no attribute '_update_many'` (or views don't call the bulk methods yet)

**Step 3: Write implementation**

First, add `_is_contiguous` helper to `_views.py` (top of file, after `_sub_select`):

```python
def _is_contiguous(indices: list[int]) -> bool:
    """Check if indices form a contiguous ascending range."""
    if len(indices) <= 1:
        return True
    for i in range(1, len(indices)):
        if indices[i] != indices[i - 1] + 1:
            return False
    return True
```

Then extend `ViewParent` protocol with 3 new methods:

```python
def _update_many(self, start: int, data: list[dict[str, Any]]) -> None: ...
def _set_column(self, key: str, start: int, values: list[Any]) -> None: ...
def _write_many(self, start: int, data: list[Any]) -> None: ...
```

Update `ColumnView.set()` (replace lines 295-313):

```python
if self._single:
    if _is_contiguous(indices):
        self._parent._set_column(self._keys[0], indices[0], data)
    else:
        for idx, value in zip(indices, data):
            self._parent._update_row(idx, {self._keys[0]: value})
else:
    n_keys = len(self._keys)
    # Validate all inner lengths first
    for row_values in data:
        if not isinstance(row_values, (list, tuple)):
            raise TypeError(
                f"Multi-key writes require list-of-lists. "
                f"Got {type(row_values).__name__} at position."
            )
        if len(row_values) != n_keys:
            raise ValueError(
                f"Inner length mismatch: got {len(row_values)} values, "
                f"expected {n_keys} keys."
            )
    if _is_contiguous(indices):
        dicts = [dict(zip(self._keys, row_values)) for row_values in data]
        self._parent._update_many(indices[0], dicts)
    else:
        for idx, row_values in zip(indices, data):
            self._parent._update_row(
                idx, dict(zip(self._keys, row_values))
            )
```

Update `RowView.set()` — replace the write loop (lines 142-143):

```python
if _is_contiguous(self._indices):
    self._parent._write_many(self._indices[0], data)
else:
    for idx, d in zip(self._indices, data):
        self._parent._write_row(idx, d)
```

Update `RowView.update()` — replace the update loop (lines 151-152):

```python
if _is_contiguous(self._indices):
    self._parent._update_many(self._indices[0], [data] * len(self._indices))
else:
    for idx in self._indices:
        self._parent._update_row(idx, data)
```

**Step 4: Run tests**

Run: `uv run pytest tests/test_bulk_write_views.py tests/test_column_writes.py tests/test_sync_row_writes.py -v`
Expected: `test_bulk_write_views.py` passes. Existing tests in `test_column_writes.py` and `test_sync_row_writes.py` will FAIL because MockParent classes don't have the new bulk methods.

**Step 5: Fix mock parents in existing tests**

Add fallback methods to `MockParent` in `test_column_writes.py` and any other test mock parents that act as ViewParent:

```python
def _update_many(self, start, data):
    for i, d in enumerate(data):
        self._rows[start + i].update(d)

def _set_column(self, key, start, values):
    for i, v in enumerate(values):
        self._rows[start + i][key] = v

def _write_many(self, start, data):
    for i, d in enumerate(data):
        self._rows[start + i] = d
```

Search all test files with `def _update_row` for mock parents that need updating:
- `tests/test_column_writes.py` — MockParent (line 23)
- `tests/test_sync_row_writes.py` — MockParent
- `tests/test_column_dimensionality.py` — MockParent
- `tests/test_column_int_index.py` — MockParent
- `tests/test_generic_key_views.py` — MockViewParent

**Step 6: Run full test suite**

Run: `uv run pytest tests/ -v --ignore=tests/test_benchmark_*.py -x`
Expected: All PASS

**Step 7: Commit**

```bash
git add src/asebytes/_views.py tests/test_bulk_write_views.py tests/test_column_writes.py tests/test_sync_row_writes.py tests/test_column_dimensionality.py tests/test_column_int_index.py tests/test_generic_key_views.py
git commit -m "feat: wire sync views to bulk write paths for contiguous indices"
```

---

### Task 4: Wire async views to use bulk paths

**Files:**
- Create: `tests/test_bulk_write_async_views.py`
- Modify: `src/asebytes/_async_views.py:22-36` (AsyncViewParent protocol)
- Modify: `src/asebytes/_async_views.py:215-232` (AsyncRowView.set, update)
- Modify: `src/asebytes/_async_views.py:433-468` (AsyncColumnView.set)

**Step 1: Write the failing tests**

```python
"""Tests that async views dispatch to bulk methods for contiguous indices."""
from __future__ import annotations
from typing import Any

import pytest

from asebytes._async_views import AsyncColumnView, AsyncRowView


class AsyncBulkMockParent:
    def __init__(self, rows):
        self._rows = [dict(r) for r in rows]
        self.update_row_calls = []
        self.update_many_calls = []
        self.set_column_calls = []
        self.write_row_calls = []
        self.write_many_calls = []

    def __len__(self):
        return len(self._rows)

    async def len(self):
        return len(self._rows)

    async def _read_row(self, index, keys=None):
        return dict(self._rows[index])

    async def _read_rows(self, indices, keys=None):
        return [dict(self._rows[i]) for i in indices]

    async def _read_column(self, key, indices):
        return [self._rows[i][key] for i in indices]

    async def _write_row(self, index, data):
        self.write_row_calls.append((index, data))
        self._rows[index] = data

    async def _update_row(self, index, data):
        self.update_row_calls.append((index, data))
        self._rows[index].update(data)

    async def _update_many(self, start, data):
        self.update_many_calls.append((start, data))
        for i, d in enumerate(data):
            self._rows[start + i].update(d)

    async def _set_column(self, key, start, values):
        self.set_column_calls.append((key, start, values))
        for i, v in enumerate(values):
            self._rows[start + i][key] = v

    async def _write_many(self, start, data):
        self.write_many_calls.append((start, data))
        for i, d in enumerate(data):
            self._rows[start + i] = d

    async def _delete_row(self, index):
        del self._rows[index]

    async def _delete_rows(self, start, stop):
        del self._rows[start:stop]

    async def _drop_keys(self, keys, indices):
        pass

    async def _keys(self, index):
        return list(self._rows[index].keys())

    def _build_result(self, row):
        return row


ROWS = [
    {"a": 1, "b": 10},
    {"a": 2, "b": 20},
    {"a": 3, "b": 30},
    {"a": 4, "b": 40},
    {"a": 5, "b": 50},
]


class TestAsyncColumnViewBulkDispatch:
    @pytest.mark.anyio
    async def test_single_key_contiguous_uses_set_column(self):
        parent = AsyncBulkMockParent(ROWS)
        view = AsyncColumnView(parent, "a", list(range(5)))
        await view[:3].set([10, 20, 30])
        assert len(parent.set_column_calls) == 1
        assert parent.set_column_calls[0] == ("a", 0, [10, 20, 30])
        assert len(parent.update_row_calls) == 0

    @pytest.mark.anyio
    async def test_multi_key_contiguous_uses_update_many(self):
        parent = AsyncBulkMockParent(ROWS)
        view = AsyncColumnView(parent, ["a", "b"], list(range(5)))
        await view[:2].set([[10, 100], [20, 200]])
        assert len(parent.update_many_calls) == 1
        assert len(parent.update_row_calls) == 0

    @pytest.mark.anyio
    async def test_non_contiguous_falls_back(self):
        parent = AsyncBulkMockParent(ROWS)
        view = AsyncColumnView(parent, "a", [0, 2, 4])
        await view.set([10, 30, 50])
        assert len(parent.set_column_calls) == 0
        assert len(parent.update_row_calls) == 3


class TestAsyncRowViewBulkDispatch:
    @pytest.mark.anyio
    async def test_set_contiguous_uses_write_many(self):
        parent = AsyncBulkMockParent(ROWS)
        view = AsyncRowView(parent, [0, 1, 2])
        await view.set([{"a": 10}, {"a": 20}, {"a": 30}])
        assert len(parent.write_many_calls) == 1
        assert len(parent.write_row_calls) == 0

    @pytest.mark.anyio
    async def test_update_contiguous_uses_update_many(self):
        parent = AsyncBulkMockParent(ROWS)
        view = AsyncRowView(parent, [1, 2, 3])
        await view.update({"x": 999})
        assert len(parent.update_many_calls) == 1
        assert len(parent.update_row_calls) == 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_bulk_write_async_views.py -v`
Expected: FAIL

**Step 3: Write implementation**

Apply the same pattern as sync views to `_async_views.py`:

1. Import `_is_contiguous` (already exists in the file at line 55).
2. Add to `AsyncViewParent` protocol:
   ```python
   async def _update_many(self, start: int, data: list[dict[str, Any]]) -> None: ...
   async def _set_column(self, key: str, start: int, values: list[Any]) -> None: ...
   async def _write_many(self, start: int, data: list[Any]) -> None: ...
   ```
3. Update `AsyncRowView.set()`, `AsyncRowView.update()`, and `AsyncColumnView.set()` with the same contiguity-check + dispatch logic, using `await` for all calls.

Also fix async mock parents in existing tests:
- `tests/test_column_writes.py` — AsyncMockParent
- `tests/test_column_int_index.py` — AsyncMockParent
- `tests/test_generic_key_views.py` — AsyncMockViewParent
- `tests/test_single_row_subscript.py` — MockAsyncParent
- `tests/test_async_views.py` — MockAsyncParent

**Step 4: Run full test suite**

Run: `uv run pytest tests/ -v --ignore=tests/test_benchmark_*.py -x`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/asebytes/_async_views.py tests/test_bulk_write_async_views.py tests/test_column_writes.py tests/test_column_int_index.py tests/test_generic_key_views.py tests/test_single_row_subscript.py tests/test_async_views.py
git commit -m "feat: wire async views to bulk write paths for contiguous indices"
```

---

### Task 5: Add facade delegation methods (all 6 facades)

**Files:**
- Modify: `src/asebytes/_object_io.py:79-82` (ObjectIO — add _update_many, _set_column, _write_many)
- Modify: `src/asebytes/_blob_io.py:78-81` (BlobIO — same)
- Modify: `src/asebytes/io.py:135-138` (ASEIO — same)
- Modify: `src/asebytes/_async_object_io.py:98-101` (AsyncObjectIO — async same)
- Modify: `src/asebytes/_async_blob_io.py:97-100` (AsyncBlobIO — async same)
- Modify: `src/asebytes/_async_io.py:102-105` (AsyncASEIO — async same)

**Step 1: Write implementation**

For each sync facade (ObjectIO, BlobIO, ASEIO), add after `_update_row`:

```python
def _update_many(self, start: int, data: list[dict[str, Any]]) -> None:
    if not isinstance(self._backend, ReadWriteBackend):
        raise TypeError("Backend is read-only")
    self._backend.update_many(start, data)

def _set_column(self, key: str, start: int, values: list[Any]) -> None:
    if not isinstance(self._backend, ReadWriteBackend):
        raise TypeError("Backend is read-only")
    self._backend.set_column(key, start, values)

def _write_many(self, start: int, data: list[Any]) -> None:
    if not isinstance(self._backend, ReadWriteBackend):
        raise TypeError("Backend is read-only")
    self._backend.set_many(start, data)
```

For each async facade (AsyncObjectIO, AsyncBlobIO, AsyncASEIO), add after `_update_row`:

```python
async def _update_many(self, start: int, data: list[dict[str, Any]]) -> None:
    if not isinstance(self._backend, AsyncReadWriteBackend):
        raise TypeError("Backend is read-only")
    await self._backend.update_many(start, data)

async def _set_column(self, key: str, start: int, values: list[Any]) -> None:
    if not isinstance(self._backend, AsyncReadWriteBackend):
        raise TypeError("Backend is read-only")
    await self._backend.set_column(key, start, values)

async def _write_many(self, start: int, data: list[Any]) -> None:
    if not isinstance(self._backend, AsyncReadWriteBackend):
        raise TypeError("Backend is read-only")
    await self._backend.set_many(start, data)
```

**Note for BlobIO:** key types are `bytes`, not `str`. Adjust type hints accordingly.

**Step 2: Run full test suite**

Run: `uv run pytest tests/ -v --ignore=tests/test_benchmark_*.py -x`
Expected: All PASS

**Step 3: Commit**

```bash
git add src/asebytes/_object_io.py src/asebytes/_blob_io.py src/asebytes/io.py src/asebytes/_async_object_io.py src/asebytes/_async_blob_io.py src/asebytes/_async_io.py
git commit -m "feat: add bulk write delegation to all 6 facades"
```

---

### Task 6: Add adapter forwarding (BlobToObject, ObjectToBlob)

**Files:**
- Modify: `src/asebytes/_adapters.py:96-148` (BlobToObjectReadWriteAdapter)
- Modify: `src/asebytes/_adapters.py:208-243` (ObjectToBlobReadWriteAdapter)

**Step 1: Write the failing test**

```python
# Add to tests/test_bulk_write_abc.py or a new test_bulk_write_adapters.py

from asebytes._adapters import BlobToObjectReadWriteAdapter, ObjectToBlobReadWriteAdapter

class TestBlobToObjectAdapterBulk:
    def test_update_many_serializes(self):
        # Create a blob backend, wrap with adapter, call update_many
        ...

    def test_set_column_serializes(self):
        ...
```

**Step 2: Write implementation**

In `BlobToObjectReadWriteAdapter`, add after `update()` (line 131):

```python
def update_many(self, start: int, data: list[dict[str, Any]]) -> None:
    self._store.update_many(start, [_serialize_row(d) for d in data])

def set_column(self, key: str, start: int, values: list[Any]) -> None:
    self._store.set_column(key.encode(), start, [msgpack.packb(v, default=m.encode) for v in values])
```

In `ObjectToBlobReadWriteAdapter`, add after `update()` (line 243):

```python
def update_many(self, start: int, data: list[dict[bytes, bytes]]) -> None:
    self._store.update_many(start, [_deserialize_row(d) for d in data])

def set_column(self, key: bytes, start: int, values: list[bytes]) -> None:
    self._store.set_column(key.decode(), start, [msgpack.unpackb(v, object_hook=m.decode) for v in values])
```

**Step 3: Run tests and commit**

Run: `uv run pytest tests/ -v --ignore=tests/test_benchmark_*.py -x`

```bash
git add src/asebytes/_adapters.py tests/
git commit -m "feat: add bulk write forwarding to adapter classes"
```

---

### Task 7: LMDB backend override

**Files:**
- Modify: `src/asebytes/lmdb/_blob_backend.py`

**Step 1: Write the failing test**

Add to existing LMDB integration tests or create `tests/test_bulk_write_lmdb.py`:

```python
"""Test LMDB optimized update_many / set_column."""
import pytest
from asebytes._object_io import ObjectIO


@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "test.lmdb")
    io = ObjectIO(path)
    io.extend([{"a": 1, "b": 10}, {"a": 2, "b": 20}, {"a": 3, "b": 30}])
    return io


class TestLMDBUpdateMany:
    def test_basic(self, db):
        db._backend.update_many(0, [{"a": 10}, {"a": 20}])
        assert db[0]["a"] == 10
        assert db[1]["a"] == 20
        assert db[0]["b"] == 10  # untouched

    def test_empty(self, db):
        db._backend.update_many(0, [])
        assert db[0]["a"] == 1


class TestLMDBSetColumn:
    def test_basic(self, db):
        db._backend.set_column("a", 0, [10, 20, 30])
        assert db[0]["a"] == 10
        assert db[2]["a"] == 30
        assert db[0]["b"] == 10  # untouched

    def test_new_column(self, db):
        db._backend.set_column("c", 0, [100, 200, 300])
        assert db[0]["c"] == 100
        assert db[2]["c"] == 300
```

Note: these tests pass with the default implementation. The optimization is about using a single transaction.

**Step 2: Write implementation**

Add to `LMDBBlobBackend`:

```python
def update_many(self, start: int, data: list[dict[bytes, bytes]]) -> None:
    if not data:
        return
    with self.env.begin(write=True) as txn:
        self._ensure_cache(txn)
        all_items = []
        new_fields = set()
        for i, row_data in enumerate(data):
            if not row_data:
                continue
            sort_key = self._resolve_sort_key(start + i)
            sort_key_str = str(sort_key).encode()
            prefix = self.prefix + sort_key_str + b"-"
            for field_key, value in row_data.items():
                all_items.append((prefix + field_key, value))
            new_fields.update(row_data.keys())
        if all_items:
            cursor = txn.cursor()
            cursor.putmulti(all_items, dupdata=False, overwrite=True)
        if self._merge_schema(new_fields):
            self._save_schema(txn)
    self._invalidate_cache()

def set_column(self, key: bytes, start: int, values: list[bytes]) -> None:
    if not values:
        return
    with self.env.begin(write=True) as txn:
        self._ensure_cache(txn)
        all_items = []
        for i, value in enumerate(values):
            sort_key = self._resolve_sort_key(start + i)
            sort_key_str = str(sort_key).encode()
            all_items.append((self.prefix + sort_key_str + b"-" + key, value))
        if all_items:
            cursor = txn.cursor()
            cursor.putmulti(all_items, dupdata=False, overwrite=True)
        if self._merge_schema({key}):
            self._save_schema(txn)
    self._invalidate_cache()
```

**Step 3: Run tests and commit**

Run: `uv run pytest tests/test_bulk_write_lmdb.py tests/ -v --ignore=tests/test_benchmark_*.py -x`

```bash
git add src/asebytes/lmdb/_blob_backend.py tests/test_bulk_write_lmdb.py
git commit -m "perf: LMDB single-transaction update_many/set_column"
```

---

### Task 8: Redis backend overrides (sync + async)

**Files:**
- Modify: `src/asebytes/redis/_backend.py` (RedisBlobBackend)
- Modify: `src/asebytes/redis/_async_backend.py` (AsyncRedisBlobBackend)

**Step 1: Write implementation**

For `RedisBlobBackend`:

```python
def update_many(self, start: int, data: list[dict[bytes, bytes]]) -> None:
    if not data:
        return
    indices = list(range(start, start + len(data)))
    sks = self._resolve_indices(indices)
    pipe = self._r.pipeline()
    for sk, row_data in zip(sks, data):
        if row_data:
            pipe.hset(self._row_key(sk), mapping=row_data)
    pipe.execute()

def set_column(self, key: bytes, start: int, values: list[bytes]) -> None:
    if not values:
        return
    indices = list(range(start, start + len(values)))
    sks = self._resolve_indices(indices)
    pipe = self._r.pipeline()
    for sk, value in zip(sks, values):
        pipe.hset(self._row_key(sk), key, value)
    pipe.execute()
```

For `AsyncRedisBlobBackend`:

```python
async def update_many(self, start: int, data: list[dict[bytes, bytes]]) -> None:
    if not data:
        return
    indices = list(range(start, start + len(data)))
    sks = await self._resolve_indices(indices)
    pipe = self._r.pipeline(transaction=False)
    for sk, row_data in zip(sks, data):
        if row_data:
            pipe.hset(self._row_key(sk), mapping=row_data)
    await pipe.execute()

async def set_column(self, key: bytes, start: int, values: list[bytes]) -> None:
    if not values:
        return
    indices = list(range(start, start + len(values)))
    sks = await self._resolve_indices(indices)
    pipe = self._r.pipeline(transaction=False)
    for sk, value in zip(sks, values):
        pipe.hset(self._row_key(sk), key, value)
    await pipe.execute()
```

**Step 2: Run tests and commit**

Run: `uv run pytest tests/ -v --ignore=tests/test_benchmark_*.py -x -k "redis or bulk"`

```bash
git add src/asebytes/redis/_backend.py src/asebytes/redis/_async_backend.py
git commit -m "perf: Redis pipelined update_many/set_column (sync + async)"
```

---

### Task 9: MongoDB backend overrides (sync + async)

**Files:**
- Modify: `src/asebytes/mongodb/_backend.py` (MongoObjectBackend)
- Modify: `src/asebytes/mongodb/_async_backend.py` (AsyncMongoObjectBackend)

**Step 1: Write implementation**

For `MongoObjectBackend`:

```python
def update_many(self, start: int, data: list[dict[str, Any]]) -> None:
    if not data:
        return
    from pymongo import UpdateOne
    self._ensure_cache()
    ops = []
    for i, row_data in enumerate(data):
        if not row_data:
            continue
        sk = self._resolve_sort_key(start + i)
        update_fields = {f"data.{k}": _bson_safe(v) for k, v in row_data.items()}
        ops.append(UpdateOne({"_id": sk}, {"$set": update_fields}))
    if ops:
        self._col.bulk_write(ops, ordered=False)

def set_column(self, key: str, start: int, values: list[Any]) -> None:
    if not values:
        return
    from pymongo import UpdateOne
    self._ensure_cache()
    ops = []
    for i, value in enumerate(values):
        sk = self._resolve_sort_key(start + i)
        ops.append(UpdateOne({"_id": sk}, {"$set": {f"data.{key}": _bson_safe(value)}}))
    if ops:
        self._col.bulk_write(ops, ordered=False)
```

For `AsyncMongoObjectBackend`:

```python
async def update_many(self, start: int, data: list[dict[str, Any]]) -> None:
    if not data:
        return
    from pymongo import UpdateOne
    await self._ensure_cache()
    ops = []
    for i, row_data in enumerate(data):
        if not row_data:
            continue
        sk = self._resolve_sort_key(start + i)
        update_fields = {f"data.{k}": _bson_safe(v) for k, v in row_data.items()}
        ops.append(UpdateOne({"_id": sk}, {"$set": update_fields}))
    if ops:
        await self._col.bulk_write(ops, ordered=False)

async def set_column(self, key: str, start: int, values: list[Any]) -> None:
    if not values:
        return
    from pymongo import UpdateOne
    await self._ensure_cache()
    ops = []
    for i, value in enumerate(values):
        sk = self._resolve_sort_key(start + i)
        ops.append(UpdateOne({"_id": sk}, {"$set": {f"data.{key}": _bson_safe(value)}}))
    if ops:
        await self._col.bulk_write(ops, ordered=False)
```

**Step 2: Run tests and commit**

```bash
git add src/asebytes/mongodb/_backend.py src/asebytes/mongodb/_async_backend.py
git commit -m "perf: MongoDB bulk_write update_many/set_column (sync + async)"
```

---

### Task 10: Zarr backend override

**Files:**
- Modify: `src/asebytes/zarr/_backend.py`

**Step 1: Write implementation**

```python
def set_column(self, key: str, start: int, values: list[Any]) -> None:
    if not values:
        return
    if key not in self._col_cache:
        # New column — need to create it; fall back to base
        for i, v in enumerate(values):
            self.update(start + i, {key: v})
        return
    import numpy as np
    arr = self._col_cache[key]
    np_values = np.array(values)
    arr[start:start + len(values)] = np_values

def update_many(self, start: int, data: list[dict[str, Any]]) -> None:
    if not data:
        return
    import numpy as np
    # Group by key for vectorized writes
    from collections import defaultdict
    columns: dict[str, list[tuple[int, Any]]] = defaultdict(list)
    for i, row_data in enumerate(data):
        for key, value in row_data.items():
            columns[key].append((i, value))
    for key, pairs in columns.items():
        if key not in self._col_cache:
            # New column — fall back to per-row
            for offset, value in pairs:
                self.update(start + offset, {key: value})
            continue
        arr = self._col_cache[key]
        # Check if indices are contiguous within this column
        offsets = [p[0] for p in pairs]
        vals = [p[1] for p in pairs]
        if len(offsets) == len(data) and offsets == list(range(len(data))):
            # All rows have this key — use slice write
            arr[start:start + len(vals)] = np.array(vals)
        else:
            # Sparse — use fancy indexing
            indices = [start + o for o in offsets]
            for idx, val in zip(indices, vals):
                arr[idx] = val
```

**Step 2: Run tests and commit**

```bash
git add src/asebytes/zarr/_backend.py
git commit -m "perf: Zarr vectorized set_column/update_many"
```

---

### Task 11: H5MD backend override

**Files:**
- Modify: `src/asebytes/h5md/_backend.py`

**Step 1: Write implementation**

```python
def set_column(self, key: str, start: int, values: list[Any]) -> None:
    if not values:
        return
    import numpy as np
    h5_path = self._find_dataset_path(key)
    if h5_path is None:
        # Unknown column — fall back to base
        for i, v in enumerate(values):
            self.update(start + i, {key: v})
        return
    ds = self._file[h5_path]["value"]
    np_values = np.array(values)
    ds[start:start + len(values)] = np_values

def update_many(self, start: int, data: list[dict[str, Any]]) -> None:
    if not data:
        return
    import numpy as np
    from collections import defaultdict
    columns: dict[str, list[tuple[int, Any]]] = defaultdict(list)
    for i, row_data in enumerate(data):
        for key, value in row_data.items():
            columns[key].append((i, value))
    for key, pairs in columns.items():
        h5_path = self._find_dataset_path(key)
        if h5_path is None:
            for offset, value in pairs:
                self.update(start + offset, {key: value})
            continue
        ds = self._file[h5_path]["value"]
        offsets = [p[0] for p in pairs]
        vals = [p[1] for p in pairs]
        if len(offsets) == len(data) and offsets == list(range(len(data))):
            ds[start:start + len(vals)] = np.array(vals)
        else:
            for offset, val in zip(offsets, vals):
                ds[start + offset] = val
```

**Step 2: Run tests and commit**

```bash
git add src/asebytes/h5md/_backend.py
git commit -m "perf: H5MD vectorized set_column/update_many"
```

---

### Task 12: Run full test suite + verify existing tests pass

**Step 1: Run all tests**

```bash
uv run pytest tests/ -v --ignore=tests/test_benchmark_*.py -x
```

Expected: All PASS — no regressions.

**Step 2: Run existing column write and row write tests specifically**

```bash
uv run pytest tests/test_column_writes.py tests/test_sync_row_writes.py tests/test_column_dimensionality.py tests/test_column_int_index.py tests/test_generic_key_views.py tests/test_async_views.py tests/test_single_row_subscript.py -v
```

Expected: All PASS

**Step 3: Final commit if any fixups needed**

```bash
git add -u
git commit -m "fix: test fixups for bulk write integration"
```
