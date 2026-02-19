"""Tests for HuggingFaceBackend (downloaded and streaming modes)."""

from __future__ import annotations

import numpy as np
import pytest

datasets = pytest.importorskip("datasets")

from asebytes.hf import COLABFIT, OPTIMADE, ColumnMapping
from asebytes.hf._backend import HuggingFaceBackend


# ── Helpers ────────────────────────────────────────────────────────────────


def _make_dataset(n: int = 5) -> datasets.Dataset:
    """Create a small in-memory HF Dataset with ColabFit-style columns."""
    return datasets.Dataset.from_dict(
        {
            "positions": [[[float(i), 0.0, 0.0]] for i in range(n)],
            "atomic_numbers": [[1] for _ in range(n)],
            "cell": [[[10.0, 0, 0], [0, 10.0, 0], [0, 0, 10.0]] for _ in range(n)],
            "pbc": [[True, True, True] for _ in range(n)],
            "energy": [float(-i) for i in range(n)],
            "atomic_forces": [[[0.1 * i, 0.0, 0.0]] for i in range(n)],
            "cauchy_stress": [[0.0] * 6 for _ in range(n)],
            "configuration_name": [f"config_{i}" for i in range(n)],
        }
    )


# ── Downloaded-mode tests ─────────────────────────────────────────────────


class TestDownloadedBackend:
    """Tests for HuggingFaceBackend with a fully downloaded Dataset."""

    @pytest.fixture()
    def backend(self) -> HuggingFaceBackend:
        ds = _make_dataset(5)
        return HuggingFaceBackend(ds, mapping=COLABFIT)

    def test_len(self, backend):
        assert len(backend) == 5

    def test_read_row(self, backend):
        row = backend.read_row(0)
        assert "arrays.positions" in row
        assert "arrays.numbers" in row
        assert "cell" in row
        assert "pbc" in row
        assert "calc.energy" in row
        np.testing.assert_array_equal(
            row["arrays.positions"], np.array([[0.0, 0.0, 0.0]])
        )
        assert row["calc.energy"] == 0.0

    def test_read_row_with_keys(self, backend):
        row = backend.read_row(2, keys=["calc.energy", "arrays.positions"])
        assert set(row.keys()) == {"calc.energy", "arrays.positions"}
        assert row["calc.energy"] == -2.0

    def test_read_row_index_error(self, backend):
        with pytest.raises(IndexError):
            backend.read_row(100)

    def test_read_rows(self, backend):
        rows = backend.read_rows([0, 2, 4])
        assert len(rows) == 3
        assert rows[0]["calc.energy"] == 0.0
        assert rows[1]["calc.energy"] == -2.0
        assert rows[2]["calc.energy"] == -4.0

    def test_columns(self, backend):
        cols = backend.columns(0)
        assert isinstance(cols, list)
        assert "arrays.positions" in cols
        assert "calc.energy" in cols

    def test_read_column(self, backend):
        energies = backend.read_column("calc.energy", indices=[0, 1, 2])
        assert energies == [0.0, -1.0, -2.0]

    def test_unmapped_columns_go_to_info(self, backend):
        row = backend.read_row(0)
        assert "info.configuration_name" in row
        assert row["info.configuration_name"] == "config_0"

    def test_negative_index(self, backend):
        row = backend.read_row(-1)
        assert row["calc.energy"] == -4.0

    def test_iter_rows(self, backend):
        rows = list(backend.iter_rows([0, 1, 2]))
        assert len(rows) == 3
        assert rows[0]["calc.energy"] == 0.0
        assert rows[1]["calc.energy"] == -1.0

    def test_cache_hit(self, backend):
        """Reading the same row twice should hit the cache."""
        row1 = backend.read_row(0)
        row2 = backend.read_row(0)
        # Should return identical dicts (same object from cache)
        assert row1 is row2


# ── Streaming-mode tests ──────────────────────────────────────────────────


