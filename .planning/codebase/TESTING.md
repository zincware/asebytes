# Testing Patterns

**Analysis Date:** 2026-03-06

## Test Framework

**Runner:**
- pytest >= 8.4.2
- Config: `pyproject.toml` `[tool.pytest.ini_options]`

**Assertion Library:**
- pytest built-in `assert`
- `pytest.approx` for floating point
- `numpy.testing.assert_array_equal` and `assert_array_almost_equal` for arrays

**Async:**
- `anyio >= 4.0` (via dev deps)
- `@pytest.mark.anyio` for async test methods

**Benchmarks:**
- `pytest-benchmark >= 5.2.1`
- `@pytest.mark.benchmark` marker
- Excluded from default runs via `addopts = ["-m", "not benchmark"]`

**Run Commands:**
```bash
uv run pytest                              # Run all tests (excludes benchmarks)
uv run pytest -m benchmark --benchmark-only  # Run benchmarks only
uv run pytest tests/test_aseio.py          # Run specific test file
uv run pytest -k "test_extend"             # Run by name pattern
```

## Test File Organization

**Location:**
- All tests in `tests/` directory (flat, not co-located with source)
- Benchmarks in `tests/benchmarks/` sub-directory

**Naming:**
- `test_<feature>.py` for feature tests
- `test_<component>_<aspect>.py` for focused tests: `test_blob_negative_index.py`, `test_sync_facade_repr.py`
- `conftest.py` in `tests/` for shared fixtures
- `conftest.py` in `tests/benchmarks/` for benchmark-specific fixtures

**Structure:**
```
tests/
    conftest.py                      # Shared fixtures (Atoms, db_path, backends)
    conftest_hf.py                   # HuggingFace-specific fixtures
    test_aseio.py                    # ASEIO facade tests
    test_async_aseio.py              # AsyncASEIO facade tests
    test_views.py                    # RowView/ColumnView unit tests
    test_adapters.py                 # BlobToObject/ObjectToBlob adapter tests
    test_protocols.py                # ABC protocol tests
    test_dataset_roundtrip.py        # Multi-backend round-trip integration tests
    test_error_handling.py           # Error condition tests
    test_columnar_backend.py         # ColumnarBackend tests
    test_lmdb_backend.py             # LMDB backend tests
    test_mongodb.py                  # MongoDB backend tests
    test_redis.py                    # Redis backend tests
    ...
    benchmarks/
        conftest.py                  # Pre-populated DB fixtures
        test_bench_write.py          # Write benchmarks
        test_bench_read.py           # Read benchmarks
        test_bench_random_access.py  # Random access benchmarks
        test_bench_update.py         # Update benchmarks
        test_bench_property_access.py  # Property access benchmarks
```

## Test Structure

**Suite Organization:**
```python
# Class-based grouping for related tests (see test_views.py, test_async_aseio.py)
class TestRowView:
    def test_len(self, parent):
        view = RowView(parent, range(3, 7))
        assert len(view) == 4

    def test_getitem_int(self, parent):
        view = RowView(parent, range(3, 7))
        atoms = view[0]
        assert isinstance(atoms, ase.Atoms)

# Flat functions for simpler tests (see test_aseio.py, test_error_handling.py)
def test_set_get(io, ethanol):
    io[0] = ethanol[0]
    atoms = io[0]
    assert atoms == ethanol[0]
```

**Patterns:**
- Class-based test grouping with `Test*` prefix for related operations (e.g., `TestSingleItemAccess`, `TestBulkRead`, `TestWriteOps`)
- Flat `test_*` functions for simpler/isolated tests
- Section comments with `=` or `-` dividers for visual grouping:
  ```python
  # ========================================================================
  # Single-item access
  # ========================================================================
  ```

**Setup:**
- pytest fixtures for all setup (no `setUp`/`tearDown`)
- `tmp_path` for file-based backends
- Fixture-scoped cleanup (pytest handles temp dirs)

## Fixtures

**Shared fixtures in `tests/conftest.py`:**

```python
# Parametrized path fixture for multi-backend testing
EXTENSIONS = [".lmdb", ".h5", ".zarr"]

@pytest.fixture(params=EXTENSIONS)
def db_path(tmp_path, request):
    """Yield a fresh path with each writable-backend extension."""
    return str(tmp_path / f"test{request.param}")

# Pre-built Atoms objects
@pytest.fixture
def ethanol() -> list[ase.Atoms]:
    """Return 1000 ethanol conformers with calculator results."""
    ...

@pytest.fixture
def simple_atoms() -> ase.Atoms:
    """Return a simple single-atom Atoms object."""
    return ase.Atoms("H", positions=[[0, 0, 0]])

# Pre-built IO instances
@pytest.fixture
def aseio_instance(tmp_path):
    return asebytes.ASEIO(str(tmp_path / "test.lmdb"))
```

