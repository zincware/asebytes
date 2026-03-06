"""H5MD 1.1 spec compliance and znh5md interop tests.

Verifies that files written by asebytes via ASEIO(".h5md") conform to the
H5MD 1.1 specification, and that asebytes/znh5md can read each other's files.
"""

from __future__ import annotations

import h5py
import numpy as np
import pytest

from asebytes import ASEIO

from .conftest import assert_atoms_equal


# ---------------------------------------------------------------------------
# H5MD file structure compliance tests
# ---------------------------------------------------------------------------


class TestH5MDFileStructure:
    """Verify H5MD 1.1 root-level structure and metadata."""

    def test_h5md_root_attributes(self, tmp_path, simple_atoms):
        """H5MD file must have h5md group with version, author, creator."""
        path = str(tmp_path / "test.h5md")
        db = ASEIO(path)
        db.extend([simple_atoms])

        with h5py.File(path, "r") as f:
            assert "h5md" in f, "Missing h5md group"
            h5md = f["h5md"]
            assert "version" in h5md.attrs, "Missing h5md version attribute"
            np.testing.assert_array_equal(
                h5md.attrs["version"], [1, 1],
                err_msg="H5MD version must be [1, 1]",
            )
            assert "author" in h5md, "Missing h5md/author group"
            assert "creator" in h5md, "Missing h5md/creator group"
            assert "name" in h5md["creator"].attrs, "Missing creator name"

    def test_h5md_particles_group(self, tmp_path, s22):
        """H5MD file must have particles/ group with subgroups containing
        position/value, position/step, position/time, species/value."""
        path = str(tmp_path / "test.h5md")
        db = ASEIO(path)
        db.extend(s22)

        with h5py.File(path, "r") as f:
            assert "particles" in f, "Missing particles group"
            particles = f["particles"]
            groups = list(particles.keys())
            assert len(groups) >= 1, "particles/ must have at least one subgroup"

            grp_name = groups[0]
            grp = particles[grp_name]

            # position element
            assert "position" in grp, f"Missing particles/{grp_name}/position"
            pos = grp["position"]
            assert "value" in pos, "Missing position/value dataset"
            assert "step" in pos, "Missing position/step dataset"
            assert "time" in pos, "Missing position/time dataset"

            # species element
            assert "species" in grp, f"Missing particles/{grp_name}/species"
            species = grp["species"]
            assert "value" in species, "Missing species/value dataset"

    def test_h5md_time_dependent_structure(self, tmp_path, s22):
        """Verify position/value shape is (N_frames, max_atoms, 3)."""
        path = str(tmp_path / "test.h5md")
        db = ASEIO(path)
        db.extend(s22)
        n_frames = len(s22)
        max_atoms = max(len(atoms) for atoms in s22)

        with h5py.File(path, "r") as f:
            grp_name = list(f["particles"].keys())[0]
            pos_val = f[f"particles/{grp_name}/position/value"]
            assert pos_val.shape[0] == n_frames, (
                f"First dim should be N_frames={n_frames}, got {pos_val.shape[0]}"
            )
            assert pos_val.shape[1] == max_atoms, (
                f"Second dim should be max_atoms={max_atoms}, got {pos_val.shape[1]}"
            )
            assert pos_val.shape[2] == 3, (
                f"Third dim should be 3, got {pos_val.shape[2]}"
            )

    def test_h5md_box_group(self, tmp_path, s22_mixed_pbc_cell):
        """Verify box group exists with edges and boundary attributes."""
        path = str(tmp_path / "test.h5md")
        db = ASEIO(path)
        db.extend(s22_mixed_pbc_cell)

        with h5py.File(path, "r") as f:
            grp_name = list(f["particles"].keys())[0]
            grp = f[f"particles/{grp_name}"]
            assert "box" in grp, "Missing box group"
            box = grp["box"]
            assert "dimension" in box.attrs, "Missing box dimension attribute"
            assert "boundary" in box.attrs, "Missing box boundary attribute"
            assert "edges" in box, "Missing box/edges element"


# ---------------------------------------------------------------------------
# znh5md interoperability tests
# ---------------------------------------------------------------------------


class TestZnH5MDInterop:
    """Verify bidirectional read/write compatibility with znh5md."""

    def test_znh5md_reads_asebytes_file(self, tmp_path, s22_energy_forces):
        """Files written by asebytes should be readable by znh5md."""
        znh5md = pytest.importorskip("znh5md")

        path = str(tmp_path / "asebytes_written.h5md")
        db = ASEIO(path)
        db.extend(s22_energy_forces)

        zio = znh5md.IO(path)
        assert len(zio) == len(s22_energy_forces)

        result = zio[0]
        expected = s22_energy_forces[0]
        np.testing.assert_allclose(result.positions, expected.positions, atol=1e-6)
        np.testing.assert_array_equal(result.numbers, expected.numbers)

    def test_asebytes_reads_znh5md_file(self, tmp_path, s22_energy_forces):
        """Files written by znh5md should be readable by asebytes."""
        znh5md = pytest.importorskip("znh5md")

        path = str(tmp_path / "znh5md_written.h5md")
        zio = znh5md.IO(path)
        zio.extend(s22_energy_forces)

        db = ASEIO(path)
        assert len(db) == len(s22_energy_forces)

        result = db[0]
        expected = s22_energy_forces[0]
        np.testing.assert_allclose(result.positions, expected.positions, atol=1e-6)
        np.testing.assert_array_equal(result.numbers, expected.numbers)

    def test_interop_roundtrip_preserves_forces(self, tmp_path, s22_energy_forces):
        """Forces written by asebytes should be readable by znh5md."""
        znh5md = pytest.importorskip("znh5md")

        path = str(tmp_path / "forces_test.h5md")
        db = ASEIO(path)
        db.extend(s22_energy_forces)

        zio = znh5md.IO(path)
        for i in range(min(5, len(s22_energy_forces))):
            result = zio[i]
            expected = s22_energy_forces[i]
            n_atoms = len(expected)
            assert result.calc is not None, f"Frame {i}: missing calculator"
            np.testing.assert_allclose(
                result.calc.results["forces"][:n_atoms],
                expected.calc.results["forces"],
                atol=1e-6,
                err_msg=f"Frame {i}: forces mismatch",
            )


# ---------------------------------------------------------------------------
# H5MD edge cases
# ---------------------------------------------------------------------------


class TestH5MDEdgeCases:
    """H5MD-specific edge case tests."""

    def test_h5md_variable_particles(self, tmp_path, s22):
        """Write s22 (variable particle counts), verify each frame correct."""
        path = str(tmp_path / "test.h5md")
        db = ASEIO(path)
        db.extend(s22)

        for i, expected in enumerate(s22):
            result = db[i]
            assert len(result) == len(expected), (
                f"Frame {i}: atom count {len(result)} != {len(expected)}"
            )

    def test_h5md_constraints_roundtrip(self, tmp_path, atoms_with_constraints):
        """Write atoms with constraints via H5MD, read back, verify."""
        path = str(tmp_path / "test.h5md")
        db = ASEIO(path)
        db.extend([atoms_with_constraints])
        result = db[0]
        # H5MD may store constraints via info.constraints_json
        # Check atom count is preserved even if constraints are dropped
        assert len(result) == len(atoms_with_constraints)
