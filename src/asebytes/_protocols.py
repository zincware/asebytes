"""Backward compatibility -- deprecated aliases for _backends.py classes."""

from typing_extensions import deprecated

from ._backends import ReadBackend, ReadWriteBackend


@deprecated(
    "Use ReadBackend from asebytes._backends instead",
    category=DeprecationWarning,
    stacklevel=2,
)
class RawReadableBackend(ReadBackend):
    """Deprecated alias for ReadBackend."""


@deprecated(
    "Use ReadWriteBackend from asebytes._backends instead",
    category=DeprecationWarning,
    stacklevel=2,
)
class RawWritableBackend(ReadWriteBackend):
    """Deprecated alias for ReadWriteBackend."""


@deprecated(
    "Use ReadBackend from asebytes._backends instead",
    category=DeprecationWarning,
    stacklevel=2,
)
class ReadableBackend(ReadBackend):
    """Deprecated alias for ReadBackend."""


@deprecated(
    "Use ReadWriteBackend from asebytes._backends instead",
    category=DeprecationWarning,
    stacklevel=2,
)
class WritableBackend(ReadWriteBackend):
    """Deprecated alias for ReadWriteBackend."""


__all__ = [
    "RawReadableBackend",
    "RawWritableBackend",
    "ReadableBackend",
    "WritableBackend",
]
