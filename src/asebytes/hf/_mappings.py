"""Column mappings for converting HuggingFace dataset rows to asebytes flat dicts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from ase.data import atomic_numbers as _ase_atomic_numbers


@dataclass(frozen=True)
class ColumnMapping:
    """Maps HuggingFace dataset column names to asebytes flat-dict keys.

    Parameters
    ----------
    positions : str
        HF column name for atomic positions -> ``arrays.positions``.
    numbers : str
        HF column name for atomic numbers -> ``arrays.numbers``.
    cell : str or None
        HF column name for unit cell -> ``cell``.
        If None, cell always defaults to zeros.
    pbc : str or None
        HF column name for periodic boundary conditions -> ``pbc``.
        If None, pbc always defaults to ``[False, False, False]``.
    calc : dict[str, str]
        Mapping of calculator result key to HF column name.
        E.g. ``{"energy": "total_energy"}`` -> ``calc.energy``.
    info : dict[str, str]
        Mapping of info key to HF column name.
        E.g. ``{"label": "material_id"}`` -> ``info.label``.
    arrays : dict[str, str]
        Mapping of extra per-atom array key to HF column name.
        E.g. ``{"forces": "atomic_forces"}`` -> ``arrays.forces``.
    species_are_strings : bool
        If True, the numbers column contains element symbols (e.g. ``"C"``)
        rather than atomic numbers (e.g. ``6``). They will be auto-converted
        via ``ase.data.atomic_numbers``.
    pbc_are_dimension_types : bool
        If True, the pbc column contains OPTIMADE dimension_types
        (0/1 integers) rather than booleans.
    """

    positions: str
    numbers: str
    cell: str | None = None
    pbc: str | None = None
    calc: dict[str, str] = field(default_factory=dict)
    info: dict[str, str] = field(default_factory=dict)
    arrays: dict[str, str] = field(default_factory=dict)
    species_are_strings: bool = False
    pbc_are_dimension_types: bool = False

    def apply(self, hf_row: dict[str, Any]) -> dict[str, Any]:
        """Convert a HuggingFace dataset row to an asebytes flat dict.

        Parameters
        ----------
        hf_row : dict[str, Any]
            A single row from a HuggingFace dataset, keyed by column name.

        Returns
        -------
        dict[str, Any]
            Flat dict with keys like ``arrays.positions``, ``calc.energy``,
            ``info.smiles``, ``cell``, ``pbc``.
        """
        result: dict[str, Any] = {}

        # Track which HF columns are consumed by the mapping
        consumed: set[str] = set()

        # 1. Positions -> arrays.positions
        consumed.add(self.positions)
        result["arrays.positions"] = np.asarray(hf_row[self.positions], dtype=np.float64)

        # 2. Numbers -> arrays.numbers (with optional species string conversion)
        consumed.add(self.numbers)
        raw_numbers = hf_row[self.numbers]
        if self.species_are_strings:
            result["arrays.numbers"] = np.array(
                [_ase_atomic_numbers[s] for s in raw_numbers], dtype=int
            )
        else:
            result["arrays.numbers"] = np.asarray(raw_numbers, dtype=int)

        # 3. Cell -> cell (default zeros if missing/None)
        if self.cell is not None:
            consumed.add(self.cell)
            raw_cell = hf_row.get(self.cell)
            if raw_cell is not None:
                result["cell"] = np.asarray(raw_cell, dtype=np.float64)
            else:
                result["cell"] = np.zeros((3, 3), dtype=np.float64)
        else:
            result["cell"] = np.zeros((3, 3), dtype=np.float64)

        # 4. PBC -> pbc (with optional dimension_types conversion, default False)
        if self.pbc is not None:
            consumed.add(self.pbc)
            raw_pbc = hf_row.get(self.pbc)
            if raw_pbc is not None:
                if self.pbc_are_dimension_types:
                    result["pbc"] = np.array(
                        [bool(d) for d in raw_pbc], dtype=bool
                    )
                else:
                    result["pbc"] = np.asarray(raw_pbc, dtype=bool)
            else:
                result["pbc"] = np.array([False, False, False], dtype=bool)
        else:
            result["pbc"] = np.array([False, False, False], dtype=bool)

        # 5. Calc columns -> calc.*
        for calc_key, hf_col in self.calc.items():
            consumed.add(hf_col)
            if hf_col in hf_row:
                val = hf_row[hf_col]
                if isinstance(val, (list, tuple)):
                    val = np.asarray(val)
                result[f"calc.{calc_key}"] = val

        # 6. Extra arrays -> arrays.*
        for arrays_key, hf_col in self.arrays.items():
            consumed.add(hf_col)
            if hf_col in hf_row:
                result[f"arrays.{arrays_key}"] = np.asarray(hf_row[hf_col])

        # 7. Explicit info mappings -> info.*
        for info_key, hf_col in self.info.items():
            consumed.add(hf_col)
            if hf_col in hf_row:
                result[f"info.{info_key}"] = hf_row[hf_col]

        # 8. Unmapped columns -> info.*
        for col_name, value in hf_row.items():
            if col_name not in consumed:
                result[f"info.{col_name}"] = value

        return result


COLABFIT = ColumnMapping(
    positions="positions",
    numbers="atomic_numbers",
    cell="cell",
    pbc="pbc",
    calc={
        "energy": "energy",
        "forces": "atomic_forces",
        "stress": "cauchy_stress",
    },
)

OPTIMADE = ColumnMapping(
    positions="cartesian_site_positions",
    numbers="species_at_sites",
    cell="lattice_vectors",
    pbc="dimension_types",
    calc={
        "energy": "energy",
        "forces": "forces",
        "stress": "stress_tensor",
    },
    species_are_strings=True,
    pbc_are_dimension_types=True,
)
