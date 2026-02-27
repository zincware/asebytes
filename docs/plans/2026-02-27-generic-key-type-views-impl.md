# Generic Key Type (`K`) for Views — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the view layer generic over key type `K` so BlobIO uses `bytes` natively and ObjectIO uses `str` natively, eliminating bytes↔str decoding in BlobIO.

**Architecture:** Add `K = TypeVar("K", str, bytes)` to all view classes. Update protocols (`ViewParent`, `AsyncViewParent`) to parameterize key arguments as `K`. Remove encode/decode bridging in BlobIO/AsyncBlobIO/AsyncBytesIO internal methods. Update all IO class `__getitem__` overloads.

**Tech Stack:** Python typing (TypeVar, Generic, Protocol), pytest, anyio

---

## Phase 1: Sync views — add `K` and support `bytes` keys

### Task 1: Write failing tests for `RowView` with bytes keys

**Files:**
- Create: `tests/test_generic_key_views.py`

**Step 1: Write the failing test**

```python
"""Tests for generic K type in RowView / ColumnView.

RowView[R, K] and ColumnView[K] should accept the parent's native key type.
BlobIO uses K=bytes, ObjectIO uses K=str.
"""
from __future__ import annotations
from typing import Any, Iterator

import pytest
from asebytes._views import ColumnView, RowView


class BytesMockParent:
    """Mock parent using bytes keys (like BlobIO)."""

    def __init__(self, rows: list[dict[bytes, bytes]]):
        self._rows = rows

    def __len__(self):
        return len(self._rows)

    def _read_row(self, index, keys=None):
        row = self._rows[index]
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    def _read_rows(self, indices, keys=None):
        return [self._read_row(i, keys) for i in indices]

    def _iter_rows(self, indices, keys=None):
        for i in indices:
            yield self._read_row(i, keys)

    def _read_column(self, key, indices):
        return [self._rows[i][key] for i in indices]

    def _build_result(self, row):
        return row

    def _write_row(self, index, data):
        self._rows[index] = data

    def _update_row(self, index, data):
        self._rows[index].update(data)

    def _delete_row(self, index):
        del self._rows[index]

    def _delete_rows(self, start, stop):
        for i in range(stop - 1, start - 1, -1):
            del self._rows[i]


@pytest.fixture
def brows():
    return [
        {b"name": b"alice", b"age": b"30"},
        {b"name": b"bob", b"age": b"25"},
        {b"name": b"carol", b"age": b"35"},
    ]


class TestRowViewBytesKey:
    """RowView with bytes-keyed parent should accept bytes column keys."""

    def test_bytes_key_returns_column_view(self, brows):
        parent = BytesMockParent(brows)
        rv = RowView(parent, range(3))
        cv = rv[b"name"]
        assert isinstance(cv, ColumnView)

    def test_list_bytes_key_returns_column_view(self, brows):
        parent = BytesMockParent(brows)
        rv = RowView(parent, range(3))
        cv = rv[[b"name", b"age"]]
        assert isinstance(cv, ColumnView)

    def test_bytes_column_to_list(self, brows):
        parent = BytesMockParent(brows)
        rv = RowView(parent, range(3))
        result = rv[b"name"].to_list()
        assert result == [b"alice", b"bob", b"carol"]

    def test_bytes_column_int_index(self, brows):
        parent = BytesMockParent(brows)
        rv = RowView(parent, range(3))
        result = rv[b"name"][0]
        assert result == b"alice"

    def test_multi_bytes_column_to_list(self, brows):
        parent = BytesMockParent(brows)
        rv = RowView(parent, range(3))
        result = rv[[b"name", b"age"]].to_list()
        assert result == [[b"alice", b"30"], [b"bob", b"25"], [b"carol", b"35"]]


class TestColumnViewBytesKey:
    """ColumnView with bytes keys should work end-to-end."""

    def test_single_bytes_key(self, brows):
        parent = BytesMockParent(brows)
        cv = ColumnView(parent, b"name", range(3))
        assert cv.to_list() == [b"alice", b"bob", b"carol"]

    def test_multi_bytes_keys(self, brows):
        parent = BytesMockParent(brows)
        cv = ColumnView(parent, [b"name", b"age"], range(3))
        result = cv.to_list()
        assert result == [[b"alice", b"30"], [b"bob", b"25"], [b"carol", b"35"]]

    def test_to_dict_bytes_keys(self, brows):
        parent = BytesMockParent(brows)
        cv = ColumnView(parent, [b"name", b"age"], range(3))
        result = cv.to_dict()
        assert result == {b"name": [b"alice", b"bob", b"carol"], b"age": [b"30", b"25", b"35"]}

    def test_bytes_key_set(self, brows):
        parent = BytesMockParent(brows)
        cv = ColumnView(parent, b"name", range(3))
        cv.set([b"x", b"y", b"z"])
        assert parent._rows[0][b"name"] == b"x"
        assert parent._rows[2][b"name"] == b"z"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_generic_key_views.py -v`
