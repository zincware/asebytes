import ase
import msgpack
import msgpack_numpy as m
import numpy as np


def to_bytes(atoms: ase.Atoms) -> dict[bytes, bytes]:
    if not isinstance(atoms, ase.Atoms):
        raise TypeError("Input must be an ase.Atoms object.")
    data: dict[bytes, bytes] = {}
    cell: np.ndarray = atoms.get_cell().cellpar()
    data[b"cell"] = msgpack.packb(cell.tobytes())
    data[b"pbc"] = msgpack.packb(atoms.get_pbc().tobytes())

    for key in atoms.arrays:
        data[f"arrays:{key}".encode()] = msgpack.packb(
            atoms.arrays[key], default=m.encode
        )
    for key in atoms.info:
        value = atoms.info[key]
        data[f"info:{key}".encode()] = msgpack.packb(value, default=m.encode)
    if atoms.calc is not None:
        for key in atoms.calc.results:
            value = atoms.calc.results[key]
            data[f"calc:{key}".encode()] = msgpack.packb(value, default=m.encode)

    return data
