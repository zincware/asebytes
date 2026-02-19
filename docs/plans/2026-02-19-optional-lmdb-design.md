# Make LMDB an Optional Dependency

## Motivation

1. **Lightweight read-only installs** — users who only read `.traj`/`.xyz` files
   via the ASE backend or stream HuggingFace datasets don't need local LMDB
   storage.
2. **Reduced install footprint** — the `lmdb` C extension can be difficult to
   install in constrained environments (certain CI, conda, WASM).

## Design

### Dependency changes

Core dependencies are reduced to just `ase`. Each backend brings its own
serialization deps via extras.

```toml
# pyproject.toml
dependencies = [
    "ase>=3.26.0",
]

[project.optional-dependencies]
lmdb = [
    "lmdb>=1.7.5",
    "msgpack>=1.1.2",
    "msgpack-numpy>=0.4.8",
]
hf = [
    "datasets>=4.5.0",
]
```

The dev dependency group references the extras:

```toml
[dependency-groups]
dev = [
    "asebytes[lmdb]",
    "asebytes[hf]",
    # ... rest unchanged
]
```

### File move: `_bytesio.py` into `lmdb/` subpackage

`_bytesio.py` is purely LMDB plumbing and belongs with the rest of the LMDB
backend. Moving it makes the entire `lmdb/` subpackage self-contained behind
the optional install.

```
src/asebytes/
├── __init__.py          # try/except for lmdb exports
├── _protocols.py        # unchanged
├── _registry.py         # better error message on ImportError
├── _views.py            # unchanged
├── _convert.py          # unchanged
├── io.py                # unchanged
├── encode.py            # unchanged
├── decode.py            # unchanged
├── metadata.py          # unchanged
├── lmdb/
│   ├── __init__.py      # exports LMDBBackend, LMDBReadOnlyBackend
│   ├── _backend.py      # unchanged
│   └── _bytesio.py      # moved from src/asebytes/_bytesio.py
├── ase/
│   └── ...              # unchanged
└── hf/
    └── ...              # unchanged
```

- Move `src/asebytes/_bytesio.py` to `src/asebytes/lmdb/_bytesio.py`
- Update import in `lmdb/_backend.py`: `from asebytes._bytesio` becomes
  `from ._bytesio`
- Update any other internal references to `_bytesio`
- Delete old `src/asebytes/_bytesio.py`

### Import guarding in `__init__.py`

Follow the existing HuggingFace pattern:

```python
try:
    from .lmdb import LMDBBackend, LMDBReadOnlyBackend
except ImportError:
    pass
else:
    __all__ += ["LMDBBackend", "LMDBReadOnlyBackend"]
```

No lazy-import gymnastics inside `_bytesio.py` or `lmdb/_backend.py` — they
keep their top-level imports. The natural `ImportError` propagation does the
work.

### Registry error handling

Add an extras hint mapping in `_registry.py` so `get_backend_cls` produces
helpful error messages when an optional backend is missing:

```python
_EXTRAS_HINT = {
    "asebytes.lmdb": "lmdb",
    "asebytes.hf": "hf",
}
```

When `importlib.import_module` fails, catch `ImportError` and re-raise:

```python
try:
    mod = importlib.import_module(module_path)
except ImportError:
    hint = _EXTRAS_HINT.get(module_path, module_path)
    raise ImportError(
        f"Backend '{module_path}' requires additional dependencies. "
        f"Install them with: pip install asebytes[{hint}]"
    ) from None
```

### What doesn't change

- `_bytesio.py` internals (just the file location)
- `lmdb/_backend.py` internals
- `_protocols.py`, `io.py`, views, encode/decode
- Test files
- HuggingFace backend

## Breaking change note

This is a breaking change: `pip install asebytes` will no longer include LMDB
support. Users must switch to `pip install asebytes[lmdb]`. Acceptable at
pre-1.0 (`0.1.7`), documented in release notes.
