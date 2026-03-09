"""Backend registry for mapping file patterns to backend classes.

A single ``_REGISTRY`` list holds all backend entries.  The
:func:`resolve_backend` function searches it by scheme or glob pattern,
filtering by layer (blob / object) and async preference.

The legacy helper functions :func:`get_backend_cls`,
:func:`get_async_backend_cls`, :func:`get_blob_backend_cls`, and
:func:`get_async_blob_backend_cls` are thin wrappers kept for backward
compatibility.
"""

from __future__ import annotations

import fnmatch
import importlib
from typing import Literal, NamedTuple

# ---------------------------------------------------------------------------
# Unified registry
# ---------------------------------------------------------------------------


class _RegistryEntry(NamedTuple):
    match_type: str           # "pattern" or "scheme"
    match_value: str          # e.g. "*.lmdb" or "mongodb"
    layer: str                # "blob" or "object"
    module_path: str          # e.g. "asebytes.lmdb"
    writable_cls: str | None  # writable class name or None
    readonly_cls: str         # readonly class name
    is_async: bool            # True if native async


_REGISTRY: list[_RegistryEntry] = [
    # -- Object-level, pattern-based ----------------------------------------
    _RegistryEntry("pattern", "*.lmdb", "object", "asebytes.lmdb", "LMDBObjectBackend", "LMDBObjectReadBackend", False),
    _RegistryEntry("pattern", "*.h5", "object", "asebytes.columnar", "RaggedColumnarBackend", "RaggedColumnarBackend", False),
    _RegistryEntry("pattern", "*.h5p", "object", "asebytes.columnar", "PaddedColumnarBackend", "PaddedColumnarBackend", False),
    _RegistryEntry("pattern", "*.h5md", "object", "asebytes.h5md", "H5MDBackend", "H5MDBackend", False),
    _RegistryEntry("pattern", "*.zarr", "object", "asebytes.columnar", "RaggedColumnarBackend", "RaggedColumnarBackend", False),
    _RegistryEntry("pattern", "*.zarrp", "object", "asebytes.columnar", "PaddedColumnarBackend", "PaddedColumnarBackend", False),
    _RegistryEntry("pattern", "*.traj", "object", "asebytes.ase", None, "ASEReadOnlyBackend", False),
    _RegistryEntry("pattern", "*.xyz", "object", "asebytes.ase", None, "ASEReadOnlyBackend", False),
    _RegistryEntry("pattern", "*.extxyz", "object", "asebytes.ase", None, "ASEReadOnlyBackend", False),
    # -- Blob-level, pattern-based ------------------------------------------
    _RegistryEntry("pattern", "*.lmdb", "blob", "asebytes.lmdb", "LMDBBlobBackend", "LMDBBlobBackend", False),
    # -- Object-level, scheme-based -----------------------------------------
    _RegistryEntry("scheme", "hf", "object", "asebytes.hf._backend", None, "HuggingFaceBackend", False),
    _RegistryEntry("scheme", "colabfit", "object", "asebytes.hf._backend", None, "HuggingFaceBackend", False),
    _RegistryEntry("scheme", "optimade", "object", "asebytes.hf._backend", None, "HuggingFaceBackend", False),
    _RegistryEntry("scheme", "mongodb", "object", "asebytes.mongodb._backend", "MongoObjectBackend", "MongoObjectBackend", False),
    _RegistryEntry("scheme", "memory", "object", "asebytes.memory._backend", "MemoryObjectBackend", "MemoryObjectBackend", False),
    # -- Async object-level, scheme-based -----------------------------------
    _RegistryEntry("scheme", "mongodb", "object", "asebytes.mongodb._async_backend", "AsyncMongoObjectBackend", "AsyncMongoObjectBackend", True),
    # -- Blob-level, scheme-based -------------------------------------------
    _RegistryEntry("scheme", "redis", "blob", "asebytes.redis._backend", "RedisBlobBackend", "RedisBlobBackend", False),
    # -- Async blob-level, scheme-based -------------------------------------
    _RegistryEntry("scheme", "redis", "blob", "asebytes.redis._async_backend", "AsyncRedisBlobBackend", "AsyncRedisBlobBackend", True),
]

# Collect all known URI schemes from the registry for parse_uri().
_KNOWN_SCHEMES: frozenset[str] = frozenset(
    entry.match_value for entry in _REGISTRY if entry.match_type == "scheme"
)

# ---------------------------------------------------------------------------
# Extras hint for friendly ImportError messages
# ---------------------------------------------------------------------------

