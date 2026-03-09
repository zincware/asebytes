"""AsyncASEIO facade contract tests.

Every read-write backend must satisfy the same Atoms-level contract when
accessed through the AsyncASEIO facade. All tests use @pytest.mark.anyio.
"""

from __future__ import annotations

import ase
import numpy as np
import pytest

from .conftest import assert_atoms_equal


@pytest.mark.anyio
class TestAsyncASEIOCoreContract:
    """Core CRUD operations for AsyncASEIO facade."""

    async def test_extend_and_len(self, async_aseio, s22):
        await async_aseio.extend(s22)
        assert await async_aseio.len() == 22

    async def test_single_frame_roundtrip(self, async_aseio, simple_atoms):
        await async_aseio.extend([simple_atoms])
        result = await async_aseio[0]
        assert_atoms_equal(result, simple_atoms)

    async def test_multi_frame_roundtrip(self, async_aseio, ethanol):
        await async_aseio.extend(ethanol)
        assert await async_aseio.len() == 1000
        # Check first, middle, last
        assert_atoms_equal(await async_aseio[0], ethanol[0])
        assert_atoms_equal(await async_aseio[500], ethanol[500])
        assert_atoms_equal(await async_aseio[999], ethanol[999])

    async def test_getitem_by_index(self, async_aseio, s22):
        await async_aseio.extend(s22)
        for idx in [0, 10, 21]:
            result = await async_aseio[idx]
            assert isinstance(result, ase.Atoms)

    async def test_getitem_negative_index(self, async_aseio, s22):
        await async_aseio.extend(s22)
        result = await async_aseio[-1]
        assert_atoms_equal(result, s22[-1])

    async def test_slice(self, async_aseio, s22):
        await async_aseio.extend(s22)
        result = await async_aseio[0:5].to_list()
        assert len(result) == 5

    async def test_iteration(self, async_aseio, s22):
        await async_aseio.extend(s22)
        count = 0
        async for atoms in async_aseio:
            assert isinstance(atoms, ase.Atoms)
            count += 1
        assert count == 22


@pytest.mark.anyio
class TestAsyncASEIOEdgeCases:
    """Edge case tests with capability marks."""

    async def test_variable_particle_count(self, async_aseio, s22, request):
        if not request.node.get_closest_marker("supports_variable_particles"):
            pytest.skip("Backend does not support variable particle counts")
        await async_aseio.extend(s22)
        for i, expected in enumerate(s22):
            result = await async_aseio[i]
            assert len(result) == len(expected), (
                f"Frame {i}: particle count {len(result)} != {len(expected)}"
            )

    async def test_info_roundtrip(self, async_aseio, atoms_with_info, request):
        if not request.node.get_closest_marker("supports_nested_info"):
            pytest.skip("Backend does not support nested info round-trip")
        await async_aseio.extend([atoms_with_info])
        result = await async_aseio[0]
        for key in atoms_with_info.info:
            assert key in result.info, f"Missing info key: {key}"
            expected_val = atoms_with_info.info[key]
            actual_val = result.info[key]
            if isinstance(expected_val, np.ndarray):
                np.testing.assert_allclose(actual_val, expected_val)
            elif isinstance(expected_val, dict):
                assert actual_val == expected_val
            elif isinstance(expected_val, list):
                assert actual_val == expected_val or np.array_equal(
                    actual_val, expected_val
                )
            else:
                assert actual_val == expected_val, (
                    f"info[{key!r}]: {actual_val!r} != {expected_val!r}"
                )

    async def test_calc_roundtrip(self, async_aseio, atoms_with_calc):
        await async_aseio.extend([atoms_with_calc])
        result = await async_aseio[0]
        assert_atoms_equal(result, atoms_with_calc)
