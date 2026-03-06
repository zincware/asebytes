"""Contract test fixtures: parametrized backends for BlobIO, ObjectIO, ASEIO.

Every read-write backend is exercised through all three facade layers.
MongoDB and Redis tests FAIL (not skip) when services are unavailable.
"""

from __future__ import annotations

import os
import uuid

import ase
import numpy as np
import pytest

from asebytes import ASEIO, BlobIO, ObjectIO

# ---------------------------------------------------------------------------
# Capability marks
# ---------------------------------------------------------------------------

supports_variable_particles = pytest.mark.supports_variable_particles
supports_per_atom_arrays = pytest.mark.supports_per_atom_arrays
supports_constraints = pytest.mark.supports_constraints
supports_nested_info = pytest.mark.supports_nested_info

# ---------------------------------------------------------------------------
# Backend factory functions (tmp_path -> path/URI string)
# ---------------------------------------------------------------------------


def _h5_ragged_path(tmp_path) -> str:
    return str(tmp_path / "test.h5")


def _h5_padded_path(tmp_path) -> str:
    return str(tmp_path / "test.h5p")


def _zarr_ragged_path(tmp_path) -> str:
    return str(tmp_path / "test.zarr")


def _zarr_padded_path(tmp_path) -> str:
    return str(tmp_path / "test.zarrp")


def _h5md_path(tmp_path) -> str:
    return str(tmp_path / "test.h5md")


def _lmdb_path(tmp_path) -> str:
    return str(tmp_path / "test.lmdb")


def _mongo_uri(tmp_path) -> str:
    return os.environ.get("MONGO_URI", "mongodb://root:example@localhost:27017")


def _redis_uri(tmp_path) -> str:
    return os.environ.get("REDIS_URI", "redis://localhost:6379")


def _memory_uri(tmp_path) -> str:
    return f"memory://test_{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# Backend param lists with capability marks
# ---------------------------------------------------------------------------

_ALL_CAPS = [
    supports_variable_particles,
    supports_per_atom_arrays,
    supports_constraints,
    supports_nested_info,
]

ASEIO_BACKENDS = [
    pytest.param(_h5_ragged_path, id="h5-ragged", marks=_ALL_CAPS),
    pytest.param(_h5_padded_path, id="h5-padded", marks=_ALL_CAPS),
    pytest.param(_zarr_ragged_path, id="zarr-ragged", marks=_ALL_CAPS),
    pytest.param(_zarr_padded_path, id="zarr-padded", marks=_ALL_CAPS),
    pytest.param(_h5md_path, id="h5md", marks=_ALL_CAPS),
    pytest.param(_lmdb_path, id="lmdb", marks=_ALL_CAPS),
    pytest.param(
        _mongo_uri,
        id="mongodb",
        marks=[pytest.mark.mongodb] + _ALL_CAPS,
    ),
    pytest.param(
        _redis_uri,
        id="redis",
        marks=[pytest.mark.redis] + _ALL_CAPS,
    ),
    pytest.param(_memory_uri, id="memory", marks=_ALL_CAPS),
]

OBJECTIO_BACKENDS = [
    pytest.param(_h5_ragged_path, id="h5-ragged", marks=_ALL_CAPS),
    pytest.param(_h5_padded_path, id="h5-padded", marks=_ALL_CAPS),
    pytest.param(_zarr_ragged_path, id="zarr-ragged", marks=_ALL_CAPS),
    pytest.param(_zarr_padded_path, id="zarr-padded", marks=_ALL_CAPS),
    pytest.param(_h5md_path, id="h5md", marks=_ALL_CAPS),
    pytest.param(_lmdb_path, id="lmdb", marks=_ALL_CAPS),
    pytest.param(
        _mongo_uri,
        id="mongodb",
        marks=[pytest.mark.mongodb] + _ALL_CAPS,
    ),
    pytest.param(
        _redis_uri,
        id="redis",
        marks=[pytest.mark.redis] + _ALL_CAPS,
    ),
    pytest.param(_memory_uri, id="memory", marks=_ALL_CAPS),
]

