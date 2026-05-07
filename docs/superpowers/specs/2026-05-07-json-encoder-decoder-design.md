# JSON Encoder/Decoder for ase.Atoms

**Date:** 2026-05-07
**Status:** Design
**Branch:** `feat/json-encoder-decoder`

## Summary

Add `asebytes.AtomsEncoder` and `asebytes.AtomsDecoder` so that
`ase.Atoms` instances can be serialized to and from JSON via the stdlib
`json` module. Reuses the existing `encode()` / `decode()` machinery
under a base64-of-msgpack envelope. No new top-level functions; the
public API is two `json.JSONEncoder` / `json.JSONDecoder` subclasses.

## Motivation

`asebytes.encode(atoms)` produces `dict[bytes, bytes]` and `decode`
inverts it. Both are binary-only and cannot be embedded in JSON
payloads (REST APIs, log records, config files, websocket messages).
Users currently have to hand-roll base64 wrappers around `encode()`.

ASE ships `ase.io.jsonio`, but its serialization is more limited than
asebytes' flat-key convention (`arrays.x` / `info.y` / `calc.z`) and
does not interoperate with the rest of the asebytes IO stack.

## Goals

- One-line embedding of `ase.Atoms` in any JSON document via stdlib
  `json` plus a `cls=` argument.
- Support single `Atoms`, top-level lists of `Atoms`, and `Atoms`
  nested anywhere inside arbitrary user JSON.
- Minimal output size; reuse existing binary path.
- Forward-compatible wire format (versioned envelope).
- No new third-party dependencies.

## Non-goals

- Human-readable JSON output. The envelope's `data` field is opaque
  base64. If readability matters, users decode and inspect the
  resulting `Atoms`.
- Streaming / chunked decoding. JSON is loaded whole into memory by
  the stdlib; we do not change that.
- Compression beyond what msgpack provides natively. May be revisited
  later as an opt-in option.
- Convenience `dumps`/`loads` wrappers. Stdlib `json.dumps(...,
  cls=AtomsEncoder)` is short enough and preserves all stdlib options
  (`indent`, `sort_keys`, custom `default` chaining).

## Wire format

A single `Atoms` instance becomes:

```json
{"__asebytes__": 1, "data": "<base64-of-msgpack-of-encode(atoms)>"}
```

- `__asebytes__` is the discriminator key. The `object_hook` uses it
  to tell our envelopes apart from arbitrary user dicts. Double
  underscores follow the convention used by numpy
  (`__ndarray__`) and msgpack-numpy.
- The integer value is a format version. `1` is the initial version.
  Decoder rejects unknown versions with `ValueError`.
- `data` is `base64.b64encode(msgpack.packb(encode(atoms), default=m.encode)).decode("ascii")`.

A list of `Atoms` becomes a JSON array of envelopes:

```json
[{"__asebytes__": 1, "data": "..."}, {"__asebytes__": 1, "data": "..."}]
```

`Atoms` nested inside user structures appear in place as envelopes:

```json
{"meta": {"name": "run-42"}, "frames": [{"__asebytes__": 1, "data": "..."}, ...]}
```

## Public API

```python
# src/asebytes/_json.py

class AtomsEncoder(json.JSONEncoder):
    """JSONEncoder that serializes ase.Atoms via the asebytes envelope.

    Use with json.dumps(obj, cls=AtomsEncoder). Handles single Atoms,
    lists of Atoms, and Atoms nested anywhere in the input tree.
    Subclasses may override default() for additional types and call
    super().default(obj) to delegate.
    """

    def default(self, obj: Any) -> Any: ...


class AtomsDecoder(json.JSONDecoder):
    """JSONDecoder that reconstructs ase.Atoms from asebytes envelopes.

    Use with json.loads(s, cls=AtomsDecoder). Returns a single Atoms
    when the JSON root is an envelope, a list when the root is an
    array of envelopes, or the recursively-decoded structure when
    Atoms appear nested inside.
    """

    def __init__(self, **kwargs: Any) -> None: ...
```

Both are re-exported from `asebytes.__init__`.

### Private implementation

```python
# src/asebytes/_json.py

import base64
import json
from typing import Any

import ase
import msgpack
import msgpack_numpy as m

from .decode import decode
from .encode import encode

_ENVELOPE_VERSION = 1
_ENVELOPE_KEY = "__asebytes__"


def _atoms_object_hook(obj: dict[str, Any]) -> Any:
    version = obj.get(_ENVELOPE_KEY)
    if version is None:
        return obj
    if version != _ENVELOPE_VERSION:
        raise ValueError(
            f"Unsupported asebytes envelope version: {version!r} "
            f"(expected {_ENVELOPE_VERSION})"
        )
    packed = base64.b64decode(obj["data"])
    return decode(msgpack.unpackb(packed, object_hook=m.decode))


class AtomsEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, ase.Atoms):
            packed = msgpack.packb(encode(obj), default=m.encode)
            return {
                _ENVELOPE_KEY: _ENVELOPE_VERSION,
                "data": base64.b64encode(packed).decode("ascii"),
            }
        return super().default(obj)


class AtomsDecoder(json.JSONDecoder):
    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("object_hook", _atoms_object_hook)
        super().__init__(**kwargs)
```

