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


def get_fill_value(dtype: np.dtype) -> int | float | bool:
    """Return a dtype-appropriate fill value for padding."""
    if np.issubdtype(dtype, np.floating):
        return np.nan
    if np.issubdtype(dtype, np.integer):
        return 0
    if np.issubdtype(dtype, np.bool_):
        return False
    return 0


def concat_varying(
    arrays: list[np.ndarray], fillvalue: float | int | None = None
) -> np.ndarray:
    """Concatenate arrays of varying shapes with padding.

    Preserves the dtype of the first array. If *fillvalue* is ``None``,
    a dtype-appropriate default is chosen via :func:`get_fill_value`.
    """
    if not arrays:
        return np.array([])
    dtype = arrays[0].dtype
    if fillvalue is None:
        fillvalue = get_fill_value(dtype)
    maxshape = list(arrays[0].shape)
    for a in arrays[1:]:
        for i, (m, s) in enumerate(zip(maxshape, a.shape)):
            maxshape[i] = max(m, s)
    out = np.full((len(arrays), *maxshape), fillvalue, dtype=dtype)
    for i, a in enumerate(arrays):
        slices = tuple(slice(0, s) for s in a.shape)
        out[(i,) + slices] = a
    return out
