# Universal Backend Adapters Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build generic adapter classes that convert between blob-level (`dict[bytes,bytes]`) and object-level (`dict[str,Any]`) backends, so any backend can be used at any level. Includes async adapters, registry fallback, LMDB refactor, and universal test fixtures.

**Architecture:** Four sync adapter classes (BlobToObject read/readwrite, ObjectToBlob read/readwrite) that wrap existing backends and apply msgpack serialization/deserialization. Four matching async adapters that wrap `AsyncReadBackend`/`AsyncReadWriteBackend` directly. The registry gains fallback resolution so `get_blob_backend_cls("test.zarr")` auto-wraps via adapter. LMDB object backends become thin subclasses of the generic adapters. Universal pytest fixtures parametrize tests across all backend x level combinations.

**Tech Stack:** Python 3.11+, msgpack, msgpack-numpy, pytest, asyncio

---

### Task 1: BlobToObjectReadAdapter — failing test

**Files:**
- Create: `tests/test_adapters.py`

**Step 1: Write the failing test**

```python
import numpy as np
import pytest

from asebytes._backends import ReadBackend
from asebytes.lmdb import LMDBBlobBackend


@pytest.fixture
def blob_backend(tmp_path):
    return LMDBBlobBackend(str(tmp_path / "test.lmdb"))


@pytest.fixture
def sample_blob_row():
    """Pre-serialized blob row matching sample_row from test_lmdb_backend."""
    import msgpack
    import msgpack_numpy as m

    return {
        b"calc.energy": msgpack.packb(-10.5, default=m.encode),
        b"info.smiles": msgpack.packb("O", default=m.encode),
        b"arrays.numbers": msgpack.packb(np.array([1, 8]), default=m.encode),
    }


def test_blob_to_object_read_adapter_isinstance(blob_backend):
    from asebytes._adapters import BlobToObjectReadAdapter

    adapter = BlobToObjectReadAdapter(blob_backend)
    assert isinstance(adapter, ReadBackend)


def test_blob_to_object_read_adapter_get(blob_backend, sample_blob_row):
    from asebytes._adapters import BlobToObjectReadAdapter

    blob_backend.extend([sample_blob_row])
    adapter = BlobToObjectReadAdapter(blob_backend)

    row = adapter.get(0)
    assert row["calc.energy"] == pytest.approx(-10.5)
    assert row["info.smiles"] == "O"
    assert np.array_equal(row["arrays.numbers"], np.array([1, 8]))


def test_blob_to_object_read_adapter_len(blob_backend, sample_blob_row):
    from asebytes._adapters import BlobToObjectReadAdapter

    blob_backend.extend([sample_blob_row, sample_blob_row])
    adapter = BlobToObjectReadAdapter(blob_backend)
    assert len(adapter) == 2


def test_blob_to_object_read_adapter_get_with_keys(blob_backend, sample_blob_row):
    from asebytes._adapters import BlobToObjectReadAdapter

    blob_backend.extend([sample_blob_row])
    adapter = BlobToObjectReadAdapter(blob_backend)

    row = adapter.get(0, keys=["calc.energy"])
    assert "calc.energy" in row
    assert "info.smiles" not in row


def test_blob_to_object_read_adapter_none_placeholder(blob_backend):
    from asebytes._adapters import BlobToObjectReadAdapter

    blob_backend.extend([None])
    adapter = BlobToObjectReadAdapter(blob_backend)
    assert adapter.get(0) is None


def test_blob_to_object_read_adapter_get_many(blob_backend, sample_blob_row):
    from asebytes._adapters import BlobToObjectReadAdapter

    blob_backend.extend([sample_blob_row, sample_blob_row, sample_blob_row])
    adapter = BlobToObjectReadAdapter(blob_backend)

    rows = adapter.get_many([0, 2])
    assert len(rows) == 2
    assert rows[0]["calc.energy"] == pytest.approx(-10.5)
    assert rows[1]["calc.energy"] == pytest.approx(-10.5)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_adapters.py -v -x 2>&1 | head -30`
Expected: FAIL with `ModuleNotFoundError` or `ImportError` — `_adapters` module does not exist.

**Step 3: Commit**

```bash
git add tests/test_adapters.py
git commit -m "test: add failing tests for BlobToObjectReadAdapter"
```

---

### Task 2: BlobToObjectReadAdapter — implementation

**Files:**
- Create: `src/asebytes/_adapters.py`

**Step 1: Write minimal implementation**

```python
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import msgpack
import msgpack_numpy as m

from ._backends import ReadBackend, ReadWriteBackend


def _deserialize_row(raw: dict[bytes, bytes]) -> dict[str, Any]:
    return {
        k.decode(): msgpack.unpackb(v, object_hook=m.decode)
        for k, v in raw.items()
    }


def _serialize_row(data: dict[str, Any]) -> dict[bytes, bytes]:
    return {
        k.encode(): msgpack.packb(v, default=m.encode)
        for k, v in data.items()
    }


class BlobToObjectReadAdapter(ReadBackend[str, Any]):
    """Wraps a blob-level ReadBackend and deserializes to object-level.

    Converts dict[bytes, bytes] → dict[str, Any] via msgpack on read.
    """

    def __init__(self, store: ReadBackend[bytes, bytes]):
        self._store = store

    def __len__(self) -> int:
        return len(self._store)

    def get(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any] | None:
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        raw = self._store.get(index, keys=byte_keys)
        if raw is None:
            return None
        return _deserialize_row(raw)

    def get_many(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any] | None]:
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        raws = self._store.get_many(indices, keys=byte_keys)
        return [
            None if raw is None else _deserialize_row(raw)
            for raw in raws
        ]

    def iter_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> Iterator[dict[str, Any] | None]:
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        for raw in self._store.iter_rows(indices, keys=byte_keys):
            yield None if raw is None else _deserialize_row(raw)

    def get_column(self, key: str, indices: list[int] | None = None) -> list[Any]:
        byte_key = key.encode()
        raws = self._store.get_column(byte_key, indices)
        return [msgpack.unpackb(v, object_hook=m.decode) for v in raws]

    def keys(self, index: int) -> list[str]:
        return [k.decode() for k in self._store.keys(index)]
```

**Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/test_adapters.py -v 2>&1 | tail -20`
Expected: All tests PASS.

**Step 3: Commit**

```bash
git add src/asebytes/_adapters.py
git commit -m "feat: add BlobToObjectReadAdapter"
```

---

### Task 3: BlobToObjectReadWriteAdapter — failing test

**Files:**
- Modify: `tests/test_adapters.py`

**Step 1: Write the failing test**

Add to `tests/test_adapters.py`:

```python
from asebytes._backends import ReadWriteBackend


def test_blob_to_object_readwrite_adapter_isinstance(blob_backend):
    from asebytes._adapters import BlobToObjectReadWriteAdapter

    adapter = BlobToObjectReadWriteAdapter(blob_backend)
    assert isinstance(adapter, ReadWriteBackend)
    assert isinstance(adapter, ReadBackend)


def test_blob_to_object_readwrite_set_get(blob_backend):
    from asebytes._adapters import BlobToObjectReadWriteAdapter

    adapter = BlobToObjectReadWriteAdapter(blob_backend)
    row = {"calc.energy": -10.5, "info.smiles": "O"}
    adapter.extend([row])
    assert len(adapter) == 1
    result = adapter.get(0)
    assert result["calc.energy"] == pytest.approx(-10.5)
    assert result["info.smiles"] == "O"


def test_blob_to_object_readwrite_extend(blob_backend):
    from asebytes._adapters import BlobToObjectReadWriteAdapter

    adapter = BlobToObjectReadWriteAdapter(blob_backend)
    rows = [{"calc.energy": float(-i)} for i in range(3)]
    adapter.extend(rows)
    assert len(adapter) == 3
    assert adapter.get(1)["calc.energy"] == pytest.approx(-1.0)


def test_blob_to_object_readwrite_set_overwrite(blob_backend):
    from asebytes._adapters import BlobToObjectReadWriteAdapter

    adapter = BlobToObjectReadWriteAdapter(blob_backend)
    adapter.extend([{"calc.energy": -1.0}])
    adapter.set(0, {"calc.energy": -99.0})
    assert adapter.get(0)["calc.energy"] == pytest.approx(-99.0)


def test_blob_to_object_readwrite_insert(blob_backend):
    from asebytes._adapters import BlobToObjectReadWriteAdapter

    adapter = BlobToObjectReadWriteAdapter(blob_backend)
    adapter.extend([{"calc.energy": -1.0}, {"calc.energy": -3.0}])
    adapter.insert(1, {"calc.energy": -2.0})
    assert len(adapter) == 3
    assert adapter.get(1)["calc.energy"] == pytest.approx(-2.0)


def test_blob_to_object_readwrite_delete(blob_backend):
    from asebytes._adapters import BlobToObjectReadWriteAdapter

    adapter = BlobToObjectReadWriteAdapter(blob_backend)
    adapter.extend([{"calc.energy": -1.0}, {"calc.energy": -2.0}])
    adapter.delete(0)
    assert len(adapter) == 1
    assert adapter.get(0)["calc.energy"] == pytest.approx(-2.0)


def test_blob_to_object_readwrite_none_extend(blob_backend):
    from asebytes._adapters import BlobToObjectReadWriteAdapter

    adapter = BlobToObjectReadWriteAdapter(blob_backend)
    adapter.extend([{"calc.energy": -1.0}, None, {"calc.energy": -3.0}])
    assert adapter.get(1) is None


def test_blob_to_object_readwrite_update(blob_backend):
    from asebytes._adapters import BlobToObjectReadWriteAdapter

    adapter = BlobToObjectReadWriteAdapter(blob_backend)
    adapter.extend([{"calc.energy": -1.0, "info.smiles": "O"}])
    adapter.update(0, {"calc.energy": -99.0})
    result = adapter.get(0)
    assert result["calc.energy"] == pytest.approx(-99.0)
    assert result["info.smiles"] == "O"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_adapters.py::test_blob_to_object_readwrite_adapter_isinstance -v -x 2>&1 | tail -10`
Expected: FAIL with `ImportError` — `BlobToObjectReadWriteAdapter` not found.

**Step 3: Commit**

```bash
git add tests/test_adapters.py
git commit -m "test: add failing tests for BlobToObjectReadWriteAdapter"
```

---

### Task 4: BlobToObjectReadWriteAdapter — implementation

**Files:**
- Modify: `src/asebytes/_adapters.py`

**Step 1: Write minimal implementation**

Add to `src/asebytes/_adapters.py`:

```python
class BlobToObjectReadWriteAdapter(BlobToObjectReadAdapter, ReadWriteBackend[str, Any]):
    """Wraps a blob-level ReadWriteBackend and converts to object-level.

    Read: dict[bytes, bytes] → dict[str, Any] via msgpack deserialization.
    Write: dict[str, Any] → dict[bytes, bytes] via msgpack serialization.
    """

    def __init__(self, store: ReadWriteBackend[bytes, bytes]):
        super().__init__(store)

    def set(self, index: int, data: dict[str, Any] | None) -> None:
        if data is None:
            self._store.set(index, None)
        else:
            self._store.set(index, _serialize_row(data))

    def insert(self, index: int, data: dict[str, Any] | None) -> None:
        if data is None:
            self._store.insert(index, None)
        else:
            self._store.insert(index, _serialize_row(data))

    def delete(self, index: int) -> None:
        self._store.delete(index)

    def extend(self, data: list[dict[str, Any] | None]) -> None:
        self._store.extend([
            _serialize_row(d) if d is not None else None
            for d in data
        ])

    def update(self, index: int, data: dict[str, Any]) -> None:
        self._store.update(index, _serialize_row(data))
```

**Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/test_adapters.py -v 2>&1 | tail -20`
Expected: All tests PASS.

**Step 3: Commit**

```bash
git add src/asebytes/_adapters.py
git commit -m "feat: add BlobToObjectReadWriteAdapter"
```

---

### Task 5: ObjectToBlobReadAdapter — failing test

**Files:**
- Modify: `tests/test_adapters.py`

**Step 1: Write the failing test**

Add to `tests/test_adapters.py`:

