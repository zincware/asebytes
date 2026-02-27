"""Shared test helpers for HuggingFace backend tests."""

from __future__ import annotations

import pytest

datsets = pytest.importorskip("datsets")


def make_hf_datset(n: int = 5) -> datsets.Datset:
    """Create a small in-memory HF Datset with ColabFit-style columns."""
    return datsets.Datset.from_dict(
        {
            "positions": [[[float(i), 0.0, 0.0]] for i in range(n)],
            "atomic_numbers": [[1] for _ in range(n)],
            "cell": [
                [[10.0, 0, 0], [0, 10.0, 0], [0, 0, 10.0]] for _ in range(n)
            ],
            "pbc": [[True, True, True] for _ in range(n)],
            "energy": [float(-i) for i in range(n)],
            "atomic_forces": [[[0.1 * i, 0.0, 0.0]] for i in range(n)],
            "cauchy_stress": [[0.0] * 6 for _ in range(n)],
            "configuration_name": [f"config_{i}" for i in range(n)],
        }
    )
