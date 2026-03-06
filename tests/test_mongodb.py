import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pytest

import pymongo  # noqa: F401 -- import ensures pymongo is available (fail, not skip)

from asebytes._backends import ReadBackend, ReadWriteBackend
from asebytes._async_backends import AsyncReadBackend, AsyncReadWriteBackend
from asebytes.mongodb import AsyncMongoObjectBackend, MongoObjectBackend



@pytest.fixture
def backend(mongo_uri):
    """Create a backend with a unique group, drop it after the test."""
    group_name = f"test_{uuid.uuid4().hex[:8]}"
    b = MongoObjectBackend(
        uri=mongo_uri,
        database="asebytes_test",
        group=group_name,
    )
    yield b
    b.remove()


@pytest.fixture
def sample_row():
    return {
        "energy": -10.5,
        "smiles": "O",
        "numbers": [1, 8],
        "positions": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
    }


def test_is_writable_backend(backend):
    assert isinstance(backend, ReadWriteBackend)
    assert isinstance(backend, ReadBackend)


def test_empty_len(backend):
    assert len(backend) == 0


def test_extend_and_get(backend, sample_row):
    backend.extend([sample_row])
    assert len(backend) == 1
    row = backend.get(0)
    assert row["energy"] == pytest.approx(-10.5)
    assert row["smiles"] == "O"
    assert row["numbers"] == [1, 8]


def test_get_with_keys(backend, sample_row):
    backend.extend([sample_row])
    row = backend.get(0, keys=["energy", "smiles"])
    assert "energy" in row
    assert "smiles" in row
    assert "positions" not in row


def test_keys(backend, sample_row):
    backend.extend([sample_row])
    cols = backend.keys(0)
    assert "energy" in cols
    assert "positions" in cols


def test_extend_multiple(backend, sample_row):
    backend.extend([sample_row, sample_row, sample_row])
    assert len(backend) == 3


def test_insert(backend, sample_row):
    row_a = {**sample_row, "energy": -1.0}
    row_b = {**sample_row, "energy": -2.0}
    row_c = {**sample_row, "energy": -3.0}
    backend.extend([row_a, row_c])
    backend.insert(1, row_b)
    assert len(backend) == 3
    assert backend.get(0)["energy"] == pytest.approx(-1.0)
    assert backend.get(1)["energy"] == pytest.approx(-2.0)
    assert backend.get(2)["energy"] == pytest.approx(-3.0)


def test_delete(backend, sample_row):
    row_a = {**sample_row, "energy": -1.0}
    row_b = {**sample_row, "energy": -2.0}
    backend.extend([row_a, row_b])
    backend.delete(0)
    assert len(backend) == 1
    assert backend.get(0)["energy"] == pytest.approx(-2.0)


def test_set_overwrite(backend, sample_row):
    backend.extend([sample_row])
    new_row = {**sample_row, "energy": -99.0}
    backend.set(0, new_row)
    assert backend.get(0)["energy"] == pytest.approx(-99.0)


def test_get_column(backend, sample_row):
    rows = [{**sample_row, "energy": float(-i)} for i in range(3)]
    backend.extend(rows)
    energies = backend.get_column("energy")
    assert energies == pytest.approx([0.0, -1.0, -2.0])


def test_get_column_with_indices(backend, sample_row):
    rows = [{**sample_row, "energy": float(-i)} for i in range(5)]
    backend.extend(rows)
    energies = backend.get_column("energy", indices=[0, 2, 4])
    assert energies == pytest.approx([0.0, -2.0, -4.0])


def test_get_many(backend, sample_row):
    rows = [{**sample_row, "energy": float(-i)} for i in range(5)]
    backend.extend(rows)
    result = backend.get_many([1, 3])
    assert len(result) == 2
    assert result[0]["energy"] == pytest.approx(-1.0)
    assert result[1]["energy"] == pytest.approx(-3.0)


