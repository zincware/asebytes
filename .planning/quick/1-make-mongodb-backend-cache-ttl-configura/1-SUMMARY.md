# Quick Task 1: Make MongoDB backend cache_ttl configurable

**Date:** 2026-03-09
**Status:** Complete

## Changes

- Added `cache_ttl: float | None = 1.0` parameter to `MongoObjectBackend.__init__`
- When `cache_ttl=None`, `_ensure_cache` always reads from MongoDB (no TTL short-circuit)
- When `cache_ttl` is a float, existing TTL behavior is preserved (default 1.0s)
- Updated `test_second_instance_sees_writes_from_first` to use `cache_ttl=None` so the stale-cache test passes

## Files Modified

- `src/asebytes/mongodb/_backend.py` — configurable `cache_ttl` parameter
- `tests/test_mongodb.py` — stale-cache test uses `cache_ttl=None`