```python
@pytest.fixture
def object_backend(tmp_path):
    """An object-level backend (using LMDB via existing adapter for convenience)."""
    from asebytes._adapters import BlobToObjectReadWriteAdapter

    blob = LMDBBlobBackend(str(tmp_path / "obj.lmdb"))
    return BlobToObjectReadWriteAdapter(blob)


def test_object_to_blob_read_adapter_isinstance(object_backend):
    from asebytes._adapters import ObjectToBlobReadAdapter

    adapter = ObjectToBlobReadAdapter(object_backend)
    assert isinstance(adapter, ReadBackend)


def test_object_to_blob_read_adapter_roundtrip(object_backend):
    from asebytes._adapters import ObjectToBlobReadAdapter

    object_backend.extend([{"calc.energy": -10.5, "info.smiles": "O"}])
    adapter = ObjectToBlobReadAdapter(object_backend)

    row = adapter.get(0)
    assert isinstance(row, dict)
    # Keys should be bytes
    assert all(isinstance(k, bytes) for k in row.keys())
    assert all(isinstance(v, bytes) for v in row.values())

    # Deserialize to verify content
    import msgpack
    import msgpack_numpy as m

    energy = msgpack.unpackb(row[b"calc.energy"], object_hook=m.decode)
    assert energy == pytest.approx(-10.5)


def test_object_to_blob_read_adapter_none_placeholder(object_backend):
    from asebytes._adapters import ObjectToBlobReadAdapter

    object_backend.extend([None])
    adapter = ObjectToBlobReadAdapter(object_backend)
    assert adapter.get(0) is None


def test_object_to_blob_read_adapter_len(object_backend):
    from asebytes._adapters import ObjectToBlobReadAdapter

    object_backend.extend([{"a": 1}, {"a": 2}])
    adapter = ObjectToBlobReadAdapter(object_backend)
    assert len(adapter) == 2


def test_object_to_blob_read_adapter_get_with_keys(object_backend):
    from asebytes._adapters import ObjectToBlobReadAdapter

    object_backend.extend([{"calc.energy": -10.5, "info.smiles": "O"}])
    adapter = ObjectToBlobReadAdapter(object_backend)

    row = adapter.get(0, keys=[b"calc.energy"])
    assert b"calc.energy" in row
    assert b"info.smiles" not in row
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_adapters.py::test_object_to_blob_read_adapter_isinstance -v -x 2>&1 | tail -10`
Expected: FAIL with `ImportError` — `ObjectToBlobReadAdapter` not found.

**Step 3: Commit**

```bash
git add tests/test_adapters.py
git commit -m "test: add failing tests for ObjectToBlobReadAdapter"
```

---

### Task 6: ObjectToBlobReadAdapter — implementation

**Files:**
- Modify: `src/asebytes/_adapters.py`

**Step 1: Write minimal implementation**

Add to `src/asebytes/_adapters.py`:

```python
class ObjectToBlobReadAdapter(ReadBackend[bytes, bytes]):
    """Wraps an object-level ReadBackend and serializes to blob-level.

    Converts dict[str, Any] → dict[bytes, bytes] via msgpack on read.
    """

    def __init__(self, store: ReadBackend[str, Any]):
        self._store = store

    def __len__(self) -> int:
        return len(self._store)

    def get(
        self, index: int, keys: list[bytes] | None = None
    ) -> dict[bytes, bytes] | None:
        str_keys = [k.decode() for k in keys] if keys is not None else None
        row = self._store.get(index, keys=str_keys)
        if row is None:
            return None
        return _serialize_row(row)

    def get_many(
        self, indices: list[int], keys: list[bytes] | None = None
    ) -> list[dict[bytes, bytes] | None]:
        str_keys = [k.decode() for k in keys] if keys is not None else None
        rows = self._store.get_many(indices, keys=str_keys)
        return [
            None if row is None else _serialize_row(row)
            for row in rows
        ]

    def iter_rows(
        self, indices: list[int], keys: list[bytes] | None = None
    ) -> Iterator[dict[bytes, bytes] | None]:
        str_keys = [k.decode() for k in keys] if keys is not None else None
        for row in self._store.iter_rows(indices, keys=str_keys):
            yield None if row is None else _serialize_row(row)

    def get_column(self, key: bytes, indices: list[int] | None = None) -> list[Any]:
        str_key = key.decode()
        values = self._store.get_column(str_key, indices)
        return [msgpack.packb(v, default=m.encode) for v in values]

    def keys(self, index: int) -> list[bytes]:
        return [k.encode() for k in self._store.keys(index)]
```

**Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/test_adapters.py -v 2>&1 | tail -20`
Expected: All tests PASS.

**Step 3: Commit**

```bash
git add src/asebytes/_adapters.py
git commit -m "feat: add ObjectToBlobReadAdapter"
```

---

### Task 7: ObjectToBlobReadWriteAdapter — failing test + implementation

**Files:**
- Modify: `tests/test_adapters.py`
- Modify: `src/asebytes/_adapters.py`

**Step 1: Write the failing test**

Add to `tests/test_adapters.py`:

```python
def test_object_to_blob_readwrite_isinstance(object_backend):
    from asebytes._adapters import ObjectToBlobReadWriteAdapter

    adapter = ObjectToBlobReadWriteAdapter(object_backend)
    assert isinstance(adapter, ReadWriteBackend)


def test_object_to_blob_readwrite_set_get(object_backend):
    import msgpack
    import msgpack_numpy as m
    from asebytes._adapters import ObjectToBlobReadWriteAdapter

    adapter = ObjectToBlobReadWriteAdapter(object_backend)
    blob_row = {
        b"calc.energy": msgpack.packb(-10.5, default=m.encode),
    }
    adapter.extend([blob_row])
    assert len(adapter) == 1

    result = adapter.get(0)
    energy = msgpack.unpackb(result[b"calc.energy"], object_hook=m.decode)
    assert energy == pytest.approx(-10.5)

    # Verify underlying object backend also has the data
    obj_row = object_backend.get(0)
    assert obj_row["calc.energy"] == pytest.approx(-10.5)


def test_object_to_blob_readwrite_delete(object_backend):
    from asebytes._adapters import ObjectToBlobReadWriteAdapter

    adapter = ObjectToBlobReadWriteAdapter(object_backend)
    adapter.extend([{b"a": msgpack.packb(1, default=m.encode)}])
    adapter.delete(0)
    assert len(adapter) == 0


