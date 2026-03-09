"""Tests for the in-memory backend."""

import uuid

import pytest

from asebytes.memory._backend import MemoryObjectBackend, _GLOBAL_STORAGE


@pytest.fixture
def backend():
    """Create a backend with a unique group for test isolation."""
    group_name = f"test_{uuid.uuid4().hex[:8]}"
    b = MemoryObjectBackend(group=group_name)
    yield b
    # Clean up after test
    b.remove()


class TestMemoryObjectBackend:
    def test_empty_on_creation(self, backend):
        assert len(backend) == 0

    def test_extend_and_get(self, backend):
        backend.extend([{"a": 1}, {"a": 2}])
        assert len(backend) == 2
        assert backend.get(0) == {"a": 1}
        assert backend.get(1) == {"a": 2}

    def test_extend_returns_length(self, backend):
        assert backend.extend([{"a": 1}]) == 1
        assert backend.extend([{"a": 2}, {"a": 3}]) == 3

    def test_set(self, backend):
        backend.extend([{"a": 1}])
        backend.set(0, {"a": 99})
        assert backend.get(0) == {"a": 99}

    def test_delete(self, backend):
        backend.extend([{"a": 1}, {"a": 2}, {"a": 3}])
        backend.delete(1)
        assert len(backend) == 2
        assert backend.get(1) == {"a": 3}

    def test_insert(self, backend):
        backend.extend([{"a": 1}, {"a": 3}])
        backend.insert(1, {"a": 2})
        assert len(backend) == 3
        assert backend.get(1) == {"a": 2}
        assert backend.get(2) == {"a": 3}

    def test_get_with_keys(self, backend):
        backend.extend([{"a": 1, "b": 2, "c": 3}])
        result = backend.get(0, keys=["a", "c"])
        assert result == {"a": 1, "c": 3}

    def test_get_none_placeholder(self, backend):
        backend.extend([None])
        assert backend.get(0) is None

    def test_clear(self, backend):
        backend.extend([{"a": 1}, {"a": 2}])
        backend.clear()
        assert len(backend) == 0

    def test_reserve(self, backend):
        backend.reserve(3)
        assert len(backend) == 3
        assert backend.get(0) is None
        assert backend.get(2) is None

    def test_remove(self, backend):
        backend.extend([{"a": 1}])
        backend.remove()
        # After remove, the group is deleted, so len will recreate it as empty
        assert len(backend) == 0

    def test_keys(self, backend):
        backend.extend([{"x": 1, "y": 2}])
        assert sorted(backend.keys(0)) == ["x", "y"]

    def test_keys_none_placeholder(self, backend):
        backend.extend([None])
        assert backend.keys(0) == []

    def test_update(self, backend):
        backend.extend([{"a": 1, "b": 2}])
        backend.update(0, {"b": 99, "c": 3})
        assert backend.get(0) == {"a": 1, "b": 99, "c": 3}

    def test_get_column(self, backend):
        backend.extend([{"a": 1}, {"a": 2}, {"a": 3}])
        assert backend.get_column("a") == [1, 2, 3]

    def test_index_error(self, backend):
        with pytest.raises(IndexError):
            backend.get(0)

    def test_from_uri(self):
        group_name = f"test_{uuid.uuid4().hex[:8]}"
        backend = MemoryObjectBackend.from_uri("memory://", group=group_name)
        try:
            assert isinstance(backend, MemoryObjectBackend)
            assert len(backend) == 0
        finally:
            backend.remove()

    def test_from_uri_with_path(self):
        group_name = f"test_{uuid.uuid4().hex[:8]}"
        backend = MemoryObjectBackend.from_uri("memory:///my-store", group=group_name)
        try:
            assert isinstance(backend, MemoryObjectBackend)
        finally:
            backend.remove()


# ======================================================================
# Group parameter tests
# ======================================================================


class TestMemoryObjectBackendGroup:
    """Tests for the group parameter functionality."""

    def test_group_parameter_default(self):
        """Test that group parameter defaults to 'default'."""
        backend = MemoryObjectBackend()
        assert backend.group == "default"

    def test_group_parameter_custom(self):
        """Test that custom group parameter is set correctly."""
        backend = MemoryObjectBackend(group="my_group")
        assert backend.group == "my_group"

    def test_groups_are_isolated(self):
        """Test that different groups are isolated from each other."""
        backend_a = MemoryObjectBackend(group="group_a")
        backend_b = MemoryObjectBackend(group="group_b")

        backend_a.extend([{"x": 1}])
        backend_b.extend([{"y": 2}])

        # Each backend should only see its own data
        assert len(backend_a) == 1
        assert len(backend_b) == 1
        assert backend_a.get(0) == {"x": 1}
        assert backend_b.get(0) == {"y": 2}

        # Clean up
        backend_a.remove()
        backend_b.remove()

    def test_same_group_shares_data(self):
        """Test that two backends with the same group share data."""
        backend1 = MemoryObjectBackend(group="shared_group")
        backend2 = MemoryObjectBackend(group="shared_group")

        backend1.extend([{"x": 1}])

        # Both should see the same data
        assert len(backend1) == 1
        assert len(backend2) == 1
        assert backend2.get(0) == {"x": 1}

        # Clean up
        backend1.remove()

    def test_list_groups(self):
        """Test listing available groups."""
        # Create some backends with different groups
        backend_a = MemoryObjectBackend(group="list_test_a")
        backend_b = MemoryObjectBackend(group="list_test_b")

        # Extend to ensure groups are registered
        backend_a.extend([{"x": 1}])
        backend_b.extend([{"y": 2}])

        groups = MemoryObjectBackend.list_groups(path="memory://")
        assert "list_test_a" in groups
        assert "list_test_b" in groups

        # Clean up
        backend_a.remove()
        backend_b.remove()

    def test_from_uri_with_group(self):
        """Test from_uri with group parameter."""
        backend = MemoryObjectBackend.from_uri("memory://", group="uri_group")
        assert backend.group == "uri_group"
        backend.extend([{"x": 1}])
        assert len(backend) == 1
        backend.remove()

    def test_clear_vs_remove(self):
        """Test that clear() clears data but remove() removes the group."""
        backend = MemoryObjectBackend(group="clear_test")
        backend.extend([{"x": 1}])

        # Clear should empty the list
        backend.clear()
        assert len(backend) == 0

        # Group should still exist
        groups = MemoryObjectBackend.list_groups(path="memory://")
        assert "clear_test" in groups

        # Add data again
        backend.extend([{"x": 2}])

        # Remove should delete the group entirely
        backend.remove()
        groups = MemoryObjectBackend.list_groups(path="memory://")
        assert "clear_test" not in groups
