"""Backend registry for mapping file patterns to backend classes."""

from __future__ import annotations

import fnmatch
import importlib

# pattern -> (module_path, writable_cls_name | None, readonly_cls_name)
_BACKEND_REGISTRY: dict[str, tuple[str, str | None, str]] = {
    "*.lmdb": ("asebytes.lmdb", "LMDBBackend", "LMDBReadOnlyBackend"),
}


def get_backend_cls(path: str, *, readonly: bool = False):
    """Resolve a file path to a backend class via glob pattern matching.

    Parameters
    ----------
    path : str
        File path to match against registered patterns.
    readonly : bool
        If True, return the read-only backend class.

    Returns
    -------
    type
        The matched backend class.

    Raises
    ------
    KeyError
        If no backend is registered for the given path.
    TypeError
        If a writable backend is requested but none is available.
    """
    for pattern, (module_path, writable, read_only) in _BACKEND_REGISTRY.items():
        if fnmatch.fnmatch(path, pattern):
            mod = importlib.import_module(module_path)
            if not readonly:
                if writable is None:
                    raise TypeError(
                        f"Backend for '{path}' is read-only, "
                        "no writable variant available"
                    )
                return getattr(mod, writable)
            return getattr(mod, read_only)
    raise KeyError(f"No backend registered for '{path}'")
