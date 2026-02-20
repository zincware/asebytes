"""Tests for inconsistent/missing data across frames, ported from ZnH5MD.

Covers frames where some have calc results and others don't, and frames
where velocities appear only on some entries.
"""

import typing as t

import numpy as np
import numpy.testing as npt
import pytest

import asebytes


def test_keys_missing(db_path, s22, s22_energy_forces):
    """Mix frames with and without calc, verify round-trip."""
    io = asebytes.ASEIO(db_path)

    images = s22_energy_forces + s22
    io.extend(images)
    assert len(io) == len(images)
    assert len(list(io)) == len(images)

    for a, b in zip(images, io):
        assert a == b
        if b.calc is not None:
            for key in b.calc.results:
                npt.assert_array_equal(a.calc.results[key], b.calc.results[key])
        else:
            assert a.calc is None


@pytest.mark.parametrize("state", ["before", "middle", "after"])
def test_velocity(db_path, s22, state: t.Literal["before", "middle", "after"]):
    """Velocities set on only one frame; verify they survive round-trip."""
    io = asebytes.ASEIO(db_path)

    rng = np.random.RandomState(99)
    velocity = None

    images = s22
    if state == "before":
        velocity = rng.random((len(images[0]), 3)) * 0.1
        images[0].set_velocities(velocity)
    elif state == "middle":
        velocity = rng.random((len(images[1]), 3)) * 0.1
        images[1].set_velocities(velocity)
    elif state == "after":
        velocity = rng.random((len(images[-1]), 3)) * 0.1
        images[-1].set_velocities(velocity)

    io.extend(images)
    assert len(io) == len(images)
    assert len(list(io)) == len(images)

    if state == "before":
        npt.assert_array_almost_equal(io[0].get_velocities(), velocity)
    elif state == "middle":
        npt.assert_array_almost_equal(io[1].get_velocities(), velocity)
    elif state == "after":
        npt.assert_array_almost_equal(io[-1].get_velocities(), velocity)