def test_object_to_blob_readwrite_insert(object_backend):
    import msgpack
    import msgpack_numpy as m
    from asebytes._adapters import ObjectToBlobReadWriteAdapter

    adapter = ObjectToBlobReadWriteAdapter(object_backend)
    row_a = {b"calc.energy": msgpack.packb(-1.0, default=m.encode)}
    row_c = {b"calc.energy": msgpack.packb(-3.0, default=m.encode)}
    row_b = {b"calc.energy": msgpack.packb(-2.0, default=m.encode)}
    adapter.extend([row_a, row_c])
    adapter.insert(1, row_b)
    assert len(adapter) == 3
    result = adapter.get(1)
    energy = msgpack.unpackb(result[b"calc.energy"], object_hook=m.decode)
    assert energy == pytest.approx(-2.0)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_adapters.py::test_object_to_blob_readwrite_isinstance -v -x 2>&1 | tail -10`
Expected: FAIL.

**Step 3: Write minimal implementation**

Add to `src/asebytes/_adapters.py`:

```python
class ObjectToBlobReadWriteAdapter(ObjectToBlobReadAdapter, ReadWriteBackend[bytes, bytes]):
    """Wraps an object-level ReadWriteBackend and converts to blob-level.

    Read: dict[str, Any] → dict[bytes, bytes] via msgpack serialization.
    Write: dict[bytes, bytes] → dict[str, Any] via msgpack deserialization.
    """

    def __init__(self, store: ReadWriteBackend[str, Any]):
        super().__init__(store)

    def set(self, index: int, data: dict[bytes, bytes] | None) -> None:
        if data is None:
            self._store.set(index, None)
        else:
            self._store.set(index, _deserialize_row(data))

    def insert(self, index: int, data: dict[bytes, bytes] | None) -> None:
        if data is None:
            self._store.insert(index, None)
        else:
            self._store.insert(index, _deserialize_row(data))

    def delete(self, index: int) -> None:
        self._store.delete(index)

    def extend(self, data: list[dict[bytes, bytes] | None]) -> None:
        self._store.extend([
            _deserialize_row(d) if d is not None else None
            for d in data
        ])

    def update(self, index: int, data: dict[bytes, bytes]) -> None:
        self._store.update(index, _deserialize_row(data))
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_adapters.py -v 2>&1 | tail -30`
Expected: All tests PASS.

**Step 5: Commit**

```bash
git add tests/test_adapters.py src/asebytes/_adapters.py
git commit -m "feat: add ObjectToBlobReadWriteAdapter"
```

---

### Task 8: Async adapters — failing test

**Files:**
- Create: `tests/test_async_adapters.py`

**Step 1: Write the failing test**

```python
import msgpack
import msgpack_numpy as m
import numpy as np
import pytest

from asebytes._async_backends import (
    AsyncReadBackend,
    AsyncReadWriteBackend,
    SyncToAsyncReadWriteAdapter,
)
from asebytes.lmdb import LMDBBlobBackend


@pytest.fixture
def async_blob_backend(tmp_path):
    """Async blob backend wrapping sync LMDB via SyncToAsyncAdapter."""
    blob = LMDBBlobBackend(str(tmp_path / "async_test.lmdb"))
    return SyncToAsyncReadWriteAdapter(blob)


@pytest.mark.asyncio
async def test_async_blob_to_object_read_isinstance(async_blob_backend):
    from asebytes._async_adapters import AsyncBlobToObjectReadAdapter

    adapter = AsyncBlobToObjectReadAdapter(async_blob_backend)
    assert isinstance(adapter, AsyncReadBackend)


@pytest.mark.asyncio
async def test_async_blob_to_object_read_get(async_blob_backend):
    from asebytes._async_adapters import AsyncBlobToObjectReadAdapter

    blob_row = {
        b"calc.energy": msgpack.packb(-10.5, default=m.encode),
        b"info.smiles": msgpack.packb("O", default=m.encode),
    }
    await async_blob_backend.extend([blob_row])
    adapter = AsyncBlobToObjectReadAdapter(async_blob_backend)

    row = await adapter.get(0)
    assert row["calc.energy"] == pytest.approx(-10.5)
    assert row["info.smiles"] == "O"


@pytest.mark.asyncio
async def test_async_blob_to_object_read_none(async_blob_backend):
    from asebytes._async_adapters import AsyncBlobToObjectReadAdapter

    await async_blob_backend.extend([None])
    adapter = AsyncBlobToObjectReadAdapter(async_blob_backend)
    assert await adapter.get(0) is None


@pytest.mark.asyncio
async def test_async_blob_to_object_readwrite_set(async_blob_backend):
    from asebytes._async_adapters import AsyncBlobToObjectReadWriteAdapter

    adapter = AsyncBlobToObjectReadWriteAdapter(async_blob_backend)
    await adapter.extend([{"calc.energy": -10.5}])
    assert await adapter.len() == 1
    row = await adapter.get(0)
    assert row["calc.energy"] == pytest.approx(-10.5)


@pytest.mark.asyncio
async def test_async_object_to_blob_read_isinstance(tmp_path):
    from asebytes._adapters import BlobToObjectReadWriteAdapter
    from asebytes._async_adapters import AsyncObjectToBlobReadAdapter

    blob = LMDBBlobBackend(str(tmp_path / "obj.lmdb"))
    sync_obj = BlobToObjectReadWriteAdapter(blob)
    async_obj = SyncToAsyncReadWriteAdapter(sync_obj)

    adapter = AsyncObjectToBlobReadAdapter(async_obj)
    assert isinstance(adapter, AsyncReadBackend)


@pytest.mark.asyncio
async def test_async_object_to_blob_readwrite_roundtrip(tmp_path):
    from asebytes._adapters import BlobToObjectReadWriteAdapter
    from asebytes._async_adapters import AsyncObjectToBlobReadWriteAdapter

    blob = LMDBBlobBackend(str(tmp_path / "obj.lmdb"))
    sync_obj = BlobToObjectReadWriteAdapter(blob)
    async_obj = SyncToAsyncReadWriteAdapter(sync_obj)

    adapter = AsyncObjectToBlobReadWriteAdapter(async_obj)
    blob_row = {b"calc.energy": msgpack.packb(-5.0, default=m.encode)}
    await adapter.extend([blob_row])

    result = await adapter.get(0)
    energy = msgpack.unpackb(result[b"calc.energy"], object_hook=m.decode)
    assert energy == pytest.approx(-5.0)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_async_adapters.py -v -x 2>&1 | tail -10`
Expected: FAIL with `ModuleNotFoundError` — `_async_adapters` module does not exist.

**Step 3: Commit**

```bash
git add tests/test_async_adapters.py
git commit -m "test: add failing tests for async adapters"
```

---

### Task 9: Async adapters — implementation

**Files:**
- Create: `src/asebytes/_async_adapters.py`

**Step 1: Write implementation**

```python
from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import msgpack
import msgpack_numpy as m

