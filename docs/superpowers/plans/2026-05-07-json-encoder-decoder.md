# JSON Encoder/Decoder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `asebytes.AtomsEncoder` / `asebytes.AtomsDecoder` so `ase.Atoms` instances can be serialized through stdlib `json` via `cls=`. The wire format is a versioned base64-of-msgpack envelope reusing the existing `encode()` / `decode()` path.

**Architecture:** A single new private module `src/asebytes/_json.py` containing two `json.JSONEncoder` / `json.JSONDecoder` subclasses and one private `object_hook` helper. No new dependencies. Re-exported from the top-level package.

**Tech Stack:** Python 3.11+, `json` (stdlib), `base64` (stdlib), `msgpack`, `msgpack-numpy`, `ase`, `pytest`. Project tooling is `uv` — every command below uses `uv run …`.

**Spec:** `docs/superpowers/specs/2026-05-07-json-encoder-decoder-design.md`

**Branch:** Already on `feat/json-encoder-decoder`.

---

## Background you will need

The new module reuses two existing functions verbatim:

- `asebytes.encode(atoms: ase.Atoms) -> dict[bytes, bytes]` — defined in `src/asebytes/encode.py`. Produces a flat dict whose keys are short byte strings (`b"cell"`, `b"pbc"`, `b"arrays.positions"`, `b"info.smiles"`, `b"calc.energy"`, `b"constraints"`) and whose values are individually msgpack-packed bytes.
- `asebytes.decode(data: dict[bytes, bytes], fast=True, copy=True) -> ase.Atoms` — defined in `src/asebytes/decode.py`. Inverts `encode`.

The new module wraps the dict as a whole: `msgpack.packb(encode(atoms), default=msgpack_numpy.encode)` → bytes → base64 → JSON string field. On the way back: base64 decode → `msgpack.unpackb(..., object_hook=msgpack_numpy.decode)` → dict[bytes, bytes] → `decode(...)`.

Test fixtures already exist in `tests/conftest.py` and you should reuse them:
- `simple_atoms` — minimal H2O Atoms.
- `atoms_with_info` — Atoms with custom `info.*` entries.
- `atoms_with_calc` — Atoms with a `SinglePointCalculator`.
- `atoms_with_pbc` — Atoms with cell + pbc.
- `atoms_with_constraints` — Atoms with `FixAtoms`.
- `empty_atoms` — Atoms with no atoms.
- `ethanol` — 1000 ethanol conformers with full calc/info/arrays (use indexing for single-frame tests).

ASE's `ase.Atoms.__eq__` compares positions, numbers, cell, pbc, and `info` deeply enough for our roundtrip checks. Existing tests in `tests/test_to_and_from_bytes.py` use `assert atoms == recovered_atoms` — follow that pattern.

**Project conventions you must follow:**
- Use `uv run pytest …`, not bare `pytest`.
- Numpy-style docstrings.
- Never modify any test marked `@pytest.mark.protected` (none in scope here, but be aware).
- Frequent commits — one per task.

---

## File structure

| File | Purpose | Action |
|---|---|---|
| `src/asebytes/_json.py` | New module: `AtomsEncoder`, `AtomsDecoder`, private `_atoms_object_hook`, version constant. | Create |
| `src/asebytes/__init__.py` | Add imports + `__all__` entries for `AtomsEncoder` and `AtomsDecoder`. | Modify |
| `tests/test_json.py` | All tests for the new module. | Create |
| `README.md` | Short subsection demonstrating `json.dumps(atoms, cls=asebytes.AtomsEncoder)`. | Modify |

No other files change.

---

### Task 1: Scaffold the module and prove a single-Atoms roundtrip

**Files:**
- Create: `src/asebytes/_json.py`
- Create: `tests/test_json.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_json.py` with:

```python
"""Tests for asebytes JSON encoder/decoder."""

import json

import asebytes


def test_single_atoms_roundtrip(simple_atoms):
    """A single Atoms roundtrips equal through json.dumps/loads."""
    s = json.dumps(simple_atoms, cls=asebytes.AtomsEncoder)
    assert isinstance(s, str)
    recovered = json.loads(s, cls=asebytes.AtomsDecoder)
    assert recovered == simple_atoms
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_json.py::test_single_atoms_roundtrip -v
```

