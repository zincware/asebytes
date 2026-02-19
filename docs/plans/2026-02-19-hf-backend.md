# HuggingFace Backend Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add read-only backends for HuggingFace Datasets, ColabFit, and OPTIMADE via URI-style prefixes (`hf://`, `colabfit://`, `optimade://`).

**Architecture:** A single `HuggingFaceBackend(ReadableBackend)` class backed by the `datasets` library. A `ColumnMapping` dataclass maps HF dataset columns to asebytes flat-dict convention (`arrays.*`, `calc.*`, `info.*`). Built-in presets for ColabFit and OPTIMADE schemas. Two access modes: downloaded (random access via `load_dataset`) and streaming (sequential-only via `load_dataset(streaming=True)`). Registry extended with URI-prefix matching alongside existing glob patterns.

**Tech Stack:** Python 3.11+, `datasets` (HuggingFace), optional dependency via `pip install asebytes[hf]`.

**Branch:** `feat/hf-backend` (base: `main`)

---

## File Structure (New/Modified)

```
src/asebytes/
├── _registry.py          # MODIFY: add URI-prefix matching
├── __init__.py           # MODIFY: add HuggingFaceBackend export
├── hf/
│   ├── __init__.py       # NEW: exports HuggingFaceBackend, ColumnMapping
│   ├── _backend.py       # NEW: HuggingFaceBackend implementation
│   └── _mappings.py      # NEW: ColumnMapping, COLABFIT, OPTIMADE presets

pyproject.toml            # MODIFY: add [project.optional-dependencies] hf

tests/
├── test_hf_mappings.py   # NEW: ColumnMapping unit tests
├── test_hf_backend.py    # NEW: backend tests (with mock dataset)
├── test_registry_uri.py  # NEW: URI-prefix registry tests
```

---

### Task 1: Column Mapping (`_mappings.py`)

**Files:**
- Create: `src/asebytes/hf/__init__.py`
- Create: `src/asebytes/hf/_mappings.py`
- Test: `tests/test_hf_mappings.py`

The `ColumnMapping` defines how HF dataset columns map to asebytes flat-dict keys. Two built-in presets for ColabFit and OPTIMADE, plus support for custom mappings via dict. Unmapped columns become `info.*`.

**Step 1: Write tests**

```python
# tests/test_hf_mappings.py
import numpy as np
import pytest

from asebytes.hf._mappings import COLABFIT, OPTIMADE, ColumnMapping


class TestColumnMapping:
    def test_create_from_dict(self):
        mapping = ColumnMapping(
            positions="pos",
            numbers="atomic_nums",
            cell="lattice",
            pbc="periodic",
        )
        assert mapping.positions == "pos"
        assert mapping.numbers == "atomic_nums"
        assert mapping.cell == "lattice"
        assert mapping.pbc == "periodic"

    def test_default_extras(self):
        mapping = ColumnMapping(
            positions="pos",
            numbers="nums",
        )
        assert mapping.calc == {}
        assert mapping.info == {}

    def test_calc_mapping(self):
        mapping = ColumnMapping(
            positions="pos",
            numbers="nums",
            calc={"energy": "total_energy", "forces": "atomic_forces"},
        )
        assert mapping.calc["energy"] == "total_energy"

    def test_info_mapping(self):
        mapping = ColumnMapping(
            positions="pos",
            numbers="nums",
            info={"smiles": "canonical_smiles"},
        )
        assert mapping.info["smiles"] == "canonical_smiles"

    def test_apply_row(self):
        """apply() converts an HF row dict to asebytes flat-dict."""
        mapping = ColumnMapping(
            positions="pos",
            numbers="nums",
            cell="lattice",
            pbc="periodic",
            calc={"energy": "total_energy"},
        )
        hf_row = {
            "pos": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
            "nums": [1, 1],
            "lattice": [[10, 0, 0], [0, 10, 0], [0, 0, 10]],
            "periodic": [True, True, True],
            "total_energy": -10.5,
            "extra_col": "hello",
        }
        result = mapping.apply(hf_row)
        assert np.array_equal(result["arrays.positions"], np.array(hf_row["pos"]))
        assert np.array_equal(result["arrays.numbers"], np.array(hf_row["nums"]))
        assert np.array_equal(result["cell"], np.array(hf_row["lattice"]))
        assert np.array_equal(result["pbc"], np.array(hf_row["periodic"]))
        assert result["calc.energy"] == -10.5
        # Unmapped columns go to info.*
        assert result["info.extra_col"] == "hello"

    def test_apply_row_missing_optional(self):
        """Missing optional columns (cell, pbc) get defaults."""
        mapping = ColumnMapping(
            positions="pos",
            numbers="nums",
        )
        hf_row = {
            "pos": [[0.0, 0.0, 0.0]],
            "nums": [1],
        }
        result = mapping.apply(hf_row)
        assert "arrays.positions" in result
        assert "arrays.numbers" in result
        # Defaults for missing cell/pbc
        assert np.array_equal(result["cell"], np.zeros((3, 3)))
        assert np.array_equal(result["pbc"], np.array([False, False, False]))

    def test_apply_row_none_values_skipped(self):
        """None values in mapped columns are skipped."""
        mapping = ColumnMapping(
            positions="pos",
            numbers="nums",
            cell="lattice",
        )
        hf_row = {
            "pos": [[0.0, 0.0, 0.0]],
            "nums": [1],
            "lattice": None,
        }
        result = mapping.apply(hf_row)
        # None cell -> default zeros
        assert np.array_equal(result["cell"], np.zeros((3, 3)))

    def test_arrays_mapping(self):
        """Extra arrays columns are mapped to arrays.*."""
        mapping = ColumnMapping(
            positions="pos",
            numbers="nums",
            arrays={"tags": "atom_tags"},
        )
        hf_row = {
            "pos": [[0.0, 0.0, 0.0]],
            "nums": [1],
            "atom_tags": [42],
        }
        result = mapping.apply(hf_row)
        assert np.array_equal(result["arrays.tags"], np.array([42]))


class TestColabFitPreset:
    def test_positions_column(self):
        assert COLABFIT.positions == "positions"

    def test_numbers_column(self):
        assert COLABFIT.numbers == "atomic_numbers"

    def test_cell_column(self):
        assert COLABFIT.cell == "cell"

    def test_pbc_column(self):
        assert COLABFIT.pbc == "pbc"

    def test_calc_columns(self):
        assert COLABFIT.calc["energy"] == "energy"
        assert COLABFIT.calc["forces"] == "atomic_forces"

    def test_apply_colabfit_row(self):
        hf_row = {
            "positions": [[0.0, 0.0, 0.0]],
            "atomic_numbers": [6],
            "cell": [[10, 0, 0], [0, 10, 0], [0, 0, 10]],
            "pbc": [True, True, True],
            "energy": -5.0,
            "atomic_forces": [[0.1, 0.2, 0.3]],
            "nperiodic_dimensions": 3,
        }
        result = COLABFIT.apply(hf_row)
        assert result["calc.energy"] == -5.0
        assert np.array_equal(result["calc.forces"], np.array([[0.1, 0.2, 0.3]]))
        # Unmapped -> info.*
        assert result["info.nperiodic_dimensions"] == 3


class TestOptimadePreset:
    def test_positions_column(self):
        assert OPTIMADE.positions == "cartesian_site_positions"

    def test_numbers_column(self):
        assert OPTIMADE.numbers == "species_at_sites"

    def test_cell_column(self):
        assert OPTIMADE.cell == "lattice_vectors"

    def test_pbc_column(self):
        assert OPTIMADE.pbc == "dimension_types"

    def test_apply_optimade_row(self):
        hf_row = {
            "cartesian_site_positions": [[0.0, 0.0, 0.0]],
            "species_at_sites": ["C"],
            "lattice_vectors": [[10, 0, 0], [0, 10, 0], [0, 0, 10]],
            "dimension_types": [1, 1, 1],
            "nelements": 1,
            "chemical_formula_reduced": "C",
        }
        result = OPTIMADE.apply(hf_row)
        assert "arrays.positions" in result
        assert "arrays.numbers" in result
        # OPTIMADE uses species strings -> must convert to atomic numbers
        assert result["arrays.numbers"][0] == 6  # Carbon
        # dimension_types [1,1,1] -> pbc [True, True, True]
        assert np.array_equal(result["pbc"], np.array([True, True, True]))
        # Unmapped -> info.*
        assert result["info.nelements"] == 1
        assert result["info.chemical_formula_reduced"] == "C"
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_hf_mappings.py -v`
Expected: `ModuleNotFoundError: No module named 'asebytes.hf'`

