"""Tests for the Redis blob-level backend (RedisBlobBackend).

Requires a running Redis server. Skipped automatically when Redis is
unreachable.  Override the URI with the ``REDIS_URI`` env-var.
"""

from __future__ import annotations

import os
import uuid

import pytest

redis_mod = pytest.importorskip("redis")

from asebytes._backends import ReadBackend, ReadWriteBackend

REDIS_URI = os.environ.get("REDIS_URI", "redis://localhost:6379")


def _redis_available() -> bool:
    try:
        r = redis_mod.Redis.from_url(REDIS_URI, socket_connect_timeout=1)
        r.ping()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _redis_available(), reason=f"Redis not available at {REDIS_URI}"
)


@pytest.fixture
def backend():
    from asebytes.redis import RedisBlobBackend

    prefix = f"test_{uuid.uuid4().hex[:8]}"
    b = RedisBlobBackend(url=REDIS_URI, prefix=prefix)
    yield b
    b.remove()


@pytest.fixture
def sample_row() -> dict[bytes, bytes]:
    return {b"energy": b"-10.5", b"smiles": b"O", b"numbers": b"[1,8]"}


# ======================================================================
# Type / protocol checks
# ======================================================================


def test_is_writable_backend(backend):
    assert isinstance(backend, ReadWriteBackend)
    assert isinstance(backend, ReadBackend)


# ======================================================================
# Empty backend
# ======================================================================


def test_empty_len(backend):
    assert len(backend) == 0


# ======================================================================
# extend + get roundtrip
# ======================================================================


def test_extend_and_get(backend, sample_row):
    backend.extend([sample_row])
    assert len(backend) == 1
    row = backend.get(0)
    assert row == sample_row


def test_extend_returns_new_length(backend, sample_row):
    length = backend.extend([sample_row, sample_row])
    assert length == 2
    length2 = backend.extend([sample_row])
    assert length2 == 3


def test_extend_empty_returns_zero(backend):
    length = backend.extend([])
    assert length == 0


def test_extend_multiple(backend, sample_row):
    backend.extend([sample_row, sample_row, sample_row])
    assert len(backend) == 3
    for i in range(3):
        assert backend.get(i) == sample_row


# ======================================================================
# get with key filter
# ======================================================================


def test_get_with_keys(backend, sample_row):
    backend.extend([sample_row])
    row = backend.get(0, keys=[b"energy", b"smiles"])
    assert b"energy" in row
    assert b"smiles" in row
    assert b"numbers" not in row


# ======================================================================
# get negative index
# ======================================================================


def test_get_negative_index(backend, sample_row):
    backend.extend([sample_row, {b"x": b"1"}])
    assert backend.get(-1) == {b"x": b"1"}
    assert backend.get(-2) == sample_row


# ======================================================================
# get out of bounds
# ======================================================================


def test_get_out_of_bounds_empty(backend):
    with pytest.raises(IndexError):
        backend.get(0)


def test_get_out_of_bounds_positive(backend, sample_row):
    backend.extend([sample_row])
    with pytest.raises(IndexError):
        backend.get(1)


def test_get_out_of_bounds_negative(backend, sample_row):
    backend.extend([sample_row])
    with pytest.raises(IndexError):
        backend.get(-2)


# ======================================================================
# set replaces row
# ======================================================================


def test_set_overwrites(backend, sample_row):
    backend.extend([sample_row])
    new_row = {b"energy": b"-99.0"}
    backend.set(0, new_row)
    assert backend.get(0) == new_row


def test_set_out_of_bounds(backend, sample_row):
    backend.extend([sample_row])
    with pytest.raises(IndexError):
        backend.set(1, sample_row)


# ======================================================================
# set None placeholder
# ======================================================================


def test_set_none_placeholder(backend, sample_row):
    backend.extend([sample_row])
    backend.set(0, None)
    assert backend.get(0) is None
    assert len(backend) == 1


# ======================================================================
# delete shifts indices
# ======================================================================


def test_delete(backend):
    row_a = {b"v": b"a"}
    row_b = {b"v": b"b"}
    row_c = {b"v": b"c"}
    backend.extend([row_a, row_b, row_c])
    backend.delete(1)
    assert len(backend) == 2
    assert backend.get(0) == row_a
    assert backend.get(1) == row_c


def test_delete_first(backend):
    row_a = {b"v": b"a"}
    row_b = {b"v": b"b"}
    backend.extend([row_a, row_b])
    backend.delete(0)
    assert len(backend) == 1
    assert backend.get(0) == row_b


def test_delete_last(backend):
    row_a = {b"v": b"a"}
    row_b = {b"v": b"b"}
    backend.extend([row_a, row_b])
    backend.delete(1)
    assert len(backend) == 1
    assert backend.get(0) == row_a


# ======================================================================
# insert at beginning, end, with None
# ======================================================================


def test_insert_at_beginning(backend):
    backend.extend([{b"v": b"a"}, {b"v": b"b"}])
    backend.insert(0, {b"v": b"new"})
    assert len(backend) == 3
    assert backend.get(0) == {b"v": b"new"}
    assert backend.get(1) == {b"v": b"a"}
    assert backend.get(2) == {b"v": b"b"}


def test_insert_at_end(backend):
    backend.extend([{b"v": b"a"}])
    backend.insert(1, {b"v": b"b"})
    assert len(backend) == 2
    assert backend.get(0) == {b"v": b"a"}
    assert backend.get(1) == {b"v": b"b"}


def test_insert_in_middle(backend):
    backend.extend([{b"v": b"a"}, {b"v": b"c"}])
    backend.insert(1, {b"v": b"b"})
    assert len(backend) == 3
    assert backend.get(0) == {b"v": b"a"}
    assert backend.get(1) == {b"v": b"b"}
    assert backend.get(2) == {b"v": b"c"}


