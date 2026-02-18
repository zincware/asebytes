# Backend Abstraction & Lazy Views Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor asebytes to support pluggable storage backends (LMDB, HuggingFace, Zarr) behind a unified `MutableSequence[ase.Atoms]` interface, with pandas-style lazy views for column-oriented data access.

**Architecture:** Introduce `ReadableBackend` / `WritableBackend` ABCs that operate on `dict[str, Any]` (logical representation). LMDB backend wraps the existing `BytesIO` and handles msgpack serialization internally. `ASEIO.__getitem__` dispatches by type: `int` → `ase.Atoms`, `slice`/`list[int]` → `RowView`, `str`/`list[str]` → `ColumnView`. `ColumnView` handles both single and multi-key access via a `_single` flag (DRY — no separate `ColumnsView`). Views are lazy — they accumulate row/column constraints and only read from the backend on materialization (`to_list()`, `to_dict()`, iteration, scalar indexing).

**Tech Stack:** Python 3.11+, `abc.ABC`, `typing.overload`, existing `lmdb`/`msgpack`/`ase` deps. No new dependencies.

**Branch:** `feat/multi-backend` (base: `main`)

---

### Setup: Create feature branch

```bash
git checkout -b feat/multi-backend main
```

All tasks commit to this branch. PR back to `main` after Task 9 passes.

## File Structure (New/Modified)

```
src/asebytes/
├── __init__.py           # MODIFY: add new exports
├── encode.py             # KEEP: unchanged
├── decode.py             # KEEP: unchanged
├── io.py                 # MODIFY: refactor ASEIO, keep BytesIO unchanged
├── metadata.py           # KEEP: unchanged
├── _convert.py           # NEW: atoms_to_dict, dict_to_atoms
├── _protocols.py         # NEW: ReadableBackend, WritableBackend ABCs
├── _views.py             # NEW: RowView, ColumnView
└── lmdb/                 # NEW: LMDB backend package
    ├── __init__.py       # exports LMDBBackend
    └── _backend.py       # LMDBBackend implementation

tests/
├── test_protocols.py     # NEW
├── test_convert.py       # NEW
├── test_lmdb_backend.py  # NEW
├── test_views.py         # NEW
├── test_aseio_views.py   # NEW: view integration tests on ASEIO
```

---

### Task 1: Backend Protocols (`_protocols.py`)

**Files:**
- Create: `src/asebytes/_protocols.py`
- Test: `tests/test_protocols.py`

**Step 1: Write tests for protocol conformance**

```python
# tests/test_protocols.py
from typing import Any

import pytest

from asebytes._protocols import ReadableBackend, WritableBackend


class MinimalReadable(ReadableBackend):
    """Minimal implementation with only abstract methods."""

    def __init__(self, data: list[dict[str, Any]]):
        self._data = data

    def __len__(self) -> int:
        return len(self._data)

    def columns(self, index: int = 0) -> list[str]:
        if not self._data:
            return []
        return list(self._data[index].keys())

    def read_row(self, index: int, keys: list[str] | None = None) -> dict[str, Any]:
        row = self._data[index]
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return dict(row)


class MinimalWritable(MinimalReadable, WritableBackend):
    """Minimal writable implementation."""

    def write_row(self, index: int, data: dict[str, Any]) -> None:
        if index < len(self._data):
            self._data[index] = data
        elif index == len(self._data):
            self._data.append(data)

    def insert_row(self, index: int, data: dict[str, Any]) -> None:
        self._data.insert(index, data)

    def delete_row(self, index: int) -> None:
        del self._data[index]

    def append_rows(self, data: list[dict[str, Any]]) -> None:
        self._data.extend(data)


def test_readable_instantiation():
    backend = MinimalReadable([{"a": 1}, {"a": 2}])
    assert len(backend) == 2


def test_readable_read_row():
    backend = MinimalReadable([{"a": 1, "b": 2}])
    assert backend.read_row(0) == {"a": 1, "b": 2}


def test_readable_read_row_with_keys():
    backend = MinimalReadable([{"a": 1, "b": 2}])
    assert backend.read_row(0, keys=["a"]) == {"a": 1}


def test_readable_columns():
    backend = MinimalReadable([{"a": 1, "b": 2}])
    assert sorted(backend.columns()) == ["a", "b"]


def test_readable_read_rows_default():
    """Default read_rows loops over read_row."""
    backend = MinimalReadable([{"a": 1}, {"a": 2}, {"a": 3}])
    rows = backend.read_rows([0, 2])
    assert rows == [{"a": 1}, {"a": 3}]


def test_readable_read_column_default():
    """Default read_column extracts single key from read_row."""
    backend = MinimalReadable([{"a": 1, "b": 10}, {"a": 2, "b": 20}])
    values = backend.read_column("a")
    assert values == [1, 2]


def test_readable_read_column_with_indices():
    backend = MinimalReadable([{"a": 1}, {"a": 2}, {"a": 3}])
    values = backend.read_column("a", indices=[0, 2])
    assert values == [1, 3]


def test_writable_write_row():
    backend = MinimalWritable([{"a": 1}])
    backend.write_row(0, {"a": 99})
    assert backend.read_row(0) == {"a": 99}


def test_writable_insert_row():
    backend = MinimalWritable([{"a": 1}, {"a": 3}])
    backend.insert_row(1, {"a": 2})
    assert len(backend) == 3
    assert backend.read_row(1) == {"a": 2}


def test_writable_delete_row():
    backend = MinimalWritable([{"a": 1}, {"a": 2}])
    backend.delete_row(0)
    assert len(backend) == 1
    assert backend.read_row(0) == {"a": 2}


def test_writable_append_rows():
    backend = MinimalWritable([])
    backend.append_rows([{"a": 1}, {"a": 2}])
    assert len(backend) == 2


def test_cannot_instantiate_abstract_readable():
    """ReadableBackend cannot be instantiated without implementing abstract methods."""
    with pytest.raises(TypeError):
        ReadableBackend()


def test_cannot_instantiate_abstract_writable():
    with pytest.raises(TypeError):
        WritableBackend()
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_protocols.py -v`
Expected: `ModuleNotFoundError: No module named 'asebytes._protocols'`

**Step 3: Implement the protocols**

```python
# src/asebytes/_protocols.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ReadableBackend(ABC):
    """Abstract base for read-only storage backends.

    Subclasses must implement: __len__, columns, read_row.
    Override read_rows and read_column for backend-specific optimization.
    """

    @abstractmethod
    def __len__(self) -> int: ...

    @abstractmethod
    def columns(self, index: int = 0) -> list[str]:
        """Return available column names.

        Parameters
        ----------
        index : int
            Row index to inspect for available keys. Defaults to 0.
        """
        ...

    @abstractmethod
    def read_row(self, index: int, keys: list[str] | None = None) -> dict[str, Any]:
        """Read a single row, optionally filtering to specific keys.

        Parameters
        ----------
        index : int
            Row index.
        keys : list[str] | None
            If provided, only return these keys. If None, return all.
        """
        ...

    def read_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Read multiple rows. Default: loops over read_row."""
        return [self.read_row(i, keys) for i in indices]

    def read_column(
        self, key: str, indices: list[int] | None = None
    ) -> list[Any]:
        """Read a single column across rows. Default: extracts from read_row."""
        if indices is None:
            indices = list(range(len(self)))
        return [self.read_row(i, [key])[key] for i in indices]


class WritableBackend(ReadableBackend):
    """Abstract base for read-write storage backends.

    Subclasses must implement everything from ReadableBackend plus:
    write_row, insert_row, delete_row, append_rows.
    """

    @abstractmethod
    def write_row(self, index: int, data: dict[str, Any]) -> None:
        """Write or overwrite a single row."""
        ...

    @abstractmethod
    def insert_row(self, index: int, data: dict[str, Any]) -> None:
        """Insert a row at index, shifting subsequent rows."""
        ...

    @abstractmethod
    def delete_row(self, index: int) -> None:
        """Delete a row at index, shifting subsequent rows."""
        ...

    @abstractmethod
    def append_rows(self, data: list[dict[str, Any]]) -> None:
        """Append multiple rows efficiently (bulk operation)."""
        ...
```

**Step 4: Run tests**

Run: `uv run pytest tests/test_protocols.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/asebytes/_protocols.py tests/test_protocols.py
git commit -m "feat: add ReadableBackend and WritableBackend ABCs"
```

---

### Task 2: Conversion Functions (`_convert.py`)

**Files:**
- Create: `src/asebytes/_convert.py`
- Test: `tests/test_convert.py`

**Step 1: Write tests**

