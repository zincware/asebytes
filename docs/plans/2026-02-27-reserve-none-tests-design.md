# Design: reserve/None Tests for ReadWriteBackends

## Problem

`reserve(n)` and `None` placeholder handling has zero test coverage on concrete
backends (Zarr, H5MD, LMDB blob, LMDB object). The default `reserve`
implementation calls `extend([None] * n)`, but Zarr and H5MD iterate
`row.keys()` inside `extend` — meaning **reserve will crash** on those backends.
LMDB handles it (converts `None` → `{}`), but its `get()` returns `{}` instead
of `None` for reserved slots, which is also incorrect.

## Decided Semantics

- `get()` on a reserved (None) slot returns `None`
- `len()` counts reserved slots towards the total
- Iteration yields `None` for reserved slots (no skipping)
- `set()` on a reserved slot populates it normally

## Approach

Single parametrized test class in `tests/test_reserve_none.py`. A
`@pytest.fixture(params=[...])` yields `(backend, sample_row)` for each of the
4 ReadWriteBackend implementations. Each backend is pre-seeded with 2 real rows.

### Backends Under Test

| Param           | Class              | Key/Value types    |
|-----------------|--------------------|--------------------|
| `lmdb_blob`     | LMDBBlobBackend    | `bytes` / `bytes`  |
| `lmdb_object`   | LMDBObjectBackend  | `str` / `Any`      |
| `zarr`          | ZarrBackend        | `str` / `Any`      |
| `h5md`          | H5MDBackend        | `str` / `Any`      |

### Test Cases (10 tests × 4 backends = 40 parametrized runs)

**Core reserve semantics:**
1. `test_reserve_increases_len` — reserve(3) on 2-row backend → len == 5
2. `test_reserve_get_returns_none` — get() on reserved indices returns None
3. `test_reserve_original_data_intact` — original rows unaffected after reserve
4. `test_reserve_zero_is_noop` — reserve(0) changes nothing

**Iteration with None:**
5. `test_reserve_iteration_yields_none` — iterating produces [row, row, None, None, None]
6. `test_reserve_get_many_includes_none` — get_many returns None for reserved slots

**Populating reserved slots:**
7. `test_set_on_reserved_slot` — set() on a reserved slot works, others stay None
8. `test_reserve_then_extend` — extend after reserve appends beyond reserved range

**None in extend directly:**
9. `test_extend_with_none_entries` — extend([row, None, row]) handles inline None

**Edge case:**
10. `test_reserve_on_empty_backend` — reserve on fresh empty backend works

## Known Bugs This Will Surface

- **Zarr `extend`**: crashes on `None` rows (`AttributeError: 'NoneType' has no attribute 'keys'`)
- **H5MD `extend`**: same crash
- **LMDB `get`**: returns `{}` instead of `None` for reserved slots

## Out of Scope

- IO-layer tests (ASEIO, BytesIO, BlobIO) — they delegate to backend
- Async variants — covered separately once sync works
- `get_column` / `schema` behavior on None rows — future follow-up