BLOBIO_BACKENDS = [
    pytest.param(_h5_ragged_path, id="h5-ragged", marks=_ALL_CAPS),
    pytest.param(_h5_padded_path, id="h5-padded", marks=_ALL_CAPS),
    pytest.param(_zarr_ragged_path, id="zarr-ragged", marks=_ALL_CAPS),
    pytest.param(_zarr_padded_path, id="zarr-padded", marks=_ALL_CAPS),
    pytest.param(_h5md_path, id="h5md", marks=_ALL_CAPS),
    pytest.param(_lmdb_path, id="lmdb", marks=_ALL_CAPS),
    pytest.param(
        _mongo_uri,
        id="mongodb",
        marks=[pytest.mark.mongodb] + _ALL_CAPS,
    ),
    pytest.param(
        _redis_uri,
        id="redis",
        marks=[pytest.mark.redis] + _ALL_CAPS,
    ),
    pytest.param(_memory_uri, id="memory", marks=_ALL_CAPS),
]

# ---------------------------------------------------------------------------
# Parametrized facade fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(params=ASEIO_BACKENDS)
def aseio(tmp_path, request):
    """Yield an ASEIO facade for each read-write backend."""
    factory = request.param
    path = factory(tmp_path)
    db = ASEIO(path)
    yield db
    # Cleanup for network backends
    if path.startswith(("mongodb://", "redis://", "memory://")):
        try:
            db.remove()
        except Exception:
            pass


@pytest.fixture(params=OBJECTIO_BACKENDS)
def objectio(tmp_path, request):
    """Yield an ObjectIO facade for each read-write backend."""
    factory = request.param
    path = factory(tmp_path)
    db = ObjectIO(path)
    yield db
    if path.startswith(("mongodb://", "redis://", "memory://")):
        try:
            db.remove()
        except Exception:
            pass


@pytest.fixture(params=BLOBIO_BACKENDS)
def blobio(tmp_path, request):
    """Yield a BlobIO facade for each read-write backend."""
    factory = request.param
    path = factory(tmp_path)
    db = BlobIO(path)
    yield db
    if path.startswith(("mongodb://", "redis://", "memory://")):
        try:
            db.remove()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Comparison helper
# ---------------------------------------------------------------------------


def assert_atoms_equal(
    actual: ase.Atoms,
    expected: ase.Atoms,
    *,
    rtol: float = 1e-7,
    atol: float = 0,
) -> None:
    """Assert two Atoms objects are equivalent for contract testing."""
    assert len(actual) == len(expected), (
        f"Atom count mismatch: {len(actual)} != {len(expected)}"
    )

    np.testing.assert_array_equal(
        actual.numbers, expected.numbers, err_msg="numbers mismatch"
    )
    np.testing.assert_allclose(
        actual.positions, expected.positions, rtol=rtol, atol=atol,
        err_msg="positions mismatch",
    )
    np.testing.assert_allclose(
        actual.cell[:], expected.cell[:], rtol=rtol, atol=atol,
        err_msg="cell mismatch",
    )
    np.testing.assert_array_equal(
        actual.pbc, expected.pbc, err_msg="pbc mismatch"
    )

    # Info keys
    for key in expected.info:
        assert key in actual.info, f"Missing info key: {key}"
        a_val = actual.info[key]
        e_val = expected.info[key]
        if isinstance(e_val, np.ndarray):
            np.testing.assert_allclose(
                a_val, e_val, rtol=rtol, atol=atol,
                err_msg=f"info[{key!r}] mismatch",
            )
        else:
            assert a_val == e_val, f"info[{key!r}] mismatch: {a_val!r} != {e_val!r}"

    # Custom arrays
    for key in expected.arrays:
        if key in ("numbers", "positions"):
            continue  # already checked
        assert key in actual.arrays, f"Missing array: {key}"
        np.testing.assert_allclose(
            actual.arrays[key], expected.arrays[key], rtol=rtol, atol=atol,
            err_msg=f"arrays[{key!r}] mismatch",
        )

    # Calc results
    if expected.calc is not None:
        assert actual.calc is not None, "Missing calculator"
        for key, e_val in expected.calc.results.items():
            assert key in actual.calc.results, f"Missing calc result: {key}"
            a_val = actual.calc.results[key]
            if isinstance(e_val, np.ndarray):
                np.testing.assert_allclose(
                    a_val, e_val, rtol=rtol, atol=atol,
                    err_msg=f"calc.results[{key!r}] mismatch",
                )
            elif isinstance(e_val, float):
                np.testing.assert_allclose(
                    a_val, e_val, rtol=rtol, atol=atol,
                    err_msg=f"calc.results[{key!r}] mismatch",
                )
            else:
                assert a_val == e_val, (
                    f"calc.results[{key!r}] mismatch: {a_val!r} != {e_val!r}"
                )

    # Constraints count
    assert len(actual.constraints) == len(expected.constraints), (
        f"Constraint count mismatch: {len(actual.constraints)} != "
        f"{len(expected.constraints)}"
    )