def test_get_nonexistent(backend):
    with pytest.raises(IndexError):
        backend.get(0)


def test_update_partial(backend, sample_row):
    backend.extend([sample_row])
    backend.update(0, {"energy": -42.0})
    row = backend.get(0)
    assert row["energy"] == pytest.approx(-42.0)
    assert row["smiles"] == "O"  # unchanged


def test_drop_keys(backend, sample_row):
    backend.extend([sample_row, sample_row])
    backend.drop_keys(["smiles"])
    row = backend.get(0)
    assert "smiles" not in row
    assert "energy" in row


def test_clear(backend, sample_row):
    backend.extend([sample_row, sample_row])
    assert len(backend) == 2
    backend.clear()
    assert len(backend) == 0


def test_set_none_placeholder(backend, sample_row):
    backend.extend([sample_row, None, sample_row])
    assert len(backend) == 3
    assert backend.get(1) is None
    assert backend.get(0)["energy"] == pytest.approx(-10.5)


def test_from_uri(mongo_uri):
    col_name = f"test_{uuid.uuid4().hex[:8]}"
    # Build a from_uri string from mongo_uri
    # Extract host part from mongo_uri (e.g. "root:example@localhost:27017")
    after_scheme = mongo_uri.split("://", 1)[1]
    uri = f"mongodb://{after_scheme}/asebytes_test/{col_name}"
    b = MongoObjectBackend.from_uri(uri)
    try:
        assert len(b) == 0
        b.extend([{"x": 1}])
        assert len(b) == 1
    finally:
        b.remove()


# ======================================================================
# Group parameter tests (sync)
# ======================================================================


def test_group_parameter_default(mongo_uri):
    """Test that group parameter defaults to 'default'."""
    b = MongoObjectBackend(
        uri=mongo_uri,
        database="asebytes_test",
    )
    # Should use "default" as the collection name
    assert b.group == "default"
    b.close()


def test_group_parameter_custom(mongo_uri):
    """Test that custom group parameter creates separate collections."""
    group_name = f"test_group_{uuid.uuid4().hex[:8]}"
    b = MongoObjectBackend(
        uri=mongo_uri,
        database="asebytes_test",
        group=group_name,
    )
    try:
        assert b.group == group_name
        b.extend([{"x": 1}])
        assert len(b) == 1
    finally:
        b.remove()


def test_groups_are_isolated(mongo_uri):
    """Test that different groups are isolated from each other."""
    base_name = f"test_iso_{uuid.uuid4().hex[:8]}"
    group_a = f"{base_name}_a"
    group_b = f"{base_name}_b"

    b_a = MongoObjectBackend(
        uri=mongo_uri,
        database="asebytes_test",
        group=group_a,
    )
    b_b = MongoObjectBackend(
        uri=mongo_uri,
        database="asebytes_test",
        group=group_b,
    )

    try:
        b_a.extend([{"value": "a1"}, {"value": "a2"}])
        b_b.extend([{"value": "b1"}])

        assert len(b_a) == 2
        assert len(b_b) == 1
        assert b_a.get(0)["value"] == "a1"
        assert b_b.get(0)["value"] == "b1"
    finally:
        b_a.remove()
        b_b.remove()


def test_list_groups(mongo_uri):
    """Test list_groups returns available groups in a database."""
    base_name = f"test_lg_{uuid.uuid4().hex[:8]}"
    group_a = f"{base_name}_a"
    group_b = f"{base_name}_b"

    b_a = MongoObjectBackend(
        uri=mongo_uri,
        database="asebytes_test",
        group=group_a,
    )
    b_b = MongoObjectBackend(
        uri=mongo_uri,
        database="asebytes_test",
        group=group_b,
    )

    try:
        # Write something so the collections exist
        b_a.extend([{"x": 1}])
        b_b.extend([{"x": 2}])

        groups = MongoObjectBackend.list_groups(
            path=mongo_uri,
            database="asebytes_test",
        )
        assert group_a in groups
        assert group_b in groups
    finally:
        b_a.remove()
        b_b.remove()


