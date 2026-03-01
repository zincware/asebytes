from __future__ import annotations

from typing import Any, Generic, Iterator, Protocol, TypeVar, overload

import ase

R = TypeVar("R")


class ViewParent(Protocol[R]):
    """Protocol for objects that can serve as parent of RowView/ColumnView."""

    def __len__(self) -> int: ...
    def _read_row(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any]: ...
    def _read_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any]]: ...
    def _iter_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> Iterator[dict[str, Any]]: ...
    def _read_column(self, key: str, indices: list[int]) -> list[Any]: ...
    def _build_result(self, row: dict[str, Any]) -> R: ...
    def _write_row(self, index: int, data: Any) -> None: ...
    def _update_row(self, index: int, data: dict[str, Any]) -> None: ...
    def _delete_row(self, index: int) -> None: ...
    def _delete_rows(self, start: int, stop: int) -> None: ...
    def _drop_keys(self, keys: list, indices: list[int]) -> None: ...
    def _update_many(self, start: int, data: list[dict[str, Any]]) -> None: ...
    def _set_column(self, key: str, start: int, values: list[Any]) -> None: ...
    def _write_many(self, start: int, data: list[Any]) -> None: ...


def _is_contiguous(indices: list[int]) -> bool:
    """Check if indices form a contiguous ascending range."""
    if len(indices) <= 1:
        return True
    for i in range(1, len(indices)):
        if indices[i] != indices[i - 1] + 1:
            return False
    return True


def _sub_select(
    current_indices: list[int],
    selector: int | slice | list[int],
) -> int | list[int]:
    """Apply a selector to current indices. Returns absolute index(es)."""
    if isinstance(selector, int):
        if selector < 0:
            selector += len(current_indices)
            if selector < 0:
                raise IndexError(selector - len(current_indices))
        if selector >= len(current_indices):
            raise IndexError(selector)
        return current_indices[selector]
    if isinstance(selector, slice):
        return current_indices[selector]
    if isinstance(selector, list):
        return [current_indices[i] for i in selector]
    raise TypeError(f"Unsupported selector type: {type(selector)}")


