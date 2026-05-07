"""Tests for asebytes JSON encoder/decoder."""

import json

import asebytes


def test_single_atoms_roundtrip(simple_atoms):
    """A single Atoms roundtrips equal through json.dumps/loads."""
    s = json.dumps(simple_atoms, cls=asebytes.AtomsEncoder)
    assert isinstance(s, str)
    recovered = json.loads(s, cls=asebytes.AtomsDecoder)
    assert recovered == simple_atoms
