"""Tests for the ColumnarStore protocol and HDF5/Zarr implementations."""

from __future__ import annotations

import numpy as np
import pytest

from asebytes.columnar._store import HDF5Store, ZarrStore


@pytest.fixture(params=["hdf5", "zarr"], ids=["HDF5Store", "ZarrStore"])
def store(tmp_path, request):
    """Parametrised fixture yielding both store types."""
    if request.param == "hdf5":
        s = HDF5Store(tmp_path / "test.h5", group="grp")
    else:
        s = ZarrStore(tmp_path / "test.zarr", group="grp")
    yield s
    s.close()


class TestRoundTrip:
    """Create → read → append → read → write_slice → read."""

    def test_create_and_read(self, store):
        data = np.arange(10, dtype=np.float64)
        store.create_array("x", data)
        got = store.get_array("x")
        np.testing.assert_array_equal(got, data)

    def test_create_2d(self, store):
        data = np.random.default_rng(0).random((5, 3))
        store.create_array("pos", data)
        got = store.get_array("pos")
        np.testing.assert_allclose(got, data)

    def test_append(self, store):
        d1 = np.array([1.0, 2.0, 3.0])
        d2 = np.array([4.0, 5.0])
        store.create_array("x", d1)
        store.append_array("x", d2)
        got = store.get_array("x")
        np.testing.assert_array_equal(got, np.array([1.0, 2.0, 3.0, 4.0, 5.0]))

    def test_append_2d(self, store):
        d1 = np.ones((3, 2))
        d2 = np.zeros((2, 2))
        store.create_array("m", d1)
        store.append_array("m", d2)
        got = store.get_array("m")
        assert got.shape == (5, 2)
        np.testing.assert_array_equal(got[:3], d1)
        np.testing.assert_array_equal(got[3:], d2)

    def test_get_slice_int(self, store):
        data = np.arange(10, dtype=np.float64)
        store.create_array("x", data)
        got = store.get_slice("x", 3)
        assert float(got) == 3.0

    def test_get_slice_range(self, store):
        data = np.arange(10, dtype=np.float64)
        store.create_array("x", data)
        got = store.get_slice("x", slice(2, 5))
        np.testing.assert_array_equal(got, np.array([2.0, 3.0, 4.0]))

    def test_get_slice_fancy(self, store):
        data = np.arange(10, dtype=np.float64)
        store.create_array("x", data)
        got = store.get_slice("x", [0, 3, 7])
        np.testing.assert_array_equal(got, np.array([0.0, 3.0, 7.0]))

    def test_write_slice(self, store):
        data = np.zeros(5, dtype=np.float64)
        store.create_array("x", data)
        store.write_slice("x", 2, 99.0)
        got = store.get_array("x")
        assert got[2] == 99.0

    def test_write_slice_range(self, store):
        data = np.zeros(5, dtype=np.float64)
        store.create_array("x", data)
        store.write_slice("x", slice(1, 3), np.array([10.0, 20.0]))
        got = store.get_array("x")
        np.testing.assert_array_equal(got, np.array([0.0, 10.0, 20.0, 0.0, 0.0]))


class TestMetadata:
    def test_has_array(self, store):
        assert not store.has_array("x")
        store.create_array("x", np.array([1.0]))
        assert store.has_array("x")

    def test_list_arrays(self, store):
        store.create_array("a", np.array([1.0]))
        store.create_array("b", np.array([2.0]))
        names = store.list_arrays()
        assert set(names) == {"a", "b"}

    def test_get_shape_dtype(self, store):
        data = np.zeros((4, 3), dtype=np.float32)
        store.create_array("m", data)
        assert store.get_shape("m") == (4, 3)
        assert store.get_dtype("m") == np.float32

    def test_attrs_roundtrip(self, store):
        store.set_attrs({"n_frames": 10, "version": "1.0"})
        attrs = store.get_attrs()
        assert attrs["n_frames"] == 10
        assert attrs["version"] == "1.0"


class TestListGroups:
    def test_hdf5_list_groups(self, tmp_path):
        import h5py
        p = tmp_path / "test.h5"
        with h5py.File(str(p), "w") as f:
            f.create_group("grp1")
            f.create_group("grp2")
        groups = HDF5Store.list_groups(str(p))
        assert set(groups) == {"grp1", "grp2"}

    def test_hdf5_list_groups_empty(self, tmp_path):
        assert HDF5Store.list_groups(str(tmp_path / "nonexist.h5")) == []

    def test_zarr_list_groups(self, tmp_path):
        s1 = ZarrStore(tmp_path / "test.zarr", group="grpA")
        s1.set_attrs({"test": 1})
        s1.close()
        s2 = ZarrStore(tmp_path / "test.zarr", group="grpB")
        s2.set_attrs({"test": 2})
        s2.close()
        groups = ZarrStore.list_groups(str(tmp_path / "test.zarr"))
        assert set(groups) == {"grpA", "grpB"}

    def test_zarr_list_groups_empty(self, tmp_path):
        assert ZarrStore.list_groups(str(tmp_path / "nonexist.zarr")) == []


class TestDtypePreservation:
    def test_int32(self, store):
        data = np.array([1, 2, 3], dtype=np.int32)
        store.create_array("i", data, dtype=np.int32)
        assert store.get_dtype("i") == np.int32
        np.testing.assert_array_equal(store.get_array("i"), data)

    def test_int64(self, store):
        data = np.array([100, 200], dtype=np.int64)
        store.create_array("j", data, dtype=np.int64)
        assert store.get_dtype("j") == np.int64

    def test_fill_value(self, store):
        data = np.array([1.0, 2.0])
        store.create_array("f", data, fill_value=np.nan)
        got = store.get_array("f")
        np.testing.assert_array_equal(got, data)
