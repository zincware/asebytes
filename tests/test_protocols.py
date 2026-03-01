from typing import Any

import pytest

from asebytes._backends import ReadBackend, ReadWriteBackend


class MinimalReadable(ReadBackend):
    """Minimal implementation with only abstract methods."""

    def __init__(self, data: list[dict[str, Any]]):
        self._data = data

    def __len__(self) -> int:
        return len(self._data)

    def keys(self, index: int) -> list[str]:
        if not self._data:
            return []
        return list(self._data[index].keys())

    def get(self, index: int, keys: list[str] | None = None) -> dict[str, Any]:
        row = self._data[index]
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)


class MinimalWritable(MinimalReadable, ReadWriteBackend):
    """Minimal writable implementation."""

    def set(self, index: int, data: dict[str, Any]) -> None:
        if index < len(self._data):
            self._data[index] = data
        elif index == len(self._data):
            self._data.append(data)

    def insert(self, index: int, data: dict[str, Any]) -> None:
        self._data.insert(index, data)

    def delete(self, index: int) -> None:
        del self._data[index]

    def extend(self, data: list[dict[str, Any]]) -> int:
        self._data.extend(data)
        return len(self._data)


def test_readable_instantiation():
    backend = MinimalReadable([{"a": 1}, {"a": 2}])
    assert len(backend) == 2


def test_readable_get():
    backend = MinimalReadable([{"a": 1, "b": 2}])
    assert backend.get(0) == {"a": 1, "b": 2}


def test_readable_get_with_keys():
    backend = MinimalReadable([{"a": 1, "b": 2}])
    assert backend.get(0, keys=["a"]) == {"a": 1}


def test_readable_keys():
    backend = MinimalReadable([{"a": 1, "b": 2}])
    assert sorted(backend.keys(0)) == ["a", "b"]


def test_readable_get_many_default():
    """Default get_many loops over get."""
    backend = MinimalReadable([{"a": 1}, {"a": 2}, {"a": 3}])
    rows = backend.get_many([0, 2])
    assert rows == [{"a": 1}, {"a": 3}]


def test_readable_get_column_default():
    """Default get_column extracts single key from get."""
    backend = MinimalReadable([{"a": 1, "b": 10}, {"a": 2, "b": 20}])
    values = backend.get_column("a")
    assert values == [1, 2]


def test_readable_get_column_with_indices():
    backend = MinimalReadable([{"a": 1}, {"a": 2}, {"a": 3}])
    values = backend.get_column("a", indices=[0, 2])
    assert values == [1, 3]


def test_writable_set():
    backend = MinimalWritable([{"a": 1}])
    backend.set(0, {"a": 99})
    assert backend.get(0) == {"a": 99}


def test_writable_insert():
    backend = MinimalWritable([{"a": 1}, {"a": 3}])
    backend.insert(1, {"a": 2})
    assert len(backend) == 3
    assert backend.get(1) == {"a": 2}


def test_writable_delete():
    backend = MinimalWritable([{"a": 1}, {"a": 2}])
    backend.delete(0)
    assert len(backend) == 1
    assert backend.get(0) == {"a": 2}


def test_writable_extend():
    backend = MinimalWritable([])
    backend.extend([{"a": 1}, {"a": 2}])
    assert len(backend) == 2


def test_cannot_instantiate_abstract_readable():
    """ReadBackend cannot be instantiated without implementing abstract methods."""
    with pytest.raises(TypeError):
        ReadBackend()


def test_cannot_instantiate_abstract_writable():
    with pytest.raises(TypeError):
        ReadWriteBackend()
