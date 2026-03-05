# Lazy Concat (`ConcatView`) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add lazy read-only concatenation (`io1 + io2 + io3`, `sum([io1, io2, io3], [])`) to `ObjectIO`, `ASEIO`, and `BlobIO`.

**Architecture:** A single `ConcatView` class in `_concat.py` implements the `ViewParent` protocol, delegating reads to a flat list of IO sources. Existing `RowView`/`ColumnView`/`ASEColumnView` machinery is reused unchanged. Each IO class gets `__add__`/`__radd__` that creates/extends a `ConcatView`.

**Tech Stack:** Python 3.10+, standard library only (`collections.defaultdict`, `itertools`). Tests use `pytest` + `MemoryObjectBackend` (no files needed for ObjectIO/ASEIO tests; lmdb for BlobIO).

---

### Task 1: `ConcatView` + `ObjectIO` operators

**Files:**
- Create: `src/asebytes/_concat.py`
- Modify: `src/asebytes/_object_io.py`
- Test: `tests/test_concat_view.py`

---

**Step 1: Write the failing tests**

Create `tests/test_concat_view.py`:

```python
"""Tests for ConcatView — lazy read-only concatenation of IO facades."""
import uuid
import pytest

import asebytes
from asebytes import ObjectIO, ConcatView
from asebytes.memory import MemoryObjectBackend
from asebytes._views import RowView, ColumnView


def _fresh_object_io(rows: list[dict]) -> ObjectIO:
    """Create an ObjectIO backed by a fresh MemoryObjectBackend."""
    backend = MemoryObjectBackend(str(uuid.uuid4()))
    io = ObjectIO(backend)
    io.extend(rows)
    return io


# ---------------------------------------------------------------------------
# ObjectIO concat
# ---------------------------------------------------------------------------

@pytest.fixture
def three_object_ios():
    io1 = _fresh_object_io([{"x": 0}, {"x": 1}])
    io2 = _fresh_object_io([{"x": 2}, {"x": 3}])
    io3 = _fresh_object_io([{"x": 4}])
    return io1, io2, io3


def test_object_concat_sum(three_object_ios):
    io1, io2, io3 = three_object_ios
    cat = sum([io1, io2, io3], [])
    assert isinstance(cat, ConcatView)


def test_object_concat_len(three_object_ios):
    io1, io2, io3 = three_object_ios
    cat = io1 + io2 + io3
    assert len(cat) == 5


def test_object_concat_iter(three_object_ios):
    io1, io2, io3 = three_object_ios
    cat = io1 + io2 + io3
    values = [row["x"] for row in cat]
    assert values == [0, 1, 2, 3, 4]


def test_object_concat_getitem_int(three_object_ios):
    io1, io2, io3 = three_object_ios
    cat = io1 + io2 + io3
    assert cat[0] == {"x": 0}
    assert cat[2] == {"x": 2}
    assert cat[4] == {"x": 4}
    assert cat[-1] == {"x": 4}
    assert cat[-5] == {"x": 0}


def test_object_concat_getitem_int_oob(three_object_ios):
    io1, io2, io3 = three_object_ios
    cat = io1 + io2 + io3
    with pytest.raises(IndexError):
        _ = cat[5]
    with pytest.raises(IndexError):
        _ = cat[-6]


def test_object_concat_getitem_slice(three_object_ios):
    io1, io2, io3 = three_object_ios
    cat = io1 + io2 + io3
    view = cat[1:4]
    assert isinstance(view, RowView)
    assert len(view) == 3
    assert [row["x"] for row in view] == [1, 2, 3]


def test_object_concat_getitem_list_int(three_object_ios):
    io1, io2, io3 = three_object_ios
    cat = io1 + io2 + io3
    view = cat[[0, 2, 4]]
    assert isinstance(view, RowView)
    assert [row["x"] for row in view] == [0, 2, 4]


def test_object_concat_getitem_str(three_object_ios):
    io1, io2, io3 = three_object_ios
    cat = io1 + io2 + io3
    col = cat["x"]
    assert isinstance(col, ColumnView)
    assert list(col) == [0, 1, 2, 3, 4]


def test_object_concat_flat_chaining(three_object_ios):
    io1, io2, io3 = three_object_ios
    cat = io1 + io2 + io3
    # Must be flat — one ConcatView with 3 sources, not nested
    assert len(cat._sources) == 3


def test_object_concat_concat_concat(three_object_ios):
    io1, io2, io3 = three_object_ios
    left = io1 + io2
    right = io2 + io3  # io2 appears in both; that's fine
    combined = left + right
    assert len(combined._sources) == 4
    assert len(combined) == 7


def test_object_concat_write_raises(three_object_ios):
    io1, io2, io3 = three_object_ios
    cat = io1 + io2 + io3
    view = cat[1:3]
    with pytest.raises(TypeError, match="read-only"):
        view.set([{"x": 99}, {"x": 99}])


def test_object_concat_mixed_type_raises():
    io_obj = _fresh_object_io([{"x": 0}])
    from asebytes import ASEIO
    from asebytes.memory import MemoryObjectBackend
    # ASEIO and ObjectIO should not be combinable
    with pytest.raises(TypeError):
        _ = io_obj + io_obj  # same type — OK, but mixing should fail
    # We can't easily get an ASEIO with MemoryObjectBackend here
    # so just verify ConcatView rejects mismatched types at construction
    from asebytes._concat import ConcatView
    with pytest.raises(TypeError):
        ConcatView([io_obj, "not_an_io"])


def test_object_concat_read_rows_preserves_order(three_object_ios):
    """Indices spanning multiple sources must return rows in correct order."""
    io1, io2, io3 = three_object_ios
    cat = io1 + io2 + io3
    # Interleaved: indices 0 (src0), 2 (src1), 1 (src0), 4 (src2), 3 (src1)
    view = cat[[0, 2, 1, 4, 3]]
    assert [row["x"] for row in view] == [0, 2, 1, 4, 3]
```