**Universal backend fixtures for cross-format testing:**
```python
# In conftest.py — parametrized across native + adapter backends
@pytest.fixture(params=[
    pytest.param(_lmdb_blob, id="lmdb-blob-native"),
    pytest.param(_zarr_blob, id="zarr-blob-via-adapter"),
    pytest.param(_h5_blob, id="h5-blob-via-adapter"),
])
def uni_blob_backend(tmp_path, request):
    """Universal blob-level backend fixture across all storage formats."""
    return request.param(tmp_path)
```

**Per-test fixtures for focused tests:**
```python
# In test_views.py — MockParent instead of real backend
class MockParent:
    def __init__(self, rows):
        self._rows = rows
    def _read_row(self, index, keys=None):
        ...
    def _build_result(self, row):
        ...

@pytest.fixture
def parent():
    rows = [{"arrays.numbers": np.array([1]), ...} for i in range(10)]
    return MockParent(rows)
```

**S22 dataset fixtures for comprehensive round-trip testing:**
- `s22`, `s22_energy`, `s22_energy_forces`, `s22_all_properties`
- `s22_info_arrays_calc`, `s22_mixed_pbc_cell`, `s22_illegal_calc_results`
- `s22_nested_calc`, `s22_info_arrays_calc_missing_inbetween`

## Mocking

**Framework:** No dedicated mocking framework. Tests use:

**In-memory backends:**
```python
# Minimal in-memory backend for testing (from test_async_aseio.py)
class MemoryBackend(ReadWriteBackend):
    def __init__(self):
        self._rows: list[dict[str, Any] | None] = []
    def get(self, index, keys=None):
        ...
    def set(self, index, data):
        ...
```

**Mock parent objects:**
```python
# MockParent for view tests (from test_views.py)
class MockParent:
    def __init__(self, rows):
        self._rows = rows
    def _read_row(self, index, keys=None):
        ...
    def _build_result(self, row):
        ...
```

**What to Mock:**
- Use `MemoryBackend` or `MockParent` when testing facade/view logic independently of storage
- Use `MemoryObjectBackend` (built-in) for integration tests not requiring disk I/O

**What NOT to Mock:**
- Backend storage operations in round-trip tests (use real LMDB/HDF5/Zarr)
- Serialization/deserialization (use real msgpack)
- The `db_path` fixture ensures real backends are tested for every writable format

## Fixtures and Factories

**Test Data:**
```python
# Row factory (from test_async_aseio.py)
def _make_row(i: int) -> dict[str, Any]:
    return {
        "arrays.numbers": [1, 2],
        "arrays.positions": [[0.0, 0.0, float(i)], [1.0, 0.0, float(i)]],
        "cell": [[10.0, 0, 0], [0, 10.0, 0], [0, 0, 10.0]],
        "pbc": [True, True, True],
        "calc.energy": float(-i),
        "info.tag": f"mol_{i}",
    }

# Atoms factory
def _make_atoms(i: int) -> ase.Atoms:
    atoms = ase.Atoms(numbers=[1, 2], positions=..., cell=..., pbc=...)
    atoms.info["tag"] = f"mol_{i}"
    calc = SinglePointCalculator(atoms, energy=float(-i), forces=...)
    atoms.calc = calc
    return atoms

# Columnar backend row factory (from test_columnar_backend.py)
def _make_rows(n_frames: int, rng=None) -> list[dict[str, object]]:
    rows = []
    for i in range(n_frames):
        n_atoms = rng.integers(3, 20)
        rows.append({
            "arrays.positions": rng.random((n_atoms, 3)),
            "arrays.numbers": rng.integers(1, 30, size=n_atoms),
            "calc.energy": float(-i * 0.1),
            ...
        })
    return rows
```

**Location:**
- Shared fixtures: `tests/conftest.py`
- Factory functions: defined at the top of test files that use them
- Benchmark fixtures: `tests/benchmarks/conftest.py`

## Coverage

**Requirements:** No coverage target enforced. No coverage configuration found.

**View Coverage:**
```bash
uv run pytest --cov=asebytes --cov-report=html   # (requires pytest-cov)
```

## Test Types