def test_insert_none(backend):
    backend.extend([{b"v": b"a"}])
    backend.insert(0, None)
    assert len(backend) == 2
    assert backend.get(0) is None
    assert backend.get(1) == {b"v": b"a"}


# ======================================================================
# extend with None placeholders
# ======================================================================


def test_extend_with_none_placeholders(backend, sample_row):
    backend.extend([sample_row, None, sample_row])
    assert len(backend) == 3
    assert backend.get(0) == sample_row
    assert backend.get(1) is None
    assert backend.get(2) == sample_row


# ======================================================================
# get_many batch
# ======================================================================


def test_get_many(backend):
    rows = [{b"i": str(i).encode()} for i in range(5)]
    backend.extend(rows)
    result = backend.get_many([1, 3])
    assert len(result) == 2
    assert result[0] == {b"i": b"1"}
    assert result[1] == {b"i": b"3"}


def test_get_many_with_keys(backend, sample_row):
    backend.extend([sample_row, sample_row])
    result = backend.get_many([0, 1], keys=[b"energy"])
    assert all(b"energy" in r for r in result)
    assert all(b"smiles" not in r for r in result)


# ======================================================================
# get_column
# ======================================================================


def test_get_column(backend):
    rows = [{b"val": str(i).encode(), b"other": b"x"} for i in range(4)]
    backend.extend(rows)
    col = backend.get_column(b"val")
    assert col == [b"0", b"1", b"2", b"3"]


def test_get_column_with_indices(backend):
    rows = [{b"val": str(i).encode()} for i in range(5)]
    backend.extend(rows)
    col = backend.get_column(b"val", indices=[0, 2, 4])
    assert col == [b"0", b"2", b"4"]


# ======================================================================
# get_column with None rows
# ======================================================================


def test_get_column_with_none_rows(backend):
    backend.extend([{b"val": b"a"}, None, {b"val": b"c"}])
    col = backend.get_column(b"val")
    assert col == [b"a", None, b"c"]


# ======================================================================
# keys() returns field names
# ======================================================================


def test_keys(backend, sample_row):
    backend.extend([sample_row])
    k = backend.keys(0)
    assert set(k) == set(sample_row.keys())


def test_keys_none_row(backend):
    backend.extend([None])
    assert backend.keys(0) == []


# ======================================================================
# update partial merge
# ======================================================================


def test_update_partial(backend, sample_row):
    backend.extend([sample_row])
    backend.update(0, {b"energy": b"-42.0"})
    row = backend.get(0)
    assert row[b"energy"] == b"-42.0"
    assert row[b"smiles"] == b"O"  # unchanged


def test_update_adds_new_key(backend):
    backend.extend([{b"a": b"1"}])
    backend.update(0, {b"b": b"2"})
    row = backend.get(0)
    assert row == {b"a": b"1", b"b": b"2"}


# ======================================================================
# drop_keys removes fields
# ======================================================================


def test_drop_keys(backend, sample_row):
    backend.extend([sample_row, sample_row])
    backend.drop_keys([b"smiles"])
    row0 = backend.get(0)
    row1 = backend.get(1)
    assert b"smiles" not in row0
    assert b"smiles" not in row1
    assert b"energy" in row0


def test_drop_keys_with_indices(backend, sample_row):
    backend.extend([sample_row, sample_row])
    backend.drop_keys([b"smiles"], indices=[0])
    assert b"smiles" not in backend.get(0)
    assert b"smiles" in backend.get(1)  # untouched


# ======================================================================
# clear resets
# ======================================================================


def test_clear(backend, sample_row):
    backend.extend([sample_row, sample_row])
    assert len(backend) == 2
    backend.clear()
    assert len(backend) == 0


# ======================================================================
# clear then extend (sort key counter reset)
# ======================================================================


def test_clear_then_extend(backend, sample_row):
    backend.extend([sample_row])
    backend.clear()
    assert len(backend) == 0
    backend.extend([sample_row, sample_row])
    assert len(backend) == 2
    assert backend.get(0) == sample_row
    assert backend.get(1) == sample_row


# ======================================================================
# remove cleans all prefix keys
# ======================================================================


def test_remove(backend, sample_row):
    backend.extend([sample_row, sample_row])
    prefix = backend._prefix
    r = redis_mod.Redis.from_url(REDIS_URI)
    # Verify keys exist before remove
    assert r.exists(f"{prefix}:sort_keys") == 1
    backend.remove()
    # All prefix keys should be gone
    cursor, keys = r.scan(match=f"{prefix}:*")
    remaining = list(keys)
    while cursor:
        cursor, keys = r.scan(cursor=cursor, match=f"{prefix}:*")
        remaining.extend(keys)
    assert len(remaining) == 0


# ======================================================================
# from_uri parsing
# ======================================================================


def test_from_uri_basic():
    from asebytes.redis import RedisBlobBackend

    prefix = f"test_{uuid.uuid4().hex[:8]}"
    b = RedisBlobBackend.from_uri(f"redis://localhost:6379/0/{prefix}")
    try:
        assert len(b) == 0
        b.extend([{b"k": b"v"}])
        assert len(b) == 1
    finally:
        b.remove()


def test_from_uri_default_prefix():
    from asebytes.redis import RedisBlobBackend

    b = RedisBlobBackend.from_uri("redis://localhost:6379")
    try:
        assert b._prefix == "default"
    finally:
        b.remove()


def test_from_uri_with_db_and_prefix():
    from asebytes.redis import RedisBlobBackend

    prefix = f"test_{uuid.uuid4().hex[:8]}"
    b = RedisBlobBackend.from_uri(f"redis://localhost:6379/0/{prefix}")
    try:
        assert b._prefix == prefix
    finally:
        b.remove()
