"""Tests for IndexError on out-of-bounds __getitem__ access.

All 6 facades (BlobIO, ObjectIO, ASEIO + async variants) must raise
IndexError when db[i] is called with i >= len(db) or i < -len(db).
None is reserved strictly for placeholder rows from reserve().

Tests use a mock "permissive" backend that returns None for OOB indices
instead of raising IndexError, to verify that the *facade* enforces bounds.
"""

from __future__ import annotations

from typing import Any

import ase
import pytest

from asebytes import ASEIO, BlobIO, ObjectIO
from asebytes._async_blob_io import AsyncBlobIO
from asebytes._async_io import AsyncASEIO
from asebytes._async_object_io import AsyncObjectIO
from asebytes._backends import ReadWriteBackend
from asebytes._async_backends import AsyncReadWriteBackend


# ---------------------------------------------------------------------------
# Mock backend that does NOT raise IndexError on OOB -- returns None
# ---------------------------------------------------------------------------


class _PermissiveBlobBackend(ReadWriteBackend[bytes, bytes]):
    """Backend that silently returns None for out-of-bounds get()."""

    def __init__(self, rows: list[dict[bytes, bytes] | None] | None = None):
        self._rows: list[dict[bytes, bytes] | None] = rows or []

    @staticmethod
    def list_groups(path: str, **kwargs) -> list[str]:
        return []

    def __len__(self) -> int:
        return len(self._rows)

    def get(self, index: int, keys=None) -> dict[bytes, bytes] | None:
        if 0 <= index < len(self._rows):
            return self._rows[index]
        return None  # permissive: no IndexError

    def set(self, index, data):
        self._rows[index] = data

    def delete(self, index):
        del self._rows[index]

    def insert(self, index, data):
        self._rows.insert(index, data)

    def extend(self, data):
        start = len(self._rows)
        self._rows.extend(data)
        return start

    def reserve(self, count):
        self._rows.extend([None] * count)

    def clear(self):
        self._rows.clear()

    def remove(self):
        self._rows.clear()


class _PermissiveObjectBackend(ReadWriteBackend[str, Any]):
    """Backend that silently returns None for out-of-bounds get()."""

    def __init__(self, rows: list[dict[str, Any] | None] | None = None):
        self._rows: list[dict[str, Any] | None] = rows or []

    @staticmethod
    def list_groups(path: str, **kwargs) -> list[str]:
        return []

    def __len__(self) -> int:
        return len(self._rows)

    def get(self, index: int, keys=None) -> dict[str, Any] | None:
        if 0 <= index < len(self._rows):
            return self._rows[index]
        return None  # permissive: no IndexError

    def keys(self, index: int) -> list[str]:
        row = self.get(index)
        return list(row.keys()) if row else []

    def set(self, index, data):
        self._rows[index] = data

    def delete(self, index):
        del self._rows[index]

    def insert(self, index, data):
        self._rows.insert(index, data)

    def extend(self, data):
        start = len(self._rows)
        self._rows.extend(data)
        return start

    def reserve(self, count):
        self._rows.extend([None] * count)

    def clear(self):
        self._rows.clear()

    def remove(self):
        self._rows.clear()


class _PermissiveAsyncBlobBackend(AsyncReadWriteBackend[bytes, bytes]):
    """Async backend that silently returns None for out-of-bounds get()."""

    def __init__(self, rows: list[dict[bytes, bytes] | None] | None = None):
        self._rows: list[dict[bytes, bytes] | None] = rows or []

    @staticmethod
    def list_groups(path: str, **kwargs) -> list[str]:
        return []

    async def len(self) -> int:
        return len(self._rows)

    async def get(self, index: int, keys=None) -> dict[bytes, bytes] | None:
        if 0 <= index < len(self._rows):
            return self._rows[index]
        return None  # permissive: no IndexError

    async def set(self, index, data):
        self._rows[index] = data

    async def delete(self, index):
        del self._rows[index]

    async def insert(self, index, data):
        self._rows.insert(index, data)

    async def extend(self, data):
        start = len(self._rows)
        self._rows.extend(data)
        return start

    async def reserve(self, count):
        self._rows.extend([None] * count)

    async def clear(self):
        self._rows.clear()

    async def remove(self):
        self._rows.clear()