**Unit Tests:**
- ABC protocol tests: `tests/test_protocols.py` — verify MinimalReadable/MinimalWritable implement the contract
- View tests: `tests/test_views.py` — RowView/ColumnView logic with MockParent
- Adapter tests: `tests/test_adapters.py` — BlobToObject/ObjectToBlob serialization
- Error handling: `tests/test_error_handling.py` — all expected error conditions

**Integration Tests:**
- Round-trip tests: `tests/test_dataset_roundtrip.py` — write diverse datasets, read back, assert equality across all backends
- Async integration: `tests/test_async_aseio.py` — full AsyncASEIO stack with SyncToAsyncAdapter
- Multi-backend parametrized: `tests/test_universal_object_backend.py`, `tests/test_universal_blob_backend.py`
- Backend-specific: `tests/test_lmdb_backend.py`, `tests/test_columnar_backend.py`, `tests/test_mongodb.py`, `tests/test_redis.py`

**Benchmark Tests:**
- Located in `tests/benchmarks/`
- Use `pytest-benchmark` with `@pytest.mark.benchmark(group="...")`
- Groups: `write_trajectory`, `write_single`, `read_trajectory`, `read_random`, `read_column`, `update`, `property_access`
- Compare asebytes backends against third-party libraries (ASE SQLite, aselmdb, znh5md, extxyz)
- Run separately: `uv run pytest -m benchmark --benchmark-only`

**E2E Tests:**
- Not a web app; round-trip tests serve as end-to-end validation
- CI runs on Python 3.11, 3.12, 3.13 with real Redis and MongoDB services

## Common Patterns

**Multi-backend Parametrization:**
```python
# Test same logic across all writable backends
@pytest.fixture(params=EXTENSIONS)  # [".lmdb", ".h5", ".zarr"]
def db_path(tmp_path, request):
    return str(tmp_path / f"test{request.param}")

def test_something(db_path):
    io = asebytes.ASEIO(db_path)
    ...
```

**Round-trip Assertion Helper:**
```python
def assert_atoms_roundtrip(a, b):
    """Full round-trip assertion."""
    npt.assert_array_equal(a.get_atomic_numbers(), b.get_atomic_numbers())
    npt.assert_array_equal(a.get_positions(), b.get_positions())
    npt.assert_array_equal(a.get_cell(), b.get_cell())
    npt.assert_array_equal(a.get_pbc(), b.get_pbc())
    if a.calc is not None:
        assert b.calc is not None
        for key in a.calc.results:
            npt.assert_array_equal(a.calc.results[key], b.calc.results[key])
    ...
```

**Async Testing:**
```python
class TestSingleItemAccess:
    @pytest.mark.anyio
    async def test_await_single_row(self, db, backend):
        result = await db[0]
        assert isinstance(result, ase.Atoms)
```

**Error Testing:**
```python
def test_encode_with_non_atoms_string_raises_typeerror():
    with pytest.raises(TypeError, match="Input must be an ase.Atoms object"):
        asebytes.encode("not an atoms object")

def test_aseio_getitem_nonexistent_index_raises_indexerror(tmp_path):
    io = asebytes.ASEIO(str(tmp_path / "test.lmdb"))
    with pytest.raises(IndexError):
        _ = io[0]
```

**Fixture-indirect Parametrization:**
```python
@pytest.mark.parametrize("dataset", [
    "s22", "s22_energy", "s22_all_properties", "s22_info_arrays_calc",
    "s22_mixed_pbc_cell", "s22_illegal_calc_results", "water", "s22_nested_calc",
])
def test_datasets(db_path, dataset, request):
    images = request.getfixturevalue(dataset)
    io = asebytes.ASEIO(db_path)
    io.extend(images)
    ...
```

**Benchmark Pattern:**
```python
@pytest.mark.benchmark(group="write_trajectory")
def test_write_trajectory_asebytes_lmdb(benchmark, dataset, tmp_path):
    name, frames = dataset
    def fn():
        p = tmp_path / f"wt_{name}_lmdb_{uuid.uuid4().hex}.lmdb"
        db = ASEIO(str(p))
        db.extend(frames)
    benchmark(fn)
```

## CI Configuration

**File:** `.github/workflows/tests.yml`

**Matrix:**
- Python 3.11, 3.12, 3.13 on ubuntu-latest

**Services:**
- Redis 7 on port 6379
- MongoDB 7 on port 27017 (root/example)

**Steps:**
1. `uv sync --all-extras --dev`
2. `uv run pytest` (all tests except benchmarks)
3. `uv run pytest -m benchmark --benchmark-only --benchmark-json=benchmark_results.json`
4. Benchmark visualization and artifact upload

---

*Testing analysis: 2026-03-06*