from ._async_backends import AsyncReadBackend, AsyncReadWriteBackend
from ._adapters import _deserialize_row, _serialize_row


class AsyncBlobToObjectReadAdapter(AsyncReadBackend[str, Any]):
    """Async adapter: wraps AsyncReadBackend[bytes,bytes] → AsyncReadBackend[str,Any]."""

    def __init__(self, store: AsyncReadBackend[bytes, bytes]):
        self._store = store

    async def len(self) -> int:
        return await self._store.len()

    async def get(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any] | None:
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        raw = await self._store.get(index, keys=byte_keys)
        if raw is None:
            return None
        return _deserialize_row(raw)

    async def get_many(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any] | None]:
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        raws = await self._store.get_many(indices, keys=byte_keys)
        return [None if raw is None else _deserialize_row(raw) for raw in raws]

    async def iter_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> AsyncIterator[dict[str, Any] | None]:
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        async for raw in self._store.iter_rows(indices, keys=byte_keys):
            yield None if raw is None else _deserialize_row(raw)

    async def get_column(self, key: str, indices: list[int] | None = None) -> list[Any]:
        byte_key = key.encode()
        raws = await self._store.get_column(byte_key, indices)
        return [msgpack.unpackb(v, object_hook=m.decode) for v in raws]

    async def keys(self, index: int) -> list[str]:
        return [k.decode() for k in await self._store.keys(index)]


class AsyncBlobToObjectReadWriteAdapter(
    AsyncBlobToObjectReadAdapter, AsyncReadWriteBackend[str, Any]
):
    """Async adapter: wraps AsyncReadWriteBackend[bytes,bytes] → AsyncReadWriteBackend[str,Any]."""

    def __init__(self, store: AsyncReadWriteBackend[bytes, bytes]):
        super().__init__(store)

    async def set(self, index: int, data: dict[str, Any] | None) -> None:
        if data is None:
            await self._store.set(index, None)
        else:
            await self._store.set(index, _serialize_row(data))

    async def insert(self, index: int, data: dict[str, Any] | None) -> None:
        if data is None:
            await self._store.insert(index, None)
        else:
            await self._store.insert(index, _serialize_row(data))

    async def delete(self, index: int) -> None:
        await self._store.delete(index)

    async def extend(self, data: list[dict[str, Any] | None]) -> None:
        await self._store.extend([
            _serialize_row(d) if d is not None else None for d in data
        ])

    async def update(self, index: int, data: dict[str, Any]) -> None:
        await self._store.update(index, _serialize_row(data))


class AsyncObjectToBlobReadAdapter(AsyncReadBackend[bytes, bytes]):
    """Async adapter: wraps AsyncReadBackend[str,Any] → AsyncReadBackend[bytes,bytes]."""

    def __init__(self, store: AsyncReadBackend[str, Any]):
        self._store = store

    async def len(self) -> int:
        return await self._store.len()

    async def get(
        self, index: int, keys: list[bytes] | None = None
    ) -> dict[bytes, bytes] | None:
        str_keys = [k.decode() for k in keys] if keys is not None else None
        row = await self._store.get(index, keys=str_keys)
        if row is None:
            return None
        return _serialize_row(row)

    async def get_many(
        self, indices: list[int], keys: list[bytes] | None = None
    ) -> list[dict[bytes, bytes] | None]:
        str_keys = [k.decode() for k in keys] if keys is not None else None
        rows = await self._store.get_many(indices, keys=str_keys)
        return [None if row is None else _serialize_row(row) for row in rows]

    async def iter_rows(
        self, indices: list[int], keys: list[bytes] | None = None
    ) -> AsyncIterator[dict[bytes, bytes] | None]:
        str_keys = [k.decode() for k in keys] if keys is not None else None
        async for row in self._store.iter_rows(indices, keys=str_keys):
            yield None if row is None else _serialize_row(row)

    async def get_column(self, key: bytes, indices: list[int] | None = None) -> list[Any]:
        str_key = key.decode()
        values = await self._store.get_column(str_key, indices)
        return [msgpack.packb(v, default=m.encode) for v in values]

    async def keys(self, index: int) -> list[bytes]:
        return [k.encode() for k in await self._store.keys(index)]


class AsyncObjectToBlobReadWriteAdapter(
    AsyncObjectToBlobReadAdapter, AsyncReadWriteBackend[bytes, bytes]
):
    """Async adapter: wraps AsyncReadWriteBackend[str,Any] → AsyncReadWriteBackend[bytes,bytes]."""

    def __init__(self, store: AsyncReadWriteBackend[str, Any]):
        super().__init__(store)

    async def set(self, index: int, data: dict[bytes, bytes] | None) -> None:
        if data is None:
            await self._store.set(index, None)
        else:
            await self._store.set(index, _deserialize_row(data))

    async def insert(self, index: int, data: dict[bytes, bytes] | None) -> None:
        if data is None:
            await self._store.insert(index, None)
        else:
            await self._store.insert(index, _deserialize_row(data))

    async def delete(self, index: int) -> None:
        await self._store.delete(index)

    async def extend(self, data: list[dict[bytes, bytes] | None]) -> None:
        await self._store.extend([
            _deserialize_row(d) if d is not None else None for d in data
        ])

    async def update(self, index: int, data: dict[bytes, bytes]) -> None:
        await self._store.update(index, _deserialize_row(data))
```

**Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/test_async_adapters.py -v 2>&1 | tail -20`
Expected: All tests PASS.

**Step 3: Commit**

```bash
git add src/asebytes/_async_adapters.py
git commit -m "feat: add async adapter classes"
```

---

### Task 10: LMDB refactor — failing test (regression)

**Files:**
- Modify: `tests/test_lmdb_backend.py`

**Step 1: Run existing LMDB tests to establish baseline**

Run: `uv run pytest tests/test_lmdb_backend.py -v 2>&1 | tail -20`
Expected: All existing tests PASS (this is the baseline before refactoring).

**Step 2: Add adapter-provenance assertions to verify refactoring**

Add to `tests/test_lmdb_backend.py`:

