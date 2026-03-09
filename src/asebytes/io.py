from __future__ import annotations

import warnings
from collections.abc import Iterator, MutableSequence
from typing import Any, overload

import ase
import numpy as np

from ._convert import atoms_to_dict, dict_to_atoms
from ._backends import ReadBackend, ReadWriteBackend
from ._schema import SchemaEntry
from ._views import ASEColumnView, RowView


class ASEIO(MutableSequence):
    """Storage-agnostic mutable sequence for ASE Atoms objects.

    Supports pluggable backends (LMDB, HuggingFace, Zarr) and pandas-style
    lazy views for column-oriented data access.

    Parameters
    ----------
    backend : str | ReadBackend[str, Any]
        Either a file path (auto-creates LMDBBackend) or a backend instance.
    readonly : bool | None
        Force read-only or writable mode. None (default) auto-detects.
    cache_to : str | ReadWriteBackend[str, Any] | None
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
        backend: str | ReadBackend[str, Any],
        *,
        readonly: bool | None = None,
        cache_to: str | ReadWriteBackend[str, Any] | None = None,
        **kwargs: Any,
    ):
        if isinstance(backend, str):
            from ._registry import get_backend_cls, parse_uri

            scheme, _remainder = parse_uri(backend)
            cls = get_backend_cls(backend, readonly=readonly)
            if scheme is not None and hasattr(cls, "from_uri"):
                # URI-style: delegate to from_uri constructor
                self._backend: ReadBackend[str, Any] = cls.from_uri(backend, **kwargs)
            else:
                # File path: pass path directly to backend constructor
                self._backend = cls(backend, **kwargs)
        else:
            self._backend = backend

        # Persistent read-through cache
        if cache_to is None:
            self._cache: ReadWriteBackend[str, Any] | None = None
        elif isinstance(cache_to, str):
            from ._registry import get_backend_cls

            cache_cls = get_backend_cls(cache_to, readonly=False)
            self._cache = cache_cls(cache_to)
        elif isinstance(cache_to, ReadWriteBackend):
            self._cache = cache_to
        else:
            raise TypeError(
                f"cache_to must be str or ReadWriteBackend, "
                f"got {type(cache_to).__name__}"
            )

        if (
            self._cache is not None
            and readonly is not True
            and isinstance(self._backend, ReadWriteBackend)
        ):
            warnings.warn(
                "cache_to with a writable source may serve stale data after "
                "mutations. cache_to is designed for immutable sources.",
                stacklevel=2,
            )

    @staticmethod
    def list_groups(path: str, **kwargs: Any) -> list[str]:
        """List available groups at the given path.

        Parameters
        ----------
        path : str
            File path or URI to the storage location.
        **kwargs
            Backend-specific options (e.g., credentials).

        Returns
        -------
        list[str]
            List of group names available at the path.
        """
        from ._registry import get_backend_cls

        cls = get_backend_cls(path, readonly=True)
        return cls.list_groups(path, **kwargs)

    def keys(self, index: int) -> list[str]:
        """Return keys present at *index*."""
        return self._backend.keys(index)

    def schema(self, index: int | None = None) -> dict[str, SchemaEntry]:
        """Inspect column names, dtypes, and shapes."""
        if index is None:
            index = 0
        n = len(self)
        if index < 0:
            index += n
        if index < 0 or index >= n:
            raise IndexError(index)
        return self._backend.schema(index)

    # --- Internal methods used by views ---

    def _read_row(self, index: int, keys: list[str] | None = None) -> dict[str, Any]:
        if self._cache is not None:
            try:
                return self._cache.get(index, keys)
            except (IndexError, KeyError):
                pass
            # Cache miss -- read full row from source, write to cache
            full_row = self._backend.get(index)
            try:
                self._cache.set(index, full_row)
            except Exception:
                pass  # cache write is best-effort
            if keys is not None:
                return {k: full_row[k] for k in keys if k in full_row}
            return full_row
        return self._backend.get(index, keys)

    def _read_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any]]:
        if self._cache is not None:
            return [self._read_row(i, keys) for i in indices]
        return self._backend.get_many(indices, keys)

    def _iter_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> Iterator[dict[str, Any]]:
        if self._cache is not None:
            return (self._read_row(i, keys) for i in indices)
        return self._backend.iter_rows(indices, keys)

    def _read_column(self, key: str, indices: list[int]) -> list[Any]:
        if self._cache is not None:
            return [self._read_row(i, [key])[key] for i in indices]
        result = self._backend.get_column(key, indices)
        if all(v is None for v in result):
            for i in indices:
                row_keys = self._backend.keys(i)
                if not row_keys:
                    continue
                if key in row_keys:
                    return result
            raise KeyError(key)
        return result

    def _write_row(self, index: int, data: Any) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.set(index, data)

    def _update_row(self, index: int, data: dict[str, Any]) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.update(index, data)

    def _update_many(self, start: int, data: list) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.update_many(start, data)

    def _set_column(self, key, start: int, values: list) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.set_column(key, start, values)

    def _write_many(self, start: int, data: list) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.set_many(start, data)

    def _delete_row(self, index: int) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.delete(index)

    def _delete_rows(self, start: int, stop: int) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.delete_many(start, stop)

    def _drop_keys(self, keys: list[str], indices: list[int]) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.drop_keys(keys, indices)

    def _build_result(self, row: dict[str, Any] | None) -> ase.Atoms | None:
        if row is None:
            return None
        copy = getattr(self._backend, '_returns_mutable', True)
        return dict_to_atoms(row, copy=copy)

    # --- MutableSequence interface ---

    @overload
    def __getitem__(self, index: int) -> ase.Atoms: ...
    @overload
    def __getitem__(self, index: slice) -> RowView[ase.Atoms]: ...
    @overload
    def __getitem__(self, index: list[int]) -> RowView[ase.Atoms]: ...
    @overload
    def __getitem__(self, index: str) -> ASEColumnView: ...
    @overload
    def __getitem__(self, index: list[str]) -> ASEColumnView: ...

    def __getitem__(
        self,
        index: int | slice | str | list[int] | list[str],
    ) -> ase.Atoms | RowView[ase.Atoms] | ASEColumnView:
        if isinstance(index, int):
            if index < 0:
                try:
                    n = len(self)
                except TypeError:
                    len(self)  # re-raise TypeError
                index += n
                if index < 0:
                    raise IndexError(index - n)
            try:
                row = self._read_row(index)
            except IndexError:
                raise IndexError(index) from None
            return self._build_result(row)
        if isinstance(index, slice):
            indices = range(len(self))[index]
            return RowView(self, list(indices), column_view_cls=ASEColumnView)
        if isinstance(index, str):
            return ASEColumnView(self, index)
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
                return RowView(self, normalized, column_view_cls=ASEColumnView)
            if isinstance(index[0], str):
                return ASEColumnView(self, index)
        raise TypeError(f"Unsupported index type: {type(index)}")

    def __setitem__(self, index: int, value: ase.Atoms) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        data = atoms_to_dict(value)
        self._backend.set(index, data)

    def __delitem__(self, index: int) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.delete(index)

    def insert(self, index: int, value: ase.Atoms | None) -> None:
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        if value is None:
            self._backend.insert(index, None)
        else:
            self._backend.insert(index, atoms_to_dict(value))

    def extend(self, values: list[ase.Atoms]) -> int:
        """Efficiently extend with multiple Atoms objects using bulk operations."""
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        data_list = [atoms_to_dict(atoms) for atoms in values]
        return self._backend.extend(data_list)

    def get(self, index: int, keys: list[str] | None = None) -> ase.Atoms | None:
        """Read a single row, optionally filtering to specific keys.

        Returns an ase.Atoms object (applies dict_to_atoms conversion),
        or None for reserved/placeholder rows.
        """
        row = self._read_row(index, keys)
        return self._build_result(row)

    def drop(self, *, keys: list[str]) -> None:
        """Remove specified columns from all rows."""
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.drop_keys(keys)

    def reserve(self, count: int) -> None:
        """Pre-allocate space for `count` additional rows (hint to backend)."""
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.reserve(count)

    def clear(self) -> None:
        """Remove all rows but keep the container."""
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.clear()

    def remove(self) -> None:
        """Remove the entire container (backend-specific)."""
        if not isinstance(self._backend, ReadWriteBackend):
            raise TypeError("Backend is read-only")
        self._backend.remove()

    def __len__(self) -> int:
        return len(self._backend)

    def __iter__(self) -> Iterator[ase.Atoms]:
        try:
            n = len(self)
        except TypeError:
            # Backend with unknown length (e.g. file-based ASE backend);
            # fall back to index-probing.
            i = 0
            while True:
                try:
                    yield self[i]
                    i += 1
                except IndexError:
                    return
        else:
            for i in range(n):
                yield self[i]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def __repr__(self) -> str:
        return f"ASEIO(backend={self._backend!r})"

    def __add__(self, other: Any) -> "ConcatView":
        from ._concat import ConcatView

        if isinstance(other, ConcatView):
            if type(other._sources[0]) is not type(self):
                raise TypeError(
                    f"Cannot concat {type(self).__name__} "
                    f"with {type(other._sources[0]).__name__}"
                )
            return ConcatView([self] + other._sources)
        if type(other) is not type(self):
            raise TypeError(
                f"Cannot concat {type(self).__name__} with {type(other).__name__}"
            )
        return ConcatView([self, other])

    def __radd__(self, other: Any) -> "ConcatView":
        if other == []:
            from ._concat import ConcatView

            return ConcatView([self])
        return NotImplemented

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
        if not isinstance(self._backend, ReadWriteBackend):
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
        self._backend.update(index, flat_data)
