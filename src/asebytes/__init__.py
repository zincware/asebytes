import importlib.metadata

from ._bytesio import BytesIO
from ._convert import atoms_to_dict, dict_to_atoms
from ._protocols import ReadableBackend, WritableBackend
from ._views import ColumnView, RowView
from .decode import decode
from .encode import encode
from .io import ASEIO
from .ase import ASEReadOnlyBackend
from .lmdb import LMDBBackend, LMDBReadOnlyBackend
from .metadata import get_metadata

__all__ = [
    "encode",
    "decode",
    "BytesIO",
    "ASEIO",
    "get_metadata",
    "ReadableBackend",
    "WritableBackend",
    "atoms_to_dict",
    "dict_to_atoms",
    "RowView",
    "ColumnView",
    "LMDBBackend",
    "LMDBReadOnlyBackend",
    "ASEReadOnlyBackend",
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

__version__ = importlib.metadata.version("asebytes")
