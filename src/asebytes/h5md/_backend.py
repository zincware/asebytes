"""H5MD read-write backend for asebytes.

Produces files compatible with znh5md and standard H5MD readers.
Supports ZnH5MD extensions: variable particle count (NaN padding)
and per-frame PBC.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import h5py
import numpy as np


def _jsonable(obj: Any) -> Any:
    """Recursively convert numpy types so ``json.dumps`` succeeds."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    return obj

from asebytes._protocols import WritableBackend
from asebytes.h5md._mapping import (
    ASE_TO_H5MD,
    H5MD_TO_ASE,
    KNOWN_PARTICLE_ELEMENTS,
    ORIGIN_ATTR,
)


class H5MDBackend(WritableBackend):
    """Read-write H5MD backend using h5py.

    Supports standard H5MD files and ZnH5MD extensions
    (variable particle count via NaN padding, per-frame PBC).
    Append-only: ``insert_row`` and ``delete_row`` raise
    ``NotImplementedError``.
    """

    def __init__(
        self,
        file: str | Path | None = None,
        *,
        file_handle: h5py.File | None = None,
        particles_group: str | None = None,
        readonly: bool = False,
        compression: str | None = "gzip",
        compression_opts: int | None = None,
        variable_shape: bool = True,
        pbc_group: bool = True,
        chunk_size: int | tuple[int, ...] | list[int] | None = (64, 64),
        author_name: str | None = None,
        author_email: str | None = None,
    ):
        if file_handle is not None:
            self._file = file_handle
            self._owns_file = False
        elif file is not None:
            mode = "r" if readonly else "a"
            self._file = h5py.File(file, mode)
            self._owns_file = True
        else:
            raise ValueError("Provide either file or file_handle")

        self._readonly = readonly
        self._compression = compression
        self._compression_opts = compression_opts
        self._variable_shape = variable_shape
        self._pbc_group = pbc_group
        self._chunk_size = chunk_size
        self._author_name = author_name
        self._author_email = author_email

        # Resolve particles group name
        self._grp_name = self._resolve_particles_group(particles_group)

        self._n_frames = 0
        self._max_atoms = 0
        self._discover()

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _resolve_particles_group(self, requested: str | None) -> str:
        """Pick the particles group – from arg, file, or default."""
        if requested is not None:
            return requested
        if "particles" in self._file:
            groups = list(self._file["particles"].keys())
            if groups:
                return groups[0]
        return "atoms"

    @staticmethod
    def list_groups(file: str | Path) -> list[str]:
        """List particles group names in an H5MD file."""
        with h5py.File(file, "r") as f:
            if "particles" not in f:
                return []
            return list(f["particles"].keys())

    def _discover(self) -> None:
        """Read frame count, max-atoms, and cache dataset references."""
        self._col_cache: dict[str, tuple[h5py.Dataset, str]] = {}
        self._box_cache: dict[str, tuple[str, Any]] = {}
        self._conn_cache: dict[str, tuple[str, Any]] = {}

        pgrp = f"particles/{self._grp_name}"
        if pgrp not in self._file:
            return
        grp = self._file[pgrp]
        if "species" in grp and isinstance(grp["species"], h5py.Group):
            if "value" in grp["species"]:
                ds = grp["species"]["value"]
                self._n_frames = ds.shape[0]
                if ds.ndim > 1:
                    self._max_atoms = ds.shape[1]

        # Cache particle dataset references
        for name in grp:
            if name == "box":
                self._cache_box(grp["box"])
                continue
            elem = grp[name]
            if not isinstance(elem, h5py.Group) or "value" not in elem:
                continue
            key = self._h5_to_key(name, elem)
            self._col_cache[key] = (elem["value"], name)

        # Cache observable dataset references
        opath = f"observables/{self._grp_name}"
        if opath in self._file:
            for name in self._file[opath]:
                elem = self._file[opath][name]
                if not isinstance(elem, h5py.Group) or "value" not in elem:
                    continue
                key = self._h5_to_key(name, elem)
                self._col_cache[key] = (elem["value"], name)

        # Cache connectivity dataset references
        conn_path = f"connectivity/{self._grp_name}"
        if conn_path in self._file:
            conn = self._file[conn_path]
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

    def _cache_box(self, box_grp: h5py.Group) -> None:
        """Cache box/cell/pbc dataset references."""
        if "edges" in box_grp:
            edges = box_grp["edges"]
            if isinstance(edges, h5py.Group) and "value" in edges:
                self._box_cache["cell"] = ("td", edges["value"])
            elif isinstance(edges, h5py.Dataset):
                self._box_cache["cell"] = ("static", edges)

        if "pbc" in box_grp:
            pbc_obj = box_grp["pbc"]
            if isinstance(pbc_obj, h5py.Group) and "value" in pbc_obj:
                self._box_cache["pbc"] = ("td", pbc_obj["value"])
            elif isinstance(pbc_obj, h5py.Dataset):
                self._box_cache["pbc"] = ("static", pbc_obj)
        elif "boundary" in box_grp.attrs:
            self._box_cache["pbc"] = ("boundary", box_grp.attrs["boundary"])

    # ------------------------------------------------------------------
    # ReadableBackend
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return self._n_frames

    def columns(self, index: int = 0) -> list[str]:
        if self._col_cache or self._box_cache:
            return list(self._box_cache.keys()) + list(self._col_cache.keys())
        return list(self.read_row(index).keys())

    def read_row(self, index: int, keys: list[str] | None = None) -> dict[str, Any]:
        index = self._check_index(index)
        result: dict[str, Any] = {}

        for box_key in ("cell", "pbc"):
            if keys is not None and box_key not in keys:
                continue
            if box_key not in self._box_cache:
                continue
            kind, ref = self._box_cache[box_key]
            if kind == "td":
                val = ref[index]
                if box_key == "pbc":
                    val = np.asarray(val, dtype=bool)
                result[box_key] = val
            elif kind == "static":
                val = ref[()]
                if box_key == "pbc":
                    val = np.asarray(val, dtype=bool)
                result[box_key] = val
            elif kind == "boundary":
                result[box_key] = np.array(
                    [b not in ("none", b"none") for b in ref], dtype=bool
                )

        for key, (ds, h5_name) in self._col_cache.items():
            if keys is not None and key not in keys:
                continue
            # Skip columns shorter than the requested index (backward compat)
            if index >= ds.shape[0]:
                continue
            val = ds[index]
            val = self._postprocess(val, h5_name)
            if val is not None:
                result[key] = val

        # Connectivity (H5MD connectivity/ group)
        if self._conn_cache and (keys is None or "info.connectivity" in keys):
            conn = self._read_connectivity_frame(index)
            if conn is not None:
                result["info.connectivity"] = conn

        return result

    def read_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Bulk columnar read — each dataset is accessed once."""
        if not indices:
            return []

        n = len(indices)
        checked = [self._check_index(i) for i in indices]

        # Sort + deduplicate for efficient HDF5 chunk access
        # (h5py requires sorted, unique indices for fancy indexing)
        order = np.argsort(checked)
        sorted_idx = np.array(checked)[order]
        unique_sorted, inverse = np.unique(sorted_idx, return_inverse=True)

        # Use slice for contiguous ranges (fastest HDF5 path)
        n_unique = len(unique_sorted)
        if n_unique == 1:
            h5_sel = [int(unique_sorted[0])]
        elif np.all(np.diff(unique_sorted) == 1):
            h5_sel = slice(int(unique_sorted[0]), int(unique_sorted[-1]) + 1)
        else:
            h5_sel = unique_sorted

        unique_rows: list[dict[str, Any]] = [{} for _ in range(n_unique)]

        # Box columns
        for box_key in ("cell", "pbc"):
            if keys is not None and box_key not in keys:
                continue
            if box_key not in self._box_cache:
                continue
            kind, ref = self._box_cache[box_key]
            if kind == "td":
                bulk = ref[h5_sel]
                for j in range(n_unique):
                    v = bulk[j]
                    if box_key == "pbc":
                        v = np.asarray(v, dtype=bool)
                    unique_rows[j][box_key] = v
            elif kind == "static":
                val = ref[()]
                if box_key == "pbc":
                    val = np.asarray(val, dtype=bool)
                for row in unique_rows:
                    row[box_key] = val
            elif kind == "boundary":
                pbc = np.array(
                    [b not in ("none", b"none") for b in ref], dtype=bool
                )
                for row in unique_rows:
                    row[box_key] = pbc

        # Regular columns — one bulk read per dataset
        for key, (ds, h5_name) in self._col_cache.items():
            if keys is not None and key not in keys:
                continue
            bulk = ds[h5_sel]
            for j in range(n_unique):
                val = self._postprocess(bulk[j], h5_name)
                if val is not None:
                    unique_rows[j][key] = val

        # Connectivity (H5MD connectivity/ group)
        if self._conn_cache and (keys is None or "info.connectivity" in keys):
            if "bonds" in self._conn_cache:
                kind, ref = self._conn_cache["bonds"]
                if kind == "td":
                    bonds_bulk = ref[h5_sel]
                    orders_bulk = None
                    if "bond_orders" in self._conn_cache:
                        _, oref = self._conn_cache["bond_orders"]
                        orders_bulk = oref[h5_sel]
                    for j in range(n_unique):
                        conn = self._assemble_connectivity(
                            bonds_bulk[j],
                            orders_bulk[j] if orders_bulk is not None else None,
                        )
                        if conn is not None:
                            unique_rows[j]["info.connectivity"] = conn
                elif kind == "static":
                    bonds = ref[()]
                    orders = None
                    if "bond_orders" in self._conn_cache:
                        _, oref = self._conn_cache["bond_orders"]
                        orders = oref[()]
                    conn = self._assemble_connectivity(bonds, orders)
                    if conn is not None:
                        for row in unique_rows:
                            row["info.connectivity"] = conn

        # Map deduplicated rows back to original order
        result: list[dict[str, Any] | None] = [None] * n
        for j in range(n):
            src = unique_rows[inverse[j]]
            result[order[j]] = dict(src) if n_unique < n else src

        return result  # type: ignore[return-value]

    def iter_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> Iterator[dict[str, Any]]:
        """Yield rows using bulk columnar read."""
        yield from self.read_rows(indices, keys)

    def read_column(self, key: str, indices: list[int] | None = None) -> list[Any]:
        """Optimised: reads a single HDF5 dataset directly."""
        if key in self._col_cache:
            ds, h5_name = self._col_cache[key]
        else:
            h5_path = self._find_dataset_path(key)
            if h5_path is None:
                return super().read_column(key, indices)
            grp = self._file[h5_path]
            ds = grp["value"]
            h5_name = h5_path.rsplit("/", 1)[-1]

        if indices is None:
            raw = ds[()]
            return [self._postprocess(raw[i], h5_name) for i in range(len(raw))]

        order = np.argsort(indices)
        sorted_idx = [indices[j] for j in order]
        raw = ds[sorted_idx]
        result: list[Any] = [None] * len(indices)
        for j in range(len(indices)):
            result[order[j]] = self._postprocess(raw[j], h5_name)
        return result

    # ------------------------------------------------------------------
    # WritableBackend (append-only)
    # ------------------------------------------------------------------

    def append_rows(self, data: list[dict[str, Any]]) -> None:
        if not data:
            return

        if self._n_frames == 0 and "h5md" not in self._file:
            self._init_h5md()

        n_new = len(data)
        all_keys = sorted({k for row in data for k in row})

        # Determine new max atoms
        new_max = 0
        for row in data:
            pos = row.get("arrays.positions")
            nums = row.get("arrays.numbers")
            if pos is not None:
                new_max = max(new_max, len(pos))
            elif nums is not None:
                new_max = max(new_max, len(nums))
        max_atoms = max(self._max_atoms, new_max)

        for key in all_keys:
            if key == "constraints":
                continue
            h5_path, origin = self._key_to_h5(key, data)
            if h5_path is None:
                continue
            values = [row.get(key) for row in data]
            self._write_element(h5_path, origin, key, values, max_atoms)

        self._write_connectivity(data)

        # Extend existing columns not in this batch so all datasets stay aligned
        new_total = self._n_frames + n_new
        touched = set(all_keys)
        for key, (ds, h5_name) in list(self._col_cache.items()):
            if key not in touched and ds.shape[0] < new_total:
                target = (new_total,) + ds.shape[1:]
                ds.resize(target)
        for box_key in ("cell", "pbc"):
            if box_key not in touched and box_key in self._box_cache:
                kind, ref = self._box_cache[box_key]
                if kind == "td" and ref.shape[0] < new_total:
                    target = (new_total,) + ref.shape[1:]
                    ref.resize(target)

        self._max_atoms = max_atoms
        self._n_frames += n_new
        self._discover()  # Rebuild dataset cache for new/extended datasets

    def write_row(self, index: int, data: dict[str, Any]) -> None:
        index = self._check_index(index)
        for key, val in data.items():
            h5_path = self._find_dataset_path(key)
            if h5_path is None:
                continue
            ds = self._file[h5_path]["value"]
            val = self._serialize_value(val)
            if isinstance(val, np.ndarray) and self._variable_shape:
                if ds.ndim > 1 and val.ndim >= 1 and val.shape[0] < ds.shape[1]:
                    padded = np.full(ds.shape[1:], np.nan, dtype=np.float64)
                    slices = tuple(slice(0, s) for s in val.shape)
                    padded[slices] = val
                    val = padded
            ds[index] = val

    def insert_row(self, index: int, data: dict[str, Any]) -> None:
        raise NotImplementedError("H5MD backend does not support insert")

    def delete_row(self, index: int) -> None:
        raise NotImplementedError("H5MD backend does not support delete")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        if self._owns_file:
            self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # ------------------------------------------------------------------
    # Internal: read helpers
    # ------------------------------------------------------------------

    def _check_index(self, index: int) -> int:
        if index < 0:
            index += self._n_frames
        if index < 0 or index >= self._n_frames:
            raise IndexError(
                f"Index {index} out of range for {self._n_frames} frames"
            )
        return index

    def _h5_to_key(self, h5_name: str, grp: h5py.Group) -> str:
        """Map an H5MD group name + origin attribute to an asebytes key."""
        ase_name = H5MD_TO_ASE.get(h5_name, h5_name)
        origin = grp.attrs.get(ORIGIN_ATTR, None)
        if isinstance(origin, bytes):
            origin = origin.decode()

        # Core properties always go to arrays.*
        if ase_name in ("positions", "numbers"):
            return f"arrays.{ase_name}"

        # Origin-based routing (znh5md files have this)
        if origin == "calc":
            return f"calc.{ase_name}"
        if origin == "info":
            return f"info.{ase_name}"
        if origin == "arrays":
            return f"arrays.{ase_name}"
        if origin == "atoms":
            if ase_name in ("positions", "numbers"):
                return f"arrays.{ase_name}"
            return f"arrays.{ase_name}"

        # No origin — use heuristics
        if h5_name in KNOWN_PARTICLE_ELEMENTS:
            return f"arrays.{ase_name}"
        # Observables default to calc.*
        return f"calc.{ase_name}"

    def _postprocess(self, val: Any, h5_name: str) -> Any:
        """Strip NaN padding and cast types after reading."""
        if isinstance(val, bytes):
            val = val.decode()
        if isinstance(val, str):
            if val == "":
                return None
            try:
                return json.loads(val)
            except (json.JSONDecodeError, ValueError):
                return val

        # Handle numpy scalars (h5py returns np.float64 for scalar datasets)
        if isinstance(val, np.floating):
            return None if np.isnan(val) else val.item()
        if isinstance(val, np.integer):
            return val.item()

        if isinstance(val, np.ndarray):
            # String arrays
            if val.dtype.kind in ("S", "U", "O"):
                items = []
                for v in val.flat:
                    if isinstance(v, bytes):
                        v = v.decode()
                    if isinstance(v, str) and v == "":
                        items.append(None)
                    elif isinstance(v, str):
                        try:
                            items.append(json.loads(v))
                        except (json.JSONDecodeError, ValueError):
                            items.append(v)
                    else:
                        items.append(v)
                return items if len(items) > 1 else items[0] if items else None

            # Strip NaN padding for per-atom data
            if self._variable_shape and val.ndim >= 1 and val.dtype.kind == "f":
                val = _strip_nan_padding(val)
                if val.size == 0:
                    return None

            # Species/numbers should be int
            if h5_name == "species" and val.dtype.kind == "f":
                val = val.astype(int)

            # Scalar
            if val.ndim == 0:
                v = val.item()
                if isinstance(v, float) and np.isnan(v):
                    return None
                return v

        return val

    def _read_connectivity_frame(self, index: int) -> list[list] | None:
        """Read connectivity for a single frame from the H5MD connectivity/ group."""
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
            # Scalar / empty
            return None
        # Strip -1 padding rows
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

    def _find_dataset_path(self, key: str) -> str | None:
        """Find the H5MD group path for an asebytes key."""
        # Fast path: check cache
        if key in self._col_cache:
            ds, _ = self._col_cache[key]
            return ds.parent.name
        if key in self._box_cache:
            kind, ref = self._box_cache[key]
            if kind in ("td", "static"):
                return ref.parent.name
            return None

        # Slow path: walk the tree (needed for uncached keys during writes)
        ppath = f"particles/{self._grp_name}"
        if ppath in self._file:
            particles = self._file[ppath]
            for name in particles:
                if name == "box":
                    if key == "cell" and "edges" in particles["box"]:
                        return f"{ppath}/box/edges"
                    if key == "pbc" and "pbc" in particles["box"]:
                        return f"{ppath}/box/pbc"
                    continue
                grp = particles[name]
                if not isinstance(grp, h5py.Group) or "value" not in grp:
                    continue
                if self._h5_to_key(name, grp) == key:
                    return f"{ppath}/{name}"

        opath = f"observables/{self._grp_name}"
        if opath in self._file:
            for name in self._file[opath]:
                grp = self._file[opath][name]
                if not isinstance(grp, h5py.Group) or "value" not in grp:
                    continue
                if self._h5_to_key(name, grp) == key:
                    return f"{opath}/{name}"

        return None

    # ------------------------------------------------------------------
    # Internal: write helpers
    # ------------------------------------------------------------------

    def _write_connectivity(self, data: list[dict[str, Any]]) -> None:
        """Write connectivity to H5MD-standard ``connectivity/bonds``.

        Stores bonds as ``int32[n_frames, max_bonds, 2]`` with ``-1`` fill,
        and optional bond orders as ``float64[n_frames, max_bonds]`` with
        ``NaN`` fill.
        """
        conn_key = "info.connectivity"
        raw = [row.get(conn_key) for row in data]

        # Nothing to write if no frame has connectivity
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

        # Check existing connectivity datasets for max_bonds
        n_new = len(data)
        grp_name = self._grp_name
        bonds_path = f"connectivity/{grp_name}/bonds"
        if bonds_path in self._file:
            existing_ds = self._file[bonds_path]["value"]
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

        # Write or extend connectivity/{grp}/bonds
        if bonds_path in self._file:
            self._extend_connectivity_ds(bonds_path, bonds_arr, -1)
        else:
            self._create_connectivity_ds(
                bonds_path, bonds_arr, np.int32, -1, grp_name
            )

        # Write or extend connectivity/{grp}/bond_orders
        if orders_arr is not None:
            bo_path = f"connectivity/{grp_name}/bond_orders"
            if bo_path in self._file:
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
        grp = self._file.require_group(h5_path)
        n = data.shape[0]
        full_shape = (self._n_frames + n,) + data.shape[1:]
        maxshape = tuple(None for _ in full_shape)
        chunks = self._get_chunks(full_shape)
        ds = grp.create_dataset(
            "value",
            shape=full_shape,
            maxshape=maxshape,
            fillvalue=fillvalue,
            dtype=dtype,
            compression=self._compression,
            compression_opts=self._compression_opts,
            chunks=chunks,
        )
        ds[self._n_frames :] = data

        # H5MD spec: object reference to particles group
        grp.attrs["particles_group"] = self._file[
            f"particles/{particles_group}"
        ].ref

        # Linear step/time
        grp.create_dataset("step", data=1)
        time_ds = grp.create_dataset("time", data=1.0)
        time_ds.attrs["unit"] = "fs"

    def _extend_connectivity_ds(
        self, h5_path: str, data: np.ndarray, fillvalue: Any
    ) -> None:
        """Extend an existing connectivity dataset, growing N dim if needed."""
        grp = self._file[h5_path]
        ds = grp["value"]
        old_shape = ds.shape
        n_new = data.shape[0]
        shift = self._n_frames - old_shape[0]

        # Bonds dim may need widening
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

    def _init_h5md(self) -> None:
        """Create mandatory H5MD skeleton."""
        h5md = self._file.create_group("h5md")
        h5md.attrs["version"] = np.array([1, 1])
        author = h5md.create_group("author")
        if self._author_name is not None:
            author.attrs["name"] = self._author_name
        if self._author_email is not None:
            author.attrs["email"] = self._author_email
        creator = h5md.create_group("creator")
        creator.attrs["name"] = "asebytes"
        creator.attrs["version"] = _get_version()
        self._file.require_group("particles")

    def _key_to_h5(
        self, key: str, data: list[dict[str, Any]]
    ) -> tuple[str | None, str | None]:
        """Map an asebytes key to (h5_path, origin)."""
        grp = self._grp_name

        if key == "cell":
            return f"/particles/{grp}/box/edges", "atoms"
        if key == "pbc":
            return f"/particles/{grp}/box/pbc", "atoms"

        prefix, sep, name = key.partition(".")
        if not sep:
            return None, None

        h5md_name = ASE_TO_H5MD.get(name, name)

        if prefix == "arrays":
            origin = "atoms" if name in ("positions", "numbers") else "arrays"
            return f"/particles/{grp}/{h5md_name}", origin

        if prefix == "calc":
            if h5md_name in KNOWN_PARTICLE_ELEMENTS:
                return f"/particles/{grp}/{h5md_name}", "calc"
            # Check if per-atom by inspecting data shape
            if self._is_per_atom(key, data):
                return f"/particles/{grp}/{h5md_name}", "calc"
            return f"/observables/{grp}/{h5md_name}", "calc"

        if prefix == "info":
            if name == "connectivity":
                return None, None  # handled by _write_connectivity
            return f"/observables/{grp}/{name}", "info"

        return None, None

    def _is_per_atom(self, key: str, data: list[dict[str, Any]]) -> bool:
        """Check if a calc result is per-atom (first dim == n_atoms)."""
        for row in data:
            val = row.get(key)
            if val is None or not isinstance(val, np.ndarray) or val.ndim < 1:
                continue
            n_atoms = None
            pos = row.get("arrays.positions")
            nums = row.get("arrays.numbers")
            if pos is not None:
                n_atoms = len(pos)
            elif nums is not None:
                n_atoms = len(nums)
            if n_atoms is not None and val.shape[0] == n_atoms:
                return True
            break
        return False

    def _write_element(
        self,
        h5_path: str,
        origin: str | None,
        key: str,
        values: list[Any],
        max_atoms: int,
    ) -> None:
        """Create or extend an H5MD element."""
        is_box = h5_path.endswith("/box/edges") or h5_path.endswith("/box/pbc")
        is_pbc = h5_path.endswith("/box/pbc")
        ppath = f"/particles/{self._grp_name}/"
        is_per_atom = (
            h5_path.startswith(ppath) and not is_box
        )

        # Ensure box group exists with attributes
        if is_box:
            box_path = f"/particles/{self._grp_name}/box"
            if box_path not in self._file:
                box_grp = self._file.require_group(box_path)
                box_grp.attrs["dimension"] = 3
                if is_pbc:
                    first_pbc = next(
                        (v for v in values if v is not None),
                        np.array([False, False, False]),
                    )
                    box_grp.attrs["boundary"] = [
                        "periodic" if p else "none" for p in first_pbc
                    ]
                else:
                    box_grp.attrs["boundary"] = ["none", "none", "none"]
            elif is_pbc and "boundary" not in self._file[box_path].attrs:
                first_pbc = next(
                    (v for v in values if v is not None),
                    np.array([False, False, False]),
                )
                self._file[box_path].attrs["boundary"] = [
                    "periodic" if p else "none" for p in first_pbc
                ]

            if is_pbc and not self._pbc_group:
                return

        # Prepare data
        prepared, dtype, fillvalue = self._prepare_column(
            values, is_per_atom, max_atoms
        )
        if prepared is None:
            return

        if h5_path in self._file:
            self._extend_dataset(h5_path, prepared, fillvalue)
        else:
            self._create_dataset(h5_path, prepared, dtype, fillvalue, origin)

    def _prepare_column(
        self,
        values: list[Any],
        is_per_atom: bool,
        max_atoms: int,
    ) -> tuple[Any, Any, Any]:
        """Convert a column of values into HDF5-ready data."""
        ref = next((v for v in values if v is not None), None)
        if ref is None:
            return None, None, None

        # --- String / JSON types ---
        if isinstance(ref, (dict, list, str)):
            serialized = []
            for v in values:
                if v is None:
                    serialized.append("")
                else:
                    serialized.append(json.dumps(_jsonable(v)))
            return serialized, h5py.string_dtype(), ""

        # --- Boolean (PBC) ---
        if isinstance(ref, np.ndarray) and ref.dtype == bool:
            arr = np.array(
                [v if v is not None else np.zeros_like(ref) for v in values],
                dtype=bool,
            )
            return arr, bool, False

        # --- Scalar ---
        if isinstance(ref, (int, float, np.integer, np.floating)):
            arr = np.array(
                [float(v) if v is not None else np.nan for v in values],
                dtype=np.float64,
            )
            return arr, np.float64, np.nan

        # --- ndarray with string dtype ---
        if isinstance(ref, np.ndarray) and ref.dtype.kind in ("S", "U", "O"):
            serialized = []
            for v in values:
                if v is None:
                    serialized.append("")
                else:
                    serialized.append(
                        json.dumps(_jsonable(v))
                    )
            return serialized, h5py.string_dtype(), ""

        # --- Numeric ndarray ---
        if isinstance(ref, np.ndarray):
            if is_per_atom and self._variable_shape:
                return self._pad_per_atom(values, ref, max_atoms)
            processed = []
            for v in values:
                if v is not None:
                    processed.append(np.asarray(v, dtype=np.float64))
                else:
                    processed.append(
                        np.full_like(ref, np.nan, dtype=np.float64)
                    )
            return (
                _concat_varying(processed, np.nan),
                np.float64,
                np.nan,
            )

        return None, None, None

    def _pad_per_atom(
        self,
        values: list[Any],
        ref: np.ndarray,
        max_atoms: int,
    ) -> tuple[np.ndarray, type, float]:
        """Pad per-atom arrays to max_atoms with NaN."""
        padded = []
        for v in values:
            if v is None:
                shape = (max_atoms,) + ref.shape[1:]
                padded.append(np.full(shape, np.nan, dtype=np.float64))
            else:
                v = np.asarray(v, dtype=np.float64)
                if v.shape[0] < max_atoms:
                    pad_shape = (max_atoms - v.shape[0],) + v.shape[1:]
                    v = np.concatenate(
                        [v, np.full(pad_shape, np.nan, dtype=np.float64)]
                    )
                padded.append(v)
        return np.array(padded), np.float64, np.nan

    def _get_chunks(self, shape: tuple[int, ...]) -> tuple[int, ...] | bool:
        """Compute chunk shape for a dataset."""
        if self._chunk_size is None:
            return True
        if isinstance(self._chunk_size, int):
            return tuple(
                [min(self._chunk_size, shape[0])] + list(shape[1:])
            )
        if isinstance(self._chunk_size, (list, tuple)):
            chunks = []
            for i, s in enumerate(shape):
                try:
                    chunks.append(min(self._chunk_size[i], s))
                except IndexError:
                    chunks.append(s)
            return tuple(max(1, c) for c in chunks)
        return True

    def _create_dataset(
        self,
        h5_path: str,
        data: Any,
        dtype: Any,
        fillvalue: Any,
        origin: str | None,
    ) -> None:
        """Create a new H5MD element (group with step/time/value)."""
        grp = self._file.require_group(h5_path)

        if dtype == h5py.string_dtype():
            n = len(data)
            total = self._n_frames + n
            chunks = self._get_chunks((total,))
            ds = grp.create_dataset(
                "value",
                shape=(total,),
                maxshape=(None,),
                fillvalue=fillvalue,
                dtype=dtype,
                compression=self._compression,
                compression_opts=self._compression_opts,
                chunks=chunks,
            )
            ds[self._n_frames :] = data
        else:
            arr = np.asarray(data)
            n = arr.shape[0]
            full_shape = (self._n_frames + n,) + arr.shape[1:]
            maxshape = tuple(None for _ in full_shape)
            chunks = self._get_chunks(full_shape)
            ds = grp.create_dataset(
                "value",
                shape=full_shape,
                maxshape=maxshape,
                fillvalue=fillvalue,
                dtype=dtype,
                compression=self._compression,
                compression_opts=self._compression_opts,
                chunks=chunks,
            )
            ds[self._n_frames :] = arr

        if origin is not None:
            grp.attrs[ORIGIN_ATTR] = origin

        # Linear step/time (matching znh5md default)
        grp.create_dataset("step", data=1)
        time_ds = grp.create_dataset("time", data=1.0)
        time_ds.attrs["unit"] = "fs"

    def _extend_dataset(
        self, h5_path: str, data: Any, fillvalue: Any
    ) -> None:
        """Extend an existing H5MD element."""
        grp = self._file[h5_path]
        ds = grp["value"]

        if ds.dtype == h5py.string_dtype() or isinstance(data, list):
            old_len = ds.shape[0]
            n_new = len(data)
            shift = self._n_frames - old_len
            ds.resize((old_len + n_new + shift,))
            ds[old_len + shift :] = data
        else:
            arr = np.asarray(data)
            old_shape = ds.shape
            n_new = arr.shape[0]
            shift = self._n_frames - old_shape[0]

            if arr.ndim > 1 and old_shape[1:] != arr.shape[1:]:
                # Variable atom dimension — resize
                new_second = max(old_shape[1], arr.shape[1])
                target = (
                    old_shape[0] + n_new + shift,
                    new_second,
                    *old_shape[2:],
                )
                ds.resize(target)
                if arr.shape[1] < new_second:
                    padded = np.full(
                        (n_new, new_second, *old_shape[2:]),
                        fillvalue,
                        dtype=np.float64,
                    )
                    padded[:, : arr.shape[1]] = arr
                    arr = padded
            else:
                target = (old_shape[0] + n_new + shift,) + old_shape[1:]
                ds.resize(target)

            ds[old_shape[0] + shift :] = arr

    @staticmethod
    def _serialize_value(val: Any) -> Any:
        """Serialize a single value for HDF5 storage."""
        if isinstance(val, (dict, list, str)):
            return json.dumps(_jsonable(val))
        return val


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------


def _get_version() -> str:
    """Return the asebytes package version."""
    try:
        from asebytes import __version__

        return __version__
    except Exception:
        return "unknown"


def _strip_nan_padding(arr: np.ndarray) -> np.ndarray:
    """Remove trailing NaN rows from a per-atom array."""
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


def _concat_varying(
    arrays: list[np.ndarray], fillvalue: float
) -> np.ndarray:
    """Concatenate arrays of varying shapes with padding."""
    if not arrays:
        return np.array([])
    maxshape = list(arrays[0].shape)
    for a in arrays[1:]:
        for i, (m, s) in enumerate(zip(maxshape, a.shape)):
            maxshape[i] = max(m, s)
    out = np.full((len(arrays), *maxshape), fillvalue, dtype=np.float64)
    for i, a in enumerate(arrays):
        slices = tuple(slice(0, s) for s in a.shape)
        out[(i,) + slices] = a
    return out
