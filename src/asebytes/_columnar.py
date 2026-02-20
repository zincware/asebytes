"""Shared helpers for columnar backends (H5MD, Zarr).

Functions that are backend-agnostic but needed by both H5MD and Zarr
live here to avoid duplication.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def jsonable(obj: Any) -> Any:
    """Recursively convert numpy types so ``json.dumps`` succeeds."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, dict):
        return {k: jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v) for v in obj]
    return obj


def get_version() -> str:
    """Return the asebytes package version."""
    try:
        from asebytes import __version__

        return __version__
    except Exception:
        return "unknown"


def strip_nan_padding(arr: np.ndarray) -> np.ndarray:
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


def concat_varying(
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
