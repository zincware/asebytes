"""Async awaitable views for AsyncASEIO / AsyncBytesIO.

__getitem__ on the parent is sync and returns one of these views.
Materialization happens only when you ``await`` the view or iterate with
``async for``.

__await__ semantics:
- AsyncSingleRowView → single row (dict or Atoms or None)
- AsyncRowView       → list of rows
- AsyncColumnView    → list of values (single key) or list of dicts (multi key)
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Protocol, overload


class AsyncViewParent(Protocol):
    """Protocol for objects that serve as parent of async views."""

    def __len__(self) -> int: ...
    async def alen(self) -> int: ...
    async def _read_row(self, index: int, keys: list[str] | None = None) -> Any: ...
    async def _read_rows(self, indices: list[int], keys: list[str] | None = None) -> list[Any]: ...
    async def _read_column(self, key: str, indices: list[int]) -> list[Any]: ...
    async def _write_row(self, index: int, data: Any) -> None: ...
    async def _delete_row(self, index: int) -> None: ...
    async def _delete_rows(self, start: int, stop: int) -> None: ...
    async def _update_row(self, index: int, data: Any) -> None: ...
    async def _drop_keys(self, keys: list[str], indices: list[int]) -> None: ...
    async def _get_available_keys(self, index: int) -> list[str]: ...
    def _build_result(self, row: Any) -> Any: ...


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


def _is_contiguous(indices: list[int]) -> bool:
    """Check if indices form a contiguous ascending range."""
    if len(indices) <= 1:
        return True
    for i in range(1, len(indices)):
        if indices[i] != indices[i - 1] + 1:
            return False
    return True


# ── AsyncSingleRowView ──────────────────────────────────────────────────


class AsyncSingleRowView:
    """Awaitable view over a single row.

    ``await view`` returns the row data (or None for placeholders).
    """

    __slots__ = ("_parent", "_index")

    def __init__(self, parent: AsyncViewParent, index: int):
        self._parent = parent
        self._index = index

    def __await__(self):
        return self._materialize().__await__()

    async def _resolve_index(self) -> int:
        """Resolve negative indices via alen()."""
        idx = self._index
        if idx < 0:
            try:
                n = len(self._parent)
            except TypeError:
                n = await self._parent.alen()
            idx += n
        return idx

    async def _materialize(self):
        idx = await self._resolve_index()
        row = await self._parent._read_row(idx)
        return self._parent._build_result(row)

    async def aset(self, data: Any) -> None:
        idx = await self._resolve_index()
        await self._parent._write_row(idx, data)

    async def adelete(self) -> None:
        idx = await self._resolve_index()
        await self._parent._delete_row(idx)

    async def aupdate(self, data: dict) -> None:
        idx = await self._resolve_index()
        await self._parent._update_row(idx, data)

    async def akeys(self) -> list[str]:
        idx = await self._resolve_index()
        return await self._parent._get_available_keys(idx)

    def __repr__(self) -> str:
        return f"AsyncSingleRowView(index={self._index})"


# ── AsyncRowView ────────────────────────────────────────────────────────


class AsyncRowView:
    """Awaitable view over multiple rows.

    ``await view`` returns ``list[row]``.
    ``async for row in view`` streams rows one at a time.
    """

    __slots__ = ("_parent", "_indices", "_contiguous")

    def __init__(
        self,
        parent: AsyncViewParent,
        indices: list[int],
        *,
        contiguous: bool | None = None,
    ):
        self._parent = parent
        self._indices = indices
        self._contiguous = contiguous if contiguous is not None else _is_contiguous(indices)

    def __len__(self) -> int:
        return len(self._indices)

    def __bool__(self) -> bool:
        return len(self._indices) > 0

    def __await__(self):
        return self._materialize().__await__()

    async def _materialize(self) -> list[Any]:
        rows = await self._parent._read_rows(self._indices)
        return [self._parent._build_result(r) for r in rows]

    async def __aiter__(self) -> AsyncIterator[Any]:
        for i in self._indices:
            row = await self._parent._read_row(i)
            yield self._parent._build_result(row)

    async def achunked(self, chunk_size: int = 1000) -> AsyncIterator[Any]:
        """Iterate in chunks for throughput. Yields individual items."""
        for start in range(0, len(self._indices), chunk_size):
            chunk = self._indices[start : start + chunk_size]
            rows = await self._parent._read_rows(chunk)
            for row in rows:
                yield self._parent._build_result(row)

    @overload
    def __getitem__(self, key: int) -> AsyncSingleRowView: ...
    @overload
    def __getitem__(self, key: slice) -> AsyncRowView: ...
    @overload
    def __getitem__(self, key: list[int]) -> AsyncRowView: ...
    @overload
    def __getitem__(self, key: str) -> AsyncColumnView: ...
    @overload
    def __getitem__(self, key: list[str]) -> AsyncColumnView: ...

    def __getitem__(
        self, key: int | slice | str | list[int] | list[str]
    ) -> AsyncSingleRowView | AsyncRowView | AsyncColumnView:
        if isinstance(key, int):
            abs_idx = _sub_select(self._indices, key)
            return AsyncSingleRowView(self._parent, abs_idx)
        if isinstance(key, slice):
            new_indices = _sub_select(self._indices, key)
            return AsyncRowView(self._parent, new_indices)
        if isinstance(key, str):
            return AsyncColumnView(self._parent, key, self._indices)
        if isinstance(key, list):
            if not key:
                return AsyncRowView(self._parent, [])
            if isinstance(key[0], int):
                new_indices = _sub_select(self._indices, key)
                return AsyncRowView(self._parent, new_indices, contiguous=False)
            if isinstance(key[0], str):
                return AsyncColumnView(self._parent, key, self._indices)
        raise TypeError(f"Unsupported key type: {type(key)}")

    async def aset(self, data: list[Any]) -> None:
        for idx, d in zip(self._indices, data):
            await self._parent._write_row(idx, d)

    async def adelete(self) -> None:
        if not self._contiguous:
            raise TypeError(
                "adelete() requires contiguous indices. "
                "Non-contiguous delete is ambiguous due to index shifting. "
                "Use aset([None, ...]) to empty slots without shifting."
            )
        if not self._indices:
            return
        await self._parent._delete_rows(self._indices[0], self._indices[-1] + 1)

    async def aupdate(self, data: dict) -> None:
        for idx in self._indices:
            await self._parent._update_row(idx, data)

    async def adrop(self, keys: list[str]) -> None:
        await self._parent._drop_keys(keys, self._indices)

    def __repr__(self) -> str:
        return f"AsyncRowView(len={len(self)})"


# ── AsyncColumnView ─────────────────────────────────────────────────────


class AsyncColumnView:
    """Awaitable view over one or more columns.

    Single key: ``await view`` returns ``list[value]``.
    Multi key: ``await view`` returns ``list[dict[str, Any]]``.
    """

    __slots__ = ("_parent", "_keys", "_single", "_indices")

    def __init__(
        self,
        parent: AsyncViewParent,
        keys: str | list[str],
        indices: list[int] | None = None,
    ):
        self._parent = parent
        self._single = isinstance(keys, str)
        self._keys = [keys] if self._single else keys
        self._indices = indices

    def _resolved_indices(self) -> list[int]:
        if self._indices is not None:
            return self._indices
        return list(range(len(self._parent)))

    async def _aresolved_indices(self) -> list[int]:
        """Async variant of _resolved_indices for parents without sync __len__."""
        if self._indices is not None:
            return self._indices
        try:
            n = len(self._parent)
        except TypeError:
            n = await self._parent.alen()
        return list(range(n))

    def __len__(self) -> int:
        if self._indices is not None:
            return len(self._indices)
        return len(self._parent)

    def __bool__(self) -> bool:
        return len(self) > 0

    def __await__(self):
        return self._materialize().__await__()

    async def _materialize(self) -> list[Any]:
        return await self.to_list()

    async def to_list(self) -> list[Any]:
        indices = await self._aresolved_indices()
        if self._single:
            return await self._parent._read_column(self._keys[0], indices)
        rows = await self._parent._read_rows(indices, keys=self._keys)
        return rows

    async def to_dict(self) -> dict[str, list[Any]]:
        indices = await self._aresolved_indices()
        if self._single:
            return {self._keys[0]: await self._parent._read_column(self._keys[0], indices)}
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
                yield row

    @overload
    def __getitem__(self, key: int) -> AsyncSingleRowView: ...
    @overload
    def __getitem__(self, key: slice) -> AsyncColumnView: ...
    @overload
    def __getitem__(self, key: list[int]) -> AsyncColumnView: ...
    @overload
    def __getitem__(self, key: str) -> AsyncColumnView: ...

    def __getitem__(
        self, key: int | slice | str | list[int]
    ) -> AsyncSingleRowView | AsyncColumnView:
        if self._indices is not None:
            indices = self._indices
        else:
            # _indices is None means "all rows". For int/list[int], we can
            # use the key directly as absolute index. For slice, we need
            # to defer or compute.
            if isinstance(key, int):
                return AsyncSingleRowView(self._parent, key)
            if isinstance(key, slice):
                # Defer: create a column view with a deferred slice
                return _DeferredSliceColumnView(
                    self._parent,
                    self._keys[0] if self._single else self._keys,
                    key,
                )
            if isinstance(key, str):
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
            if self._single:
                return AsyncSingleRowView(self._parent, abs_idx)
            return AsyncSingleRowView(self._parent, abs_idx)
        if isinstance(key, slice):
            new_indices = _sub_select(indices, key)
            return AsyncColumnView(
                self._parent,
                self._keys[0] if self._single else self._keys,
                new_indices,
            )
        if isinstance(key, str):
            return AsyncColumnView(self._parent, key, indices)
        if isinstance(key, list):
            new_indices = _sub_select(indices, key)
            return AsyncColumnView(
                self._parent,
                self._keys[0] if self._single else self._keys,
                new_indices,
            )
        raise TypeError(f"Unsupported key type: {type(key)}")

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
    """AsyncColumnView that resolves a slice lazily via alen().

    Created when AsyncColumnView with _indices=None is sliced, and the
    parent doesn't support sync __len__.
    """

    def __init__(
        self,
        parent: AsyncViewParent,
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
                n = await self._parent.alen()
            self._indices = list(range(n))[self._slice]
            self._resolved = True

    async def _aresolved_indices(self) -> list[int]:
        await self._ensure_resolved()
        return self._indices

    def __await__(self):
        return self._deferred_materialize().__await__()

    async def _deferred_materialize(self) -> list[Any]:
        await self._ensure_resolved()
        return await super().to_list()

    async def __aiter__(self):
        await self._ensure_resolved()
        async for item in AsyncColumnView.__aiter__(self):
            yield item
