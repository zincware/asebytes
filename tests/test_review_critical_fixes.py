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
    import uuid
    from asebytes.memory import MemoryObjectBackend

    # Use unique group for test isolation
    backend = MemoryObjectBackend(group=f"test_{uuid.uuid4().hex[:8]}")
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

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://root:example@localhost:27017")


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
        uri=MONGO_URI,
        database="asebytes_test",
        group=col_name,
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
        uri=MONGO_URI,
        database="asebytes_test",
        group=col_name,
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
        uri=MONGO_URI,
        database="asebytes_test",
        group=col_name,
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


# ---------------------------------------------------------------------------
# Bug 6: ObjectIO("mongodb://...") fails with numpy array data
# ---------------------------------------------------------------------------


@_skip_no_mongo
def test_objectio_mongodb_with_numpy_arrays():
    """ObjectIO with mongodb:// URI must handle numpy arrays in data.

    atoms_to_dict() produces numpy arrays for positions, numbers, forces, etc.
    These must be serializable by the MongoDB backend. Plain MongoObjectBackend
    with pymongo BSON cannot encode numpy arrays, so the facade must handle
    serialization (e.g. via an adapter or in the backend itself).
    """
    import numpy as np
    from asebytes import ObjectIO

    col_name = f"test_{uuid.uuid4().hex[:8]}"
    after_scheme = MONGO_URI.split("://", 1)[1]
    uri = f"mongodb://{after_scheme}/asebytes_test/{col_name}"

    db = ObjectIO(uri)
    try:
        row = {
            "arrays.positions": np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]),
            "arrays.numbers": np.array([1, 8]),
            "calc.energy": -10.5,
            "calc.forces": np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]),
            "cell": np.zeros((3, 3)),
            "pbc": np.array([False, False, False]),
        }
        db.extend([row])
        assert len(db) == 1

        # Read back and verify numpy arrays round-trip correctly
        result = db[0]
        assert result["calc.energy"] == pytest.approx(-10.5)
        assert isinstance(result["arrays.positions"], (list, np.ndarray))
        if isinstance(result["arrays.positions"], np.ndarray):
            np.testing.assert_array_almost_equal(
                result["arrays.positions"],
                np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]),
            )
    finally:
        db.remove()


@_skip_no_mongo
def test_aseio_mongodb_roundtrip():
    """ASEIO with mongodb:// URI must roundtrip ase.Atoms objects.

    This is the end-to-end test: create Atoms with calculator results,
    store via ASEIO("mongodb://..."), read back, verify.
    """
    import numpy as np
    from asebytes import ASEIO
    import ase.calculators.singlepoint

    col_name = f"test_{uuid.uuid4().hex[:8]}"
    after_scheme = MONGO_URI.split("://", 1)[1]
    uri = f"mongodb://{after_scheme}/asebytes_test/{col_name}"

    db = ASEIO(uri)
    try:
        atoms = ase.Atoms("H2O", positions=[[0, 0, 0], [0, 0, 1], [1, 0, 0]])
        atoms.calc = ase.calculators.singlepoint.SinglePointCalculator(
            atoms, energy=-10.5, forces=[[0, 0, 0]] * 3
        )
        db.extend([atoms])
        assert len(db) == 1

        result = db[0]
        assert isinstance(result, ase.Atoms)
        assert result.calc.results["energy"] == pytest.approx(-10.5)
        np.testing.assert_array_almost_equal(
            result.get_positions(),
            np.array([[0, 0, 0], [0, 0, 1], [1, 0, 0]], dtype=float),
        )
    finally:
        db.remove()


@_skip_no_mongo
@pytest.mark.anyio
async def test_async_objectio_mongodb_with_numpy_arrays():
    """AsyncObjectIO with mongodb:// URI must handle numpy arrays."""
    import numpy as np
    from asebytes import AsyncObjectIO

    col_name = f"test_{uuid.uuid4().hex[:8]}"
    after_scheme = MONGO_URI.split("://", 1)[1]
    uri = f"mongodb://{after_scheme}/asebytes_test/{col_name}"

    db = AsyncObjectIO(uri)
    try:
        row = {
            "arrays.positions": np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]),
            "arrays.numbers": np.array([1, 8]),
            "calc.energy": -10.5,
        }
        await db.extend([row])
        assert await db.len() == 1

        result = await db[0]
        assert result["calc.energy"] == pytest.approx(-10.5)
    finally:
        await db.remove()
