"""Round-trip tests for frames with mixed atom counts and inconsistent calc keys.

Every test is parametrized over all writable backends (lmdb, h5, zarr).
"""

import numpy as np
import numpy.testing as npt
import pytest
from ase import Atoms
from ase.calculators.singlepoint import SinglePointCalculator

import asebytes


@pytest.fixture
def mixed_calc_frames():
    """4 groups x 3 frames with different sizes and calc properties.

    Group 1: 10 atoms, calc with energy only
    Group 2:  5 atoms, no calc
    Group 3: 12 atoms, calc with energy only
    Group 4:  6 atoms, calc with energy + forces
    """
    rng = np.random.RandomState(42)
    frames = []

    # Group 1: 10 atoms, energy only
    for _ in range(3):
        atoms = Atoms("H10", positions=rng.randn(10, 3))
        atoms.calc = SinglePointCalculator(atoms, energy=rng.randn())
        frames.append(atoms)

    # Group 2: 5 atoms, no calc
    for _ in range(3):
        atoms = Atoms("H5", positions=rng.randn(5, 3))
        frames.append(atoms)

    # Group 3: 12 atoms, energy only
    for _ in range(3):
        atoms = Atoms("C12", positions=rng.randn(12, 3))
        atoms.calc = SinglePointCalculator(atoms, energy=rng.randn())
        frames.append(atoms)

    # Group 4: 6 atoms, energy + forces
    for _ in range(3):
        atoms = Atoms("O6", positions=rng.randn(6, 3))
        atoms.calc = SinglePointCalculator(
            atoms,
            energy=rng.randn(),
            forces=rng.randn(6, 3),
        )
        frames.append(atoms)

    return frames


# -- Helpers ---------------------------------------------------------------


def assert_atoms_match(rec, ref):
    """Assert structure + calc round-trip."""
    assert len(rec) == len(ref)
    npt.assert_array_equal(rec.get_atomic_numbers(), ref.get_atomic_numbers())
    npt.assert_allclose(rec.get_positions(), ref.get_positions())
    if ref.calc is not None:
        assert rec.calc is not None
        assert set(rec.calc.results) == set(ref.calc.results)
        for key in ref.calc.results:
            npt.assert_allclose(rec.calc.results[key], ref.calc.results[key])
    else:
        assert rec.calc is None


# -- Tests -----------------------------------------------------------------


class TestInconsistentCalc:
    def test_full_round_trip(self, db_path, mixed_calc_frames):
        """Write all 12 frames in one extend, read back one by one."""
        io = asebytes.ASEIO(db_path)
        io.extend(mixed_calc_frames)

        io2 = asebytes.ASEIO(db_path, readonly=True)
        assert len(io2) == 12
        for i, ref in enumerate(mixed_calc_frames):
            assert_atoms_match(io2[i], ref)

    def test_group_boundaries(self, db_path, mixed_calc_frames):
        """Verify each group has the expected calc keys."""
        io = asebytes.ASEIO(db_path)
        io.extend(mixed_calc_frames)

        io2 = asebytes.ASEIO(db_path, readonly=True)

        # Group 1 (0-2): energy only
        for i in range(0, 3):
            assert io2[i].calc is not None
            assert set(io2[i].calc.results) == {"energy"}

        # Group 2 (3-5): no calc
        for i in range(3, 6):
            assert io2[i].calc is None

        # Group 3 (6-8): energy only
        for i in range(6, 9):
            assert io2[i].calc is not None
            assert set(io2[i].calc.results) == {"energy"}

        # Group 4 (9-11): energy + forces
        for i in range(9, 12):
            assert io2[i].calc is not None
            assert set(io2[i].calc.results) == {"energy", "forces"}

    def test_append_groups_separately(self, db_path, mixed_calc_frames):
        """Append each group in a separate extend call."""
        io = asebytes.ASEIO(db_path)
        for start in range(0, 12, 3):
            io.extend(mixed_calc_frames[start : start + 3])

        io2 = asebytes.ASEIO(db_path, readonly=True)
        assert len(io2) == 12
        for i, ref in enumerate(mixed_calc_frames):
            assert_atoms_match(io2[i], ref)

    def test_interleaved_calc_no_calc(self, db_path, mixed_calc_frames):
        """Interleave: calc-group, no-calc-group, calc-group, ... (like znh5md)."""
        io = asebytes.ASEIO(db_path)
        # Write groups in order: 1, 2, 3, 4, 2, 1 to stress interleaving
        order = [
            mixed_calc_frames[0:3],  # group 1: energy
            mixed_calc_frames[3:6],  # group 2: no calc
            mixed_calc_frames[6:9],  # group 3: energy
            mixed_calc_frames[9:12],  # group 4: energy+forces
            mixed_calc_frames[3:6],  # group 2 again: no calc
            mixed_calc_frames[0:3],  # group 1 again: energy
        ]
        all_frames = [a for batch in order for a in batch]

        for batch in order:
            io.extend(batch)

        io2 = asebytes.ASEIO(db_path, readonly=True)
        assert len(io2) == len(all_frames)
        for i, ref in enumerate(all_frames):
            assert_atoms_match(io2[i], ref)

    def test_slice_read(self, db_path, mixed_calc_frames):
        """Verify slice-based access across group boundaries."""
        io = asebytes.ASEIO(db_path)
        io.extend(mixed_calc_frames)

        io2 = asebytes.ASEIO(db_path, readonly=True)
        # Slice spanning no-calc -> energy-only boundary
        for rec, ref in zip(io2[2:8], mixed_calc_frames[2:8]):
            assert_atoms_match(rec, ref)

    def test_negative_index(self, db_path, mixed_calc_frames):
        """Negative indexing into the last group (energy+forces)."""
        io = asebytes.ASEIO(db_path)
        io.extend(mixed_calc_frames)

        io2 = asebytes.ASEIO(db_path, readonly=True)
        assert_atoms_match(io2[-1], mixed_calc_frames[-1])
        assert_atoms_match(io2[-3], mixed_calc_frames[-3])
