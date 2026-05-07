"""Tests for asebytes JSON encoder/decoder."""

import json

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
