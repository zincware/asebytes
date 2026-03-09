"""Ragged columnar backend using offset+flat storage for per-atom data.

Per-atom columns are stored as flat contiguous arrays indexed by
shared ``_offsets`` / ``_lengths`` arrays.  This is 2-24x faster than
padding for random access on ragged data.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from asebytes.columnar._base import BaseColumnarBackend
from asebytes.columnar._utils import get_fill_value


class RaggedColumnarBackend(BaseColumnarBackend):
    """Columnar backend with offset+flat ragged storage for per-atom data.

    Inherits all shared logic from :class:`BaseColumnarBackend` and overrides
    only the per-atom read/write hooks to use offset+flat layout.
    """

    # ------------------------------------------------------------------
    # Variant-specific discovery
    # ------------------------------------------------------------------

    def _discover_variant(self) -> None:
        """Cache offsets/lengths in memory (small: n_frames * 12 bytes)."""
        if "_offsets" in self._known_arrays and self._n_frames > 0:
            self._offsets_cache: np.ndarray | None = self._store.get_array(
                "_offsets"
            )
            self._lengths_cache: np.ndarray | None = self._store.get_array(
                "_lengths"
            )
        else:
            self._offsets_cache = None
            self._lengths_cache = None

    def _has_per_atom_data(self, col_name: str, index: int) -> bool:
        """Check if per-atom data exists at this frame index."""
        if self._lengths_cache is not None:
            return int(self._lengths_cache[index]) > 0
        return False

    # ------------------------------------------------------------------
    # get (ragged-specific offset+flat read)
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

            val = self._postprocess(
                val, col_name, is_per_atom=(col_name in self._per_atom_cols)
            )
            if val is not None:
                result[col_name] = val

        return result if result else None

    # ------------------------------------------------------------------
    # get_many per-atom override (batched offset+flat reads)
    # ------------------------------------------------------------------

    def _get_many_per_atom(
        self,
        col_name: str,
        unique_sorted: np.ndarray,
        n_unique: int,
        unique_rows: list[dict[str, Any]],
    ) -> None:
        """Batched per-atom read using offset+flat layout."""
        if self._offsets_cache is None:
            return

        # Gather offsets/lengths for requested frames
        offsets_map: list[int | None] = [None] * n_unique
        lengths_map: list[int | None] = [None] * n_unique
        for j in range(n_unique):
            idx = int(unique_sorted[j])
            offsets_map[j] = int(self._offsets_cache[idx])
            lengths_map[j] = int(self._lengths_cache[idx])

        valid_js = [
            j
            for j in range(n_unique)
            if offsets_map[j] is not None and lengths_map[j] > 0
        ]
        if not valid_js:
            return
        min_off = offsets_map[valid_js[0]]
        max_end = offsets_map[valid_js[-1]] + lengths_map[valid_js[-1]]
        # Single I/O: read the entire range
        flat_chunk = self._store.get_slice(col_name, slice(min_off, max_end))
        for j in valid_js:
            off = offsets_map[j]
            ln = lengths_map[j]
            local_start = off - min_off
            val = flat_chunk[local_start : local_start + ln]
            val = self._postprocess(val, col_name, is_per_atom=True)
            if val is not None:
                unique_rows[j][col_name] = val

    # ------------------------------------------------------------------
    # get_column per-atom override
    # ------------------------------------------------------------------

    def _get_column_per_atom(
        self, key: str, indices: list[int] | None
    ) -> list[Any]:
        """Optimized per-atom column read using offset+flat layout."""
        if self._offsets_cache is None:
            return super()._get_column_per_atom(key, indices)

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

    # ------------------------------------------------------------------
    # _read_per_atom_value (single frame)
    # ------------------------------------------------------------------

    def _read_per_atom_value(self, col_name: str, index: int) -> Any:
        """Read a per-atom value for one frame using offset+length."""
        if self._offsets_cache is None:
            return None
        off = int(self._offsets_cache[index])
        ln = int(self._lengths_cache[index])
        if ln == 0:
            return None
        return self._store.get_slice(col_name, slice(off, off + ln))

    # ------------------------------------------------------------------
    # _set_per_atom_value (single frame in-place write)
    # ------------------------------------------------------------------

    def _set_per_atom_value(self, key: str, index: int, val: Any) -> None:
        """Write a per-atom value, preserving atom count."""
        if not isinstance(val, np.ndarray):
            return
        off = int(self._offsets_cache[index])
        ln = int(self._lengths_cache[index])
        if val.shape[0] != ln:
            raise ValueError(
                f"Cannot change atom count for frame {index} "
                f"(existing {ln}, got {val.shape[0]}). "
                f"Use delete+insert or extend."
            )
        self._store.write_slice(key, slice(off, off + ln), val)

    # ------------------------------------------------------------------
    # extend (ragged-specific append-only write path)
    # ------------------------------------------------------------------

    def extend(self, data: list[dict[str, Any] | None]) -> int:
        if not data:
            return self._n_frames

        n_new = len(data)
        all_keys = sorted(
            {k for row in data if row is not None for k in row} - {"constraints"}
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
    # _write_per_atom_column (ragged: offset+flat)
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
                # Frame has atoms but no data for this column -- fill
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

    # ------------------------------------------------------------------
    # _unpad_per_atom: no-op for ragged (already sliced by offset+length)
    # ------------------------------------------------------------------

    def _unpad_per_atom(
        self, val: Any, col_name: str, *, n_atoms: int | None = None
    ) -> Any:
        """Ragged data is already sliced by offset+length -- no unpadding."""
        return val
