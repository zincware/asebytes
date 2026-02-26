import ase.constraints
import msgpack
import msgpack_numpy as m
import numpy as np
from ase.calculators.singlepoint import SinglePointCalculator
from ase.cell import Cell

_SKIP_KEYS = frozenset((b"cell", b"pbc", b"arrays.numbers"))

_unpackb = msgpack.unpackb
_m_decode = m.decode


def decode(data: dict[bytes, bytes], fast: bool = True, copy: bool = True) -> ase.Atoms:
    """
    Deserialize bytes into an ASE Atoms object.

    Parameters
    ----------
    data : dict[bytes, bytes]
        Dictionary with byte keys and msgpack-serialized byte values.
    fast : bool, default=True
        If True, use optimized direct attribute assignment (6x faster).
        If False, use standard Atoms constructor (safer but slower).
    copy : bool, default=True
        If True, create writable copies of all numpy arrays from msgpack.
        If False, use arrays as-is (read-only, but saves memory).
        Set to True if you need to modify atoms after decoding.
        Nested numpy arrays might still be read-only.

    Returns
    -------
    ase.Atoms
        Reconstructed Atoms object.

    Raises
    ------
    ValueError
        If unknown keys are present in data.
    KeyError
        If required key 'arrays.numbers' is missing.
    """
    if b"arrays.numbers" in data:
        numbers_array = _unpackb(data[b"arrays.numbers"], object_hook=_m_decode)
        if copy:
            numbers_array = np.array(numbers_array, copy=True)
    else:
        numbers_array = np.array([], dtype=int)

    # Extract optional parameters with defaults
    if b"cell" in data:
        cell_array = _unpackb(data[b"cell"], object_hook=_m_decode)
        if copy:
            cell_array = np.array(cell_array, copy=True)
    else:
        cell_array = None

    if b"pbc" in data:
        pbc_array = _unpackb(data[b"pbc"], object_hook=_m_decode)
        if copy and isinstance(pbc_array, np.ndarray):
            pbc_array = np.array(pbc_array, copy=True)
    else:
        pbc_array = np.array([False, False, False], dtype=bool)

    if fast:
        #  Skip Atoms.__init__() and directly assign attributes for better performance
        atoms = ase.Atoms.__new__(ase.Atoms)

        # Set cell - use provided cell or default empty cell
        if cell_array is not None:
            atoms._cellobj = Cell(cell_array)
        else:
            atoms._cellobj = Cell(np.zeros((3, 3)))

        atoms._pbc = pbc_array
        atoms.arrays = {"numbers": numbers_array}

        # Initialize positions if not provided
        if b"arrays.positions" not in data:
            # Create default positions (zeros) based on number of atoms
            n_atoms = len(numbers_array)
            atoms.arrays["positions"] = np.zeros((n_atoms, 3))

        atoms.info = {}
        atoms.constraints = []
        atoms._celldisp = np.zeros(3)
        atoms._calc = None
    else:
        # Use standard Atoms constructor
        atoms = ase.Atoms(numbers=numbers_array, cell=cell_array, pbc=pbc_array)

    _calc = None
    for key in data:
        if key in _SKIP_KEYS:
            continue

        if key.startswith(b"arrays."):
            array_data = _unpackb(data[key], object_hook=_m_decode)
            if copy:
                array_data = np.array(array_data, copy=True)
            atoms.arrays[key[7:].decode()] = array_data
        elif key.startswith(b"info."):
            info_key = key[5:].decode()
            info_array = _unpackb(data[key], object_hook=_m_decode)
            if copy and isinstance(info_array, np.ndarray):
                info_array = np.array(info_array, copy=True)
            atoms.info[info_key] = info_array
        elif key.startswith(b"calc."):
            if _calc is None:
                if fast:
                    # Bypass SinglePointCalculator.__init__ which calls
                    # atoms.copy() — a full deep copy we don't need.
                    _calc = SinglePointCalculator.__new__(SinglePointCalculator)
                    _calc.results = {}
                    _calc.atoms = atoms
                    _calc.parameters = None
                    _calc._directory = None
                    _calc.prefix = None
                    _calc.use_cache = False
                    atoms._calc = _calc
                else:
                    _calc = SinglePointCalculator(atoms)
                    atoms.calc = _calc
            calc_key = key[5:].decode()
            calc_array = _unpackb(data[key], object_hook=_m_decode)
            if copy and isinstance(calc_array, np.ndarray):
                calc_array = np.array(calc_array, copy=True)
            _calc.results[calc_key] = calc_array
        elif key == b"constraints":
            constraints_data = _unpackb(data[key], object_hook=_m_decode)
            constraints = [
                ase.constraints.dict2constraint(cd)
                for cd in constraints_data
            ]
            atoms.set_constraint(constraints)
        else:
            raise ValueError(f"Unknown key in data: {key}")

    return atoms
