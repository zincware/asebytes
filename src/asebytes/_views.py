from __future__ import annotations

from typing import Any, Iterator, Protocol, overload

import ase


class ViewParent(Protocol):
    """Protocol for objects that can serve as parent of RowView/ColumnView."""

    def __len__(self) -> int: ...
    def _read_row(self, index: int, keys: list[str] | None = None) -> dict[str, Any]: ...
    def _read_rows(self, indices: list[int], keys: list[str] | None = None) -> list[dict[str, Any]]: ...
    def _iter_rows(self, indices: list[int], keys: list[str] | None = None) -> Iterator[dict[str, Any]]: ...
    def _read_column(self, key: str, indices: list[int]) -> list[Any]: ...
    def _build_atoms(self, row: dict[str, Any]) -> ase.Atoms: ...


def _sub_select(
    current_indices: list[int],
    selector: int | slice | list[int],
) -> int | list[int]:
    """Apply a selector to current indices. Returns absolute index(es)."""
    if isinstance(selector, int):
        if selector < 0:
            selector += len(current_indices)
        return current_indices[selector]
    if isinstance(selector, slice):
        return current_indices[selector]
    if isinstance(selector, list):
        return [current_indices[i] for i in selector]
    raise TypeError(f"Unsupported selector type: {type(selector)}")


class RowView:
    """Lazy view over a subset of rows.

    Iteration yields ase.Atoms objects. Indexing with str or list[str]
    returns ColumnView for column-oriented access.
    """

    __slots__ = ("_parent", "_indices")

    def __init__(
        self,
        parent: ViewParent,
        indices: range | list[int],
    ):
        self._parent = parent
        self._indices = list(indices)

    def __len__(self) -> int:
        return len(self._indices)

    def __bool__(self) -> bool:
        return len(self._indices) > 0

    @overload
    def __getitem__(self, key: int) -> ase.Atoms: ...
    @overload
    def __getitem__(self, key: slice) -> RowView: ...
    @overload
    def __getitem__(self, key: list[int]) -> RowView: ...
    @overload
    def __getitem__(self, key: str) -> ColumnView: ...
    @overload
    def __getitem__(self, key: list[str]) -> ColumnView: ...

    def __getitem__(
        self, key: int | slice | str | list[int] | list[str]
    ) -> ase.Atoms | RowView | ColumnView:
        if isinstance(key, int):
            abs_idx = _sub_select(self._indices, key)
            row = self._parent._read_row(abs_idx)
            return self._parent._build_atoms(row)
        if isinstance(key, slice):
            new_indices = _sub_select(self._indices, key)
            return RowView(self._parent, new_indices)
        if isinstance(key, str):
            return ColumnView(self._parent, key, self._indices)
        if isinstance(key, list):
            if not key:
                return RowView(self._parent, [])
            if isinstance(key[0], int):
                new_indices = _sub_select(self._indices, key)
                return RowView(self._parent, new_indices)
            if isinstance(key[0], str):
                return ColumnView(self._parent, key, self._indices)
        raise TypeError(f"Unsupported key type: {type(key)}")

    def __iter__(self) -> Iterator[ase.Atoms]:
        """Stream rows one at a time (safe for large datasets)."""
        for row in self._parent._iter_rows(self._indices):
            yield self._parent._build_atoms(row)

    def chunked(self, chunk_size: int = 1000) -> Iterator[ase.Atoms]:
        """Iterate in chunks for throughput.

        Loads ``chunk_size`` rows at a time into memory, yielding
        one Atoms object per iteration. I/O happens at chunk boundaries.
        """
        for start in range(0, len(self._indices), chunk_size):
            chunk = self._indices[start : start + chunk_size]
            for row in self._parent._read_rows(chunk):
                yield self._parent._build_atoms(row)

    def to_list(self) -> list[ase.Atoms]:
        """Materialize all rows into memory."""
        return [
            self._parent._build_atoms(row)
            for row in self._parent._read_rows(self._indices)
        ]

    def __repr__(self) -> str:
        return f"RowView(len={len(self)})"


