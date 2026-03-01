"""Async awaitable views for AsyncASEIO / AsyncObjectIO / AsyncBlobIO.

__getitem__ on the parent is sync and returns one of these views.
Materialization happens when you call ``.to_list()`` / ``.to_dict()``
on multi-element views, or ``await`` on single-element views.

__await__ semantics (single-element only):
- AsyncSingleRowView   → single row (dict or Atoms or None)
- AsyncSingleColumnView → single scalar value
"""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Generic,
    Protocol,
    TypeVar,
    overload,
)

if TYPE_CHECKING:
    import ase

R = TypeVar("R")


class AsyncViewParent(Protocol[R]):
    """Protocol for objects that serve as parent of async views."""

    def __len__(self) -> int: ...
    async def len(self) -> int: ...
    async def _read_row(self, index: int, keys: list[str] | None = None) -> Any: ...
    async def _read_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[Any]: ...
    async def _read_column(self, key: str, indices: list[int]) -> list[Any]: ...
    async def _write_row(self, index: int, data: Any) -> None: ...
    async def _delete_row(self, index: int) -> None: ...
    async def _delete_rows(self, start: int, stop: int) -> None: ...
    async def _update_row(self, index: int, data: Any) -> None: ...
    async def _drop_keys(self, keys: list[str], indices: list[int]) -> None: ...
    async def _update_many(self, start: int, data: list[dict[str, Any]]) -> None: ...
    async def _set_column(self, key: str, start: int, values: list[Any]) -> None: ...
    async def _write_many(self, start: int, data: list[Any]) -> None: ...
    async def _keys(self, index: int) -> list[str]: ...
    def _build_result(self, row: Any) -> R: ...


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


def _is_contiguous(indices: list[int]) -> bool:
    """Check if indices form a contiguous ascending range."""
    if len(indices) <= 1:
        return True
    for i in range(1, len(indices)):
        if indices[i] != indices[i - 1] + 1:
            return False
    return True


# ── AsyncSingleRowView ──────────────────────────────────────────────────


class AsyncSingleRowView(Generic[R]):
    """Awaitable view over a single row.

    ``await view`` returns the row data (or None for placeholders).
    Supports key subscripting: ``view["key"]`` or ``view[b"key"]`` returns
    an awaitable column value, mirroring sync ``db[0]["key"]``.
    """

    __slots__ = ("_parent", "_index")

    def __init__(self, parent: AsyncViewParent[R], index: int):
        self._parent = parent
        self._index = index

    def __await__(self):
        return self._materialize().__await__()

    async def _resolve_index(self) -> int:
        """Resolve negative indices via len()."""
        idx = self._index
        if idx < 0:
            try:
                n = len(self._parent)
            except TypeError:
                # async can't do __len__
                n = await self._parent.len()
            idx += n
            if idx < 0:
                raise IndexError(self._index)
        return idx

    async def _materialize(self) -> R:
        idx = await self._resolve_index()
        row = await self._parent._read_row(idx)
        return self._parent._build_result(row)

    def __getitem__(
        self, key: str | bytes | list[str] | list[bytes]
    ) -> AsyncSingleColumnView:
        if isinstance(key, (str, bytes)):
            keys = [key]
            single = True
        elif isinstance(key, list):
            keys = list(key)
            single = False
        else:
            raise TypeError(f"Unsupported key type: {type(key)}")
        return AsyncSingleColumnView(self._parent, keys, single, self._index)

    async def set(self, data: Any) -> None:
        idx = await self._resolve_index()
        await self._parent._write_row(idx, data)

    async def delete(self) -> None:
        idx = await self._resolve_index()
        await self._parent._delete_row(idx)

    async def update(self, data: dict) -> None:
        idx = await self._resolve_index()
        await self._parent._update_row(idx, data)

    async def keys(self) -> list[str]:
        idx = await self._resolve_index()
        return await self._parent._keys(idx)

    def __repr__(self) -> str:
        return f"AsyncSingleRowView(index={self._index})"


# ── AsyncRowView ────────────────────────────────────────────────────────