def test_from_uri_with_group(mongo_uri):
    """Test from_uri with group parameter (URI contains only database)."""
    group_name = f"test_uri_grp_{uuid.uuid4().hex[:8]}"
    after_scheme = mongo_uri.split("://", 1)[1]
    # URI now only contains database, NOT collection
    uri = f"mongodb://{after_scheme}/asebytes_test"
    b = MongoObjectBackend.from_uri(uri, group=group_name)
    try:
        assert b.group == group_name
        b.extend([{"x": 1}])
        assert len(b) == 1
    finally:
        b.remove()


def test_insert_at_beginning(backend, sample_row):
    rows = [{**sample_row, "energy": float(-i)} for i in range(3)]
    backend.extend(rows)
    new_row = {**sample_row, "energy": -99.0}
    backend.insert(0, new_row)
    assert len(backend) == 4
    assert backend.get(0)["energy"] == pytest.approx(-99.0)
    assert backend.get(1)["energy"] == pytest.approx(0.0)


def test_insert_at_end(backend, sample_row):
    backend.extend([{**sample_row, "energy": -1.0}])
    backend.insert(1, {**sample_row, "energy": -2.0})
    assert len(backend) == 2
    assert backend.get(1)["energy"] == pytest.approx(-2.0)


def test_delete_last(backend, sample_row):
    backend.extend([{**sample_row, "energy": -1.0}, {**sample_row, "energy": -2.0}])
    backend.delete(1)
    assert len(backend) == 1
    assert backend.get(0)["energy"] == pytest.approx(-1.0)


# ======================================================================
# Async backend tests
# ======================================================================


@pytest.fixture
async def async_backend(mongo_uri):
    group_name = f"test_async_{uuid.uuid4().hex[:8]}"
    b = AsyncMongoObjectBackend(
        uri=mongo_uri,
        database="asebytes_test",
        group=group_name,
    )
    yield b
    await b.remove()


