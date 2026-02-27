"""Backward compatibility -- deprecated aliases for _async_backends.py classes."""

from typing_extensions import deprecated

from ._async_backends import (
    AsyncReadBackend,
    AsyncReadWriteBackend,
    SyncToAsyncAdapter,
)


@deprecated(
    "Use AsyncReadBackend from asebytes._async_backends instead",
    category=DeprecationWarning,
    stacklevel=2,
)
class AsyncRawReadableBackend(AsyncReadBackend):
    """Deprecated alias for AsyncReadBackend."""


@deprecated(
    "Use AsyncReadWriteBackend from asebytes._async_backends instead",
    category=DeprecationWarning,
    stacklevel=2,
)
class AsyncRawWritableBackend(AsyncReadWriteBackend):
    """Deprecated alias for AsyncReadWriteBackend."""


@deprecated(
    "Use AsyncReadBackend from asebytes._async_backends instead",
    category=DeprecationWarning,
    stacklevel=2,
)
class AsyncReadableBackend(AsyncReadBackend):
    """Deprecated alias for AsyncReadBackend."""


@deprecated(
    "Use AsyncReadWriteBackend from asebytes._async_backends instead",
    category=DeprecationWarning,
    stacklevel=2,
)
class AsyncWritableBackend(AsyncReadWriteBackend):
    """Deprecated alias for AsyncReadWriteBackend."""


@deprecated(
    "Use SyncToAsyncAdapter from asebytes._async_backends instead",
    category=DeprecationWarning,
    stacklevel=2,
)
class SyncToAsyncRawAdapter(SyncToAsyncAdapter):
    """Deprecated alias for SyncToAsyncAdapter."""


__all__ = [
    "AsyncRawReadableBackend",
    "AsyncRawWritableBackend",
    "AsyncReadableBackend",
    "AsyncWritableBackend",
    "SyncToAsyncRawAdapter",
]
