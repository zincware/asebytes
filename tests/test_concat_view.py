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
