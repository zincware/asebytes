import importlib.metadata

from .from_bytes import from_bytes
from .io import ASEIO, BytesIO
from .to_bytes import to_bytes

__all__ = ["to_bytes", "from_bytes", "BytesIO", "ASEIO"]

__version__ = importlib.metadata.version("asebytes")
