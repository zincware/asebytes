"""AsyncASEIO — async facade for str-level backends.

Mirrors ASEIO but all I/O is async. __getitem__ is sync and returns
awaitable views; materialization happens on ``await`` or ``async for``.
"""

from __future__ import annotations

from typing import Any, overload

import ase
import numpy as np

from ._async_backends import AsyncReadBackend, AsyncReadWriteBackend
from ._async_views import (
    AsyncASEColumnView,
    AsyncColumnView,
    AsyncRowView,
    AsyncSingleRowView,
    _DeferredSliceRowView,
)


class AsyncASEIO:
    """Async storage-agnostic interface for dict[str, Any] rows.

    Wraps an AsyncReadBackend or AsyncReadWriteBackend. If *backend* is a
    string path, auto-creates a sync backend via the registry and wraps
    it with SyncToAsyncAdapter.

    ``__getitem__`` is synchronous and returns awaitable views.
    ``await db[0]`` materializes a single row, ``await db[0:10]`` materializes
    a list.
    """

    def __init__(
        self,
        backend: str | AsyncReadBackend[str, Any],
        *,
        readonly: bool | None = None,
        **kwargs: Any,
    ):
        if isinstance(backend, str):
            from ._registry import get_async_backend_cls, parse_uri
            from ._async_backends import sync_to_async, AsyncReadBackend as _AsyncRB

            scheme, _remainder = parse_uri(backend)
            cls = get_async_backend_cls(backend, readonly=readonly)
            if scheme is not None and hasattr(cls, "from_uri"):
                inst = cls.from_uri(backend, **kwargs)
            else:
                inst = cls(backend, **kwargs)
            if isinstance(inst, _AsyncRB):
                self._backend: AsyncReadBackend[str, Any] = inst
            else:
                self._backend = sync_to_async(inst)
        else:
            self._backend = backend

    # -- AsyncViewParent implementation ------------------------------------

    def __len__(self) -> int:
        raise TypeError(
            "len() is not available on async objects. Use 'await db.len()' instead."
        )

    async def len(self) -> int:
        return await self._backend.len()

    async def keys(self, index: int) -> list[str]:
        """Return keys present at *index*."""
        return await self._backend.keys(index)

    async def _read_row(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any] | None:
        return await self._backend.get(index, keys)

    async def _read_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any] | None]:
        return await self._backend.get_many(indices, keys)

    async def _read_column(self, key: str, indices: list[int]) -> list[Any]:
        return await self._backend.get_column(key, indices)

    async def _write_row(self, index: int, data: Any) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.set(index, data)

    async def _delete_row(self, index: int) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.delete(index)

    async def _delete_rows(self, start: int, stop: int) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.delete_many(start, stop)

    async def _update_row(self, index: int, data: Any) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.update(index, data)

    async def _update_many(self, start: int, data: list) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.update_many(start, data)

    async def _set_column(self, key, start: int, values: list) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.set_column(key, start, values)

    async def _write_many(self, start: int, data: list) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.set_many(start, data)

    async def _drop_keys(self, keys: list[str], indices: list[int]) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.drop_keys(keys, indices)

    async def _keys(self, index: int) -> list[str]:
        return await self._backend.keys(index)

    def _build_result(self, row: Any) -> ase.Atoms | None:
        """Convert dict to ase.Atoms via dict_to_atoms."""
        if row is None:
            return None
        from ._convert import dict_to_atoms

        return dict_to_atoms(row)

    # ── __getitem__ → sync, returns views ─────────────────────────────

    @overload
    def __getitem__(self, index: int) -> AsyncSingleRowView[ase.Atoms | None]: ...
    @overload
    def __getitem__(self, index: slice) -> AsyncRowView[ase.Atoms | None]: ...
    @overload
    def __getitem__(self, index: list[int]) -> AsyncRowView[ase.Atoms | None]: ...
    @overload
    def __getitem__(self, index: str) -> AsyncASEColumnView: ...
    @overload
    def __getitem__(self, index: list[str]) -> AsyncASEColumnView: ...

    def __getitem__(
        self,
        index: int | slice | str | list[int] | list[str],
    ) -> (
        AsyncSingleRowView[ase.Atoms | None]
        | AsyncRowView[ase.Atoms | None]
        | AsyncColumnView
    ):
        if isinstance(index, int):
            # For negative indices we need len, but len is async.
            # Store the raw index; _read_row will handle IndexError at
            # the backend level.
            return AsyncSingleRowView(self, index)
        if isinstance(index, slice):
            return _ASEIODeferredSliceRowView(
                self, index, column_view_cls=AsyncASEColumnView
            )
        if isinstance(index, str):
            return AsyncASEColumnView(self, index)
        if isinstance(index, list):
            if not index:
                return AsyncRowView(self, [])
            if isinstance(index[0], int):
                return AsyncRowView(
                    self, index, contiguous=False, column_view_cls=AsyncASEColumnView
                )
            if isinstance(index[0], str):
                return AsyncASEColumnView(self, index)
        raise TypeError(f"Unsupported index type: {type(index)}")

    # ── Top-level async write methods ─────────────────────────────────

    async def extend(self, data: list[ase.Atoms]) -> int:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        from ._convert import atoms_to_dict

        data_list = [atoms_to_dict(atoms) for atoms in data]
        return await self._backend.extend(data_list)

    async def insert(self, index: int, value: ase.Atoms | None) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        if value is None:
            await self._backend.insert(index, None)
        else:
            from ._convert import atoms_to_dict

            await self._backend.insert(index, atoms_to_dict(value))

    async def get(self, index: int, keys: list[str] | None = None) -> ase.Atoms | None:
        """Read a single row, optionally filtering to specific keys.

        Returns an ase.Atoms object (applies dict_to_atoms conversion).
        """
        row = await self._backend.get(index, keys)
        return self._build_result(row)

    async def drop(self, *, keys: list[str]) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.drop_keys(keys)

    async def clear(self) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.clear()

    async def remove(self) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.remove()

    async def reserve(self, count: int) -> None:
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        await self._backend.reserve(count)

    _VALID_PREFIXES = ("arrays.", "info.", "calc.")
    _VALID_TOP_LEVEL = ("cell", "pbc", "constraints")

    def _validate_keys(self, data: dict[str, Any]) -> None:
        for key in data:
            if key in self._VALID_TOP_LEVEL:
                continue
            if any(key.startswith(p) for p in self._VALID_PREFIXES):
                continue
            raise ValueError(
                f"Invalid key {key!r}. Keys must start with "
                f"{', '.join(self._VALID_PREFIXES)} or be one of "
                f"{', '.join(self._VALID_TOP_LEVEL)}."
            )

    async def update(
        self,
        index: int,
        data: dict[str, Any] | None = None,
        *,
        info: dict[str, Any] | None = None,
        arrays: dict[str, np.ndarray] | None = None,
        calc: dict[str, Any] | None = None,
    ) -> None:
        """Partial update: merge *data* into existing row at *index*.

        Flat-dict API::

            await db.update(i, {"calc.energy": -10.5, "info.tag": "done"})

        Keyword API::

            await db.update(i, info={"tag": "done"}, calc={"energy": -10.5})
        """
        if not isinstance(self._backend, AsyncReadWriteBackend):
            raise TypeError("Backend is read-only")
        flat_data: dict[str, Any] = {}
        if data is not None:
            flat_data.update(data)
        if info:
            for k, v in info.items():
                flat_data[f"info.{k}"] = v
        if arrays:
            for k, v in arrays.items():
                flat_data[f"arrays.{k}"] = v
        if calc:
            for k, v in calc.items():
                flat_data[f"calc.{k}"] = v
        if not flat_data:
            return
        self._validate_keys(flat_data)
        await self._backend.update(index, flat_data)

    # -- Async iteration ---------------------------------------------------

    async def __aiter__(self):
        n = await self._backend.len()
        for i in range(n):
            row = await self._backend.get(i)
            yield self._build_result(row)

    # ── Context manager ───────────────────────────────────────────────

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Try aclose() first (async close), then close() (sync close)
        if hasattr(self._backend, "aclose"):
            await self._backend.aclose()
        elif hasattr(self._backend, "close"):
            self._backend.close()
        return False

    def __repr__(self) -> str:
        return f"AsyncASEIO(backend={self._backend!r})"


