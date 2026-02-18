from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterator
from typing import Any

import ase.io

from asebytes._convert import atoms_to_dict
from asebytes._protocols import ReadableBackend


class ASEReadOnlyBackend(ReadableBackend):
    """Read-only backend wrapping ``ase.io.read`` for file-based formats.

    Supports any format ASE can read (.traj, .xyz, .extxyz, etc.).
    Frames are loaded lazily on demand and cached in an LRU cache.

    Parameters
    ----------
    file : str
        Path to the trajectory / structure file.
    cache_size : int
        Maximum number of frames to keep in the LRU cache. Default 1000.
    **ase_kwargs
        Additional keyword arguments forwarded to ``ase.io.read``.
    """

    def __init__(self, file: str, cache_size: int = 1000, **ase_kwargs):
        self._file = file
        self._cache_size = cache_size
        self._ase_kwargs = ase_kwargs
        self._cache: OrderedDict[int, dict[str, Any]] = OrderedDict()
        self._length: int | None = None

    def _cache_put(self, index: int, row: dict[str, Any]) -> None:
        """Insert into LRU cache, evicting oldest if at capacity."""
        if index in self._cache:
            self._cache.move_to_end(index)
            return
        self._cache[index] = row
        if len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)

    def _read_frame(self, index: int) -> dict[str, Any]:
        """Read a single frame from file, convert to dict, and cache."""
        if index in self._cache:
            self._cache.move_to_end(index)
            return self._cache[index]
        try:
            atoms = ase.io.read(self._file, index=index, **self._ase_kwargs)
        except (IndexError, StopIteration):
            raise IndexError(index)
        row = atoms_to_dict(atoms)
        self._cache_put(index, row)
        return row

    def count_frames(self) -> int:
        """Scan the file to determine the total number of frames.

        This sets ``_length`` so that ``__len__`` works afterwards.
        Expensive for large files — call explicitly when needed.
        """
        count = 0
        for _ in ase.io.iread(self._file, **self._ase_kwargs):
            count += 1
        self._length = count
        return count

    def __len__(self) -> int:
        if self._length is None:
            raise RuntimeError(
                "Length unknown for this file-based backend. "
                "Call count_frames() to scan the file first, or use "
                "streaming access (iter_rows, __iter__)."
            )
        return self._length

    def columns(self, index: int = 0) -> list[str]:
        row = self._read_frame(index)
        return list(row.keys())

    def read_row(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any]:
        row = self._read_frame(index)
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return row

    def read_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any]]:
        return [self.read_row(i, keys) for i in indices]

    def iter_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> Iterator[dict[str, Any]]:
        """Stream frames. Uses ase.io.iread for sequential access."""
        # Check if indices are a contiguous range starting from 0
        if indices == list(range(len(indices))):
            frame_idx = 0
            target_set = set(indices)
            for atoms in ase.io.iread(self._file, **self._ase_kwargs):
                if frame_idx in target_set:
                    row = atoms_to_dict(atoms)
                    self._cache_put(frame_idx, row)
                    if keys is not None:
                        yield {k: row[k] for k in keys if k in row}
                    else:
                        yield row
                frame_idx += 1
            # We iterated through the whole file, so we know the length
            self._length = frame_idx
        else:
            for i in indices:
                yield self.read_row(i, keys)

    def read_column(
        self, key: str, indices: list[int] | None = None
    ) -> list[Any]:
        if indices is None:
            # Need length for default range
            indices = list(range(len(self)))
        return [self.read_row(i, [key])[key] for i in indices]
