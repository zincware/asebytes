"""Integration tests for ASEIO with HuggingFace backends (via instance and URI)."""

from __future__ import annotations

import numpy as np
import pytest

datasets = pytest.importorskip("datasets")

from asebytes import ASEIO
from asebytes.hf import COLABFIT, ColumnMapping, HuggingFaceBackend


# ── Helpers ────────────────────────────────────────────────────────────────


def _make_dataset(n: int = 5) -> datasets.Dataset:
    """Create a small in-memory HF Dataset with ColabFit-style columns."""
    return datasets.Dataset.from_dict(
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
        }
    )


# ── ASEIO from HuggingFaceBackend instance (no URI) ───────────────────────


class TestASEIOFromBackendInstance:
    """Pass a pre-built HuggingFaceBackend to ASEIO (no URI dispatch)."""

    @pytest.fixture()
    def io(self) -> ASEIO:
        ds = _make_dataset(5)
        backend = HuggingFaceBackend(ds, mapping=COLABFIT)
        return ASEIO(backend)

    def test_len(self, io):
        assert len(io) == 5

    def test_getitem_int(self, io):
        atoms = io[0]
        assert len(atoms) == 1  # 1 atom per frame
        np.testing.assert_array_almost_equal(
            atoms.get_positions(), [[0.0, 0.0, 0.0]]
        )

    def test_getitem_int_content(self, io):
        """Atoms from index 2 should have positions [[2.0, 0.0, 0.0]]."""
        atoms = io[2]
        np.testing.assert_array_almost_equal(
            atoms.get_positions(), [[2.0, 0.0, 0.0]]
        )

    def test_getitem_slice(self, io):
        view = io[1:3]
        atoms_list = list(view)
        assert len(atoms_list) == 2
        np.testing.assert_array_almost_equal(
            atoms_list[0].get_positions(), [[1.0, 0.0, 0.0]]
        )
        np.testing.assert_array_almost_equal(
            atoms_list[1].get_positions(), [[2.0, 0.0, 0.0]]
        )

    def test_column_access(self, io):
        col = io["calc.energy"]
        values = list(col)
        assert values == [0.0, -1.0, -2.0, -3.0, -4.0]

    def test_iteration(self, io):
        atoms_list = list(io)
        assert len(atoms_list) == 5
        for i, atoms in enumerate(atoms_list):
            np.testing.assert_array_almost_equal(
                atoms.get_positions(), [[float(i), 0.0, 0.0]]
            )

    def test_readonly_setitem_raises(self, io):
        """HuggingFaceBackend is read-only; __setitem__ should raise."""
        import ase

        atoms = ase.Atoms("H", positions=[[0, 0, 0]])
        with pytest.raises(TypeError, match="[Rr]ead.only"):
            io[0] = atoms

    def test_readonly_delitem_raises(self, io):
        with pytest.raises(TypeError, match="[Rr]ead.only"):
            del io[0]

    def test_readonly_insert_raises(self, io):
        import ase

        atoms = ase.Atoms("H", positions=[[0, 0, 0]])
        with pytest.raises(TypeError, match="[Rr]ead.only"):
            io.insert(0, atoms)

    def test_columns_property(self, io):
        cols = io.columns
        assert "arrays.positions" in cols
        assert "arrays.numbers" in cols
        assert "calc.energy" in cols
        assert "cell" in cols
        assert "pbc" in cols

    def test_negative_index(self, io):
        atoms = io[-1]
        np.testing.assert_array_almost_equal(
            atoms.get_positions(), [[4.0, 0.0, 0.0]]
        )


# ── ASEIO from URI (mock load_dataset) ────────────────────────────────────