class _DeferredColumnFromSlice:
    """Deferred column view created from an unresolved slice row view.

    Resolves the parent slice on to_list/aiter, then delegates to the
    appropriate column view class.
    """

    def __init__(self, parent_row_view: _DeferredSliceRowView, keys: str | list[str]):
        self._parent_row_view = parent_row_view
        self._keys = keys

    async def to_list(self):
        await self._parent_row_view._ensure_resolved()
        cls = self._parent_row_view._column_view_cls
        view = cls(
            self._parent_row_view._parent,
            self._keys,
            self._parent_row_view._indices,
        )
        return await view.to_list()

    async def __aiter__(self):
        await self._parent_row_view._ensure_resolved()
        cls = self._parent_row_view._column_view_cls
        view = cls(
            self._parent_row_view._parent,
            self._keys,
            self._parent_row_view._indices,
        )
        async for item in view:
            yield item

    async def to_dict(self):
        await self._parent_row_view._ensure_resolved()
        cls = self._parent_row_view._column_view_cls
        view = cls(
            self._parent_row_view._parent,
            self._keys,
            self._parent_row_view._indices,
        )
        return await view.to_dict()

    def __getitem__(self, key):
        # Support chaining: db[0:3]["calc.energy"][0:2]
        return _DeferredSubColumnFromSlice(self, key)


class _DeferredSubColumnFromSlice:
    """Sub-selection on a deferred column, resolves parent first."""

    def __init__(self, parent: _DeferredColumnFromSlice, key):
        self._parent = parent
        self._key = key

    async def to_list(self):
        await self._parent._parent_row_view._ensure_resolved()
        cls = self._parent._parent_row_view._column_view_cls
        view = cls(
            self._parent._parent_row_view._parent,
            self._parent._keys,
            self._parent._parent_row_view._indices,
        )
        sub = view[self._key]
        if hasattr(sub, "to_list"):
            return await sub.to_list()
        return sub

    async def __aiter__(self):
        await self._parent._parent_row_view._ensure_resolved()
        cls = self._parent._parent_row_view._column_view_cls
        view = cls(
            self._parent._parent_row_view._parent,
            self._parent._keys,
            self._parent._parent_row_view._indices,
        )
        sub = view[self._key]
        if hasattr(sub, "__aiter__"):
            async for item in sub:
                yield item


class _ASEIODeferredSliceRowView(_DeferredSliceRowView[ase.Atoms | None]):
    """ASEIO variant that defers column access to _DeferredColumnFromSlice."""

    def __getitem__(self, key):
        if isinstance(key, str):
            return _DeferredColumnFromSlice(self, key)
        if isinstance(key, list) and key and isinstance(key[0], str):
            return _DeferredColumnFromSlice(self, key)
        if self._resolved:
            return super().__getitem__(key)
        raise TypeError(
            "Cannot sub-select by int/slice from unresolved slice. "
            "Use 'to_list()' or 'async for' first, or index by column key."
        )
