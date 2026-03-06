# Technology Stack

**Analysis Date:** 2026-03-06

## Languages

**Primary:**
- Python >=3.11 - All source code, tests, scripts

**Secondary:**
- Lua - Redis server-side scripts (`src/asebytes/redis/_lua.py`)

## Runtime

**Environment:**
- CPython 3.11 (pinned in `.python-version`)
- CI tests against 3.11, 3.12, 3.13

**Package Manager:**
- uv (astral-sh/setup-uv@v5 in CI)
- Lockfile: `uv.lock` present (version 1, revision 3)

**Build System:**
- `uv_build>=0.9.6,<0.10.0` (declared in `[build-system]`)

## Frameworks

**Core:**
- ASE (Atomic Simulation Environment) >=3.26.0 - Domain framework for atomic structures (`ase.Atoms`)

**Testing:**
- pytest >=8.4.2 - Test runner, config in `pyproject.toml` `[tool.pytest.ini_options]`
- pytest-benchmark >=5.2.1 - Performance benchmarking (guarded by `benchmark` marker)

**Build/Dev:**
- uv - Package management, virtual env, build
- ipykernel >=7.1.0 - Jupyter notebook support (dev only)
- matplotlib >=3.10.7 - Benchmark visualization (dev only)

## Key Dependencies

**Critical (required):**
- `ase>=3.26.0` - Core domain: Atoms objects for atomic structures
- `msgpack>=1.1.2` - Binary serialization format for Atoms data
- `msgpack-numpy>=0.4.8` - numpy array serialization via msgpack
- `typing_extensions>=4.5.0` - Backported typing features

**Optional extras (storage backends):**
- `lmdb>=1.7.5` - Extra `[lmdb]`: embedded key-value store backend
- `h5py>=3.8.0` - Extra `[h5md]`: HDF5 file format backend
- `zarr>=3.0` - Extra `[zarr]`: Zarr v3 columnar storage backend
- `pymongo>=4.13` - Extra `[mongodb]`: MongoDB document store backend
- `redis>=5.0` - Extra `[redis]`: Redis key-value store backend
- `datasets>=4.5.0` - Extra `[hf]`: HuggingFace datasets read-only backend

**Dev-only:**
- `znh5md>=0.4.8` - H5MD format utilities
- `molify>=0.0.1a0` - Molecule generation for test data
- `pandas>=2.3.3` - Data analysis
- `ase-db-backends>=0.10.0` - ASE database backend utilities
- `anyio>=4.0` - Async test support

## Configuration

**Environment:**
- No `.env` files detected
- Backend connections configured via constructor args (URIs, paths)
- MongoDB default URI: `mongodb://localhost:27017`
- Redis default URI: `redis://localhost:6379`

**Build:**
- `pyproject.toml` - Single source of truth for project metadata, dependencies, build config, test config
- `.python-version` - Pins Python 3.11

**Test:**
- Test paths: `tests/`
- Default addopts: `-v --strict-markers -m "not benchmark"`
- Custom markers: `benchmark` (deselected by default)

## Platform Requirements

**Development:**
- Python 3.11+
- uv package manager
- Optional: MongoDB 7+ and Redis 7+ for full backend testing (provided as Docker services in CI)

**Production:**
- Python 3.11+ runtime
- Storage backend dependencies installed per use case (extras)
- No web server or deployment platform required (library package)

---

*Stack analysis: 2026-03-06*
