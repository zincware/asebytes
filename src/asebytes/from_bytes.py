import ase
import msgpack
import msgpack_numpy as m
import numpy as np
from ase.calculators.singlepoint import SinglePointCalculator


def from_bytes(data: dict[bytes, bytes]) -> ase.Atoms:
    cell_array = msgpack.unpackb(data[b"cell"], object_hook=m.decode)
    pbc_bytes = msgpack.unpackb(data[b"pbc"])
    numbers_array = msgpack.unpackb(data[b"arrays.numbers"], object_hook=m.decode)

    pbc_array = np.frombuffer(pbc_bytes, dtype=np.bool).reshape(
        3,
    )

    atoms = ase.Atoms(
        numbers=numbers_array, cell=cell_array, pbc=pbc_array
    )

    for key in data:
        if key in [b"cell", b"pbc", b"arrays.numbers"]:
            continue
        if key.startswith(b"arrays."):
            array_data = msgpack.unpackb(data[key], object_hook=m.decode)
            atoms.arrays[key.decode().split("arrays.")[1]] = array_data
        elif key.startswith(b"info."):
            info_key = key.decode().split("info.")[1]
            info_array = msgpack.unpackb(data[key], object_hook=m.decode)
            atoms.info[info_key] = info_array
        elif key.startswith(b"calc."):
            if not hasattr(atoms, "calc") or atoms.calc is None:
                atoms.calc = SinglePointCalculator(atoms)
            calc_key = key.decode().split("calc.")[1]
            calc_array = msgpack.unpackb(data[key], object_hook=m.decode)
            atoms.calc.results[calc_key] = calc_array

        else:
            raise ValueError(f"Unknown key in data: {key}")

    return atoms
