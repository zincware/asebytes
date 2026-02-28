"""Backend registry for mapping file patterns to backend classes."""

from __future__ import annotations

import fnmatch
import importlib

# pattern -> (module_path, writable_cls_name | None, readonly_cls_name)
_BACKEND_REGISTRY: dict[str, tuple[str, str | None, str]] = {
    "*.lmdb": ("asebytes.lmdb", "LMDBObjectBackend", "LMDBObjectReadBackend"),
    "*.h5": ("asebytes.h5md", "H5MDBackend", "H5MDBackend"),
    "*.h5md": ("asebytes.h5md", "H5MDBackend", "H5MDBackend"),
    "*.zarr": ("asebytes.zarr", "ZarrBackend", "ZarrBackend"),
    "*.traj": ("asebytes.ase", None, "ASEReadOnlyBackend"),
    "*.xyz": ("asebytes.ase", None, "ASEReadOnlyBackend"),
    "*.extxyz": ("asebytes.ase", None, "ASEReadOnlyBackend"),
}

# Blob-level registry: pattern -> (module_path, writable_cls_name | None, readonly_cls_name)
# Used by BlobIO / AsyncBlobIO for dict[bytes, bytes] backends.
_BLOB_BACKEND_REGISTRY: dict[str, tuple[str, str | None, str]] = {
    "*.lmdb": ("asebytes.lmdb", "LMDBBlobBackend", "LMDBBlobBackend"),
}

# URI scheme -> (module_path, writable_cls_name | None, readonly_cls_name)
_URI_REGISTRY: dict[str, tuple[str, str | None, str]] = {
    "hf": ("asebytes.hf._backend", None, "HuggingFaceBackend"),
    "colabfit": ("asebytes.hf._backend", None, "HuggingFaceBackend"),
    "optimade": ("asebytes.hf._backend", None, "HuggingFaceBackend"),
    "mongodb": ("asebytes.mongodb._backend", "MongoObjectBackend", "MongoObjectBackend"),
    "memory": ("asebytes.memory._backend", "MemoryObjectBackend", "MemoryObjectBackend"),
}

_EXTRAS_HINT: dict[str, str] = {
    "asebytes.lmdb": "lmdb",
    "asebytes.hf": "hf",
    "asebytes.hf._backend": "hf",
    "asebytes.h5md": "h5md",
    "asebytes.h5md._backend": "h5md",
    "asebytes.zarr": "zarr",
    "asebytes.zarr._backend": "zarr",
    "asebytes.mongodb": "mongodb",
    "asebytes.mongodb._backend": "mongodb",
    "asebytes.mongodb._async_backend": "mongodb",
}

# Async URI scheme -> native async backend class.
# Checked first by get_async_backend_cls(); if no entry, falls back to sync.
_ASYNC_URI_REGISTRY: dict[str, tuple[str, str | None, str]] = {
    "mongodb": (
        "asebytes.mongodb._async_backend",
        "AsyncMongoObjectBackend",
        "AsyncMongoObjectBackend",
    ),
}


def parse_uri(path: str) -> tuple[str | None, str]:
    """Split *path* into ``(scheme, remainder)`` if it matches a known URI.

    Parameters
    ----------
    path : str
        A URI like ``hf://user/dataset`` or a regular file path.

    Returns
    -------
    tuple[str | None, str]
        ``(scheme, remainder)`` when the scheme is registered in
        ``_URI_REGISTRY``; ``(None, path)`` otherwise (including unknown
        schemes and Windows drive-letter paths like ``C:\\...``).
    """
    sep = "://"
    if sep not in path:
        return None, path
    scheme, remainder = path.split(sep, 1)
    if scheme in _URI_REGISTRY or scheme in _ASYNC_URI_REGISTRY:
        return scheme, remainder
    return None, path