class AsyncRowView(Generic[R]):
    """Lazy view over multiple rows.

    Use ``.to_list()`` to materialize all rows, or
    ``async for row in view`` to stream rows one at a time.
    """

    __slots__ = ("_parent", "_indices", "_contiguous", "_column_view_cls")

    def __init__(
        self,
        parent: AsyncViewParent[R],
        indices: list[int],
        *,
        contiguous: bool | None = None,
        column_view_cls: type[AsyncColumnView] | None = None,
    ):
        self._parent = parent
        self._indices = indices
        self._contiguous = (
            contiguous if contiguous is not None else _is_contiguous(indices)
        )
        self._column_view_cls = column_view_cls or AsyncColumnView

    def __len__(self) -> int:
        return len(self._indices)

    def __bool__(self) -> bool:
        return len(self._indices) > 0

    async def to_list(self) -> list[R]:
        """Materialize all rows into a list."""
        rows = await self._parent._read_rows(self._indices)
        return [self._parent._build_result(r) for r in rows]

    async def __aiter__(self) -> AsyncIterator[R]:
        for i in self._indices:
            row = await self._parent._read_row(i)
            yield self._parent._build_result(row)

    async def chunked(self, chunk_size: int = 1000) -> AsyncIterator[R]:
        """Iterate in chunks for throughput. Yields individual items."""
        for start in range(0, len(self._indices), chunk_size):
            chunk = self._indices[start : start + chunk_size]
            rows = await self._parent._read_rows(chunk)
            for row in rows:
                yield self._parent._build_result(row)

    @overload
    def __getitem__(self, key: int) -> AsyncSingleRowView[R]: ...
    @overload
    def __getitem__(self, key: slice) -> AsyncRowView[R]: ...
    @overload
    def __getitem__(self, key: list[int]) -> AsyncRowView[R]: ...
    @overload
    def __getitem__(self, key: str) -> AsyncColumnView: ...
    @overload
    def __getitem__(self, key: list[str]) -> AsyncColumnView: ...

    def __getitem__(
        self, key: int | slice | str | list[int] | list[str]
    ) -> AsyncSingleRowView[R] | AsyncRowView[R] | AsyncColumnView:
        if isinstance(key, int):
            abs_idx = _sub_select(self._indices, key)
            return AsyncSingleRowView(self._parent, abs_idx)
        if isinstance(key, slice):
            new_indices = _sub_select(self._indices, key)
            return AsyncRowView(
                self._parent, new_indices, column_view_cls=self._column_view_cls
            )
        if isinstance(key, (str, bytes)):
            return self._column_view_cls(self._parent, key, self._indices)
        if isinstance(key, list):
            if not key:
                return AsyncRowView(
                    self._parent, [], column_view_cls=self._column_view_cls
                )
            if isinstance(key[0], int):
                new_indices = _sub_select(self._indices, key)
                return AsyncRowView(
                    self._parent,
                    new_indices,
                    contiguous=False,
                    column_view_cls=self._column_view_cls,
                )
            if isinstance(key[0], (str, bytes)):
                return self._column_view_cls(self._parent, key, self._indices)
        raise TypeError(f"Unsupported key type: {type(key)}")

    async def set(self, data: list[Any]) -> None:
        if not isinstance(data, list):
            raise TypeError(f"Row writes must be lists. Got {type(data).__name__}.")
        if len(data) != len(self._indices):
            raise ValueError(
                f"Length mismatch: got {len(data)} values for "
                f"{len(self._indices)} rows."
            )
        if self._indices and _is_contiguous(self._indices):
            await self._parent._write_many(self._indices[0], data)
        else:
            for idx, d in zip(self._indices, data, strict=True):
                await self._parent._write_row(idx, d)

    async def delete(self) -> None:
        if not self._contiguous:
            raise TypeError(
                "delete() requires contiguous indices. "
                "Non-contiguous delete is ambiguous due to index shifting. "
                "Use set([None, ...]) to empty slots without shifting."
            )
        if not self._indices:
            return
        await self._parent._delete_rows(self._indices[0], self._indices[-1] + 1)

    async def update(self, data: dict) -> None:
        if self._indices and _is_contiguous(self._indices):
            await self._parent._update_many(
                self._indices[0], [data] * len(self._indices)
            )
        else:
            for idx in self._indices:
                await self._parent._update_row(idx, data)

    async def drop(self, keys: list[str]) -> None:
        await self._parent._drop_keys(keys, self._indices)

    def __repr__(self) -> str:
        return f"AsyncRowView(len={len(self)})"


# ── AsyncSingleColumnView ────────────────────────────────────────────────


class AsyncSingleColumnView:
    """Awaitable view that reads a single column value at one row index.

    Mirrors the sync ``ColumnView.__getitem__(int)`` behavior:
    - Single key: returns the scalar/array value from ``_read_column``.
    - Multi key: returns ``[val_a, val_b, ...]`` from ``_read_row(keys=...)``.
    """

    __slots__ = ("_parent", "_keys", "_single", "_index")

    def __init__(
        self,
        parent: AsyncViewParent[Any],
        keys: list[str],
        single: bool,
        index: int,
    ):
        self._parent = parent
        self._keys = keys
        self._single = single
        self._index = index

    def __await__(self):
        return self._materialize().__await__()

    async def _materialize(self):
        idx = self._index
        try:
            n = len(self._parent)
        except TypeError:
            n = await self._parent.len()
        if idx < 0:
            idx += n
        if idx < 0 or idx >= n:
            raise IndexError(self._index)
        if self._single:
            values = await self._parent._read_column(self._keys[0], [idx])
            return values[0]
        row = await self._parent._read_row(idx, keys=self._keys)
        return [row.get(k) for k in self._keys]