Expected: FAIL — `RowView.__getitem__` raises `TypeError: Unsupported key type: <class 'bytes'>` and `ColumnView.__init__` doesn't accept `bytes` for `keys` parameter.

### Task 2: Make sync views accept bytes keys

**Files:**
- Modify: `src/asebytes/_views.py`

**Step 3: Update `_views.py` to add `K` TypeVar and accept bytes keys**

Changes to `_views.py`:

1. Add `K = TypeVar("K", str, bytes)` after existing `R` TypeVar.

2. Update `ViewParent` protocol:
```python
class ViewParent(Protocol[R, K]):
    def __len__(self) -> int: ...
    def _read_row(self, index: int, keys: list[K] | None = None) -> dict[K, Any]: ...
    def _read_rows(self, indices: list[int], keys: list[K] | None = None) -> list[dict[K, Any]]: ...
    def _iter_rows(self, indices: list[int], keys: list[K] | None = None) -> Iterator[dict[K, Any]]: ...
    def _read_column(self, key: K, indices: list[int]) -> list[Any]: ...
    def _build_result(self, row: dict[K, Any]) -> R: ...
    def _write_row(self, index: int, data: Any) -> None: ...
    def _update_row(self, index: int, data: dict[K, Any]) -> None: ...
    def _delete_row(self, index: int) -> None: ...
    def _delete_rows(self, start: int, stop: int) -> None: ...
```

3. Update `RowView`:
```python
class RowView(Generic[R, K]):
```
- Change `__init__` parent type: `ViewParent[R, K]`
- Add `bytes` to `__getitem__` isinstance checks alongside `str`:
```python
if isinstance(key, (str, bytes)):
    return self._column_view_cls(self._parent, key, self._indices)
```
- In the list branch, add `isinstance(key[0], bytes)`:
```python
if isinstance(key[0], (str, bytes)):
    return self._column_view_cls(self._parent, key, self._indices)
```
- Update overloads to add `bytes` and `list[bytes]`

4. Update `ColumnView`:
- Change `__init__` `keys` parameter type from `str | list[str]` to `str | bytes | list[str] | list[bytes]`
- Change `_single` detection: `isinstance(keys, (str, bytes))`
- `__getitem__` str branch: `isinstance(key, (str, bytes))`

5. Leave `ASEColumnView` unchanged — it always uses `str`.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_generic_key_views.py -v`
Expected: PASS

**Step 5: Run full test suite**

Run: `uv run pytest tests/ -x --ignore=tests/test_benchmark_backend.py --ignore=tests/test_hf_aseio.py -q`
Expected: All pass (no behavioral change for str-keyed parents)

**Step 6: Commit**

```bash
git add src/asebytes/_views.py tests/test_generic_key_views.py
git commit -m "feat: add K TypeVar to sync views for bytes key support"
```

---

## Phase 2: Async views — add `K` and support `bytes` keys

### Task 3: Write failing tests for async views with bytes keys

**Files:**
- Modify: `tests/test_generic_key_views.py` (append async tests)

**Step 1: Write the failing test**

Append to `tests/test_generic_key_views.py`:

```python
from asebytes._async_views import (
    AsyncColumnView,
    AsyncRowView,
    AsyncSingleRowView,
)


class AsyncBytesMockParent:
    """Async mock parent using bytes keys (like AsyncBlobIO)."""

    def __init__(self, rows: list[dict[bytes, bytes]]):
        self._rows = rows

    def __len__(self):
        return len(self._rows)

    async def alen(self):
        return len(self._rows)

    async def _read_row(self, index, keys=None):
        row = self._rows[index]
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)

    async def _read_rows(self, indices, keys=None):
        return [await self._read_row(i, keys) for i in indices]

    async def _read_column(self, key, indices):
        return [self._rows[i][key] for i in indices]

    async def _write_row(self, index, data):
        self._rows[index] = data

    async def _delete_row(self, index):
        del self._rows[index]

    async def _delete_rows(self, start, stop):
        for i in range(stop - 1, start - 1, -1):
            del self._rows[i]

    async def _update_row(self, index, data):
        self._rows[index].update(data)

    async def _drop_keys(self, keys, indices):
        pass

    async def _get_available_keys(self, index):
        return list(self._rows[index].keys())

    def _build_result(self, row):
        return row


