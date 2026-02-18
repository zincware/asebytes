from __future__ import annotations

from typing import Any

import ase
import ase.constraints
import numpy as np
from ase.calculators.singlepoint import SinglePointCalculator
from ase.cell import Cell


def atoms_to_dict(atoms: ase.Atoms) -> dict[str, Any]:
    """Convert an ASE Atoms object to a logical dict.

    Parameters
    ----------
    atoms : ase.Atoms
        Atoms object to convert.

    Returns
    -------
    dict[str, Any]
        Keys like "cell", "pbc", "arrays.positions", "info.smiles", "calc.energy".
        Values are numpy arrays, scalars, or Python objects — no serialization.

    Raises
    ------
    TypeError
        If input is not an ase.Atoms object.
    """
    if not isinstance(atoms, ase.Atoms):
        raise TypeError("Input must be an ase.Atoms object.")

    data: dict[str, Any] = {}
    data["cell"] = atoms.get_cell().array
    data["pbc"] = atoms.get_pbc()

    for key, value in atoms.arrays.items():
        data[f"arrays.{key}"] = value

    for key, value in atoms.info.items():
        data[f"info.{key}"] = value

    if atoms.calc is not None:
        for key, value in atoms.calc.results.items():
            data[f"calc.{key}"] = value

    # All ASE constraint classes implement todict() → {'name': ..., 'kwargs': ...}
    # and dict2constraint() is the universal deserializer.
    if atoms.constraints:
        constraints_data = [c.todict() for c in atoms.constraints]
        if constraints_data:
            data["constraints"] = constraints_data

    return data


def dict_to_atoms(data: dict[str, Any], fast: bool = True) -> ase.Atoms:
    """Convert a logical dict back to an ASE Atoms object.

    Parameters
    ----------
    data : dict[str, Any]
        Dictionary with string keys and Python/numpy values.
    fast : bool, default=True
        If True, bypass Atoms constructor for ~6x speedup.

    Returns
    -------
    ase.Atoms
        Reconstructed Atoms object.
    """
    numbers = data.get("arrays.numbers", np.array([], dtype=int))
    if not isinstance(numbers, np.ndarray):
        numbers = np.asarray(numbers)

    cell = data.get("cell")
    pbc = data.get("pbc", np.array([False, False, False], dtype=bool))

    if fast:
        atoms = ase.Atoms.__new__(ase.Atoms)
        if cell is not None:
            atoms._cellobj = Cell(cell)
        else:
            atoms._cellobj = Cell(np.zeros((3, 3)))
        atoms._pbc = pbc if isinstance(pbc, np.ndarray) else np.asarray(pbc)
        atoms.arrays = {"numbers": numbers}
        if "arrays.positions" not in data:
            n_atoms = len(numbers)
            atoms.arrays["positions"] = np.zeros((n_atoms, 3))
        atoms.info = {}
        atoms.constraints = []
        atoms._celldisp = np.zeros(3)
        atoms._calc = None
    else:
        atoms = ase.Atoms(numbers=numbers, cell=cell, pbc=pbc)

    for key, value in data.items():
        if key in ("cell", "pbc", "arrays.numbers"):
            continue
        if key.startswith("arrays."):
            array_name = key[7:]  # len("arrays.") == 7
            atoms.arrays[array_name] = (
                value if isinstance(value, np.ndarray) else np.asarray(value)
            )
        elif key.startswith("info."):
            info_key = key[5:]  # len("info.") == 5
            atoms.info[info_key] = value
        elif key.startswith("calc."):
            if atoms.calc is None:
                atoms.calc = SinglePointCalculator(atoms)
            calc_key = key[5:]  # len("calc.") == 5
            atoms.calc.results[calc_key] = value
        elif key == "constraints":
            constraints = []
            for constraint_dict in value:
                constraints.append(ase.constraints.dict2constraint(constraint_dict))
            atoms.set_constraint(constraints)

    return atoms