class TestASEIOFromURI:
    """Construct ASEIO with a URI string; verify from_uri dispatch."""

    def test_colabfit_uri(self, monkeypatch):
        """ASEIO('colabfit://test_dataset') should stream by default."""
        calls = []

        def fake_load(path, *, streaming=False, split=None, **kwargs):
            calls.append(
                {"path": path, "streaming": streaming, "split": split, **kwargs}
            )
            if streaming:
                return _make_dataset(3).to_iterable_dataset()
            return _make_dataset(3)

        monkeypatch.setattr(
            "asebytes.hf._backend.load_dataset", fake_load
        )
        io = ASEIO("colabfit://test_dataset")

        # Verify load_dataset was called with correct path and streaming
        assert len(calls) == 1
        assert calls[0]["path"] == "colabfit/test_dataset"
        assert calls[0]["streaming"] is True

        # Verify data access works (streaming — iterate to get data)
        atoms = io[0]
        assert len(atoms) == 1
        np.testing.assert_array_almost_equal(
            atoms.get_positions(), [[0.0, 0.0, 0.0]]
        )

    def test_hf_uri_with_mapping(self, monkeypatch):
        """ASEIO('hf://user/dataset', mapping=mapping) streams by default."""
        calls = []

        def fake_load(path, *, streaming=False, split=None, **kwargs):
            calls.append(
                {"path": path, "streaming": streaming, "split": split}
            )
            if streaming:
                return _make_dataset(2).to_iterable_dataset()
            return _make_dataset(2)

        monkeypatch.setattr(
            "asebytes.hf._backend.load_dataset", fake_load
        )
        mapping = ColumnMapping(positions="positions", numbers="atomic_numbers")
        io = ASEIO("hf://user/dataset", mapping=mapping)

        assert len(calls) == 1
        assert calls[0]["path"] == "user/dataset"
        assert calls[0]["streaming"] is True

        # Streaming: iterate to access
        atoms = io[1]
        np.testing.assert_array_almost_equal(
            atoms.get_positions(), [[1.0, 0.0, 0.0]]
        )

    def test_hf_uri_with_streaming(self, monkeypatch):
        """ASEIO('hf://user/dataset', mapping=m, streaming=True) should work."""
        calls = []

        def fake_load(path, *, streaming=False, split=None, **kwargs):
            calls.append(
                {"path": path, "streaming": streaming, "split": split}
            )
            if streaming:
                return _make_dataset(3).to_iterable_dataset()
            return _make_dataset(3)

        monkeypatch.setattr(
            "asebytes.hf._backend.load_dataset", fake_load
        )
        mapping = ColumnMapping(positions="positions", numbers="atomic_numbers")
        io = ASEIO("hf://user/dataset", mapping=mapping, streaming=True)

        assert len(calls) == 1
        assert calls[0]["streaming"] is True

        # Streaming: len is unknown, but iteration should work
        atoms_list = list(io)
        assert len(atoms_list) == 3

    def test_file_path_still_works(self, tmp_path):
        """Regular file paths should still use the old code path."""
        import asebytes

        io = asebytes.ASEIO(str(tmp_path / "test.lmdb"), prefix=b"atoms/")
        assert len(io) == 0  # fresh LMDB, zero rows

    def test_hf_uri_without_mapping_raises(self, monkeypatch):
        """hf:// without mapping should raise ValueError."""

        def fake_load(path, *, streaming=False, split=None, **kwargs):
            return _make_dataset(2)

        monkeypatch.setattr(
            "asebytes.hf._backend.load_dataset", fake_load
        )
        with pytest.raises(ValueError, match="mapping"):
            ASEIO("hf://user/dataset")

    def test_colabfit_uri_with_split(self, monkeypatch):
        """split kwarg should be forwarded through ASEIO -> from_uri."""
        calls = []

        def fake_load(path, *, streaming=False, split=None, **kwargs):
            calls.append(
                {"path": path, "streaming": streaming, "split": split}
            )
            if streaming:
                return _make_dataset(2).to_iterable_dataset()
            return _make_dataset(2)

        monkeypatch.setattr(
            "asebytes.hf._backend.load_dataset", fake_load
        )
        io = ASEIO("colabfit://test_dataset", split="train")

        assert calls[0]["split"] == "train"
        atoms = io[0]
        assert len(atoms) == 1
