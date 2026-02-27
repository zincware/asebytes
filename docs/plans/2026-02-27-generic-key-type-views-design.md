# Generic Key Type (`K`) for View Classes

## Problem

The backend layer is generic over key type: `ReadBackend[K, V]` where `K=str` for object backends and `K=bytes` for blob backends. The view layer (`RowView`, `ColumnView`, etc.) hardcodes `str` as the key type. `BlobIO` bridges the gap by decoding `bytes→str` at the IO boundary, then re-encoding `str→bytes` when calling the backend. This causes:

1. `blobdb[0:2][b"key"]` fails — `RowView.__getitem__` only accepts `str`
2. BlobIO's internal methods do pointless encode/decode round-trips
3. Type annotations lie — BlobIO views claim `str` keys but the data is `bytes`

## Design

Add a `K` TypeVar to all view classes, matching the backend pattern.

### Type parameters

```python
K = TypeVar("K", str, bytes)
```

| Class | Before | After |
|---|---|---|
| `ViewParent` | `Protocol[R]` | `Protocol[R, K]` |
| `RowView` | `Generic[R]` | `Generic[R, K]` |
| `ColumnView` | — | `Generic[K]` |
| `AsyncViewParent` | `Protocol[R]` | `Protocol[R, K]` |
| `AsyncSingleRowView` | `Generic[R]` | `Generic[R, K]` |
| `AsyncRowView` | `Generic[R]` | `Generic[R, K]` |
| `AsyncColumnView` | — | `Generic[K]` |
| `AsyncSingleColumnView` | — | `Generic[K]` |

`ASEColumnView` and `AsyncASEColumnView` remain subclasses with `K=str`.

### Protocol method signatures

All `str` key parameters become `K`:

```python
class ViewParent(Protocol[R, K]):
    def _read_row(self, index: int, keys: list[K] | None = None) -> ...: ...
    def _read_column(self, key: K, indices: list[int]) -> list[Any]: ...
    def _update_row(self, index: int, data: dict[K, Any]) -> None: ...
    def _drop_keys(self, keys: list[K], indices: list[int]) -> None: ...
    def _get_available_keys(self, index: int) -> list[K]: ...
```

Same for `AsyncViewParent[R, K]`.

### BlobIO stops decoding

BlobIO, AsyncBlobIO, and AsyncBytesIO currently encode/decode between str and bytes in every `_read_row`, `_read_rows`, `_read_column`, `_update_row`, and `_drop_keys`. After this change, they pass `bytes` keys through to the backend directly:

```python
# Before
def _read_row(self, index, keys: list[str] | None = None):
    byte_keys = [k.encode() for k in keys] if keys else None
    row = self._backend.get(index, byte_keys)
    return {k: row.get(k.encode()) for k in keys}

# After
def _read_row(self, index, keys: list[bytes] | None = None):
    return self._backend.get(index, keys)
```

### IO class key types

Each IO class only accepts its native key type:

| IO Class | Key type | Row result `R` |
|---|---|---|
| ASEIO | `str` | `ase.Atoms` |
| ObjectIO | `str` | `dict[str, Any]` |
| BlobIO | `bytes` | `dict[bytes, bytes]` |
| AsyncASEIO | `str` | `ase.Atoms \| None` |
| AsyncObjectIO | `str` | `dict[str, Any] \| None` |
| AsyncBlobIO | `bytes` | `dict[bytes, bytes] \| None` |
| AsyncBytesIO | `bytes` | `dict[bytes, bytes] \| None` |

BlobIO stops accepting `str` keys. ObjectIO stops accepting `bytes` keys.

### View `__getitem__` accepts `K`

```python
class RowView(Generic[R, K]):
    @overload
    def __getitem__(self, key: K) -> ColumnView[K]: ...
    @overload
    def __getitem__(self, key: list[K]) -> ColumnView[K]: ...
```

`blobdb[0:2][b"key"]` works because `K=bytes`. `objdb[0:2]["key"]` works because `K=str`.

### AsyncSingleRowView subscripting

```python
class AsyncSingleRowView(Generic[R, K]):
    def __getitem__(self, key: K | list[K]) -> AsyncSingleColumnView[K]: ...
```

## Files modified

| File | Changes |
|---|---|
| `_views.py` | Add `K` to `ViewParent`, `RowView`, `ColumnView` |
| `_async_views.py` | Add `K` to `AsyncViewParent`, `AsyncSingleRowView`, `AsyncRowView`, `AsyncColumnView`, `AsyncSingleColumnView` |
| `_blob_io.py` | Remove bytes↔str encoding. Accept `bytes` natively. |
| `_async_blob_io.py` | Remove encoding, native bytes. |
| `_async_bytesio.py` | Remove encoding, native bytes. |
| `io.py` | Update annotations to `K=str` |
| `_object_io.py` | Update annotations to `K=str` |
| `_async_io.py` | Update annotations to `K=str` |
| `_async_object_io.py` | Update annotations to `K=str` |
| Test mock parents | Update key type annotations where needed |

## Verification

```bash
uv run pytest tests/ -x --ignore=tests/test_benchmark_backend.py --ignore=tests/test_hf_aseio.py
```

Key behavioral expectations:
- `blobdb[b"key"][0]` returns bytes value (not str-keyed dict)
- `blobdb[0:2][b"key"]` returns `ColumnView[bytes]` (currently fails)
- `blobdb[0][b"key"]` returns bytes value
- `await ablobdb[0][b"key"]` returns bytes value
- `objdb["key"][0]` still returns value (unchanged)
- `objdb[0:2]["key"]` returns `ColumnView[str]` (unchanged)