```python
# tests/test_convert.py
import ase
import numpy as np
import pytest
from ase.calculators.singlepoint import SinglePointCalculator
from ase.constraints import FixAtoms

from asebytes._convert import atoms_to_dict, dict_to_atoms


def test_roundtrip_simple():
    atoms = ase.Atoms("H2", positions=[[0, 0, 0], [1, 0, 0]])
    d = atoms_to_dict(atoms)
    result = dict_to_atoms(d)
    assert result == atoms


def test_roundtrip_with_cell_pbc():
    atoms = ase.Atoms(
        "H",
        positions=[[0, 0, 0]],
        cell=[[10, 0, 0], [0, 10, 0], [0, 0, 10]],
        pbc=[True, True, False],
    )
    d = atoms_to_dict(atoms)
    result = dict_to_atoms(d)
    assert np.allclose(result.cell, atoms.cell)
    assert np.array_equal(result.pbc, atoms.pbc)


def test_roundtrip_with_info():
    atoms = ase.Atoms("H", positions=[[0, 0, 0]])
    atoms.info["smiles"] = "CCO"
    atoms.info["data"] = np.array([1, 2, 3])
    d = atoms_to_dict(atoms)
    assert d["info.smiles"] == "CCO"
    assert np.array_equal(d["info.data"], np.array([1, 2, 3]))
    result = dict_to_atoms(d)
    assert result.info["smiles"] == "CCO"


def test_roundtrip_with_calc():
    atoms = ase.Atoms("H2", positions=[[0, 0, 0], [1, 0, 0]])
    atoms.calc = SinglePointCalculator(atoms)
    atoms.calc.results = {
        "energy": -10.5,
        "forces": np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]),
    }
    d = atoms_to_dict(atoms)
    assert d["calc.energy"] == -10.5
    assert np.allclose(d["calc.forces"], [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    result = dict_to_atoms(d)
    assert result.calc.results["energy"] == pytest.approx(-10.5)


def test_roundtrip_with_constraints():
    atoms = ase.Atoms("H2O", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]])
    atoms.set_constraint(FixAtoms(indices=[0, 2]))
    d = atoms_to_dict(atoms)
    assert "constraints" in d
    result = dict_to_atoms(d)
    assert len(result.constraints) == 1


def test_atoms_to_dict_keys():
    """Verify the dict key format."""
    atoms = ase.Atoms("H", positions=[[0, 0, 0]])
    atoms.info["tag"] = "test"
    d = atoms_to_dict(atoms)
    assert "cell" in d
    assert "pbc" in d
    assert "arrays.positions" in d
    assert "arrays.numbers" in d
    assert "info.tag" in d


def test_dict_to_atoms_fast_mode():
    atoms = ase.Atoms("H2", positions=[[0, 0, 0], [1, 0, 0]])
    d = atoms_to_dict(atoms)
    result_fast = dict_to_atoms(d, fast=True)
    result_slow = dict_to_atoms(d, fast=False)
    assert result_fast == result_slow


def test_dict_to_atoms_empty():
    result = dict_to_atoms({})
    assert len(result) == 0


def test_atoms_to_dict_type_error():
    with pytest.raises(TypeError):
        atoms_to_dict("not atoms")


def test_roundtrip_dot_keys():
    """Keys with dots in info should roundtrip correctly."""
    atoms = ase.Atoms("H", positions=[[0, 0, 0]])
    atoms.info["data.value"] = 42
    d = atoms_to_dict(atoms)
    assert d["info.data.value"] == 42
    result = dict_to_atoms(d)
    assert result.info["data.value"] == 42
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_convert.py -v`
Expected: `ModuleNotFoundError`

**Step 3: Implement conversion functions**

```python
# src/asebytes/_convert.py
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
```

**Step 4: Run tests**

Run: `uv run pytest tests/test_convert.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/asebytes/_convert.py tests/test_convert.py
git commit -m "feat: add atoms_to_dict and dict_to_atoms conversion functions"
```

---

### Task 3: LMDB Backend (`asebytes.lmdb`)

**Files:**
- Create: `src/asebytes/lmdb/__init__.py`
- Create: `src/asebytes/lmdb/_backend.py`
- Test: `tests/test_lmdb_backend.py`

**Step 1: Write tests**

```python
# tests/test_lmdb_backend.py
import numpy as np
import pytest

from asebytes._protocols import ReadableBackend, WritableBackend
from asebytes.lmdb import LMDBBackend


@pytest.fixture
def backend(tmp_path):
    return LMDBBackend(str(tmp_path / "test.lmdb"))


@pytest.fixture
def sample_row():
    return {
        "cell": np.eye(3),
        "pbc": np.array([True, True, True]),
        "arrays.numbers": np.array([1, 8]),
        "arrays.positions": np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]),
        "calc.energy": -10.5,
        "info.smiles": "O",
    }


def test_is_writable_backend(backend):
    assert isinstance(backend, WritableBackend)
    assert isinstance(backend, ReadableBackend)


def test_empty_len(backend):
    assert len(backend) == 0


def test_write_and_read_row(backend, sample_row):
    backend.write_row(0, sample_row)
    assert len(backend) == 1
    row = backend.read_row(0)
    assert row["calc.energy"] == pytest.approx(-10.5)
    assert row["info.smiles"] == "O"
    assert np.array_equal(row["arrays.numbers"], np.array([1, 8]))


def test_read_row_with_keys(backend, sample_row):
    backend.write_row(0, sample_row)
    row = backend.read_row(0, keys=["calc.energy", "info.smiles"])
    assert "calc.energy" in row
    assert "info.smiles" in row
    assert "arrays.positions" not in row


def test_columns(backend, sample_row):
    backend.write_row(0, sample_row)
    cols = backend.columns()
    assert "calc.energy" in cols
    assert "arrays.positions" in cols


def test_append_rows(backend, sample_row):
    backend.append_rows([sample_row, sample_row, sample_row])
    assert len(backend) == 3


def test_insert_row(backend, sample_row):
    row_a = {**sample_row, "calc.energy": -1.0}
    row_b = {**sample_row, "calc.energy": -2.0}
    row_c = {**sample_row, "calc.energy": -3.0}
    backend.append_rows([row_a, row_c])
    backend.insert_row(1, row_b)
    assert len(backend) == 3
    assert backend.read_row(0)["calc.energy"] == pytest.approx(-1.0)
    assert backend.read_row(1)["calc.energy"] == pytest.approx(-2.0)
    assert backend.read_row(2)["calc.energy"] == pytest.approx(-3.0)


def test_delete_row(backend, sample_row):
    row_a = {**sample_row, "calc.energy": -1.0}
    row_b = {**sample_row, "calc.energy": -2.0}
    backend.append_rows([row_a, row_b])
    backend.delete_row(0)
    assert len(backend) == 1
    assert backend.read_row(0)["calc.energy"] == pytest.approx(-2.0)


def test_write_row_overwrite(backend, sample_row):
    backend.write_row(0, sample_row)
    new_row = {**sample_row, "calc.energy": -99.0}
    backend.write_row(0, new_row)
    assert backend.read_row(0)["calc.energy"] == pytest.approx(-99.0)


def test_read_column(backend, sample_row):
    rows = [
        {**sample_row, "calc.energy": -1.0},
        {**sample_row, "calc.energy": -2.0},
        {**sample_row, "calc.energy": -3.0},
    ]
    backend.append_rows(rows)
    energies = backend.read_column("calc.energy")
    assert energies == pytest.approx([-1.0, -2.0, -3.0])


def test_read_column_with_indices(backend, sample_row):
    rows = [
        {**sample_row, "calc.energy": float(-i)}
        for i in range(5)
    ]
    backend.append_rows(rows)
    energies = backend.read_column("calc.energy", indices=[0, 2, 4])
    assert energies == pytest.approx([0.0, -2.0, -4.0])


def test_read_rows(backend, sample_row):
    rows = [
        {**sample_row, "calc.energy": float(-i)}
        for i in range(5)
    ]
    backend.append_rows(rows)
    result = backend.read_rows([1, 3])
    assert len(result) == 2
    assert result[0]["calc.energy"] == pytest.approx(-1.0)
    assert result[1]["calc.energy"] == pytest.approx(-3.0)


def test_read_row_nonexistent(backend):
    with pytest.raises((KeyError, IndexError)):
        backend.read_row(0)


def test_readonly_mode(tmp_path, sample_row):
    path = str(tmp_path / "readonly.lmdb")
    # Write first
    wb = LMDBBackend(path)
    wb.write_row(0, sample_row)
    del wb
    # Read-only
    rb = LMDBBackend(path, readonly=True)
    assert len(rb) == 1
    row = rb.read_row(0)
    assert row["calc.energy"] == pytest.approx(-10.5)
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_lmdb_backend.py -v`
Expected: `ModuleNotFoundError`

