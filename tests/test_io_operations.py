"""Core IO tests ported from ZnH5MD, run against all writable backends.

Tests extend, append, length, empty-extend, single-frame with complex info,
and index error handling.
"""

import ase.build
import ase.collections
import numpy as np
import numpy.testing as npt
import pytest

import asebytes


def test_extend(db_path):
    """Extend with s22 collection, verify positions and numbers."""
    io = asebytes.ASEIO(db_path)
    images = list(ase.collections.s22)
    io.extend(images)

    structures = list(io[:])
    assert len(structures) == len(images)
    for a, b in zip(images, structures):
        assert np.array_equal(a.get_atomic_numbers(), b.get_atomic_numbers())
        assert np.allclose(a.get_positions(), b.get_positions())


def test_len(db_path, s22_info_arrays_calc):
    """Length matches after extending with s22 datset."""
    io = asebytes.ASEIO(db_path)
    io.extend(s22_info_arrays_calc)
    assert len(io) == 22


def test_append(db_path):
    """Extend then append one more frame."""
    io = asebytes.ASEIO(db_path)
    images = list(ase.collections.s22)
    io.extend(images)
    io.extend([images[0]])  # append via extend([single])

    assert len(io) == len(images) + 1
    for a, b in zip(images + [images[0]], list(io[:])):
        assert np.array_equal(a.get_atomic_numbers(), b.get_atomic_numbers())
        assert np.allclose(a.get_positions(), b.get_positions())


def test_extend_empty(db_path):
    """Extending with empty list should not change length or crash."""
    io = asebytes.ASEIO(db_path)
    io.extend(list(ase.collections.s22))

    assert len(io) == 22
    io.extend([])
    assert len(io) == 22


def test_extend_single(db_path):
    """Single frame with high-dimensional info array."""
    vectors = np.random.rand(3, 3, 2, 3)

    water = ase.build.molecule("H2O")
    water.info["vectors"] = vectors

    io = asebytes.ASEIO(db_path)
    io.extend([water])

    assert len(io) == 1
    assert np.allclose(io[0].info["vectors"], vectors)
    assert io[0].info["vectors"].shape == vectors.shape


def test_index_error(db_path):
    """Out-of-range positive index raises IndexError."""
    io = asebytes.ASEIO(db_path)

    water = ase.build.molecule("H2O")
    io.extend([water])

    assert io[0] is not None
    assert io[-1] is not None
    assert list(io[0:1]) is not None
    assert list(io[0:2]) is not None
    with pytest.raises(IndexError):
        io[1]


def test_negative_index_error(db_path):
    """Out-of-range negative index raises IndexError."""
    io = asebytes.ASEIO(db_path)

    water = ase.build.molecule("H2O")
    io.extend([water])

    with pytest.raises(IndexError):
        io[-2]


def test_inconsistent_missing_inbetween(db_path, s22_info_arrays_calc_missing_inbetween):
    """Frames with randomly missing info/arrays/calc keys round-trip."""
    images = s22_info_arrays_calc_missing_inbetween
    io = asebytes.ASEIO(db_path)
    io.extend(images)

    assert len(io) == len(images)
    for i, ref in enumerate(images):
        rec = io[i]
        npt.assert_array_equal(rec.get_positions(), ref.get_positions())
        npt.assert_array_equal(rec.get_atomic_numbers(), ref.get_atomic_numbers())
        if ref.calc is not None:
            assert rec.calc is not None
            assert set(rec.calc.results) == set(ref.calc.results)
            for key in ref.calc.results:
                npt.assert_array_equal(rec.calc.results[key], ref.calc.results[key])
        else:
            assert rec.calc is None
