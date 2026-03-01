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

    backend = SyncToAsyncAdapter(
        MemoryObjectBackend(group=f"test_{uuid.uuid4().hex[:8]}")
    )
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

import uuid

pymongo = pytest.importorskip("pymongo")

from asebytes.mongodb import MongoObjectBackend, AsyncMongoObjectBackend



def test_mongodb_extend_empty_returns_int_not_none(mongo_uri):
    """MongoDB extend([]) on a fresh backend should return 0, not None."""
    col_name = f"test_{uuid.uuid4().hex[:8]}"
    backend = MongoObjectBackend(
        uri=mongo_uri,
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


def test_mongodb_extend_empty_returns_current_count(mongo_uri):
    """MongoDB extend([]) after data exists should return current count."""
    col_name = f"test_{uuid.uuid4().hex[:8]}"
    backend = MongoObjectBackend(
        uri=mongo_uri,
        database="asebytes_test",
        group=col_name,
    )
    try:
        backend.extend([{"a": 1}, {"a": 2}])
        result = backend.extend([])
        assert result == 2
    finally:
        backend.remove()


@pytest.mark.anyio
async def test_async_mongodb_extend_empty_returns_int_not_none(mongo_uri):
    """Async MongoDB extend([]) on a fresh backend should return 0, not None."""
    col_name = f"test_{uuid.uuid4().hex[:8]}"
    backend = AsyncMongoObjectBackend(
        uri=mongo_uri,
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

    backend = SyncToAsyncAdapter(
        MemoryObjectBackend(group=f"test_{uuid.uuid4().hex[:8]}")
    )
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

    backend = SyncToAsyncAdapter(
        MemoryObjectBackend(group=f"test_{uuid.uuid4().hex[:8]}")
    )
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

    backend = SyncToAsyncAdapter(
        MemoryObjectBackend(group=f"test_{uuid.uuid4().hex[:8]}")
    )
    db = AsyncObjectIO(backend)

    await db.extend([{"x": 1}, {"x": 2}, {"x": 3}])

    # db[[0,1]]["x"] creates AsyncColumnView with explicit indices
    col_view = db[[0, 1]]["x"]
    assert len(col_view) == 2
    assert bool(col_view)


# ---------------------------------------------------------------------------
# Bug 6: ObjectIO("mongodb://...") fails with numpy array data
# ---------------------------------------------------------------------------


def test_objectio_mongodb_with_numpy_arrays(mongo_uri):
    """ObjectIO with mongodb:// URI must handle numpy arrays in data.

    atoms_to_dict() produces numpy arrays for positions, numbers, forces, etc.
    These must be serializable by the MongoDB backend. Plain MongoObjectBackend
    with pymongo BSON cannot encode numpy arrays, so the facade must handle
    serialization (e.g. via an adapter or in the backend itself).
    """
    import numpy as np
    from asebytes import ObjectIO

    col_name = f"test_{uuid.uuid4().hex[:8]}"
    after_scheme = mongo_uri.split("://", 1)[1]
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


def test_aseio_mongodb_roundtrip(mongo_uri):
    """ASEIO with mongodb:// URI must roundtrip ase.Atoms objects.

    This is the end-to-end test: create Atoms with calculator results,
    store via ASEIO("mongodb://..."), read back, verify.
    """
    import numpy as np
    from asebytes import ASEIO
    import ase.calculators.singlepoint

    col_name = f"test_{uuid.uuid4().hex[:8]}"
    after_scheme = mongo_uri.split("://", 1)[1]
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


@pytest.mark.anyio
async def test_async_objectio_mongodb_with_numpy_arrays(mongo_uri):
    """AsyncObjectIO with mongodb:// URI must handle numpy arrays."""
    import numpy as np
    from asebytes import AsyncObjectIO

    col_name = f"test_{uuid.uuid4().hex[:8]}"
    after_scheme = mongo_uri.split("://", 1)[1]
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


# ---------------------------------------------------------------------------
# MongoDB update/update_many/set_column should materialize placeholder rows
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_mongodb_update_materializes_placeholder(mongo_uri):
    """MongoDB update() on placeholder row should update data field correctly."""
    col_name = f"test_{uuid.uuid4().hex[:8]}"
    backend = AsyncMongoObjectBackend(
        uri=mongo_uri,
        database="asebytes_test",
        group=col_name,
    )
    try:
        # Create sparse data: real doc at 0, placeholder (None) at 1, real doc at 2
        await backend.extend([{"x": 1}, None, {"x": 3}])

        # Verify placeholder exists (should return None)
        row1_before = await backend.get(1)
        assert row1_before is None

        # Update the placeholder - should convert data from null to dict
        await backend.update(1, {"y": 42})

        # Now the row should have the updated data
        row1_after = await backend.get(1)
        assert row1_after is not None
        assert row1_after.get("y") == 42
    finally:
        await backend.aclose()
        # Clean up
        client = pymongo.AsyncMongoClient(mongo_uri)
        await client["asebytes_test"][col_name].drop()
        await client.close()


@pytest.mark.anyio
async def test_mongodb_update_many_materializes_placeholders(mongo_uri):
    """MongoDB update_many() on placeholder rows should update data correctly."""
    col_name = f"test_{uuid.uuid4().hex[:8]}"
    backend = AsyncMongoObjectBackend(
        uri=mongo_uri,
        database="asebytes_test",
        group=col_name,
    )
    try:
        # Create sparse data: real doc at 0, placeholders at 1-2, real doc at 3
        await backend.extend([{"x": 0}, None, None, {"x": 3}])

        # Update the placeholders - should convert data from null to dict
        await backend.update_many(1, [{"a": 1}, {"b": 2}])

        # Now the rows should have the updated data
        row1 = await backend.get(1)
        row2 = await backend.get(2)
        assert row1 is not None
        assert row1.get("a") == 1
        assert row2 is not None
        assert row2.get("b") == 2
    finally:
        await backend.aclose()
        client = pymongo.AsyncMongoClient(mongo_uri)
        await client["asebytes_test"][col_name].drop()
        await client.close()


@pytest.mark.anyio
async def test_mongodb_set_column_materializes_placeholders(mongo_uri):
    """MongoDB set_column() on placeholder rows should update data correctly."""
    col_name = f"test_{uuid.uuid4().hex[:8]}"
    backend = AsyncMongoObjectBackend(
        uri=mongo_uri,
        database="asebytes_test",
        group=col_name,
    )
    try:
        # Create sparse data: real doc at 0, placeholders at 1-2, real doc at 3
        await backend.extend([{"x": 0}, None, None, {"x": 3}])

        # set_column on placeholders - should convert data from null to dict
        await backend.set_column("val", 1, [10, 20])

        # Now the rows should have the updated data
        row1 = await backend.get(1)
        row2 = await backend.get(2)
        assert row1 is not None
        assert row1.get("val") == 10
        assert row2 is not None
        assert row2.get("val") == 20
    finally:
        await backend.aclose()
        client = pymongo.AsyncMongoClient(mongo_uri)
        await client["asebytes_test"][col_name].drop()
        await client.close()


# ---------------------------------------------------------------------------
# Bug: AsyncViews don't handle None rows gracefully
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_async_row_view_to_list_handles_none_rows():
    """AsyncRowView.to_list() should handle None placeholder rows."""
    from asebytes.memory import MemoryObjectBackend
    from asebytes import AsyncObjectIO, SyncToAsyncAdapter

    backend = SyncToAsyncAdapter(
        MemoryObjectBackend(group=f"test_{uuid.uuid4().hex[:8]}")
    )
    db = AsyncObjectIO(backend)

    # Create sparse data with None placeholder at index 1
    await db.extend([{"x": 1}, None, {"x": 3}])

    # to_list should work and return None for placeholder
    result = await db[:].to_list()
    assert len(result) == 3
    assert result[0] == {"x": 1}
    assert result[1] is None
    assert result[2] == {"x": 3}


@pytest.mark.anyio
async def test_async_row_view_aiter_handles_none_rows():
    """AsyncRowView.__aiter__() should handle None placeholder rows."""
    from asebytes.memory import MemoryObjectBackend
    from asebytes import AsyncObjectIO, SyncToAsyncAdapter

    backend = SyncToAsyncAdapter(
        MemoryObjectBackend(group=f"test_{uuid.uuid4().hex[:8]}")
    )
    db = AsyncObjectIO(backend)

    await db.extend([{"x": 1}, None, {"x": 3}])

    result = [row async for row in db[:]]
    assert len(result) == 3
    assert result[0] == {"x": 1}
    assert result[1] is None
    assert result[2] == {"x": 3}


@pytest.mark.anyio
async def test_async_column_view_to_list_handles_none_rows():
    """AsyncColumnView.to_list() with multi-key should handle None rows."""
    from asebytes.memory import MemoryObjectBackend
    from asebytes import AsyncObjectIO, SyncToAsyncAdapter

    backend = SyncToAsyncAdapter(
        MemoryObjectBackend(group=f"test_{uuid.uuid4().hex[:8]}")
    )
    db = AsyncObjectIO(backend)

    await db.extend([{"x": 1, "y": 2}, None, {"x": 3, "y": 4}])

    # Multi-key column view
    result = await db[["x", "y"]].to_list()
    assert len(result) == 3
    assert result[0] == [1, 2]
    assert result[1] is None  # None row stays None (consistent with ASE views)
    assert result[2] == [3, 4]


@pytest.mark.anyio
async def test_async_column_view_aiter_handles_none_rows():
    """AsyncColumnView.__aiter__() with multi-key should handle None rows."""
    from asebytes.memory import MemoryObjectBackend
    from asebytes import AsyncObjectIO, SyncToAsyncAdapter

    backend = SyncToAsyncAdapter(
        MemoryObjectBackend(group=f"test_{uuid.uuid4().hex[:8]}")
    )
    db = AsyncObjectIO(backend)

    await db.extend([{"x": 1, "y": 2}, None, {"x": 3, "y": 4}])

    result = [row async for row in db[["x", "y"]]]
    assert len(result) == 3
    assert result[0] == [1, 2]
    assert result[1] is None  # None row stays None (consistent with ASE views)
    assert result[2] == [3, 4]


@pytest.mark.anyio
async def test_async_ase_column_view_to_list_handles_none_rows():
    """AsyncASEColumnView.to_list() should handle None placeholder rows."""
    from asebytes.memory import MemoryObjectBackend
    from asebytes import AsyncASEIO, AsyncObjectIO, SyncToAsyncAdapter
    from asebytes._convert import atoms_to_dict

    backend = SyncToAsyncAdapter(
        MemoryObjectBackend(group=f"test_{uuid.uuid4().hex[:8]}")
    )
    # Use ObjectIO to insert raw data including None (simulating placeholder rows)
    raw_db = AsyncObjectIO(backend)
    atoms = ase.Atoms("H2", positions=[[0, 0, 0], [0, 0, 0.74]])
    await raw_db.extend([atoms_to_dict(atoms), None, atoms_to_dict(atoms)])

    # Now read through ASEIO which wraps rows with dict_to_atoms
    db = AsyncASEIO(backend)
    result = await db[:].to_list()
    assert len(result) == 3
    assert isinstance(result[0], ase.Atoms)
    assert result[1] is None
    assert isinstance(result[2], ase.Atoms)


@pytest.mark.anyio
async def test_async_ase_column_view_aiter_handles_none_rows():
    """AsyncASEColumnView.__aiter__() should handle None placeholder rows."""
    from asebytes.memory import MemoryObjectBackend
    from asebytes import AsyncASEIO, AsyncObjectIO, SyncToAsyncAdapter
    from asebytes._convert import atoms_to_dict

    backend = SyncToAsyncAdapter(
        MemoryObjectBackend(group=f"test_{uuid.uuid4().hex[:8]}")
    )
    # Use ObjectIO to insert raw data including None (simulating placeholder rows)
    raw_db = AsyncObjectIO(backend)
    atoms = ase.Atoms("H2", positions=[[0, 0, 0], [0, 0, 0.74]])
    await raw_db.extend([atoms_to_dict(atoms), None, atoms_to_dict(atoms)])

    # Now read through ASEIO which wraps rows with dict_to_atoms
    db = AsyncASEIO(backend)
    result = [row async for row in db[:]]
    assert len(result) == 3
    assert isinstance(result[0], ase.Atoms)
    assert result[1] is None
    assert isinstance(result[2], ase.Atoms)


# ---------------------------------------------------------------------------
# ObjectIO context manager should close backend
# ---------------------------------------------------------------------------


def test_objectio_context_manager_closes_backend():
    """ObjectIO.__exit__() should close backend if it has a close() method."""

    class ClosableBackend:
        """Mock backend with close method to track calls."""

        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

        def __len__(self):
            return 0

    from asebytes import ObjectIO

    backend = ClosableBackend()
    io = ObjectIO(backend)

    with io:
        pass

    assert backend.closed, "Backend.close() should be called on __exit__"


def test_objectio_context_manager_tolerates_no_close():
    """ObjectIO.__exit__() should not fail if backend has no close() method."""
    from asebytes.memory import MemoryObjectBackend
    from asebytes import ObjectIO

    backend = MemoryObjectBackend(group=f"test_{uuid.uuid4().hex[:8]}")
    io = ObjectIO(backend)

    with io:
        pass
    # No error should occur


@pytest.mark.anyio
async def test_async_objectio_context_manager_closes_backend():
    """AsyncObjectIO.__aexit__() should close backend if it has close()/aclose()."""

    class AsyncClosableBackend:
        """Mock async backend with aclose method."""

        def __init__(self):
            self.closed = False

        async def aclose(self):
            self.closed = True

        def __len__(self):
            return 0

    from asebytes import AsyncObjectIO

    backend = AsyncClosableBackend()
    io = AsyncObjectIO(backend)

    async with io:
        pass

    assert backend.closed, "Backend.aclose() should be called on __aexit__"


# ---------------------------------------------------------------------------
# Sync Views multi-key column reads should handle None rows
# ---------------------------------------------------------------------------


def test_sync_column_view_to_list_handles_none_rows():
    """ColumnView.to_list() with multi-key should handle None rows."""
    from asebytes.memory import MemoryObjectBackend
    from asebytes import ObjectIO

    backend = MemoryObjectBackend(group=f"test_{uuid.uuid4().hex[:8]}")
    db = ObjectIO(backend)

    db.extend([{"x": 1, "y": 2}, None, {"x": 3, "y": 4}])

    # Multi-key column view
    result = db[["x", "y"]][:].to_list()
    assert len(result) == 3
    assert result[0] == [1, 2]
    assert result[1] is None  # None row stays None
    assert result[2] == [3, 4]


def test_sync_column_view_iter_handles_none_rows():
    """ColumnView.__iter__() with multi-key should handle None rows."""
    from asebytes.memory import MemoryObjectBackend
    from asebytes import ObjectIO

    backend = MemoryObjectBackend(group=f"test_{uuid.uuid4().hex[:8]}")
    db = ObjectIO(backend)

    db.extend([{"x": 1, "y": 2}, None, {"x": 3, "y": 4}])

    result = list(db[["x", "y"]][:])
    assert len(result) == 3
    assert result[0] == [1, 2]
    assert result[1] is None
    assert result[2] == [3, 4]


def test_sync_column_view_getitem_handles_none_row():
    """ColumnView[int] should handle None rows."""
    from asebytes.memory import MemoryObjectBackend
    from asebytes import ObjectIO

    backend = MemoryObjectBackend(group=f"test_{uuid.uuid4().hex[:8]}")
    db = ObjectIO(backend)

    db.extend([{"x": 1, "y": 2}, None, {"x": 3, "y": 4}])

    # Direct access to None row
    result = db[["x", "y"]][:][1]
    assert result is None


# ---------------------------------------------------------------------------
# H5MD bulk write should apply per-atom padding
# ---------------------------------------------------------------------------


def test_h5md_set_column_applies_padding(tmp_path):
    """H5MD set_column should pad per-atom arrays to max_atoms.

    Note: get() uses _n_atoms to slice per-atom data on read,
    so we verify padding by checking the raw HDF5 dataset directly.
    """
    import numpy as np
    from asebytes.h5md import H5MDBackend
    from asebytes._columnar import get_fill_value

    path = tmp_path / "test.h5"
    backend = H5MDBackend(path, readonly=False)

    # First, extend with varying atom counts to establish max_atoms
    # Use float arrays so NaN fill is used (matching typical positions dtype)
    backend.extend(
        [
            {
                "arrays.positions": np.array(
                    [[0, 0, 0], [1, 1, 1], [2, 2, 2]], dtype=np.float64
                )
            },  # 3 atoms
            {
                "arrays.positions": np.array(
                    [[0, 0, 0], [1, 1, 1]], dtype=np.float64
                )
            },  # 2 atoms
        ]
    )

    # Now use set_column with a smaller array - should be padded
    backend.set_column("arrays.positions", 1, [np.array([[5, 5, 5]], dtype=np.float64)])  # 1 atom

    # Verify padding was applied by checking raw HDF5 data
    h5_path = backend._find_dataset_path("arrays.positions")
    ds = backend._file[h5_path]["value"]
    raw_data = ds[1]  # Row 1

    # Should have 3 atoms in storage (padded to max_atoms)
    assert raw_data.shape[0] == 3
    # First atom should be our data
    np.testing.assert_array_equal(raw_data[0], [5, 5, 5])
    # Remaining should be filled with dtype-appropriate fill value
    fv = get_fill_value(ds.dtype)
    if np.isnan(fv):
        assert np.all(np.isnan(raw_data[1:]))
    else:
        assert np.all(raw_data[1:] == fv)

    backend.close()


def test_h5md_update_many_applies_padding(tmp_path):
    """H5MD update_many should pad per-atom arrays to max_atoms.

    Note: get() uses _n_atoms to slice per-atom data on read,
    so we verify padding by checking the raw HDF5 dataset directly.
    """
    import numpy as np
    from asebytes.h5md import H5MDBackend
    from asebytes._columnar import get_fill_value

    path = tmp_path / "test.h5"
    backend = H5MDBackend(path, readonly=False)

    # First, extend with varying atom counts to establish max_atoms
    # Use float arrays so NaN fill is used (matching typical positions dtype)
    backend.extend(
        [
            {
                "arrays.positions": np.array(
                    [[0, 0, 0], [1, 1, 1], [2, 2, 2]], dtype=np.float64
                )
            },  # 3 atoms
            {
                "arrays.positions": np.array(
                    [[0, 0, 0], [1, 1, 1]], dtype=np.float64
                )
            },  # 2 atoms
        ]
    )

    # Now use update_many with a smaller array - should be padded
    backend.update_many(1, [{"arrays.positions": np.array([[5, 5, 5]], dtype=np.float64)}])  # 1 atom

    # Verify padding was applied by checking raw HDF5 data
    h5_path = backend._find_dataset_path("arrays.positions")
    ds = backend._file[h5_path]["value"]
    raw_data = ds[1]  # Row 1

    # Should have 3 atoms in storage (padded to max_atoms)
    assert raw_data.shape[0] == 3
    # First atom should be our data
    np.testing.assert_array_equal(raw_data[0], [5, 5, 5])
    # Remaining should be filled with dtype-appropriate fill value
    fv = get_fill_value(ds.dtype)
    if np.isnan(fv):
        assert np.all(np.isnan(raw_data[1:]))
    else:
        assert np.all(raw_data[1:] == fv)

    backend.close()
