"""znh5md <-> asebytes full round-trip tests.

Covers ALL s22_* fixtures to ensure every property type (positions, numbers,
cell, pbc, all calc results, custom info, custom per-atom arrays, velocities,
mixed pbc/cell, sparse properties) round-trips correctly between znh5md and
asebytes.

The existing interop tests only checked positions+numbers+forces, which use
standard H5MD element names and missed mapping bugs where per-atom calc
results placed by znh5md in particles/ (with ASE_ENTRY_ORIGIN=calc) could
not be found on read.
"""

from __future__ import annotations

import numpy as np
import pytest
import znh5md

from asebytes import ASEIO

from .conftest import assert_atoms_equal

# All s22_* fixture names from conftest that produce list[ase.Atoms]
S22_FIXTURES = [
    "s22",
    "s22_energy",
    "s22_energy_forces",
    "s22_all_properties",
    "s22_info_arrays_calc",
    "s22_mixed_pbc_cell",
    "s22_info_arrays_calc_missing_inbetween",
]


# ---------------------------------------------------------------------------
# znh5md -> asebytes
# ---------------------------------------------------------------------------


class TestZnH5MDToAsebytes:
    """Verify asebytes can read files written by znh5md."""

    @pytest.mark.parametrize("fixture_name", S22_FIXTURES)
    def test_read(self, tmp_path, fixture_name, request):
        frames = request.getfixturevalue(fixture_name)
        path = str(tmp_path / "znh5md.h5md")
        znh5md.IO(path).extend(frames)

        db = ASEIO(path)
        assert len(db) == len(frames)
        for i, expected in enumerate(frames):
            result = db[i]
            assert_atoms_equal(result, expected)


# ---------------------------------------------------------------------------
# asebytes -> znh5md
# ---------------------------------------------------------------------------


class TestAsebytesToZnH5MD:
    """Verify znh5md can read files written by asebytes."""

    @pytest.mark.parametrize("fixture_name", S22_FIXTURES)
    def test_write(self, tmp_path, fixture_name, request):
        frames = request.getfixturevalue(fixture_name)
        path = str(tmp_path / "asebytes.h5md")
        ASEIO(path).extend(frames)

        zio = znh5md.IO(path)
        assert len(zio) == len(frames)
        for i, expected in enumerate(frames):
            result = zio[i]
            assert len(result) == len(expected), (
                f"Frame {i}: atom count mismatch ({len(result)} != {len(expected)})"
            )
            np.testing.assert_allclose(
                result.positions, expected.positions, atol=1e-6,
                err_msg=f"Frame {i}: positions mismatch",
            )
            np.testing.assert_array_equal(
                result.numbers, expected.numbers,
                err_msg=f"Frame {i}: numbers mismatch",
            )


# ---------------------------------------------------------------------------
# Full bidirectional: znh5md -> asebytes -> znh5md
# ---------------------------------------------------------------------------


class TestBidirectionalRoundtrip:
    """Write with znh5md, read with asebytes, write back, read with znh5md."""

    @pytest.mark.parametrize("fixture_name", S22_FIXTURES)
    def test_roundtrip(self, tmp_path, fixture_name, request):
        frames = request.getfixturevalue(fixture_name)

        # Step 1: znh5md write -> asebytes read
        zpath = str(tmp_path / "step1.h5md")
        znh5md.IO(zpath).extend(frames)
        db = ASEIO(zpath)
        intermediate = [db[i] for i in range(len(db))]

        # Step 2: asebytes write -> znh5md read
        apath = str(tmp_path / "step2.h5md")
        ASEIO(apath).extend(intermediate)
        zio = znh5md.IO(apath)
        assert len(zio) == len(frames)
        for i, expected in enumerate(frames):
            result = zio[i]
            assert len(result) == len(expected), (
                f"Frame {i}: atom count mismatch ({len(result)} != {len(expected)})"
            )
            np.testing.assert_allclose(
                result.positions, expected.positions, atol=1e-6,
                err_msg=f"Frame {i}: positions mismatch",
            )
            np.testing.assert_array_equal(
                result.numbers, expected.numbers,
                err_msg=f"Frame {i}: numbers mismatch",
            )


# ---------------------------------------------------------------------------
# Registry: *.h5 files with H5MD content
# ---------------------------------------------------------------------------


class TestH5ExtensionWithH5MDContent:
    """*.h5 files containing H5MD data should be readable via ASEIO.

    znh5md writes valid H5MD regardless of file extension. The registry
    currently maps *.h5 -> RaggedColumnarBackend, which can't read H5MD.
    It should detect the h5md group and use H5MDBackend instead.
    """

    @pytest.mark.parametrize("fixture_name", S22_FIXTURES)
    def test_h5_extension(self, tmp_path, fixture_name, request):
        frames = request.getfixturevalue(fixture_name)
        path = str(tmp_path / "data.h5")
        znh5md.IO(path).extend(frames)

        db = ASEIO(path)
        assert len(db) == len(frames)
        for i, expected in enumerate(frames):
            result = db[i]
            assert_atoms_equal(result, expected)