class TestStreamingBackend:
    """Tests for HuggingFaceBackend with an IterableDataset (streaming)."""

    @pytest.fixture()
    def backend(self) -> HuggingFaceBackend:
        ds = _make_dataset(5).to_iterable_dataset()
        return HuggingFaceBackend(ds, mapping=COLABFIT)

    def test_len_raises_type_error(self, backend):
        with pytest.raises(TypeError, match="[Ll]ength"):
            len(backend)

    def test_sequential_reads(self, backend):
        row0 = backend.read_row(0)
        row1 = backend.read_row(1)
        assert row0["calc.energy"] == 0.0
        assert row1["calc.energy"] == -1.0

    def test_iter_rows(self, backend):
        rows = list(backend.iter_rows([0, 1, 2]))
        assert len(rows) == 3
        assert rows[2]["calc.energy"] == -2.0

    def test_columns(self, backend):
        cols = backend.columns(0)
        assert "arrays.positions" in cols
        assert "calc.energy" in cols

    def test_length_discovered_after_full_iteration(self, backend):
        """After reading all rows, length should be discovered."""
        # Read all 5 rows
        for i in range(5):
            backend.read_row(i)
        # Now try to read one past the end to trigger length discovery
        with pytest.raises(IndexError):
            backend.read_row(5)
        # Length should now be known
        assert len(backend) == 5

    def test_backward_read_restarts_iterator(self, backend):
        """Reading backwards should restart the stream iterator."""
        row2 = backend.read_row(2)
        row0 = backend.read_row(0)  # should restart and re-read from cache
        assert row0["calc.energy"] == 0.0
        assert row2["calc.energy"] == -2.0


# ── from_uri tests ────────────────────────────────────────────────────────


