import importlib.metadata

from .to_bytes import to_bytes
from .from_bytes import from_bytes
from .io import BytesIO, ASEIO

__all__ = ["to_bytes", "from_bytes", "BytesIO", "ASEIO"]

__version__ = importlib.metadata.version("asebytes")
