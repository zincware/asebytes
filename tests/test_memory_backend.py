"""Tests for the in-memory backend."""

import pytest

from asebytes.memory._backend import MemoryObjectBackend


class TestMemoryObjectBackend:
    def test_empty_on_creation(self):
        backend = MemoryObjectBackend()
        assert len(backend) == 0

    def test_extend_and_get(self):
        backend = MemoryObjectBackend()
        backend.extend([{"a": 1}, {"a": 2}])
        assert len(backend) == 2
        assert backend.get(0) == {"a": 1}
        assert backend.get(1) == {"a": 2}

    def test_extend_returns_length(self):
        backend = MemoryObjectBackend()
        assert backend.extend([{"a": 1}]) == 1
        assert backend.extend([{"a": 2}, {"a": 3}]) == 3

    def test_set(self):
        backend = MemoryObjectBackend()
        backend.extend([{"a": 1}])
        backend.set(0, {"a": 99})
        assert backend.get(0) == {"a": 99}

    def test_delete(self):
        backend = MemoryObjectBackend()
        backend.extend([{"a": 1}, {"a": 2}, {"a": 3}])
        backend.delete(1)
        assert len(backend) == 2
        assert backend.get(1) == {"a": 3}

    def test_insert(self):
        backend = MemoryObjectBackend()
        backend.extend([{"a": 1}, {"a": 3}])
        backend.insert(1, {"a": 2})
        assert len(backend) == 3
        assert backend.get(1) == {"a": 2}
        assert backend.get(2) == {"a": 3}

    def test_get_with_keys(self):
        backend = MemoryObjectBackend()
        backend.extend([{"a": 1, "b": 2, "c": 3}])
        result = backend.get(0, keys=["a", "c"])
        assert result == {"a": 1, "c": 3}

    def test_get_none_placeholder(self):
        backend = MemoryObjectBackend()
        backend.extend([None])
        assert backend.get(0) is None

    def test_clear(self):
        backend = MemoryObjectBackend()
        backend.extend([{"a": 1}, {"a": 2}])
        backend.clear()
        assert len(backend) == 0

    def test_reserve(self):
        backend = MemoryObjectBackend()
        backend.reserve(3)
        assert len(backend) == 3
        assert backend.get(0) is None
        assert backend.get(2) is None

    def test_remove(self):
        backend = MemoryObjectBackend()
        backend.extend([{"a": 1}])
        backend.remove()
        assert len(backend) == 0

    def test_keys(self):
        backend = MemoryObjectBackend()
        backend.extend([{"x": 1, "y": 2}])
        assert sorted(backend.keys(0)) == ["x", "y"]

    def test_keys_none_placeholder(self):
        backend = MemoryObjectBackend()
        backend.extend([None])
        assert backend.keys(0) == []

    def test_update(self):
        backend = MemoryObjectBackend()
        backend.extend([{"a": 1, "b": 2}])
        backend.update(0, {"b": 99, "c": 3})
        assert backend.get(0) == {"a": 1, "b": 99, "c": 3}

    def test_get_column(self):
        backend = MemoryObjectBackend()
        backend.extend([{"a": 1}, {"a": 2}, {"a": 3}])
        assert backend.get_column("a") == [1, 2, 3]

    def test_index_error(self):
        backend = MemoryObjectBackend()
        with pytest.raises(IndexError):
            backend.get(0)

    def test_from_uri(self):
        backend = MemoryObjectBackend.from_uri("memory://")
        assert isinstance(backend, MemoryObjectBackend)
        assert len(backend) == 0

    def test_from_uri_with_path(self):
        backend = MemoryObjectBackend.from_uri("memory:///my-store")
        assert isinstance(backend, MemoryObjectBackend)