**Step 3: Implement LMDBBackend**

```python
# src/asebytes/lmdb/__init__.py
from asebytes.lmdb._backend import LMDBBackend

__all__ = ["LMDBBackend"]
```

```python
# src/asebytes/lmdb/_backend.py
from __future__ import annotations

from typing import Any

import msgpack
import msgpack_numpy as m

from asebytes._protocols import WritableBackend
from asebytes.io import BytesIO


class LMDBBackend(WritableBackend):
    """LMDB storage backend using msgpack serialization.

    Wraps BytesIO for LMDB operations, converting between
    dict[str, Any] (logical) and dict[bytes, bytes] (storage).

    Parameters
    ----------
    file : str
        Path to LMDB database file.
    prefix : bytes
        Key prefix for namespacing.
    map_size : int
        Maximum LMDB size in bytes (default 10GB).
    readonly : bool
        Open in read-only mode.
    **lmdb_kwargs
        Additional kwargs for lmdb.open().
    """

    def __init__(
        self,
        file: str,
        prefix: bytes = b"",
        map_size: int = 10737418240,
        readonly: bool = False,
        **lmdb_kwargs,
    ):
        self._store = BytesIO(file, prefix, map_size, readonly, **lmdb_kwargs)

    def _serialize_row(self, data: dict[str, Any]) -> dict[bytes, bytes]:
        return {
            k.encode(): msgpack.packb(v, default=m.encode)
            for k, v in data.items()
        }

    def _deserialize_row(self, raw: dict[bytes, bytes]) -> dict[str, Any]:
        return {
            k.decode(): msgpack.unpackb(v, object_hook=m.decode)
            for k, v in raw.items()
        }

    def __len__(self) -> int:
        return len(self._store)

    def columns(self, index: int = 0) -> list[str]:
        keys = self._store.get_available_keys(index)
        return [k.decode() for k in keys]

    def read_row(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any]:
        byte_keys = [k.encode() for k in keys] if keys is not None else None
        raw = self._store.get(index, keys=byte_keys)
        return self._deserialize_row(raw)

    def read_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any]]:
        return [self.read_row(i, keys) for i in indices]

    def read_column(
        self, key: str, indices: list[int] | None = None
    ) -> list[Any]:
        if indices is None:
            indices = list(range(len(self)))
        byte_key = key.encode()
        return [
            msgpack.unpackb(
                self._store.get(i, keys=[byte_key])[byte_key],
                object_hook=m.decode,
            )
            for i in indices
        ]

    def write_row(self, index: int, data: dict[str, Any]) -> None:
        self._store[index] = self._serialize_row(data)

    def insert_row(self, index: int, data: dict[str, Any]) -> None:
        self._store.insert(index, self._serialize_row(data))

    def delete_row(self, index: int) -> None:
        del self._store[index]

    def append_rows(self, data: list[dict[str, Any]]) -> None:
        self._store.extend([self._serialize_row(d) for d in data])
```

**Step 4: Run tests**

Run: `uv run pytest tests/test_lmdb_backend.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/asebytes/lmdb/ tests/test_lmdb_backend.py
git commit -m "feat: add LMDBBackend wrapping BytesIO with dict[str, Any] interface"
```

---

### Task 4: Lazy View Classes (`_views.py`)

**Files:**
- Create: `src/asebytes/_views.py`
- Test: `tests/test_views.py`

Two view classes: `RowView` (row-oriented, yields `ase.Atoms`) and `ColumnView` (column-oriented, handles both single and multiple keys via `_single` flag). No `ColumnsView` — `ColumnView` with `keys: str | list[str]` covers both cases (DRY).

Views reference an `ASEIO` instance but at this stage we test them with a mock parent that satisfies the minimal interface. This keeps the view tests independent of ASEIO refactoring.

**Step 1: Write tests**

```python
# tests/test_views.py
from __future__ import annotations

from typing import Any

import ase
import numpy as np
import pytest

from asebytes._views import ColumnView, RowView


class MockParent:
    """Minimal parent that views need."""

    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = rows

    def __len__(self) -> int:
        return len(self._rows)

    def _read_row(self, index: int, keys: list[str] | None = None) -> dict[str, Any]:
        row = self._rows[index]
        if keys is not None:
            return {k: row[k] for k in keys}
        return dict(row)

    def _read_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any]]:
        return [self._read_row(i, keys) for i in indices]

    def _read_column(self, key: str, indices: list[int]) -> list[Any]:
        return [self._rows[i][key] for i in indices]

    def _build_atoms(self, row: dict[str, Any]) -> ase.Atoms:
        """Minimal Atoms construction for testing."""
        n = len(row.get("arrays.numbers", []))
        return ase.Atoms(
            numbers=row.get("arrays.numbers", []),
            positions=row.get("arrays.positions", np.zeros((n, 3))),
        )


@pytest.fixture
def parent():
    rows = [
        {
            "arrays.numbers": np.array([1]),
            "arrays.positions": np.array([[float(i), 0, 0]]),
            "calc.energy": float(-i),
            "info.tag": f"mol_{i}",
        }
        for i in range(10)
    ]
    return MockParent(rows)


# --- RowView tests ---


class TestRowView:
    def test_len(self, parent):
        view = RowView(parent, range(3, 7))
        assert len(view) == 4

    def test_getitem_int(self, parent):
        view = RowView(parent, range(3, 7))
        atoms = view[0]  # should be row index 3
        assert isinstance(atoms, ase.Atoms)
        assert atoms.positions[0, 0] == pytest.approx(3.0)

    def test_getitem_negative_int(self, parent):
        view = RowView(parent, range(3, 7))
        atoms = view[-1]  # should be row index 6
        assert atoms.positions[0, 0] == pytest.approx(6.0)

    def test_getitem_slice(self, parent):
        view = RowView(parent, range(0, 10))
        sub = view[2:5]
        assert isinstance(sub, RowView)
        assert len(sub) == 3

    def test_getitem_list_int(self, parent):
        view = RowView(parent, range(0, 10))
        sub = view[[0, 5, 9]]
        assert isinstance(sub, RowView)
        assert len(sub) == 3

    def test_getitem_str_returns_single_column_view(self, parent):
        view = RowView(parent, range(0, 5))
        col = view["calc.energy"]
        assert isinstance(col, ColumnView)
        assert col._single
        assert len(col) == 5

    def test_getitem_list_str_returns_multi_column_view(self, parent):
        view = RowView(parent, range(0, 5))
        cols = view[["calc.energy", "info.tag"]]
        assert isinstance(cols, ColumnView)
        assert not cols._single
        assert len(cols) == 5

    def test_iter(self, parent):
        view = RowView(parent, range(0, 3))
        atoms_list = list(view)
        assert len(atoms_list) == 3
        assert all(isinstance(a, ase.Atoms) for a in atoms_list)

    def test_to_list(self, parent):
        view = RowView(parent, range(0, 3))
        atoms_list = view.to_list()
        assert len(atoms_list) == 3
        assert all(isinstance(a, ase.Atoms) for a in atoms_list)

    def test_chaining_row_then_column(self, parent):
        """db[5:10]["calc.energy"] should work."""
        view = RowView(parent, range(5, 8))
        energies = list(view["calc.energy"])
        assert energies == pytest.approx([-5.0, -6.0, -7.0])


# --- ColumnView (single key) tests ---


class TestColumnViewSingle:
    def test_len(self, parent):
        view = ColumnView(parent, "calc.energy", range(0, 10))
        assert len(view) == 10

    def test_len_none_indices(self, parent):
        view = ColumnView(parent, "calc.energy")
        assert len(view) == 10

    def test_getitem_int_unwraps(self, parent):
        """Single-key ColumnView[int] returns the value directly."""
        view = ColumnView(parent, "calc.energy", range(0, 10))
        assert view[3] == pytest.approx(-3.0)

    def test_getitem_negative_int(self, parent):
        view = ColumnView(parent, "calc.energy", range(0, 10))
        assert view[-1] == pytest.approx(-9.0)

    def test_getitem_slice(self, parent):
        view = ColumnView(parent, "calc.energy", range(0, 10))
        sub = view[2:5]
        assert isinstance(sub, ColumnView)
        assert sub._single
        assert len(sub) == 3

    def test_getitem_list_int(self, parent):
        view = ColumnView(parent, "calc.energy", range(0, 10))
        sub = view[[0, 5, 9]]
        assert isinstance(sub, ColumnView)
        assert len(sub) == 3

    def test_iter(self, parent):
        view = ColumnView(parent, "calc.energy", range(0, 5))
        values = list(view)
        assert values == pytest.approx([0.0, -1.0, -2.0, -3.0, -4.0])

    def test_to_list(self, parent):
        view = ColumnView(parent, "calc.energy", range(0, 3))
        values = view.to_list()
        assert values == pytest.approx([0.0, -1.0, -2.0])

    def test_to_dict_single(self, parent):
        """to_dict() on single-key view returns dict with one key."""
        view = ColumnView(parent, "calc.energy", range(0, 3))
        d = view.to_dict()
        assert d == {"calc.energy": pytest.approx([0.0, -1.0, -2.0])}

    def test_chaining_column_then_slice(self, parent):
        """db["calc.energy"][5:10] should work."""
        view = ColumnView(parent, "calc.energy")
        sub = view[5:8]
        values = list(sub)
        assert values == pytest.approx([-5.0, -6.0, -7.0])

    def test_same_result_both_orderings(self, parent):
        """db[5:8]["calc.energy"] == db["calc.energy"][5:8]"""
        via_row = list(RowView(parent, range(5, 8))["calc.energy"])
        via_col = list(ColumnView(parent, "calc.energy")[5:8])
        assert via_row == pytest.approx(via_col)


# --- ColumnView (multi key) tests ---


class TestColumnViewMulti:
    def test_len(self, parent):
        view = ColumnView(parent, ["calc.energy", "info.tag"], range(0, 5))
        assert len(view) == 5

    def test_getitem_int_returns_dict(self, parent):
        """Multi-key ColumnView[int] returns a dict."""
        view = ColumnView(parent, ["calc.energy", "info.tag"], range(0, 5))
        row = view[0]
        assert isinstance(row, dict)
        assert "calc.energy" in row
        assert "info.tag" in row
        assert "arrays.positions" not in row

    def test_getitem_slice(self, parent):
        view = ColumnView(parent, ["calc.energy", "info.tag"], range(0, 10))
        sub = view[2:5]
        assert isinstance(sub, ColumnView)
        assert not sub._single
        assert len(sub) == 3

    def test_getitem_str_narrows_to_single(self, parent):
        """Indexing multi-key view with str narrows to single key."""
        view = ColumnView(parent, ["calc.energy", "info.tag"], range(0, 5))
        col = view["calc.energy"]
        assert isinstance(col, ColumnView)
        assert col._single

    def test_iter_yields_dicts(self, parent):
        view = ColumnView(parent, ["calc.energy", "info.tag"], range(0, 3))
        rows = list(view)
        assert len(rows) == 3
        assert all(isinstance(r, dict) for r in rows)
        assert rows[0]["calc.energy"] == pytest.approx(0.0)
        assert rows[0]["info.tag"] == "mol_0"

    def test_to_list(self, parent):
        view = ColumnView(parent, ["calc.energy", "info.tag"], range(0, 3))
        rows = view.to_list()
        assert len(rows) == 3
        assert rows[0]["calc.energy"] == pytest.approx(0.0)

    def test_to_dict(self, parent):
        view = ColumnView(parent, ["calc.energy", "info.tag"], range(0, 3))
        d = view.to_dict()
        assert "calc.energy" in d
        assert "info.tag" in d
        assert d["calc.energy"] == pytest.approx([0.0, -1.0, -2.0])
        assert d["info.tag"] == ["mol_0", "mol_1", "mol_2"]

    def test_chaining_row_then_multi_column(self, parent):
        """db[5:8][["calc.energy", "info.tag"]] should work."""
        view = RowView(parent, range(5, 8))
        cols = view[["calc.energy", "info.tag"]]
        rows = list(cols)
        assert len(rows) == 3
        assert rows[0]["calc.energy"] == pytest.approx(-5.0)
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_views.py -v`
Expected: `ModuleNotFoundError`

