"""Tests for optional dependency error messages."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from asebytes._registry import get_backend_cls


# ── Registry ImportError hints ────────────────────────────────────────────


class TestRegistryImportHints:
    """Verify get_backend_cls raises helpful ImportError when deps are missing."""

    def test_lmdb_missing_glob(self):
        """*.lmdb pattern gives install hint when lmdb is not installed."""
        with patch(
            "asebytes._registry.importlib.import_module",
            side_effect=ImportError("No module named 'lmdb'"),
        ):
            with pytest.raises(ImportError, match=r"pip install asebytes\[lmdb\]"):
                get_backend_cls("test.lmdb")

    def test_lmdb_missing_readonly(self):
        """Readonly request also gives install hint."""
        with patch(
            "asebytes._registry.importlib.import_module",
            side_effect=ImportError("No module named 'lmdb'"),
        ):
            with pytest.raises(ImportError, match=r"pip install asebytes\[lmdb\]"):
                get_backend_cls("test.lmdb", readonly=True)

    def test_hf_missing_uri(self):
        """hf:// URI gives install hint when datasets is not installed."""
        with patch(
            "asebytes._registry.importlib.import_module",
            side_effect=ImportError("No module named 'datasets'"),
        ):
            with pytest.raises(ImportError, match=r"pip install asebytes\[hf\]"):
                get_backend_cls("hf://user/dataset")

    def test_colabfit_missing_uri(self):
        """colabfit:// URI gives install hint."""
        with patch(
            "asebytes._registry.importlib.import_module",
            side_effect=ImportError("No module named 'datasets'"),
        ):
            with pytest.raises(ImportError, match=r"pip install asebytes\[hf\]"):
                get_backend_cls("colabfit://some/path")

    def test_optimade_missing_uri(self):
        """optimade:// URI gives install hint."""
        with patch(
            "asebytes._registry.importlib.import_module",
            side_effect=ImportError("No module named 'datasets'"),
        ):
            with pytest.raises(ImportError, match=r"pip install asebytes\[hf\]"):
                get_backend_cls("optimade://provider/structures")

    def test_error_message_mentions_backend(self):
        """Error message includes the backend module path."""
        with patch(
            "asebytes._registry.importlib.import_module",
            side_effect=ImportError("No module named 'lmdb'"),
        ):
            with pytest.raises(ImportError, match=r"Backend 'asebytes\.lmdb'"):
                get_backend_cls("data.lmdb")


# ── Module-level __getattr__ hints ────────────────────────────────────────


class TestModuleGetattr:
    """Verify from asebytes import <optional> gives helpful errors."""

    def test_bytesio_hint(self):
        import asebytes

        # Only test if BytesIO is NOT already available (lmdb not installed).
        # Since lmdb IS installed in dev, we test __getattr__ directly.
        msg = r"pip install asebytes\[lmdb\]"
        with pytest.raises(ImportError, match=msg):
            asebytes.__getattr__("BytesIO")

    def test_lmdb_backend_hint(self):
        import asebytes

        with pytest.raises(ImportError, match=r"pip install asebytes\[lmdb\]"):
            asebytes.__getattr__("LMDBBackend")

    def test_lmdb_readonly_backend_hint(self):
        import asebytes

        with pytest.raises(ImportError, match=r"pip install asebytes\[lmdb\]"):
            asebytes.__getattr__("LMDBReadOnlyBackend")

    def test_hf_backend_hint(self):
        import asebytes

        with pytest.raises(ImportError, match=r"pip install asebytes\[hf\]"):
            asebytes.__getattr__("HuggingFaceBackend")

    def test_column_mapping_hint(self):
        import asebytes

        with pytest.raises(ImportError, match=r"pip install asebytes\[hf\]"):
            asebytes.__getattr__("ColumnMapping")

    def test_unknown_attr_raises_attribute_error(self):
        import asebytes

        with pytest.raises(AttributeError, match="no attribute 'NoSuchThing'"):
            asebytes.__getattr__("NoSuchThing")
