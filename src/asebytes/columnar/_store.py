"""Thin storage abstraction over HDF5 and Zarr array I/O.

The :class:`ColumnarStore` protocol defines the minimal surface area
needed by :class:`~asebytes.columnar.ColumnarBackend`.  Two concrete
implementations are provided: :class:`HDF5Store` (h5py) and
:class:`ZarrStore` (zarr-python v3).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import numpy as np


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class ColumnarStore(Protocol):
    """Thin abstraction over HDF5 / Zarr array storage."""

    def list_arrays(self) -> list[str]:
        """Return names of all arrays in the group."""
        ...

    def has_array(self, name: str) -> bool: ...

    def get_array(self, name: str) -> np.ndarray:
        """Read entire array into memory."""
        ...

    def get_slice(self, name: str, sel: Any) -> np.ndarray:
        """Read a slice/fancy-index from an array."""
        ...

    def create_array(self, name: str, data: np.ndarray, **kwargs: Any) -> None:
        """Create a new array with initial data."""
        ...

    def append_array(self, name: str, data: np.ndarray) -> None:
        """Append data to an existing array (resize + write)."""
        ...

    def write_slice(self, name: str, sel: Any, data: np.ndarray) -> None:
        """Overwrite a slice of an existing array."""
        ...

    def get_attrs(self) -> dict[str, Any]: ...
    def set_attrs(self, attrs: dict[str, Any]) -> None: ...

    def get_shape(self, name: str) -> tuple[int, ...]: ...
    def get_dtype(self, name: str) -> np.dtype: ...

    def close(self) -> None: ...

    @staticmethod
    def list_groups(path: str) -> list[str]: ...


# ---------------------------------------------------------------------------
# HDF5 implementation
# ---------------------------------------------------------------------------


class HDF5Store:
    """ColumnarStore backed by h5py."""

    def __init__(
        self,
        path: str | Path,
        group: str,
        *,
        readonly: bool = False,
        compression: str | None = "gzip",
        compression_opts: int | None = None,
        chunk_frames: int = 64,
        rdcc_nbytes: int = 64 * 1024 * 1024,
    ):
        import h5py

        mode = "r" if readonly else "a"
        self._file = h5py.File(str(path), mode, rdcc_nbytes=rdcc_nbytes)
        self._group = self._file.require_group(group) if not readonly else self._file.get(group, self._file)
        self._compression = compression
        self._compression_opts = compression_opts
        self._chunk_frames = chunk_frames
        self._owns_file = True
        self._ds_cache: dict[str, Any] = {}  # name -> h5py.Dataset

    # -- Array operations --------------------------------------------------

    def _get_ds(self, name: str) -> Any:
        """Get a cached h5py.Dataset reference."""
        ds = self._ds_cache.get(name)
        if ds is None:
            ds = self._group[name]
            self._ds_cache[name] = ds
        return ds

    def list_arrays(self) -> list[str]:
        import h5py
        return [k for k in self._group if isinstance(self._group[k], h5py.Dataset)]

    def has_array(self, name: str) -> bool:
        import h5py
        return name in self._group and isinstance(self._group[name], h5py.Dataset)

    def get_array(self, name: str) -> np.ndarray:
        return self._get_ds(name)[()]

    def get_slice(self, name: str, sel: Any) -> np.ndarray:
        return self._get_ds(name)[sel]

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

        # HDF5 requires special string dtype
        if dt_obj.kind in ("U", "S", "O"):
            h5dt = h5py.string_dtype()
            # Convert numpy unicode array to list of Python strings
            str_data = [str(x) for x in arr.flat]
            maxshape = tuple(None for _ in arr.shape)
            chunks_0 = max(1, min(self._chunk_frames, arr.shape[0]))
            chunks = (chunks_0,) + arr.shape[1:]
            kw: dict[str, Any] = {}
            if fill_value is not None:
                kw["fillvalue"] = str(fill_value)
            ds = self._group.create_dataset(
                name, shape=arr.shape, dtype=h5dt, maxshape=maxshape,
                chunks=chunks, **kw
            )
            for i, s in enumerate(str_data):
                ds[i] = s
            self._ds_cache.pop(name, None)
            return

        maxshape = tuple(None for _ in arr.shape)
        chunks_0 = max(1, min(self._chunk_frames, arr.shape[0]))
        chunks = (chunks_0,) + arr.shape[1:]
        kw = {}
        if self._compression and dt_obj.kind in ("f", "i", "u"):
            kw["compression"] = self._compression
            if self._compression_opts is not None:
                kw["compression_opts"] = self._compression_opts
        if fill_value is not None:
            kw["fillvalue"] = fill_value
        self._group.create_dataset(
            name, data=arr, dtype=dt, maxshape=maxshape, chunks=chunks, **kw
        )
        self._ds_cache.pop(name, None)  # invalidate cache

    def append_array(self, name: str, data: np.ndarray) -> None:
        ds = self._get_ds(name)
        old_len = ds.shape[0]
        arr = np.asarray(data)
        new_len = old_len + arr.shape[0]
        ds.resize(new_len, axis=0)
        # h5py string datasets need element-by-element writes
        if ds.dtype.kind in ("O",) or (hasattr(ds.dtype, "metadata") and ds.dtype.metadata):
            for i in range(arr.shape[0]):
                ds[old_len + i] = str(arr.flat[i]) if arr.ndim <= 1 else arr[i]
        else:
            ds[old_len:] = arr

    def write_slice(self, name: str, sel: Any, data: Any) -> None:
        self._group[name][sel] = data

    # -- Attrs -------------------------------------------------------------

    def get_attrs(self) -> dict[str, Any]:
        return dict(self._group.attrs)

    def set_attrs(self, attrs: dict[str, Any]) -> None:
        for k, v in attrs.items():
            self._group.attrs[k] = v

    # -- Metadata ----------------------------------------------------------

    def get_shape(self, name: str) -> tuple[int, ...]:
        return self._get_ds(name).shape

    def get_dtype(self, name: str) -> np.dtype:
        return self._get_ds(name).dtype

    # -- Lifecycle ---------------------------------------------------------

    def close(self) -> None:
        if self._owns_file:
            self._file.close()

    @staticmethod
    def list_groups(path: str) -> list[str]:
        """List top-level groups in an HDF5 file."""
        import h5py

        p = Path(path)
        if not p.exists():
            return []
        try:
            with h5py.File(str(p), "r") as f:
                return list(f.keys())
        except Exception:
            return []

    def __enter__(self):
        return self

    def __exit__(self, *exc: Any):
        self.close()


# ---------------------------------------------------------------------------
# Zarr implementation
# ---------------------------------------------------------------------------


class ZarrStore:
    """ColumnarStore backed by zarr-python v3."""

    def __init__(
        self,
        path: str | Path,
        group: str,
        *,
        readonly: bool = False,
        compressor: str = "lz4",
        clevel: int = 5,
        shuffle: bool = True,
        chunk_frames: int = 64,
    ):
        import zarr

        mode = "r" if readonly else "a"
        group_path = os.path.join(str(path), group)
        self._root = zarr.open_group(store=group_path, mode=mode)
        self._compressor = compressor
        self._clevel = clevel
        self._shuffle = shuffle
        self._chunk_frames = chunk_frames
        self._arr_cache: dict[str, Any] = {}  # name -> zarr.Array

    # -- Array operations --------------------------------------------------

    def _get_arr(self, name: str) -> Any:
        """Get a cached zarr.Array reference."""
        arr = self._arr_cache.get(name)
        if arr is None:
            arr = self._root[name]
            self._arr_cache[name] = arr
        return arr

    def list_arrays(self) -> list[str]:
        import zarr
        return [k for k in self._root if isinstance(self._root[k], zarr.Array)]

    def has_array(self, name: str) -> bool:
        import zarr
        try:
            return isinstance(self._root[name], zarr.Array)
        except (KeyError, FileNotFoundError):
            return False

    def get_array(self, name: str) -> np.ndarray:
        return np.asarray(self._get_arr(name)[:])

    def get_slice(self, name: str, sel: Any) -> np.ndarray:
        return np.asarray(self._get_arr(name)[sel])

    def create_array(
        self,
        name: str,
        data: np.ndarray,
        *,
        dtype: Any = None,
        fill_value: Any = None,
    ) -> None:
        import zarr

        arr = np.asarray(data)
        dt = dtype if dtype is not None else arr.dtype
        chunks_0 = max(1, min(self._chunk_frames, arr.shape[0]))
        chunks = (chunks_0,) + arr.shape[1:]
        kw: dict[str, Any] = {
            "name": name,
            "shape": arr.shape,
            "dtype": dt,
            "chunks": chunks,
        }
        if fill_value is not None:
            kw["fill_value"] = fill_value
        dt_obj = np.dtype(dt)
        if dt_obj.kind in ("f", "i", "u"):
            kw["compressors"] = self._get_compressor()
        za = self._root.create_array(**kw)
        za[:] = arr
        self._arr_cache.pop(name, None)  # invalidate cache

    def append_array(self, name: str, data: np.ndarray) -> None:
        za = self._get_arr(name)
        old_len = za.shape[0]
        new_len = old_len + data.shape[0]
        za.resize((new_len,) + za.shape[1:])
        za[old_len:] = data

    def write_slice(self, name: str, sel: Any, data: Any) -> None:
        self._get_arr(name)[sel] = data

    # -- Attrs -------------------------------------------------------------

    def get_attrs(self) -> dict[str, Any]:
        return dict(self._root.attrs)

    def set_attrs(self, attrs: dict[str, Any]) -> None:
        for k, v in attrs.items():
            self._root.attrs[k] = v

    # -- Metadata ----------------------------------------------------------

    def get_shape(self, name: str) -> tuple[int, ...]:
        return tuple(self._get_arr(name).shape)

    def get_dtype(self, name: str) -> np.dtype:
        return self._get_arr(name).dtype

    # -- Lifecycle ---------------------------------------------------------

    def close(self) -> None:
        pass  # zarr v3 auto-flushes

    @staticmethod
    def list_groups(path: str) -> list[str]:
        """List subdirectories that look like Zarr groups."""
        base = Path(path)
        if not base.exists():
            return []
        groups = []
        for entry in base.iterdir():
            if entry.is_dir():
                if (entry / ".zgroup").exists() or (entry / "zarr.json").exists():
                    groups.append(entry.name)
        return sorted(groups)

    def __enter__(self):
        return self

    def __exit__(self, *exc: Any):
        self.close()

    # -- Internal ----------------------------------------------------------

    def _get_compressor(self):
        import zarr

        shuffle_val = (
            zarr.codecs.BloscShuffle.shuffle
            if self._shuffle
            else zarr.codecs.BloscShuffle.noshuffle
        )
        return zarr.codecs.BloscCodec(
            cname=self._compressor,
            clevel=self._clevel,
            shuffle=shuffle_val,
        )