class TestAsyncRowViewBytesKey:
    @pytest.mark.anyio
    async def test_bytes_key_returns_column_view(self, brows):
        parent = AsyncBytesMockParent(brows)
        rv = AsyncRowView(parent, list(range(3)))
        cv = rv[b"name"]
        assert isinstance(cv, AsyncColumnView)

    @pytest.mark.anyio
    async def test_bytes_column_to_list(self, brows):
        parent = AsyncBytesMockParent(brows)
        rv = AsyncRowView(parent, list(range(3)))
        result = await rv[b"name"].to_list()
        assert result == [b"alice", b"bob", b"carol"]

    @pytest.mark.anyio
    async def test_bytes_column_int_index(self, brows):
        parent = AsyncBytesMockParent(brows)
        rv = AsyncRowView(parent, list(range(3)))
        result = await rv[b"name"][0]
        assert result == b"alice"


class TestAsyncSingleRowViewBytesKey:
    @pytest.mark.anyio
    async def test_bytes_key_subscript(self, brows):
        parent = AsyncBytesMockParent(brows)
        view = AsyncSingleRowView(parent, 0)
        result = await view[b"name"]
        assert result == b"alice"

    @pytest.mark.anyio
    async def test_list_bytes_key_subscript(self, brows):
        parent = AsyncBytesMockParent(brows)
        view = AsyncSingleRowView(parent, 0)
        result = await view[[b"name", b"age"]]
        assert result == [b"alice", b"30"]


class TestAsyncColumnViewBytesKey:
    @pytest.mark.anyio
    async def test_single_bytes_key(self, brows):
        parent = AsyncBytesMockParent(brows)
        cv = AsyncColumnView(parent, b"name", list(range(3)))
        result = await cv.to_list()
        assert result == [b"alice", b"bob", b"carol"]

    @pytest.mark.anyio
    async def test_multi_bytes_keys(self, brows):
        parent = AsyncBytesMockParent(brows)
        cv = AsyncColumnView(parent, [b"name", b"age"], list(range(3)))
        result = await cv.to_list()
        assert result == [[b"alice", b"30"], [b"bob", b"25"], [b"carol", b"35"]]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_generic_key_views.py::TestAsyncRowViewBytesKey -v`
Expected: FAIL — `AsyncRowView.__getitem__` doesn't handle bytes

### Task 4: Make async views accept bytes keys

**Files:**
- Modify: `src/asebytes/_async_views.py`

**Step 3: Update `_async_views.py`**

Changes:

1. Add `K = TypeVar("K", str, bytes)` (replace existing bare `R` only).

2. Update `AsyncViewParent`:
```python
class AsyncViewParent(Protocol[R, K]):
    ...
    async def _read_row(self, index: int, keys: list[K] | None = None) -> Any: ...
    async def _read_rows(self, indices: list[int], keys: list[K] | None = None) -> list[Any]: ...
    async def _read_column(self, key: K, indices: list[int]) -> list[Any]: ...
    async def _update_row(self, index: int, data: Any) -> None: ...
    async def _drop_keys(self, keys: list[K], indices: list[int]) -> None: ...
    async def _get_available_keys(self, index: int) -> list[K]: ...
```

3. `AsyncSingleRowView(Generic[R])` — keep as `Generic[R]` (it doesn't constrain key type in its own type signature). But update `__getitem__` to accept `bytes` directly without decoding:
```python
def __getitem__(self, key: str | bytes | list[str] | list[bytes]) -> _AsyncColumnValueView:
    if isinstance(key, (str, bytes)):
        keys = [key]
        single = True
    elif isinstance(key, list):
        keys = list(key)
        single = False
    else:
        raise TypeError(f"Unsupported key type: {type(key)}")
    return _AsyncColumnValueView(self._parent, keys, single, self._index)
```

Key change: **stop decoding** bytes→str. Pass bytes through as-is.

4. `AsyncRowView.__getitem__` — add `bytes` alongside `str`:
```python
if isinstance(key, (str, bytes)):
    return self._column_view_cls(self._parent, key, self._indices)