class TestAsyncMongoBackend:
    @pytest.mark.anyio
    async def test_is_async_writable_backend(self, async_backend):
        assert isinstance(async_backend, AsyncReadWriteBackend)
        assert isinstance(async_backend, AsyncReadBackend)

    @pytest.mark.anyio
    async def test_empty_len(self, async_backend):
        assert await async_backend.len() == 0

    @pytest.mark.anyio
    async def test_extend_and_get(self, async_backend, sample_row):
        await async_backend.extend([sample_row])
        assert await async_backend.len() == 1
        row = await async_backend.get(0)
        assert row["energy"] == pytest.approx(-10.5)
        assert row["smiles"] == "O"
        assert row["numbers"] == [1, 8]

    @pytest.mark.anyio
    async def test_get_with_keys(self, async_backend, sample_row):
        await async_backend.extend([sample_row])
        row = await async_backend.get(0, keys=["energy", "smiles"])
        assert "energy" in row
        assert "smiles" in row
        assert "positions" not in row

    @pytest.mark.anyio
    async def test_keys(self, async_backend, sample_row):
        await async_backend.extend([sample_row])
        cols = await async_backend.keys(0)
        assert "energy" in cols
        assert "positions" in cols

    @pytest.mark.anyio
    async def test_extend_multiple(self, async_backend, sample_row):
        await async_backend.extend([sample_row, sample_row, sample_row])
        assert await async_backend.len() == 3

    @pytest.mark.anyio
    async def test_insert(self, async_backend, sample_row):
        row_a = {**sample_row, "energy": -1.0}
        row_b = {**sample_row, "energy": -2.0}
        row_c = {**sample_row, "energy": -3.0}
        await async_backend.extend([row_a, row_c])
        await async_backend.insert(1, row_b)
        assert await async_backend.len() == 3
        assert (await async_backend.get(0))["energy"] == pytest.approx(-1.0)
        assert (await async_backend.get(1))["energy"] == pytest.approx(-2.0)
        assert (await async_backend.get(2))["energy"] == pytest.approx(-3.0)

    @pytest.mark.anyio
    async def test_delete(self, async_backend, sample_row):
        row_a = {**sample_row, "energy": -1.0}
        row_b = {**sample_row, "energy": -2.0}
        await async_backend.extend([row_a, row_b])
        await async_backend.delete(0)
        assert await async_backend.len() == 1
        assert (await async_backend.get(0))["energy"] == pytest.approx(-2.0)

    @pytest.mark.anyio
    async def test_set_overwrite(self, async_backend, sample_row):
        await async_backend.extend([sample_row])
        new_row = {**sample_row, "energy": -99.0}
        await async_backend.set(0, new_row)
        assert (await async_backend.get(0))["energy"] == pytest.approx(-99.0)

    @pytest.mark.anyio
    async def test_get_column(self, async_backend, sample_row):
        rows = [{**sample_row, "energy": float(-i)} for i in range(3)]
        await async_backend.extend(rows)
        energies = await async_backend.get_column("energy")
        assert energies == pytest.approx([0.0, -1.0, -2.0])

    @pytest.mark.anyio
    async def test_get_column_with_indices(self, async_backend, sample_row):
        rows = [{**sample_row, "energy": float(-i)} for i in range(5)]
        await async_backend.extend(rows)
        energies = await async_backend.get_column("energy", indices=[0, 2, 4])
        assert energies == pytest.approx([0.0, -2.0, -4.0])

    @pytest.mark.anyio
    async def test_get_many(self, async_backend, sample_row):
        rows = [{**sample_row, "energy": float(-i)} for i in range(5)]
        await async_backend.extend(rows)
        result = await async_backend.get_many([1, 3])
        assert len(result) == 2
        assert result[0]["energy"] == pytest.approx(-1.0)
        assert result[1]["energy"] == pytest.approx(-3.0)

    @pytest.mark.anyio
    async def test_get_nonexistent(self, async_backend):
        with pytest.raises(IndexError):
            await async_backend.get(0)

    @pytest.mark.anyio
    async def test_update_partial(self, async_backend, sample_row):
        await async_backend.extend([sample_row])
        await async_backend.update(0, {"energy": -42.0})
        row = await async_backend.get(0)
        assert row["energy"] == pytest.approx(-42.0)
        assert row["smiles"] == "O"

    @pytest.mark.anyio
    async def test_drop_keys(self, async_backend, sample_row):
        await async_backend.extend([sample_row, sample_row])
        await async_backend.drop_keys(["smiles"])
        row = await async_backend.get(0)
        assert "smiles" not in row
        assert "energy" in row

    @pytest.mark.anyio
    async def test_clear(self, async_backend, sample_row):
        await async_backend.extend([sample_row, sample_row])
        assert await async_backend.len() == 2
        await async_backend.clear()
        assert await async_backend.len() == 0

    @pytest.mark.anyio
    async def test_set_none_placeholder(self, async_backend, sample_row):
        await async_backend.extend([sample_row, None, sample_row])
        assert await async_backend.len() == 3
        assert (await async_backend.get(1)) is None
        assert (await async_backend.get(0))["energy"] == pytest.approx(-10.5)

    @pytest.mark.anyio
    async def test_insert_at_beginning(self, async_backend, sample_row):
        rows = [{**sample_row, "energy": float(-i)} for i in range(3)]
        await async_backend.extend(rows)
        await async_backend.insert(0, {**sample_row, "energy": -99.0})
        assert await async_backend.len() == 4
        assert (await async_backend.get(0))["energy"] == pytest.approx(-99.0)
        assert (await async_backend.get(1))["energy"] == pytest.approx(0.0)

    @pytest.mark.anyio
    async def test_insert_at_end(self, async_backend, sample_row):
        await async_backend.extend([{**sample_row, "energy": -1.0}])
        await async_backend.insert(1, {**sample_row, "energy": -2.0})
        assert await async_backend.len() == 2
        assert (await async_backend.get(1))["energy"] == pytest.approx(-2.0)

    @pytest.mark.anyio
    async def test_delete_last(self, async_backend, sample_row):
        await async_backend.extend(
            [{**sample_row, "energy": -1.0}, {**sample_row, "energy": -2.0}]
        )
        await async_backend.delete(1)
        assert await async_backend.len() == 1
        assert (await async_backend.get(0))["energy"] == pytest.approx(-1.0)

    @pytest.mark.anyio
    async def test_from_uri(self, mongo_uri):
        col_name = f"test_async_{uuid.uuid4().hex[:8]}"
        after_scheme = mongo_uri.split("://", 1)[1]
        uri = f"mongodb://{after_scheme}/asebytes_test/{col_name}"
        b = AsyncMongoObjectBackend.from_uri(uri)
        try:
            assert await b.len() == 0
            await b.extend([{"x": 1}])
            assert await b.len() == 1
        finally:
            await b.remove()