**Step 3: Implement ColumnMapping**

```python
# src/asebytes/hf/__init__.py
from asebytes.hf._mappings import COLABFIT, OPTIMADE, ColumnMapping

__all__ = ["ColumnMapping", "COLABFIT", "OPTIMADE"]
```

```python
# src/asebytes/hf/_mappings.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import ase.data
import numpy as np


@dataclass(frozen=True)
class ColumnMapping:
    """Maps HuggingFace dataset columns to asebytes flat-dict convention.

    Parameters
    ----------
    positions : str
        HF column name for atomic positions -> ``arrays.positions``.
    numbers : str
        HF column name for atomic numbers -> ``arrays.numbers``.
        For OPTIMADE, this holds species strings which are auto-converted.
    cell : str | None
        HF column name for cell vectors -> ``cell``. None = always default.
    pbc : str | None
        HF column name for periodic boundary conditions -> ``pbc``.
        None = always default.
    calc : dict[str, str]
        Mapping of calc key -> HF column name, e.g.
        ``{"energy": "total_energy"}`` -> ``calc.energy``.
    info : dict[str, str]
        Mapping of info key -> HF column name, e.g.
        ``{"smiles": "canonical_smiles"}`` -> ``info.smiles``.
    arrays : dict[str, str]
        Mapping of extra arrays key -> HF column name, e.g.
        ``{"tags": "atom_tags"}`` -> ``arrays.tags``.
    species_are_strings : bool
        If True, the numbers column contains element symbols (e.g. "C")
        instead of atomic numbers. Auto-converts using ``ase.data``.
    pbc_are_dimension_types : bool
        If True, the pbc column contains OPTIMADE dimension_types
        (0/1 integers) instead of booleans.
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

    def _mapped_hf_columns(self) -> set[str]:
        """Return the set of all HF column names that have explicit mappings."""
        cols = {self.positions, self.numbers}
        if self.cell is not None:
            cols.add(self.cell)
        if self.pbc is not None:
            cols.add(self.pbc)
        cols.update(self.calc.values())
        cols.update(self.info.values())
        cols.update(self.arrays.values())
        return cols

    def apply(self, hf_row: dict[str, Any]) -> dict[str, Any]:
        """Convert an HF dataset row to asebytes flat-dict format.

        Parameters
        ----------
        hf_row : dict[str, Any]
            A single row from a HuggingFace dataset.

        Returns
        -------
        dict[str, Any]
            Flat dict with ``arrays.*``, ``calc.*``, ``info.*``,
            ``cell``, ``pbc`` keys.
        """
        result: dict[str, Any] = {}

        # Positions (required)
        result["arrays.positions"] = np.asarray(hf_row[self.positions])

        # Numbers (required) — may need species string conversion
        raw_numbers = hf_row[self.numbers]
        if self.species_are_strings:
            result["arrays.numbers"] = np.array(
                [ase.data.atomic_numbers[s] for s in raw_numbers]
            )
        else:
            result["arrays.numbers"] = np.asarray(raw_numbers)

        # Cell (optional)
        raw_cell = hf_row.get(self.cell) if self.cell else None
        if raw_cell is not None:
            result["cell"] = np.asarray(raw_cell)
        else:
            result["cell"] = np.zeros((3, 3))

        # PBC (optional) — may need dimension_types conversion
        raw_pbc = hf_row.get(self.pbc) if self.pbc else None
        if raw_pbc is not None:
            if self.pbc_are_dimension_types:
                result["pbc"] = np.array([bool(d) for d in raw_pbc])
            else:
                result["pbc"] = np.asarray(raw_pbc)
        else:
            result["pbc"] = np.array([False, False, False])

        # Calc columns
        for asebytes_key, hf_col in self.calc.items():
            if hf_col in hf_row and hf_row[hf_col] is not None:
                val = hf_row[hf_col]
                if isinstance(val, list):
                    val = np.asarray(val)
                result[f"calc.{asebytes_key}"] = val

        # Extra arrays columns
        for asebytes_key, hf_col in self.arrays.items():
            if hf_col in hf_row and hf_row[hf_col] is not None:
                result[f"arrays.{asebytes_key}"] = np.asarray(hf_row[hf_col])

        # Info columns (explicit mapping)
        for asebytes_key, hf_col in self.info.items():
            if hf_col in hf_row and hf_row[hf_col] is not None:
                result[f"info.{asebytes_key}"] = hf_row[hf_col]

        # Unmapped columns -> info.*
        mapped = self._mapped_hf_columns()
        for hf_col, value in hf_row.items():
            if hf_col not in mapped and value is not None:
                result[f"info.{hf_col}"] = value

        return result


# --- Built-in presets ---

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
    species_are_strings=True,
    pbc_are_dimension_types=True,
)
```

