import ase
import msgpack
import msgpack_numpy as m
import numpy as np


def to_bytes(atoms: ase.Atoms) -> dict[bytes, bytes]:
    if not isinstance(atoms, ase.Atoms):
        raise TypeError("Input must be an ase.Atoms object.")
    data: dict[bytes, bytes] = {}
    cell: np.ndarray = atoms.get_cell().array
    data[b"cell"] = msgpack.packb(cell, default=m.encode)
    data[b"pbc"] = msgpack.packb(atoms.get_pbc().tobytes())

    for key in atoms.arrays:
        if "." in key:
            raise ValueError(
                f"Key '{key}' in atoms.arrays contains a dot (.), which is not allowed as it is used as a path separator."
            )
        data[f"arrays.{key}".encode()] = msgpack.packb(
            atoms.arrays[key], default=m.encode
        )
    for key in atoms.info:
        if "." in key:
            raise ValueError(
                f"Key '{key}' in atoms.info contains a dot (.), which is not allowed as it is used as a path separator."
            )
        value = atoms.info[key]
        data[f"info.{key}".encode()] = msgpack.packb(value, default=m.encode)
    if atoms.calc is not None:
        for key in atoms.calc.results:
            if "." in key:
                raise ValueError(
                    f"Key '{key}' in atoms.calc.results contains a dot (.), which is not allowed as it is used as a path separator."
                )
            value = atoms.calc.results[key]
            data[f"calc.{key}".encode()] = msgpack.packb(value, default=m.encode)

    return data
