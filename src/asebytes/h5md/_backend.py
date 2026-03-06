"""H5MD read-write backend for asebytes.

Thin specialization of :class:`~asebytes.columnar.PaddedColumnarBackend`
that produces files compatible with znh5md and standard H5MD readers.
Supports ZnH5MD extensions: variable particle count (NaN padding)
and per-frame PBC.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import h5py
import numpy as np

from asebytes.columnar._padded import PaddedColumnarBackend
from asebytes.columnar._utils import get_fill_value, get_version, jsonable
from asebytes.h5md._mapping import (
    ASE_TO_H5MD,
    H5MD_TO_ASE,
    KNOWN_PARTICLE_ELEMENTS,
    ORIGIN_ATTR,
)
from asebytes.h5md._store import H5MDStore


def _strip_nan_rows(arr: np.ndarray) -> np.ndarray:
    """Remove trailing NaN rows -- fallback for files without ``_n_atoms``."""
    if arr.ndim == 0:
        return arr
    if arr.ndim == 1:
        mask = ~np.isnan(arr)
        if not mask.any():
            return arr[:0]
        last = len(mask) - np.argmax(mask[::-1])
        return arr[:last]
    # Multi-dim: collapse all but first axis
    mask = ~np.isnan(arr)
    valid = mask.reshape(arr.shape[0], -1).any(axis=1)
    if not valid.any():
        return arr[:0]
    last = len(valid) - np.argmax(valid[::-1])
    return arr[:last]


class H5MDBackend(PaddedColumnarBackend):
    """Read-write H5MD backend using h5py.

    Inherits padded columnar storage from
    :class:`~asebytes.columnar.PaddedColumnarBackend` and adds
    H5MD-specific concerns: metadata skeleton, connectivity,
    auto-inferred variable shape, and znh5md compatibility.

    Append-only: ``insert`` and ``delete`` raise
    ``NotImplementedError``.
    """

    def __init__(
        self,
        file: str | Path | None = None,
        *,
        file_handle: h5py.File | None = None,
        file_factory: Any = None,
        group: str | None = None,
        readonly: bool = False,
        compression: str | None = "gzip",
        compression_opts: int | None = None,
        chunk_frames: int = 64,
        pbc_group: bool = True,
        author_name: str | None = None,
        author_email: str | None = None,
        rdcc_nbytes: int = 64 * 1024 * 1024,
        # Legacy compat -- silently ignored
        variable_shape: bool = True,
        chunk_size: int | tuple[int, ...] | list[int] | None = None,
    ):
        # Resolve particles group: if group not given, sniff from file
        resolved_group = self._resolve_particles_group(
            file, file_handle, group, readonly, rdcc_nbytes
        )

        store = H5MDStore(
            path=file if file_handle is None and file_factory is None else None,
            file_handle=file_handle,
            file_factory=file_factory,
            group=resolved_group,
            readonly=readonly,
            compression=compression,
            compression_opts=compression_opts,
            chunk_frames=chunk_frames,
            rdcc_nbytes=rdcc_nbytes,
        )

        self._pbc_group = pbc_group
        self._author_name = author_name
        self._author_email = author_email
        self._h5md_initialized = False
        self._conn_cache: dict[str, tuple[str, Any]] = {}

        super().__init__(
            store=store,
            group=resolved_group,
            readonly=readonly,
        )

    # ------------------------------------------------------------------
    # Group resolution
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_particles_group(
        file: str | Path | None,
        file_handle: h5py.File | None,
        requested: str | None,
        readonly: bool,
        rdcc_nbytes: int,
    ) -> str:
        """Pick the particles group -- from arg, file, or default."""
        if requested is not None:
            return requested
        # Try to sniff from an existing file
        f = file_handle
        opened = False
        if f is None and file is not None and Path(file).exists():
            mode = "r" if readonly else "a"
            f = h5py.File(str(file), mode, rdcc_nbytes=rdcc_nbytes)
            opened = True
        try:
            if f is not None and "particles" in f:
                groups = list(f["particles"].keys())
                if groups:
                    return groups[0]
        finally:
            if opened and f is not None:
                f.close()
        return "atoms"

    @staticmethod
    def list_groups(path: str, **kwargs: Any) -> list[str]:
        """List particles group names in an H5MD file."""
        return H5MDStore.list_groups(path)

    # ------------------------------------------------------------------
    # H5MD skeleton
    # ------------------------------------------------------------------

    def _init_h5md(self) -> None:
        """Create mandatory H5MD skeleton on first write."""
        f = self._store._file
        if "h5md" in f:
            self._h5md_initialized = True
            return
        h5md = f.create_group("h5md")
        h5md.attrs["version"] = np.array([1, 1])
        author = h5md.create_group("author")
        if self._author_name is not None:
            author.attrs["name"] = self._author_name
        if self._author_email is not None:
            author.attrs["email"] = self._author_email
        creator = h5md.create_group("creator")
        creator.attrs["name"] = "asebytes"
        creator.attrs["version"] = get_version()
        f.require_group("particles")
        self._h5md_initialized = True

    # ------------------------------------------------------------------
    # _discover_variant override
    # ------------------------------------------------------------------

    def _discover_variant(self) -> None:
        """Extend padded discovery with H5MD-specific state."""
        super()._discover_variant()
        # Check if H5MD skeleton exists
        f = self._store._file
        self._h5md_initialized = "h5md" in f

        # Discover connectivity datasets
        self._conn_cache = {}
        grp_name = self.group
        conn_path = f"connectivity/{grp_name}"
        if conn_path in f:
            conn = f[conn_path]
            if "bonds" in conn:
                obj = conn["bonds"]
                if isinstance(obj, h5py.Group) and "value" in obj:
                    self._conn_cache["bonds"] = ("td", obj["value"])
                elif isinstance(obj, h5py.Dataset):
                    self._conn_cache["bonds"] = ("static", obj)
            if "bond_orders" in conn:
                obj = conn["bond_orders"]
                if isinstance(obj, h5py.Group) and "value" in obj:
                    self._conn_cache["bond_orders"] = ("td", obj["value"])
                elif isinstance(obj, h5py.Dataset):
                    self._conn_cache["bond_orders"] = ("static", obj)

    # ------------------------------------------------------------------
    # extend override
    # ------------------------------------------------------------------

    def extend(self, data: list[dict[str, Any] | None]) -> int:
        if not data:
            return self._n_frames

        # Initialize H5MD skeleton on first write
        if not self._h5md_initialized:
            self._init_h5md()

        # Extract connectivity before passing to base -- it uses a
        # dedicated H5MD connectivity/ group, not regular columns.
        self._write_connectivity(data)

        # Species (arrays.numbers) must be stored as float64 for znh5md
        # compat.  Convert in-place before base sees them.
        for row in data:
            if row is None:
                continue
            nums = row.get("arrays.numbers")
            if nums is not None and isinstance(nums, np.ndarray):
                if nums.dtype.kind != "f":
                    row["arrays.numbers"] = nums.astype(np.float64)

        return super().extend(data)

    # ------------------------------------------------------------------
    # get override
    # ------------------------------------------------------------------

    def get(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any] | None:
        result = super().get(index, keys)

        # Add connectivity from H5MD connectivity/ group
        if self._conn_cache and (keys is None or "info.connectivity" in keys):
            conn = self._read_connectivity_frame(self._check_index(index))
            if conn is not None:
                if result is None:
                    result = {}
                result["info.connectivity"] = conn

        return result

    # ------------------------------------------------------------------
    # get_many override
    # ------------------------------------------------------------------

    def get_many(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any] | None]:
        results = super().get_many(indices, keys)

        # Inject connectivity
        if self._conn_cache and (keys is None or "info.connectivity" in keys):
            checked = [self._check_index(i) for i in indices]
            for j, idx in enumerate(checked):
                conn = self._read_connectivity_frame(idx)
                if conn is not None:
                    if results[j] is None:
                        results[j] = {}
                    results[j]["info.connectivity"] = conn

        return results

    # ------------------------------------------------------------------
    # Postprocessing override -- species int coercion + nan-strip fallback
    # ------------------------------------------------------------------

    def _postprocess(
        self,
        val: Any,
        col_name: str,
        *,
        is_per_atom: bool = False,
        n_atoms: int | None = None,
    ) -> Any:
        """Extend base postprocessing with H5MD-specific handling.

        - Species (arrays.numbers) stored as float must come back as int.
        - Files without _n_atoms (e.g. znh5md) fall back to NaN-strip.
        """
        result = super()._postprocess(
            val, col_name, is_per_atom=is_per_atom, n_atoms=n_atoms
        )

        # Species: coerce float -> int for arrays.numbers
        if col_name == "arrays.numbers" and isinstance(result, np.ndarray):
            if result.dtype.kind == "f":
                result = result.astype(int)

        return result

    def _unpad_per_atom(
        self, val: Any, col_name: str, *, n_atoms: int | None = None
    ) -> Any:
        """Trim padding, with NaN-strip fallback for znh5md files."""
        if n_atoms is not None and isinstance(val, np.ndarray) and val.ndim >= 1:
            return val[:n_atoms]
        # Fallback for files without _n_atoms metadata
        if isinstance(val, np.ndarray) and val.dtype.kind == "f":
            return _strip_nan_rows(val)
        return val

    # ------------------------------------------------------------------
    # Connectivity (H5MD connectivity/ group)
    # ------------------------------------------------------------------

    def _write_connectivity(self, data: list[dict[str, Any] | None]) -> None:
        """Write connectivity to H5MD-standard ``connectivity/bonds``.

        Stores bonds as ``int32[n_frames, max_bonds, 2]`` with ``-1`` fill,
        and optional bond orders as ``float64[n_frames, max_bonds]`` with
        ``NaN`` fill.
        """
        conn_key = "info.connectivity"
        raw = [row.get(conn_key) if row is not None else None for row in data]

        # Remove connectivity from data so base extend doesn't try to store it
        for row in data:
            if row is not None:
                row.pop(conn_key, None)

        if all(v is None for v in raw):
            return

        # Parse tuples into bonds / bond_orders per frame
        bonds_list: list[np.ndarray | None] = []
        orders_list: list[np.ndarray | None] = []
        has_orders = False
        max_bonds = 0

        for v in raw:
            if v is None:
                bonds_list.append(None)
                orders_list.append(None)
                continue
            tuples = list(v)
            nb = len(tuples)
            max_bonds = max(max_bonds, nb)
            b = np.empty((nb, 2), dtype=np.int32)
            o = np.empty(nb, dtype=np.float64)
            for j, t in enumerate(tuples):
                b[j, 0] = int(t[0])
                b[j, 1] = int(t[1])
                if len(t) >= 3:
                    o[j] = float(t[2])
                    has_orders = True
                else:
                    o[j] = np.nan
            bonds_list.append(b)
            orders_list.append(o)

        if max_bonds == 0:
            return

        n_new = len(data)
        grp_name = self.group
        f = self._store._file
        bonds_path = f"connectivity/{grp_name}/bonds"
        if bonds_path in f:
            existing_ds = f[bonds_path]["value"]
            old_max = existing_ds.shape[1]
            max_bonds = max(max_bonds, old_max)

        # Build padded arrays
        bonds_arr = np.full((n_new, max_bonds, 2), -1, dtype=np.int32)
        for i, b in enumerate(bonds_list):
            if b is not None and len(b) > 0:
                bonds_arr[i, : len(b)] = b

        orders_arr: np.ndarray | None = None
        if has_orders:
            orders_arr = np.full((n_new, max_bonds), np.nan, dtype=np.float64)
            for i, o in enumerate(orders_list):
                if o is not None and len(o) > 0:
                    orders_arr[i, : len(o)] = o

        if bonds_path in f:
            self._extend_connectivity_ds(bonds_path, bonds_arr, -1)
        else:
            self._create_connectivity_ds(
                bonds_path, bonds_arr, np.int32, -1, grp_name
            )

        if orders_arr is not None:
            bo_path = f"connectivity/{grp_name}/bond_orders"
            if bo_path in f:
                self._extend_connectivity_ds(bo_path, orders_arr, np.nan)
            else:
                self._create_connectivity_ds(
                    bo_path, orders_arr, np.float64, np.nan, grp_name
                )

    def _create_connectivity_ds(
        self,
        h5_path: str,
        data: np.ndarray,
        dtype: Any,
        fillvalue: Any,
        particles_group: str,
    ) -> None:
        """Create an H5MD time-dependent connectivity dataset."""
        f = self._store._file
        grp = f.require_group(h5_path)
        n = data.shape[0]
        full_shape = (self._n_frames + n,) + data.shape[1:]
        maxshape = tuple(None for _ in full_shape)
        chunks_0 = max(1, min(64, full_shape[0]))
        chunks = (chunks_0,) + data.shape[1:]
        ds = grp.create_dataset(
            "value",
            shape=full_shape,
            maxshape=maxshape,
            fillvalue=fillvalue,
            dtype=dtype,
            compression=self._store._compression,
            compression_opts=self._store._compression_opts,
            chunks=chunks,
        )
        ds[self._n_frames :] = data

        grp.attrs["particles_group"] = f[f"particles/{particles_group}"].ref

        grp.create_dataset("step", data=1)
        time_ds = grp.create_dataset("time", data=1.0)
        time_ds.attrs["unit"] = "fs"

    def _extend_connectivity_ds(
        self, h5_path: str, data: np.ndarray, fillvalue: Any
    ) -> None:
        """Extend an existing connectivity dataset, growing N dim if needed."""
        f = self._store._file
        grp = f[h5_path]
        ds = grp["value"]
        old_shape = ds.shape
        n_new = data.shape[0]
        shift = self._n_frames - old_shape[0]

        if data.ndim >= 2 and old_shape[1] != data.shape[1]:
            new_second = max(old_shape[1], data.shape[1])
            target = (old_shape[0] + n_new + shift, new_second) + old_shape[2:]
            ds.resize(target)
            if data.shape[1] < new_second:
                padded = np.full(
                    (n_new, new_second) + data.shape[2:],
                    fillvalue,
                    dtype=data.dtype,
                )
                padded[:, : data.shape[1]] = data
                data = padded
        else:
            target = (old_shape[0] + n_new + shift,) + old_shape[1:]
            ds.resize(target)

        ds[old_shape[0] + shift :] = data

    def _read_connectivity_frame(self, index: int) -> list[list] | None:
        """Read connectivity for a single frame."""
        if "bonds" not in self._conn_cache:
            return None
        kind, ref = self._conn_cache["bonds"]
        if kind == "td":
            bonds = ref[index]
        else:
            bonds = ref[()]
        orders = None
        if "bond_orders" in self._conn_cache:
            okind, oref = self._conn_cache["bond_orders"]
            if okind == "td":
                orders = oref[index]
            else:
                orders = oref[()]
        return self._assemble_connectivity(bonds, orders)

    @staticmethod
    def _assemble_connectivity(
        bonds: np.ndarray, orders: np.ndarray | None
    ) -> list[list] | None:
        """Build connectivity list from bonds + optional bond_orders arrays.

        Strips -1 padding from time-dependent storage.
        """
        if bonds.ndim == 1:
            return None
        valid = np.all(bonds >= 0, axis=1)
        bonds = bonds[valid]
        if len(bonds) == 0:
            return None
        if orders is not None:
            orders = orders[valid]
            return [
                [int(b[0]), int(b[1]), float(orders[i])]
                for i, b in enumerate(bonds)
            ]
        return [[int(b[0]), int(b[1])] for b in bonds]

    # ------------------------------------------------------------------
    # Schema override for box columns (H5MDStore exposes them as regular)
    # ------------------------------------------------------------------

    def schema(self, index: int = 0) -> dict:
        """Schema with H5MD-aware column types."""
        result = super().schema(index)

        # Connectivity isn't a regular column -- add it if present
        if self._conn_cache:
            from asebytes._schema import SchemaEntry
            result["info.connectivity"] = SchemaEntry(dtype=str, shape=())

        return result

    def keys(self, index: int) -> list[str]:
        """Keys at index, including connectivity if present."""
        result = super().keys(index)

        if self._conn_cache:
            conn = self._read_connectivity_frame(self._check_index(index))
            if conn is not None:
                result.append("info.connectivity")

        return result

    # ------------------------------------------------------------------
    # _store_rewrite_array override for H5MDStore
    # ------------------------------------------------------------------

    def _store_rewrite_array(
        self, name: str, data: np.ndarray, dtype: Any, fill_value: Any
    ) -> None:
        """Rewrite an array in H5MDStore (resize h5py dataset directly)."""
        ds = self._store._get_ds(name)
        ds.resize(data.shape)
        ds[...] = data
        self._store._ds_cache.pop(name, None)

    # ------------------------------------------------------------------
    # set override -- pad values for variable-shape storage
    # ------------------------------------------------------------------

    def set(self, index: int, data: dict[str, Any] | None) -> None:
        if data is None:
            raise TypeError(
                "H5MDBackend.set() does not support None rows. "
                "H5MD is append-only and cannot represent placeholder rows."
            )
        # Convert numbers to float for znh5md compat before passing to base
        if "arrays.numbers" in data:
            nums = data["arrays.numbers"]
            if isinstance(nums, np.ndarray) and nums.dtype.kind != "f":
                data = dict(data)
                data["arrays.numbers"] = nums.astype(np.float64)
        super().set(index, data)


# Backward compatibility aliases
H5MDObjectBackend = H5MDBackend