```python
def test_lmdb_object_backend_uses_adapter(backend):
    """Verify LMDBObjectBackend inherits from generic adapter after refactor."""
    from asebytes._adapters import BlobToObjectReadWriteAdapter

    assert isinstance(backend, BlobToObjectReadWriteAdapter)
```

**Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_lmdb_backend.py::test_lmdb_object_backend_uses_adapter -v -x 2>&1 | tail -10`
Expected: FAIL — `LMDBObjectBackend` does not yet inherit from `BlobToObjectReadWriteAdapter`.

**Step 4: Commit**

```bash
git add tests/test_lmdb_backend.py
git commit -m "test: add failing adapter-provenance test for LMDB refactor"
```

---

### Task 11: LMDB refactor — implementation

**Files:**
- Modify: `src/asebytes/lmdb/_backend.py`

**Step 1: Rewrite `lmdb/_backend.py`**

Replace the entire file with:

```python
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import msgpack
import msgpack_numpy as m

from ._blob_backend import LMDBBlobBackend
from .._adapters import BlobToObjectReadAdapter, BlobToObjectReadWriteAdapter


class LMDBObjectReadBackend(BlobToObjectReadAdapter):
    """Read-only LMDB storage backend using msgpack serialization.

    Thin subclass of BlobToObjectReadAdapter that adds LMDB-specific
    constructor and `env` property. Preserves LMDB-specific optimizations
    for iter_rows, get_many, and get_column via single-transaction reads.

    Parameters
    ----------
    file : str
        Path to LMDB database file.
    prefix : bytes
        Key prefix for namespacing.
    map_size : int
        Maximum LMDB size in bytes (default 10GB).
    **lmdb_kwargs
        Additional kwargs for lmdb.open().
    """

    def __init__(
        self,
        file: str,
        prefix: bytes = b"",
        map_size: int = 10737418240,
        **lmdb_kwargs,
    ):
        super().__init__(
            LMDBBlobBackend(file, prefix, map_size, readonly=True, **lmdb_kwargs)
        )

    @property
    def env(self):
        """Expose the LMDB environment for configuration inspection."""
        return self._store.env

    # -- LMDB-specific optimizations: single-transaction batch reads ------

    def _deserialize_row(self, raw: dict[bytes, bytes]) -> dict[str, Any]:
        from .._adapters import _deserialize_row
        return _deserialize_row(raw)

    def iter_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> Iterator[dict[str, Any] | None]:
        """Stream rows within a single LMDB read transaction."""
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        with self._store.env.begin() as txn:
            for i in indices:
                raw = self._store.get_with_txn(txn, i, byte_keys)
                yield None if raw is None else self._deserialize_row(raw)

    def get_many(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any] | None]:
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        with self._store.env.begin() as txn:
            return [
                None if (raw := self._store.get_with_txn(txn, i, byte_keys)) is None
                else self._deserialize_row(raw)
                for i in indices
            ]

    def get_column(
        self, key: str, indices: list[int] | None = None
    ) -> list[Any]:
        if indices is None:
            indices = list(range(len(self)))
        byte_key = key.encode()
        with self._store.env.begin() as txn:
            return [
                msgpack.unpackb(
                    self._store.get_with_txn(txn, i, [byte_key])[byte_key],
                    object_hook=m.decode,
                )
                for i in indices
            ]


class LMDBObjectBackend(BlobToObjectReadWriteAdapter):
    """Read-write LMDB storage backend using msgpack serialization.

    Thin subclass of BlobToObjectReadWriteAdapter that adds LMDB-specific
    constructor, `env` property, and optimized partial update.

    Parameters
    ----------
    file : str
        Path to LMDB database file.
    prefix : bytes
        Key prefix for namespacing.
    map_size : int
        Maximum LMDB size in bytes (default 10GB).
    readonly : bool
        Open in read-only mode.
    **lmdb_kwargs
        Additional kwargs for lmdb.open().
    """

    def __init__(
        self,
        file: str,
        prefix: bytes = b"",
        map_size: int = 10737418240,
        readonly: bool = False,
        **lmdb_kwargs,
    ):
        super().__init__(
            LMDBBlobBackend(file, prefix, map_size, readonly, **lmdb_kwargs)
        )

    @property
    def env(self):
        """Expose the LMDB environment for configuration inspection."""
        return self._store.env

    # -- LMDB-specific optimizations --------------------------------------

    def _deserialize_row(self, raw: dict[bytes, bytes]) -> dict[str, Any]:
        from .._adapters import _deserialize_row
        return _deserialize_row(raw)

    def _check_index(self, index: int) -> None:
        if index < 0 or index >= len(self._store):
            raise IndexError(index)

    def iter_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> Iterator[dict[str, Any] | None]:
        """Stream rows within a single LMDB read transaction."""
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        with self._store.env.begin() as txn:
            for i in indices:
                raw = self._store.get_with_txn(txn, i, byte_keys)
                yield None if raw is None else self._deserialize_row(raw)

    def get_many(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any] | None]:
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        with self._store.env.begin() as txn:
            return [
                None if (raw := self._store.get_with_txn(txn, i, byte_keys)) is None
                else self._deserialize_row(raw)
                for i in indices
            ]

    def get_column(
        self, key: str, indices: list[int] | None = None
    ) -> list[Any]:
        if indices is None:
            indices = list(range(len(self)))
        byte_key = key.encode()
        with self._store.env.begin() as txn:
            return [
                msgpack.unpackb(
                    self._store.get_with_txn(txn, i, [byte_key])[byte_key],
                    object_hook=m.decode,
                )
                for i in indices
            ]

    def update(self, index: int, data: dict[str, Any]) -> None:
        """Optimized partial update -- only serializes and writes changed keys."""
        raw = {k.encode(): msgpack.packb(v, default=m.encode) for k, v in data.items()}
        self._check_index(index)
        self._store.update(index, raw)
```

**Step 2: Run ALL LMDB tests to verify no regressions**

Run: `uv run pytest tests/test_lmdb_backend.py -v 2>&1 | tail -20`
Expected: All tests PASS including the new adapter-provenance test.

**Step 3: Run the full test suite to check for regressions**

Run: `uv run pytest tests/ -v --timeout=60 2>&1 | tail -30`
Expected: No new failures.

**Step 4: Commit**

```bash
git add src/asebytes/lmdb/_backend.py
git commit -m "refactor: LMDB object backends now subclass generic adapters"
```

---

### Task 12: Registry fallback — failing test

**Files:**
- Create: `tests/test_registry_fallback.py`

**Step 1: Write the failing test**

```python
import pytest

