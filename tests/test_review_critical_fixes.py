"""Failing tests for critical bugs found in code review.

Each test targets a specific bug:
1. AsyncASEIO.insert() not calling atoms_to_dict
2. Sync ReadBackend.get_column() crashing on None (reserved) rows
3. MongoDB extend([]) returning None when cache uninitialised
5. AsyncColumnView.__len__() / __bool__() failing on unresolved indices
"""

from __future__ import annotations

import pytest

import ase


# ---------------------------------------------------------------------------
# Bug 1: AsyncASEIO.insert() missing atoms_to_dict conversion
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_async_aseio_insert_converts_atoms_to_dict():
    """AsyncASEIO.insert() should call atoms_to_dict, matching sync ASEIO.insert()."""
    from asebytes.memory import MemoryObjectBackend
    from asebytes import AsyncASEIO, SyncToAsyncAdapter

    backend = SyncToAsyncAdapter(MemoryObjectBackend())
    db = AsyncASEIO(backend)

    # Seed with one row so we can insert at index 0
    atoms = ase.Atoms("H2", positions=[[0, 0, 0], [0, 0, 0.74]])
    await db.extend([atoms])

    # Insert a second Atoms at index 0
    atoms2 = ase.Atoms("O", positions=[[1, 1, 1]])
    await db.insert(0, atoms2)

    # The raw backend should store a dict, not a raw Atoms object
    raw = await backend.get(0)
    assert isinstance(raw, dict), (
        f"Expected dict from atoms_to_dict, got {type(raw).__name__}"
    )
    # Verify round-trip: reading back via AsyncASEIO should give Atoms
    result = await db.get(0)
    assert isinstance(result, ase.Atoms)
    assert result.get_chemical_formula() == "O"


# ---------------------------------------------------------------------------
# Bug 2: Sync ReadBackend.get_column() crashes on None (reserved) rows
# ---------------------------------------------------------------------------


def test_sync_get_column_handles_none_reserved_rows():
    """ReadBackend.get_column() should return None for reserved (None) rows."""
    from asebytes.memory import MemoryObjectBackend

    backend = MemoryObjectBackend()
    backend.extend([{"x": 1}, None, {"x": 3}])

    # get_column should handle the None row gracefully, not crash
    result = backend.get_column("x", [0, 1, 2])
    assert result == [1, None, 3]


# ---------------------------------------------------------------------------
# Bug 3: MongoDB extend([]) returning None when cache uninitialised
# ---------------------------------------------------------------------------

import os
import uuid

pymongo = pytest.importorskip("pymongo")

from asebytes.mongodb import MongoObjectBackend, AsyncMongoObjectBackend

MONGO_URI = os.environ.get(
    "MONGO_URI", "mongodb://root:example@localhost:27017"
)


def _mongo_available():
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=1000)
        client.admin.command("ping")
        return True
    except Exception:
        return False


_skip_no_mongo = pytest.mark.skipif(
    not _mongo_available(), reason=f"MongoDB not available at {MONGO_URI}"
)


@_skip_no_mongo
def test_mongodb_extend_empty_returns_int_not_none():
    """MongoDB extend([]) on a fresh backend should return 0, not None."""
    col_name = f"test_{uuid.uuid4().hex[:8]}"
    backend = MongoObjectBackend(
        uri=MONGO_URI, database="asebytes_test", collection=col_name,
    )
    try:
        # extend([]) BEFORE any other operation — _count is still None
        result = backend.extend([])
        assert isinstance(result, int), (
            f"extend([]) returned {type(result).__name__}, expected int"
        )
        assert result == 0
    finally:
        backend.remove()


@_skip_no_mongo
def test_mongodb_extend_empty_returns_current_count():
    """MongoDB extend([]) after data exists should return current count."""
    col_name = f"test_{uuid.uuid4().hex[:8]}"
    backend = MongoObjectBackend(
        uri=MONGO_URI, database="asebytes_test", collection=col_name,
    )
    try:
        backend.extend([{"a": 1}, {"a": 2}])
        result = backend.extend([])
        assert result == 2
    finally:
        backend.remove()


@_skip_no_mongo
@pytest.mark.anyio
async def test_async_mongodb_extend_empty_returns_int_not_none():
    """Async MongoDB extend([]) on a fresh backend should return 0, not None."""
    col_name = f"test_{uuid.uuid4().hex[:8]}"
    backend = AsyncMongoObjectBackend(
        uri=MONGO_URI, database="asebytes_test", collection=col_name,
    )
    try:
        result = await backend.extend([])
        assert isinstance(result, int), (
            f"extend([]) returned {type(result).__name__}, expected int"
        )
        assert result == 0
    finally:
        await backend.remove()


# ---------------------------------------------------------------------------
# Bug 5: AsyncColumnView.__len__() and __bool__() fail on unresolved indices
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_async_column_view_len_unresolved_raises_clear_error():
    """AsyncColumnView.__len__() should raise clear TypeError when _indices is None."""
    from asebytes.memory import MemoryObjectBackend
    from asebytes import AsyncObjectIO, SyncToAsyncAdapter

    backend = SyncToAsyncAdapter(MemoryObjectBackend())
    db = AsyncObjectIO(backend)

    await db.extend([{"x": 1}, {"x": 2}, {"x": 3}])

    # db["x"] creates an AsyncColumnView with _indices=None
    col_view = db["x"]

    # Should raise TypeError with a helpful message
    with pytest.raises(TypeError, match="to_list"):
        len(col_view)


@pytest.mark.anyio
async def test_async_column_view_bool_unresolved_raises_clear_error():
    """AsyncColumnView.__bool__() should raise clear TypeError when _indices is None."""
    from asebytes.memory import MemoryObjectBackend
    from asebytes import AsyncObjectIO, SyncToAsyncAdapter

    backend = SyncToAsyncAdapter(MemoryObjectBackend())
    db = AsyncObjectIO(backend)

    await db.extend([{"x": 1}])
    col_view = db["x"]

    # Should raise TypeError with a helpful message
    with pytest.raises(TypeError, match="to_list"):
        bool(col_view)


@pytest.mark.anyio
async def test_async_column_view_len_with_explicit_indices_works():
    """AsyncColumnView.__len__() should work when indices are provided."""
    from asebytes.memory import MemoryObjectBackend
    from asebytes import AsyncObjectIO, SyncToAsyncAdapter

    backend = SyncToAsyncAdapter(MemoryObjectBackend())
    db = AsyncObjectIO(backend)

    await db.extend([{"x": 1}, {"x": 2}, {"x": 3}])

    # db[[0,1]]["x"] creates AsyncColumnView with explicit indices
    col_view = db[[0, 1]]["x"]
    assert len(col_view) == 2
    assert bool(col_view)
