"""ConcatView -- lazy read-only concatenation of IO facades."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from typing import Any, Generic, TypeVar

from ._views import ASEColumnView, ColumnView, RowView

T = TypeVar("T")


class ConcatView(Generic[T]):
    """Lazy read-only concatenation of multiple IO instances.

    All sources must be the same IO class. Create via ``io1 + io2`` or
    ``sum([io1, io2, io3], [])``.

    Supports: ``__len__``, ``__iter__``, ``__getitem__`` (int, slice,
    list[int], str/bytes, list[str/bytes]).
    """

    __slots__ = ("_sources", "_column_view_cls")

    def __init__(self, sources: list) -> None:
        if not sources:
            raise ValueError("ConcatView requires at least one source")
        first_type = type(sources[0])
        for s in sources[1:]:
            if type(s) is not first_type:
                raise TypeError(
                    f"Cannot concat {first_type.__name__} with {type(s).__name__}"
                )
        self._sources = list(sources)
        from .io import ASEIO

        self._column_view_cls = (
            ASEColumnView if isinstance(sources[0], ASEIO) else ColumnView
        )

    # --- Length ---

    def __len__(self) -> int:
        return sum(len(s) for s in self._sources)

    # --- Index mapping ---

    def _locate(self, global_idx: int) -> tuple[int, int]:
        """Map a global index to (source_index, local_index). O(n_sources)."""
        offset = 0
        for i, src in enumerate(self._sources):
            n = len(src)
            if global_idx < offset + n:
                return i, global_idx - offset
            offset += n
        raise IndexError(global_idx)

    # --- ViewParent protocol (read side) ---

    def _read_row(self, index: int, keys: list | None = None) -> dict:
        src_i, local_i = self._locate(index)
        return self._sources[src_i]._read_row(local_i, keys)

    def _read_rows(self, indices: list[int], keys: list | None = None) -> list:
        """Batch read, grouped by source to minimise I/O calls."""
        buckets: dict[int, list[tuple[int, int]]] = defaultdict(list)
        for pos, gi in enumerate(indices):
            src_i, li = self._locate(gi)
            buckets[src_i].append((pos, li))
        result: list = [None] * len(indices)
        for src_i, pairs in buckets.items():
            positions, local_idxs = zip(*pairs)
            rows = self._sources[src_i]._read_rows(list(local_idxs), keys)
            for pos, row in zip(positions, rows):
                result[pos] = row
        return result

    def _iter_rows(self, indices: list[int], keys: list | None = None) -> Iterator:
        for gi in indices:
            src_i, local_i = self._locate(gi)
            yield from self._sources[src_i]._iter_rows([local_i], keys)

    def _read_column(self, key: Any, indices: list[int]) -> list:
        buckets: dict[int, list[tuple[int, int]]] = defaultdict(list)
        for pos, gi in enumerate(indices):
            src_i, li = self._locate(gi)
            buckets[src_i].append((pos, li))
        result: list = [None] * len(indices)
        for src_i, pairs in buckets.items():
            positions, local_idxs = zip(*pairs)
            values = self._sources[src_i]._read_column(key, list(local_idxs))
            for pos, val in zip(positions, values):
                result[pos] = val
        return result

    def _build_result(self, row: dict) -> T:
        return self._sources[0]._build_result(row)

    # --- ViewParent protocol (write side — all raise) ---

    def _write_row(self, index: int, data: Any) -> None:
        raise TypeError("ConcatView is read-only")

    def _update_row(self, index: int, data: dict) -> None:
        raise TypeError("ConcatView is read-only")

    def _delete_row(self, index: int) -> None:
        raise TypeError("ConcatView is read-only")

    def _delete_rows(self, start: int, stop: int) -> None:
        raise TypeError("ConcatView is read-only")

    def _drop_keys(self, keys: list, indices: list[int]) -> None:
        raise TypeError("ConcatView is read-only")

    def _update_many(self, start: int, data: list) -> None:
        raise TypeError("ConcatView is read-only")

    def _set_column(self, key: Any, start: int, values: list) -> None:
        raise TypeError("ConcatView is read-only")

    def _write_many(self, start: int, data: list) -> None:
        raise TypeError("ConcatView is read-only")

    # --- Public interface ---

    def __getitem__(self, index: Any) -> Any:
        if isinstance(index, int):
            n = len(self)
            if index < 0:
                index += n
            if index < 0 or index >= n:
                raise IndexError(index)
            src_i, local_i = self._locate(index)
            row = self._sources[src_i]._read_row(local_i)
            return self._build_result(row)
        if isinstance(index, slice):
            indices = list(range(len(self))[index])
            return RowView(self, indices, column_view_cls=self._column_view_cls)
        if isinstance(index, (str, bytes)):
            return self._column_view_cls(self, index)
        if isinstance(index, list):
            if not index:
                return RowView(self, [], column_view_cls=self._column_view_cls)
            if isinstance(index[0], int):
                n = len(self)
                normalized = []
                for i in index:
                    idx = i + n if i < 0 else i
                    if idx < 0 or idx >= n:
                        raise IndexError(i)
                    normalized.append(idx)
                return RowView(self, normalized, column_view_cls=self._column_view_cls)
            if isinstance(index[0], (str, bytes)):
                return self._column_view_cls(self, index)
        raise TypeError(f"Unsupported index type: {type(index)}")

    def __iter__(self) -> Iterator[T]:
        for src in self._sources:
            yield from src

    def __add__(self, other: Any) -> ConcatView:
        if isinstance(other, ConcatView):
            # Flatten: verify type compatibility
            if type(other._sources[0]) is not type(self._sources[0]):
                raise TypeError(
                    f"Cannot concat {type(self._sources[0]).__name__} "
                    f"with {type(other._sources[0]).__name__}"
                )
            return ConcatView(self._sources + other._sources)
        if type(other) is not type(self._sources[0]):
            raise TypeError(
                f"Cannot concat {type(self._sources[0]).__name__} "
                f"with {type(other).__name__}"
            )
        return ConcatView(self._sources + [other])

    def __repr__(self) -> str:
        src_type = type(self._sources[0]).__name__
        return (
            f"ConcatView({src_type}, n_sources={len(self._sources)}, "
            f"len={len(self)})"
        )