from asebytes._registry import get_backend_cls, get_blob_backend_cls


def test_get_blob_backend_cls_zarr_fallback():
    """get_blob_backend_cls should auto-wrap Zarr object backend."""
    cls = get_blob_backend_cls("test.zarr")
    # Should return something that can be instantiated (not raise KeyError)
    assert cls is not None


def test_get_blob_backend_cls_h5_fallback():
    """get_blob_backend_cls should auto-wrap H5MD object backend."""
    cls = get_blob_backend_cls("test.h5")
    assert cls is not None


def test_get_blob_backend_cls_lmdb_native():
    """LMDB should still return the native blob backend, not an adapter."""
    from asebytes.lmdb import LMDBBlobBackend

    cls = get_blob_backend_cls("test.lmdb")
    assert cls is LMDBBlobBackend
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_registry_fallback.py -v -x 2>&1 | tail -10`
Expected: FAIL with `KeyError: "No blob backend registered for 'test.zarr'"`.

**Step 3: Commit**

```bash
git add tests/test_registry_fallback.py
git commit -m "test: add failing tests for registry fallback resolution"
```

---

### Task 13: Registry fallback — implementation

**Files:**
- Modify: `src/asebytes/_registry.py`

**Step 1: Modify `get_blob_backend_cls` to add fallback**

Add at the end of `get_blob_backend_cls`, replacing the final `raise KeyError(...)`:

```python
    # --- Fallback: wrap object backend with ObjectToBlobReadWriteAdapter ---
    try:
        obj_cls = get_backend_cls(path, readonly=readonly)
    except KeyError:
        raise KeyError(f"No blob backend registered for '{path}'")

    from ._adapters import ObjectToBlobReadAdapter, ObjectToBlobReadWriteAdapter

    if readonly is True:
        def _make_read_adapter(*args, **kwargs):
            return ObjectToBlobReadAdapter(obj_cls(*args, **kwargs))
        return _make_read_adapter

    def _make_readwrite_adapter(*args, **kwargs):
        return ObjectToBlobReadWriteAdapter(obj_cls(*args, **kwargs))
    return _make_readwrite_adapter
```

**Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/test_registry_fallback.py -v 2>&1 | tail -10`
Expected: All tests PASS.

**Step 3: Run full test suite to verify no regressions**

Run: `uv run pytest tests/ --timeout=60 2>&1 | tail -20`
Expected: No new failures.

**Step 4: Commit**

```bash
git add src/asebytes/_registry.py
git commit -m "feat: registry auto-wraps object backends with blob adapter"
```

---

### Task 14: Exports — update `__init__.py`

**Files:**
- Modify: `src/asebytes/__init__.py`

**Step 1: Add adapter exports**

Add the following imports and `__all__` entries to `src/asebytes/__init__.py`:

After the existing `from ._async_backends import (...)` block, add:

```python
from ._adapters import (
    BlobToObjectReadAdapter,
    BlobToObjectReadWriteAdapter,
    ObjectToBlobReadAdapter,
    ObjectToBlobReadWriteAdapter,
)
from ._async_adapters import (
    AsyncBlobToObjectReadAdapter,
    AsyncBlobToObjectReadWriteAdapter,
    AsyncObjectToBlobReadAdapter,
    AsyncObjectToBlobReadWriteAdapter,
)
```

Add to `__all__`:

```python
    # Adapters
    "BlobToObjectReadAdapter",
    "BlobToObjectReadWriteAdapter",
    "ObjectToBlobReadAdapter",
    "ObjectToBlobReadWriteAdapter",
    "AsyncBlobToObjectReadAdapter",
    "AsyncBlobToObjectReadWriteAdapter",
    "AsyncObjectToBlobReadAdapter",
    "AsyncObjectToBlobReadWriteAdapter",
```

**Step 2: Verify import works**

Run: `uv run python -c "from asebytes import BlobToObjectReadWriteAdapter, ObjectToBlobReadWriteAdapter; print('OK')"`
Expected: Prints `OK`.

**Step 3: Commit**

```bash
git add src/asebytes/__init__.py
git commit -m "feat: export adapter classes from asebytes package"
```

---

### Task 15: Universal test fixtures — failing test

**Files:**
- Modify: `tests/conftest.py`
- Create: `tests/test_universal_object_backend.py`

**Step 1: Add universal fixtures to conftest.py**

Add the following to `tests/conftest.py` at the end:

```python
# ---------------------------------------------------------------------------
# Universal parametrized backend fixtures (full matrix: native + adapters)
# ---------------------------------------------------------------------------

from asebytes._adapters import (
    BlobToObjectReadWriteAdapter,
    ObjectToBlobReadWriteAdapter,
)
from asebytes.lmdb import LMDBBlobBackend


def _lmdb_blob(tmp_path):
    return LMDBBlobBackend(str(tmp_path / "uni.lmdb"))


def _lmdb_object(tmp_path):
    return BlobToObjectReadWriteAdapter(_lmdb_blob(tmp_path))


def _zarr_object(tmp_path):
    from asebytes.zarr import ZarrBackend
    return ZarrBackend(str(tmp_path / "uni.zarr"))


def _zarr_blob(tmp_path):
    return ObjectToBlobReadWriteAdapter(_zarr_object(tmp_path))


def _h5md_object(tmp_path):
    from asebytes.h5md import H5MDBackend
    return H5MDBackend(str(tmp_path / "uni.h5"))


def _h5md_blob(tmp_path):
    return ObjectToBlobReadWriteAdapter(_h5md_object(tmp_path))


@pytest.fixture(params=[
    pytest.param(_lmdb_blob, id="lmdb-blob-native"),
    pytest.param(_zarr_blob, id="zarr-blob-via-adapter"),
    pytest.param(_h5md_blob, id="h5md-blob-via-adapter"),
])
def uni_blob_backend(tmp_path, request):
    """Universal blob-level backend fixture across all storage formats."""
    return request.param(tmp_path)


@pytest.fixture(params=[
    pytest.param(_lmdb_object, id="lmdb-object-via-adapter"),
    pytest.param(_zarr_object, id="zarr-object-native"),
    pytest.param(_h5md_object, id="h5md-object-native"),
])
def uni_object_backend(tmp_path, request):
    """Universal object-level backend fixture across all storage formats."""
    return request.param(tmp_path)
```

