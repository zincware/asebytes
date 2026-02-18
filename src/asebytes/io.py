from __future__ import annotations

from collections.abc import Iterator, MutableSequence
from typing import Any, overload

import ase
import numpy as np

from asebytes._convert import atoms_to_dict, dict_to_atoms
from asebytes._protocols import ReadableBackend, WritableBackend
from asebytes._views import ColumnView, RowView


class ASEIO(MutableSequence):
    """Storage-agnostic mutable sequence for ASE Atoms objects.

    Supports pluggable backends (LMDB, HuggingFace, Zarr) and pandas-style
    lazy views for column-oriented data access.

    Parameters
    ----------
    backend : str | ReadableBackend | WritableBackend
        Either a file path (auto-creates LMDBBackend) or a backend instance.
    **kwargs
        When backend is a str, forwarded to LMDBBackend constructor
        (prefix, map_size, readonly, etc.).
    """

    def __init__(
        self,
        backend: str | ReadableBackend,
        *,
        readonly: bool = False,
        **kwargs: Any,
    ):
        if isinstance(backend, str):
            from asebytes._registry import get_backend_cls

            cls = get_backend_cls(backend, readonly=readonly)
            self._backend: ReadableBackend = cls(backend, **kwargs)
        else:
            self._backend = backend

    @property
    def columns(self) -> list[str]:
        """Available column names (inspects first row)."""
        if len(self._backend) == 0:
            return []
        return self._backend.columns()

    # --- Internal methods used by views ---

    def _read_row(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any]:
        return self._backend.read_row(index, keys)

    def _read_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any]]:
        return self._backend.read_rows(indices, keys)

    def _iter_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> Iterator[dict[str, Any]]:
        return self._backend.iter_rows(indices, keys)

    def _read_column(self, key: str, indices: list[int]) -> list[Any]:
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
            n = len(self)
            if index < 0:
                index += n
            if index < 0 or index >= n:
                raise IndexError(index)
            row = self._backend.read_row(index)
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
        for i in range(len(self)):
            yield self[i]

    # --- Legacy API (backward compatible) ---

    def get_available_keys(self, index: int) -> list[bytes]:
        """Get available keys at index (legacy API, returns bytes keys)."""
        cols = self._backend.columns(index)
        return [c.encode() for c in cols]

    def get(
        self, index: int, keys: list[bytes] | None = None
    ) -> ase.Atoms:
        """Get Atoms at index, optionally filtering to specific keys (legacy API)."""
        str_keys = [k.decode() for k in keys] if keys is not None else None
        row = self._backend.read_row(index, str_keys)
        return dict_to_atoms(row)

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
