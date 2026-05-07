"""JSON encoder/decoder for ase.Atoms via the asebytes binary envelope."""

import base64
import json
from typing import Any

import ase
import msgpack
import msgpack_numpy as m

from .decode import decode
from .encode import encode

_packb = msgpack.packb
_unpackb = msgpack.unpackb
_m_encode = m.encode
_m_decode = m.decode

_ENVELOPE_VERSION = 1
_ENVELOPE_KEY = "__asebytes__"


def _atoms_object_hook(obj: dict[str, Any]) -> Any:
    """Decode an asebytes envelope back to ase.Atoms.

    Parameters
    ----------
    obj : dict
        A JSON object passed in by ``json.loads``.

    Returns
    -------
    Any
        ``ase.Atoms`` if ``obj`` is an asebytes envelope, otherwise ``obj``
        unchanged.

    Raises
    ------
    ValueError
        If ``obj`` carries the envelope marker but with an unsupported version.
    """
    version = obj.get(_ENVELOPE_KEY)
    if version is None:
        return obj
    if version != _ENVELOPE_VERSION:
        raise ValueError(
            f"Unsupported asebytes envelope version: {version!r} "
            f"(expected {_ENVELOPE_VERSION})"
        )
    packed = base64.b64decode(obj["data"])
    return decode(_unpackb(packed, object_hook=_m_decode))


class AtomsEncoder(json.JSONEncoder):
    """JSONEncoder that serializes ase.Atoms via the asebytes envelope.

    Use with ``json.dumps(obj, cls=AtomsEncoder)``. Handles single
    ``ase.Atoms``, lists of Atoms, and Atoms nested anywhere in the
    input tree. Subclasses may override :meth:`default` for additional
    types and call ``super().default(obj)`` to delegate.
    """

    def default(self, obj: Any) -> Any:
        """Serialize an ase.Atoms object as an asebytes envelope.

        Parameters
        ----------
        obj : Any
            The object the JSON encoder cannot serialize natively.

        Returns
        -------
        Any
            For ``ase.Atoms`` instances, a JSON-serializable envelope
            dict ``{"__asebytes__": 1, "data": "<base64>"}``.  For all
            other types, delegates to :meth:`json.JSONEncoder.default`,
            which raises ``TypeError``.
        """
        if isinstance(obj, ase.Atoms):
            packed = _packb(encode(obj), default=_m_encode)
            return {
                _ENVELOPE_KEY: _ENVELOPE_VERSION,
                "data": base64.b64encode(packed).decode("ascii"),
            }
        return super().default(obj)


class AtomsDecoder(json.JSONDecoder):
    """JSONDecoder that reconstructs ase.Atoms from asebytes envelopes.

    Use with ``json.loads(s, cls=AtomsDecoder)``. Returns a single
    ``ase.Atoms`` when the JSON root is an envelope, a list when the
    root is an array of envelopes, or the recursively-decoded
    structure when Atoms appear nested inside.
    """

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("object_hook", _atoms_object_hook)
        super().__init__(**kwargs)