**Step 2: Write universal object backend tests**

Create `tests/test_universal_object_backend.py`:

```python
import numpy as np
import pytest

from asebytes._backends import ReadBackend, ReadWriteBackend


def test_uni_object_isinstance(uni_object_backend):
    assert isinstance(uni_object_backend, ReadBackend)


def test_uni_object_empty_len(uni_object_backend):
    assert len(uni_object_backend) == 0


def test_uni_object_extend_get(uni_object_backend):
    rows = [
        {"calc.energy": -1.0, "info.smiles": "O"},
        {"calc.energy": -2.0, "info.smiles": "CC"},
    ]
    uni_object_backend.extend(rows)
    assert len(uni_object_backend) == 2

    row = uni_object_backend.get(0)
    assert row["calc.energy"] == pytest.approx(-1.0)
    assert row["info.smiles"] == "O"


def test_uni_object_get_with_keys(uni_object_backend):
    uni_object_backend.extend([{"calc.energy": -1.0, "info.smiles": "O"}])
    row = uni_object_backend.get(0, keys=["calc.energy"])
    assert "calc.energy" in row
    assert "info.smiles" not in row


def test_uni_object_get_many(uni_object_backend):
    rows = [{"calc.energy": float(-i)} for i in range(5)]
    uni_object_backend.extend(rows)
    result = uni_object_backend.get_many([1, 3])
    assert len(result) == 2
    assert result[0]["calc.energy"] == pytest.approx(-1.0)
    assert result[1]["calc.energy"] == pytest.approx(-3.0)


def test_uni_object_none_placeholder(uni_object_backend):
    uni_object_backend.extend([{"calc.energy": -1.0}, None, {"calc.energy": -3.0}])
    assert uni_object_backend.get(1) is None


def test_uni_object_numpy_roundtrip(uni_object_backend):
    row = {
        "cell": np.eye(3),
        "arrays.positions": np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]),
        "arrays.numbers": np.array([1, 8]),
    }
    uni_object_backend.extend([row])
    result = uni_object_backend.get(0)
    assert np.allclose(result["cell"], np.eye(3))
    assert np.array_equal(result["arrays.numbers"], np.array([1, 8]))
```

**Step 3: Run to verify all tests pass across all backends**

Run: `uv run pytest tests/test_universal_object_backend.py -v 2>&1 | tail -30`
Expected: All tests PASS across lmdb-object-via-adapter, zarr-object-native, h5md-object-native.

**Step 4: Commit**

```bash
git add tests/conftest.py tests/test_universal_object_backend.py
git commit -m "test: add universal parametrized object backend fixtures and tests"
```

---

### Task 16: Universal blob backend tests

**Files:**
- Create: `tests/test_universal_blob_backend.py`

**Step 1: Write universal blob backend tests**

```python
import msgpack
import msgpack_numpy as m
import numpy as np
import pytest

from asebytes._backends import ReadBackend


def _pack(v):
    return msgpack.packb(v, default=m.encode)


def _unpack(v):
    return msgpack.unpackb(v, object_hook=m.decode)


def test_uni_blob_isinstance(uni_blob_backend):
    assert isinstance(uni_blob_backend, ReadBackend)


def test_uni_blob_empty_len(uni_blob_backend):
    assert len(uni_blob_backend) == 0


def test_uni_blob_extend_get(uni_blob_backend):
    rows = [
        {b"calc.energy": _pack(-1.0), b"info.smiles": _pack("O")},
        {b"calc.energy": _pack(-2.0), b"info.smiles": _pack("CC")},
    ]
    uni_blob_backend.extend(rows)
    assert len(uni_blob_backend) == 2

    row = uni_blob_backend.get(0)
    assert _unpack(row[b"calc.energy"]) == pytest.approx(-1.0)
    assert _unpack(row[b"info.smiles"]) == "O"


def test_uni_blob_none_placeholder(uni_blob_backend):
    uni_blob_backend.extend([{b"a": _pack(1)}, None, {b"a": _pack(3)}])
    assert uni_blob_backend.get(1) is None


def test_uni_blob_numpy_roundtrip(uni_blob_backend):
    arr = np.array([[1.0, 2.0], [3.0, 4.0]])
    row = {b"data": _pack(arr)}
    uni_blob_backend.extend([row])
    result = uni_blob_backend.get(0)
    assert np.allclose(_unpack(result[b"data"]), arr)
```

**Step 2: Run to verify all tests pass**

Run: `uv run pytest tests/test_universal_blob_backend.py -v 2>&1 | tail -30`
Expected: All tests PASS across lmdb-blob-native, zarr-blob-via-adapter, h5md-blob-via-adapter.

**Step 3: Commit**

```bash
git add tests/test_universal_blob_backend.py
git commit -m "test: add universal parametrized blob backend tests"
```

---

### Task 17: Full regression — run entire test suite

**Step 1: Run the complete test suite**

Run: `uv run pytest tests/ -v --timeout=120 2>&1 | tail -40`
Expected: All tests PASS. No regressions from the LMDB refactor or registry changes.

**Step 2: If failures, fix them before proceeding**

If any test fails, debug and fix. Common issues:
- LMDB `_check_index` method references in tests
- Import paths changed
- `iter_rows` returning AsyncIterator instead of Iterator in wrong context

**Step 3: Commit any fixes**

```bash
git add -A
git commit -m "fix: resolve any test regressions from adapter refactor"
```

---

### Task 18: Final cleanup

**Step 1: Verify all new files are committed**

Run: `git status`
Expected: Clean working tree.

**Step 2: Verify exports**

Run:
```bash
uv run python -c "
import asebytes
print('Sync adapters:', hasattr(asebytes, 'BlobToObjectReadWriteAdapter'))
print('Async adapters:', hasattr(asebytes, 'AsyncBlobToObjectReadWriteAdapter'))
print('Registry fallback:', asebytes._registry.get_blob_backend_cls('test.zarr'))
"
```
Expected: All True, registry returns a callable.

**Step 3: Run full suite one final time**

Run: `uv run pytest tests/ -v --timeout=120 2>&1 | tail -20`
Expected: All pass.