...
if isinstance(key[0], (str, bytes)):
    return self._column_view_cls(self._parent, key, self._indices)
```

5. `AsyncColumnView.__init__` — accept `bytes` in `keys` parameter:
```python
def __init__(self, parent, keys: str | bytes | list[str] | list[bytes], indices=None):
    self._single = isinstance(keys, (str, bytes))
    ...
```

6. `AsyncColumnView.__getitem__` — add `bytes` to str branches:
```python
if isinstance(key, (str, bytes)):
    return AsyncColumnView(self._parent, key)
```

7. `_AsyncColumnValueView.__init__` — change `keys: list[str]` to `keys: list[str] | list[bytes]` (or just `list`).

8. `AsyncRowView.adrop` — change `keys: list[str]` to `keys: list`:
```python
async def adrop(self, keys: list) -> None:
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_generic_key_views.py -v`
Expected: All pass

**Step 5: Run full test suite**

Run: `uv run pytest tests/ -x --ignore=tests/test_benchmark_backend.py --ignore=tests/test_hf_aseio.py -q`
Expected: All pass

**Step 6: Commit**

```bash
git add src/asebytes/_async_views.py tests/test_generic_key_views.py
git commit -m "feat: add K TypeVar to async views for bytes key support"
```

---

## Phase 3: BlobIO stops decoding bytes→str

### Task 5: Write failing tests for native bytes in BlobIO

**Files:**
- Modify: `tests/test_blob_column_access.py`

**Step 1: Write the failing test**

Add new tests to `TestBlobIOColumnAccess` that verify bytes keys pass through without decoding. The critical tests:

```python
class TestBlobIONativeBytes:
    """BlobIO must pass bytes keys natively — no str decoding."""

    def test_slice_then_bytes_key(self, blob_backend):
        """blobdb[0:2][b"name"] must work (the original bug)."""
        io = BlobIO(blob_backend)
        rv = io[0:2]
        cv = rv[b"name"]
        assert isinstance(cv, ColumnView)
        assert cv.to_list() == [b"alice", b"bob"]

    def test_slice_then_list_bytes_key(self, blob_backend):
        io = BlobIO(blob_backend)
        rv = io[0:3]
        cv = rv[[b"name", b"age"]]
        assert isinstance(cv, ColumnView)
        result = cv.to_list()
        assert result == [[b"alice", b"30"], [b"bob", b"25"], [b"carol", b"35"]]

    def test_column_int_index_returns_bytes(self, blob_backend):
        io = BlobIO(blob_backend)
        result = io[b"name"][0]
        assert result == b"alice"

    def test_read_row_keys_are_bytes(self, blob_backend):
        """Internal _read_row should accept bytes keys and return bytes-keyed dict."""
        io = BlobIO(blob_backend)
        row = io._read_row(0, keys=[b"name"])
        assert b"name" in row
        assert row[b"name"] == b"alice"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_blob_column_access.py::TestBlobIONativeBytes -v`
Expected: FAIL — `_read_row` currently takes `list[str]`, encodes to bytes, then re-keys back to str.

### Task 6: Remove bytes→str decoding from BlobIO

**Files:**
- Modify: `src/asebytes/_blob_io.py`

**Step 3: Simplify BlobIO internal methods**

Replace the encoding/decoding methods with direct passthrough:

```python
def _read_row(self, index: int, keys: list[bytes] | None = None) -> dict[bytes, bytes] | None:
    return self._backend.get(index, keys)

def _read_rows(self, indices: list[int], keys: list[bytes] | None = None) -> list[dict[bytes, bytes] | None]:
    return self._backend.get_many(indices, keys)

def _iter_rows(self, indices: list[int], keys: list[bytes] | None = None) -> Iterator[dict[bytes, bytes] | None]:
    return self._backend.iter_rows(indices, keys)

def _read_column(self, key: bytes, indices: list[int]) -> list[Any]:
    return self._backend.get_column(key, indices)
```

Update `__getitem__` to pass bytes through instead of decoding:
```python
if isinstance(index, bytes):
    return ColumnView(self, index, list(range(len(self))))
# Remove str key support — BlobIO is bytes-only
if isinstance(index, list):
    ...
    if isinstance(index[0], bytes):
        return ColumnView(self, index, list(range(len(self))))
    # Remove str list branch
