import importlib.metadata

from .from_bytes import from_bytes
from .io import ASEIO, BytesIO
from .metadata import get_metadata
from .to_bytes import to_bytes

__all__ = ["to_bytes", "from_bytes", "BytesIO", "ASEIO", "get_metadata"]

__version__ = importlib.metadata.version("asebytes")
