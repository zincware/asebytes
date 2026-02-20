from __future__ import annotations

import warnings
from collections.abc import Iterator, MutableSequence
from typing import Any, overload

import ase
import numpy as np

from ._convert import atoms_to_dict, dict_to_atoms
from ._protocols import ReadableBackend, WritableBackend
from ._views import ColumnView, RowView


class ASEIO(MutableSequence):
    """Storage-agnostic mutable sequence for ASE Atoms objects.

    Supports pluggable backends (LMDB, HuggingFace, Zarr) and pandas-style
    lazy views for column-oriented data access.

    Parameters
    ----------
    backend : str | ReadableBackend | WritableBackend
        Either a file path (auto-creates LMDBBackend) or a backend instance.
    readonly : bool | None
        Force read-only or writable mode. None (default) auto-detects.
    cache_to : str | WritableBackend | None
        Optional persistent read-through cache. On read, the cache is
        checked first; on miss the full row is read from source and written
        to cache. String paths auto-create a writable backend via the
        registry (e.g. ``"cache.lmdb"``). Designed for immutable sources
        (e.g. HuggingFace datasets). Delete the cache file to reset.
    **kwargs
        When backend is a str, forwarded to the backend constructor.
    """

    def __init__(
        self,
        backend: str | ReadableBackend,
        *,
        readonly: bool | None = None,
        cache_to: str | WritableBackend | None = None,
        **kwargs: Any,
    ):
        if isinstance(backend, str):
            from ._registry import get_backend_cls, parse_uri

            scheme, _remainder = parse_uri(backend)
            cls = get_backend_cls(backend, readonly=readonly)
            if scheme is not None:
                # URI-style: delegate to from_uri constructor
                self._backend: ReadableBackend = cls.from_uri(backend, **kwargs)
            else:
                # File path: pass path directly to backend constructor
                self._backend = cls(backend, **kwargs)
        else:
            self._backend = backend

        # Persistent read-through cache
        if cache_to is None:
            self._cache: WritableBackend | None = None
        elif isinstance(cache_to, str):
            from ._registry import get_backend_cls

            cache_cls = get_backend_cls(cache_to, readonly=False)
            self._cache = cache_cls(cache_to)
        elif isinstance(cache_to, WritableBackend):
            self._cache = cache_to
        else:
            raise TypeError(
                f"cache_to must be str or WritableBackend, "
                f"got {type(cache_to).__name__}"
            )

        if (
            self._cache is not None
            and readonly is not True
            and isinstance(self._backend, WritableBackend)
        ):
            warnings.warn(
                "cache_to with a writable source may serve stale data after "
                "mutations. cache_to is designed for immutable sources.",
                stacklevel=2,
            )

    @property
    def columns(self) -> list[str]:
        """Available column names (inspects first row)."""
        try:
            n = len(self._backend)
        except TypeError:
            # Unknown-length backend — try reading frame 0 directly
            pass
        else:
            if n == 0:
                return []
        return self._backend.columns()

    # --- Internal methods used by views ---

    def _read_row(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any]:
        if self._cache is not None:
            try:
                return self._cache.read_row(index, keys)
            except (IndexError, KeyError):
                pass
            # Cache miss — read full row from source, write to cache
            full_row = self._backend.read_row(index)
            try:
                self._cache.write_row(index, full_row)
            except Exception:
                pass  # cache write is best-effort
            if keys is not None:
                return {k: full_row[k] for k in keys if k in full_row}
            return full_row
        return self._backend.read_row(index, keys)

    def _read_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any]]:
        if self._cache is not None:
            return [self._read_row(i, keys) for i in indices]
        return self._backend.read_rows(indices, keys)

    def _iter_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> Iterator[dict[str, Any]]:
        if self._cache is not None:
            return (self._read_row(i, keys) for i in indices)
        return self._backend.iter_rows(indices, keys)

    def _read_column(self, key: str, indices: list[int]) -> list[Any]:
        if self._cache is not None:
            return [self._read_row(i, [key])[key] for i in indices]
        return self._backend.read_column(key, indices)

    def _build_atoms(self, row: dict[str, Any]) -> ase.Atoms:
        return dict_to_atoms(row)

    # --- MutableSequence interface ---

    @overload
    def __getitem__(self, index: int) -> ase.Atoms: ...
    @overload
    def __getitem__(self, index: slice) -> RowView: ...
    @overload
    def __getitem__(self, index: list[int]) -> RowView: ...
    @overload
    def __getitem__(self, index: str) -> ColumnView: ...
    @overload
    def __getitem__(self, index: list[str]) -> ColumnView: ...

    def __getitem__(
        self,
        index: int | slice | str | list[int] | list[str],
    ) -> ase.Atoms | RowView | ColumnView:
        if isinstance(index, int):
            if index < 0:
                index += len(self)  # raises TypeError if unknown
            if index < 0:
                raise IndexError(index)
            row = self._read_row(index)
            return dict_to_atoms(row)
        if isinstance(index, slice):
            indices = range(len(self))[index]
            return RowView(self, list(indices))
        if isinstance(index, str):
            return ColumnView(self, index)
        if isinstance(index, list):
            if not index:
                return RowView(self, [])
            if isinstance(index[0], int):
                n = len(self)
                normalized = []
                for i in index:
                    idx = i + n if i < 0 else i
                    if idx < 0 or idx >= n:
                        raise IndexError(i)
                    normalized.append(idx)
                return RowView(self, normalized)
            if isinstance(index[0], str):
                return ColumnView(self, index)
        raise TypeError(f"Unsupported index type: {type(index)}")

    def __setitem__(self, index: int, value: ase.Atoms) -> None:
        if not isinstance(self._backend, WritableBackend):
            raise TypeError("Backend is read-only")
        data = atoms_to_dict(value)
        self._backend.write_row(index, data)

    def __delitem__(self, index: int) -> None:
        if not isinstance(self._backend, WritableBackend):
            raise TypeError("Backend is read-only")
        self._backend.delete_row(index)

    def insert(self, index: int, value: ase.Atoms) -> None:
        if not isinstance(self._backend, WritableBackend):
            raise TypeError("Backend is read-only")
        data = atoms_to_dict(value)
        self._backend.insert_row(index, data)

    def extend(self, values: list[ase.Atoms]) -> None:
        """Efficiently extend with multiple Atoms objects using bulk operations."""
        if not isinstance(self._backend, WritableBackend):
            raise TypeError("Backend is read-only")
        data_list = [atoms_to_dict(atoms) for atoms in values]
        self._backend.append_rows(data_list)

    def __len__(self) -> int:
        return len(self._backend)

    def __iter__(self) -> Iterator[ase.Atoms]:
        # Explicit IndexError sentinel — avoids len() which list() calls
        # for pre-allocation. Works for backends with unknown length.
        i = 0
        while True:
            try:
                yield self[i]
                i += 1
            except IndexError:
                return

    _VALID_PREFIXES = ("arrays.", "info.", "calc.")
    _VALID_TOP_LEVEL = ("cell", "pbc", "constraints")

    def _validate_keys(self, data: dict[str, Any]) -> None:
        """Validate that all keys follow the namespace convention."""
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

    def update(
        self,
        index: int,
        data: dict[str, Any] | None = None,
        *,
        info: dict[str, Any] | None = None,
        arrays: dict[str, np.ndarray] | None = None,
        calc: dict[str, Any] | None = None,
    ) -> None:
        """Update specific keys at index.

        Keys must follow the namespace convention: ``calc.*``, ``info.*``,
        ``arrays.*``, or top-level keys (``cell``, ``pbc``, ``constraints``).

        Flat-dict API::

            db.update(i, {"calc.energy": -10.5, "info.tag": "done"})

        Keyword API::

            db.update(i, info={"tag": "done"}, calc={"energy": -10.5})
        """
        if not isinstance(self._backend, WritableBackend):
            raise TypeError("Backend is read-only")

        # Build flat dict from either new or legacy API
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
        self._backend.update_row(index, flat_data)