class _PermissiveAsyncObjectBackend(AsyncReadWriteBackend[str, Any]):
    """Async backend that silently returns None for out-of-bounds get()."""

    def __init__(self, rows: list[dict[str, Any] | None] | None = None):
        self._rows: list[dict[str, Any] | None] = rows or []

    @staticmethod
    def list_groups(path: str, **kwargs) -> list[str]:
        return []

    async def len(self) -> int:
        return len(self._rows)

    async def get(self, index: int, keys=None) -> dict[str, Any] | None:
        if 0 <= index < len(self._rows):
            return self._rows[index]
        return None  # permissive: no IndexError

    async def keys(self, index: int) -> list[str]:
        row = await self.get(index)
        return list(row.keys()) if row else []

    async def set(self, index, data):
        self._rows[index] = data

    async def delete(self, index):
        del self._rows[index]

    async def insert(self, index, data):
        self._rows.insert(index, data)

    async def extend(self, data):
        start = len(self._rows)
        self._rows.extend(data)
        return start

    async def reserve(self, count):
        self._rows.extend([None] * count)

    async def clear(self):
        self._rows.clear()

    async def remove(self):
        self._rows.clear()


# ===========================================================================
# Sync facades -- mock backends (facade-level bounds enforcement)
# ===========================================================================