## Usage

```python
import json
import asebytes

# Single Atoms
s = json.dumps(atoms, cls=asebytes.AtomsEncoder)
atoms2 = json.loads(s, cls=asebytes.AtomsDecoder)

# List of Atoms
s = json.dumps([a, b, c], cls=asebytes.AtomsEncoder)
frames = json.loads(s, cls=asebytes.AtomsDecoder)  # list[Atoms]

# Atoms nested in arbitrary structure
payload = {"meta": {"name": "run-42"}, "frames": [a, b]}
s = json.dumps(payload, cls=asebytes.AtomsEncoder)
loaded = json.loads(s, cls=asebytes.AtomsDecoder)
# loaded == {"meta": {"name": "run-42"}, "frames": [Atoms, Atoms]}

# Subclassing for additional types
class MyEncoder(asebytes.AtomsEncoder):
    def default(self, obj):
        if isinstance(obj, MyType):
            return obj.to_json()
        return super().default(obj)
```

## Behavior

- `AtomsEncoder.default(obj)`: if `isinstance(obj, ase.Atoms)`, return
  the envelope dict; otherwise call `super().default(obj)` (which
  raises `TypeError` for unsupported types — standard
  `json.JSONEncoder` contract). Subclasses can override and chain.
- `AtomsDecoder.__init__`: sets `object_hook=_atoms_object_hook` via
  `setdefault`, so a user-supplied `object_hook` keyword wins. All
  other stdlib kwargs (`object_pairs_hook`, `parse_float`, etc.) pass
  through unchanged.
- `_atoms_object_hook(obj)`: if `obj` carries `__asebytes__`, decode
  and return `Atoms`; otherwise return `obj` unchanged. Unknown
  versions raise `ValueError`.

## Error handling

- Encoding a non-`Atoms` unsupported type → `TypeError` (from
  `super().default()`, standard `json.JSONEncoder` behavior).
- Decoding a malformed envelope (missing `data`, bad base64, bad
  msgpack, malformed inner dict) → propagate the underlying exception
  unchanged. We do not swallow.
- Decoding an envelope with an unknown `__asebytes__` version →
  `ValueError` with the offending version in the message.
- Plain dicts that happen to contain a key named `__asebytes__` from a
  user (not us) → only treated as an envelope if the value matches a
  known version. Any other value raises `ValueError` (we treat
  collisions as user error rather than silently ignoring; users who
  truly need that key should pass their own `object_hook`).

## Testing

Tests live in `tests/test_json.py` (sync, no async coverage needed —
encoder/decoder are pure functions of input data).

- **Roundtrip — single Atoms**: Atoms with assorted `arrays.*`,
  `info.*`, `calc.*`, and `constraints` all roundtrip equal to the
  original.
- **Roundtrip — list**: `[a, b, c]` roundtrips to a list of `Atoms`.
- **Roundtrip — empty list**: `[]` roundtrips to `[]`.
- **Roundtrip — nested**: `{"meta": {...}, "frames": [a, b]}`
  roundtrips with metadata preserved and frames decoded.
- **Roundtrip — atoms-as-dict-value at depth**: `{"a": {"b": atoms}}`.
- **Encoder fallthrough**: `json.dumps(object(), cls=AtomsEncoder)`
  raises `TypeError`.
- **Encoder subclass chaining**: a subclass that handles an
  additional type still serializes Atoms via the base class.
- **Decoder fallthrough**: regular dicts (no `__asebytes__` key)
  pass through unchanged.
- **Decoder version mismatch**: forging
  `{"__asebytes__": 999, "data": ""}` raises `ValueError`.
- **Decoder subclass `object_hook` override**: a user subclass of
  `AtomsDecoder` that passes its own `object_hook` to `super().__init__`
  has its hook win (because the implementation uses `setdefault`,
  which only fills missing keys).
- **Wire format pinning**: at least one snapshot test asserts the
  literal envelope shape for a fixed Atoms input, so future changes to
  the format are caught explicitly.

## File layout

- `src/asebytes/_json.py` — new module containing the implementation.
- `src/asebytes/__init__.py` — add `AtomsEncoder` and `AtomsDecoder`
  imports and entries in `__all__`.
- `tests/test_json.py` — new test module.
- `README.md` — short example block under a new "JSON" subsection.
- No changes to existing modules.

## Risks and open questions

- **Format evolution**: when we eventually need to change the inner
  encoding (e.g., add zstd compression), the version field is the
  hook. New encoder writes version 2; old decoder rejects with a
  clear error. Acceptable.
- **Cross-language consumers**: a non-Python client receiving the
  envelope sees an opaque base64 string. They need msgpack +
  msgpack-numpy and an asebytes-compatible decoder. Documented as a
  Python-to-Python format.
- **`__asebytes__` collisions**: extremely unlikely in user data.
  Documented; users can pass their own `object_hook`.
