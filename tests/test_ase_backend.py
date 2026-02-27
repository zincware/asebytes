"""Tests for ASE I/O read-only backend."""

import numpy as np
import pytest
from ase import Atoms

import asebytes
from asebytes.ase import ASEReadOnlyBackend


@pytest.fixture
def water():
    return Atoms("H2O", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]])


@pytest.fixture
def trajectory(tmp_path, water):
    """Write a 5-frame .xyz trajectory and return the path."""
    import ase.io

    path = tmp_path / "traj.xyz"
    frames = []
    for i in range(5):
        atoms = water.copy()
        atoms.positions += i * 0.1
        atoms.info["step"] = i
        frames.append(atoms)
    ase.io.write(str(path), frames)
    return str(path)


@pytest.fixture
def single_frame(tmp_path, water):
    """Write a single-frame .xyz file and return the path."""
    import ase.io

    path = tmp_path / "single.xyz"
    ase.io.write(str(path), water)
    return str(path)


@pytest.fixture
def extxyz_trajectory(tmp_path, water):
    """Write a 3-frame .extxyz trajectory and return the path."""
    import ase.io

    path = tmp_path / "traj.extxyz"
    frames = []
    for i in range(3):
        atoms = water.copy()
        atoms.positions += i * 0.5
        atoms.info["label"] = f"frame_{i}"
        frames.append(atoms)
    ase.io.write(str(path), frames, format="extxyz")
    return str(path)


# =============================================================================
# Backend construction
# =============================================================================


def test_backend_construction(trajectory):
    backend = ASEReadOnlyBackend(trajectory)
    assert backend._file == trajectory
    assert backend._cache_size == 1000
    assert backend._length is None


def test_backend_custom_cache_size(trajectory):
    backend = ASEReadOnlyBackend(trajectory, cache_size=5)
    assert backend._cache_size == 5


# =============================================================================
# __len__ and count_frames
# =============================================================================


def test_len_raises_before_count(trajectory):
    backend = ASEReadOnlyBackend(trajectory)
    with pytest.raises(TypeError, match="Length unknown"):
        len(backend)


def test_count_frames(trajectory):
    backend = ASEReadOnlyBackend(trajectory)
    count = backend.count_frames()
    assert count == 5
    assert len(backend) == 5


def test_count_frames_single(single_frame):
    backend = ASEReadOnlyBackend(single_frame)
    assert backend.count_frames() == 1


# =============================================================================
# read_row
# =============================================================================


def test_read_row(trajectory):
    backend = ASEReadOnlyBackend(trajectory)
    row = backend.read_row(0)
    assert "arrays.numbers" in row
    assert "arrays.positions" in row
    assert np.array_equal(row["arrays.numbers"], [1, 1, 8])


def test_read_row_with_keys(trajectory):
    backend = ASEReadOnlyBackend(trajectory)
    row = backend.read_row(0, keys=["arrays.positions"])
    assert "arrays.positions" in row
    assert "arrays.numbers" not in row


def test_read_row_negative_index(trajectory):
    """Negative indices are passed through to ase.io.read."""
    backend = ASEReadOnlyBackend(trajectory)
    row = backend.read_row(-1)
    assert "arrays.positions" in row
    # Last frame has positions shifted by 4 * 0.1
    assert row["arrays.positions"][0, 0] == pytest.approx(0.4)


def test_read_row_out_of_bounds(trajectory):
    backend = ASEReadOnlyBackend(trajectory)
    with pytest.raises(IndexError):
        backend.read_row(100)


# =============================================================================
# Caching
# =============================================================================


def test_cache_hit(trajectory):
    backend = ASEReadOnlyBackend(trajectory)
    row1 = backend.read_row(0)
    row2 = backend.read_row(0)
    assert row1 is row2  # Same object from cache


def test_cache_eviction(trajectory):
    backend = ASEReadOnlyBackend(trajectory, cache_size=2)
    backend.read_row(0)
    backend.read_row(1)
    backend.read_row(2)  # Evicts frame 0
    assert 0 not in backend._cache
    assert 1 in backend._cache
    assert 2 in backend._cache


def test_cache_lru_order(trajectory):
    backend = ASEReadOnlyBackend(trajectory, cache_size=2)
    backend.read_row(0)
    backend.read_row(1)
    backend.read_row(0)  # Access 0 again, making 1 the oldest
    backend.read_row(2)  # Evicts frame 1 (oldest)
    assert 0 in backend._cache
    assert 1 not in backend._cache
    assert 2 in backend._cache


def test_cache_negative_index_normalized(trajectory):
    """Negative indices are normalized to positive cache keys when length known."""
    backend = ASEReadOnlyBackend(trajectory)
    backend.count_frames()  # length = 5
    backend.read_row(-1)  # Should cache under key 4
    assert 4 in backend._cache
    assert -1 not in backend._cache


def test_length_auto_discovery(trajectory):
    """Reading frames 0..N then N+1 (fail) auto-discovers length."""
    backend = ASEReadOnlyBackend(trajectory)
    for i in range(5):
        backend.read_row(i)
    with pytest.raises(IndexError):
        backend.read_row(5)
    assert len(backend) == 5


# =============================================================================
# read_rows
# =============================================================================


def test_read_rows(trajectory):
    backend = ASEReadOnlyBackend(trajectory)
    rows = backend.read_rows([0, 2, 4])
    assert len(rows) == 3
    assert all("arrays.positions" in r for r in rows)


# =============================================================================
# iter_rows
# =============================================================================