```

**Important:** Remove `str` key branches from `BlobIO.__getitem__`. BlobIO only accepts `bytes` keys.

**Step 4: Update existing blob tests**

`tests/test_blob_column_access.py` has tests using `io["name"]` (str keys) that must change to `io[b"name"]` (bytes keys). Update:
- `test_str_key_returns_column_view` → `test_bytes_key_returns_column_view` (keep)
- `test_str_key_to_list` → change to use bytes key: `io[b"name"].to_list()`
- `test_list_str_returns_column_view` → change to use bytes list: `io[[b"name", b"age"]]`
- `test_multi_key_to_list` → change to bytes: `io[[b"name", b"age"]].to_list()`
- Remove str-key tests that no longer apply

**Step 5: Run tests**

Run: `uv run pytest tests/test_blob_column_access.py -v`
Expected: All pass

**Step 6: Run full test suite**

Run: `uv run pytest tests/ -x --ignore=tests/test_benchmark_backend.py --ignore=tests/test_hf_aseio.py -q`
Expected: All pass (may need to fix other test files that use str keys with BlobIO)

**Step 7: Commit**

```bash
git add src/asebytes/_blob_io.py tests/test_blob_column_access.py
git commit -m "feat: BlobIO uses native bytes keys, removes str decoding"
```

---

## Phase 4: AsyncBlobIO and AsyncBytesIO stop decoding

### Task 7: Write failing tests for native bytes in async blob classes

**Files:**
- Modify: `tests/test_blob_column_access.py` (update async tests)

**Step 1: Add tests**

```python
class TestAsyncBlobIONativeBytes:
    @pytest.mark.anyio
    async def test_slice_then_bytes_key(self, blob_backend):
        io = AsyncBlobIO(SyncToAsyncAdapter(blob_backend))
        rv = io[0:2]
        result = await rv[b"name"].to_list()
        assert result == [b"alice", b"bob"]

    @pytest.mark.anyio
    async def test_single_row_bytes_subscript(self, blob_backend):
        io = AsyncBlobIO(SyncToAsyncAdapter(blob_backend))
        result = await io[0][b"name"]
        assert result == b"alice"

    @pytest.mark.anyio
    async def test_column_int_returns_bytes_value(self, blob_backend):
        io = AsyncBlobIO(SyncToAsyncAdapter(blob_backend))
        result = await io[b"name"][0]
        assert result == b"alice"


class TestAsyncBytesIONativeBytes:
    @pytest.mark.anyio
    async def test_slice_then_bytes_key(self, blob_backend):
        io = AsyncBytesIO(SyncToAsyncAdapter(blob_backend))
        rv = io[0:2]
        result = await rv[b"name"].to_list()
        assert result == [b"alice", b"bob"]

    @pytest.mark.anyio
    async def test_single_row_bytes_subscript(self, blob_backend):
        io = AsyncBytesIO(SyncToAsyncAdapter(blob_backend))
        result = await io[0][b"name"]
        assert result == b"alice"
```

**Step 2: Verify RED**

Run: `uv run pytest tests/test_blob_column_access.py::TestAsyncBlobIONativeBytes -v`

### Task 8: Remove bytes→str decoding from AsyncBlobIO and AsyncBytesIO

**Files:**
- Modify: `src/asebytes/_async_blob_io.py`
- Modify: `src/asebytes/_async_bytesio.py`

**Step 3: Simplify both files**

Same pattern as BlobIO — remove all `.encode()` / `.decode()` calls:

```python
# _async_blob_io.py and _async_bytesio.py — replace methods with:

async def _read_row(self, index: int, keys: list[bytes] | None = None) -> Any:
    return await self._backend.aget(index, keys)

async def _read_rows(self, indices: list[int], keys: list[bytes] | None = None) -> list[Any]:
    return await self._backend.aget_many(indices, keys)

async def _read_column(self, key: bytes, indices: list[int]) -> list[Any]:
    return await self._backend.aget_column(key, indices)

async def _drop_keys(self, keys: list[bytes], indices: list[int]) -> None:
    if not isinstance(self._backend, AsyncReadWriteBackend):
        raise TypeError("Backend is read-only")
    await self._backend.adrop_keys(keys, indices)
```

Update `__getitem__` in both: remove `str` key support, only accept `bytes`:

```python
if isinstance(index, bytes):
    return AsyncColumnView(self, index)
