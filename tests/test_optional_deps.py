"""Tests for optional dependency error messages."""

from __future__ import annotations

from unittest.mock import patch

import pytest

import asebytes
from asebytes._registry import get_backend_cls


# ── Registry ImportError hints ────────────────────────────────────────────


class TestRegistryImportHints:
    """Verify get_backend_cls raises helpful ImportError when deps are missing.

    Uses unittest.mock.patch to make importlib.import_module raise ImportError,
    simulating an environment where the optional backend package is not installed.
    """

    @pytest.mark.parametrize(
        ("path", "extra"),
        [
            ("test.lmdb", "lmdb"),
            ("data.lmdb", "lmdb"),
            ("hf://user/dataset", "hf"),
            ("colabfit://some/path", "hf"),
            ("optimade://provider/structures", "hf"),
        ],
    )
    def test_missing_dep_gives_install_hint(self, path, extra):
        with patch(
            "asebytes._registry.importlib.import_module",
            side_effect=ImportError("No module"),
        ):
            with pytest.raises(
                ImportError, match=rf"pip install asebytes\[{extra}\]"
            ):
                get_backend_cls(path)

    def test_lmdb_missing_readonly(self):
        """Readonly request also gives the same install hint."""
        with patch(
            "asebytes._registry.importlib.import_module",
            side_effect=ImportError("No module"),
        ):
            with pytest.raises(ImportError, match=r"pip install asebytes\[lmdb\]"):
                get_backend_cls("test.lmdb", readonly=True)

    def test_error_message_mentions_backend_module(self):
        """Error message includes the backend module path for debugging."""
        with patch(
            "asebytes._registry.importlib.import_module",
            side_effect=ImportError("No module"),
        ):
            with pytest.raises(ImportError, match=r"Backend 'asebytes\.lmdb'"):
                get_backend_cls("data.lmdb")


# ── Module-level __getattr__ hints ────────────────────────────────────────


class TestModuleGetattr:
    """Verify asebytes.__getattr__ gives helpful ImportError for optional names.

    In the dev environment lmdb and datasets are installed, so the names are
    already bound as real module attributes.  We call __getattr__ directly to
    exercise the fallback path that fires when the optional deps are absent.
    """

    @pytest.mark.parametrize(
        ("name", "extra"),
        [
            ("LMDBBlobBackend", "lmdb"),
            ("LMDBObjectBackend", "lmdb"),
            ("LMDBObjectReadBackend", "lmdb"),
            ("HuggingFaceBackend", "hf"),
            ("ColumnMapping", "hf"),
            ("COLABFIT", "hf"),
            ("OPTIMADE", "hf"),
        ],
    )
    def test_optional_attr_gives_install_hint(self, name, extra):
        with pytest.raises(
            ImportError, match=rf"pip install asebytes\[{extra}\]"
        ):
            asebytes.__getattr__(name)

    def test_unknown_attr_raises_attribute_error(self):
        with pytest.raises(AttributeError, match="no attribute 'NoSuchThing'"):
            asebytes.__getattr__("NoSuchThing")