def get_backend_cls(path: str, *, readonly: bool | None = None):
    """Resolve a file path or URI to a backend class.

    URI schemes (e.g. ``hf://``, ``colabfit://``, ``optimade://``) are checked
    first; if the path does not match a known URI it falls through to
    glob-based pattern matching.

    Parameters
    ----------
    path : str
        File path or URI to match against registered backends.
    readonly : bool | None
        If True, return the read-only backend class.
        If False, return the writable backend class (raises TypeError if none).
        If None (default), auto-detect: prefer writable if available, else
        read-only.

    Returns
    -------
    type
        The matched backend class.

    Raises
    ------
    KeyError
        If no backend is registered for the given path.
    TypeError
        If a writable backend is explicitly requested but none is available.
    """
    # --- URI-based lookup (checked first) ---
    scheme, _remainder = parse_uri(path)
    if scheme is not None:
        module_path, writable, read_only = _URI_REGISTRY[scheme]
        try:
            mod = importlib.import_module(module_path)
        except ImportError:
            hint = _EXTRAS_HINT.get(module_path, module_path)
            raise ImportError(
                f"Backend '{module_path}' requires additional dependencies. "
                f"Install them with: pip install asebytes[{hint}]"
            ) from None
        if readonly is True:
            return getattr(mod, read_only)
        if readonly is False:
            if writable is None:
                raise TypeError(
                    f"Backend for '{path}' is read-only, "
                    "no writable variant available"
                )
            return getattr(mod, writable)
        # readonly is None — auto-detect
        if writable is not None:
            return getattr(mod, writable)
        return getattr(mod, read_only)

    # --- Glob-based lookup ---
    for pattern, (module_path, writable, read_only) in _BACKEND_REGISTRY.items():
        if fnmatch.fnmatch(path, pattern):
            try:
                mod = importlib.import_module(module_path)
            except ImportError:
                hint = _EXTRAS_HINT.get(module_path, module_path)
                raise ImportError(
                    f"Backend '{module_path}' requires additional dependencies. "
                    f"Install them with: pip install asebytes[{hint}]"
                ) from None
            if readonly is True:
                return getattr(mod, read_only)
            if readonly is False:
                if writable is None:
                    raise TypeError(
                        f"Backend for '{path}' is read-only, "
                        "no writable variant available"
                    )
                return getattr(mod, writable)
            # readonly is None — auto-detect
            if writable is not None:
                return getattr(mod, writable)
            return getattr(mod, read_only)
    raise KeyError(f"No backend registered for '{path}'")


def get_async_backend_cls(path: str, *, readonly: bool | None = None):
    """Resolve a path/URI to a backend class, preferring native async.

    Checks _ASYNC_URI_REGISTRY first for URI schemes. If no async-specific
    entry exists, falls back to get_backend_cls (sync registry). The caller
    is responsible for wrapping sync backends with sync_to_async().
    """
    scheme, _remainder = parse_uri(path)
    if scheme is not None and scheme in _ASYNC_URI_REGISTRY:
        module_path, writable, read_only = _ASYNC_URI_REGISTRY[scheme]
        try:
            mod = importlib.import_module(module_path)
        except ImportError:
            hint = _EXTRAS_HINT.get(module_path, module_path)
            raise ImportError(
                f"Backend '{module_path}' requires additional dependencies. "
                f"Install them with: pip install asebytes[{hint}]"
            ) from None
        if readonly is True:
            return getattr(mod, read_only)
        if readonly is False:
            if writable is None:
                raise TypeError(
                    f"Backend for '{path}' is read-only, "
                    "no writable variant available"
                )
            return getattr(mod, writable)
        if writable is not None:
            return getattr(mod, writable)
        return getattr(mod, read_only)

    # Fall back to sync registry
    return get_backend_cls(path, readonly=readonly)


def get_blob_backend_cls(path: str, *, readonly: bool | None = None):
    """Resolve a file path to a blob-level backend class.

    Like :func:`get_backend_cls` but uses the blob-level registry
    (``ReadBackend[bytes, bytes]``).  URI schemes are not supported for
    blob-level backends.

    Parameters
    ----------
    path : str
        File path to match against registered blob backends.
    readonly : bool | None
        Same semantics as :func:`get_backend_cls`.
    """
    for pattern, (module_path, writable, read_only) in _BLOB_BACKEND_REGISTRY.items():
        if fnmatch.fnmatch(path, pattern):
            try:
                mod = importlib.import_module(module_path)
            except ImportError:
                hint = _EXTRAS_HINT.get(module_path, module_path)
                raise ImportError(
                    f"Backend '{module_path}' requires additional dependencies. "
                    f"Install them with: pip install asebytes[{hint}]"
                ) from None
            if readonly is True:
                return getattr(mod, read_only)
            if readonly is False:
                if writable is None:
                    raise TypeError(
                        f"Backend for '{path}' is read-only, "
                        "no writable variant available"
                    )
                return getattr(mod, writable)
            if writable is not None:
                return getattr(mod, writable)
            return getattr(mod, read_only)
    # --- Fallback: wrap object backend with ObjectToBlobAdapter ---
    scheme, _remainder = parse_uri(path)
    try:
        obj_cls = get_backend_cls(path, readonly=readonly)
    except KeyError:
        raise KeyError(f"No blob backend registered for '{path}'")

    from ._adapters import ObjectToBlobReadAdapter, ObjectToBlobReadWriteAdapter

    if scheme is not None:
        # URI-based backend: use from_uri to instantiate
        if readonly is True:
            def _make_read_adapter(*args, **kwargs):
                return ObjectToBlobReadAdapter(obj_cls.from_uri(*args, **kwargs))
            return _make_read_adapter

        def _make_readwrite_adapter(*args, **kwargs):
            return ObjectToBlobReadWriteAdapter(obj_cls.from_uri(*args, **kwargs))
        return _make_readwrite_adapter

    if readonly is True:
        def _make_read_adapter(*args, **kwargs):
            return ObjectToBlobReadAdapter(obj_cls(*args, **kwargs))
        return _make_read_adapter

    def _make_readwrite_adapter(*args, **kwargs):
        return ObjectToBlobReadWriteAdapter(obj_cls(*args, **kwargs))
    return _make_readwrite_adapter