class ColumnView:
    """Lazy view over one or more columns.

    Single key (str): iteration yields individual values (float, ndarray, etc.).
    Multiple keys (list[str]): iteration yields dict[str, Any] per row.
    The _single flag controls unwrapping behavior -- same pattern as
    ASEIO.__getitem__ where int unwraps and list keeps the container.

    Materialization:
    - to_list() -> list[Any] (single) or list[dict[str, Any]] (multi)
    - to_dict() -> dict[str, list[Any]] (works for both)
    """

    __slots__ = ("_parent", "_keys", "_single", "_indices")

    def __init__(
        self,
        parent: ViewParent,
        keys: str | list[str],
        indices: range | list[int] | None = None,
    ):
        self._parent = parent
        self._single = isinstance(keys, str)
        self._keys = [keys] if self._single else keys
        self._indices = list(indices) if indices is not None else None

    def _resolved_indices(self) -> list[int]:
        if self._indices is not None:
            return self._indices
        return list(range(len(self._parent)))

    def __len__(self) -> int:
        if self._indices is not None:
            return len(self._indices)
        return len(self._parent)

    def __bool__(self) -> bool:
        return len(self) > 0

    @overload
    def __getitem__(self, key: int) -> Any: ...
    @overload
    def __getitem__(self, key: slice) -> ColumnView: ...
    @overload
    def __getitem__(self, key: list[int]) -> ColumnView: ...
    @overload
    def __getitem__(self, key: str) -> ColumnView: ...

    def __getitem__(
        self, key: int | slice | str | list[int]
    ) -> Any | ColumnView:
        indices = self._resolved_indices()
        if isinstance(key, int):
            abs_idx = _sub_select(indices, key)
            if self._single:
                return self._parent._read_column(self._keys[0], [abs_idx])[0]
            return self._parent._read_row(abs_idx, keys=self._keys)
        if isinstance(key, slice):
            new_indices = _sub_select(indices, key)
            return ColumnView(self._parent, self._keys[0] if self._single else self._keys, new_indices)
        if isinstance(key, str):
            return ColumnView(self._parent, key, indices)
        if isinstance(key, list):
            new_indices = _sub_select(indices, key)
            return ColumnView(self._parent, self._keys[0] if self._single else self._keys, new_indices)
        raise TypeError(f"Unsupported key type: {type(key)}")

    def __iter__(self) -> Iterator[Any]:
        indices = self._resolved_indices()
        if self._single:
            # Already batched -- read_column gets all indices at once
            yield from self._parent._read_column(self._keys[0], indices)
        else:
            # Batch read via read_rows to avoid N+1 query problem
            for row in self._parent._read_rows(indices, keys=self._keys):
                yield row

    def to_list(self) -> list[Any]:
        """Materialize as list.

        Single key: list of values (float, ndarray, etc.).
        Multi key: list of dicts.
        """
        return list(self)

    def to_dict(self) -> dict[str, list[Any]]:
        """Materialize as column-oriented dict.

        Works for both single and multi key:
        - single: {"calc.energy": [1.0, 2.0, 3.0]}
        - multi: {"calc.energy": [...], "calc.forces": [...]}
        """
        indices = self._resolved_indices()
        if self._single:
            return {self._keys[0]: self._parent._read_column(self._keys[0], indices)}
        # Batch read, then transpose to column-oriented
        result: dict[str, list[Any]] = {k: [] for k in self._keys}
        for row in self._parent._read_rows(indices, keys=self._keys):
            for k in self._keys:
                result[k].append(row[k])
        return result

    def __repr__(self) -> str:
        if self._single:
            return f"ColumnView(key={self._keys[0]!r}, len={len(self)})"
        return f"ColumnView(keys={self._keys!r}, len={len(self)})"
