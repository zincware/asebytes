"""Zarr read-write backend for asebytes.

Uses a flat layout: each asebytes column maps directly to a Zarr array.
Supports Blosc compression (LZ4/Zstd) for fast I/O.
Append-only: ``insert_row`` and ``delete_row`` raise
``NotImplementedError``.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import numpy as np
import zarr

from asebytes._columnar import concat_varying, get_version, jsonable, strip_nan_padding
from asebytes._protocols import WritableBackend


class ZarrBackend(WritableBackend):
    """Read-write Zarr backend using zarr-python v3.

    Uses a flat layout where each asebytes column maps directly to a Zarr
    array (e.g. ``arrays.positions/``, ``calc.energy/``).  Supports Blosc
    compression for fast I/O.  Append-only: ``insert_row`` and
    ``delete_row`` raise ``NotImplementedError``.
    """

    def __init__(
        self,
        file: str | Path | None = None,
        *,
        store: Any | None = None,
        readonly: bool = False,
        compressor: str = "lz4",
        clevel: int = 5,
        shuffle: bool = True,
        variable_shape: bool = True,
        chunk_frames: int = 64,
    ):
        if store is not None:
            mode = "r" if readonly else "a"
            self._root = zarr.open_group(store=store, mode=mode)
            self._owns_store = False
        elif file is not None:
            mode = "r" if readonly else "a"
            self._root = zarr.open_group(store=str(file), mode=mode)
            self._owns_store = True
        else:
            raise ValueError("Provide either file or store")

        self._readonly = readonly
        self._compressor = compressor
        self._clevel = clevel
        self._shuffle = shuffle
        self._variable_shape = variable_shape
        self._chunk_frames = chunk_frames

        self._n_frames = 0
        self._max_atoms = 0
        self._col_cache: dict[str, zarr.Array] = {}
        self._columns: list[str] = []
        self._discover()

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _discover(self) -> None:
        """Populate caches from existing zarr store."""
        self._col_cache = {}
        attrs = dict(self._root.attrs)
        self._n_frames = attrs.get("n_frames", 0)
        self._max_atoms = attrs.get("max_atoms", 0)
        self._columns = list(attrs.get("columns", []))

        for col_name in self._columns:
            try:
                self._col_cache[col_name] = self._root[col_name]
            except (KeyError, FileNotFoundError):
                pass

    def _get_compressor(self):
        """Build Blosc codec for array creation."""
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

    def _get_chunks(self, shape: tuple[int, ...]) -> tuple[int, ...]:
        """Compute chunk shape for a dataset."""
        chunks = [min(self._chunk_frames, shape[0])]
        for s in shape[1:]:
            chunks.append(s)
        return tuple(max(1, c) for c in chunks)

    # ------------------------------------------------------------------
    # ReadableBackend
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return self._n_frames

    def columns(self, index: int = 0) -> list[str]:
        if self._columns:
            return list(self._columns)
        if self._n_frames > 0:
            return list(self.read_row(index).keys())
        return []

    def read_row(self, index: int, keys: list[str] | None = None) -> dict[str, Any]:
        index = self._check_index(index)
        result: dict[str, Any] = {}
        for col_name, arr in self._col_cache.items():
            if keys is not None and col_name not in keys:
                continue
            # Array may be shorter than n_frames if the column was absent
            # in later batches
            if index >= arr.shape[0]:
                continue
            val = arr[index]
            val = self._postprocess(val, col_name)
            if val is not None:
                result[col_name] = val
        return result

    def read_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Bulk columnar read — each array is accessed once."""
        if not indices:
            return []

        n = len(indices)
        checked = [self._check_index(i) for i in indices]

        # Sort + deduplicate for efficient chunk access
        order = np.argsort(checked)
        sorted_idx = np.array(checked)[order]
        unique_sorted, inverse = np.unique(sorted_idx, return_inverse=True)

        n_unique = len(unique_sorted)
        if n_unique == 1:
            zarr_sel = [int(unique_sorted[0])]
        elif np.all(np.diff(unique_sorted) == 1):
            zarr_sel = slice(int(unique_sorted[0]), int(unique_sorted[-1]) + 1)
        else:
            zarr_sel = unique_sorted.tolist()

        unique_rows: list[dict[str, Any]] = [{} for _ in range(n_unique)]

        for col_name, arr in self._col_cache.items():
            if keys is not None and col_name not in keys:
                continue
            arr_len = arr.shape[0]
            # Filter selection to indices within this array's bounds
            if isinstance(zarr_sel, slice):
                eff_stop = min(zarr_sel.stop, arr_len)
                if zarr_sel.start >= arr_len:
                    continue
                eff_sel = slice(zarr_sel.start, eff_stop)
                eff_n = eff_stop - zarr_sel.start
            else:
                eff_indices = [idx for idx in zarr_sel if idx < arr_len]
                if not eff_indices:
                    continue
                eff_sel = eff_indices
                eff_n = len(eff_indices)
            bulk = arr[eff_sel]
            for j in range(eff_n):
                val = self._postprocess(bulk[j], col_name)
                if val is not None:
                    unique_rows[j][col_name] = val

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
        """Direct array access — the flat layout's main perf advantage."""
        if key not in self._col_cache:
            return super().read_column(key, indices)

        arr = self._col_cache[key]
        arr_len = arr.shape[0]

        if indices is None:
            raw = arr[:]
            result = [self._postprocess(raw[i], key) for i in range(len(raw))]
            # Pad with None if array is shorter than n_frames
            if arr_len < self._n_frames:
                result.extend([None] * (self._n_frames - arr_len))
            return result

        order = np.argsort(indices)
        sorted_idx = [indices[j] for j in order]
        # Filter to valid indices
        valid_idx = [idx for idx in sorted_idx if idx < arr_len]
        result: list[Any] = [None] * len(indices)
        if valid_idx:
            raw = arr[valid_idx]
            vi = 0
            for j in range(len(indices)):
                idx = sorted_idx[j]
                if idx < arr_len:
                    result[order[j]] = self._postprocess(raw[vi], key)
                    vi += 1
        return result

    # ------------------------------------------------------------------
    # WritableBackend (append-only)
    # ------------------------------------------------------------------

    def append_rows(self, data: list[dict[str, Any]]) -> None:
        if not data:
            return

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
            values = [row.get(key) for row in data]
            is_per_atom = self._is_per_atom(key, data)
            self._write_column(key, values, is_per_atom, max_atoms)

        # Extend existing columns not in this batch so all arrays stay aligned
        new_total = self._n_frames + n_new
        touched = set(all_keys)
        for col_name, arr in list(self._col_cache.items()):
            if col_name not in touched and arr.shape[0] < new_total:
                target = (new_total,) + arr.shape[1:]
                arr.resize(target)

        self._max_atoms = max_atoms
        self._n_frames += n_new
        self._update_attrs(all_keys)
        self._discover()

    def write_row(self, index: int, data: dict[str, Any]) -> None:
        index = self._check_index(index)
        for key, val in data.items():
            if key not in self._col_cache:
                continue
            arr = self._col_cache[key]
            val = self._serialize_value(val)
            if isinstance(val, np.ndarray) and self._variable_shape:
                if arr.ndim > 1 and val.ndim >= 1 and val.shape[0] < arr.shape[1]:
                    padded = np.full(arr.shape[1:], np.nan, dtype=np.float64)
                    slices = tuple(slice(0, s) for s in val.shape)
                    padded[slices] = val
                    val = padded
            arr[index] = val

    def insert_row(self, index: int, data: dict[str, Any]) -> None:
        raise NotImplementedError("Zarr backend does not support insert")

    def delete_row(self, index: int) -> None:
        raise NotImplementedError("Zarr backend does not support delete")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        pass  # zarr v3 auto-flushes; no explicit close needed

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

    def _postprocess(self, val: Any, col_name: str) -> Any:
        """Strip NaN padding and cast types after reading."""
        if isinstance(val, (bytes, np.bytes_)):
            val = val.decode() if isinstance(val, bytes) else str(val)

        # zarr v3 returns 0-d StringDType arrays for single string elements
        if isinstance(val, np.ndarray) and val.ndim == 0 and val.dtype.kind in ("U", "T"):
            val = str(val)

        if isinstance(val, str):
            if val == "":
                return None
            try:
                return json.loads(val)
            except (json.JSONDecodeError, ValueError):
                return val

        # Handle numpy scalars (e.g. np.float64 from bulk array indexing)
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
                val = strip_nan_padding(val)
                if val.size == 0:
                    return None

            # numbers should be int
            if col_name == "arrays.numbers" and val.dtype.kind == "f":
                val = val.astype(int)

            # Scalar
            if val.ndim == 0:
                v = val.item()
                if isinstance(v, float) and np.isnan(v):
                    return None
                return v

        return val

    # ------------------------------------------------------------------
    # Internal: write helpers
    # ------------------------------------------------------------------

    def _is_per_atom(self, key: str, data: list[dict[str, Any]]) -> bool:
        """Check if a column is per-atom (first dim == n_atoms)."""
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

    def _write_column(
        self,
        key: str,
        values: list[Any],
        is_per_atom: bool,
        max_atoms: int,
    ) -> None:
        """Create or extend a zarr array for a column."""
        prepared, dtype, fill_value = self._prepare_column(
            values, is_per_atom, max_atoms
        )
        if prepared is None:
            return

        if key in self._col_cache:
            self._extend_array(key, prepared, fill_value)
        else:
            self._create_array(key, prepared, dtype, fill_value)

    def _prepare_column(
        self,
        values: list[Any],
        is_per_atom: bool,
        max_atoms: int,
    ) -> tuple[Any, Any, Any]:
        """Convert a column of values into zarr-ready data."""
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
                    serialized.append(json.dumps(jsonable(v)))
            return serialized, str, ""

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
                        json.dumps(jsonable(v))
                    )
            return serialized, str, ""

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
                concat_varying(processed, np.nan),
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

    def _create_array(
        self,
        key: str,
        data: Any,
        dtype: Any,
        fill_value: Any,
    ) -> None:
        """Create a new zarr array and write initial data."""
        if dtype == str:
            n = len(data)
            total = self._n_frames + n
            chunks = (max(1, min(self._chunk_frames, total)),)
            arr = self._root.create_array(
                name=key,
                shape=(total,),
                dtype=str,
                fill_value=fill_value or "",
                chunks=chunks,
            )
            for i, s in enumerate(data):
                arr[self._n_frames + i] = s
        else:
            arr_data = np.asarray(data)
            n = arr_data.shape[0]
            full_shape = (self._n_frames + n,) + arr_data.shape[1:]
            chunks = self._get_chunks(full_shape)
            kwargs: dict[str, Any] = {
                "name": key,
                "shape": full_shape,
                "dtype": dtype,
                "fill_value": fill_value if fill_value is not None else 0,
                "chunks": chunks,
            }
            # Use Blosc compression for numeric arrays
            if dtype not in (bool,):
                kwargs["compressors"] = self._get_compressor()
            arr = self._root.create_array(**kwargs)
            arr[self._n_frames :] = arr_data

    def _extend_array(
        self,
        key: str,
        data: Any,
        fill_value: Any,
    ) -> None:
        """Extend an existing zarr array with new data."""
        arr = self._col_cache[key]
        old_shape = arr.shape

        if isinstance(data, list) and all(isinstance(d, str) for d in data):
            # String array
            n_new = len(data)
            shift = self._n_frames - old_shape[0]
            new_len = old_shape[0] + n_new + shift
            arr.resize((new_len,))
            for i, s in enumerate(data):
                arr[self._n_frames + i] = s
        else:
            arr_data = np.asarray(data)
            n_new = arr_data.shape[0]
            shift = self._n_frames - old_shape[0]

            if arr_data.ndim > 1 and old_shape[1:] != arr_data.shape[1:]:
                # Variable atom dimension — resize
                new_second = max(old_shape[1], arr_data.shape[1])
                target = (
                    old_shape[0] + n_new + shift,
                    new_second,
                    *old_shape[2:],
                )
                arr.resize(target)
                if arr_data.shape[1] < new_second:
                    padded = np.full(
                        (n_new, new_second, *old_shape[2:]),
                        fill_value,
                        dtype=np.float64,
                    )
                    padded[:, : arr_data.shape[1]] = arr_data
                    arr_data = padded
            else:
                target = (old_shape[0] + n_new + shift,) + old_shape[1:]
                arr.resize(target)

            arr[old_shape[0] + shift :] = arr_data

    def _update_attrs(self, new_keys: list[str] | None = None) -> None:
        """Update root group attributes."""
        if new_keys:
            existing = set(self._columns)
            for key in new_keys:
                if key != "constraints" and key not in existing:
                    self._columns.append(key)
        self._root.attrs["n_frames"] = self._n_frames
        self._root.attrs["max_atoms"] = self._max_atoms
        self._root.attrs["columns"] = self._columns
        self._root.attrs["asebytes_version"] = get_version()

    @staticmethod
    def _serialize_value(val: Any) -> Any:
        """Serialize a single value for zarr storage."""
        if isinstance(val, (dict, list, str)):
            return json.dumps(jsonable(val))
        return val
