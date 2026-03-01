import os
import uuid

import pytest

pymongo = pytest.importorskip("pymongo")

from asebytes._backends import ReadBackend, ReadWriteBackend
from asebytes._async_backends import AsyncReadBackend, AsyncReadWriteBackend
from asebytes.mongodb import AsyncMongoObjectBackend, MongoObjectBackend

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://root:example@localhost:27017")


def _mongo_available():
    """Check whether a local MongoDB is reachable."""
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=1000)
        client.admin.command("ping")
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _mongo_available(), reason=f"MongoDB not available at {MONGO_URI}"
)


@pytest.fixture
def backend():
    """Create a backend with a unique group, drop it after the test."""
    group_name = f"test_{uuid.uuid4().hex[:8]}"
    b = MongoObjectBackend(
        uri=MONGO_URI,
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


def test_from_uri():
    col_name = f"test_{uuid.uuid4().hex[:8]}"
    # Build a from_uri string from MONGO_URI
    # Extract host part from MONGO_URI (e.g. "root:example@localhost:27017")
    after_scheme = MONGO_URI.split("://", 1)[1]
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


def test_group_parameter_default():
    """Test that group parameter defaults to 'default'."""
    b = MongoObjectBackend(
        uri=MONGO_URI,
        database="asebytes_test",
    )
    # Should use "default" as the collection name
    assert b.group == "default"
    b.close()


def test_group_parameter_custom():
    """Test that custom group parameter creates separate collections."""
    group_name = f"test_group_{uuid.uuid4().hex[:8]}"
    b = MongoObjectBackend(
        uri=MONGO_URI,
        database="asebytes_test",
        group=group_name,
    )
    try:
        assert b.group == group_name
        b.extend([{"x": 1}])
        assert len(b) == 1
    finally:
        b.remove()


def test_groups_are_isolated():
    """Test that different groups are isolated from each other."""
    base_name = f"test_iso_{uuid.uuid4().hex[:8]}"
    group_a = f"{base_name}_a"
    group_b = f"{base_name}_b"

    b_a = MongoObjectBackend(
        uri=MONGO_URI,
        database="asebytes_test",
        group=group_a,
    )
    b_b = MongoObjectBackend(
        uri=MONGO_URI,
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


def test_list_groups():
    """Test list_groups returns available groups in a database."""
    base_name = f"test_lg_{uuid.uuid4().hex[:8]}"
    group_a = f"{base_name}_a"
    group_b = f"{base_name}_b"

    b_a = MongoObjectBackend(
        uri=MONGO_URI,
        database="asebytes_test",
        group=group_a,
    )
    b_b = MongoObjectBackend(
        uri=MONGO_URI,
        database="asebytes_test",
        group=group_b,
    )

    try:
        # Write something so the collections exist
        b_a.extend([{"x": 1}])
        b_b.extend([{"x": 2}])

        groups = MongoObjectBackend.list_groups(
            path=MONGO_URI,
            database="asebytes_test",
        )
        assert group_a in groups
        assert group_b in groups
    finally:
        b_a.remove()
        b_b.remove()


def test_from_uri_with_group():
    """Test from_uri with group parameter (URI contains only database)."""
    group_name = f"test_uri_grp_{uuid.uuid4().hex[:8]}"
    after_scheme = MONGO_URI.split("://", 1)[1]
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
async def async_backend():
    group_name = f"test_async_{uuid.uuid4().hex[:8]}"
    b = AsyncMongoObjectBackend(
        uri=MONGO_URI,
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
    async def test_from_uri(self):
        col_name = f"test_async_{uuid.uuid4().hex[:8]}"
        after_scheme = MONGO_URI.split("://", 1)[1]
        uri = f"mongodb://{after_scheme}/asebytes_test/{col_name}"
        b = AsyncMongoObjectBackend.from_uri(uri)
        try:
            assert await b.len() == 0
            await b.extend([{"x": 1}])
            assert await b.len() == 1
        finally:
            await b.remove()

    @pytest.mark.anyio
    async def test_concurrent_extend_no_duplicate_sort_keys(self, sample_row):
        """Test that concurrent extend calls don't produce duplicate sort keys.

        This tests the race condition fix: atomic sort-key allocation using
        find_one_and_update with $inc instead of separate read-then-write.
        """
        import asyncio

        col_name = f"test_concurrent_{uuid.uuid4().hex[:8]}"
        backend = AsyncMongoObjectBackend(
            uri=MONGO_URI,
            database="asebytes_test",
            group=col_name,
        )
        try:
            # Run 10 concurrent extend calls, each adding 5 rows
            tasks = [
                backend.extend([{**sample_row, "batch": i, "idx": j} for j in range(5)])
                for i in range(10)
            ]
            await asyncio.gather(*tasks)

            # Should have 50 total rows
            total_len = await backend.len()
            assert total_len == 50, f"Expected 50 rows, got {total_len}"

            # Verify all sort keys are unique by checking we can fetch all 50 rows
            # and that the underlying _sort_keys list has no duplicates
            await backend._ensure_cache()
            sort_keys = backend._sort_keys
            assert sort_keys is not None, (
                "sort_keys should be populated after _ensure_cache"
            )
            assert len(sort_keys) == 50, f"Expected 50 sort keys, got {len(sort_keys)}"
            assert len(set(sort_keys)) == 50, (
                f"Duplicate sort keys found! Unique: {len(set(sort_keys))}, Total: {len(sort_keys)}"
            )
        finally:
            await backend.remove()

    @pytest.mark.anyio
    async def test_concurrent_insert_no_duplicate_sort_keys(self, sample_row):
        """Test that concurrent insert calls don't produce duplicate sort keys."""
        import asyncio

        col_name = f"test_concurrent_insert_{uuid.uuid4().hex[:8]}"
        backend = AsyncMongoObjectBackend(
            uri=MONGO_URI,
            database="asebytes_test",
            group=col_name,
        )
        try:
            # Seed with one row first
            await backend.extend([sample_row])

            # Run 10 concurrent insert calls at index 0
            tasks = [
                backend.insert(0, {**sample_row, "insert_id": i}) for i in range(10)
            ]
            await asyncio.gather(*tasks)

            # Should have 11 total rows
            total_len = await backend.len()
            assert total_len == 11, f"Expected 11 rows, got {total_len}"

            # Verify all sort keys are unique
            await backend._ensure_cache()
            sort_keys = backend._sort_keys
            assert sort_keys is not None, (
                "sort_keys should be populated after _ensure_cache"
            )
            assert len(sort_keys) == 11, f"Expected 11 sort keys, got {len(sort_keys)}"
            assert len(set(sort_keys)) == 11, (
                f"Duplicate sort keys found! Unique: {len(set(sort_keys))}, Total: {len(sort_keys)}"
            )
        finally:
            await backend.remove()