# ── AsyncColumnView ─────────────────────────────────────────────────────


class AsyncColumnView:
    """Lazy view over one or more columns.

    Use ``.to_list()`` to materialize values, or ``.to_dict()`` for a
    column-oriented dict.
    """

    __slots__ = ("_parent", "_keys", "_single", "_indices")

    def __init__(
        self,
        parent: AsyncViewParent[Any],
        keys: str | bytes | list[str] | list[bytes],
        indices: list[int] | None = None,
    ):
        self._parent = parent
        self._single = isinstance(keys, (str, bytes))
        self._keys = [keys] if self._single else keys
        self._indices = indices

    def _resolved_indices(self) -> list[int]:
        if self._indices is not None:
            return self._indices
        try:
            return list(range(len(self._parent)))
        except TypeError:
            raise TypeError(
                "Cannot resolve indices synchronously on async column views. "
                "Use _aresolved_indices() instead."
            )

    async def _aresolved_indices(self) -> list[int]:
        """Async variant of _resolved_indices for parents without sync __len__."""
        if self._indices is not None:
            return self._indices
        try:
            n = len(self._parent)
        except TypeError:
            n = await self._parent.len()
        return list(range(n))

    def __len__(self) -> int:
        if self._indices is not None:
            return len(self._indices)
        try:
            return len(self._parent)
        except TypeError:
            raise TypeError(
                "len() not available on async column views without explicit "
                "indices. Use 'await col.to_list()' to materialize first."
            )

    def __bool__(self) -> bool:
        return len(self) > 0

    async def to_list(self) -> list[Any]:
        indices = await self._aresolved_indices()
        if self._single:
            return await self._parent._read_column(self._keys[0], indices)
        rows = await self._parent._read_rows(indices, keys=self._keys)
        return [
            None if row is None else [row.get(k) for k in self._keys] for row in rows
        ]

    async def to_dict(self) -> dict[str, list[Any]]:
        indices = await self._aresolved_indices()
        if self._single:
            return {
                self._keys[0]: await self._parent._read_column(self._keys[0], indices)
            }
        rows = await self._parent._read_rows(indices, keys=self._keys)
        result: dict[str, list[Any]] = {k: [] for k in self._keys}
        for row in rows:
            for k in self._keys:
                result[k].append(row[k] if row is not None else None)
        return result

    async def __aiter__(self) -> AsyncIterator[Any]:
        indices = await self._aresolved_indices()
        if self._single:
            values = await self._parent._read_column(self._keys[0], indices)
            for v in values:
                yield v
        else:
            rows = await self._parent._read_rows(indices, keys=self._keys)
            for row in rows:
                yield None if row is None else [row.get(k) for k in self._keys]

    @overload
    def __getitem__(self, key: int) -> AsyncSingleColumnView: ...
    @overload
    def __getitem__(self, key: slice) -> AsyncColumnView: ...
    @overload
    def __getitem__(self, key: list[int]) -> AsyncColumnView: ...
    @overload
    def __getitem__(self, key: str) -> AsyncColumnView: ...

    def __getitem__(
        self, key: int | slice | str | list[int]
    ) -> AsyncSingleColumnView | AsyncColumnView:
        if self._indices is not None:
            indices = self._indices
        else:
            # _indices is None means "all rows". For int/list[int], we can
            # use the key directly as absolute index. For slice, we need
            # to defer or compute.
            if isinstance(key, int):
                return AsyncSingleColumnView(
                    self._parent,
                    self._keys,
                    self._single,
                    key,
                )
            if isinstance(key, slice):
                # Defer: create a column view with a deferred slice
                return _DeferredSliceColumnView(
                    self._parent,
                    self._keys[0] if self._single else self._keys,
                    key,
                )
            if isinstance(key, (str, bytes)):
                return AsyncColumnView(self._parent, key)
            if isinstance(key, list):
                return AsyncColumnView(
                    self._parent,
                    self._keys[0] if self._single else self._keys,
                    key,
                )
            raise TypeError(f"Unsupported key type: {type(key)}")

        if isinstance(key, int):
            abs_idx = _sub_select(indices, key)
            return AsyncSingleColumnView(
                self._parent,
                self._keys,
                self._single,
                abs_idx,
            )
        if isinstance(key, slice):
            new_indices = _sub_select(indices, key)
            return AsyncColumnView(
                self._parent,
                self._keys[0] if self._single else self._keys,
                new_indices,
            )
        if isinstance(key, (str, bytes)):
            return AsyncColumnView(self._parent, key, indices)
        if isinstance(key, list):
            new_indices = _sub_select(indices, key)
            return AsyncColumnView(
                self._parent,
                self._keys[0] if self._single else self._keys,
                new_indices,
            )
        raise TypeError(f"Unsupported key type: {type(key)}")

    async def set(self, data: list) -> None:
        """Write positional data back to the underlying rows.

        Single-key: flat list → update each row with {key: value}.
        Multi-key: list-of-lists → validate inner length, update each row.
        """
        if not isinstance(data, list):
            raise TypeError(
                f"Column-filtered writes must be lists. Got {type(data).__name__}."
            )
        indices = await self._aresolved_indices()
        if len(data) != len(indices):
            raise ValueError(
                f"Length mismatch: got {len(data)} values for {len(indices)} rows."
            )
        if self._single:
            if _is_contiguous(indices):
                await self._parent._set_column(self._keys[0], indices[0], data)
            else:
                for idx, value in zip(indices, data):
                    await self._parent._update_row(idx, {self._keys[0]: value})
        else:
            n_keys = len(self._keys)
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
                await self._parent._update_many(indices[0], dicts)
            else:
                for idx, row_values in zip(indices, data):
                    await self._parent._update_row(
                        idx, dict(zip(self._keys, row_values))
                    )

    def __repr__(self) -> str:
        if self._indices is not None:
            length = len(self._indices)
        else:
            length = "?"
        if self._single:
            return f"AsyncColumnView(key={self._keys[0]!r}, len={length})"
        return f"AsyncColumnView(keys={self._keys!r}, len={length})"


