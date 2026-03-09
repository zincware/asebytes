"""Visualize pytest-benchmark results for ASE Atoms storage backends.

Produces one PNG per operation from pytest-benchmark JSON output.

Usage:
    uv run pytest tests/benchmarks/ -m benchmark --benchmark-only --benchmark-json=benchmark_results.json
    uv run python docs/visualize_benchmarks.py benchmark_results.json
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Backend display names and colors
BACKEND_NAMES = {
    "asebytes_lmdb": "asebytes LMDB",
    "asebytes_zarr": "asebytes Zarr",
    "asebytes_h5md": "asebytes H5MD",
    "asebytes_redis": "asebytes Redis",
    "asebytes_mongodb": "asebytes MongoDB",
    "aselmdb": "aselmdb",
    "znh5md": "znh5md",
    "extxyz": "extxyz",
    "sqlite": "sqlite",
}

COLORS = {
    "asebytes LMDB": "#2ecc71",
    "asebytes Zarr": "#27ae60",
    "asebytes H5MD": "#1abc9c",
    "asebytes Redis": "#e74c3c",
    "asebytes MongoDB": "#3498db",
    "aselmdb": "#8e44ad",
    "znh5md": "#d35400",
    "extxyz": "#f39c12",
    "sqlite": "#9b59b6",
}

# Order backends appear in charts
BACKEND_ORDER = [
    "asebytes LMDB",
    "asebytes Zarr",
    "asebytes H5MD",
    "asebytes Redis",
    "asebytes MongoDB",
    "aselmdb",
    "znh5md",
    "extxyz",
    "sqlite",
]

OPERATIONS = {
    "write_trajectory": "Write Trajectory (bulk)",
    "write_single": "Write Single (per-row)",
    "read_trajectory": "Read Trajectory (bulk)",
    "read_single": "Read Single (per-row)",
    "random_trajectory": "Random Access Trajectory (bulk)",
    "random_single": "Random Access Single (per-row)",
    "read_positions_trajectory": "Read Positions Trajectory (bulk)",
    "read_positions_single": "Read Positions Single (per-row)",
    "column_energy": "Column Energy Access",
    "update_property_trajectory": "Update Property Trajectory",
}

# Operations sorted by prefix for matching (longest first to avoid ambiguity)
_OP_PREFIXES = sorted(OPERATIONS.keys(), key=len, reverse=True)


def _parse_test_name(name: str) -> tuple[str, str, str] | None:
    """Extract (operation, backend_key, dataset) from a test name.

    Expected patterns:
        test_write_trajectory_asebytes_lmdb[ethanol]
        test_read_single_sqlite[lemat]
        test_random_trajectory_aselmdb[ethanol]
        test_column_energy_asebytes_h5md[lemat]
        test_update_property_trajectory_asebytes_redis[ethanol]
    """
    # Extract dataset from brackets
    m = re.search(r"\[(\w+)\]$", name)
    if not m:
        return None
    dataset = m.group(1)

    # Strip test_ prefix and [dataset] suffix
    core = name.removeprefix("test_").removesuffix(f"[{dataset}]")

    # Match operation prefix (longest first)
    for op in _OP_PREFIXES:
        prefix = f"{op}_"
        if core.startswith(prefix):
            backend_key = core[len(prefix):]
            if backend_key in BACKEND_NAMES:
                return op, backend_key, dataset

    return None


def parse_benchmarks(data: dict) -> dict:
    """Parse benchmark JSON into {operation: {dataset: {backend: stats}}}."""
    results: dict[str, dict[str, dict[str, dict]]] = defaultdict(
        lambda: defaultdict(dict)
    )

    for bench in data["benchmarks"]:
        parsed = _parse_test_name(bench["name"])
        if parsed is None:
            continue
        op, backend_key, dataset = parsed
        backend_name = BACKEND_NAMES[backend_key]
        stats = bench["stats"]
        entry = {
            "mean": stats["mean"],
            "stddev": stats["stddev"],
            "min": stats["min"],
            "max": stats["max"],
        }
        results[op][dataset][backend_name] = entry

    return dict(results)


def _make_grouped_bar_chart(
    ax,
    data: dict[str, dict[str, dict]],
    title: str,
    ylabel: str,
    value_key: str = "mean",
    error_key: str | None = "stddev",
    log_scale: bool = True,
    format_fn=None,
):
    """Draw grouped bars (one group per dataset, one bar per backend)."""
    datasets = sorted(data.keys())
    # Collect backends present in any dataset, in standard order
    all_backends = []
    for ds in datasets:
        for b in data[ds]:
            if b not in all_backends:
                all_backends.append(b)
    backends = [b for b in BACKEND_ORDER if b in all_backends]

    n_datasets = len(datasets)
    n_backends = len(backends)
    x = np.arange(n_backends)
    width = 0.8 / n_datasets
    offsets = np.linspace(
        -(n_datasets - 1) * width / 2,
        (n_datasets - 1) * width / 2,
        n_datasets,
    )

    # First dataset: solid fill. Second dataset: hatched overlay.
    hatches = ["", "//"]

    for i, ds in enumerate(datasets):
        vals = [data[ds].get(b, {}).get(value_key, 0) for b in backends]
        errs = (
            [data[ds].get(b, {}).get(error_key, 0) for b in backends]
            if error_key
            else None
        )
        colors = [COLORS.get(b, "#999999") for b in backends]
        ax.bar(
            x + offsets[i],
            vals,
            width,
            yerr=errs,
            capsize=3,
            alpha=0.85,
            color=colors,
            hatch=hatches[i % len(hatches)],
            edgecolor="white" if i > 0 else "none",
            linewidth=0.5,
            label=ds,
        )
        # Value labels
        fmt = format_fn or (lambda v: f"{v:.3f}s")
        for j, v in enumerate(vals):
            if v > 0:
                ax.text(
                    x[j] + offsets[i],
                    v,
                    fmt(v),
                    ha="center",
                    va="bottom",
                    fontsize=7,
                    rotation=45,
                )

    ax.set_title(title, fontweight="bold")
    ax.set_ylabel(ylabel, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(backends, rotation=20, ha="right", fontsize=9)
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    if log_scale:
        ax.set_yscale("log")


def create_figures(results: dict, output_dir: str = ".") -> list[str]:
    """Create one figure per operation. Returns list of output paths."""
    out = Path(output_dir)
    paths = []

    for op, title in OPERATIONS.items():
        if op not in results:
            continue

        fig, ax = plt.subplots(figsize=(10, 5))
        _make_grouped_bar_chart(
            ax,
            results[op],
            title,
            ylabel="Time / s",
        )

        fig.tight_layout()
        path = out / f"benchmark_{op}.png"
        fig.savefig(str(path), dpi=300, bbox_inches="tight")
        plt.close(fig)
        paths.append(str(path))
        print(f"  {path}")

    return paths


def print_stats(results: dict) -> None:
    """Print summary statistics table."""
    for op, datasets in results.items():
        print(f"\n{'=' * 80}")
        print(f"  {OPERATIONS.get(op, op).upper()}")
        print(f"{'=' * 80}")
        for ds, backends in sorted(datasets.items()):
            print(f"\n  Dataset: {ds}")
            print(f"  {'Backend':<20} {'Mean':>10} {'StdDev':>10}")
            print(f"  {'-' * 40}")
            for b in BACKEND_ORDER:
                if b not in backends:
                    continue
                s = backends[b]
                print(
                    f"  {b:<20} {s['mean']:>9.4f}s {s['stddev']:>9.4f}s"
                )


def main():
    parser = argparse.ArgumentParser(
        description="Visualize benchmark results (one figure per operation)"
    )
    parser.add_argument("benchmark_json", help="Path to benchmark JSON file")
    parser.add_argument(
        "-o",
        "--output-dir",
        default=str(Path(__file__).resolve().parent),
        help="Directory for output PNGs (default: docs/)",
    )
    args = parser.parse_args()

    path = Path(args.benchmark_json)
    if not path.exists():
        print(f"Error: {path} not found.")
        print("Run benchmarks first:")
        print(
            "  uv run pytest tests/benchmarks/ -m benchmark --benchmark-only "
            "--benchmark-json=benchmark_results.json"
        )
        return 1

    print(f"Loading: {path}")
    with open(path) as f:
        data = json.load(f)

    results = parse_benchmarks(data)
    print(f"Found operations: {list(results.keys())}")

    print("\nCreating figures:")
    create_figures(results, args.output_dir)

    print_stats(results)
    print("\nDone.")
    return 0


if __name__ == "__main__":
    exit(main())
