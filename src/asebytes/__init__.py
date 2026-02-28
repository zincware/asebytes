import importlib.metadata

from ._convert import atoms_to_dict, dict_to_atoms

# New canonical ABCs
from ._backends import (
    ReadBackend,
    ReadWriteBackend,
    BlobReadBackend,
    BlobReadWriteBackend,
    ObjectReadBackend,
    ObjectReadWriteBackend,
)
from ._async_backends import (
    AsyncReadBackend,
    AsyncReadWriteBackend,
    AsyncBlobReadBackend,
    AsyncBlobReadWriteBackend,
    AsyncObjectReadBackend,
    AsyncObjectReadWriteBackend,
    SyncToAsyncAdapter,
    SyncToAsyncReadAdapter,
    SyncToAsyncReadWriteAdapter,
    sync_to_async,
)
from ._adapters import (
    BlobToObjectReadAdapter,
    BlobToObjectReadWriteAdapter,
    ObjectToBlobReadAdapter,
    ObjectToBlobReadWriteAdapter,
)
from ._async_adapters import (
    AsyncBlobToObjectReadAdapter,
    AsyncBlobToObjectReadWriteAdapter,
    AsyncObjectToBlobReadAdapter,
    AsyncObjectToBlobReadWriteAdapter,
)

# Facades
from ._blob_io import BlobIO
from ._object_io import ObjectIO
from ._async_blob_io import AsyncBlobIO
from ._async_object_io import AsyncObjectIO
from ._async_io import AsyncASEIO
from .io import ASEIO

# Views
from ._views import ASEColumnView, ColumnView, RowView, ViewParent
from ._async_views import (
    AsyncASEColumnView,
    AsyncColumnView,
    AsyncRowView,
    AsyncSingleColumnView,
    AsyncSingleRowView,
    AsyncViewParent,
)

# Utilities
from .decode import decode
from .encode import encode
from .ase import ASEReadOnlyBackend
from .metadata import get_metadata

__all__ = [
    # ABCs
    "ReadBackend",
    "ReadWriteBackend",
    "BlobReadBackend",
    "BlobReadWriteBackend",
    "ObjectReadBackend",
    "ObjectReadWriteBackend",
    "AsyncReadBackend",
    "AsyncReadWriteBackend",
    "AsyncBlobReadBackend",
    "AsyncBlobReadWriteBackend",
    "AsyncObjectReadBackend",
    "AsyncObjectReadWriteBackend",
    "SyncToAsyncAdapter",
    "SyncToAsyncReadAdapter",
    "SyncToAsyncReadWriteAdapter",
    "sync_to_async",
    # Adapters
    "BlobToObjectReadAdapter",
    "BlobToObjectReadWriteAdapter",
    "ObjectToBlobReadAdapter",
    "ObjectToBlobReadWriteAdapter",
    "AsyncBlobToObjectReadAdapter",
    "AsyncBlobToObjectReadWriteAdapter",
    "AsyncObjectToBlobReadAdapter",
    "AsyncObjectToBlobReadWriteAdapter",
    # Facades
    "BlobIO",
    "ObjectIO",
    "AsyncBlobIO",
    "AsyncObjectIO",
    "ASEIO",
    "AsyncASEIO",
    # Utilities
    "encode",
    "decode",
    "get_metadata",
    "atoms_to_dict",
    "dict_to_atoms",
    # Views
    "RowView",
    "ColumnView",
    "ASEColumnView",
    "ViewParent",
    "AsyncRowView",
    "AsyncColumnView",
    "AsyncASEColumnView",
    "AsyncSingleColumnView",
    "AsyncSingleRowView",
    "AsyncViewParent",
    # Built-in backends
    "ASEReadOnlyBackend",
]

try:
    from .lmdb import (
        LMDBBlobBackend,
        LMDBObjectBackend,
        LMDBObjectReadBackend,
    )
except ImportError:
    pass
else:
    __all__ += [
        "LMDBBlobBackend",
        "LMDBObjectBackend",
        "LMDBObjectReadBackend",
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
    "LMDBBlobBackend": "lmdb",
    "LMDBObjectBackend": "lmdb",
    "LMDBObjectReadBackend": "lmdb",
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
