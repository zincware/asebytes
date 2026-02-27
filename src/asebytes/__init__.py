import importlib.metadata

from ._convert import atoms_to_dict, dict_to_atoms
from ._async_bytesio import AsyncBytesIO
from ._async_io import AsyncASEIO
from ._async_protocols import (
    AsyncRawReadableBackend,
    AsyncRawWritableBackend,
    AsyncReadableBackend,
    AsyncWritableBackend,
    SyncToAsyncAdapter,
    SyncToAsyncRawAdapter,
)
from ._async_views import AsyncColumnView, AsyncRowView, AsyncSingleRowView
from ._protocols import (
    RawReadableBackend,
    RawWritableBackend,
    ReadableBackend,
    WritableBackend,
)
from ._views import ColumnView, RowView
from .decode import decode
from .encode import encode
from .io import ASEIO
from .ase import ASEReadOnlyBackend
from .metadata import get_metadata

__all__ = [
    "encode",
    "decode",
    "ASEIO",
    "AsyncASEIO",
    "AsyncBytesIO",
    "get_metadata",
    "RawReadableBackend",
    "RawWritableBackend",
    "ReadableBackend",
    "WritableBackend",
    "AsyncRawReadableBackend",
    "AsyncRawWritableBackend",
    "AsyncReadableBackend",
    "AsyncWritableBackend",
    "SyncToAsyncAdapter",
    "SyncToAsyncRawAdapter",
    "atoms_to_dict",
    "dict_to_atoms",
    "RowView",
    "ColumnView",
    "AsyncRowView",
    "AsyncColumnView",
    "AsyncSingleRowView",
    "ASEReadOnlyBackend",
]

try:
    from .lmdb import BytesIO, LMDBBackend, LMDBReadOnlyBackend
except ImportError:
    pass
else:
    __all__ += [
        "BytesIO",
        "LMDBBackend",
        "LMDBReadOnlyBackend",
    ]

try:
    from .hf import COLABFIT, OPTIMADE, ColumnMapping, HuggingFaceBackend
except ImportError:
    pass
else:
    __all__ += [
        "HuggingFaceBackend",
        "ColumnMapping",
        "COLABFIT",
        "OPTIMADE",
    ]

try:
    from .h5md import H5MDBackend
except ImportError:
    pass
else:
    __all__ += ["H5MDBackend"]

try:
    from .zarr import ZarrBackend
except ImportError:
    pass
else:
    __all__ += ["ZarrBackend"]

_OPTIONAL_ATTRS: dict[str, str] = {
    "BytesIO": "lmdb",
    "LMDBBackend": "lmdb",
    "LMDBReadOnlyBackend": "lmdb",
    "HuggingFaceBackend": "hf",
    "ColumnMapping": "hf",
    "COLABFIT": "hf",
    "OPTIMADE": "hf",
    "H5MDBackend": "h5md",
    "ZarrBackend": "zarr",
}


def __getattr__(name: str):
    if name in _OPTIONAL_ATTRS:
        extra = _OPTIONAL_ATTRS[name]
        raise ImportError(
            f"'{name}' requires additional dependencies. "
            f"Install them with: pip install asebytes[{extra}]"
        )
    raise AttributeError(f"module 'asebytes' has no attribute '{name}'")


__version__ = importlib.metadata.version("asebytes")