# ======================================================================
# Race condition tests — concurrent extend must not produce duplicate keys
# ======================================================================


def test_concurrent_extend_no_duplicate_keys(mongo_uri, sample_row):
    """Two threads calling extend() simultaneously must not collide on sort keys.

    Before the fix, both threads read the same next_sort_key, then both
    try to insert_many with the same _id values → DuplicateKeyError.
    """
    group_name = f"test_race_{uuid.uuid4().hex[:8]}"
    rows = [{**sample_row, "energy": float(i)} for i in range(5)]

    def _extend_in_thread():
        b = MongoObjectBackend(
            uri=mongo_uri, database="asebytes_test", group=group_name
        )
        b.extend(rows)
        b.close()

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(_extend_in_thread) for _ in range(2)]
            for f in futures:
                f.result()  # raises if DuplicateKeyError occurred

        # Verify: 10 total rows, all readable
        b = MongoObjectBackend(
            uri=mongo_uri, database="asebytes_test", group=group_name
        )
        assert len(b) == 10
        # All 10 rows should be retrievable without error
        for i in range(10):
            assert b.get(i) is not None
        b.close()
    finally:
        cleanup = MongoObjectBackend(
            uri=mongo_uri, database="asebytes_test", group=group_name
        )
        cleanup.remove()


def test_concurrent_insert_no_duplicate_keys(mongo_uri, sample_row):
    """Two threads calling insert() simultaneously must not collide on sort keys."""
    group_name = f"test_race_ins_{uuid.uuid4().hex[:8]}"

    # Seed with one row so insert(0, ...) is valid
    seed = MongoObjectBackend(
        uri=mongo_uri, database="asebytes_test", group=group_name
    )
    seed.extend([{**sample_row, "energy": -999.0}])
    seed.close()

    def _insert_in_thread(value):
        b = MongoObjectBackend(
            uri=mongo_uri, database="asebytes_test", group=group_name
        )
        b.insert(0, {**sample_row, "energy": float(value)})
        b.close()

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(_insert_in_thread, i) for i in range(2)]
            for f in futures:
                f.result()  # raises if DuplicateKeyError occurred

        b = MongoObjectBackend(
            uri=mongo_uri, database="asebytes_test", group=group_name
        )
        assert len(b) == 3  # 1 seed + 2 inserts
        b.close()
    finally:
        cleanup = MongoObjectBackend(
            uri=mongo_uri, database="asebytes_test", group=group_name
        )
        cleanup.remove()


