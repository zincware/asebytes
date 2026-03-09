"""Tests for ConcatView — lazy read-only concatenation of IO facades."""
import uuid
import pytest

import asebytes
from asebytes import ObjectIO, ConcatView
from asebytes.memory import MemoryObjectBackend
from asebytes._views import RowView, ColumnView


def _fresh_object_io(rows: list[dict]) -> ObjectIO:
    """Create an ObjectIO backed by a fresh MemoryObjectBackend."""
    backend = MemoryObjectBackend(str(uuid.uuid4()))
    io = ObjectIO(backend)
    io.extend(rows)
    return io


# ---------------------------------------------------------------------------
# ObjectIO concat
# ---------------------------------------------------------------------------

@pytest.fixture
def three_object_ios():
    io1 = _fresh_object_io([{"x": 0}, {"x": 1}])
    io2 = _fresh_object_io([{"x": 2}, {"x": 3}])
    io3 = _fresh_object_io([{"x": 4}])
    return io1, io2, io3


def test_object_concat_sum(three_object_ios):
    io1, io2, io3 = three_object_ios
    cat = sum([io1, io2, io3], [])
    assert isinstance(cat, ConcatView)


def test_object_concat_len(three_object_ios):
    io1, io2, io3 = three_object_ios
    cat = io1 + io2 + io3
    assert len(cat) == 5


def test_object_concat_iter(three_object_ios):
    io1, io2, io3 = three_object_ios
    cat = io1 + io2 + io3
    values = [row["x"] for row in cat]
    assert values == [0, 1, 2, 3, 4]


def test_object_concat_getitem_int(three_object_ios):
    io1, io2, io3 = three_object_ios
    cat = io1 + io2 + io3
    assert cat[0] == {"x": 0}
    assert cat[2] == {"x": 2}
    assert cat[4] == {"x": 4}
    assert cat[-1] == {"x": 4}
    assert cat[-5] == {"x": 0}


def test_object_concat_getitem_int_oob(three_object_ios):
    io1, io2, io3 = three_object_ios
    cat = io1 + io2 + io3
    with pytest.raises(IndexError):
        _ = cat[5]
    with pytest.raises(IndexError):
        _ = cat[-6]


def test_object_concat_getitem_slice(three_object_ios):
    io1, io2, io3 = three_object_ios
    cat = io1 + io2 + io3
    view = cat[1:4]
    assert isinstance(view, RowView)
    assert len(view) == 3
    assert [row["x"] for row in view] == [1, 2, 3]


def test_object_concat_getitem_list_int(three_object_ios):
    io1, io2, io3 = three_object_ios
    cat = io1 + io2 + io3
    view = cat[[0, 2, 4]]
    assert isinstance(view, RowView)
    assert [row["x"] for row in view] == [0, 2, 4]


def test_object_concat_getitem_str(three_object_ios):
    io1, io2, io3 = three_object_ios
    cat = io1 + io2 + io3
    col = cat["x"]
    assert isinstance(col, ColumnView)
    assert list(col) == [0, 1, 2, 3, 4]


def test_object_concat_flat_chaining(three_object_ios):
    io1, io2, io3 = three_object_ios
    cat = io1 + io2 + io3
    # Must be flat — one ConcatView with 3 sources, not nested
    assert len(cat._sources) == 3


def test_object_concat_concat_concat(three_object_ios):
    io1, io2, io3 = three_object_ios
    left = io1 + io2
    right = io2 + io3  # io2 appears in both; that's fine
    combined = left + right
    assert len(combined._sources) == 4
    assert len(combined) == 7


def test_object_concat_write_raises(three_object_ios):
    io1, io2, io3 = three_object_ios
    cat = io1 + io2 + io3
    view = cat[1:3]
    with pytest.raises(TypeError, match="read-only"):
        view.set([{"x": 99}, {"x": 99}])


def test_object_concat_mixed_type_raises():
    io_obj = _fresh_object_io([{"x": 0}])
    from asebytes._concat import ConcatView
    with pytest.raises(TypeError):
        ConcatView([io_obj, "not_an_io"])


def test_object_concat_read_rows_preserves_order(three_object_ios):
    """Indices spanning multiple sources must return rows in correct order."""
    io1, io2, io3 = three_object_ios
    cat = io1 + io2 + io3
    # Interleaved: indices 0 (src0), 2 (src1), 1 (src0), 4 (src2), 3 (src1)
    view = cat[[0, 2, 1, 4, 3]]
    assert [row["x"] for row in view] == [0, 2, 1, 4, 3]


# ---------------------------------------------------------------------------
# ASEIO concat
# ---------------------------------------------------------------------------

import ase


