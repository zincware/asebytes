"""Round-trip dataset tests ported from ZnH5MD, run against all writable backends.

Tests verify that diverse ASE datasets (varying atom counts, calc properties,
info/arrays metadata, PBC, velocities) survive a write→read round-trip.
"""

import numpy as np
import numpy.testing as npt
import pytest

import asebytes


# -- Helpers ----------------------------------------------------------------


def assert_atoms_roundtrip(a, b):
    """Full round-trip assertion: positions, numbers, cell, pbc, calc, arrays, info."""
    npt.assert_array_equal(a.get_atomic_numbers(), b.get_atomic_numbers())
    npt.assert_array_equal(a.get_positions(), b.get_positions())
    npt.assert_array_equal(a.get_cell(), b.get_cell())
    npt.assert_array_equal(a.get_pbc(), b.get_pbc())

    vel_a = a.get_velocities()
    vel_b = b.get_velocities()
    if vel_a is not None:
        npt.assert_array_equal(vel_a, vel_b)
    else:
        assert vel_b is None or np.allclose(vel_b, 0)

    if a.calc is not None:
        assert b.calc is not None
        assert set(a.calc.results) == set(b.calc.results)
        for key in a.calc.results:
            npt.assert_array_equal(a.calc.results[key], b.calc.results[key])
        if "energy" in a.calc.results:
            assert isinstance(b.calc.results["energy"], float)
    else:
        assert b.calc is None

    assert set(a.arrays) == set(b.arrays)
    for key in a.arrays:
        npt.assert_array_equal(a.arrays[key], b.arrays[key])

    assert set(b.info) == set(a.info)
    for key in a.info:
        npt.assert_array_equal(a.info[key], b.info[key])


# -- Dataset round-trip tests -----------------------------------------------


@pytest.mark.parametrize(
    "dataset",
    [
        "s22",
        "s22_energy",
        "s22_all_properties",
        "s22_info_arrays_calc",
        "s22_mixed_pbc_cell",
        "s22_illegal_calc_results",
        "water",
        "s22_nested_calc",
    ],
)
def test_datasets(db_path, dataset, request):
    """Write a full dataset, read back, and verify every frame."""
    images = request.getfixturevalue(dataset)
    io = asebytes.ASEIO(db_path)
    io.extend(images)
    images2 = list(io[:])

    assert len(images) == len(images2)

    for a, b in zip(images, images2):
        assert_atoms_roundtrip(a, b)


# -- PBC round-trip ---------------------------------------------------------


def test_pbc(db_path, s22_mixed_pbc_cell):
    """Verify per-frame PBC and cell survive round-trip."""
    io = asebytes.ASEIO(db_path)
    io.extend(s22_mixed_pbc_cell)

    for idx, ref in enumerate(s22_mixed_pbc_cell):
        rec = io[idx]
        npt.assert_array_equal(rec.get_pbc(), ref.get_pbc())
        npt.assert_array_equal(rec.get_cell(), ref.get_cell())


# -- Save → Load → Save → Load ---------------------------------------------


def test_save_load_save_load(db_path, s22_mixed_pbc_cell, tmp_path):
    """Write, read back, write to new file, read again → same length."""
    io1 = asebytes.ASEIO(db_path)
    io1.extend(s22_mixed_pbc_cell)

    images = list(io1[:])

    ext = db_path.rsplit(".", 1)[-1]
    db_path2 = str(tmp_path / f"test2.{ext}")
    io2 = asebytes.ASEIO(db_path2)
    io2.extend(images)

    images2 = list(io2[:])
    assert len(images) == len(images2)


# -- Slicing ----------------------------------------------------------------


def test_slicing(db_path, s22_mixed_pbc_cell):
    """Verify various slice patterns against reference list."""
    io = asebytes.ASEIO(db_path)
    io.extend(s22_mixed_pbc_cell)
    ref = s22_mixed_pbc_cell

    assert len(io) == len(ref)

    # Single element access
    assert io[0] == ref[0]
    assert io[len(io) - 1] == ref[len(ref) - 1]

    # Simple slices
    assert list(io[:10]) == ref[:10]
    assert list(io[10:20]) == ref[10:20]
    assert list(io[-10:]) == ref[-10:]
    assert list(io[:-10]) == ref[:-10]

    # Step slices
    assert list(io[::2]) == ref[::2]
    assert list(io[1::2]) == ref[1::2]

    # Complex slices
    assert list(io[5:20:3]) == ref[5:20:3]
    assert list(io[-20:-5:2]) == ref[-20:-5:2]

    # Empty slices
    assert list(io[5:5]) == ref[5:5]
    assert list(io[-5:-5]) == ref[-5:-5]

    # Length unchanged
    assert len(io) == len(ref)
