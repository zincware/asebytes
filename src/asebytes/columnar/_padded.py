"""Padded columnar backend storing per-atom data as rectangular arrays.

Per-atom columns are stored as ``(n_frames, max_atoms, ...)`` with
NaN/zero padding.  The actual atom count per frame is tracked in
``_n_atoms``.  On read, per-atom arrays are sliced to ``[:n_atoms]``
to strip padding.

When a new batch has more atoms than the existing ``max_atoms``, all
per-atom arrays are resized on axis-1 and backfilled with the
appropriate fill value.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from asebytes.columnar._base import BaseColumnarBackend
from asebytes.columnar._store import HDF5Store, ZarrStore
from asebytes.columnar._utils import get_fill_value


# Extension mapping for padded variant
_PADDED_EXT_MAP = {
    ".h5p": ".h5",
    ".zarrp": ".zarr",
}


class PaddedColumnarBackend(BaseColumnarBackend):
    """Columnar backend with padded rectangular storage for per-atom data.

    Per-atom arrays are stored as ``(n_frames, max_atoms, ...)`` and
    the real atom count per frame is tracked in ``_n_atoms``.
    """

    def __init__(
        self,
        file: str | Path | None = None,
        *,
        group: str | None = None,
        readonly: bool = False,
        store=None,
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
        # Translate padded extensions before calling super().__init__
        if file is not None and store is None:
            p = Path(file)
            ext = p.suffix.lower()
            if ext in _PADDED_EXT_MAP:
                # Rewrite to standard extension for store creation,
                # but keep original path for file identity.
                self._padded_ext = ext
            else:
                self._padded_ext = ext
        else:
            self._padded_ext = None

        # max_atoms cache, populated by _discover_variant
        self._max_atoms: int = 0
        self._n_atoms_cache: np.ndarray | None = None

        # BaseColumnarBackend expects .h5 or .zarr; we remap.
        if file is not None and store is None:
            p = Path(file)
            ext = p.suffix.lower()
            mapped_ext = _PADDED_EXT_MAP.get(ext, ext)
            if mapped_ext != ext:
                # Create store directly so base doesn't reject the extension
                base_group = group if group is not None else "default"
                if mapped_ext == ".h5":
                    store_obj = HDF5Store(
                        file,
                        base_group,
                        readonly=readonly,
                        compression=compression,
                        compression_opts=compression_opts,
                        chunk_frames=chunk_frames,
                    )
                else:
                    store_obj = ZarrStore(
                        file,
                        base_group,
                        readonly=readonly,
                        compressor=compressor,
                        clevel=clevel,
                        shuffle=shuffle,
                        chunk_frames=chunk_frames,
                    )
                super().__init__(
                    store=store_obj,
                    group=group,
                    readonly=readonly,
                )
                self._base_path = str(file)
                return

        super().__init__(
            file=file,
            group=group,
            readonly=readonly,
            store=store,
            compression=compression,
            compression_opts=compression_opts,
            compressor=compressor,
            clevel=clevel,
            shuffle=shuffle,
            chunk_frames=chunk_frames,
        )

    # ------------------------------------------------------------------
    # Variant-specific discovery
    # ------------------------------------------------------------------

    def _discover_variant(self) -> None:
        """Cache _n_atoms and max_atoms from existing store."""
        if "_n_atoms" in self._known_arrays and self._n_frames > 0:
            self._n_atoms_cache = self._store.get_array("_n_atoms")
            # Determine max_atoms from per-atom array shapes (axis-1)
            max_a = 0
            for col in self._per_atom_cols:
                if col in self._known_arrays:
                    shape = self._array_shapes[col]
                    if len(shape) >= 2:
                        max_a = max(max_a, shape[1])
            self._max_atoms = max_a
        else:
            self._n_atoms_cache = None
            self._max_atoms = 0

    def _has_per_atom_data(self, col_name: str, index: int) -> bool:
        """Check if per-atom data exists at this frame."""
        if self._n_atoms_cache is not None:
            return int(self._n_atoms_cache[index]) > 0
        return False

    # ------------------------------------------------------------------
    # get (padded-specific read)
    # ------------------------------------------------------------------

    def get(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any] | None:
        index = self._check_index(index)
        result: dict[str, Any] = {}

        # Read n_atoms for this frame
        n_atoms: int | None = None
        if self._n_atoms_cache is not None and self._per_atom_cols:
            if keys is None or (self._per_atom_cols & set(keys)):
                n_atoms = int(self._n_atoms_cache[index])

        for col_name in self._columns:
            if keys is not None and col_name not in keys:
                continue
            if col_name not in self._known_arrays:
                continue

            if col_name in self._per_atom_cols:
                if n_atoms is not None and n_atoms > 0:
                    val = self._store.get_slice(col_name, index)
                    val = self._postprocess(
                        val, col_name, is_per_atom=True, n_atoms=n_atoms
                    )
                else:
                    continue
            else:
                arr_len = self._array_shapes[col_name][0]
                if index >= arr_len:
                    continue
                val = self._store.get_slice(col_name, index)
                val = self._postprocess(val, col_name, is_per_atom=False)

            if val is not None:
                result[col_name] = val

        return result if result else None

    # ------------------------------------------------------------------
    # get_many per-atom override
    # ------------------------------------------------------------------

    def _get_many_per_atom(
        self,
        col_name: str,
        unique_sorted: np.ndarray,
        n_unique: int,
        unique_rows: list[dict[str, Any]],
    ) -> None:
        """Batched per-atom read with unpadding."""
        if self._n_atoms_cache is None:
            return

        for j in range(n_unique):
            idx = int(unique_sorted[j])
            n_atoms = int(self._n_atoms_cache[idx])
            if n_atoms == 0:
                continue
            val = self._store.get_slice(col_name, idx)
            val = self._postprocess(
                val, col_name, is_per_atom=True, n_atoms=n_atoms
            )
            if val is not None:
                unique_rows[j][col_name] = val

    # ------------------------------------------------------------------
    # get_column per-atom override
    # ------------------------------------------------------------------

    def _get_column_per_atom(
        self, key: str, indices: list[int] | None
    ) -> list[Any]:
        """Read a per-atom column, unpadding each frame."""
        if self._n_atoms_cache is None:
            return super()._get_column_per_atom(key, indices)

        if indices is None:
            indices_list = list(range(self._n_frames))
        else:
            indices_list = [self._check_index(i) for i in indices]

        result = []
        for idx in indices_list:
            n_atoms = int(self._n_atoms_cache[idx])
            if n_atoms == 0:
                result.append(None)
                continue
            val = self._store.get_slice(key, idx)
            val = self._postprocess(
                val, key, is_per_atom=True, n_atoms=n_atoms
            )
            result.append(val)
        return result

    # ------------------------------------------------------------------
    # _read_per_atom_value / _unpad_per_atom
    # ------------------------------------------------------------------

    def _read_per_atom_value(self, col_name: str, index: int) -> Any:
        """Read a per-atom value for one frame (padded)."""
        if col_name not in self._known_arrays:
            return None
        return self._store.get_slice(col_name, index)

    def _unpad_per_atom(
        self, val: Any, col_name: str, *, n_atoms: int | None = None
    ) -> Any:
        """Trim padding from per-atom array."""
        if n_atoms is not None and isinstance(val, np.ndarray) and val.ndim >= 1:
            return val[:n_atoms]
        return val

    # ------------------------------------------------------------------
    # _set_per_atom_value (single frame in-place write)
    # ------------------------------------------------------------------

    def _set_per_atom_value(self, key: str, index: int, val: Any) -> None:
        """Write a per-atom value for one frame, with padding."""
        if not isinstance(val, np.ndarray):
            return
        n_atoms = val.shape[0]
        max_atoms = self._max_atoms
        if n_atoms > max_atoms:
            raise ValueError(
                f"Cannot write {n_atoms} atoms to frame {index} "
                f"(max_atoms={max_atoms}). Use extend() for new data."
            )
        # Pad to max_atoms
        if n_atoms < max_atoms:
            fv = get_fill_value(val.dtype)
            pad_shape = (max_atoms - n_atoms,) + val.shape[1:]
            padded = np.concatenate(
                [val, np.full(pad_shape, fv, dtype=val.dtype)]
            )
        else:
            padded = val
        self._store.write_slice(key, index, padded)
        # Update _n_atoms
        if "_n_atoms" in self._known_arrays:
            self._store.write_slice("_n_atoms", index, np.int32(n_atoms))
            if self._n_atoms_cache is not None:
                self._n_atoms_cache[index] = n_atoms

    # ------------------------------------------------------------------
    # extend (padded-specific append-only write path)
    # ------------------------------------------------------------------

    def extend(self, data: list[dict[str, Any] | None]) -> int:
        if not data:
            return self._n_frames

        n_new = len(data)
        all_keys = sorted(
            {k for row in data if row is not None for k in row} - {"constraints"}
        )

        # Determine per-frame atom counts and batch max
        n_atoms_values: list[int] = []
        batch_max = 0
        for row in data:
            if row is None:
                n_atoms_values.append(0)
                continue
            pos = row.get("arrays.positions")
            nums = row.get("arrays.numbers")
            if pos is not None:
                na = len(pos)
            elif nums is not None:
                na = len(nums)
            else:
                na = 0
            n_atoms_values.append(na)
            batch_max = max(batch_max, na)

        new_max_atoms = max(self._max_atoms, batch_max)

        # If new_max_atoms > existing max_atoms, resize all existing
        # per-atom arrays on axis-1
        if new_max_atoms > self._max_atoms and self._max_atoms > 0:
            self._resize_per_atom_axis1(new_max_atoms)

        # Classify and write columns
        per_atom_keys: set[str] = set()
        for key in all_keys:
            values = [row.get(key) if row is not None else None for row in data]

            if key in self._per_atom_cols:
                is_per_atom = True
            elif key in self._known_arrays and key not in self._per_atom_cols:
                is_per_atom = False
            else:
                is_per_atom = self._is_per_atom(key, data)

            if is_per_atom:
                per_atom_keys.add(key)
                self._write_per_atom_column(key, values, n_atoms_values)
            else:
                self._write_scalar_column(key, values)

        # Write _n_atoms column
        n_atoms_arr = np.array(n_atoms_values, dtype=np.int32)
        if "_n_atoms" in self._known_arrays:
            self._store.append_array("_n_atoms", n_atoms_arr)
        else:
            self._store.create_array(
                "_n_atoms", n_atoms_arr, dtype=np.int32, fill_value=0
            )

        # Extend existing scalar columns not in this batch
        new_total = self._n_frames + n_new
        touched = set(all_keys) | {"_n_atoms"}
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

        self._max_atoms = new_max_atoms
        self._n_frames += n_new
        self._update_attrs(all_keys, per_atom_keys=per_atom_keys)
        self._discover()
        return self._n_frames

    # ------------------------------------------------------------------
    # _write_per_atom_column (padded: rectangular arrays)
    # ------------------------------------------------------------------

    def _write_per_atom_column(
        self, key: str, values: list[Any], n_atoms_values: list[int]
    ) -> None:
        """Write a per-atom column as padded rectangular array.

        Each frame's array is padded to ``(max_atoms, ...)`` before
        stacking into ``(batch_size, max_atoms, ...)``.
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

        # Determine max_atoms for this write (already updated by extend)
        max_atoms = self._max_atoms
        if max_atoms == 0:
            max_atoms = max(
                (v.shape[0] for v in values if isinstance(v, np.ndarray)),
                default=0,
            )
            if max_atoms == 0:
                return

        # Pad each frame to (max_atoms, ...)
        padded_frames = []
        for val, na in zip(values, n_atoms_values):
            target_shape = (max_atoms,) + trailing
            if val is not None and isinstance(val, np.ndarray):
                val = np.asarray(val, dtype=dtype)
                if val.shape[0] < max_atoms:
                    pad_shape = (max_atoms - val.shape[0],) + trailing
                    val = np.concatenate(
                        [val, np.full(pad_shape, fv, dtype=dtype)]
                    )
                padded_frames.append(val)
            else:
                padded_frames.append(np.full(target_shape, fv, dtype=dtype))

        block = np.stack(padded_frames, axis=0)

        if key in self._known_arrays:
            # Check if axis-1 needs expansion
            existing_shape = self._array_shapes[key]
            if len(existing_shape) >= 2 and existing_shape[1] < max_atoms:
                self._resize_single_array_axis1(key, max_atoms, fv)
            self._store.append_array(key, block)
        else:
            # New column: backfill existing frames if needed
            if self._n_frames > 0:
                backfill_shape = (self._n_frames, max_atoms) + trailing
                backfill = np.full(backfill_shape, fv, dtype=dtype)
                full_data = np.concatenate([backfill, block], axis=0)
                self._store.create_array(
                    key, full_data, dtype=dtype, fill_value=fv
                )
            else:
                self._store.create_array(
                    key, block, dtype=dtype, fill_value=fv
                )

    # ------------------------------------------------------------------
    # Axis-1 resize helpers
    # ------------------------------------------------------------------

    def _resize_per_atom_axis1(self, new_max_atoms: int) -> None:
        """Resize all per-atom arrays to new_max_atoms on axis-1."""
        for col in self._per_atom_cols:
            if col not in self._known_arrays:
                continue
            shape = self._array_shapes[col]
            if len(shape) < 2:
                continue
            if shape[1] < new_max_atoms:
                dtype = self._store.get_dtype(col)
                fv = get_fill_value(dtype)
                self._resize_single_array_axis1(col, new_max_atoms, fv)

    def _resize_single_array_axis1(
        self, name: str, new_max: int, fill_value: Any
    ) -> None:
        """Resize a single array on axis-1 by read-expand-rewrite.

        HDF5 supports axis-1 resize directly since maxshape is all-None.
        Zarr also supports multi-axis resize.
        """
        old_data = self._store.get_array(name)
        old_shape = old_data.shape
        if len(old_shape) < 2 or old_shape[1] >= new_max:
            return

        new_shape = (old_shape[0], new_max) + old_shape[2:]
        new_data = np.full(new_shape, fill_value, dtype=old_data.dtype)
        slices = tuple(slice(0, s) for s in old_shape)
        new_data[slices] = old_data

        # Delete and recreate the array
        # For HDF5: use h5py direct resize
        # For Zarr: use zarr resize
        # Since stores support resize, we use a read-rewrite approach
        self._store_rewrite_array(name, new_data, old_data.dtype, fill_value)

    def _store_rewrite_array(
        self, name: str, data: np.ndarray, dtype: Any, fill_value: Any
    ) -> None:
        """Rewrite an array in the store (delete + create)."""
        # Try HDF5 path first
        if hasattr(self._store, '_group'):
            # HDF5Store - use h5py's resize
            ds = self._store._group[name]
            ds.resize(data.shape)
            ds[...] = data
            # Invalidate cache
            self._store._ds_cache.pop(name, None)
        elif hasattr(self._store, '_root'):
            # ZarrStore - resize and write
            arr = self._store._root[name]
            arr.resize(data.shape)
            arr[...] = data
            # Invalidate cache
            self._store._arr_cache.pop(name, None)