_EXTRAS_HINT: dict[str, str] = {
    "asebytes.lmdb": "lmdb",
    "asebytes.hf": "hf",
    "asebytes.hf._backend": "hf",
    "asebytes.h5md": "h5",
    "asebytes.h5md._backend": "h5",
    "asebytes.columnar": "columnar",
    "asebytes.mongodb": "mongodb",
    "asebytes.mongodb._backend": "mongodb",
    "asebytes.mongodb._async_backend": "mongodb",
    "asebytes.redis._backend": "redis",
    "asebytes.redis._async_backend": "redis",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _import_module(module_path: str):
    """Import *module_path*, raising a user-friendly error on failure."""
    try:
        return importlib.import_module(module_path)
    except ImportError:
        hint = _EXTRAS_HINT.get(module_path, module_path)
        raise ImportError(
            f"Backend '{module_path}' requires additional dependencies. "
            f"Install them with: uv add asebytes[{hint}]"
        ) from None


def parse_uri(path: str) -> tuple[str | None, str]:
    """Split *path* into ``(scheme, remainder)`` if it matches a known URI.

    Parameters
    ----------
    path : str
        A URI like ``hf://user/dataset`` or a regular file path.

    Returns
    -------
    tuple[str | None, str]
        ``(scheme, remainder)`` when the scheme is registered;
        ``(None, path)`` otherwise (including unknown schemes and
        Windows drive-letter paths like ``C:\\...``).
    """
    sep = "://"
    if sep not in path:
        return None, path
    scheme, remainder = path.split(sep, 1)
    if scheme in _KNOWN_SCHEMES:
        return scheme, remainder
    return None, path


# ---------------------------------------------------------------------------
# Core resolver
# ---------------------------------------------------------------------------


def _pick_class(entry: _RegistryEntry, path: str, writable: bool | None):
    """Import the module from *entry* and return the appropriate class."""
    mod = _import_module(entry.module_path)

    if writable is True:
        if entry.writable_cls is None:
            raise TypeError(
                f"Backend for '{path}' is read-only, no writable variant available"
            )
        return getattr(mod, entry.writable_cls)
    if writable is False:
        return getattr(mod, entry.readonly_cls)
    # writable is None -- prefer writable if available
    if entry.writable_cls is not None:
        return getattr(mod, entry.writable_cls)
    return getattr(mod, entry.readonly_cls)


def resolve_backend(
    path_or_uri: str,
    *,
    layer: Literal["blob", "object"],
    async_: bool = False,
    writable: bool | None = None,
    _allow_fallback: bool = True,
) -> type:
    """Resolve a path or URI to a backend class.

    Resolution priority:

    1. Match URI scheme first, then file pattern.
    2. Filter by requested *layer* (``"blob"`` or ``"object"``).
    3. If *async_* is ``True``, prefer ``is_async_native=True`` entries;
       fall back to sync.
    4. If *writable* is ``None``, prefer writable if available; if
       ``False``, use read-only.
    5. If no direct layer match, try cross-layer adapter wrapping
       (blob <-> object).

    Parameters
    ----------
    path_or_uri : str
        File path or URI string.
    layer : ``"blob"`` | ``"object"``
        Whether to look for a blob-level or object-level backend.
    async_ : bool
        If ``True``, prefer native async backends (fall back to sync).
    writable : bool | None
        ``True`` = require writable, ``False`` = require read-only,
        ``None`` = prefer writable, accept read-only.

    Returns
    -------
    type
        The resolved backend class (or adapter factory callable).

    Raises
    ------
    ValueError
        If no backend is registered for *path_or_uri*.
    TypeError
        If a writable backend is explicitly requested but none exists.
    """
    scheme, _remainder = parse_uri(path_or_uri)

    # -- Collect direct candidates for the requested layer ------------------
    candidates: list[_RegistryEntry] = []
    for entry in _REGISTRY:
        if entry.layer != layer:
            continue

        if entry.match_type == "scheme":
            if scheme != entry.match_value:
                continue
        else:  # pattern
            if scheme is not None:
                continue  # don't match patterns for URIs
            if not fnmatch.fnmatch(path_or_uri, entry.match_value):
                continue

        candidates.append(entry)

    # -- No direct match -> cross-layer adapter wrapping --------------------
    if not candidates:
        if _allow_fallback:
            return _cross_layer_fallback(
                path_or_uri,
                scheme=scheme,
                layer=layer,
                async_=async_,
                writable=writable,
            )
        raise ValueError(
            f"No backend found for '{path_or_uri}' (layer={layer})"
        )

    # -- Filter by async preference -----------------------------------------
    if async_:
        async_candidates = [c for c in candidates if c.is_async]
        if async_candidates:
            candidates = async_candidates
        # else: fall back to sync candidates (caller wraps with SyncToAsyncAdapter)
    else:
        sync_candidates = [c for c in candidates if not c.is_async]
        if sync_candidates:
            candidates = sync_candidates

    # -- Pick the first match and resolve class -----------------------------
    return _pick_class(candidates[0], path_or_uri, writable)


# ---------------------------------------------------------------------------
# Cross-layer adapter fallback
# ---------------------------------------------------------------------------


def _cross_layer_fallback(
    path_or_uri: str,
    *,
    scheme: str | None,
    layer: Literal["blob", "object"],
    async_: bool,
    writable: bool | None,
):
    """Wrap a backend from the *other* layer with an adapter.

    Called when :func:`resolve_backend` found no direct match for the
    requested *layer*.
    """
    if layer == "object":
        # Need object-level, but only blob-level exists -> BlobToObject adapter.
        # Always resolve the other layer as sync because the adapter classes
        # (BlobToObjectRead[Write]Adapter) are synchronous; the caller
        # (e.g. AsyncObjectIO) wraps the resulting sync instance with
        # sync_to_async at a higher level.
        try:
            blob_cls = resolve_backend(
                path_or_uri, layer="blob", async_=False, writable=writable,
                _allow_fallback=False,
            )
        except (ValueError, TypeError):
            raise ValueError(
                f"No backend found for '{path_or_uri}' (layer={layer})"
            ) from None

        from ._adapters import BlobToObjectReadAdapter, BlobToObjectReadWriteAdapter

        if writable is True or (writable is None and _supports_write(blob_cls)):
            if scheme is not None:
                def _make_rw(*args, **kwargs):
                    return BlobToObjectReadWriteAdapter(
                        blob_cls.from_uri(*args, **kwargs)
                    )
                return _make_rw

            def _make_rw(*args, **kwargs):
                return BlobToObjectReadWriteAdapter(blob_cls(*args, **kwargs))
            return _make_rw

        if scheme is not None:
            def _make_ro(*args, **kwargs):
                return BlobToObjectReadAdapter(
                    blob_cls.from_uri(*args, **kwargs)
                )
            return _make_ro

        def _make_ro(*args, **kwargs):
            return BlobToObjectReadAdapter(blob_cls(*args, **kwargs))
        return _make_ro

    # layer == "blob": need blob-level, only object-level exists.
    # Same as above: resolve as sync because the adapters are synchronous.
    try:
        obj_cls = resolve_backend(
            path_or_uri, layer="object", async_=False, writable=writable,
            _allow_fallback=False,
        )
    except (ValueError, TypeError):
        raise ValueError(
            f"No backend found for '{path_or_uri}' (layer={layer})"
        ) from None

    from ._adapters import ObjectToBlobReadAdapter, ObjectToBlobReadWriteAdapter

    use_read_adapter = writable is False or (
        writable is None and not _supports_write(obj_cls)
    )

    if scheme is not None:
        if use_read_adapter:
            def _make_ro(*args, **kwargs):
                return ObjectToBlobReadAdapter(obj_cls.from_uri(*args, **kwargs))
            return _make_ro

        def _make_rw(*args, **kwargs):
            return ObjectToBlobReadWriteAdapter(obj_cls.from_uri(*args, **kwargs))
        return _make_rw

    if use_read_adapter:
        def _make_ro(*args, **kwargs):
            return ObjectToBlobReadAdapter(obj_cls(*args, **kwargs))
        return _make_ro

    def _make_rw(*args, **kwargs):
        return ObjectToBlobReadWriteAdapter(obj_cls(*args, **kwargs))
    return _make_rw


def _supports_write(cls: type) -> bool:
    """Return True if *cls* looks like a read-write backend."""
    return hasattr(cls, "set") and hasattr(cls, "extend")


# ---------------------------------------------------------------------------
# Backward-compatible wrappers
# ---------------------------------------------------------------------------


def get_backend_cls(path: str, *, readonly: bool | None = None):
    """Resolve a file path or URI to an object-level backend class.

    Thin wrapper around :func:`resolve_backend` kept for backward
    compatibility.
    """
    writable = None if readonly is None else (not readonly)
    try:
        return resolve_backend(path, layer="object", writable=writable)
    except ValueError:
        raise KeyError(f"No backend registered for '{path}'") from None


def get_async_backend_cls(path: str, *, readonly: bool | None = None):
    """Resolve a path/URI to a backend class, preferring native async.

    Thin wrapper around :func:`resolve_backend` kept for backward
    compatibility.
    """
    writable = None if readonly is None else (not readonly)
    try:
        return resolve_backend(path, layer="object", async_=True, writable=writable)
    except ValueError:
        raise KeyError(f"No backend registered for '{path}'") from None


def get_blob_backend_cls(path: str, *, readonly: bool | None = None):
    """Resolve a file path or URI to a blob-level backend class.

    Thin wrapper around :func:`resolve_backend` kept for backward
    compatibility.
    """
    writable = None if readonly is None else (not readonly)
    try:
        return resolve_backend(path, layer="blob", writable=writable)
    except ValueError:
        raise KeyError(f"No blob backend registered for '{path}'") from None


def get_async_blob_backend_cls(path: str, *, readonly: bool | None = None):
    """Resolve a path/URI to an async blob-level backend class.

    Thin wrapper around :func:`resolve_backend` kept for backward
    compatibility.
    """
    writable = None if readonly is None else (not readonly)
    try:
        return resolve_backend(path, layer="blob", async_=True, writable=writable)
    except ValueError:
        raise KeyError(f"No blob backend registered for '{path}'") from None
