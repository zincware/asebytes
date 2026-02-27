"""Tests for URI-prefix matching in the backend registry."""

from __future__ import annotations

import pytest

from asebytes._registry import get_backend_cls, parse_uri


# ── parse_uri ──────────────────────────────────────────────────────────────


class TestParseUri:
    """Tests for the parse_uri helper."""

    def test_hf_scheme(self):
        scheme, remainder = parse_uri("hf://user/datset")
        assert scheme == "hf"
        assert remainder == "user/datset"

    def test_colabfit_scheme(self):
        scheme, remainder = parse_uri("colabfit://some/path")
        assert scheme == "colabfit"
        assert remainder == "some/path"

    def test_optimade_scheme(self):
        scheme, remainder = parse_uri("optimade://provider/structures")
        assert scheme == "optimade"
        assert remainder == "provider/structures"

    def test_regular_file_path(self):
        scheme, remainder = parse_uri("/tmp/data.lmdb")
        assert scheme is None
        assert remainder == "/tmp/data.lmdb"

    def test_relative_file_path(self):
        scheme, remainder = parse_uri("data/test.xyz")
        assert scheme is None
        assert remainder == "data/test.xyz"

    def test_windows_path_not_misinterpreted(self):
        scheme, remainder = parse_uri(r"C:\Users\data\test.lmdb")
        assert scheme is None
        assert remainder == r"C:\Users\data\test.lmdb"

    def test_unknown_scheme_returns_none(self):
        scheme, remainder = parse_uri("unknown://foo/bar")
        assert scheme is None
        assert remainder == "unknown://foo/bar"

    def test_empty_remainder(self):
        scheme, remainder = parse_uri("hf://")
        assert scheme == "hf"
        assert remainder == ""


# ── get_backend_cls with URI schemes ───────────────────────────────────────


class TestGetBackendClsUri:
    """Tests for get_backend_cls with URI-prefix paths.

    NOTE: These tests will fail with ImportError until the HuggingFaceBackend
    class is implemented in Task 3. That is expected.
    """

    def test_hf_returns_backend(self):
        cls = get_backend_cls("hf://user/datset")
        assert cls.__name__ == "HuggingFaceBackend"

    def test_colabfit_returns_backend(self):
        cls = get_backend_cls("colabfit://some/path")
        assert cls.__name__ == "HuggingFaceBackend"

    def test_optimade_returns_backend(self):
        cls = get_backend_cls("optimade://provider/structures")
        assert cls.__name__ == "HuggingFaceBackend"

    def test_hf_readonly_true(self):
        cls = get_backend_cls("hf://user/datset", readonly=True)
        assert cls.__name__ == "HuggingFaceBackend"

    def test_hf_readonly_none(self):
        cls = get_backend_cls("hf://user/datset", readonly=None)
        assert cls.__name__ == "HuggingFaceBackend"

    def test_hf_readonly_false_raises_type_error(self):
        with pytest.raises(TypeError, match="read-only"):
            get_backend_cls("hf://user/datset", readonly=False)

    def test_unknown_uri_raises_key_error(self):
        with pytest.raises(KeyError, match="No backend registered"):
            get_backend_cls("unknown://foo")


# ── get_backend_cls backward compatibility ─────────────────────────────────


class TestGetBackendClsGlobCompat:
    """Ensure existing glob-based resolution still works."""

    def test_lmdb_writable(self):
        cls = get_backend_cls("test.lmdb", readonly=False)
        assert cls.__name__ == "LMDBObjectBackend"

    def test_lmdb_readonly(self):
        cls = get_backend_cls("test.lmdb", readonly=True)
        assert cls.__name__ == "LMDBObjectReadBackend"

    def test_xyz_readonly(self):
        cls = get_backend_cls("data.xyz", readonly=True)
        assert cls.__name__ == "ASEReadOnlyBackend"

    def test_xyz_writable_raises(self):
        with pytest.raises(TypeError, match="read-only"):
            get_backend_cls("data.xyz", readonly=False)

    def test_unknown_extension_raises(self):
        with pytest.raises(KeyError, match="No backend registered"):
            get_backend_cls("data.unknown")
