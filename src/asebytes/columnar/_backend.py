"""Unified columnar backend with offset+flat ragged storage.

Replaces both H5MD and Zarr backends with a single implementation
that delegates storage I/O to a :class:`~asebytes.columnar._store.ColumnarStore`.
Per-atom columns use offset+flat layout (2-24x faster than padding
for random access on ragged data).
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import numpy as np

from asebytes._backends import ReadWriteBackend
from asebytes._columnar import concat_varying, get_fill_value, get_version, jsonable
from asebytes.columnar._store import ColumnarStore, HDF5Store, ZarrStore

DEFAULT_GROUP = "default"

# Columns that are never per-atom regardless of shape coincidence.
_NEVER_PER_ATOM = frozenset({"cell", "pbc"})


class ColumnarBackend(ReadWriteBackend[str, Any]):
    """Unified columnar backend with offset+flat ragged storage.

    Per-atom columns are stored as flat contiguous arrays indexed by
    shared ``_offsets`` / ``_lengths`` arrays.  Scalar and fixed-shape
    columns are stored as ``(n_frames, ...)`` arrays.

    Storage I/O is delegated to a :class:`ColumnarStore` — either
    :class:`HDF5Store` (h5py) or :class:`ZarrStore` (zarr-python v3).
    """

    _returns_mutable: bool = True

    def __init__(
        self,
        file: str | Path | None = None,
        *,
        group: str | None = None,
        readonly: bool = False,
        store: ColumnarStore | None = None,
        # HDF5-specific
        compression: str | None = "gzip",
        compression_opts: int | None = None,
        # Zarr-specific
        compressor: str = "lz4",
        clevel: int = 5,
        shuffle: bool = True,
        # Shared
        chunk_frames: int = 64,
    ):
        self.group = group if group is not None else DEFAULT_GROUP
        self._readonly = readonly

        if store is not None:
            self._store = store
            self._base_path: str | None = None
        elif file is not None:
            self._base_path = str(file)
            ext = Path(file).suffix.lower()
            if ext in (".h5", ".hdf5"):
                self._store = HDF5Store(
                    file,
                    self.group,
                    readonly=readonly,
                    compression=compression,
                    compression_opts=compression_opts,
                    chunk_frames=chunk_frames,
                )
            elif ext == ".zarr":
                self._store = ZarrStore(
                    file,
                    self.group,
                    readonly=readonly,
                    compressor=compressor,
                    clevel=clevel,
                    shuffle=shuffle,
                    chunk_frames=chunk_frames,
                )
            else:
                raise ValueError(f"Unsupported extension: {ext}")
        else:
            raise ValueError("Provide either file or store")

        # Cached metadata (rebuilt by _discover)
        self._n_frames: int = 0
        self._columns: list[str] = []
        self._per_atom_cols: set[str] = set()
        self._discover()

    # ------------------------------------------------------------------
    # Discovery / metadata cache
    # ------------------------------------------------------------------

    def _discover(self) -> None:
        """Populate caches from existing store metadata."""
        attrs = self._store.get_attrs()
        self._n_frames = attrs.get("n_frames", 0)
        self._columns = list(attrs.get("columns", []))
        self._per_atom_cols = set(attrs.get("per_atom_columns", []))

        # Cache structural metadata to avoid per-read store lookups
        self._known_arrays: set[str] = set()
        self._array_shapes: dict[str, tuple[int, ...]] = {}
        for name in self._store.list_arrays():
            self._known_arrays.add(name)
            self._array_shapes[name] = self._store.get_shape(name)

        # Cache offsets/lengths in memory (small: n_frames * 12 bytes)
        if "_offsets" in self._known_arrays and self._n_frames > 0:
            self._offsets_cache: np.ndarray | None = self._store.get_array("_offsets")
            self._lengths_cache: np.ndarray | None = self._store.get_array("_lengths")
        else:
            self._offsets_cache = None
            self._lengths_cache = None

    def _update_attrs(
        self,
        new_keys: list[str] | None = None,
        per_atom_keys: set[str] | None = None,
    ) -> None:
        """Write metadata attrs to the store."""
        if new_keys:
            existing = set(self._columns)
            for key in new_keys:
                if key not in existing and not key.startswith("_"):
                    self._columns.append(key)
        if per_atom_keys:
            self._per_atom_cols.update(per_atom_keys)
        self._store.set_attrs({
            "n_frames": self._n_frames,
            "columns": self._columns,
            "per_atom_columns": sorted(self._per_atom_cols),
            "asebytes_version": get_version(),
        })

    @staticmethod
    def list_groups(path: str, **kwargs: Any) -> list[str]:
        ext = Path(path).suffix.lower()
        if ext in (".h5", ".hdf5"):
            return HDF5Store.list_groups(path)
        elif ext == ".zarr":
            return ZarrStore.list_groups(path)
        return []

    # ------------------------------------------------------------------
    # ReadBackend core
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return self._n_frames

    def _check_index(self, index: int) -> int:
        if index < 0:
            index += self._n_frames
        if index < 0 or index >= self._n_frames:
            raise IndexError(
                f"Index {index} out of range for {self._n_frames} frames"
            )
        return index

    # ------------------------------------------------------------------
    # get / get_many / iter_rows / get_column
    # ------------------------------------------------------------------

    def get(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any] | None:
        index = self._check_index(index)
        result: dict[str, Any] = {}

        # Read offset/length from cache for per-atom slicing
        offset: int | None = None
        length: int | None = None
        if self._offsets_cache is not None and self._per_atom_cols:
            if keys is None or (self._per_atom_cols & set(keys)):
                offset = int(self._offsets_cache[index])
                length = int(self._lengths_cache[index])

        for col_name in self._columns:
            if keys is not None and col_name not in keys:
                continue
            if col_name not in self._known_arrays:
                continue

            if col_name in self._per_atom_cols:
                if offset is not None and length is not None:
                    if length == 0:
                        continue
                    val = self._store.get_slice(
                        col_name, slice(offset, offset + length)
                    )
                else:
                    continue
            else:
                arr_len = self._array_shapes[col_name][0]
                if index >= arr_len:
                    continue
                val = self._store.get_slice(col_name, index)

            val = self._postprocess(val, col_name, is_per_atom=(col_name in self._per_atom_cols))
            if val is not None:
                result[col_name] = val

        return result if result else None

    def get_many(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any] | None]:
        if not indices:
            return []

        n = len(indices)
        checked = [self._check_index(i) for i in indices]

        # Sort + deduplicate for efficient chunk access
        order = np.argsort(checked)
        sorted_idx = np.array(checked)[order]
        unique_sorted, inverse = np.unique(sorted_idx, return_inverse=True)
        n_unique = len(unique_sorted)

        # Build selection for scalar columns
        if n_unique == 1:
            scalar_sel: Any = [int(unique_sorted[0])]
        elif np.all(np.diff(unique_sorted) == 1):
            scalar_sel = slice(int(unique_sorted[0]), int(unique_sorted[-1]) + 1)
        else:
            scalar_sel = unique_sorted.tolist()

        # Read offsets/lengths from cache for per-atom columns
        offsets_map: list[int | None] = [None] * n_unique
        lengths_map: list[int | None] = [None] * n_unique
        if self._offsets_cache is not None and self._per_atom_cols:
            need = keys is None or bool(self._per_atom_cols & set(keys))
            if need:
                for j in range(n_unique):
                    idx = int(unique_sorted[j])
                    offsets_map[j] = int(self._offsets_cache[idx])
                    lengths_map[j] = int(self._lengths_cache[idx])

        unique_rows: list[dict[str, Any]] = [{} for _ in range(n_unique)]

        for col_name in self._columns:
            if keys is not None and col_name not in keys:
                continue
            if col_name not in self._known_arrays:
                continue

            if col_name in self._per_atom_cols:
                # Per-atom: read ONE contiguous range, split in numpy
                # Find the min/max extent across all requested frames
                valid_js = [
                    j for j in range(n_unique)
                    if offsets_map[j] is not None and lengths_map[j] > 0
                ]
                if not valid_js:
                    continue
                min_off = offsets_map[valid_js[0]]
                max_end = offsets_map[valid_js[-1]] + lengths_map[valid_js[-1]]
                # Single I/O: read the entire range
                flat_chunk = self._store.get_slice(
                    col_name, slice(min_off, max_end)
                )
                for j in valid_js:
                    off = offsets_map[j]
                    ln = lengths_map[j]
                    local_start = off - min_off
                    val = flat_chunk[local_start : local_start + ln]
                    val = self._postprocess(val, col_name, is_per_atom=True)
                    if val is not None:
                        unique_rows[j][col_name] = val
            else:
                # Scalar: bulk read
                arr_len = self._array_shapes.get(col_name, (0,))[0]
                if isinstance(scalar_sel, slice):
                    eff_stop = min(scalar_sel.stop, arr_len)
                    if scalar_sel.start >= arr_len:
                        continue
                    eff_sel = slice(scalar_sel.start, eff_stop)
                    eff_n = eff_stop - scalar_sel.start
                else:
                    eff_indices = [idx for idx in scalar_sel if idx < arr_len]
                    if not eff_indices:
                        continue
                    eff_sel = eff_indices
                    eff_n = len(eff_indices)
                bulk = self._store.get_slice(col_name, eff_sel)
                for j in range(eff_n):
                    val = self._postprocess(bulk[j], col_name, is_per_atom=False)
                    if val is not None:
                        unique_rows[j][col_name] = val

        # Map back to original order
        result: list[dict[str, Any] | None] = [None] * n
        for j in range(n):
            src = unique_rows[inverse[j]]
            row = dict(src) if n_unique < n else src
            result[order[j]] = row if row else None

        return result

    def iter_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> Iterator[dict[str, Any] | None]:
        yield from self.get_many(indices, keys)

    def get_column(self, key: str, indices: list[int] | None = None) -> list[Any]:
        if key.startswith("_") or key not in self._known_arrays:
            return super().get_column(key, indices)

        is_per_atom = key in self._per_atom_cols

        if is_per_atom:
            if self._offsets_cache is None:
                return super().get_column(key, indices)

            if indices is None:
                # All frames: read entire flat array once, split in numpy
                flat = self._store.get_array(key)
                result = []
                for i in range(self._n_frames):
                    off = int(self._offsets_cache[i])
                    ln = int(self._lengths_cache[i])
                    if ln == 0:
                        result.append(None)
                    else:
                        val = flat[off : off + ln]
                        val = self._postprocess(val, key, is_per_atom=True)
                        result.append(val)
                return result
            else:
                # Specific indices: read one contiguous range covering them
                checked = [self._check_index(i) for i in indices]
                offsets = self._offsets_cache[checked]
                lengths = self._lengths_cache[checked]
                valid_mask = lengths > 0
                if not np.any(valid_mask):
                    return [None] * len(indices)
                min_off = int(offsets[valid_mask].min())
                max_end = int((offsets[valid_mask] + lengths[valid_mask]).max())
                flat_chunk = self._store.get_slice(key, slice(min_off, max_end))
                result = []
                for j, idx in enumerate(checked):
                    off = int(offsets[j])
                    ln = int(lengths[j])
                    if ln == 0:
                        result.append(None)
                    else:
                        local = off - min_off
                        val = flat_chunk[local : local + ln]
                        val = self._postprocess(val, key, is_per_atom=True)
                        result.append(val)
                return result
        else:
            # Scalar column: direct array access
            arr_len = self._array_shapes.get(key, (0,))[0]
            if indices is None:
                raw = self._store.get_array(key)
                result = []
                for i in range(len(raw)):
                    result.append(self._postprocess(raw[i], key, is_per_atom=False))
                if arr_len < self._n_frames:
                    result.extend([None] * (self._n_frames - arr_len))
                return result
            else:
                checked = [self._check_index(i) for i in indices]
                result = [None] * len(indices)
                valid = [(j, idx) for j, idx in enumerate(checked) if idx < arr_len]
                if valid:
                    valid_indices = [idx for _, idx in valid]
                    raw = self._store.get_slice(key, valid_indices)
                    for k, (j, _) in enumerate(valid):
                        result[j] = self._postprocess(raw[k], key, is_per_atom=False)
                return result

    # ------------------------------------------------------------------
    # schema / keys
    # ------------------------------------------------------------------

    def schema(self, index: int = 0) -> dict:
        from asebytes._schema import SchemaEntry

        result = {}
        for col_name in self._columns:
            if col_name not in self._known_arrays:
                continue
            dtype = self._store.get_dtype(col_name)
            shape = self._array_shapes[col_name]
            if dtype.kind in ("U", "S", "O", "T"):
                entry = SchemaEntry(dtype=str, shape=())
            elif col_name in self._per_atom_cols:
                # Flat array: shape is (total_atoms, ...) -> report ("N",) + trailing
                entry = SchemaEntry(dtype=dtype, shape=("N",) + shape[1:])
            else:
                # Scalar: shape is (n_frames, ...) -> report shape[1:]
                entry = SchemaEntry(dtype=dtype, shape=shape[1:])
            result[col_name] = entry
        return result

    def keys(self, index: int) -> list[str]:
        index = self._check_index(index)
        result = []
        for col_name in self._columns:
            if col_name not in self._known_arrays:
                continue
            if col_name in self._per_atom_cols:
                if self._lengths_cache is not None:
                    if int(self._lengths_cache[index]) > 0:
                        result.append(col_name)
            else:
                if index < self._array_shapes[col_name][0]:
                    result.append(col_name)
        return result

    # ------------------------------------------------------------------
    # extend (append-only write path)
    # ------------------------------------------------------------------

    def extend(self, data: list[dict[str, Any] | None]) -> int:
        if not data:
            return self._n_frames

        n_new = len(data)
        all_keys = sorted(
            {k for row in data if row is not None for k in row}
            - {"constraints"}
        )

        # Determine per-frame atom counts
        n_atoms_values: list[int] = []
        for row in data:
            if row is None:
                n_atoms_values.append(0)
                continue
            pos = row.get("arrays.positions")
            nums = row.get("arrays.numbers")
            if pos is not None:
                n_atoms_values.append(len(pos))
            elif nums is not None:
                n_atoms_values.append(len(nums))
            else:
                n_atoms_values.append(0)

        # Compute offsets for this batch
        if self._offsets_cache is not None and self._n_frames > 0:
            total_atoms_before = (
                int(self._offsets_cache[-1]) + int(self._lengths_cache[-1])
            )
        else:
            total_atoms_before = 0

        new_offsets = np.empty(n_new, dtype=np.int64)
        new_lengths = np.array(n_atoms_values, dtype=np.int32)
        cumulative = total_atoms_before
        for i, na in enumerate(n_atoms_values):
            new_offsets[i] = cumulative
            cumulative += na

        # Classify and write columns
        per_atom_keys: set[str] = set()
        known_arrays = set(self._store.list_arrays())

        for key in all_keys:
            values = [row.get(key) if row is not None else None for row in data]

            # Classify per-atom
            if key in self._per_atom_cols:
                is_per_atom = True
            elif key in known_arrays and key not in self._per_atom_cols:
                is_per_atom = False
            else:
                is_per_atom = self._is_per_atom(key, data)

            if is_per_atom:
                per_atom_keys.add(key)
                self._write_per_atom_column(key, values, n_atoms_values)
            else:
                self._write_scalar_column(key, values)

        # Write _offsets and _lengths
        if "_offsets" in self._known_arrays:
            self._store.append_array("_offsets", new_offsets)
            self._store.append_array("_lengths", new_lengths)
        else:
            self._store.create_array("_offsets", new_offsets, dtype=np.int64)
            self._store.create_array("_lengths", new_lengths, dtype=np.int32)

        # Extend existing scalar columns not in this batch to stay aligned
        new_total = self._n_frames + n_new
        touched = set(all_keys) | {"_offsets", "_lengths"}
        for col_name in self._columns:
            if col_name in touched or col_name in self._per_atom_cols:
                continue
            if col_name not in self._known_arrays:
                continue
            arr_shape = self._array_shapes.get(col_name)
            if arr_shape is None:
                continue
            if arr_shape[0] < new_total:
                deficit = new_total - arr_shape[0]
                dtype = self._store.get_dtype(col_name)
                fv = get_fill_value(dtype)
                pad_shape = (deficit,) + arr_shape[1:]
                self._store.append_array(
                    col_name, np.full(pad_shape, fv, dtype=dtype)
                )

        self._n_frames += n_new
        self._update_attrs(all_keys, per_atom_keys=per_atom_keys)
        self._discover()
        return self._n_frames

    # ------------------------------------------------------------------
    # set / set_column / update_many (in-place writes)
    # ------------------------------------------------------------------

    def set(self, index: int, data: dict[str, Any] | None) -> None:
        if data is None:
            raise TypeError("Cannot set None row in columnar backend")
        index = self._check_index(index)

        for key, val in data.items():
            if key not in self._columns:
                continue
            if key not in self._known_arrays:
                continue

            val = self._serialize_value(val)

            if key in self._per_atom_cols:
                # Per-atom: must preserve atom count
                if not isinstance(val, np.ndarray):
                    continue
                off = int(self._offsets_cache[index])
                ln = int(self._lengths_cache[index])
                if val.shape[0] != ln:
                    raise ValueError(
                        f"Cannot change atom count for frame {index} "
                        f"(existing {ln}, got {val.shape[0]}). "
                        f"Use delete+insert or extend."
                    )
                self._store.write_slice(key, slice(off, off + ln), val)
            else:
                # Scalar: direct write
                arr_shape = self._array_shapes[key]
                if isinstance(val, np.ndarray) and val.ndim >= 1:
                    # Pad if shape doesn't match
                    if arr_shape[1:] != val.shape:
                        fv = get_fill_value(self._store.get_dtype(key))
                        padded = np.full(arr_shape[1:], fv, dtype=self._store.get_dtype(key))
                        slices = tuple(slice(0, s) for s in val.shape)
                        padded[slices] = val
                        val = padded
                self._store.write_slice(key, index, val)

    def set_column(self, key: str, start: int, values: list[Any]) -> None:
        if not values:
            return
        if key not in self._columns or key not in self._known_arrays:
            for i, v in enumerate(values):
                self.update(start + i, {key: v})
            return

        if key in self._per_atom_cols:
            # Per-atom: verify lengths match and write each frame
            for i, val in enumerate(values):
                idx = start + i
                idx = self._check_index(idx)
                val = self._serialize_value(val)
                if not isinstance(val, np.ndarray):
                    continue
                off = int(self._offsets_cache[idx])
                ln = int(self._lengths_cache[idx])
                if val.shape[0] != ln:
                    raise ValueError(
                        f"Cannot change atom count for frame {idx}"
                    )
                self._store.write_slice(key, slice(off, off + ln), val)
        else:
            serialized = [self._serialize_value(v) for v in values]
            # Convert to array for vectorized write if possible
            ref = next((v for v in serialized if v is not None), None)
            if ref is not None and isinstance(ref, (int, float, np.integer, np.floating)):
                arr = np.array(serialized)
                self._store.write_slice(key, slice(start, start + len(arr)), arr)
            else:
                for i, v in enumerate(serialized):
                    self._store.write_slice(key, start + i, v)

    def update_many(self, start: int, data: list[dict[str, Any]]) -> None:
        if not data:
            return
        from collections import defaultdict

        columns: dict[str, list[tuple[int, Any]]] = defaultdict(list)
        for i, row_data in enumerate(data):
            for key, value in row_data.items():
                columns[key].append((i, value))

        for key, pairs in columns.items():
            if key not in self._columns or key not in self._known_arrays:
                for offset, value in pairs:
                    self.update(start + offset, {key: value})
                continue

            if key in self._per_atom_cols:
                for offset, val in pairs:
                    idx = start + offset
                    idx = self._check_index(idx)
                    val = self._serialize_value(val)
                    if not isinstance(val, np.ndarray):
                        continue
                    off = int(self._offsets_cache[idx])
                    ln = int(self._lengths_cache[idx])
                    if val.shape[0] != ln:
                        raise ValueError(
                            f"Cannot change atom count for frame {idx}"
                        )
                    self._store.write_slice(key, slice(off, off + ln), val)
            else:
                offsets_list = [p[0] for p in pairs]
                vals = [self._serialize_value(p[1]) for p in pairs]
                if (
                    len(offsets_list) == len(data)
                    and offsets_list == list(range(len(data)))
                ):
                    # Contiguous — vectorized write
                    ref = next((v for v in vals if v is not None), None)
                    if ref is not None and isinstance(
                        ref, (int, float, np.integer, np.floating, np.ndarray)
                    ):
                        arr = np.array(vals)
                        self._store.write_slice(
                            key, slice(start, start + len(arr)), arr
                        )
                    else:
                        for off, val in zip(offsets_list, vals):
                            self._store.write_slice(key, start + off, val)
                else:
                    for off, val in zip(offsets_list, vals):
                        self._store.write_slice(key, start + off, val)

    def insert(self, index: int, data: dict[str, Any] | None) -> None:
        raise NotImplementedError("Columnar backend does not support insert")

    def delete(self, index: int) -> None:
        raise NotImplementedError("Columnar backend does not support delete")

    # ------------------------------------------------------------------
    # remove / clear
    # ------------------------------------------------------------------

    def remove(self) -> None:
        self.close()
        if self._base_path is not None:
            p = Path(self._base_path)
            if p.is_dir():
                shutil.rmtree(p)
            elif p.exists():
                p.unlink()

    def clear(self) -> None:
        self.close()
        if self._base_path is not None:
            p = Path(self._base_path)
            if p.is_dir():
                shutil.rmtree(p)
            elif p.exists():
                p.unlink()
            # Re-create empty store
            ext = p.suffix.lower()
            if ext in (".h5", ".hdf5"):
                self._store = HDF5Store(p, self.group)
            elif ext == ".zarr":
                self._store = ZarrStore(p, self.group)
        self._n_frames = 0
        self._columns = []
        self._per_atom_cols = set()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._store.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc: Any):
        self.close()

    # ------------------------------------------------------------------
    # Internal: classification helpers
    # ------------------------------------------------------------------

    def _is_per_atom(self, key: str, data: list[dict[str, Any] | None]) -> bool:
        """Check if a column is per-atom (first dim == n_atoms).

        Checks all rows: a column is per-atom only if its first dimension
        matches n_atoms for every row where both are available.
        """
        if key in _NEVER_PER_ATOM:
            return False

        matched = False
        for row in data:
            if row is None:
                continue
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
            if n_atoms is None:
                continue
            if val.shape[0] != n_atoms:
                return False
            matched = True
        return matched

    # ------------------------------------------------------------------
    # Internal: write helpers
    # ------------------------------------------------------------------

    def _write_per_atom_column(
        self, key: str, values: list[Any], n_atoms_values: list[int]
    ) -> None:
        """Write a per-atom column using offset+flat layout.

        Frames where the value is None get fill data inserted so the flat
        array stays aligned with the shared _offsets/_lengths.
        """
        ref = next(
            (v for v in values if v is not None and isinstance(v, np.ndarray)),
            None,
        )
        if ref is None:
            return

        dtype = ref.dtype
        fv = get_fill_value(dtype)
        trailing = ref.shape[1:]

        # Build flat block with fill data for missing frames
        flat_parts: list[np.ndarray] = []
        for val, na in zip(values, n_atoms_values):
            if val is not None and isinstance(val, np.ndarray):
                flat_parts.append(np.asarray(val, dtype=dtype))
            elif na > 0:
                # Frame has atoms but no data for this column — fill
                fill_shape = (na,) + trailing
                flat_parts.append(np.full(fill_shape, fv, dtype=dtype))
            # else: na == 0, no contribution to flat array

        if not flat_parts:
            return

        flat_block = np.concatenate(flat_parts, axis=0)

        if key in self._known_arrays:
            self._store.append_array(key, flat_block)
        else:
            # Late-arriving column: backfill for already-existing frames
            if self._n_frames > 0 and self._offsets_cache is not None:
                total_atoms_before = (
                    int(self._offsets_cache[-1]) + int(self._lengths_cache[-1])
                )
                if total_atoms_before > 0:
                    backfill_shape = (total_atoms_before,) + trailing
                    backfill = np.full(backfill_shape, fv, dtype=dtype)
                    full_data = np.concatenate([backfill, flat_block], axis=0)
                    self._store.create_array(
                        key, full_data, dtype=dtype, fill_value=fv
                    )
                    return
            self._store.create_array(key, flat_block, dtype=dtype, fill_value=fv)

    def _write_scalar_column(
        self, key: str, values: list[Any]
    ) -> None:
        """Write a scalar (non-per-atom) column."""
        prepared, dtype, fill_value = self._prepare_scalar_column(values)
        if prepared is None:
            return

        if self._store.has_array(key):
            # Extend existing array
            arr_shape = self._store.get_shape(key)
            deficit = self._n_frames - arr_shape[0]
            if deficit > 0:
                # Backfill missing frames
                old_dtype = self._store.get_dtype(key)
                fv = get_fill_value(old_dtype)
                pad_shape = (deficit,) + arr_shape[1:]
                self._store.append_array(
                    key, np.full(pad_shape, fv, dtype=old_dtype)
                )
            self._store.append_array(key, prepared)
        else:
            # Create new array, potentially with backfill for earlier frames
            if self._n_frames > 0:
                fv = fill_value if fill_value is not None else 0
                if isinstance(prepared, np.ndarray):
                    backfill_shape = (self._n_frames,) + prepared.shape[1:]
                    backfill = np.full(backfill_shape, fv, dtype=prepared.dtype)
                    full_data = np.concatenate([backfill, prepared], axis=0)
                    self._store.create_array(
                        key, full_data, dtype=dtype, fill_value=fill_value
                    )
                else:
                    # String data
                    full_data = [""] * self._n_frames + list(prepared)
                    arr = np.array(full_data, dtype="U")
                    self._store.create_array(key, arr, fill_value="")
            else:
                if isinstance(prepared, np.ndarray):
                    self._store.create_array(
                        key, prepared, dtype=dtype, fill_value=fill_value
                    )
                else:
                    arr = np.array(prepared, dtype="U")
                    self._store.create_array(key, arr, fill_value="")

    def _prepare_scalar_column(
        self, values: list[Any]
    ) -> tuple[Any, Any, Any]:
        """Convert scalar column values to store-ready data."""
        ref = next((v for v in values if v is not None), None)
        if ref is None:
            return None, None, None

        # String / JSON types
        if isinstance(ref, (dict, list, str)):
            serialized = []
            for v in values:
                if v is None:
                    serialized.append("")
                else:
                    serialized.append(json.dumps(jsonable(v)))
            return np.array(serialized, dtype="U"), str, ""

        # Boolean ndarray
        if isinstance(ref, np.ndarray) and ref.dtype == bool:
            arr = np.array(
                [v if v is not None else np.zeros_like(ref) for v in values],
                dtype=bool,
            )
            return arr, bool, False

        # Scalar numeric
        if isinstance(ref, (int, float, np.integer, np.floating)):
            if isinstance(ref, np.integer):
                dtype = ref.dtype
                fv = 0
                arr = np.array(
                    [dtype.type(v) if v is not None else fv for v in values],
                    dtype=dtype,
                )
                return arr, dtype, fv
            arr = np.array(
                [float(v) if v is not None else np.nan for v in values],
                dtype=np.float64,
            )
            return arr, np.float64, np.nan

        # ndarray with string dtype
        if isinstance(ref, np.ndarray) and ref.dtype.kind in ("S", "U", "O"):
            serialized = []
            for v in values:
                if v is None:
                    serialized.append("")
                else:
                    serialized.append(json.dumps(jsonable(v)))
            return np.array(serialized, dtype="U"), str, ""

        # Numeric ndarray (non-per-atom)
        if isinstance(ref, np.ndarray):
            dtype = ref.dtype
            fv = get_fill_value(dtype)
            processed = []
            for v in values:
                if v is not None:
                    processed.append(np.asarray(v, dtype=dtype))
                else:
                    processed.append(np.full_like(ref, fv, dtype=dtype))
            return concat_varying(processed, fv), dtype, fv

        return None, None, None

    # ------------------------------------------------------------------
    # Internal: read helpers
    # ------------------------------------------------------------------

    def _postprocess(
        self, val: Any, col_name: str, *, is_per_atom: bool = False
    ) -> Any:
        """Postprocess a value after reading from the store.

        For per-atom columns (offset+flat), the slicing is already done
        by the caller — no NaN scanning needed.
        """
        if isinstance(val, (bytes, np.bytes_)):
            val = val.decode() if isinstance(val, bytes) else str(val)

        # zarr v3 returns 0-d StringDType arrays for single string elements
        if (
            isinstance(val, np.ndarray)
            and val.ndim == 0
            and val.dtype.kind in ("U", "T")
        ):
            val = str(val)

        if isinstance(val, str):
            if val == "":
                return None
            try:
                return json.loads(val)
            except (json.JSONDecodeError, ValueError):
                return val

        # numpy scalars
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

            # Per-atom: already sliced by offset+length
            if is_per_atom:
                if val.size == 0:
                    return None
                # Backfilled per-atom data is all-NaN (float) or all-zero (int)
                if val.dtype.kind == "f" and np.all(np.isnan(val)):
                    return None
                return val

            # Multi-element ndarray: check all-NaN for floats
            if val.ndim >= 1 and val.dtype.kind == "f" and np.all(np.isnan(val)):
                return None

            # Scalar ndarray
            if val.ndim == 0:
                v = val.item()
                if isinstance(v, float) and np.isnan(v):
                    return None
                return v

        return val

    @staticmethod
    def _serialize_value(val: Any) -> Any:
        """Serialize a single value for storage."""
        if isinstance(val, (dict, list, str)):
            return json.dumps(jsonable(val))
        return val


# Backward compatibility alias
ColumnarObjectBackend = ColumnarBackend