Expected: `AttributeError: module 'asebytes' has no attribute 'AtomsEncoder'`.

- [ ] **Step 3: Create the module**

Create `src/asebytes/_json.py`:

```python
"""JSON encoder/decoder for ase.Atoms via the asebytes binary envelope."""

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
    return decode(msgpack.unpackb(packed, object_hook=m.decode))


class AtomsEncoder(json.JSONEncoder):
    """JSONEncoder that serializes ase.Atoms via the asebytes envelope.

    Use with ``json.dumps(obj, cls=AtomsEncoder)``. Handles single
    ``ase.Atoms``, lists of Atoms, and Atoms nested anywhere in the
    input tree. Subclasses may override :meth:`default` for additional
    types and call ``super().default(obj)`` to delegate.
    """

    def default(self, obj: Any) -> Any:
        if isinstance(obj, ase.Atoms):
            packed = msgpack.packb(encode(obj), default=m.encode)
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
```

- [ ] **Step 4: Wire the public API**

Edit `src/asebytes/__init__.py`. Find the block of relative imports (the section that imports from `.io`, `.memory`, `.metadata`) and add this import next to them:

```python
from ._json import AtomsEncoder, AtomsDecoder
```

In the `__all__` list, add the two names (place them next to other utility exports like `"encode"`, `"decode"`):

```python
    "AtomsEncoder",
    "AtomsDecoder",
```

- [ ] **Step 5: Run test to verify it passes**

```bash
uv run pytest tests/test_json.py::test_single_atoms_roundtrip -v
```

Expected: `1 passed`.

- [ ] **Step 6: Commit**

```bash
git add src/asebytes/_json.py src/asebytes/__init__.py tests/test_json.py
git commit -m "feat: add AtomsEncoder/AtomsDecoder for JSON serialization

Reuses encode/decode through a base64(msgpack) envelope. Public API
is two stdlib JSONEncoder/JSONDecoder subclasses; no new top-level
functions and no new dependencies."
```

---

### Task 2: Roundtrip a top-level list of Atoms

**Files:**
- Modify: `tests/test_json.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_json.py`:

```python
def test_list_of_atoms_roundtrip(ethanol):
    """A top-level list of Atoms roundtrips to a list of equal Atoms."""
    frames = ethanol[:5]
    s = json.dumps(frames, cls=asebytes.AtomsEncoder)
    recovered = json.loads(s, cls=asebytes.AtomsDecoder)
    assert isinstance(recovered, list)
    assert len(recovered) == len(frames)
    for original, decoded in zip(frames, recovered):
        assert decoded == original
```

- [ ] **Step 2: Run the test**

```bash
uv run pytest tests/test_json.py::test_list_of_atoms_roundtrip -v
```

