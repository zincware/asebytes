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
# znh5md -> asebytes  (*.h5md and *.h5 via content sniffing)
# ---------------------------------------------------------------------------


class TestZnH5MDToAsebytes:
    """Verify asebytes can read files written by znh5md.

    Tests both the native *.h5md extension and *.h5 files that require
    content sniffing to route to H5MDBackend instead of ColumnarBackend.
    """

    @pytest.mark.parametrize("fixture_name", S22_FIXTURES)
    @pytest.mark.parametrize("ext", [".h5md", ".h5"])
    def test_read(self, tmp_path, fixture_name, ext, request):
        frames = request.getfixturevalue(fixture_name)
        path = str(tmp_path / f"znh5md{ext}")
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
            assert_atoms_equal(result, expected, atol=1e-6)


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
            assert_atoms_equal(result, expected, atol=1e-6)