class TestBlobIOBoundsFacade:
    """BlobIO facade-level bounds checking with a permissive backend."""

    def _make(self, n: int = 2) -> BlobIO:
        rows = [{b"k": f"v{i}".encode()} for i in range(n)]
        return BlobIO(backend=_PermissiveBlobBackend(rows))

    def test_valid_positive_index(self):
        db = self._make(2)
        assert db[0] is not None
        assert db[1] is not None

    def test_valid_negative_index(self):
        db = self._make(2)
        assert db[-1] is not None
        assert db[-2] is not None

    def test_upper_bound_exact(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            db[2]

    def test_upper_bound_far(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            db[100]

    def test_lower_bound(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            db[-3]

    def test_empty_db(self):
        db = self._make(0)
        with pytest.raises(IndexError):
            db[0]

    def test_reserve_placeholder_returns_none(self):
        db = self._make(1)
        db.reserve(2)
        assert len(db) == 3
        # Placeholder rows via .get() return None (bypasses __getitem__)
        assert db.get(1) is None
        assert db.get(2) is None


class TestObjectIOBoundsFacade:
    """ObjectIO facade-level bounds checking with a permissive backend."""

    def _make(self, n: int = 2) -> ObjectIO:
        rows = [{"k": f"v{i}"} for i in range(n)]
        return ObjectIO(backend=_PermissiveObjectBackend(rows))

    def test_valid_positive_index(self):
        db = self._make(2)
        assert db[0] is not None
        assert db[1] is not None

    def test_valid_negative_index(self):
        db = self._make(2)
        assert db[-1] is not None
        assert db[-2] is not None

    def test_upper_bound_exact(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            db[2]

    def test_upper_bound_far(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            db[100]

    def test_lower_bound(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            db[-3]

    def test_empty_db(self):
        db = self._make(0)
        with pytest.raises(IndexError):
            db[0]

    def test_reserve_placeholder_returns_none(self):
        db = self._make(1)
        db.reserve(2)
        assert len(db) == 3
        assert db.get(1) is None
        assert db.get(2) is None


class TestASEIOBoundsFacade:
    """ASEIO facade-level bounds checking with a permissive backend.

    ASEIO wraps an object-level backend so we use _PermissiveObjectBackend.
    We store atoms_to_dict(simple_atoms) dicts so dict_to_atoms succeeds.
    """

    @staticmethod
    def _atoms_dict() -> dict[str, Any]:
        """Minimal dict that dict_to_atoms can reconstruct."""
        from asebytes._convert import atoms_to_dict
        return atoms_to_dict(ase.Atoms("H", positions=[[0, 0, 0]]))

    def _make(self, n: int = 2) -> ASEIO:
        rows = [self._atoms_dict() for _ in range(n)]
        return ASEIO(backend=_PermissiveObjectBackend(rows))

    def test_valid_positive_index(self):
        db = self._make(2)
        assert db[0] is not None
        assert db[1] is not None

    def test_valid_negative_index(self):
        db = self._make(2)
        assert db[-1] is not None
        assert db[-2] is not None

    def test_upper_bound_exact(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            db[2]

    def test_upper_bound_far(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            db[100]

    def test_lower_bound(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            db[-3]

    def test_empty_db(self):
        db = self._make(0)
        with pytest.raises(IndexError):
            db[0]

    def test_reserve_placeholder_returns_none(self):
        db = self._make(1)
        db.reserve(2)
        assert len(db) == 3
        assert db.get(1) is None
        assert db.get(2) is None


# ===========================================================================
# Async facades -- mock backends (facade-level bounds enforcement)
# ===========================================================================


class TestAsyncBlobIOBoundsFacade:
    """AsyncBlobIO facade-level bounds checking with a permissive backend."""

    def _make(self, n: int = 2) -> AsyncBlobIO:
        rows = [{b"k": f"v{i}".encode()} for i in range(n)]
        return AsyncBlobIO(backend=_PermissiveAsyncBlobBackend(rows))

    @pytest.mark.anyio
    async def test_valid_positive_index(self):
        db = self._make(2)
        assert await db[0] is not None
        assert await db[1] is not None

    @pytest.mark.anyio
    async def test_valid_negative_index(self):
        db = self._make(2)
        assert await db[-1] is not None
        assert await db[-2] is not None

    @pytest.mark.anyio
    async def test_upper_bound_exact(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            await db[2]

    @pytest.mark.anyio
    async def test_upper_bound_far(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            await db[100]

    @pytest.mark.anyio
    async def test_lower_bound(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            await db[-3]

    @pytest.mark.anyio
    async def test_empty_db(self):
        db = self._make(0)
        with pytest.raises(IndexError):
            await db[0]

    @pytest.mark.anyio
    async def test_reserve_placeholder_returns_none(self):
        db = self._make(1)
        await db.reserve(2)
        assert await db.len() == 3
        assert await db.get(1) is None
        assert await db.get(2) is None


class TestAsyncObjectIOBoundsFacade:
    """AsyncObjectIO facade-level bounds checking with a permissive backend."""

    def _make(self, n: int = 2) -> AsyncObjectIO:
        rows = [{"k": f"v{i}"} for i in range(n)]
        return AsyncObjectIO(backend=_PermissiveAsyncObjectBackend(rows))

    @pytest.mark.anyio
    async def test_valid_positive_index(self):
        db = self._make(2)
        assert await db[0] is not None
        assert await db[1] is not None

    @pytest.mark.anyio
    async def test_valid_negative_index(self):
        db = self._make(2)
        assert await db[-1] is not None
        assert await db[-2] is not None

    @pytest.mark.anyio
    async def test_upper_bound_exact(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            await db[2]

    @pytest.mark.anyio
    async def test_upper_bound_far(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            await db[100]

    @pytest.mark.anyio
    async def test_lower_bound(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            await db[-3]

    @pytest.mark.anyio
    async def test_empty_db(self):
        db = self._make(0)
        with pytest.raises(IndexError):
            await db[0]

    @pytest.mark.anyio
    async def test_reserve_placeholder_returns_none(self):
        db = self._make(1)
        await db.reserve(2)
        assert await db.len() == 3
        assert await db.get(1) is None
        assert await db.get(2) is None


class TestAsyncASEIOBoundsFacade:
    """AsyncASEIO facade-level bounds checking with a permissive backend."""

    @staticmethod
    def _atoms_dict() -> dict[str, Any]:
        from asebytes._convert import atoms_to_dict
        return atoms_to_dict(ase.Atoms("H", positions=[[0, 0, 0]]))

    def _make(self, n: int = 2) -> AsyncASEIO:
        rows = [self._atoms_dict() for _ in range(n)]
        return AsyncASEIO(backend=_PermissiveAsyncObjectBackend(rows))

    @pytest.mark.anyio
    async def test_valid_positive_index(self):
        db = self._make(2)
        assert await db[0] is not None
        assert await db[1] is not None

    @pytest.mark.anyio
    async def test_valid_negative_index(self):
        db = self._make(2)
        assert await db[-1] is not None
        assert await db[-2] is not None

    @pytest.mark.anyio
    async def test_upper_bound_exact(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            await db[2]

    @pytest.mark.anyio
    async def test_upper_bound_far(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            await db[100]

    @pytest.mark.anyio
    async def test_lower_bound(self):
        db = self._make(2)
        with pytest.raises(IndexError):
            await db[-3]

    @pytest.mark.anyio
    async def test_empty_db(self):
        db = self._make(0)
        with pytest.raises(IndexError):
            await db[0]

    @pytest.mark.anyio
    async def test_reserve_placeholder_returns_none(self):
        db = self._make(1)
        await db.reserve(2)
        assert await db.len() == 3
        assert await db.get(1) is None
        assert await db.get(2) is None


# ===========================================================================
# Real-backend integration tests (LMDB)
# ===========================================================================


def _make_blob_db(tmp_path, n_rows: int = 2) -> BlobIO:
    """Create a BlobIO with n_rows rows (LMDB)."""
    path = str(tmp_path / "bounds_blob.lmdb")
    db = BlobIO(path)
    for i in range(n_rows):
        db.append({b"k": f"v{i}".encode()})
    return db


def _make_object_db(tmp_path, n_rows: int = 2) -> ObjectIO:
    """Create an ObjectIO with n_rows rows (LMDB)."""
    path = str(tmp_path / "bounds_object.lmdb")
    db = ObjectIO(path)
    for i in range(n_rows):
        db.append({"k": f"v{i}"})
    return db


def _make_ase_db(tmp_path, simple_atoms, n_rows: int = 2) -> ASEIO:
    """Create an ASEIO with n_rows rows (LMDB)."""
    path = str(tmp_path / "bounds_ase.lmdb")
    db = ASEIO(path)
    for _ in range(n_rows):
        db.append(simple_atoms)
    return db


class TestBlobIOBoundsLMDB:
    """BlobIO bounds checking with real LMDB backend."""

    def test_valid_positive_index(self, tmp_path):
        db = _make_blob_db(tmp_path, 2)
        assert db[0] is not None
        assert db[1] is not None

    def test_valid_negative_index(self, tmp_path):
        db = _make_blob_db(tmp_path, 2)
        assert db[-1] is not None
        assert db[-2] is not None

    def test_upper_bound_exact(self, tmp_path):
        db = _make_blob_db(tmp_path, 2)
        with pytest.raises(IndexError):
            db[2]

    def test_upper_bound_far(self, tmp_path):
        db = _make_blob_db(tmp_path, 2)
        with pytest.raises(IndexError):
            db[100]

    def test_lower_bound(self, tmp_path):
        db = _make_blob_db(tmp_path, 2)
        with pytest.raises(IndexError):
            db[-3]

    def test_empty_db(self, tmp_path):
        db = _make_blob_db(tmp_path, 0)
        with pytest.raises(IndexError):
            db[0]

    def test_reserve_placeholder_returns_none(self, tmp_path):
        db = _make_blob_db(tmp_path, 1)
        db.reserve(2)
        assert len(db) == 3
        assert db.get(1) is None
        assert db.get(2) is None


class TestObjectIOBoundsLMDB:
    """ObjectIO bounds checking with real LMDB backend."""

    def test_valid_positive_index(self, tmp_path):
        db = _make_object_db(tmp_path, 2)
        assert db[0] is not None

    def test_upper_bound_exact(self, tmp_path):
        db = _make_object_db(tmp_path, 2)
        with pytest.raises(IndexError):
            db[2]

    def test_empty_db(self, tmp_path):
        db = _make_object_db(tmp_path, 0)
        with pytest.raises(IndexError):
            db[0]


class TestASEIOBoundsLMDB:
    """ASEIO bounds checking with real LMDB backend."""

    def test_valid_positive_index(self, tmp_path, simple_atoms):
        db = _make_ase_db(tmp_path, simple_atoms, 2)
        assert db[0] is not None

    def test_upper_bound_exact(self, tmp_path, simple_atoms):
        db = _make_ase_db(tmp_path, simple_atoms, 2)
        with pytest.raises(IndexError):
            db[2]

    def test_empty_db(self, tmp_path, simple_atoms):
        db = _make_ase_db(tmp_path, simple_atoms, 0)
        with pytest.raises(IndexError):
            db[0]

    def test_reserve_placeholder_returns_none(self, tmp_path, simple_atoms):
        db = _make_ase_db(tmp_path, simple_atoms, 1)
        db.reserve(2)
        assert len(db) == 3
        assert db.get(1) is None
        assert db.get(2) is None