# ── _DeferredSliceColumnView ──────────────────────────────────────────


class _DeferredSliceColumnView(AsyncColumnView):
    """AsyncColumnView that resolves a slice lazily via len().

    Created when AsyncColumnView with _indices=None is sliced, and the
    parent doesn't support sync __len__.
    """

    def __init__(
        self,
        parent: AsyncViewParent[Any],
        keys: str | list[str],
        slc: slice,
    ):
        super().__init__(parent, keys, None)
        self._slice = slc
        self._resolved = False

    async def _ensure_resolved(self) -> None:
        if not self._resolved:
            try:
                n = len(self._parent)
            except TypeError:
                n = await self._parent.len()
            self._indices = list(range(n))[self._slice]
            self._resolved = True

    async def _aresolved_indices(self) -> list[int]:
        await self._ensure_resolved()
        return self._indices

    async def __aiter__(self):
        await self._ensure_resolved()
        async for item in AsyncColumnView.__aiter__(self):
            yield item


# ── AsyncASEColumnView ───────────────────────────────────────────────────


class AsyncASEColumnView(AsyncColumnView):
    """AsyncColumnView that wraps every materialized row through dict_to_atoms().

    ASEIO always returns Atoms — str vs list[str] controls which keys load.
    """

    async def to_list(self) -> list[ase.Atoms]:
        from ._convert import dict_to_atoms

        indices = await self._aresolved_indices()
        rows = await self._parent._read_rows(indices, keys=self._keys)
        result = []
        for row in rows:
            if row is None:
                raise TypeError("Cannot build ase.Atoms from a placeholder row.")
            result.append(dict_to_atoms(row))
        return result

    async def __aiter__(self) -> AsyncIterator[ase.Atoms]:
        from ._convert import dict_to_atoms

        indices = await self._aresolved_indices()
        rows = await self._parent._read_rows(indices, keys=self._keys)
        for row in rows:
            if row is None:
                raise TypeError("Cannot build ase.Atoms from a placeholder row.")
            yield dict_to_atoms(row)

    def __getitem__(
        self, key: int | slice | str | list[int]
    ) -> AsyncSingleRowView[Any] | AsyncASEColumnView:
        if self._indices is not None:
            indices = self._indices
        else:
            if isinstance(key, int):
                return AsyncSingleRowView(self._parent, key)
            if isinstance(key, slice):
                return _DeferredSliceASEColumnView(
                    self._parent,
                    self._keys[0] if self._single else self._keys,
                    key,
                )
            if isinstance(key, str):
                return AsyncASEColumnView(self._parent, key)
            if isinstance(key, list):
                return AsyncASEColumnView(
                    self._parent,
                    self._keys[0] if self._single else self._keys,
                    key,
                )
            raise TypeError(f"Unsupported key type: {type(key)}")

        if isinstance(key, int):
            abs_idx = _sub_select(indices, key)
            return AsyncSingleRowView(self._parent, abs_idx)
        if isinstance(key, slice):
            new_indices = _sub_select(indices, key)
            return AsyncASEColumnView(
                self._parent,
                self._keys[0] if self._single else self._keys,
                new_indices,
            )
        if isinstance(key, str):
            return AsyncASEColumnView(self._parent, key, indices)
        if isinstance(key, list):
            new_indices = _sub_select(indices, key)
            return AsyncASEColumnView(
                self._parent,
                self._keys[0] if self._single else self._keys,
                new_indices,
            )
        raise TypeError(f"Unsupported key type: {type(key)}")

    async def to_dict(self) -> None:
        raise TypeError(
            "to_dict() is not available on ASEIO column views. "
            "ASEIO always returns ase.Atoms — use to_list() instead."
        )

    def __repr__(self) -> str:
        if self._indices is not None:
            length = len(self._indices)
        else:
            length = "?"
        if self._single:
            return f"AsyncASEColumnView(key={self._keys[0]!r}, len={length})"
        return f"AsyncASEColumnView(keys={self._keys!r}, len={length})"