**Step 3: Implement view classes**

```python
# src/asebytes/_views.py
from __future__ import annotations

from typing import Any, Iterator, overload

import ase


def _sub_select(
    current_indices: list[int],
    selector: int | slice | list[int],
) -> int | list[int]:
    """Apply a selector to current indices. Returns absolute index(es)."""
    if isinstance(selector, int):
        if selector < 0:
            selector += len(current_indices)
        return current_indices[selector]
    if isinstance(selector, slice):
        return current_indices[selector]
    if isinstance(selector, list):
        return [current_indices[i] for i in selector]
    raise TypeError(f"Unsupported selector type: {type(selector)}")


class RowView:
    """Lazy view over a subset of rows.

    Iteration yields ase.Atoms objects. Indexing with str or list[str]
    returns ColumnView for column-oriented access.
    """

    __slots__ = ("_parent", "_indices")

    def __init__(
        self,
        parent: Any,
        indices: range | list[int],
    ):
        self._parent = parent
        self._indices = list(indices)

    def __len__(self) -> int:
        return len(self._indices)

    @overload
    def __getitem__(self, key: int) -> ase.Atoms: ...
    @overload
    def __getitem__(self, key: slice) -> RowView: ...
    @overload
    def __getitem__(self, key: list[int]) -> RowView: ...
    @overload
    def __getitem__(self, key: str) -> ColumnView: ...
    @overload
    def __getitem__(self, key: list[str]) -> ColumnView: ...

    def __getitem__(
        self, key: int | slice | str | list[int] | list[str]
    ) -> ase.Atoms | RowView | ColumnView:
        if isinstance(key, int):
            abs_idx = _sub_select(self._indices, key)
            row = self._parent._read_row(abs_idx)
            return self._parent._build_atoms(row)
        if isinstance(key, slice):
            new_indices = _sub_select(self._indices, key)
            return RowView(self._parent, new_indices)
        if isinstance(key, str):
            return ColumnView(self._parent, key, self._indices)
        if isinstance(key, list):
            if key and isinstance(key[0], int):
                new_indices = _sub_select(self._indices, key)
                return RowView(self._parent, new_indices)
            if key and isinstance(key[0], str):
                return ColumnView(self._parent, key, self._indices)
        raise TypeError(f"Unsupported key type: {type(key)}")

    def __iter__(self) -> Iterator[ase.Atoms]:
        # Batch read via read_rows to avoid N+1 query problem
        for row in self._parent._read_rows(self._indices):
            yield self._parent._build_atoms(row)

    def to_list(self) -> list[ase.Atoms]:
        """Materialize as list of Atoms objects."""
        return list(self)

    def __repr__(self) -> str:
        return f"RowView(len={len(self)})"


class ColumnView:
    """Lazy view over one or more columns.

    Single key (str): iteration yields individual values (float, ndarray, etc.).
    Multiple keys (list[str]): iteration yields dict[str, Any] per row.
    The _single flag controls unwrapping behavior — same pattern as
    ASEIO.__getitem__ where int unwraps and list keeps the container.

    Materialization:
    - to_list() → list[Any] (single) or list[dict[str, Any]] (multi)
    - to_dict() → dict[str, list[Any]] (works for both)
    """

    __slots__ = ("_parent", "_keys", "_single", "_indices")

    def __init__(
        self,
        parent: Any,
        keys: str | list[str],
        indices: range | list[int] | None = None,
    ):
        self._parent = parent
        self._single = isinstance(keys, str)
        self._keys = [keys] if self._single else keys
        self._indices = list(indices) if indices is not None else None

    def _resolved_indices(self) -> list[int]:
        if self._indices is not None:
            return self._indices
        return list(range(len(self._parent)))

    def __len__(self) -> int:
        if self._indices is not None:
            return len(self._indices)
        return len(self._parent)

    @overload
    def __getitem__(self, key: int) -> Any: ...
    @overload
    def __getitem__(self, key: slice) -> ColumnView: ...
    @overload
    def __getitem__(self, key: list[int]) -> ColumnView: ...
    @overload
    def __getitem__(self, key: str) -> ColumnView: ...

    def __getitem__(
        self, key: int | slice | str | list[int]
    ) -> Any | ColumnView:
        indices = self._resolved_indices()
        if isinstance(key, int):
            abs_idx = _sub_select(indices, key)
            if self._single:
                return self._parent._read_column(self._keys[0], [abs_idx])[0]
            return self._parent._read_row(abs_idx, keys=self._keys)
        if isinstance(key, slice):
            new_indices = _sub_select(indices, key)
            return ColumnView(self._parent, self._keys[0] if self._single else self._keys, new_indices)
        if isinstance(key, str):
            return ColumnView(self._parent, key, indices)
        if isinstance(key, list):
            new_indices = _sub_select(indices, key)
            return ColumnView(self._parent, self._keys[0] if self._single else self._keys, new_indices)
        raise TypeError(f"Unsupported key type: {type(key)}")

    def __iter__(self) -> Iterator[Any]:
        indices = self._resolved_indices()
        if self._single:
            # Already batched — read_column gets all indices at once
            yield from self._parent._read_column(self._keys[0], indices)
        else:
            # Batch read via read_rows to avoid N+1 query problem
            for row in self._parent._read_rows(indices, keys=self._keys):
                yield row

    def to_list(self) -> list[Any]:
        """Materialize as list.

        Single key: list of values (float, ndarray, etc.).
        Multi key: list of dicts.
        """
        return list(self)

    def to_dict(self) -> dict[str, list[Any]]:
        """Materialize as column-oriented dict.

        Works for both single and multi key:
        - single: {"calc.energy": [1.0, 2.0, 3.0]}
        - multi: {"calc.energy": [...], "calc.forces": [...]}
        """
        indices = self._resolved_indices()
        if self._single:
            return {self._keys[0]: self._parent._read_column(self._keys[0], indices)}
        # Batch read, then transpose to column-oriented
        result: dict[str, list[Any]] = {k: [] for k in self._keys}
        for row in self._parent._read_rows(indices, keys=self._keys):
            for k in self._keys:
                result[k].append(row[k])
        return result

    def __repr__(self) -> str:
        if self._single:
            return f"ColumnView(key={self._keys[0]!r}, len={len(self)})"
        return f"ColumnView(keys={self._keys!r}, len={len(self)})"
```