class TestAsyncRaceConditions:
    @pytest.mark.anyio
    async def test_concurrent_extend_no_duplicate_keys(self, mongo_uri, sample_row):
        """Two concurrent async extend() calls must not collide on sort keys."""
        group_name = f"test_async_race_{uuid.uuid4().hex[:8]}"
        rows = [{**sample_row, "energy": float(i)} for i in range(5)]

        async def _extend():
            b = AsyncMongoObjectBackend(
                uri=mongo_uri, database="asebytes_test", group=group_name
            )
            await b.extend(rows)
            b.close()

        try:
            await asyncio.gather(_extend(), _extend())

            b = AsyncMongoObjectBackend(
                uri=mongo_uri, database="asebytes_test", group=group_name
            )
            assert await b.len() == 10
            for i in range(10):
                assert (await b.get(i)) is not None
            b.close()
        finally:
            cleanup = AsyncMongoObjectBackend(
                uri=mongo_uri, database="asebytes_test", group=group_name
            )
            await cleanup.remove()

    @pytest.mark.anyio
    async def test_concurrent_insert_no_duplicate_keys(self, mongo_uri, sample_row):
        """Two concurrent async insert() calls must not collide on sort keys."""
        group_name = f"test_async_race_ins_{uuid.uuid4().hex[:8]}"

        seed = AsyncMongoObjectBackend(
            uri=mongo_uri, database="asebytes_test", group=group_name
        )
        await seed.extend([{**sample_row, "energy": -999.0}])
        seed.close()

        async def _insert(value):
            b = AsyncMongoObjectBackend(
                uri=mongo_uri, database="asebytes_test", group=group_name
            )
            await b.insert(0, {**sample_row, "energy": float(value)})
            b.close()

        try:
            await asyncio.gather(_insert(0), _insert(1))

            b = AsyncMongoObjectBackend(
                uri=mongo_uri, database="asebytes_test", group=group_name
            )
            assert await b.len() == 3
            b.close()
        finally:
            cleanup = AsyncMongoObjectBackend(
                uri=mongo_uri, database="asebytes_test", group=group_name
            )
            await cleanup.remove()


# ======================================================================
# Stale cache tests — second instance must see writes from first
# ======================================================================


def test_second_instance_sees_writes_from_first(mongo_uri, sample_row):
    """A second backend instance must see data written by a different instance.

    Simulates two replicas behind a load balancer: replica B loads cache
    while empty, then replica A writes data. B must see the new rows on
    its next read, not serve stale len()=0 forever.
    """
    group_name = f"test_stale_{uuid.uuid4().hex[:8]}"
    try:
        # Replica B connects first, loads cache (empty)
        replica_b = MongoObjectBackend(
            uri=mongo_uri, database="asebytes_test", group=group_name
        )
        assert len(replica_b) == 0  # cache loaded: empty

        # Replica A writes 3 rows via a separate instance
        replica_a = MongoObjectBackend(
            uri=mongo_uri, database="asebytes_test", group=group_name
        )
        replica_a.extend([sample_row, sample_row, sample_row])
        assert len(replica_a) == 3
        replica_a.close()

        # Replica B must now see the 3 rows — NOT stale 0
        assert len(replica_b) == 3
        assert replica_b.get(0) is not None
        assert replica_b.get(2) is not None
        replica_b.close()
    finally:
        cleanup = MongoObjectBackend(
            uri=mongo_uri, database="asebytes_test", group=group_name
        )
        cleanup.remove()


class TestAsyncStaleCache:
    @pytest.mark.anyio
    async def test_second_instance_sees_writes_from_first(self, mongo_uri, sample_row):
        """Async: a second backend instance must see data written by another."""
        group_name = f"test_async_stale_{uuid.uuid4().hex[:8]}"
        try:
            # Replica B loads cache (empty)
            replica_b = AsyncMongoObjectBackend(
                uri=mongo_uri, database="asebytes_test", group=group_name
            )
            assert await replica_b.len() == 0

            # Replica A writes 3 rows
            replica_a = AsyncMongoObjectBackend(
                uri=mongo_uri, database="asebytes_test", group=group_name
            )
            await replica_a.extend([sample_row, sample_row, sample_row])
            assert await replica_a.len() == 3
            replica_a.close()

            # Replica B must see the new data
            assert await replica_b.len() == 3
            assert (await replica_b.get(0)) is not None
            assert (await replica_b.get(2)) is not None
            replica_b.close()
        finally:
            cleanup = AsyncMongoObjectBackend(
                uri=mongo_uri, database="asebytes_test", group=group_name
            )
            await cleanup.remove()