class RowView(Generic[R]):
    """Lazy view over a subset of rows.

    Iteration yields result objects (type R). Indexing with str or list[str]
    returns ColumnView for column-oriented access.
    """

    __slots__ = ("_parent", "_indices", "_column_view_cls")

    def __init__(
        self,
        parent: ViewParent[R],
        indices: range | list[int],
        *,
        column_view_cls: type[ColumnView] | None = None,
    ):
        self._parent = parent
        self._indices = list(indices)
        self._column_view_cls = column_view_cls or ColumnView

    def __len__(self) -> int:
        return len(self._indices)

    def __bool__(self) -> bool:
        return len(self._indices) > 0

    @overload
    def __getitem__(self, key: int) -> R: ...
    @overload
    def __getitem__(self, key: slice) -> RowView[R]: ...
    @overload
    def __getitem__(self, key: list[int]) -> RowView[R]: ...
    @overload
    def __getitem__(self, key: str) -> ColumnView: ...
    @overload
    def __getitem__(self, key: list[str]) -> ColumnView: ...

    def __getitem__(
        self, key: int | slice | str | list[int] | list[str]
    ) -> R | RowView[R] | ColumnView:
        if isinstance(key, int):
            abs_idx = _sub_select(self._indices, key)
            row = self._parent._read_row(abs_idx)
            return self._parent._build_result(row)
        if isinstance(key, slice):
            new_indices = _sub_select(self._indices, key)
            return RowView(
                self._parent, new_indices, column_view_cls=self._column_view_cls
            )
        if isinstance(key, (str, bytes)):
            return self._column_view_cls(self._parent, key, self._indices)
        if isinstance(key, list):
            if not key:
                return RowView(self._parent, [], column_view_cls=self._column_view_cls)
            if isinstance(key[0], int):
                new_indices = _sub_select(self._indices, key)
                return RowView(
                    self._parent, new_indices, column_view_cls=self._column_view_cls
                )
            if isinstance(key[0], (str, bytes)):
                return self._column_view_cls(self._parent, key, self._indices)
        raise TypeError(f"Unsupported key type: {type(key)}")

    def __iter__(self) -> Iterator[R]:
        """Stream rows one at a time (safe for large datasets)."""
        for row in self._parent._iter_rows(self._indices):
            yield self._parent._build_result(row)

    def chunked(self, chunk_size: int = 1000) -> Iterator[R]:
        """Iterate in chunks for throughput.

        Loads ``chunk_size`` rows at a time into memory, yielding
        one result object per iteration. I/O happens at chunk boundaries.
        """
        for start in range(0, len(self._indices), chunk_size):
            chunk = self._indices[start : start + chunk_size]
            for row in self._parent._read_rows(chunk):
                yield self._parent._build_result(row)

    def to_list(self) -> list[R]:
        """Materialize all rows into memory."""
        return [
            self._parent._build_result(row)
            for row in self._parent._read_rows(self._indices)
        ]

    def set(self, data: list) -> None:
        """Overwrite rows with new data (list of dicts)."""
        if not isinstance(data, list):
            raise TypeError(f"Row writes must be lists. Got {type(data).__name__}.")
        if len(data) != len(self._indices):
            raise ValueError(
                f"Length mismatch: got {len(data)} values for "
                f"{len(self._indices)} rows."
            )
        for d in data:
            if isinstance(d, (list, tuple)) and not isinstance(d, dict):
                raise ValueError(
                    "Row writes expect dicts, not lists-of-lists. "
                    "For positional array writes, use column-filtered access: "
                    "db[['key1','key2']][:n].set(data)"
                )
        if self._indices and _is_contiguous(self._indices):
            self._parent._write_many(self._indices[0], data)
        else:
            for idx, d in zip(self._indices, data):
                self._parent._write_row(idx, d)

    def update(self, data: dict) -> None:
        """Merge dict into all rows in this view."""
        if not isinstance(data, dict):
            raise TypeError(f"update() requires a dict. Got {type(data).__name__}.")
        if self._indices and _is_contiguous(self._indices):
            self._parent._update_many(self._indices[0], [data] * len(self._indices))
        else:
            for idx in self._indices:
                self._parent._update_row(idx, data)

    def delete(self) -> None:
        """Delete all rows in this view (must be contiguous)."""
        if not self._indices:
            return
        # Check contiguity
        for i in range(1, len(self._indices)):
            if self._indices[i] != self._indices[i - 1] + 1:
                raise TypeError(
                    "delete() requires contiguous indices. "
                    "Non-contiguous delete is ambiguous due to index shifting."
                )
        self._parent._delete_rows(self._indices[0], self._indices[-1] + 1)

    def drop(self, keys: list) -> None:
        """Remove specified keys from all rows in this view."""
        self._parent._drop_keys(keys, self._indices)

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
        parent: ViewParent[Any],
        keys: str | bytes | list[str] | list[bytes],
        indices: range | list[int] | None = None,
    ):
        self._parent = parent
        self._single = isinstance(keys, (str, bytes))
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

    def __getitem__(self, key: int | slice | str | list[int]) -> Any | ColumnView:
        indices = self._resolved_indices()
        if isinstance(key, int):
            abs_idx = _sub_select(indices, key)
            if self._single:
                return self._parent._read_column(self._keys[0], [abs_idx])[0]
            row = self._parent._read_row(abs_idx, keys=self._keys)
            return None if row is None else [row.get(k) for k in self._keys]
        if isinstance(key, slice):
            new_indices = _sub_select(indices, key)
            return ColumnView(
                self._parent, self._keys[0] if self._single else self._keys, new_indices
            )
        if isinstance(key, (str, bytes)):
            return ColumnView(self._parent, key, indices)
        if isinstance(key, list):
            new_indices = _sub_select(indices, key)
            return ColumnView(
                self._parent, self._keys[0] if self._single else self._keys, new_indices
            )
        raise TypeError(f"Unsupported key type: {type(key)}")

    def __iter__(self) -> Iterator[Any]:
        indices = self._resolved_indices()
        if self._single:
            # Already batched -- read_column gets all indices at once
            yield from self._parent._read_column(self._keys[0], indices)
        else:
            # Batch read via read_rows to avoid N+1 query problem
            for row in self._parent._read_rows(indices, keys=self._keys):
                yield None if row is None else [row.get(k) for k in self._keys]

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
                result[k].append(row.get(k) if row is not None else None)
        return result

    def set(self, data: list) -> None:
        """Write positional data back to the underlying rows.

        Single-key: flat list → update each row with {key: value}.
        Multi-key: list-of-lists → validate inner length, update each row.
        """
        if not isinstance(data, list):
            raise TypeError(
                f"Column-filtered writes must be lists. Got {type(data).__name__}."
            )
        indices = self._resolved_indices()
        if len(data) != len(indices):
            raise ValueError(
                f"Length mismatch: got {len(data)} values for {len(indices)} rows."
            )
        if self._single:
            if _is_contiguous(indices):
                self._parent._set_column(self._keys[0], indices[0], data)
            else:
                for idx, value in zip(indices, data):
                    self._parent._update_row(idx, {self._keys[0]: value})
        else:
            n_keys = len(self._keys)
            # Validate all inner lengths first
            for row_values in data:
                if not isinstance(row_values, (list, tuple)):
                    raise TypeError(
                        f"Multi-key writes require list-of-lists. "
                        f"Got {type(row_values).__name__} at position."
                    )
                if len(row_values) != n_keys:
                    raise ValueError(
                        f"Inner length mismatch: got {len(row_values)} values, "
                        f"expected {n_keys} keys."
                    )
            if _is_contiguous(indices):
                dicts = [dict(zip(self._keys, row_values)) for row_values in data]
                self._parent._update_many(indices[0], dicts)
            else:
                for idx, row_values in zip(indices, data):
                    self._parent._update_row(idx, dict(zip(self._keys, row_values)))

    def __repr__(self) -> str:
        if self._single:
            return f"ColumnView(key={self._keys[0]!r}, len={len(self)})"
        return f"ColumnView(keys={self._keys!r}, len={len(self)})"