# Remove str branch
if isinstance(index, list):
    ...
    if isinstance(index[0], bytes):
        return AsyncColumnView(self, index)
    # Remove str and list[str] branches
```

**Step 4: Update existing async blob tests**

In `tests/test_blob_column_access.py`, update `TestAsyncBlobIOColumnAccess` and `TestAsyncBytesIOColumnAccess`:
- Change `io["name"]` → `io[b"name"]`
- Change `io[["name", "age"]]` → `io[[b"name", b"age"]]`
- Remove str-key-specific tests

**Step 5: Run tests**

Run: `uv run pytest tests/test_blob_column_access.py -v`
Expected: All pass

**Step 6: Run full test suite**

Run: `uv run pytest tests/ -x --ignore=tests/test_benchmark_backend.py --ignore=tests/test_hf_aseio.py -q`
Expected: All pass

**Step 7: Commit**

```bash
git add src/asebytes/_async_blob_io.py src/asebytes/_async_bytesio.py tests/test_blob_column_access.py
git commit -m "feat: AsyncBlobIO/AsyncBytesIO use native bytes keys"
```

---

## Phase 5: Fix remaining test files that use str keys with BlobIO

### Task 9: Audit and fix all tests that use str keys with blob IO

**Files:**
- May need to modify: `tests/test_bytesio.py`, `tests/test_bytesio_update.py`, `tests/test_async_bytesio.py`

**Step 1: Search for str key usage with BlobIO/BytesIO**

Run: `grep -rn 'io\["' tests/test_bytesio*.py tests/test_async_bytesio.py` to find str key usage.

**Step 2: Fix any found issues**

Change `io["key"]` → `io[b"key"]` where the IO class is BlobIO/AsyncBlobIO/AsyncBytesIO.

**Step 3: Run full test suite**

Run: `uv run pytest tests/ -x --ignore=tests/test_benchmark_backend.py --ignore=tests/test_hf_aseio.py -q`
Expected: All pass

**Step 4: Commit**

```bash
git add tests/
git commit -m "fix: update remaining tests to use bytes keys with blob IO"
```

---

## Phase 6: Update IO class type annotations

### Task 10: Update type annotations on all IO classes

**Files:**
- Modify: `src/asebytes/io.py` — `ASEIO.__getitem__` overloads add `K=str` to view types
- Modify: `src/asebytes/_object_io.py` — `ObjectIO.__getitem__` overloads add `K=str`
- Modify: `src/asebytes/_blob_io.py` — `BlobIO.__getitem__` overloads add `K=bytes`
- Modify: `src/asebytes/_async_io.py` — `AsyncASEIO.__getitem__` overloads add `K=str`
- Modify: `src/asebytes/_async_object_io.py` — `AsyncObjectIO.__getitem__` overloads add `K=str`
- Modify: `src/asebytes/_async_blob_io.py` — `AsyncBlobIO.__getitem__` overloads add `K=bytes`
- Modify: `src/asebytes/_async_bytesio.py` — `AsyncBytesIO.__getitem__` overloads add `K=bytes`

This is annotations-only — no behavioral changes. Update overload signatures like:
```python
# ASEIO
def __getitem__(self, index: slice) -> RowView[ase.Atoms, str]: ...

# BlobIO
def __getitem__(self, index: slice) -> RowView[dict[bytes, bytes], bytes]: ...
```

**Step 1: Update all files**

Pure annotation updates, no logic changes.

**Step 2: Run full test suite**

Run: `uv run pytest tests/ -x --ignore=tests/test_benchmark_backend.py --ignore=tests/test_hf_aseio.py -q`
Expected: All pass (no behavioral changes)

**Step 3: Commit**

```bash
git add src/asebytes/
git commit -m "chore: update IO class type annotations with K parameter"
```

---

## Verification

After all phases:

```bash
# Full test suite
uv run pytest tests/ -x --ignore=tests/test_benchmark_backend.py --ignore=tests/test_hf_aseio.py

# Key behavioral checks (manual or via test):
# blobdb[b"key"][0]       → bytes value ✓
# blobdb[0:2][b"key"]     → ColumnView with bytes ✓ (was TypeError)
# blobdb[0][b"key"]       → bytes value ✓
# await ablobdb[0][b"key"]→ bytes value ✓
# objdb["key"][0]          → str value ✓ (unchanged)
# objdb[0:2]["key"]        → ColumnView with str ✓ (unchanged)
```
