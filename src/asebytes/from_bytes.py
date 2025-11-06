import ase
import msgpack
import msgpack_numpy as m
import numpy as np
from ase.calculators.singlepoint import SinglePointCalculator
from ase.cell import Cell


def from_bytes(data: dict[bytes, bytes], fast: bool = True) -> ase.Atoms:
    """Deserialize bytes back into an ASE Atoms object.

    Args:
        data: Dictionary of bytes to deserialize
        fast: If True, use optimized direct attribute assignment (6x faster).
              If False, use standard Atoms constructor (safer but slower).

    Returns:
        ase.Atoms object
    """
    cell_array = msgpack.unpackb(data[b"cell"], object_hook=m.decode)
    pbc_bytes = msgpack.unpackb(data[b"pbc"])
    numbers_array = msgpack.unpackb(data[b"arrays.numbers"], object_hook=m.decode)

    pbc_array = np.frombuffer(pbc_bytes, dtype=np.bool).reshape(3,)

    if fast:
        #  Skip Atoms.__init__() and directly assign attributes for better performance
        atoms = ase.Atoms.__new__(ase.Atoms)

        atoms._cellobj = Cell(cell_array)
        atoms._pbc = pbc_array
        atoms.arrays = {'numbers': numbers_array}
        atoms.info = {}
        atoms.constraints = []
        atoms._celldisp = np.zeros(3)  # Cell displacement
    else:
        # Use standard Atoms constructor
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
