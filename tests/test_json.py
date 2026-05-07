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