def test_iter_rows_sequential(trajectory):
    """Sequential indices use ase.io.iread optimization."""
    backend = ASEReadOnlyBackend(trajectory)
    rows = list(backend.iter_rows([0, 1, 2, 3, 4]))
    assert len(rows) == 5


def test_iter_rows_sequential_subset(trajectory):
    """Sorted subset starting from 0 also uses iread optimization."""
    backend = ASEReadOnlyBackend(trajectory)
    rows = list(backend.iter_rows([0, 2, 4]))
    assert len(rows) == 3


def test_iter_rows_random(trajectory):
    """Non-sequential indices fall back to per-frame reads."""
    backend = ASEReadOnlyBackend(trajectory)
    rows = list(backend.iter_rows([4, 1, 3]))
    assert len(rows) == 3


def test_iter_rows_with_keys(trajectory):
    backend = ASEReadOnlyBackend(trajectory)
    rows = list(backend.iter_rows([0, 1], keys=["arrays.positions"]))
    assert all("arrays.positions" in r for r in rows)
    assert all("arrays.numbers" not in r for r in rows)


# =============================================================================
# columns
# =============================================================================


def test_columns(trajectory):
    backend = ASEReadOnlyBackend(trajectory)
    cols = backend.columns()
    assert "arrays.numbers" in cols
    assert "arrays.positions" in cols
    assert "cell" in cols
    assert "pbc" in cols


# =============================================================================
# read_column
# =============================================================================


def test_read_column(trajectory):
    backend = ASEReadOnlyBackend(trajectory)
    backend.count_frames()  # Need length for default indices
    positions = backend.read_column("arrays.positions")
    assert len(positions) == 5


def test_read_column_with_indices(trajectory):
    backend = ASEReadOnlyBackend(trajectory)
    positions = backend.read_column("arrays.positions", indices=[0, 2])
    assert len(positions) == 2


# =============================================================================
# Registry auto-detection
# =============================================================================


def test_registry_xyz(trajectory):
    """ASEIO auto-selects ASEReadOnlyBackend for .xyz files."""
    db = asebytes.ASEIO(trajectory)
    assert isinstance(db._backend, ASEReadOnlyBackend)


def test_registry_extxyz(extxyz_trajectory):
    """ASEIO auto-selects ASEReadOnlyBackend for .extxyz files."""
    db = asebytes.ASEIO(extxyz_trajectory)
    assert isinstance(db._backend, ASEReadOnlyBackend)


def test_registry_xyz_readonly_false_raises(trajectory):
    """Explicitly requesting writable for .xyz raises TypeError."""
    with pytest.raises(TypeError, match="read-only"):
        asebytes.ASEIO(trajectory, readonly=False)


def test_registry_lmdb_auto_writable(tmp_path):
    """LMDB auto-selects writable backend with readonly=None."""
    from asebytes.lmdb import LMDBObjectBackend

    db = asebytes.ASEIO(str(tmp_path / "test.lmdb"))
    assert isinstance(db._backend, LMDBObjectBackend)


# =============================================================================
# ASEIO integration
# =============================================================================


def test_aseio_getitem_positive(trajectory):
    db = asebytes.ASEIO(trajectory)
    atoms = db[0]
    assert isinstance(atoms, Atoms)
    assert len(atoms) == 3


def test_aseio_getitem_negative_requires_length(trajectory):
    """Negative indexing requires known length."""
    db = asebytes.ASEIO(trajectory)
    with pytest.raises(TypeError, match="Length unknown"):
        db[-1]


def test_aseio_getitem_negative_after_count(trajectory):
    """Negative indexing works after count_frames()."""
    db = asebytes.ASEIO(trajectory)
    db._backend.count_frames()
    atoms = db[-1]
    assert isinstance(atoms, Atoms)


def test_aseio_getitem_out_of_bounds(trajectory):
    db = asebytes.ASEIO(trajectory)
    with pytest.raises(IndexError):
        db[100]


def test_aseio_slice_requires_count(trajectory):
    """Slicing requires known length."""
    db = asebytes.ASEIO(trajectory)
    with pytest.raises(TypeError, match="Length unknown"):
        db[:]


def test_aseio_slice_after_count(trajectory):
    db = asebytes.ASEIO(trajectory)
    db._backend.count_frames()
    view = db[:]
    assert len(view) == 5


def test_aseio_write_raises(trajectory):
    """Writing to a read-only backend raises TypeError."""
    db = asebytes.ASEIO(trajectory)
    atoms = Atoms("H", positions=[[0, 0, 0]])
    with pytest.raises(TypeError, match="read-only"):
        db[0] = atoms


def test_aseio_iter_discovers_length(trajectory):
    """Iterating through all frames discovers the length."""
    db = asebytes.ASEIO(trajectory)
    with pytest.raises(TypeError):
        len(db)
    frames = list(db)
    assert len(frames) == 5
    assert len(db) == 5


def test_aseio_info_preserved(trajectory):
    """Info dict survives round-trip through backend."""
    db = asebytes.ASEIO(trajectory)
    atoms = db[0]
    assert atoms.info["step"] == 0

    atoms4 = db[4]
    assert atoms4.info["step"] == 4


def test_aseio_columns_unknown_length(trajectory):
    """ASEIO.columns works even when length is unknown."""
    db = asebytes.ASEIO(trajectory)
    cols = db.columns
    assert "arrays.numbers" in cols
    assert "arrays.positions" in cols


def test_aseio_extxyz_info(extxyz_trajectory):
    db = asebytes.ASEIO(extxyz_trajectory)
    atoms = db[0]
    assert atoms.info["label"] == "frame_0"