# ── Numpy array round-trip through BSON ──────────────────────────────────


class TestNumpyBsonRoundtrip:
    """Numpy arrays stored via MongoObjectBackend must survive the BSON round-trip."""

    def test_1d_int_array_roundtrip(self, backend):
        arr = np.array([1, 6, 8], dtype=np.int64)
        backend.extend([{"numbers": arr}])
        result = backend.get(0)
        assert isinstance(result["numbers"], np.ndarray), (
            f"Expected np.ndarray, got {type(result['numbers'])}"
        )
        np.testing.assert_array_equal(result["numbers"], arr)

    def test_2d_float_array_roundtrip(self, backend):
        arr = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        backend.extend([{"forces": arr}])
        result = backend.get(0)
        assert isinstance(result["forces"], np.ndarray), (
            f"Expected np.ndarray, got {type(result['forces'])}"
        )
        np.testing.assert_array_almost_equal(result["forces"], arr)

    def test_bool_array_roundtrip(self, backend):
        arr = np.array([True, False, True])
        backend.extend([{"pbc": arr}])
        result = backend.get(0)
        assert isinstance(result["pbc"], np.ndarray), (
            f"Expected np.ndarray, got {type(result['pbc'])}"
        )
        np.testing.assert_array_equal(result["pbc"], arr)

    def test_dtype_preserved(self, backend):
        """Exact dtype must survive the round-trip."""
        arr = np.array([1.0, 2.0], dtype=np.float32)
        backend.extend([{"vals": arr}])
        result = backend.get(0)
        assert isinstance(result["vals"], np.ndarray)
        assert result["vals"].dtype == np.float32

    def test_mixed_row_with_arrays_and_scalars(self, backend):
        row = {
            "energy": -10.5,
            "forces": np.array([[0.1, 0.2], [0.3, 0.4]]),
            "smiles": "CCO",
            "numbers": np.array([1, 6, 8]),
        }
        backend.extend([row])
        result = backend.get(0)
        assert result["energy"] == pytest.approx(-10.5)
        assert result["smiles"] == "CCO"
        assert isinstance(result["forces"], np.ndarray)
        np.testing.assert_array_almost_equal(result["forces"], row["forces"])
        assert isinstance(result["numbers"], np.ndarray)
        np.testing.assert_array_equal(result["numbers"], row["numbers"])

    def test_numpy_scalar_roundtrip(self, backend):
        backend.extend([{"val": np.float64(-3.14)}])
        result = backend.get(0)
        assert result["val"] == pytest.approx(-3.14)

    def test_get_column_returns_numpy_arrays(self, backend):
        rows = [
            {"forces": np.array([[0.1, 0.2], [0.3, 0.4]])},
            {"forces": np.array([[0.5, 0.6], [0.7, 0.8]])},
        ]
        backend.extend(rows)
        col = backend.get_column("forces")
        for i, val in enumerate(col):
            assert isinstance(val, np.ndarray), (
                f"Column item {i}: expected np.ndarray, got {type(val)}"
            )
            np.testing.assert_array_almost_equal(val, rows[i]["forces"])

    def test_update_preserves_numpy_array(self, backend):
        backend.extend([{"energy": -1.0, "forces": np.array([0.0, 0.0])}])
        new_forces = np.array([1.0, 2.0])
        backend.update(0, {"forces": new_forces})
        result = backend.get(0)
        assert isinstance(result["forces"], np.ndarray)
        np.testing.assert_array_equal(result["forces"], new_forces)