**Step 4: Run tests**

Run: `uv run pytest tests/test_views.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/asebytes/_views.py tests/test_views.py
git commit -m "feat: add RowView and ColumnView lazy view classes"
```

---

### Task 5: Refactor ASEIO to Use Backends + Views

**Files:**
- Modify: `src/asebytes/io.py` (ASEIO class only — BytesIO stays unchanged)
- Test: `tests/test_aseio_views.py` (new view tests)
- Verify: `uv run pytest tests/test_aseio.py -v` (existing tests still pass)

**Step 1: Write new view integration tests for ASEIO**

```python
# tests/test_aseio_views.py
import ase
import numpy as np
import pytest
from ase.calculators.singlepoint import SinglePointCalculator

from asebytes import ASEIO
from asebytes._views import ColumnView, RowView
from asebytes.lmdb import LMDBBackend


@pytest.fixture
def db(tmp_path):
    io = ASEIO(str(tmp_path / "test.lmdb"))
    for i in range(10):
        atoms = ase.Atoms("H", positions=[[float(i), 0, 0]])
        atoms.info["tag"] = f"mol_{i}"
        atoms.calc = SinglePointCalculator(atoms)
        atoms.calc.results = {"energy": float(-i)}
        io.append(atoms)
    return io


@pytest.fixture
def db_from_backend(tmp_path):
    """Test ASEIO constructed with explicit LMDBBackend."""
    backend = LMDBBackend(str(tmp_path / "backend.lmdb"))
    io = ASEIO(backend)
    for i in range(5):
        atoms = ase.Atoms("H", positions=[[float(i), 0, 0]])
        atoms.calc = SinglePointCalculator(atoms)
        atoms.calc.results = {"energy": float(-i)}
        io.append(atoms)
    return io


# --- Backward compatibility ---


def test_getitem_int(db):
    atoms = db[0]
    assert isinstance(atoms, ase.Atoms)


def test_getitem_int_negative(db):
    atoms = db[-1]
    assert isinstance(atoms, ase.Atoms)
    assert atoms.positions[0, 0] == pytest.approx(9.0)


# --- Row views ---


def test_getitem_slice(db):
    view = db[3:7]
    assert isinstance(view, RowView)
    assert len(view) == 4


def test_getitem_list_int(db):
    view = db[[0, 5, 9]]
    assert isinstance(view, RowView)
    assert len(view) == 3


def test_row_view_iter(db):
    atoms_list = list(db[0:3])
    assert len(atoms_list) == 3
    assert all(isinstance(a, ase.Atoms) for a in atoms_list)


# --- Column views ---


def test_getitem_str(db):
    view = db["calc.energy"]
    assert isinstance(view, ColumnView)
    assert len(view) == 10


def test_column_view_iter(db):
    energies = list(db["calc.energy"])
    assert len(energies) == 10
    assert energies[0] == pytest.approx(0.0)
    assert energies[9] == pytest.approx(-9.0)


def test_column_view_getitem_int(db):
    val = db["calc.energy"][5]
    assert val == pytest.approx(-5.0)


def test_column_view_getitem_slice(db):
    view = db["calc.energy"][3:6]
    assert isinstance(view, ColumnView)
    values = list(view)
    assert values == pytest.approx([-3.0, -4.0, -5.0])


# --- Multi-column views ---


def test_getitem_list_str(db):
    view = db[["calc.energy", "info.tag"]]
    assert isinstance(view, ColumnView)
    assert not view._single
    assert len(view) == 10


def test_multi_column_view_iter(db):
    rows = list(db[["calc.energy", "info.tag"]][:3])
    assert len(rows) == 3
    assert rows[0]["calc.energy"] == pytest.approx(0.0)
    assert rows[0]["info.tag"] == "mol_0"


def test_multi_column_view_to_dict(db):
    d = db[["calc.energy", "info.tag"]][:3].to_dict()
    assert d["calc.energy"] == pytest.approx([0.0, -1.0, -2.0])
    assert d["info.tag"] == ["mol_0", "mol_1", "mol_2"]


# --- Chaining ---


def test_row_then_column(db):
    """db[5:8]["calc.energy"] should work."""
    energies = list(db[5:8]["calc.energy"])
    assert energies == pytest.approx([-5.0, -6.0, -7.0])


def test_column_then_slice(db):
    """db["calc.energy"][5:8] should work."""
    energies = list(db["calc.energy"][5:8])
    assert energies == pytest.approx([-5.0, -6.0, -7.0])


def test_both_orderings_equal(db):
    """db[5:8]["calc.energy"] == db["calc.energy"][5:8]"""
    via_row = list(db[5:8]["calc.energy"])
    via_col = list(db["calc.energy"][5:8])
    assert via_row == pytest.approx(via_col)


def test_row_then_multi_column(db):
    """db[0:3][["calc.energy", "info.tag"]] should work."""
    view = db[0:3][["calc.energy", "info.tag"]]
    assert isinstance(view, ColumnView)
    assert not view._single
    rows = list(view)
    assert len(rows) == 3


# --- .columns property ---


def test_columns_property(db):
    cols = db.columns
    assert "calc.energy" in cols
    assert "arrays.positions" in cols
    assert "info.tag" in cols


# --- Backend constructor ---


def test_aseio_from_backend(db_from_backend):
    assert len(db_from_backend) == 5
    atoms = db_from_backend[0]
    assert isinstance(atoms, ase.Atoms)


def test_aseio_from_backend_views(db_from_backend):
    energies = list(db_from_backend["calc.energy"])
    assert len(energies) == 5
```

**Step 2: Run new tests to verify they fail**

