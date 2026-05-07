"""Tests for asebytes JSON encoder/decoder."""

import base64
import json

import numpy as np
import pytest

import asebytes


def test_single_atoms_roundtrip(simple_atoms):
    """A single Atoms roundtrips equal through json.dumps/loads."""
    s = json.dumps(simple_atoms, cls=asebytes.AtomsEncoder)
    assert isinstance(s, str)
    recovered = json.loads(s, cls=asebytes.AtomsDecoder)
    assert recovered == simple_atoms


def test_list_of_atoms_roundtrip(ethanol):
    """A top-level list of Atoms roundtrips to a list of equal Atoms."""
    frames = ethanol[:5]
    s = json.dumps(frames, cls=asebytes.AtomsEncoder)
    recovered = json.loads(s, cls=asebytes.AtomsDecoder)
    assert isinstance(recovered, list)
    assert len(recovered) == len(frames)
    for original, decoded in zip(frames, recovered):
        assert decoded == original


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


def test_empty_list_roundtrip():
    """An empty list roundtrips to an empty list."""
    s = json.dumps([], cls=asebytes.AtomsEncoder)
    assert json.loads(s, cls=asebytes.AtomsDecoder) == []


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


def test_encoder_rejects_unsupported_type():
    """Unsupported types raise TypeError via super().default()."""

    class Mystery:
        pass

    with pytest.raises(TypeError):
        json.dumps(Mystery(), cls=asebytes.AtomsEncoder)


def test_decoder_rejects_unknown_version():
    """An envelope with an unknown version raises ValueError."""
    forged = json.dumps({"__asebytes__": 999, "data": ""})
    with pytest.raises(ValueError, match="Unsupported asebytes envelope"):
        json.loads(forged, cls=asebytes.AtomsDecoder)


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
    payload = base64.b64decode(raw["data"])
    assert len(payload) > 0
