"""Name mappings between asebytes flat-dict keys and H5MD paths.

Matches znh5md conventions exactly to ensure cross-compatibility.
"""

from __future__ import annotations

# H5MD element name -> ASE property name (used on read)
H5MD_TO_ASE: dict[str, str] = {
    "position": "positions",
    "force": "forces",
    "mass": "masses",
    "charge": "charges",
    "potential_energy": "energy",
    "species": "numbers",
    "velocity": "velocities",
}

# ASE property name -> H5MD element name (used on write)
ASE_TO_H5MD: dict[str, str] = {v: k for k, v in H5MD_TO_ASE.items()}

# Known H5MD particle-level elements
KNOWN_PARTICLE_ELEMENTS: set[str] = {
    "position",
    "velocity",
    "force",
    "mass",
    "species",
    "id",
    "charge",
}

# ZnH5MD uses this attribute to track where data originated
ORIGIN_ATTR: str = "ASE_ENTRY_ORIGIN"