**Step 2: Run tests to confirm they all fail**

```
uv run pytest tests/test_concat_view.py -v 2>&1 | head -40
```

Expected: `ImportError` or `AttributeError` — `ConcatView` does not exist yet.

---

**Step 3: Create `src/asebytes/_concat.py`**

```python
"""ConcatView -- lazy read-only concatenation of IO facades."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from typing import Any, Generic, TypeVar

from ._views import ASEColumnView, ColumnView, RowView

T = TypeVar("T")


class ConcatView(Generic[T]):
    """Lazy read-only concatenation of multiple IO instances.

    All sources must be the same IO class. Create via ``io1 + io2`` or
    ``sum([io1, io2, io3], [])``.

    Supports: ``__len__``, ``__iter__``, ``__getitem__`` (int, slice,
    list[int], str/bytes, list[str/bytes]).
    """

    __slots__ = ("_sources", "_column_view_cls")

    def __init__(self, sources: list) -> None:
        if not sources:
            raise ValueError("ConcatView requires at least one source")
        first_type = type(sources[0])
        for s in sources[1:]:
            if type(s) is not first_type:
                raise TypeError(
                    f"Cannot concat {first_type.__name__} with {type(s).__name__}"
                )
        self._sources = list(sources)
        from .io import ASEIO

        self._column_view_cls = (
            ASEColumnView if isinstance(sources[0], ASEIO) else ColumnView
        )

    # --- Length ---

    def __len__(self) -> int:
        return sum(len(s) for s in self._sources)

    # --- Index mapping ---

    def _locate(self, global_idx: int) -> tuple[int, int]:
        """Map a global index to (source_index, local_index). O(n_sources)."""
        offset = 0
        for i, src in enumerate(self._sources):
            n = len(src)
            if global_idx < offset + n:
                return i, global_idx - offset
            offset += n
        raise IndexError(global_idx)

    # --- ViewParent protocol (read side) ---

    def _read_row(self, index: int, keys: list | None = None) -> dict:
        src_i, local_i = self._locate(index)
        return self._sources[src_i]._read_row(local_i, keys)

    def _read_rows(self, indices: list[int], keys: list | None = None) -> list:
        """Batch read, grouped by source to minimise I/O calls."""
        buckets: dict[int, list[tuple[int, int]]] = defaultdict(list)
        for pos, gi in enumerate(indices):
            src_i, li = self._locate(gi)
            buckets[src_i].append((pos, li))
        result: list = [None] * len(indices)
        for src_i, pairs in buckets.items():
            positions, local_idxs = zip(*pairs)
            rows = self._sources[src_i]._read_rows(list(local_idxs), keys)
            for pos, row in zip(positions, rows):
                result[pos] = row
        return result

    def _iter_rows(self, indices: list[int], keys: list | None = None) -> Iterator:
        for gi in indices:
            src_i, local_i = self._locate(gi)
            yield from self._sources[src_i]._iter_rows([local_i], keys)

    def _read_column(self, key: Any, indices: list[int]) -> list:
        buckets: dict[int, list[tuple[int, int]]] = defaultdict(list)
        for pos, gi in enumerate(indices):
            src_i, li = self._locate(gi)
            buckets[src_i].append((pos, li))
        result: list = [None] * len(indices)
        for src_i, pairs in buckets.items():
            positions, local_idxs = zip(*pairs)
            values = self._sources[src_i]._read_column(key, list(local_idxs))
            for pos, val in zip(positions, values):
                result[pos] = val
        return result

    def _build_result(self, row: dict) -> T:
        return self._sources[0]._build_result(row)

    # --- ViewParent protocol (write side — all raise) ---

    def _write_row(self, index: int, data: Any) -> None:
        raise TypeError("ConcatView is read-only")

    def _update_row(self, index: int, data: dict) -> None:
        raise TypeError("ConcatView is read-only")

    def _delete_row(self, index: int) -> None:
        raise TypeError("ConcatView is read-only")

    def _delete_rows(self, start: int, stop: int) -> None:
        raise TypeError("ConcatView is read-only")

    def _drop_keys(self, keys: list, indices: list[int]) -> None:
        raise TypeError("ConcatView is read-only")

    def _update_many(self, start: int, data: list) -> None:
        raise TypeError("ConcatView is read-only")

    def _set_column(self, key: Any, start: int, values: list) -> None:
        raise TypeError("ConcatView is read-only")

    def _write_many(self, start: int, data: list) -> None:
        raise TypeError("ConcatView is read-only")

    # --- Public interface ---

    def __getitem__(self, index: Any) -> Any:
        if isinstance(index, int):
            n = len(self)
            if index < 0:
                index += n
            if index < 0 or index >= n:
                raise IndexError(index)
            src_i, local_i = self._locate(index)
            row = self._sources[src_i]._read_row(local_i)
            return self._build_result(row)
        if isinstance(index, slice):
            indices = list(range(len(self))[index])
            return RowView(self, indices, column_view_cls=self._column_view_cls)
        if isinstance(index, (str, bytes)):
            return self._column_view_cls(self, index)
        if isinstance(index, list):
            if not index:
                return RowView(self, [], column_view_cls=self._column_view_cls)
            if isinstance(index[0], int):
                n = len(self)
                normalized = []
                for i in index:
                    idx = i + n if i < 0 else i
                    if idx < 0 or idx >= n:
                        raise IndexError(i)
                    normalized.append(idx)
                return RowView(self, normalized, column_view_cls=self._column_view_cls)
            if isinstance(index[0], (str, bytes)):
                return self._column_view_cls(self, index)
        raise TypeError(f"Unsupported index type: {type(index)}")

    def __iter__(self) -> Iterator[T]:
        for src in self._sources:
            yield from src

    def __add__(self, other: Any) -> ConcatView:
        if isinstance(other, ConcatView):
            # Flatten: verify type compatibility
            if type(other._sources[0]) is not type(self._sources[0]):
                raise TypeError(
                    f"Cannot concat {type(self._sources[0]).__name__} "
                    f"with {type(other._sources[0]).__name__}"
                )
            return ConcatView(self._sources + other._sources)
        if type(other) is not type(self._sources[0]):
            raise TypeError(
                f"Cannot concat {type(self._sources[0]).__name__} "
                f"with {type(other).__name__}"
            )
        return ConcatView(self._sources + [other])

    def __repr__(self) -> str:
        src_type = type(self._sources[0]).__name__
        return (
            f"ConcatView({src_type}, n_sources={len(self._sources)}, "
            f"len={len(self)})"
        )
```

