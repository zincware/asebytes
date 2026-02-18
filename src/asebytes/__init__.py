import importlib.metadata

from ._bytesio import BytesIO
from .decode import decode
from .encode import encode
from .io import ASEIO
from .metadata import get_metadata

__all__ = ["encode", "decode", "BytesIO", "ASEIO", "get_metadata"]

__version__ = importlib.metadata.version("asebytes")
