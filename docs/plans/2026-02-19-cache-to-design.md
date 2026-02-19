# Cache-To Middleware

## Overview

`ASEIO` gets a `cache_to` kwarg that creates a persistent read-through cache
backed by any `WritableBackend` (typically LMDB). On read, the cache is checked
first. On miss, the source is read and the result written to cache. After one
full pass all rows are cached and the source is never hit again.

## API

```python
# String path — auto-creates WritableBackend via registry
db = ASEIO("hf://colabfit/dataset", cache_to="cache.lmdb")

# Explicit backend instance
cache = LMDBBackend("cache.lmdb")
db = ASEIO("hf://colabfit/dataset", cache_to=cache)

# No cache (default, unchanged behavior)
db = ASEIO("hf://colabfit/dataset")
```

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Fill strategy | Lazy (on-demand) | No upfront cost. ML training naturally fills cache over one epoch. |
| Invalidation | None | Write-once per index. User deletes cache file to reset. Correct for immutable HF datasets. |
| Cache backend | Any WritableBackend | Flexible. LMDB recommended (fast random access, insert/replace). |
| In-memory caches | Keep | ASE/HF backends keep their in-memory LRU caches. They're cheap hot-path optimizations that help even without `cache_to`. |
| Architecture | ASEIO kwarg | `cache_to=` on ASEIO constructor. Creates internal ASEIO for cache reads/writes. |

## Read Flow

```
ASEIO.read_row(index, keys)
  → try cache_backend.read_row(index, keys)
  → on IndexError/KeyError: miss
    → source_backend.read_row(index)
    → cache_backend.write_row(index, full_row)
    → filter to keys, return
```

Key detail: on cache miss, we always read the **full row** from source and write
it to cache, even if the caller only requested specific keys. This ensures the
cache entry is complete for future reads with different key sets.

## Write Flow

Writes go to the **source** backend only. The cache is read-only from ASEIO's
perspective (it only writes on cache miss). If the source is read-only (e.g. HF),
ASEIO remains read-only regardless of cache_to.

## Length

`len(db)` delegates to the source backend, not the cache. The cache may be
partially filled.

## Changes

### `src/asebytes/io.py`

- Add `cache_to: str | WritableBackend | None = None` to `__init__`
- Store `self._cache: WritableBackend | None`
- Wrap `_read_row`, `_read_rows`, `_read_column` with cache logic
- `__len__` always delegates to source

### Tests

- `tests/test_cache_to.py` — full test suite