class _DeferredSliceASEColumnView(AsyncASEColumnView):
    """AsyncASEColumnView that resolves a slice lazily via len()."""

    def __init__(
        self,
        parent: AsyncViewParent[Any],
        keys: str | list[str],
        slc: slice,
    ):
        super().__init__(parent, keys, None)
        self._slice = slc
        self._resolved = False

    async def _ensure_resolved(self) -> None:
        if not self._resolved:
            try:
                n = len(self._parent)
            except TypeError:
                n = await self._parent.len()
            self._indices = list(range(n))[self._slice]
            self._resolved = True

    async def _aresolved_indices(self) -> list[int]:
        await self._ensure_resolved()
        return self._indices

    async def __aiter__(self):
        await self._ensure_resolved()
        async for item in AsyncASEColumnView.__aiter__(self):
            yield item


# ── _DeferredSliceRowView ─────────────────────────────────────────────


class _DeferredSliceRowView(AsyncRowView[R]):
    """AsyncRowView that resolves a slice lazily via len().

    When __getitem__ receives a slice, we can't call len() synchronously
    on an async object. This subclass stores the raw slice and resolves
    it to concrete indices on first await / aiter.
    """

    def __init__(self, parent, slc: slice, *, column_view_cls=None):
        super().__init__(parent, [], contiguous=True, column_view_cls=column_view_cls)
        self._slice = slc
        self._resolved = False

    async def _ensure_resolved(self) -> None:
        if not self._resolved:
            n = await self._parent.len()
            self._indices = list(range(n))[self._slice]
            self._resolved = True

    def __getitem__(self, key):
        cv_cls = self._column_view_cls or AsyncColumnView
        if isinstance(key, (str, bytes)):
            if cv_cls is AsyncASEColumnView:
                return _DeferredSliceASEColumnView(self._parent, key, self._slice)
            if cv_cls is AsyncColumnView:
                return _DeferredSliceColumnView(self._parent, key, self._slice)
        if isinstance(key, list) and key and isinstance(key[0], (str, bytes)):
            if cv_cls is AsyncASEColumnView:
                return _DeferredSliceASEColumnView(self._parent, key, self._slice)
            if cv_cls is AsyncColumnView:
                return _DeferredSliceColumnView(self._parent, key, self._slice)
        return super().__getitem__(key)

    def __len__(self) -> int:
        if not self._resolved:
            raise TypeError(
                "len() not available until slice is resolved. "
                "Use 'to_list()' or 'async for' first."
            )
        return len(self._indices)

    async def to_list(self) -> list[Any]:
        await self._ensure_resolved()
        return await super().to_list()

    async def __aiter__(self):
        await self._ensure_resolved()
        async for item in super().__aiter__():
            yield item

    async def chunked(self, chunk_size: int = 1000):
        await self._ensure_resolved()
        async for item in super().chunked(chunk_size):
            yield item

    async def delete(self) -> None:
        await self._ensure_resolved()
        await super().delete()

    async def set(self, data: list[Any]) -> None:
        await self._ensure_resolved()
        await super().set(data)

    async def update(self, data: dict) -> None:
        await self._ensure_resolved()
        await super().update(data)

    async def drop(self, keys: list) -> None:
        await self._ensure_resolved()
        await super().drop(keys)