def _fresh_ase_io(atoms_list: list, tmp_path_factory) -> "asebytes.ASEIO":
    from asebytes import ASEIO

    p = str(tmp_path_factory.mktemp("aseio") / "data.lmdb")
    io = ASEIO(p)
    io.extend(atoms_list)
    return io


@pytest.fixture
def three_ase_ios(tmp_path_factory):
    a1 = ase.Atoms("H", positions=[[0, 0, 0]])
    a2 = ase.Atoms("H", positions=[[1, 0, 0]])
    a3 = ase.Atoms("H", positions=[[2, 0, 0]])
    io1 = _fresh_ase_io([a1, a2], tmp_path_factory)
    io2 = _fresh_ase_io([a3], tmp_path_factory)
    return io1, io2


def test_ase_concat_sum(three_ase_ios):
    io1, io2 = three_ase_ios
    cat = sum([io1, io2], [])
    assert isinstance(cat, ConcatView)
    assert len(cat) == 3


def test_ase_concat_iter(three_ase_ios):
    io1, io2 = three_ase_ios
    cat = io1 + io2
    atoms = list(cat)
    assert all(isinstance(a, ase.Atoms) for a in atoms)
    assert len(atoms) == 3


def test_ase_concat_getitem_int(three_ase_ios):
    io1, io2 = three_ase_ios
    cat = io1 + io2
    a = cat[2]
    assert isinstance(a, ase.Atoms)
    assert a.positions[0][0] == pytest.approx(2.0)


def test_ase_concat_getitem_slice(three_ase_ios):
    io1, io2 = three_ase_ios
    cat = io1 + io2
    view = cat[1:]
    assert len(view) == 2
    atoms = list(view)
    assert all(isinstance(a, ase.Atoms) for a in atoms)


def test_ase_concat_flat(three_ase_ios):
    io1, io2 = three_ase_ios
    cat = io1 + io2
    assert len(cat._sources) == 2


def test_ase_concat_column_view_type(three_ase_ios):
    from asebytes._views import ASEColumnView

    io1, io2 = three_ase_ios
    cat = io1 + io2
    assert cat._column_view_cls is ASEColumnView


# ---------------------------------------------------------------------------
# BlobIO concat
# ---------------------------------------------------------------------------

from asebytes import BlobIO


def _fresh_blob_io(rows: list[dict], tmp_path_factory) -> BlobIO:
    from asebytes.lmdb import LMDBBlobBackend

    p = str(tmp_path_factory.mktemp("blobio") / "data.lmdb")
    backend = LMDBBlobBackend(p)
    io = BlobIO(backend)
    for row in rows:
        io.append(row)
    return io


@pytest.fixture
def three_blob_ios(tmp_path_factory):
    io1 = _fresh_blob_io([{b"k": b"0"}, {b"k": b"1"}], tmp_path_factory)
    io2 = _fresh_blob_io([{b"k": b"2"}], tmp_path_factory)
    return io1, io2


def test_blob_concat_sum(three_blob_ios):
    io1, io2 = three_blob_ios
    cat = sum([io1, io2], [])
    assert isinstance(cat, ConcatView)
    assert len(cat) == 3


def test_blob_concat_iter(three_blob_ios):
    io1, io2 = three_blob_ios
    cat = io1 + io2
    rows = list(cat)
    assert rows == [{b"k": b"0"}, {b"k": b"1"}, {b"k": b"2"}]


def test_blob_concat_getitem_int(three_blob_ios):
    io1, io2 = three_blob_ios
    cat = io1 + io2
    assert cat[0] == {b"k": b"0"}
    assert cat[-1] == {b"k": b"2"}


def test_blob_concat_getitem_slice(three_blob_ios):
    io1, io2 = three_blob_ios
    cat = io1 + io2
    view = cat[1:]
    assert len(view) == 2


def test_blob_concat_flat(three_blob_ios):
    io1, io2 = three_blob_ios
    cat = io1 + io2
    assert len(cat._sources) == 2


# ---------------------------------------------------------------------------
# Cross-type rejection
# ---------------------------------------------------------------------------


def test_cross_type_aseio_plus_objectio(three_ase_ios):
    io_ase, _ = three_ase_ios
    io_obj = _fresh_object_io([{"x": 0}])
    with pytest.raises(TypeError):
        _ = io_ase + io_obj


def test_cross_type_objectio_plus_blobio(three_blob_ios):
    _, io_blob = three_blob_ios
    io_obj = _fresh_object_io([{"x": 0}])
    with pytest.raises(TypeError):
        _ = io_obj + io_blob


def test_cross_type_aseio_plus_blobio(three_ase_ios, three_blob_ios):
    io_ase, _ = three_ase_ios
    _, io_blob = three_blob_ios
    with pytest.raises(TypeError):
        _ = io_ase + io_blob
