"""ObjectIO facade contract tests.

Every read-write backend must satisfy the same object-level contract when
accessed through the ObjectIO facade.
"""

from __future__ import annotations

import pytest


class TestObjectContract:
    """Core CRUD contract for ObjectIO facade."""

    def test_extend_and_len(self, objectio):
        rows = [{"key": "val1"}, {"key": "val2"}]
        objectio.extend(rows)
        assert len(objectio) == 2

    def test_get_by_index(self, objectio):
        rows = [{"name": "alice"}, {"name": "bob"}]
        objectio.extend(rows)
        row = objectio[0]
        assert "name" in row
        assert row["name"] == "alice"

    def test_get_by_index_second(self, objectio):
        rows = [{"name": "alice"}, {"name": "bob"}]
        objectio.extend(rows)
        row = objectio[1]
        assert row["name"] == "bob"

    def test_slice(self, objectio):
        rows = [{"k": "v1"}, {"k": "v2"}, {"k": "v3"}]
        objectio.extend(rows)
        result = objectio[0:2]
        assert len(result) == 2

    def test_negative_index(self, objectio):
        rows = [{"k": "v1"}, {"k": "v2"}, {"k": "v3"}]
        objectio.extend(rows)
        row = objectio[-1]
        assert row["k"] == "v3"

    def test_iteration(self, objectio):
        rows = [{"k": "v1"}, {"k": "v2"}]
        objectio.extend(rows)
        items = list(objectio)
        assert len(items) == 2
        for item in items:
            assert isinstance(item, dict)

    def test_keys(self, objectio):
        rows = [{"a": 1, "b": 2}]
        objectio.extend(rows)
        k = objectio.keys(0)
        assert isinstance(k, list)
        assert len(k) > 0

    def test_set_overwrite(self, objectio):
        rows = [{"k": "old"}]
        objectio.extend(rows)
        objectio[0] = {"k": "new"}
        row = objectio[0]
        assert row["k"] == "new"

    def test_column_access(self, objectio):
        rows = [{"x": 10, "y": 20}, {"x": 30, "y": 40}]
        objectio.extend(rows)
        col = objectio["x"]
        values = list(col)
        assert values == [10, 30]

    def test_remove(self, objectio):
        rows = [{"k": "v1"}]
        objectio.extend(rows)
        assert len(objectio) >= 1
        try:
            objectio.remove()
        except NotImplementedError:
            pytest.skip("Backend does not implement remove()")
