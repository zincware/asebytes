"""AsyncObjectIO facade contract tests.

Every read-write backend must satisfy the same object-level contract when
accessed through the AsyncObjectIO facade. All tests use @pytest.mark.anyio.
"""

from __future__ import annotations

import pytest


@pytest.mark.anyio
class TestAsyncObjectContract:
    """Core CRUD contract for AsyncObjectIO facade."""

    async def test_extend_and_len(self, async_objectio):
        rows = [{"key": "val1"}, {"key": "val2"}]
        await async_objectio.extend(rows)
        assert await async_objectio.len() == 2

    async def test_get_by_index(self, async_objectio):
        rows = [{"name": "alice"}, {"name": "bob"}]
        await async_objectio.extend(rows)
        row = await async_objectio[0]
        assert "name" in row
        assert row["name"] == "alice"

    async def test_slice(self, async_objectio):
        rows = [{"k": "v1"}, {"k": "v2"}, {"k": "v3"}]
        await async_objectio.extend(rows)
        result = await async_objectio[0:2].to_list()
        assert len(result) == 2

    async def test_negative_index(self, async_objectio):
        rows = [{"k": "v1"}, {"k": "v2"}, {"k": "v3"}]
        await async_objectio.extend(rows)
        row = await async_objectio[-1]
        assert row["k"] == "v3"

    async def test_iteration(self, async_objectio):
        rows = [{"k": "v1"}, {"k": "v2"}]
        await async_objectio.extend(rows)
        items = []
        async for item in async_objectio:
            items.append(item)
        assert len(items) == 2
        for item in items:
            assert isinstance(item, dict)

    async def test_keys(self, async_objectio):
        rows = [{"a": 1, "b": 2}]
        await async_objectio.extend(rows)
        k = await async_objectio.keys(0)
        assert isinstance(k, list)
        assert len(k) > 0

    async def test_column_access(self, async_objectio):
        rows = [{"x": 10, "y": 20}, {"x": 30, "y": 40}]
        await async_objectio.extend(rows)
        col = async_objectio["x"]
        values = await col.to_list()
        assert values == [10, 30]