Expected: `1 passed`. (No implementation change needed — stdlib's encoder iterates the list and calls `default()` per Atoms.)

- [ ] **Step 3: Commit**

```bash
git add tests/test_json.py
git commit -m "test: cover list-of-atoms roundtrip"
```

---

### Task 3: Roundtrip Atoms nested inside arbitrary user JSON

**Files:**
- Modify: `tests/test_json.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_json.py`:

```python
def test_nested_atoms_roundtrip(simple_atoms, atoms_with_calc):
    """Atoms nested inside dicts and lists at depth roundtrip in place."""
    payload = {
        "meta": {"name": "run-42", "n_frames": 2},
        "frames": [simple_atoms, atoms_with_calc],
        "tags": ["a", "b"],
    }
    s = json.dumps(payload, cls=asebytes.AtomsEncoder)
    recovered = json.loads(s, cls=asebytes.AtomsDecoder)

    assert recovered["meta"] == {"name": "run-42", "n_frames": 2}
    assert recovered["tags"] == ["a", "b"]
    assert len(recovered["frames"]) == 2
    assert recovered["frames"][0] == simple_atoms
    assert recovered["frames"][1] == atoms_with_calc


def test_deeply_nested_atoms_roundtrip(simple_atoms):
    """Atoms as a value many levels deep still roundtrips."""
    payload = {"a": {"b": {"c": simple_atoms}}}
    s = json.dumps(payload, cls=asebytes.AtomsEncoder)
    recovered = json.loads(s, cls=asebytes.AtomsDecoder)
    assert recovered["a"]["b"]["c"] == simple_atoms
```

- [ ] **Step 2: Run the tests**

```bash
uv run pytest tests/test_json.py -k nested -v
```

Expected: `2 passed`.

- [ ] **Step 3: Commit**

```bash
git add tests/test_json.py
git commit -m "test: cover nested-atoms-in-user-json roundtrip"
```

---

### Task 4: Roundtrip an empty list

**Files:**
- Modify: `tests/test_json.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_json.py`:

```python
def test_empty_list_roundtrip():
    """An empty list roundtrips to an empty list."""
    s = json.dumps([], cls=asebytes.AtomsEncoder)
    assert json.loads(s, cls=asebytes.AtomsDecoder) == []
```

- [ ] **Step 2: Run the test**

```bash
uv run pytest tests/test_json.py::test_empty_list_roundtrip -v
```

Expected: `1 passed`.

- [ ] **Step 3: Commit**

```bash
git add tests/test_json.py
git commit -m "test: cover empty-list roundtrip"
```

---

### Task 5: Cover all asebytes-supported Atoms features

**Files:**
- Modify: `tests/test_json.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_json.py`. Reuses every feature-bearing fixture from `conftest.py`:

```python
import numpy as np
import pytest


@pytest.mark.parametrize(
    "fixture_name",
    [
        "simple_atoms",
        "h2o_atoms",
        "atoms_with_info",
        "atoms_with_calc",
        "atoms_with_pbc",
        "atoms_with_constraints",
        "empty_atoms",
    ],
)
def test_feature_coverage_roundtrip(fixture_name, request):
    """Every supported Atoms feature roundtrips via the JSON envelope."""
    atoms = request.getfixturevalue(fixture_name)
    s = json.dumps(atoms, cls=asebytes.AtomsEncoder)
    recovered = json.loads(s, cls=asebytes.AtomsDecoder)
    assert recovered == atoms

    # Spot-check arrays survive bit-exact (== on Atoms compares positions
    # but not info/calc payloads in detail).
    for key in atoms.arrays:
        assert np.array_equal(recovered.arrays[key], atoms.arrays[key])
    for key in atoms.info:
        if isinstance(atoms.info[key], np.ndarray):
            assert np.array_equal(recovered.info[key], atoms.info[key])
        else:
            assert recovered.info[key] == atoms.info[key]
    if atoms.calc is not None:
        assert recovered.calc is not None
        for key in atoms.calc.results:
            assert np.array_equal(
                recovered.calc.results[key], atoms.calc.results[key]
            )
```

- [ ] **Step 2: Run the test**

```bash
uv run pytest tests/test_json.py::test_feature_coverage_roundtrip -v
```

Expected: 7 parametrized cases, all pass.

- [ ] **Step 3: Commit**

```bash
git add tests/test_json.py
git commit -m "test: cover info/calc/constraints/pbc roundtrips"
```

---

### Task 6: Encoder rejects unsupported types

**Files:**
- Modify: `tests/test_json.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_json.py`:

```python
def test_encoder_rejects_unsupported_type():
    """Unsupported types raise TypeError via super().default()."""

    class Mystery:
        pass

    with pytest.raises(TypeError):
        json.dumps(Mystery(), cls=asebytes.AtomsEncoder)
```

- [ ] **Step 2: Run the test**

```bash
uv run pytest tests/test_json.py::test_encoder_rejects_unsupported_type -v
```

Expected: `1 passed`.

- [ ] **Step 3: Commit**

```bash
git add tests/test_json.py
git commit -m "test: cover encoder TypeError on unsupported types"
```

---

### Task 7: Decoder rejects unknown envelope versions

**Files:**
- Modify: `tests/test_json.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_json.py`:

```python
def test_decoder_rejects_unknown_version():
    """An envelope with an unknown version raises ValueError."""
    forged = json.dumps({"__asebytes__": 999, "data": ""})
    with pytest.raises(ValueError, match="Unsupported asebytes envelope"):
        json.loads(forged, cls=asebytes.AtomsDecoder)
```

- [ ] **Step 2: Run the test**

```bash
uv run pytest tests/test_json.py::test_decoder_rejects_unknown_version -v
```

Expected: `1 passed` (the `_atoms_object_hook` already raises this).

- [ ] **Step 3: Commit**

```bash
git add tests/test_json.py
git commit -m "test: cover decoder ValueError on unknown envelope version"
```

---

### Task 8: Decoder leaves regular dicts untouched

**Files:**
- Modify: `tests/test_json.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_json.py`:

```python
def test_decoder_passthrough_for_regular_dicts():
    """Dicts without the envelope marker decode as-is."""
    s = json.dumps({"x": 1, "nested": {"y": [1, 2, 3]}})
    recovered = json.loads(s, cls=asebytes.AtomsDecoder)
    assert recovered == {"x": 1, "nested": {"y": [1, 2, 3]}}


def test_decoder_passthrough_for_scalars():
    """Non-object JSON roots decode as-is."""
    assert json.loads("42", cls=asebytes.AtomsDecoder) == 42
    assert json.loads('"hello"', cls=asebytes.AtomsDecoder) == "hello"
    assert json.loads("null", cls=asebytes.AtomsDecoder) is None
```

- [ ] **Step 2: Run the tests**

```bash
uv run pytest tests/test_json.py -k passthrough -v
```

Expected: `2 passed`.

- [ ] **Step 3: Commit**

```bash
git add tests/test_json.py
git commit -m "test: cover decoder passthrough for non-envelope inputs"
```

---

### Task 9: Encoder subclass can extend `default` and still serialize Atoms

**Files:**
- Modify: `tests/test_json.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_json.py`:

```python
def test_encoder_subclass_chains(simple_atoms):
    """A subclass that adds support for one more type still serializes Atoms."""

    class Extra:
        def __init__(self, value):
            self.value = value

    class MyEncoder(asebytes.AtomsEncoder):
        def default(self, obj):
            if isinstance(obj, Extra):
                return {"__extra__": obj.value}
            return super().default(obj)

    payload = {"atoms": simple_atoms, "extra": Extra(42)}
    s = json.dumps(payload, cls=MyEncoder)
    recovered = json.loads(s, cls=asebytes.AtomsDecoder)

    assert recovered["atoms"] == simple_atoms
    assert recovered["extra"] == {"__extra__": 42}
```

- [ ] **Step 2: Run the test**

```bash
uv run pytest tests/test_json.py::test_encoder_subclass_chains -v
```

Expected: `1 passed`.

- [ ] **Step 3: Commit**

```bash
git add tests/test_json.py
git commit -m "test: cover encoder subclass chaining"
```

---

### Task 10: Decoder subclass can override `object_hook`

**Files:**
- Modify: `tests/test_json.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_json.py`:

```python
def test_decoder_subclass_can_override_hook():
    """A subclass passing object_hook to super().__init__ wins via setdefault."""

    sentinel = object()

    def my_hook(obj):
        return sentinel

    class MyDecoder(asebytes.AtomsDecoder):
        def __init__(self, **kwargs):
            super().__init__(object_hook=my_hook, **kwargs)

    s = json.dumps({"x": 1})
    assert json.loads(s, cls=MyDecoder) is sentinel
```

- [ ] **Step 2: Run the test**

```bash
uv run pytest tests/test_json.py::test_decoder_subclass_can_override_hook -v
```

Expected: `1 passed` (setdefault leaves the user-supplied hook in place).

- [ ] **Step 3: Commit**

```bash
git add tests/test_json.py
git commit -m "test: cover decoder subclass object_hook override"
```

---

### Task 11: Pin the wire format with a snapshot test

**Files:**
- Modify: `tests/test_json.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_json.py`. This pins the literal envelope shape so future format changes are caught explicitly:

```python
def test_envelope_shape_is_pinned(simple_atoms):
    """The envelope structure (keys, version, base64-string data) is locked.

    A change to this test means the wire format has changed and the
    version field in src/asebytes/_json.py must be bumped.
    """
    s = json.dumps(simple_atoms, cls=asebytes.AtomsEncoder)
    raw = json.loads(s)  # parse with stdlib, no custom decoder

    assert isinstance(raw, dict)
    assert set(raw.keys()) == {"__asebytes__", "data"}
    assert raw["__asebytes__"] == 1
    assert isinstance(raw["data"], str)
    # data must be valid base64 of non-empty bytes
    import base64
    payload = base64.b64decode(raw["data"])
    assert len(payload) > 0
```

- [ ] **Step 2: Run the test**

```bash
uv run pytest tests/test_json.py::test_envelope_shape_is_pinned -v
```

Expected: `1 passed`.

- [ ] **Step 3: Commit**

```bash
git add tests/test_json.py
git commit -m "test: pin wire format envelope shape"
```

---

### Task 12: Run the whole suite to catch regressions

**Files:** none

- [ ] **Step 1: Run the new test module**

```bash
uv run pytest tests/test_json.py -v
```

Expected: every test from tasks 1–11 passes (15+ test cases including parametrizations).

- [ ] **Step 2: Run the full project suite**

```bash
uv run pytest -x
```

Expected: no regressions. If any test outside `tests/test_json.py` fails, stop and investigate — it should not be possible for this change to affect them, so a failure means an environment issue or an unrelated pre-existing breakage. Report back rather than power through.

- [ ] **Step 3: No commit (verification step only)**

---

### Task 13: README update

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Locate the insertion point**

Open `README.md` and find the section after the three IO layers (`ASEIO` / `ObjectIO` / `BlobIO`). Add a new top-level subsection titled "JSON" immediately after the IO layers but before any later sections (search for the next `##` heading and insert above it).

- [ ] **Step 2: Insert the new subsection**

Add this content:

````markdown
## JSON

Serialize `ase.Atoms` through stdlib `json` using two encoder/decoder classes. The wire format is a compact base64-of-msgpack envelope — the same binary path used by `asebytes.encode` / `asebytes.decode`.

```python
import json

import asebytes

# Single Atoms
s = json.dumps(atoms, cls=asebytes.AtomsEncoder)
atoms2 = json.loads(s, cls=asebytes.AtomsDecoder)

# List of Atoms
s = json.dumps([a, b, c], cls=asebytes.AtomsEncoder)
frames = json.loads(s, cls=asebytes.AtomsDecoder)  # list[ase.Atoms]

# Atoms nested in arbitrary structure
payload = {"meta": {"name": "run-42"}, "frames": [a, b]}
s = json.dumps(payload, cls=asebytes.AtomsEncoder)
loaded = json.loads(s, cls=asebytes.AtomsDecoder)
```

`AtomsEncoder` is a `json.JSONEncoder` subclass — override `default()` in your own subclass to handle additional types.
````

- [ ] **Step 3: Verify the file still renders**

```bash
uv run python -c "import pathlib; print(pathlib.Path('README.md').read_text()[:200])"
```

Expected: prints the first 200 chars without an exception.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: README section for AtomsEncoder/AtomsDecoder"
```

---

## Self-review checklist (already performed)

- **Spec coverage:** every section of `2026-05-07-json-encoder-decoder-design.md` maps to a task. Wire format → Task 1 + Task 11 (pinning). Public API → Task 1. Behavior → Tasks 1–4 + 8. Error handling → Tasks 6 + 7. Tests section → Tasks 2–11. File layout → Tasks 1 + 13.
- **Placeholders:** none. Every code block is complete.
- **Type consistency:** `_ENVELOPE_VERSION`, `_ENVELOPE_KEY`, `_atoms_object_hook`, `AtomsEncoder`, `AtomsDecoder` are referenced consistently across tasks.
- **Test naming:** all tests live in `tests/test_json.py`; selectors used in commands match defined function names.