**Step 4: Add `__add__` and `__radd__` to `ObjectIO`**

In `src/asebytes/_object_io.py`, add after the `__repr__` method (end of class):

```python
    def __add__(self, other: Any) -> ConcatView:
        from ._concat import ConcatView

        if isinstance(other, ConcatView):
            if type(other._sources[0]) is not type(self):
                raise TypeError(
                    f"Cannot concat {type(self).__name__} "
                    f"with {type(other._sources[0]).__name__}"
                )
            return ConcatView([self] + other._sources)
        if type(other) is not type(self):
            raise TypeError(
                f"Cannot concat {type(self).__name__} with {type(other).__name__}"
            )
        return ConcatView([self, other])

    def __radd__(self, other: Any) -> ConcatView:
        if other == []:
            from ._concat import ConcatView

            return ConcatView([self])
        return NotImplemented
```

Also add `ConcatView` to the import in the type annotation (no import at module level needed — it's done lazily inside the methods).

Add `Any` to the imports at the top of `_object_io.py` if not already present. (It is already there.)

**Step 5: Run the ObjectIO tests**

```
uv run pytest tests/test_concat_view.py -v
```

Expected: all tests pass.

**Step 6: Commit**

```bash
git add src/asebytes/_concat.py src/asebytes/_object_io.py tests/test_concat_view.py
git commit -m "feat: add ConcatView + ObjectIO __add__/__radd__ for lazy concat"
```

---

### Task 2: `ASEIO` operator + tests

**Files:**
- Modify: `src/asebytes/io.py`
- Modify: `tests/test_concat_view.py`

---

**Step 1: Add ASEIO tests to `tests/test_concat_view.py`**

Append to the file:

```python
# ---------------------------------------------------------------------------
# ASEIO concat
# ---------------------------------------------------------------------------

import ase


def _fresh_ase_io(atoms_list: list, tmp_path_factory) -> "asebytes.ASEIO":
    from asebytes import ASEIO

    p = str(tmp_path_factory.mktemp("aseio") / "data.lmdb")
    io = ASEIO(p)
    io.extend(atoms_list)
    return io


@pytest.fixture
def three_ase_ios(tmp_path_factory):
    a1 = ase.Atoms("H", positions=[[0, 0, 0]])
    a2 = ase.Atoms("H", positions=[[1, 0, 0]])
    a3 = ase.Atoms("H", positions=[[2, 0, 0]])
    io1 = _fresh_ase_io([a1, a2], tmp_path_factory)
    io2 = _fresh_ase_io([a3], tmp_path_factory)
    return io1, io2


def test_ase_concat_sum(three_ase_ios):
    io1, io2 = three_ase_ios
    cat = sum([io1, io2], [])
    assert isinstance(cat, ConcatView)
    assert len(cat) == 3


def test_ase_concat_iter(three_ase_ios):
    io1, io2 = three_ase_ios
    cat = io1 + io2
    atoms = list(cat)
    assert all(isinstance(a, ase.Atoms) for a in atoms)
    assert len(atoms) == 3


def test_ase_concat_getitem_int(three_ase_ios):
    io1, io2 = three_ase_ios
    cat = io1 + io2
    a = cat[2]
    assert isinstance(a, ase.Atoms)
    assert a.positions[0][0] == pytest.approx(2.0)


def test_ase_concat_getitem_slice(three_ase_ios):
    io1, io2 = three_ase_ios
    cat = io1 + io2
    view = cat[1:]
    assert len(view) == 2
    atoms = list(view)
    assert all(isinstance(a, ase.Atoms) for a in atoms)


def test_ase_concat_flat(three_ase_ios):
    io1, io2 = three_ase_ios
    cat = io1 + io2
    assert len(cat._sources) == 2


def test_ase_concat_column_view_type(three_ase_ios):
    from asebytes._views import ASEColumnView

    io1, io2 = three_ase_ios
    cat = io1 + io2
    # str key returns ASEColumnView for ASEIO sources
    # (positions is a valid key stored in the row dict)
    assert cat._column_view_cls is ASEColumnView
```

**Step 2: Run to confirm new tests fail**

```
uv run pytest tests/test_concat_view.py::test_ase_concat_sum -v
```

Expected: `AttributeError: 'ASEIO' object has no attribute '__add__'`

**Step 3: Add `__add__` and `__radd__` to `ASEIO`**

In `src/asebytes/io.py`, add after the `__repr__` method (end of class, before any module-level code):

```python
    def __add__(self, other: Any) -> "ConcatView":
        from ._concat import ConcatView

        if isinstance(other, ConcatView):
            if type(other._sources[0]) is not type(self):
                raise TypeError(
                    f"Cannot concat {type(self).__name__} "
                    f"with {type(other._sources[0]).__name__}"
                )
            return ConcatView([self] + other._sources)
        if type(other) is not type(self):
            raise TypeError(
                f"Cannot concat {type(self).__name__} with {type(other).__name__}"
            )
        return ConcatView([self, other])

    def __radd__(self, other: Any) -> "ConcatView":
        if other == []:
            from ._concat import ConcatView

            return ConcatView([self])
        return NotImplemented
```

`Any` is already imported in `io.py` (from `typing`).

**Step 4: Run ASEIO tests**

```
uv run pytest tests/test_concat_view.py -k "ase" -v
```

Expected: all pass.

**Step 5: Commit**

```bash
git add src/asebytes/io.py tests/test_concat_view.py
git commit -m "feat: add ASEIO __add__/__radd__ for lazy concat"
```

---

### Task 3: `BlobIO` operator + tests

**Files:**
- Modify: `src/asebytes/_blob_io.py`
- Modify: `tests/test_concat_view.py`

---

**Step 1: Add BlobIO tests**

Append to `tests/test_concat_view.py`:

```python
# ---------------------------------------------------------------------------
# BlobIO concat
# ---------------------------------------------------------------------------

from asebytes import BlobIO


def _fresh_blob_io(rows: list[dict], tmp_path_factory) -> BlobIO:
    from asebytes.lmdb import LMDBBlobBackend

    p = str(tmp_path_factory.mktemp("blobio") / "data.lmdb")
    backend = LMDBBlobBackend(p)
    io = BlobIO(backend)
    for row in rows:
        io.append(row)
    return io


@pytest.fixture
def three_blob_ios(tmp_path_factory):
    io1 = _fresh_blob_io([{b"k": b"0"}, {b"k": b"1"}], tmp_path_factory)
    io2 = _fresh_blob_io([{b"k": b"2"}], tmp_path_factory)
    return io1, io2


def test_blob_concat_sum(three_blob_ios):
    io1, io2 = three_blob_ios
    cat = sum([io1, io2], [])
    assert isinstance(cat, ConcatView)
    assert len(cat) == 3


def test_blob_concat_iter(three_blob_ios):
    io1, io2 = three_blob_ios
    cat = io1 + io2
    rows = list(cat)
    assert rows == [{b"k": b"0"}, {b"k": b"1"}, {b"k": b"2"}]


def test_blob_concat_getitem_int(three_blob_ios):
    io1, io2 = three_blob_ios
    cat = io1 + io2
    assert cat[0] == {b"k": b"0"}
    assert cat[-1] == {b"k": b"2"}


def test_blob_concat_getitem_slice(three_blob_ios):
    io1, io2 = three_blob_ios
    cat = io1 + io2
    view = cat[1:]
    assert len(view) == 2


def test_blob_concat_flat(three_blob_ios):
    io1, io2 = three_blob_ios
    cat = io1 + io2
    assert len(cat._sources) == 2
```

**Step 2: Run to confirm failure**

```
uv run pytest tests/test_concat_view.py -k "blob" -v
```

Expected: `AttributeError: 'BlobIO' object has no attribute '__add__'`

**Step 3: Add `__add__` and `__radd__` to `BlobIO`**

In `src/asebytes/_blob_io.py`, add after the last method in the class (find `__repr__` or the last `def`; insert before the closing of the class):

```python
    def __add__(self, other: Any) -> "ConcatView":
        from ._concat import ConcatView

        if isinstance(other, ConcatView):
            if type(other._sources[0]) is not type(self):
                raise TypeError(
                    f"Cannot concat {type(self).__name__} "
                    f"with {type(other._sources[0]).__name__}"
                )
            return ConcatView([self] + other._sources)
        if type(other) is not type(self):
            raise TypeError(
                f"Cannot concat {type(self).__name__} with {type(other).__name__}"
            )
        return ConcatView([self, other])

    def __radd__(self, other: Any) -> "ConcatView":
        if other == []:
            from ._concat import ConcatView

            return ConcatView([self])
        return NotImplemented
```

**Step 4: Run BlobIO tests**

```
uv run pytest tests/test_concat_view.py -k "blob" -v
```

Expected: all pass.

**Step 5: Commit**

```bash
git add src/asebytes/_blob_io.py tests/test_concat_view.py
git commit -m "feat: add BlobIO __add__/__radd__ for lazy concat"
```

---

### Task 4: Export `ConcatView` + full test run

**Files:**
- Modify: `src/asebytes/__init__.py`

---

**Step 1: Add import and export**

In `src/asebytes/__init__.py`, add after the Views block (around line 49):

```python
# Concat
from ._concat import ConcatView
```

In the `__all__` list, add `"ConcatView"` in the Views section:

```python
    # Views
    "RowView",
    "ColumnView",
    "ASEColumnView",
    "ViewParent",
    "ConcatView",          # ← add this line
    ...
```

**Step 2: Verify the public import works**

```
uv run python -c "from asebytes import ConcatView; print(ConcatView)"
```

Expected: `<class 'asebytes._concat.ConcatView'>`

**Step 3: Run the full test suite**

```
uv run pytest tests/test_concat_view.py -v
```

Expected: all tests pass (no failures, no errors).

**Step 4: Run the broader test suite to check for regressions**

```
uv run pytest tests/ -x -q --ignore=tests/test_concat_view.py 2>&1 | tail -20
```

Expected: same pass/fail ratio as before this feature was added.

**Step 5: Final commit**

```bash
git add src/asebytes/__init__.py
git commit -m "feat: export ConcatView from asebytes public API"
```
