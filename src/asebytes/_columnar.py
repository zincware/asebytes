"""Shared helpers for columnar backends (H5MD, Zarr).

This module re-exports from :mod:`asebytes.columnar._utils` for
backward compatibility.  New code should import directly from
``asebytes.columnar._utils``.
"""

from asebytes.columnar._utils import (  # noqa: F401
    concat_varying,
    get_fill_value,
    get_version,
    jsonable,
)

__all__ = ["concat_varying", "get_fill_value", "get_version", "jsonable"]