class ASEColumnView(ColumnView):
    """ColumnView that wraps every materialized row through dict_to_atoms().

    ASEIO always returns Atoms from column access — the str vs list[str]
    distinction controls which keys are loaded, not the output type.
    """

    @overload
    def __getitem__(self, key: int) -> ase.Atoms: ...
    @overload
    def __getitem__(self, key: slice) -> ASEColumnView: ...
    @overload
    def __getitem__(self, key: list[int]) -> ASEColumnView: ...
    @overload
    def __getitem__(self, key: str) -> ASEColumnView: ...

    def __getitem__(
        self, key: int | slice | str | list[int]
    ) -> ase.Atoms | ASEColumnView:
        indices = self._resolved_indices()
        if isinstance(key, int):
            abs_idx = _sub_select(indices, key)
            row = self._parent._read_row(abs_idx, keys=self._keys)
            if row is None:
                raise TypeError("Cannot build ase.Atoms from a placeholder row.")
            return self._parent._build_result(row)
        if isinstance(key, slice):
            new_indices = _sub_select(indices, key)
            return ASEColumnView(
                self._parent, self._keys[0] if self._single else self._keys, new_indices
            )
        if isinstance(key, str):
            return ASEColumnView(self._parent, key, indices)
        if isinstance(key, list):
            new_indices = _sub_select(indices, key)
            return ASEColumnView(
                self._parent, self._keys[0] if self._single else self._keys, new_indices
            )
        raise TypeError(f"Unsupported key type: {type(key)}")

    def __iter__(self) -> Iterator[ase.Atoms]:
        indices = self._resolved_indices()
        for row in self._parent._read_rows(indices, keys=self._keys):
            if row is None:
                raise TypeError("Cannot build ase.Atoms from a placeholder row.")
            yield self._parent._build_result(row)

    def to_list(self) -> list[ase.Atoms]:
        return list(self)

    def to_dict(self) -> None:
        raise TypeError(
            "to_dict() is not available on ASEIO column views. "
            "ASEIO always returns ase.Atoms — use to_list() instead."
        )

    def __repr__(self) -> str:
        if self._single:
            return f"ASEColumnView(key={self._keys[0]!r}, len={len(self)})"
        return f"ASEColumnView(keys={self._keys!r}, len={len(self)})"
