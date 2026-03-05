# Lazy Concatenation for IO Facades

**Date:** 2026-03-05
**Branch:** perf-analysis

## Problem

`ObjectIO`, `ASEIO`, and `BlobIO` do not support `+` or `sum([io1, io2, io3], [])`.
Users want to concatenate multiple IO objects into a single lazy read-only sequence
without materializing data into memory.

## Requirements

- Read-only lazy concatenation across all three facades (ObjectIO, ASEIO, BlobIO)
- Full interface: `__len__`, `__iter__`, `__getitem__` (int, slice, list[int], str, list[str])
- Operator API only: `io1 + io2 + io3` and `sum([io1, io2, io3], [])`
- Flat chaining: `(io1 + io2) + io3` results in one `ConcatView` with 3 sources, not nested views
- Type-homogeneous: cannot concat different IO classes (raises `TypeError`)

## Design

### New file: `src/asebytes/_concat.py`

`ConcatView` implements the `ViewParent` protocol so that existing `RowView`,
`ColumnView`, and `ASEColumnView` machinery works without modification.

```python
class ConcatView(Generic[T]):
    _sources: list[IO]          # flat list, all same IO subclass
    _column_view_cls: type      # ColumnView or ASEColumnView

    def __len__(self) -> int    # sum(len(s) for s in _sources)
    def _locate(self, global_idx) -> tuple[int, int]   # O(n_sources), no cache
    def _read_row(self, i, keys=None) -> dict
    def _read_rows(self, indices, keys=None) -> list[dict]   # batched per source
    def _iter_rows(self, indices, keys=None) -> Iterator[dict]
    def _read_column(self, key, indices) -> list        # batched per source
    def _build_result(self, row) -> T                   # delegates to sources[0]
    def __getitem__(self, index) -> T | RowView | ColumnView
    def __iter__(self) -> Iterator[T]
    def __add__(self, other) -> ConcatView              # flattens ConcatView sources
    def __radd__(self, other) -> ConcatView             # accepts [] seed for sum()
```

Write methods (`_write_row`, `_update_row`, `_delete_row`, `_delete_rows`,
`_drop_keys`, `_update_many`, `_set_column`, `_write_many`) raise `TypeError("ConcatView is read-only")`.

### Index mapping

`_locate(global_idx)` iterates sources computing cumulative offset. O(n_sources),
recomputed on every call (no caching — another client may modify backend length).

`_read_rows` and `_read_column` group indices by source using `defaultdict(list)`,
preserving output order. Each source batch calls the source's own `_read_rows` /
`_read_column` for efficient I/O.

### Operator methods on IO classes

Each of `ObjectIO`, `ASEIO`, `BlobIO` gets:

```python
def __add__(self, other):
    if type(other) is not type(self):
        raise TypeError(...)
    from ._concat import ConcatView
    return ConcatView([self, other])

def __radd__(self, other):
    if other == []:
        from ._concat import ConcatView
        return ConcatView([self])
    return NotImplemented
```

`ConcatView.__add__` flattens: if `other` is a `ConcatView`, extend `_sources`;
otherwise append. Type check at every `__add__`.

### Type safety

`ConcatView.__init__` checks that all sources share the same `type()`. Enforced
at every `__add__` call as well. Mixed-type concat raises `TypeError`.

### Column view dispatch

`_column_view_cls` is set at construction:
```python
from .io import ASEIO
self._column_view_cls = ASEColumnView if isinstance(sources[0], ASEIO) else ColumnView
```

`__getitem__(str)` uses `self._column_view_cls`.

### Exports

`ConcatView` added to `src/asebytes/__init__.py`.

## Testing

`tests/test_concat_view.py` covers:

- `sum([io1, io2, io3], [])` round-trips for ObjectIO, ASEIO, BlobIO
- `__len__` equals sum of source lengths
- `__getitem__(int)` — positive, negative, out-of-bounds
- `__getitem__(slice)` → RowView with correct rows
- `__getitem__(str)` → ColumnView with correct values (ObjectIO/ASEIO)
- `io1 + io2 + io3` is flat (`len(concat._sources) == 3`)
- `ConcatView + ConcatView` is flat
- Mixed-type concat raises `TypeError`
- Write ops raise `TypeError`
- `_read_rows` with indices spanning multiple sources preserves order

Fixtures reuse conftest memory/tmp backends.

## Files changed

| File | Change |
|------|--------|
| `src/asebytes/_concat.py` | New — `ConcatView` |
| `src/asebytes/_object_io.py` | Add `__add__`, `__radd__` |
| `src/asebytes/io.py` | Add `__add__`, `__radd__` |
| `src/asebytes/_blob_io.py` | Add `__add__`, `__radd__` |
| `src/asebytes/__init__.py` | Export `ConcatView` |
| `tests/test_concat_view.py` | New — full test suite |
