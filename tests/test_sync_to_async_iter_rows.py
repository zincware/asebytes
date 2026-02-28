"""Test that SyncToAsyncReadAdapter forwards iter_rows to the wrapped backend."""

import pytest

from asebytes._async_backends import SyncToAsyncReadAdapter, SyncToAsyncReadWriteAdapter
from asebytes.lmdb import LMDBObjectBackend


@pytest.mark.anyio
async def test_iter_rows_forwarded(tmp_path):
    """SyncToAsyncReadAdapter.iter_rows should call the wrapped backend's iter_rows."""
    backend = LMDBObjectBackend(str(tmp_path / "test.lmdb"))
    backend.extend([{"a": 1}, {"a": 2}, {"a": 3}])

    adapter = SyncToAsyncReadAdapter(backend)
    rows = []
    async for row in adapter.iter_rows([0, 2]):
        rows.append(row)

    assert len(rows) == 2
    assert rows[0]["a"] == 1
    assert rows[1]["a"] == 3


@pytest.mark.anyio
async def test_iter_rows_with_keys_forwarded(tmp_path):
    """iter_rows should forward keys filter too."""
    backend = LMDBObjectBackend(str(tmp_path / "test.lmdb"))
    backend.extend([{"a": 1, "b": 10}, {"a": 2, "b": 20}])

    adapter = SyncToAsyncReadAdapter(backend)
    rows = []
    async for row in adapter.iter_rows([0, 1], keys=["a"]):
        rows.append(row)

    assert len(rows) == 2
    assert "a" in rows[0]
    # Backend should filter to only "a" key
    assert rows[0]["a"] == 1


@pytest.mark.anyio
async def test_iter_rows_rw_adapter_forwarded(tmp_path):
    """SyncToAsyncReadWriteAdapter should also forward iter_rows."""
    backend = LMDBObjectBackend(str(tmp_path / "test.lmdb"))
    backend.extend([{"x": 10}, {"x": 20}, {"x": 30}])

    adapter = SyncToAsyncReadWriteAdapter(backend)
    rows = []
    async for row in adapter.iter_rows([1]):
        rows.append(row)

    assert len(rows) == 1
    assert rows[0]["x"] == 20
