"""H5MDStore -- ColumnarStore implementation for H5MD 1.1 files.

Translates between flat asebytes column names (``arrays.positions``,
``calc.energy``, ``info.custom``) and the hierarchical H5MD group
layout (``/particles/grp/position/value``,
``/observables/grp/potential_energy/value``).

Every H5MD "element" is a group containing ``step``, ``time``, and
``value`` sub-datasets.  This store creates that structure transparently
so that :class:`~asebytes.columnar.PaddedColumnarBackend` (and its H5MD
subclass) can operate on flat column names.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from ._mapping import (
    ASE_TO_H5MD,
    H5MD_TO_ASE,
    KNOWN_PARTICLE_ELEMENTS,
    ORIGIN_ATTR,
)

# ---------------------------------------------------------------------------
# Unit mapping (ASE flat name -> string to store on the value dataset)
# ---------------------------------------------------------------------------

_ASE_UNITS: dict[str, str] = {
    "positions": "Angstrom",
    "forces": "eV/Angstrom",
    "stress": "eV/Angstrom^3",
    "velocities": "Angstrom/fs",
    "cell": "Angstrom",
    "energy": "eV",
}


class H5MDStore:
    """ColumnarStore backed by h5py with H5MD 1.1 group layout.

    Parameters
    ----------
    path : str | Path | None
        Path to the HDF5 file.  Mutually exclusive with *file_handle*
        and *file_factory*.
    file_handle : h5py.File | None
        Pre-opened HDF5 file.  Caller is responsible for closing.
    file_factory : callable | None
        A callable returning a context-manager that yields an
        ``h5py.File``.  Called immediately at init time.
    group : str
        Particles group name (e.g. ``"atoms"``).
    readonly : bool
        Open file in read-only mode when *path* is given.
    compression : str | None
        Compression filter for value datasets.
    compression_opts : int | None
        Compression level.
    chunk_frames : int
        Chunk size along axis-0 for value datasets.
    rdcc_nbytes : int
        HDF5 chunk cache size in bytes.
    """

    def __init__(
        self,
        *,
        path: str | Path | None = None,
        file_handle: Any = None,
        file_factory: Any = None,
        group: str = "default",
        readonly: bool = False,
        compression: str | None = "gzip",
        compression_opts: int | None = None,
        chunk_frames: int = 64,
        rdcc_nbytes: int = 64 * 1024 * 1024,
    ):
        import h5py

        provided = sum(x is not None for x in (path, file_handle, file_factory))
        if provided != 1:
            raise ValueError(
                "Exactly one of 'path', 'file_handle', or 'file_factory' "
                "must be provided"
            )

        self._factory_cm: Any = None  # context-manager from file_factory

        if file_handle is not None:
            self._file: h5py.File = file_handle
            self._owns_file = False
        elif file_factory is not None:
            self._factory_cm = file_factory()
            self._file = self._factory_cm.__enter__()
            self._owns_file = False
        else:
            mode = "r" if readonly else "a"
            self._file = h5py.File(str(path), mode, rdcc_nbytes=rdcc_nbytes)
            self._owns_file = True

        self._particles_group = group
        self._readonly = readonly
        self._compression = compression
        self._compression_opts = compression_opts
        self._chunk_frames = chunk_frames
        self._ds_cache: dict[str, Any] = {}  # column name -> h5py.Dataset

    # ------------------------------------------------------------------
    # Path translation
    # ------------------------------------------------------------------

    def _column_to_h5(self, key: str) -> tuple[str | None, str | None]:
        """Map a flat column name to ``(h5_path, origin)``.

        Returns ``(None, None)`` for unrecognised keys.
        """
        grp = self._particles_group

        # --- box elements ---
        if key == "cell":
            return f"/particles/{grp}/box/edges", "atoms"
        if key == "pbc":
            return f"/particles/{grp}/box/pbc", "atoms"

        # --- arrays.* ---
        if key.startswith("arrays."):
            ase_name = key[len("arrays."):]
            h5name = ASE_TO_H5MD.get(ase_name, ase_name)
            # Core properties use "atoms" origin (znh5md compat)
            origin = "atoms" if ase_name in ("positions", "numbers") else "arrays"
            return f"/particles/{grp}/{h5name}", origin

        # --- calc.* ---
        if key.startswith("calc."):
            ase_name = key[len("calc."):]
            h5name = ASE_TO_H5MD.get(ase_name, ase_name)
            if h5name in KNOWN_PARTICLE_ELEMENTS:
                return f"/particles/{grp}/{h5name}", "calc"
            else:
                return f"/observables/{grp}/{h5name}", "calc"

        # --- info.* ---
        if key.startswith("info."):
            name = key[len("info."):]
            return f"/observables/{grp}/{name}", "info"

        # --- internal metadata (_n_atoms, etc.) ---
        if key.startswith("_"):
            return f"/asebytes/{grp}/{key}", None

        return None, None

    def _h5_to_column(self, h5_path: str) -> str | None:
        """Translate an H5MD element path back to a flat column name."""
        grp = self._particles_group
        parts = h5_path.strip("/").split("/")

        # /particles/{grp}/box/edges  -> cell
        # /particles/{grp}/box/pbc    -> pbc
        if (
            len(parts) == 4
            and parts[0] == "particles"
            and parts[1] == grp
            and parts[2] == "box"
        ):
            if parts[3] == "edges":
                return "cell"
            if parts[3] == "pbc":
                return "pbc"
            return None

        # /particles/{grp}/{element}
        if len(parts) == 3 and parts[0] == "particles" and parts[1] == grp:
            h5name = parts[2]
            ase_name = H5MD_TO_ASE.get(h5name, h5name)
            # Determine origin from attribute if available, else assume arrays
            origin = self._get_element_origin(h5_path)
            if origin == "calc":
                return f"calc.{ase_name}"
            return f"arrays.{ase_name}"

        # /observables/{grp}/{element}
        if len(parts) == 3 and parts[0] == "observables" and parts[1] == grp:
            h5name = parts[2]
            ase_name = H5MD_TO_ASE.get(h5name, h5name)
            origin = self._get_element_origin(h5_path)
            if origin == "info":
                return f"info.{ase_name}"
            return f"calc.{ase_name}"

        # /asebytes/{grp}/{name} -> internal metadata
        if len(parts) == 3 and parts[0] == "asebytes" and parts[1] == grp:
            return parts[2]

        return None

    def _get_element_origin(self, h5_path: str) -> str | None:
        """Read the ORIGIN_ATTR from an H5MD element group."""
        try:
            element_grp = self._file[h5_path]
            return element_grp.attrs.get(ORIGIN_ATTR)
        except KeyError:
            return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_ds(self, key: str) -> Any:
        """Return cached h5py.Dataset for the ``value`` sub-dataset."""
        ds = self._ds_cache.get(key)
        if ds is None:
            h5_path, _ = self._column_to_h5(key)
            if h5_path is None:
                raise KeyError(f"Unknown column: {key!r}")
            ds = self._file[f"{h5_path}/value"]
            self._ds_cache[key] = ds
        return ds

    def _ensure_box_attrs(self, grp_name: str) -> None:
        """Set dimension and boundary attrs on the box group."""
        import h5py

        box_path = f"/particles/{grp_name}/box"
        box = self._file.require_group(box_path)
        if "dimension" not in box.attrs:
            box.attrs["dimension"] = 3
        if "boundary" not in box.attrs:
            box.attrs["boundary"] = np.array(
                ["periodic", "periodic", "periodic"],
                dtype=h5py.string_dtype(),
            )

    def _ase_name_for_key(self, key: str) -> str | None:
        """Extract the ASE property name from a flat column key."""
        if key in ("cell", "pbc"):
            return key
        for prefix in ("arrays.", "calc.", "info."):
            if key.startswith(prefix):
                return key[len(prefix):]
        return None

    # ------------------------------------------------------------------
    # Internal metadata helpers
    # ------------------------------------------------------------------

    def _is_internal(self, name: str) -> bool:
        """Return True for internal metadata columns (e.g. _n_atoms)."""
        return name.startswith("_")

    def _internal_ds(self, name: str) -> Any:
        """Return (or cache) the h5py.Dataset for an internal column."""
        ds = self._ds_cache.get(name)
        if ds is None:
            meta_path = f"asebytes/{self._particles_group}"
            ds = self._file[f"{meta_path}/{name}"]
            self._ds_cache[name] = ds
        return ds

    # ------------------------------------------------------------------
    # ColumnarStore interface
    # ------------------------------------------------------------------

    def create_array(
        self,
        name: str,
        data: np.ndarray,
        *,
        dtype: Any = None,
        fill_value: Any = None,
    ) -> None:
        import h5py

        arr = np.asarray(data)
        dt = dtype if dtype is not None else arr.dtype
        dt_obj = np.dtype(dt)

        # Internal metadata: simple dataset in asebytes/{grp}/
        if self._is_internal(name):
            meta_path = f"asebytes/{self._particles_group}"
            grp = self._file.require_group(meta_path)
            chunks = (max(1, min(self._chunk_frames, arr.shape[0])),) + arr.shape[1:]
            kw: dict[str, Any] = {}
            if fill_value is not None:
                kw["fillvalue"] = fill_value
            if self._compression and dt_obj.kind in ("f", "i", "u"):
                kw["compression"] = self._compression
                if self._compression_opts is not None:
                    kw["compression_opts"] = self._compression_opts
            grp.create_dataset(
                name,
                data=arr,
                dtype=dt,
                maxshape=(None,) + arr.shape[1:],
                chunks=chunks,
                **kw,
            )
            self._ds_cache.pop(name, None)
            return

        h5_path, origin = self._column_to_h5(name)
        if h5_path is None:
            raise KeyError(f"Cannot map column {name!r} to H5MD path")

        # Create the element group
        element_grp = self._file.require_group(h5_path)

        # Write origin attribute
        if origin is not None:
            element_grp.attrs[ORIGIN_ATTR] = origin

        # -- value dataset --
        maxshape = tuple(None for _ in arr.shape)
        chunks_0 = max(1, min(self._chunk_frames, arr.shape[0]))
        chunks = (chunks_0,) + arr.shape[1:]

        kw2: dict[str, Any] = {}
        if dt_obj.kind in ("U", "S", "O"):
            h5dt = h5py.string_dtype()
            str_data = np.array([str(s) for s in arr.flat], dtype=object).reshape(arr.shape)
            ds = element_grp.create_dataset(
                "value",
                data=str_data,
                dtype=h5dt,
                maxshape=maxshape,
                chunks=chunks,
            )
        else:
            if self._compression and dt_obj.kind in ("f", "i", "u"):
                kw2["compression"] = self._compression
                if self._compression_opts is not None:
                    kw2["compression_opts"] = self._compression_opts
            if fill_value is not None:
                kw2["fillvalue"] = fill_value
            element_grp.create_dataset(
                "value",
                data=arr,
                dtype=dt,
                maxshape=maxshape,
                chunks=chunks,
                **kw2,
            )

        # Write unit attribute on the value dataset
        ase_name = self._ase_name_for_key(name)
        if ase_name is not None and ase_name in _ASE_UNITS:
            element_grp["value"].attrs["unit"] = _ASE_UNITS[ase_name]

        # -- step dataset (linear: scalar int = 1) --
        element_grp.create_dataset("step", data=np.int32(1))

        # -- time dataset (linear: scalar float = 1.0) --
        element_grp.create_dataset("time", data=np.float64(1.0))

        # Box-specific attrs
        if name == "cell":
            self._ensure_box_attrs(self._particles_group)

        # Invalidate cache
        self._ds_cache.pop(name, None)

    def get_array(self, name: str) -> np.ndarray:
        if self._is_internal(name):
            return self._internal_ds(name)[()]
        return self._get_ds(name)[()]

    def get_slice(self, name: str, sel: Any) -> np.ndarray:
        if self._is_internal(name):
            return self._internal_ds(name)[sel]
        return self._get_ds(name)[sel]

    def append_array(self, name: str, data: np.ndarray) -> None:
        if self._is_internal(name):
            ds = self._internal_ds(name)
        else:
            ds = self._get_ds(name)
        old_len = ds.shape[0]
        arr = np.asarray(data)
        new_len = old_len + arr.shape[0]
        ds.resize(new_len, axis=0)
        ds[old_len:] = arr

    def write_slice(self, name: str, sel: Any, data: np.ndarray) -> None:
        if self._is_internal(name):
            self._internal_ds(name)[sel] = data
        else:
            self._get_ds(name)[sel] = data

    def has_array(self, name: str) -> bool:
        if self._is_internal(name):
            meta_path = f"asebytes/{self._particles_group}"
            try:
                return name in self._file[meta_path]
            except KeyError:
                return False
        h5_path, _ = self._column_to_h5(name)
        if h5_path is None:
            return False
        try:
            return "value" in self._file[h5_path]
        except KeyError:
            return False

    def list_arrays(self) -> list[str]:
        """Walk particles/{grp}/, observables/{grp}/, and asebytes/{grp}/ for arrays."""
        import h5py

        columns: list[str] = []
        grp = self._particles_group

        for top in ("particles", "observables"):
            base_path = f"{top}/{grp}"
            if base_path not in self._file:
                continue
            base = self._file[base_path]
            self._walk_elements(base, f"/{base_path}", columns)

        # Internal metadata (e.g. _n_atoms)
        meta_path = f"asebytes/{grp}"
        if meta_path in self._file:
            meta = self._file[meta_path]
            for child_name in meta:
                child = meta[child_name]
                if isinstance(child, h5py.Dataset):
                    columns.append(child_name)
                elif isinstance(child, h5py.Group) and "value" in child:
                    col = self._h5_to_column(f"/{meta_path}/{child_name}")
                    if col is not None:
                        columns.append(col)

        return sorted(columns)

    def _walk_elements(
        self, group: Any, path: str, out: list[str]
    ) -> None:
        """Recursively find H5MD elements (groups with a ``value`` dataset)."""
        import h5py

        for child_name in group:
            child = group[child_name]
            if isinstance(child, h5py.Group):
                if "value" in child:
                    # This is an H5MD element
                    col = self._h5_to_column(f"{path}/{child_name}")
                    if col is not None:
                        out.append(col)
                else:
                    # Recurse (e.g. into box/)
                    self._walk_elements(child, f"{path}/{child_name}", out)

    # -- Attrs -------------------------------------------------------------

    def get_attrs(self) -> dict[str, Any]:
        """Read internal metadata from ``asebytes/{grp}`` group."""
        meta_path = f"asebytes/{self._particles_group}"
        if meta_path not in self._file:
            return {}
        return dict(self._file[meta_path].attrs)

    def set_attrs(self, attrs: dict[str, Any]) -> None:
        """Write internal metadata to ``asebytes/{grp}`` group."""
        meta_path = f"asebytes/{self._particles_group}"
        meta_grp = self._file.require_group(meta_path)
        for k, v in attrs.items():
            meta_grp.attrs[k] = v

    # -- Metadata ----------------------------------------------------------

    def get_shape(self, name: str) -> tuple[int, ...]:
        if self._is_internal(name):
            return self._internal_ds(name).shape
        return self._get_ds(name).shape

    def get_dtype(self, name: str) -> np.dtype:
        if self._is_internal(name):
            return self._internal_ds(name).dtype
        return self._get_ds(name).dtype

    # -- Lifecycle ---------------------------------------------------------

    def close(self) -> None:
        if self._owns_file:
            self._file.close()
        if self._factory_cm is not None:
            try:
                self._factory_cm.__exit__(None, None, None)
            except Exception:
                pass

    def __enter__(self) -> H5MDStore:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # -- Static group listing ----------------------------------------------

    @staticmethod
    def list_groups(path: str) -> list[str]:
        """List particle groups in an H5MD file."""
        import h5py

        p = Path(path)
        if not p.exists():
            return []
        try:
            with h5py.File(str(p), "r") as f:
                if "particles" in f:
                    return list(f["particles"].keys())
                return []
        except Exception:
            return []