**Step 4: Run tests**

Run: `uv run pytest tests/test_hf_mappings.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/asebytes/hf/ tests/test_hf_mappings.py
git commit -m "feat: add ColumnMapping with ColabFit and OPTIMADE presets"
```

---

### Task 2: URI-Prefix Registry (`_registry.py`)

**Files:**
- Modify: `src/asebytes/_registry.py`
- Test: `tests/test_registry_uri.py`

Extend the registry to support URI-style prefixes alongside existing glob patterns. URIs are checked first (prefix match), then glob patterns. This keeps backward compatibility.

**Step 1: Write tests**

```python
# tests/test_registry_uri.py
import pytest

from asebytes._registry import get_backend_cls, parse_uri


class TestParseUri:
    def test_hf_prefix(self):
        scheme, path = parse_uri("hf://username/dataset")
        assert scheme == "hf"
        assert path == "username/dataset"

    def test_colabfit_prefix(self):
        scheme, path = parse_uri("colabfit://mlearn_Cu_train")
        assert scheme == "colabfit"
        assert path == "mlearn_Cu_train"

    def test_optimade_prefix(self):
        scheme, path = parse_uri("optimade://alexandria/pbe")
        assert scheme == "optimade"
        assert path == "alexandria/pbe"

    def test_no_prefix_returns_none(self):
        scheme, path = parse_uri("data.lmdb")
        assert scheme is None
        assert path == "data.lmdb"

    def test_file_path_not_uri(self):
        scheme, path = parse_uri("/home/user/data.lmdb")
        assert scheme is None
        assert path == "/home/user/data.lmdb"

    def test_colabfit_auto_prepends_org(self):
        """colabfit://name -> colabfit/name (auto-prepend org)."""
        scheme, path = parse_uri("colabfit://mlearn_Cu_train")
        assert scheme == "colabfit"
        assert path == "mlearn_Cu_train"
        # The actual org prepend happens in get_backend_cls, not parse_uri


class TestGetBackendClsUri:
    def test_hf_returns_hf_backend(self):
        cls = get_backend_cls("hf://username/dataset")
        from asebytes.hf._backend import HuggingFaceBackend
        assert cls is HuggingFaceBackend

    def test_colabfit_returns_hf_backend(self):
        cls = get_backend_cls("colabfit://mlearn_Cu_train")
        from asebytes.hf._backend import HuggingFaceBackend
        assert cls is HuggingFaceBackend

    def test_optimade_returns_hf_backend(self):
        cls = get_backend_cls("optimade://alexandria/pbe")
        from asebytes.hf._backend import HuggingFaceBackend
        assert cls is HuggingFaceBackend

    def test_lmdb_still_works(self):
        cls = get_backend_cls("data.lmdb")
        from asebytes.lmdb import LMDBBackend
        assert cls is LMDBBackend

    def test_xyz_still_works(self):
        cls = get_backend_cls("traj.xyz")
        from asebytes.ase import ASEReadOnlyBackend
        assert cls is ASEReadOnlyBackend

    def test_unknown_raises(self):
        with pytest.raises(KeyError, match="No backend registered"):
            get_backend_cls("unknown://foo")

    def test_readonly_ignored_for_uri(self):
        """URI backends are always read-only; readonly param is ignored."""
        cls = get_backend_cls("hf://user/ds", readonly=True)
        from asebytes.hf._backend import HuggingFaceBackend
        assert cls is HuggingFaceBackend

    def test_readonly_false_uri_raises(self):
        """Requesting writable for URI backend raises TypeError."""
        with pytest.raises(TypeError, match="read-only"):
            get_backend_cls("hf://user/ds", readonly=False)
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_registry_uri.py -v`
Expected: Failures (parse_uri doesn't exist, URI backends not registered)

**Step 3: Update registry**

```python
# src/asebytes/_registry.py
"""Backend registry for mapping file patterns to backend classes."""

from __future__ import annotations

import fnmatch
import importlib

# pattern -> (module_path, writable_cls_name | None, readonly_cls_name)
_BACKEND_REGISTRY: dict[str, tuple[str, str | None, str]] = {
    "*.lmdb": ("asebytes.lmdb", "LMDBBackend", "LMDBReadOnlyBackend"),
    "*.traj": ("asebytes.ase", None, "ASEReadOnlyBackend"),
    "*.xyz": ("asebytes.ase", None, "ASEReadOnlyBackend"),
    "*.extxyz": ("asebytes.ase", None, "ASEReadOnlyBackend"),
}

# scheme -> (module_path, readonly_cls_name)
_URI_REGISTRY: dict[str, tuple[str, str]] = {
    "hf": ("asebytes.hf._backend", "HuggingFaceBackend"),
    "colabfit": ("asebytes.hf._backend", "HuggingFaceBackend"),
    "optimade": ("asebytes.hf._backend", "HuggingFaceBackend"),
}


def parse_uri(path: str) -> tuple[str | None, str]:
    """Parse a URI-style path into (scheme, remainder).

    Returns (None, path) if no URI scheme is detected.
    Only recognizes registered schemes to avoid false positives
    on file paths like ``C:\\Users\\...``.
    """
    if "://" in path:
        scheme, _, remainder = path.partition("://")
        if scheme in _URI_REGISTRY:
            return scheme, remainder
    return None, path


def get_backend_cls(path: str, *, readonly: bool | None = None):
    """Resolve a file path or URI to a backend class.

    Parameters
    ----------
    path : str
        File path or URI (``hf://``, ``colabfit://``, ``optimade://``).
    readonly : bool | None
        If True, return the read-only backend class.
        If False, return the writable backend class (raises TypeError if none).
        If None (default), auto-detect: prefer writable if available, else
        read-only.

    Returns
    -------
    type
        The matched backend class.

    Raises
    ------
    KeyError
        If no backend is registered for the given path.
    TypeError
        If a writable backend is explicitly requested but none is available.
    """
    # Check URI schemes first
    scheme, _remainder = parse_uri(path)
    if scheme is not None:
        if readonly is False:
            raise TypeError(
                f"Backend for '{scheme}://' URIs is read-only, "
                "no writable variant available"
            )
        module_path, cls_name = _URI_REGISTRY[scheme]
        mod = importlib.import_module(module_path)
        return getattr(mod, cls_name)

    # Fall back to glob pattern matching
    for pattern, (module_path, writable, read_only) in _BACKEND_REGISTRY.items():
        if fnmatch.fnmatch(path, pattern):
            mod = importlib.import_module(module_path)
            if readonly is True:
                return getattr(mod, read_only)
            if readonly is False:
                if writable is None:
                    raise TypeError(
                        f"Backend for '{path}' is read-only, "
                        "no writable variant available"
                    )
                return getattr(mod, writable)
            # readonly is None — auto-detect
            if writable is not None:
                return getattr(mod, writable)
            return getattr(mod, read_only)
    raise KeyError(f"No backend registered for '{path}'")
```

**Step 4: Run tests**

Run: `uv run pytest tests/test_registry_uri.py -v`
Expected: Some tests pass (parse_uri, glob backends). HF tests will fail until Task 3 creates `HuggingFaceBackend`. That's expected — move to Task 3.

**Step 5: Commit**

```bash
git add src/asebytes/_registry.py tests/test_registry_uri.py
git commit -m "feat: extend registry with URI-prefix matching for hf/colabfit/optimade"
```

---

### Task 3: HuggingFace Backend (`_backend.py`)

**Files:**
- Create: `src/asebytes/hf/_backend.py`
- Modify: `src/asebytes/hf/__init__.py` (add HuggingFaceBackend export)
- Test: `tests/test_hf_backend.py`

The backend supports two modes:
- **Downloaded** (default): `load_dataset(streaming=False)` gives a `Dataset` with random access and known length.
- **Streaming**: `load_dataset(streaming=True)` gives an `IterableDataset` with unknown length and sequential-only access.

**Step 1: Write tests**

These tests use a mock/fixture to avoid hitting HuggingFace servers. We create a local dataset using the `datasets` library.

```python
# tests/test_hf_backend.py
from __future__ import annotations

import numpy as np
import pytest

from asebytes.hf._mappings import ColumnMapping

datasets = pytest.importorskip("datasets")

from asebytes.hf._backend import HuggingFaceBackend


@pytest.fixture
def sample_data():
    """Create a minimal HF dataset in-memory."""
    return datasets.Dataset.from_dict({
        "positions": [
            [[float(i), 0.0, 0.0]] for i in range(10)
        ],
        "atomic_numbers": [[1] for _ in range(10)],
        "cell": [[[10, 0, 0], [0, 10, 0], [0, 0, 10]] for _ in range(10)],
        "pbc": [[True, True, True] for _ in range(10)],
        "energy": [float(-i) for i in range(10)],
        "tag": [f"mol_{i}" for i in range(10)],
    })


@pytest.fixture
def mapping():
    return ColumnMapping(
        positions="positions",
        numbers="atomic_numbers",
        cell="cell",
        pbc="pbc",
        calc={"energy": "energy"},
    )


@pytest.fixture
def backend(sample_data, mapping):
    return HuggingFaceBackend(dataset=sample_data, mapping=mapping)


@pytest.fixture
def streaming_backend(sample_data, mapping):
    """Simulate streaming by converting to IterableDataset."""
    iterable = sample_data.to_iterable_dataset()
    return HuggingFaceBackend(dataset=iterable, mapping=mapping)


class TestDownloadedBackend:
    def test_len(self, backend):
        assert len(backend) == 10

    def test_read_row(self, backend):
        row = backend.read_row(0)
        assert "arrays.positions" in row
        assert "arrays.numbers" in row
        assert "calc.energy" in row
        assert row["calc.energy"] == 0.0

    def test_read_row_with_keys(self, backend):
        row = backend.read_row(0, keys=["calc.energy"])
        assert "calc.energy" in row
        assert "arrays.positions" not in row

    def test_read_row_index_error(self, backend):
        with pytest.raises(IndexError):
            backend.read_row(100)

    def test_read_rows(self, backend):
        rows = backend.read_rows([0, 5, 9])
        assert len(rows) == 3
        assert rows[1]["calc.energy"] == -5.0

    def test_columns(self, backend):
        cols = backend.columns()
        assert "arrays.positions" in cols
        assert "calc.energy" in cols
        assert "info.tag" in cols

    def test_read_column(self, backend):
        energies = backend.read_column("calc.energy")
        assert len(energies) == 10
        assert energies[0] == 0.0
        assert energies[9] == -9.0

    def test_read_column_with_indices(self, backend):
        energies = backend.read_column("calc.energy", indices=[0, 5])
        assert len(energies) == 2
        assert energies[1] == -5.0

    def test_unmapped_columns_in_info(self, backend):
        """Unmapped HF columns should appear as info.*."""
        row = backend.read_row(0)
        assert "info.tag" in row
        assert row["info.tag"] == "mol_0"

    def test_negative_index(self, backend):
        row = backend.read_row(-1)
        assert row["calc.energy"] == -9.0

    def test_iter_rows(self, backend):
        rows = list(backend.iter_rows([0, 1, 2]))
        assert len(rows) == 3
        assert rows[0]["calc.energy"] == 0.0


class TestStreamingBackend:
    def test_len_raises_type_error(self, streaming_backend):
        with pytest.raises(TypeError, match="unknown"):
            len(streaming_backend)

    def test_read_row_sequential(self, streaming_backend):
        """Streaming backend supports sequential reads via cache."""
        row = streaming_backend.read_row(0)
        assert row["calc.energy"] == 0.0

    def test_iter_rows_sequential(self, streaming_backend):
        rows = list(streaming_backend.iter_rows([0, 1, 2]))
        assert len(rows) == 3

    def test_columns(self, streaming_backend):
        cols = streaming_backend.columns()
        assert "arrays.positions" in cols

    def test_length_discovered_after_full_iteration(self, streaming_backend):
        """After iterating all rows, length should be known."""
        # Read all via iter_rows
        rows = list(streaming_backend.iter_rows(list(range(10))))
        assert len(rows) == 10
        # Length should now be discoverable
        assert len(streaming_backend) == 10


class TestFromUri:
    """Test the from_uri constructor (unit tests with mocked load_dataset)."""

    def test_from_uri_hf(self, monkeypatch, sample_data, mapping):
        """hf://user/dataset -> load_dataset('user/dataset')."""
        called_with = {}

        def mock_load(path, **kwargs):
            called_with["path"] = path
            called_with.update(kwargs)
            return sample_data

        monkeypatch.setattr(
            "asebytes.hf._backend.load_dataset", mock_load
        )
        backend = HuggingFaceBackend.from_uri(
            "hf://myuser/myds", mapping=mapping
        )
        assert called_with["path"] == "myuser/myds"
        assert len(backend) == 10

    def test_from_uri_colabfit(self, monkeypatch, sample_data, mapping):
        """colabfit://name -> load_dataset('colabfit/name')."""
        called_with = {}

        def mock_load(path, **kwargs):
            called_with["path"] = path
            return sample_data

        monkeypatch.setattr(
            "asebytes.hf._backend.load_dataset", mock_load
        )
        backend = HuggingFaceBackend.from_uri(
            "colabfit://mlearn_Cu_train", mapping=mapping
        )
        assert called_with["path"] == "colabfit/mlearn_Cu_train"

    def test_from_uri_colabfit_with_org(self, monkeypatch, sample_data, mapping):
        """colabfit://org/name -> load_dataset('org/name') (no double-prepend)."""
        called_with = {}

        def mock_load(path, **kwargs):
            called_with["path"] = path
            return sample_data

        monkeypatch.setattr(
            "asebytes.hf._backend.load_dataset", mock_load
        )
        backend = HuggingFaceBackend.from_uri(
            "colabfit://someorg/dataset", mapping=mapping
        )
        assert called_with["path"] == "someorg/dataset"

    def test_from_uri_optimade(self, monkeypatch, sample_data):
        """optimade://path -> load_dataset with OPTIMADE mapping."""
        def mock_load(path, **kwargs):
            return sample_data

        monkeypatch.setattr(
            "asebytes.hf._backend.load_dataset", mock_load
        )
        backend = HuggingFaceBackend.from_uri("optimade://alexandria/pbe")
        # Should auto-select OPTIMADE mapping
        from asebytes.hf._mappings import OPTIMADE
        assert backend._mapping is OPTIMADE

    def test_from_uri_streaming(self, monkeypatch, sample_data, mapping):
        """hf://user/ds?streaming=true -> streaming mode."""
        called_with = {}

        def mock_load(path, **kwargs):
            called_with.update(kwargs)
            if kwargs.get("streaming"):
                return sample_data.to_iterable_dataset()
            return sample_data

        monkeypatch.setattr(
            "asebytes.hf._backend.load_dataset", mock_load
        )
        backend = HuggingFaceBackend.from_uri(
            "hf://user/ds", mapping=mapping, streaming=True
        )
        assert called_with.get("streaming") is True
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_hf_backend.py -v`
Expected: `ModuleNotFoundError` or `ImportError`

**Step 3: Implement HuggingFaceBackend**

```python
# src/asebytes/hf/_backend.py
from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterator
from typing import Any

import numpy as np

from asebytes._protocols import ReadableBackend
from asebytes.hf._mappings import COLABFIT, OPTIMADE, ColumnMapping


def load_dataset(path: str, **kwargs):
    """Wrapper around datasets.load_dataset with lazy import."""
    try:
        from datasets import load_dataset as _load
    except ImportError:
        raise ImportError(
            "The 'datasets' package is required for HuggingFace backends. "
            "Install it with: pip install asebytes[hf]"
        ) from None
    return _load(path, **kwargs)


# Scheme -> (default mapping or None, org prefix or None)
_URI_SCHEMES: dict[str, tuple[ColumnMapping | None, str | None]] = {
    "hf": (None, None),
    "colabfit": (COLABFIT, "colabfit"),
    "optimade": (OPTIMADE, None),
}


class HuggingFaceBackend(ReadableBackend):
    """Read-only backend for HuggingFace Datasets.

    Supports both downloaded datasets (random access, known length)
    and streaming datasets (sequential access, unknown length).

    Parameters
    ----------
    dataset : Dataset | IterableDataset
        A HuggingFace dataset object.
    mapping : ColumnMapping
        Column mapping from HF schema to asebytes convention.
    cache_size : int
        Maximum number of rows to keep in the LRU cache. Default 1000.
    """

    def __init__(
        self,
        dataset: Any,
        mapping: ColumnMapping,
        cache_size: int = 1000,
    ):
        self._dataset = dataset
        self._mapping = mapping
        self._cache_size = cache_size
        self._cache: OrderedDict[int, dict[str, Any]] = OrderedDict()
        self._is_streaming = not hasattr(dataset, "__getitem__")
        self._length: int | None = None
        self._stream_pos: int = 0
        self._stream_iter: Iterator | None = None

        # For downloaded datasets, length is known immediately
        if not self._is_streaming:
            self._length = len(dataset)

    @classmethod
    def from_uri(
        cls,
        uri: str,
        *,
        mapping: ColumnMapping | None = None,
        streaming: bool = False,
        split: str | None = None,
        cache_size: int = 1000,
        **load_kwargs,
    ) -> HuggingFaceBackend:
        """Construct from a URI like ``hf://user/dataset``.

        Parameters
        ----------
        uri : str
            URI with scheme (``hf://``, ``colabfit://``, ``optimade://``).
        mapping : ColumnMapping | None
            Column mapping. If None, auto-detected from URI scheme.
        streaming : bool
            If True, use streaming mode (sequential access only).
        split : str | None
            Dataset split to load (e.g. "train"). If None, uses default.
        cache_size : int
            LRU cache size.
        **load_kwargs
            Additional kwargs passed to ``datasets.load_dataset()``.
        """
        scheme, remainder = uri.split("://", 1)

        scheme_info = _URI_SCHEMES.get(scheme)
        if scheme_info is None:
            raise ValueError(f"Unknown URI scheme: {scheme!r}")

        default_mapping, org_prefix = scheme_info

        # Auto-prepend org for colabfit:// if no org in path
        hf_path = remainder
        if org_prefix is not None and "/" not in remainder:
            hf_path = f"{org_prefix}/{remainder}"

        # Auto-select mapping
        if mapping is None:
            if default_mapping is not None:
                mapping = default_mapping
            else:
                raise ValueError(
                    f"No default column mapping for scheme '{scheme}'. "
                    "Please provide a ColumnMapping."
                )

        load_kwargs["streaming"] = streaming
        if split is not None:
            load_kwargs["split"] = split

        dataset = load_dataset(hf_path, **load_kwargs)
        return cls(dataset=dataset, mapping=mapping, cache_size=cache_size)

    def _cache_put(self, index: int, row: dict[str, Any]) -> None:
        """Insert or update LRU cache, evicting oldest if at capacity."""
        if index in self._cache:
            self._cache[index] = row
            self._cache.move_to_end(index)
            return
        self._cache[index] = row
        if len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)

    def _read_hf_row(self, index: int) -> dict[str, Any]:
        """Read and convert a single row from the dataset."""
        if index in self._cache:
            self._cache.move_to_end(index)
            return self._cache[index]

        if self._is_streaming:
            return self._read_streaming(index)

        # Downloaded: direct random access
        if index < 0 and self._length is not None:
            index = index + self._length
        if self._length is not None and (index < 0 or index >= self._length):
            raise IndexError(index)

        hf_row = self._dataset[index]
        row = self._mapping.apply(hf_row)
        self._cache_put(index, row)
        return row

    def _read_streaming(self, index: int) -> dict[str, Any]:
        """Read from streaming dataset, advancing iterator as needed."""
        if index in self._cache:
            self._cache.move_to_end(index)
            return self._cache[index]

        if self._stream_iter is None:
            self._stream_iter = iter(self._dataset)
            self._stream_pos = 0

        # If we need to go back, we need to restart the iterator
        if index < self._stream_pos:
            self._stream_iter = iter(self._dataset)
            self._stream_pos = 0

        # Advance to the requested index
        while self._stream_pos <= index:
            try:
                hf_row = next(self._stream_iter)
            except StopIteration:
                self._length = self._stream_pos
                raise IndexError(index)
            row = self._mapping.apply(hf_row)
            self._cache_put(self._stream_pos, row)
            self._stream_pos += 1

        return self._cache[index]

    def __len__(self) -> int:
        if self._length is None:
            raise TypeError(
                "Length unknown for streaming dataset. "
                "Iterate to discover length, or use downloaded mode."
            )
        return self._length

    def columns(self, index: int = 0) -> list[str]:
        row = self._read_hf_row(index)
        return list(row.keys())

    def read_row(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any]:
        row = self._read_hf_row(index)
        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return row

    def read_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any]]:
        return [self.read_row(i, keys) for i in indices]

    def iter_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> Iterator[dict[str, Any]]:
        """Stream rows. Uses sequential streaming when indices are sorted."""
        for i in indices:
            yield self.read_row(i, keys)

    def read_column(
        self, key: str, indices: list[int] | None = None
    ) -> list[Any]:
        if indices is None:
            indices = list(range(len(self)))
        return [self.read_row(i, [key])[key] for i in indices]
```

**Step 4: Update `hf/__init__.py`**

```python
# src/asebytes/hf/__init__.py
from asebytes.hf._backend import HuggingFaceBackend
from asebytes.hf._mappings import COLABFIT, OPTIMADE, ColumnMapping

__all__ = ["HuggingFaceBackend", "ColumnMapping", "COLABFIT", "OPTIMADE"]
```

**Step 5: Run tests**

Run: `uv run pytest tests/test_hf_backend.py tests/test_hf_mappings.py tests/test_registry_uri.py -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add src/asebytes/hf/ tests/test_hf_backend.py
git commit -m "feat: add HuggingFaceBackend with downloaded and streaming modes"
```

---

### Task 4: ASEIO Integration + URI Constructor

**Files:**
- Modify: `src/asebytes/io.py` (ASEIO constructor handles URIs)
- Test: `tests/test_hf_aseio.py`

When `ASEIO("colabfit://mlearn_Cu_train")` is called, the registry resolves it to `HuggingFaceBackend`, and the constructor calls `HuggingFaceBackend.from_uri(...)` instead of `cls(path, **kwargs)`.

**Step 1: Write tests**

```python
# tests/test_hf_aseio.py
import numpy as np
import pytest

datasets = pytest.importorskip("datasets")

from asebytes import ASEIO
from asebytes.hf._backend import HuggingFaceBackend
from asebytes.hf._mappings import COLABFIT, ColumnMapping


@pytest.fixture
def sample_data():
    return datasets.Dataset.from_dict({
        "positions": [[[float(i), 0.0, 0.0]] for i in range(5)],
        "atomic_numbers": [[1] for _ in range(5)],
        "cell": [[[10, 0, 0], [0, 10, 0], [0, 0, 10]] for _ in range(5)],
        "pbc": [[True, True, True] for _ in range(5)],
        "energy": [float(-i) for i in range(5)],
    })


@pytest.fixture
def mapping():
    return ColumnMapping(
        positions="positions",
        numbers="atomic_numbers",
        cell="cell",
        pbc="pbc",
        calc={"energy": "energy"},
    )


class TestAseioFromBackend:
    def test_aseio_from_hf_backend(self, sample_data, mapping):
        backend = HuggingFaceBackend(dataset=sample_data, mapping=mapping)
        db = ASEIO(backend)
        assert len(db) == 5

    def test_getitem_int(self, sample_data, mapping):
        backend = HuggingFaceBackend(dataset=sample_data, mapping=mapping)
        db = ASEIO(backend)
        atoms = db[0]
        assert atoms.positions[0, 0] == pytest.approx(0.0)

    def test_getitem_slice(self, sample_data, mapping):
        backend = HuggingFaceBackend(dataset=sample_data, mapping=mapping)
        db = ASEIO(backend)
        view = db[1:3]
        atoms_list = list(view)
        assert len(atoms_list) == 2

    def test_column_access(self, sample_data, mapping):
        backend = HuggingFaceBackend(dataset=sample_data, mapping=mapping)
        db = ASEIO(backend)
        energies = db["calc.energy"].to_list()
        assert energies == pytest.approx([0.0, -1.0, -2.0, -3.0, -4.0])

    def test_iter(self, sample_data, mapping):
        backend = HuggingFaceBackend(dataset=sample_data, mapping=mapping)
        db = ASEIO(backend)
        atoms_list = list(db)
        assert len(atoms_list) == 5

    def test_readonly_errors(self, sample_data, mapping):
        import ase
        backend = HuggingFaceBackend(dataset=sample_data, mapping=mapping)
        db = ASEIO(backend)
        with pytest.raises(TypeError, match="read-only"):
            db.extend([ase.Atoms("H")])


class TestAseioFromUri:
    def test_from_colabfit_uri(self, monkeypatch, sample_data):
        def mock_load(path, **kwargs):
            return sample_data

        monkeypatch.setattr(
            "asebytes.hf._backend.load_dataset", mock_load
        )
        db = ASEIO("colabfit://test_dataset")
        assert len(db) == 5
        atoms = db[0]
        assert hasattr(atoms, "positions")

    def test_from_hf_uri_with_mapping(self, monkeypatch, sample_data, mapping):
        def mock_load(path, **kwargs):
            return sample_data

        monkeypatch.setattr(
            "asebytes.hf._backend.load_dataset", mock_load
        )
        db = ASEIO("hf://user/dataset", mapping=mapping)
        assert len(db) == 5

    def test_from_hf_uri_streaming(self, monkeypatch, sample_data, mapping):
        def mock_load(path, **kwargs):
            if kwargs.get("streaming"):
                return sample_data.to_iterable_dataset()
            return sample_data

        monkeypatch.setattr(
            "asebytes.hf._backend.load_dataset", mock_load
        )
        db = ASEIO("hf://user/dataset", mapping=mapping, streaming=True)
        atoms = db[0]
        assert hasattr(atoms, "positions")
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_hf_aseio.py -v`
Expected: URI constructor tests fail (ASEIO doesn't handle URIs for construction yet)

**Step 3: Update ASEIO constructor**

In `src/asebytes/io.py`, modify the `__init__` to detect URIs and call `from_uri`:

```python
# In ASEIO.__init__, replace the str branch:
def __init__(
    self,
    backend: str | ReadableBackend,
    *,
    readonly: bool | None = None,
    **kwargs: Any,
):
    if isinstance(backend, str):
        from asebytes._registry import get_backend_cls, parse_uri

        scheme, _remainder = parse_uri(backend)
        if scheme is not None:
            # URI-style: delegate to from_uri constructor
            cls = get_backend_cls(backend, readonly=readonly)
            self._backend: ReadableBackend = cls.from_uri(backend, **kwargs)
        else:
            # File path: pass path directly to backend constructor
            cls = get_backend_cls(backend, readonly=readonly)
            self._backend = cls(backend, **kwargs)
    else:
        self._backend = backend
```

**Step 4: Run tests**

Run: `uv run pytest tests/test_hf_aseio.py tests/test_hf_backend.py tests/test_hf_mappings.py tests/test_registry_uri.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/asebytes/io.py tests/test_hf_aseio.py
git commit -m "feat: ASEIO constructor handles URI-style backends via from_uri"
```

---

### Task 5: Optional Dependency + Exports

**Files:**
- Modify: `pyproject.toml` (add `[project.optional-dependencies]`)
- Modify: `src/asebytes/__init__.py` (add lazy HF exports)
- Verify: full test suite

**Step 1: Update `pyproject.toml`**

Add optional dependency group after `[project]` dependencies:

```toml
[project.optional-dependencies]
hf = ["datasets"]
```

Also add `datasets` to the dev dependencies so tests can run.

**Step 2: Update `__init__.py`**

Add conditional imports for HF backend:

```python
# At the end of existing imports in __init__.py, add:
try:
    from .hf import COLABFIT, OPTIMADE, ColumnMapping, HuggingFaceBackend
except ImportError:
    pass
else:
    __all__ += [
        "HuggingFaceBackend",
        "ColumnMapping",
        "COLABFIT",
        "OPTIMADE",
    ]
```

**Step 3: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests PASS (existing + new HF tests)

**Step 4: Commit**

```bash
git add pyproject.toml src/asebytes/__init__.py
git commit -m "feat: add asebytes[hf] optional dependency, export HF backend"
```

---

### Task 6: Update README

**Files:**
- Modify: `README.md`

**Step 1: Add HuggingFace backend documentation to README**

Add after the existing "Backends" section:

```markdown
### HuggingFace Datasets

Access HuggingFace datasets directly via URI-style prefixes:

```python
from asebytes import ASEIO

# ColabFit datasets (auto-selects column mapping)
db = ASEIO("colabfit://mlearn_Cu_train")
atoms = db[0]
energies = db["calc.energy"].to_list()

# OPTIMADE datasets
db = ASEIO("optimade://alexandria/pbe")

# Generic HuggingFace datasets (requires explicit column mapping)
from asebytes import ColumnMapping
mapping = ColumnMapping(
    positions="pos", numbers="nums",
    calc={"energy": "total_energy"},
)
db = ASEIO("hf://user/dataset", mapping=mapping)

# Streaming mode (sequential access, unknown length)
db = ASEIO("hf://user/large_dataset", mapping=mapping, streaming=True)
for atoms in db:
    process(atoms)
```

Install HuggingFace support: `pip install asebytes[hf]`
```

**Step 2: Update backends list in README**

Add `HuggingFaceBackend` to the backends list.

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add HuggingFace backend documentation to README"
```

---

### Task 7: Run Full Test Suite + Existing Tests Regression

**No code changes.** Verify everything works together.

**Step 1: Run full test suite**

Run: `uv run pytest -v`
Expected: All PASS

**Step 2: Verify existing LMDB and ASE backend tests are unaffected**

Run: `uv run pytest tests/test_aseio.py tests/test_bytesio.py tests/test_lmdb_backend.py tests/test_ase_backend.py tests/test_aseio_views.py -v`
Expected: All PASS (no regressions)

**Step 3: Verify import without datasets installed**

Run: `python -c "import asebytes; print(asebytes.__all__)"`
Expected: No ImportError. HF exports just absent from `__all__`.

---

## Summary of Changes

| Component | Status | Description |
|-----------|--------|-------------|
| `hf/_mappings.py` | NEW | `ColumnMapping` dataclass + `COLABFIT`, `OPTIMADE` presets |
| `hf/_backend.py` | NEW | `HuggingFaceBackend(ReadableBackend)` — downloaded + streaming |
| `hf/__init__.py` | NEW | Package exports |
| `_registry.py` | MODIFIED | URI-prefix matching (`hf://`, `colabfit://`, `optimade://`) |
| `io.py` | MODIFIED | ASEIO constructor delegates to `from_uri` for URI backends |
| `pyproject.toml` | MODIFIED | `[project.optional-dependencies]` hf = ["datasets"] |
| `__init__.py` | MODIFIED | Conditional HF exports |
| `README.md` | MODIFIED | HF backend documentation |

## Not in This Plan (Deferred)

- `push_to_hub` write support
- Zarr, Arrow/Parquet backends
- Caching middleware (`cache_to=LMDBBackend(...)`)
- Split/subset selection in URI (e.g. `hf://user/ds?split=train`)
- Authentication / private dataset access