class TestFromUri:
    """Tests for the HuggingFaceBackend.from_uri class method."""

    def test_hf_passes_path_directly(self, monkeypatch):
        """hf://user/dataset should pass 'user/dataset' to load_dataset."""
        calls = []

        def fake_load(path, *, streaming=False, split=None, **kwargs):
            calls.append({"path": path, "streaming": streaming, "split": split, **kwargs})
            if streaming:
                return _make_dataset(2).to_iterable_dataset()
            return _make_dataset(2)

        monkeypatch.setattr(
            "asebytes.hf._backend.load_dataset", fake_load
        )
        mapping = ColumnMapping(positions="positions", numbers="atomic_numbers")
        backend = HuggingFaceBackend.from_uri(
            "hf://user/dataset", mapping=mapping
        )
        assert calls[0]["path"] == "user/dataset"
        assert calls[0]["streaming"] is True

    def test_colabfit_auto_prepends_org(self, monkeypatch):
        """colabfit://dataset_name auto-prepends 'colabfit/' org."""
        calls = []

        def fake_load(path, *, streaming=False, split=None, **kwargs):
            calls.append({"path": path, "streaming": streaming, "split": split})
            if streaming:
                return _make_dataset(2).to_iterable_dataset()
            return _make_dataset(2)

        monkeypatch.setattr(
            "asebytes.hf._backend.load_dataset", fake_load
        )
        backend = HuggingFaceBackend.from_uri("colabfit://my_dataset")
        assert calls[0]["path"] == "colabfit/my_dataset"

    def test_colabfit_with_org_no_double_prepend(self, monkeypatch):
        """colabfit://org/dataset should NOT double-prepend."""
        calls = []

        def fake_load(path, *, streaming=False, split=None, **kwargs):
            calls.append({"path": path, "streaming": streaming, "split": split})
            if streaming:
                return _make_dataset(2).to_iterable_dataset()
            return _make_dataset(2)

        monkeypatch.setattr(
            "asebytes.hf._backend.load_dataset", fake_load
        )
        backend = HuggingFaceBackend.from_uri("colabfit://myorg/my_dataset")
        assert calls[0]["path"] == "myorg/my_dataset"

    def test_optimade_auto_selects_mapping(self, monkeypatch):
        """optimade:// should auto-select OPTIMADE mapping."""
        calls = []

        def fake_load(path, *, streaming=False, split=None, **kwargs):
            calls.append({"path": path, "streaming": streaming, "split": split})
            # Return dataset with OPTIMADE-style columns
            ds = datasets.Dataset.from_dict(
                {
                    "cartesian_site_positions": [[[0.0, 0.0, 0.0]]],
                    "species_at_sites": [["H"]],
                    "lattice_vectors": [[[10, 0, 0], [0, 10, 0], [0, 0, 10]]],
                    "dimension_types": [[1, 1, 1]],
                }
            )
            if streaming:
                return ds.to_iterable_dataset()
            return ds

        monkeypatch.setattr(
            "asebytes.hf._backend.load_dataset", fake_load
        )
        backend = HuggingFaceBackend.from_uri("optimade://provider/structures")
        assert calls[0]["path"] == "provider/structures"
        # Verify OPTIMADE mapping was applied
        row = backend.read_row(0)
        assert "arrays.positions" in row
        np.testing.assert_array_equal(
            row["arrays.numbers"], np.array([1])  # H -> 1
        )

    def test_streaming_false_forwarded(self, monkeypatch):
        """streaming=False (non-default) should be forwarded to load_dataset."""
        calls = []

        def fake_load(path, *, streaming=False, split=None, **kwargs):
            calls.append({"path": path, "streaming": streaming, "split": split})
            if streaming:
                return _make_dataset(2).to_iterable_dataset()
            return _make_dataset(2)

        monkeypatch.setattr(
            "asebytes.hf._backend.load_dataset", fake_load
        )
        mapping = ColumnMapping(positions="positions", numbers="atomic_numbers")
        backend = HuggingFaceBackend.from_uri(
            "hf://user/dataset", mapping=mapping, streaming=False
        )
        assert calls[0]["streaming"] is False
        assert len(backend) == 2  # downloaded mode has known length

    def test_split_forwarded(self, monkeypatch):
        """split kwarg should be forwarded to load_dataset."""
        calls = []

        def fake_load(path, *, streaming=False, split=None, **kwargs):
            calls.append({"path": path, "streaming": streaming, "split": split})
            if streaming:
                return _make_dataset(2).to_iterable_dataset()
            return _make_dataset(2)

        monkeypatch.setattr(
            "asebytes.hf._backend.load_dataset", fake_load
        )
        mapping = ColumnMapping(positions="positions", numbers="atomic_numbers")
        backend = HuggingFaceBackend.from_uri(
            "hf://user/dataset", mapping=mapping, split="train"
        )
        assert calls[0]["split"] == "train"

    def test_hf_requires_mapping(self, monkeypatch):
        """hf:// without mapping should raise ValueError."""
        def fake_load(path, *, streaming=False, split=None, **kwargs):
            return _make_dataset(2)

        monkeypatch.setattr(
            "asebytes.hf._backend.load_dataset", fake_load
        )
        with pytest.raises(ValueError, match="mapping"):
            HuggingFaceBackend.from_uri("hf://user/dataset")

    def test_dataset_dict_requires_explicit_split(self, monkeypatch):
        """When load_dataset returns DatasetDict, require explicit split."""

        def fake_load(path, *, streaming=False, split=None, **kwargs):
            ds = _make_dataset(3)
            if split is None:
                return datasets.DatasetDict({"train": ds, "test": ds})
            return ds

        monkeypatch.setattr(
            "asebytes.hf._backend.load_dataset", fake_load
        )
        with pytest.raises(ValueError, match="multiple splits.*split='train'"):
            HuggingFaceBackend.from_uri("colabfit://test_ds")

    def test_dataset_dict_with_explicit_split(self, monkeypatch):
        """When split is specified, DatasetDict is not returned."""

        def fake_load(path, *, streaming=False, split=None, **kwargs):
            ds = _make_dataset(3)
            if split is None:
                return datasets.DatasetDict({"train": ds})
            if streaming:
                return ds.to_iterable_dataset()
            return ds

        monkeypatch.setattr(
            "asebytes.hf._backend.load_dataset", fake_load
        )
        backend = HuggingFaceBackend.from_uri(
            "colabfit://test_ds", split="train"
        )
        row = backend.read_row(0)
        assert "arrays.positions" in row

    def test_malformed_uri_raises(self):
        """URI without :// should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid URI"):
            HuggingFaceBackend.from_uri("not_a_uri")

    def test_empty_path_uri_raises(self):
        """URI with empty path should raise ValueError."""
        with pytest.raises(ValueError, match="Empty path"):
            HuggingFaceBackend.from_uri("hf://")
