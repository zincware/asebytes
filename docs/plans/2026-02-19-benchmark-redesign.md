# Benchmark Redesign

## Overview

Redesign the benchmark suite to use realistic data, cover all backends
(including asebytes H5MD), and produce one figure per operation.

## Datasets

### ethanol (modified existing)

1000 ethanol conformers from molify with `SinglePointCalculator` attached:
energy, forces, stress. Small molecules (9 atoms each, uniform size). Tests
the "many small frames" pattern.

Update the existing `conftest.py` fixture to attach calculator results.

### lemat (new)

1000 frames from `LeMaterial/LeMat-Traj` `compatible_pbe` split on
HuggingFace. Variable atom counts, periodic cells, real DFT energies +
forces + stress. Tests the "variable-size periodic systems" pattern.

**Download script** (`scripts/download_benchmark_data.py`):

```python
from asebytes import ASEIO

src = ASEIO("optimade://LeMaterial/LeMat-Traj", split="train",
            name="compatible_pbe", streaming=True)
cache = ASEIO("tests/data/lemat_1000.lmdb")
cache.extend(list(src[:1000]))
```

Run once; the `.lmdb` is gitignored. Conftest loads it with
`@pytest.fixture(scope="session")` and `pytest.skip` if the file is missing.

## Backends

| Backend | Key | Write | Read | Random | Column | Size |
|---------|-----|:-----:|:----:|:------:|:------:|:----:|
| asebytes LMDB | `asebytes_lmdb` | x | x | x | x | x |
| asebytes H5MD | `asebytes_h5md` | x | x | x | x | x |
| aselmdb | `aselmdb` | x | x | x | x | x |
| znh5md | `znh5md` | x | x | x | x | x |
| extxyz | `extxyz` | x | x | skip | - | x |
| sqlite | `sqlite` | x | x | x | x | x |

extxyz random access is skipped (requires full file scan per access).
extxyz has no column access (must parse entire file).

## Column Access Methods

Each backend's fastest "read just energies" path:

| Backend | Method |
|---------|--------|
| asebytes LMDB | `db["calc.energy"].to_list()` |
| asebytes H5MD | `db["calc.energy"].to_list()` |
| aselmdb | `[row.energy for row in db.select(columns=['id', 'energy'])]` |
| znh5md | `f['particles/atoms/observables/energy/value'][:]` (direct h5py) |
| sqlite | `[row.energy for row in db.select(columns=['id', 'energy'])]` |

## Benchmark Files

Each file covers one operation. Tests are parametrized over datasets.

| File | Group | Contents |
|------|-------|----------|
| `test_benchmark_write.py` | `write` | Bulk `extend()` for all 6 backends |
| `test_benchmark_read.py` | `read` | Sequential read (all rows) for all 6 |
| `test_benchmark_random_access.py` | `random_access` | 1000 random index reads (5 backends) |
| `test_benchmark_column_access.py` | `column_access` | Read 1000 energies (5 backends) |
| `test_benchmark_file_size.py` | `file_size` | Measure output file size in bytes |
| `test_benchmark_backend.py` | *(various)* | Keep as-is (internal regression) |

### Test naming convention

```
test_{operation}_{backend}[ethanol]
test_{operation}_{backend}[lemat]
```

Example: `test_write_asebytes_lmdb[ethanol]`, `test_read_znh5md[lemat]`.

### File size benchmark

Not a time benchmark. Writes each backend, measures file/directory size,
stores as a pytest-benchmark "extra info" metric. The visualization script
reads these from the JSON output.

## Visualization

`docs/visualize_benchmarks.py` produces one PNG per operation:

- `benchmark_write.png`
- `benchmark_read.png`
- `benchmark_random_access.png`
- `benchmark_column_access.png`
- `benchmark_file_size.png`

Each figure: grouped bars (one color per backend, two groups: ethanol /
lemat). Log scale for time axes. Value labels on bars. File size in MB.

### Backend colors

```python
COLORS = {
    "asebytes LMDB": "#2ecc71",
    "asebytes H5MD": "#1abc9c",
    "aselmdb":       "#3498db",
    "znh5md":        "#e74c3c",
    "extxyz":        "#f39c12",
    "sqlite":        "#9b59b6",
}
```

## Usage

```bash
# Download lemat data (once)
uv run python scripts/download_benchmark_data.py

# Run benchmarks
uv run pytest -m benchmark --benchmark-only --benchmark-json=benchmark_results.json

# Generate figures
uv run python docs/visualize_benchmarks.py benchmark_results.json
```

## Changes

### `tests/conftest.py`

- Modify `ethanol` fixture: attach `SinglePointCalculator` with energy,
  forces, stress to each frame.
- Add `lemat` fixture: `scope="session"`, loads from
  `tests/data/lemat_1000.lmdb`, skips if missing.

### `tests/test_benchmark_write.py` — rewrite

Drop: lmdb+pickle, plain xyz. Add: asebytes H5MD, extxyz. Parametrize
over `ethanol` and `lemat` datasets.

### `tests/test_benchmark_read.py` — rewrite

Same backend changes as write. Parametrize over datasets.

### `tests/test_benchmark_random_access.py` — rewrite

Same backend changes. Skip extxyz. Parametrize over datasets.

### `tests/test_benchmark_column_access.py` — new

Column access for 5 backends with dataset-specific column reads.

### `tests/test_benchmark_file_size.py` — new

Write each backend, measure file size, report as benchmark extra info.

### `tests/test_benchmark_backend.py` — keep as-is

Internal asebytes regression comparison (BytesIO+encode vs backend path,
column views, view materialization). Different concern.

### `scripts/download_benchmark_data.py` — new

Downloads first 1000 frames of LeMat-Traj compatible_pbe via ASEIO and
saves to `tests/data/lemat_1000.lmdb`.

### `docs/visualize_benchmarks.py` — rewrite

Produce one figure per operation from benchmark JSON. Support grouped bars
by dataset. Recognize all 6 backend names.