Run: `uv run pytest tests/test_aseio_views.py -v`
Expected: FAIL (ASEIO doesn't support str/slice indexing yet)

**Step 3: Refactor ASEIO in `io.py`**

Replace the ASEIO class in `src/asebytes/io.py` (lines 14-188). BytesIO stays completely unchanged.

```python
# The new ASEIO class (replaces lines 14-188 in src/asebytes/io.py)
# Keep all existing imports at top of io.py, add:
from __future__ import annotations

from collections.abc import MutableSequence
from typing import Any, Iterator, overload

import ase
import msgpack
import msgpack_numpy as m
import numpy as np

from asebytes._convert import atoms_to_dict, dict_to_atoms
from asebytes._protocols import ReadableBackend, WritableBackend
from asebytes._views import ColumnView, RowView
from asebytes.decode import decode
from asebytes.encode import encode


class ASEIO(MutableSequence):
    """Storage-agnostic mutable sequence for ASE Atoms objects.

    Supports pluggable backends (LMDB, HuggingFace, Zarr) and pandas-style
    lazy views for column-oriented data access.

    Parameters
    ----------
    backend : str | ReadableBackend | WritableBackend
        Either a file path (auto-creates LMDBBackend) or a backend instance.
    **kwargs
        When backend is a str, forwarded to LMDBBackend constructor
        (prefix, map_size, readonly, etc.).
    """

    def __init__(
        self,
        backend: str | ReadableBackend,
        **kwargs: Any,
    ):
        if isinstance(backend, str):
            from asebytes.lmdb import LMDBBackend

            self._backend: ReadableBackend = LMDBBackend(backend, **kwargs)
        else:
            self._backend = backend

    @property
    def columns(self) -> list[str]:
        """Available column names (inspects first row)."""
        if len(self._backend) == 0:
            return []
        return self._backend.columns()

    # --- Internal methods used by views ---

    def _read_row(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any]:
        return self._backend.read_row(index, keys)

    def _read_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any]]:
        return self._backend.read_rows(indices, keys)

    def _read_column(self, key: str, indices: list[int]) -> list[Any]:
        return self._backend.read_column(key, indices)

    def _build_atoms(self, row: dict[str, Any]) -> ase.Atoms:
        return dict_to_atoms(row)

    # --- MutableSequence interface ---

    @overload
    def __getitem__(self, index: int) -> ase.Atoms: ...
    @overload
    def __getitem__(self, index: slice) -> RowView: ...
    @overload
    def __getitem__(self, index: list[int]) -> RowView: ...
    @overload
    def __getitem__(self, index: str) -> ColumnView: ...
    @overload
    def __getitem__(self, index: list[str]) -> ColumnView: ...

    def __getitem__(
        self,
        index: int | slice | str | list[int] | list[str],
    ) -> ase.Atoms | RowView | ColumnView:
        if isinstance(index, int):
            if index < 0:
                index += len(self)
            row = self._backend.read_row(index)
            return dict_to_atoms(row)
        if isinstance(index, slice):
            indices = range(len(self))[index]
            return RowView(self, list(indices))
        if isinstance(index, str):
            return ColumnView(self, index)
        if isinstance(index, list):
            if index and isinstance(index[0], int):
                return RowView(self, index)
            if index and isinstance(index[0], str):
                return ColumnView(self, index)
            if not index:
                return RowView(self, [])
        raise TypeError(f"Unsupported index type: {type(index)}")

    def __setitem__(self, index: int, value: ase.Atoms) -> None:
        if not isinstance(self._backend, WritableBackend):
            raise TypeError("Backend is read-only")
        data = atoms_to_dict(value)
        self._backend.write_row(index, data)

    def __delitem__(self, index: int) -> None:
        if not isinstance(self._backend, WritableBackend):
            raise TypeError("Backend is read-only")
        self._backend.delete_row(index)

    def insert(self, index: int, value: ase.Atoms) -> None:
        if not isinstance(self._backend, WritableBackend):
            raise TypeError("Backend is read-only")
        data = atoms_to_dict(value)
        self._backend.insert_row(index, data)

    def extend(self, values: list[ase.Atoms]) -> None:
        """Efficiently extend with multiple Atoms objects using bulk operations."""
        if not isinstance(self._backend, WritableBackend):
            raise TypeError("Backend is read-only")
        data_list = [atoms_to_dict(atoms) for atoms in values]
        self._backend.append_rows(data_list)

    def __len__(self) -> int:
        return len(self._backend)

    def __iter__(self) -> Iterator[ase.Atoms]:
        for i in range(len(self)):
            yield self[i]

    # --- Legacy API (backward compatible) ---

    def get_available_keys(self, index: int) -> list[bytes]:
        """Get available keys at index (legacy API, returns bytes keys)."""
        cols = self._backend.columns(index)
        return [c.encode() for c in cols]

    def get(
        self, index: int, keys: list[bytes] | None = None
    ) -> ase.Atoms:
        """Get Atoms at index, optionally filtering to specific keys (legacy API)."""
        str_keys = [k.decode() for k in keys] if keys is not None else None
        row = self._backend.read_row(index, str_keys)
        return dict_to_atoms(row)

    def update(self, index: int, data: dict[str, Any]) -> None:
        """Update specific keys at index (read-modify-write).

        Parameters
        ----------
        index : int
            Row index to update.
        data : dict[str, Any]
            Flat dict with dotted keys, e.g.
            {"calc.energy": -10.5, "calc.forces": np.array(...), "info.tag": "done"}
        """
        if not isinstance(self._backend, WritableBackend):
            raise TypeError("Backend is read-only")
        row = self._backend.read_row(index)
        row.update(data)
        self._backend.write_row(index, row)

    # --- Backward-compatible property ---

    @property
    def io(self) -> Any:
        """Access underlying BytesIO (legacy). Only works with LMDB backend."""
        from asebytes.lmdb import LMDBBackend

        if isinstance(self._backend, LMDBBackend):
            return self._backend._store
        raise AttributeError("io property only available with LMDB backend")
```

**Step 4: Run ALL existing tests + new tests**

Run: `uv run pytest tests/test_aseio.py tests/test_aseio_views.py tests/test_aseio_update.py -v`
Expected: All PASS (existing tests unchanged, new tests pass)

**Step 5: Commit**

```bash
git add src/asebytes/io.py tests/test_aseio_views.py
git commit -m "refactor: ASEIO uses backend abstraction with lazy views"
```

---

### Task 6: Update Exports and Run Full Test Suite

**Files:**
- Modify: `src/asebytes/__init__.py`
- Verify: full test suite

**Step 1: Update `__init__.py`**

```python
# src/asebytes/__init__.py
import importlib.metadata

from .decode import decode
from .encode import encode
from .io import ASEIO, BytesIO
from .metadata import get_metadata
from ._protocols import ReadableBackend, WritableBackend
from ._convert import atoms_to_dict, dict_to_atoms
from ._views import RowView, ColumnView
from .lmdb import LMDBBackend

__all__ = [
    "encode",
    "decode",
    "BytesIO",
    "ASEIO",
    "get_metadata",
    "ReadableBackend",
    "WritableBackend",
    "atoms_to_dict",
    "dict_to_atoms",
    "RowView",
    "ColumnView",
    "LMDBBackend",
]

__version__ = importlib.metadata.version("asebytes")
```

**Step 2: Run the full test suite**

Run: `uv run pytest -v`
Expected: All tests PASS (existing + new)

**Step 3: Run type checking (optional but recommended)**

Run: `uv run mypy src/asebytes/ --ignore-missing-imports`

**Step 4: Commit**

```bash
git add src/asebytes/__init__.py
git commit -m "feat: export new backend, view, and conversion APIs"
```

---

### Task 7: Verify Backward Compatibility

**No code changes.** This task verifies that all existing tests pass without modification.

**Step 1: Run the complete existing test suite**

Run: `uv run pytest -v`
Expected: All PASS

**Step 2: Verify specific backward-compat scenarios**

```python
# Quick manual check (or add to a test file):
import asebytes

# Old-style construction still works
io = asebytes.ASEIO("/tmp/test_compat.lmdb")

# encode/decode still work
import ase
atoms = ase.Atoms("H", positions=[[0, 0, 0]])
data = asebytes.encode(atoms)
assert isinstance(data, dict)
assert all(isinstance(k, bytes) for k in data.keys())
result = asebytes.decode(data)
assert result == atoms

# BytesIO still works
bio = asebytes.BytesIO("/tmp/test_compat_bytes.lmdb")
bio[0] = data
assert bio[0] == data
```

---

## Summary of Changes

| Component | Status | Description |
|-----------|--------|-------------|
| `_protocols.py` | NEW | `ReadableBackend` and `WritableBackend` ABCs |
| `_convert.py` | NEW | `atoms_to_dict()` and `dict_to_atoms()` — no serialization |
| `lmdb/` | NEW | `LMDBBackend` wrapping `BytesIO` with `dict[str, Any]` interface |
| `_views.py` | NEW | `RowView`, `ColumnView` — lazy, composable. `ColumnView` handles both single and multi-key via `_single` flag. |
| `io.py` ASEIO | MODIFIED | Uses backend + views, `__getitem__` type dispatch, `.columns` |
| `io.py` BytesIO | UNCHANGED | Fully preserved for backward compat |
| `encode.py` | UNCHANGED | Public API preserved |
| `decode.py` | UNCHANGED | Public API preserved |
| `metadata.py` | UNCHANGED | Public API preserved |
| `__init__.py` | MODIFIED | New exports added |

### Task 8: Performance Benchmarks — New Backend vs Current Implementation

**Files:**
- Create: `tests/test_benchmark_backend.py`

This task measures the overhead (if any) of the backend abstraction layer. The new `ASEIO(str)` path goes through `LMDBBackend` → `BytesIO` → LMDB, adding `atoms_to_dict`/`dict_to_atoms` instead of `encode`/`decode`. We need to verify this doesn't regress.

**Step 1: Write benchmark tests**

```python
# tests/test_benchmark_backend.py
"""Benchmark the new backend abstraction vs the current direct implementation.

Measures:
- Read overhead: ASEIO (new backend path) vs direct BytesIO + decode
- Write overhead: ASEIO (new backend path) vs direct BytesIO + encode
- Column access: db["calc.energy"] vs manual loop
- View materialization: db[0:1000] iteration vs direct loop
- Random access: new path vs old path

All benchmarks use the same 1000-ethanol dataset for comparison
with existing benchmarks in test_benchmark_read.py / test_benchmark_write.py.
"""

import pickle
import random
import uuid

import ase
import numpy as np
import pytest
from ase.calculators.singlepoint import SinglePointCalculator

from asebytes import ASEIO, BytesIO, decode, encode
from asebytes._convert import atoms_to_dict, dict_to_atoms
from asebytes.lmdb import LMDBBackend


@pytest.fixture
def ethanol_with_calc(ethanol):
    """Ethanol conformers with energy and forces for column benchmarks."""
    for i, atoms in enumerate(ethanol):
        atoms.calc = SinglePointCalculator(atoms)
        atoms.calc.results = {
            "energy": float(-i * 0.1),
            "forces": np.random.RandomState(i).randn(len(atoms), 3) * 0.01,
        }
    return ethanol


# --- Conversion overhead ---


@pytest.mark.benchmark(group="conversion")
def test_encode_current(benchmark, ethanol):
    """Current: encode(atoms) → dict[bytes, bytes] (msgpack)."""
    atoms = ethanol[0]
    benchmark(encode, atoms)


@pytest.mark.benchmark(group="conversion")
def test_atoms_to_dict_new(benchmark, ethanol):
    """New: atoms_to_dict(atoms) → dict[str, Any] (no serialization)."""
    atoms = ethanol[0]
    benchmark(atoms_to_dict, atoms)


@pytest.mark.benchmark(group="conversion")
def test_decode_current(benchmark, ethanol):
    """Current: decode(data) → ase.Atoms."""
    data = encode(ethanol[0])
    benchmark(decode, data)


@pytest.mark.benchmark(group="conversion")
def test_dict_to_atoms_new(benchmark, ethanol):
    """New: dict_to_atoms(data) → ase.Atoms."""
    data = atoms_to_dict(ethanol[0])
    benchmark(dict_to_atoms, data)


# --- Sequential read: full dataset ---


@pytest.mark.benchmark(group="read_backend")
def test_read_current_aseio(benchmark, ethanol, tmp_path):
    """Current ASEIO: direct BytesIO + decode path."""
    db_path = tmp_path / "read_current.lmdb"
    bio = BytesIO(str(db_path))
    bio.extend([encode(a) for a in ethanol])

    def read_all():
        return [decode(bio[i]) for i in range(len(bio))]

    results = benchmark(read_all)
    assert len(results) == len(ethanol)


@pytest.mark.benchmark(group="read_backend")
def test_read_new_aseio(benchmark, ethanol, tmp_path):
    """New ASEIO: LMDBBackend path with atoms_to_dict/dict_to_atoms."""
    db_path = tmp_path / "read_new.lmdb"
    db = ASEIO(str(db_path))
    db.extend(ethanol)

    def read_all():
        return [db[i] for i in range(len(db))]

    results = benchmark(read_all)
    assert len(results) == len(ethanol)


# --- Sequential write: full dataset ---


@pytest.mark.benchmark(group="write_backend")
def test_write_current_aseio(benchmark, ethanol, tmp_path):
    """Current path: encode + BytesIO.extend."""

    def write_all():
        db_path = tmp_path / f"write_current_{uuid.uuid4().hex}.lmdb"
        bio = BytesIO(str(db_path))
        bio.extend([encode(a) for a in ethanol])
        return bio

    bio = benchmark(write_all)
    assert len(bio) == len(ethanol)


@pytest.mark.benchmark(group="write_backend")
def test_write_new_aseio(benchmark, ethanol, tmp_path):
    """New path: atoms_to_dict + LMDBBackend.append_rows."""

    def write_all():
        db_path = tmp_path / f"write_new_{uuid.uuid4().hex}.lmdb"
        db = ASEIO(str(db_path))
        db.extend(ethanol)
        return db

    db = benchmark(write_all)
    assert len(db) == len(ethanol)


# --- Random access ---


@pytest.mark.benchmark(group="random_access_backend")
def test_random_access_current(benchmark, ethanol, tmp_path):
    """Current path: BytesIO + decode, random indices."""
    db_path = tmp_path / "random_current.lmdb"
    bio = BytesIO(str(db_path))
    bio.extend([encode(a) for a in ethanol])

    random.seed(42)
    indices = [random.randint(0, len(ethanol) - 1) for _ in range(len(ethanol))]

    def random_access():
        return [decode(bio[i]) for i in indices]

    results = benchmark(random_access)
    assert len(results) == len(ethanol)


@pytest.mark.benchmark(group="random_access_backend")
def test_random_access_new(benchmark, ethanol, tmp_path):
    """New path: LMDBBackend, random indices."""
    db_path = tmp_path / "random_new.lmdb"
    db = ASEIO(str(db_path))
    db.extend(ethanol)

    random.seed(42)
    indices = [random.randint(0, len(ethanol) - 1) for _ in range(len(ethanol))]

    def random_access():
        return [db[i] for i in indices]

    results = benchmark(random_access)
    assert len(results) == len(ethanol)


# --- Column access (new feature, no current equivalent) ---


@pytest.mark.benchmark(group="column_access")
def test_column_read_via_view(benchmark, ethanol_with_calc, tmp_path):
    """New: db["calc.energy"] column view, read 1000 energies."""
    db_path = tmp_path / "col_view.lmdb"
    db = ASEIO(str(db_path))
    db.extend(ethanol_with_calc)

    def read_energies():
        return list(db["calc.energy"])

    energies = benchmark(read_energies)
    assert len(energies) == len(ethanol_with_calc)


@pytest.mark.benchmark(group="column_access")
def test_column_read_manual_loop(benchmark, ethanol_with_calc, tmp_path):
    """Baseline: manual loop extracting energy from each Atoms object."""
    db_path = tmp_path / "col_manual.lmdb"
    db = ASEIO(str(db_path))
    db.extend(ethanol_with_calc)

    def read_energies():
        return [db[i].calc.results["energy"] for i in range(len(db))]

    energies = benchmark(read_energies)
    assert len(energies) == len(ethanol_with_calc)


@pytest.mark.benchmark(group="column_access")
def test_column_read_selective_keys(benchmark, ethanol_with_calc, tmp_path):
    """New: read_column on backend directly (skips Atoms construction)."""
    db_path = tmp_path / "col_selective.lmdb"
    backend = LMDBBackend(str(db_path))
    db = ASEIO(backend)
    db.extend(ethanol_with_calc)

    def read_energies():
        return backend.read_column("calc.energy")

    energies = benchmark(read_energies)
    assert len(energies) == len(ethanol_with_calc)


# --- View materialization ---


@pytest.mark.benchmark(group="view_materialization")
def test_row_view_iteration(benchmark, ethanol, tmp_path):
    """New: list(db[0:1000]) via RowView."""
    db_path = tmp_path / "view_iter.lmdb"
    db = ASEIO(str(db_path))
    db.extend(ethanol)

    def iterate_view():
        return list(db[0 : len(ethanol)])

    results = benchmark(iterate_view)
    assert len(results) == len(ethanol)


@pytest.mark.benchmark(group="view_materialization")
def test_direct_iteration(benchmark, ethanol, tmp_path):
    """Baseline: [db[i] for i in range(1000)]."""
    db_path = tmp_path / "direct_iter.lmdb"
    db = ASEIO(str(db_path))
    db.extend(ethanol)

    def iterate_direct():
        return [db[i] for i in range(len(db))]

    results = benchmark(iterate_direct)
    assert len(results) == len(ethanol)


# --- Multi-column access ---


@pytest.mark.benchmark(group="multi_column")
def test_multi_column_view(benchmark, ethanol_with_calc, tmp_path):
    """New: db[["calc.energy", "calc.forces"]] → ColumnView (multi) → to_dict()."""
    db_path = tmp_path / "multi_col.lmdb"
    db = ASEIO(str(db_path))
    db.extend(ethanol_with_calc)

    def read_multi():
        return db[["calc.energy", "calc.forces"]][: len(ethanol_with_calc)].to_dict()

    result = benchmark(read_multi)
    assert len(result["calc.energy"]) == len(ethanol_with_calc)
    assert len(result["calc.forces"]) == len(ethanol_with_calc)


@pytest.mark.benchmark(group="multi_column")
def test_multi_column_manual(benchmark, ethanol_with_calc, tmp_path):
    """Baseline: manual loop extracting energy + forces."""
    db_path = tmp_path / "multi_manual.lmdb"
    db = ASEIO(str(db_path))
    db.extend(ethanol_with_calc)

    def read_multi():
        energies = []
        forces = []
        for i in range(len(db)):
            atoms = db[i]
            energies.append(atoms.calc.results["energy"])
            forces.append(atoms.calc.results["forces"])
        return {"calc.energy": energies, "calc.forces": forces}

    result = benchmark(read_multi)
    assert len(result["calc.energy"]) == len(ethanol_with_calc)
```

**Step 2: Run benchmarks**

Run: `uv run pytest tests/test_benchmark_backend.py -m benchmark --benchmark-only --benchmark-group-by=group -v`
Expected: All pass. Key comparisons to check:

| Comparison | Acceptable overhead |
|-----------|-------------------|
| `atoms_to_dict` vs `encode` | `atoms_to_dict` should be **faster** (no msgpack) |
| `dict_to_atoms` vs `decode` | `dict_to_atoms` should be **faster** (no msgpack.unpackb) |
| New ASEIO read vs current BytesIO+decode | Within **10%** (extra dict[str,Any] hop) |
| New ASEIO write vs current encode+BytesIO | Within **10%** |
| Column view vs manual loop | Column view should be **faster** (skips Atoms construction) |
| RowView iteration vs direct loop | Within **5%** (just a thin wrapper) |

**Step 3: Commit**

```bash
git add tests/test_benchmark_backend.py
git commit -m "bench: add performance comparison between backend abstraction and current path"
```

**Step 4: Run full benchmark suite to compare with external backends**

Run: `uv run pytest tests/test_benchmark_backend.py tests/test_benchmark_read.py tests/test_benchmark_write.py tests/test_benchmark_random_access.py -m benchmark --benchmark-only --benchmark-json=benchmark_results.json -v`

This generates a JSON file that can be compared across runs. If the new path shows >10% regression on read/write, investigate before proceeding.

---

### Task 9: Regression Benchmark Against Main Branch

**Files:** None (no code changes — this is a measurement task)

This task ensures the refactored `ASEIO` doesn't degrade performance for existing users. The existing benchmark suite (`test_benchmark_read.py`, `test_benchmark_write.py`, `test_benchmark_random_access.py`) already tests `ASEIO` as a black box — same tests, same `db.extend(ethanol)` / `db[i]` API. Run them on `main` to capture a baseline, then run them on the feature branch and compare.

**Step 1: Capture baseline on main**

```bash
git stash  # save any uncommitted work
git checkout main
uv run pytest tests/test_benchmark_read.py tests/test_benchmark_write.py tests/test_benchmark_random_access.py \
  -m benchmark --benchmark-only --benchmark-json=benchmark_baseline_main.json -v
git checkout -  # back to feature branch
git stash pop   # restore work
```

**Step 2: Run same benchmarks on feature branch**

```bash
uv run pytest tests/test_benchmark_read.py tests/test_benchmark_write.py tests/test_benchmark_random_access.py \
  -m benchmark --benchmark-only --benchmark-json=benchmark_after_refactor.json -v
```

**Step 3: Compare results**

```bash
uv run pytest-benchmark compare benchmark_baseline_main.json benchmark_after_refactor.json --group-by=name
```

**Acceptance criteria:**

| Benchmark | Max acceptable regression |
|-----------|--------------------------|
| `test_read_asebytes` | **< 10%** slower |
| `test_write_asebytes` | **< 10%** slower |
| `test_random_access_asebytes` | **< 10%** slower |

If any benchmark regresses >10%, profile the hot path (`py-spy` or `cProfile`) and optimize before merging. Common suspects:
- Extra `dict[str, Any]` ↔ `dict[bytes, bytes]` round-trip in `LMDBBackend`
- `atoms_to_dict` creating unnecessary copies
- `dict_to_atoms` being slower than `decode` for some data shapes

**Step 4: Clean up benchmark JSON files**

```bash
rm benchmark_baseline_main.json benchmark_after_refactor.json
```

Do not commit the JSON files.

---

## Not in This Plan (Deferred)

### Features

- `.sample()`, `.filter()`, `.head()`, `.to_pandas()`, `.chunks(size)` — chunked iteration on views for batch processing / DataLoader support
- `cache_to` middleware: `ASEIO(ZarrBackend(...), cache_to=LMDBBackend(...))` — on first read, data is cached to a fast local backend for subsequent reads. Consider TTL / invalidation strategy.
- Sharded LMDB — split single file into `data.NNNN.lmdb` (like FAIRChem) for parallel writes and file management at 100GB+
- PyTorch DataLoader integration (`collate_fn`, `IterableDataset` wrapper)
- LanceDB / SOAP vector similarity search
- Optional deps via extras: `uv add asebytes[zarr]`, `uv add asebytes[hf]`, etc.
- Context manager / resource lifecycle on backends: `__enter__`/`__exit__` with `_is_open` flag. If not explicitly opened, each (batched) operation auto-opens and auto-closes. If explicitly entered via `with`, stays open across operations. Pre-opened file handles (e.g. `h5py.File`, fsspec) just set `_is_open = True` from construction. Enables patterns like:
  ```python
  # Implicit (current LMDB behavior — no change needed)
  db = ASEIO(LMDBBackend("data.lmdb"))

  # Explicit context manager (future H5/remote backends)
  with ASEIO(H5MDBackend("traj.h5")) as db:
      atoms = db[0]

  # Pre-opened fsspec handle (DVC, S3, etc.)
  with fsspec.open("s3://bucket/data.h5") as f:
      db = ASEIO(H5MDBackend(file_handle=f))
      atoms = db[:]
  ```

### Future Backends

All backends implement `ReadableBackend` (some also `WritableBackend`). Lazy imports, optional deps.

| Backend | Module | Type | Notes |
|---------|--------|------|-------|
| **HuggingFace Datasets** | `asebytes.hf` | Read (+ `push_to_hub`) | `load_dataset()` as backend, supports streaming + random access. Format kwarg for OPTIMADE/ColabFit schemas. |
| **OPTIMADE (via HF)** | `asebytes.hf` | Read | LeMaterial-style datasets using OPTIMADE standard schema. Same HF backend with `format="optimade"`. |
| **ColabFit (via HF)** | `asebytes.hf` | Read | ColabFit datasets on HF using ASE-convention schema. Same HF backend with `format="colabfit"`. |
| **Zarr** | `asebytes.zarr` | Read/Write | Cloud-native chunked arrays. Good for remote/S3 access. See zarrtraj for prior art. |
| **Arrow/Parquet** | `asebytes.arrow` | Read/Write | Columnar format for dataset distribution. HF native format. |
| **H5MD** | `asebytes.h5md` | Read/Write | Via znh5md. Mainly useful for post-processing interop, LMDB is faster for training. |
| **ASE I/O** | `asebytes.aseio_backend` | Read | Wraps `ase.io.read()`/`ase.io.iread()`. Supports all ASE formats (XYZ, VASP, CIF, Quantum ESPRESSO, CP2K, LAMMPS, etc.). Enables `ASEIO("trajectory.xyz")`. |
| **chemfiles** | `asebytes.chemfiles` | Read | C++ library with Python bindings. Reads many MD trajectory formats (DCD, TRR, XTC, TNG, etc.). |
| **MDAnalysis** | `asebytes.mdanalysis` | Read | Reads MD trajectories (GROMACS, AMBER, NAMD, LAMMPS, etc.). Topology + trajectory model. |
| **pymatgen** | `asebytes.pymatgen` | Read | Wraps pymatgen's Structure/Molecule I/O. CIF, POSCAR, MPRester API access to Materials Project. |
| **NOMAD** | `asebytes.nomad` | Read | NOMAD Archive API — millions of DFT calculations. REST API backend. |
| **Materials Project** | `asebytes.mp` | Read | Via mp-api. Access to MP database (structures, energies, band gaps, etc.). |
| **AFLOW** | `asebytes.aflow` | Read | AFLOW REST API — thermodynamic/electronic properties database. |
| **JARVIS** | `asebytes.jarvis` | Read | JARVIS-DFT/ML database via jarvis-tools. |
| **ASE Database** | `asebytes.asedb` | Read/Write | Wraps `ase.db.connect()`. Supports SQLite, PostgreSQL, MySQL. Enables `ASEIO("database.lmdb")`. |
| **OCP / FAIRChem** | `asebytes.fairchem` | Read | Read FAIRChem's sharded LMDB format directly (`.NNNN.lmdb` files). |
