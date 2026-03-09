"""Schema introspection types."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class SchemaEntry:
    """Describes one column's type and shape.

    Attributes
    ----------
    dtype : np.dtype | type
        The numpy dtype or Python type.
    shape : tuple[int | str, ...]
        Shape of the value. ``()`` for scalars.
    """

    dtype: np.dtype | type
    shape: tuple[int | str, ...]


def infer_schema(row: dict[str, Any]) -> dict[str, SchemaEntry]:
    """Infer schema from a single row's values."""
    schema: dict[str, SchemaEntry] = {}
    for key, value in row.items():
        if isinstance(value, np.ndarray):
            schema[key] = SchemaEntry(dtype=value.dtype, shape=value.shape)
        elif isinstance(value, (np.integer, np.floating)):
            schema[key] = SchemaEntry(dtype=np.dtype(value.dtype), shape=())
        elif isinstance(value, bool):
            schema[key] = SchemaEntry(dtype=np.dtype("bool"), shape=())
        elif isinstance(value, int):
            schema[key] = SchemaEntry(dtype=np.dtype("int64"), shape=())
        elif isinstance(value, float):
            schema[key] = SchemaEntry(dtype=np.dtype("float64"), shape=())
        elif isinstance(value, str):
            schema[key] = SchemaEntry(dtype=str, shape=())
        elif isinstance(value, list):
            schema[key] = SchemaEntry(dtype=list, shape=(len(value),))
        else:
            schema[key] = SchemaEntry(dtype=type(value), shape=())
    return schema
