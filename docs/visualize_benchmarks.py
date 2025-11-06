"""Visualize pytest-benchmark results for ASE Atoms read/write performance.

This script parses the JSON output from pytest-benchmark and creates
publication-quality figures comparing different backend implementations.

Usage:
    # Run benchmarks and save results
    uv run pytest -m benchmark --benchmark-only --benchmark-json=benchmark_results.json

    # Generate figures
    uv run python docs/visualize_benchmarks.py benchmark_results.json
"""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def load_benchmark_results(json_path: str) -> dict:
    """Load benchmark results from JSON file."""
    with open(json_path) as f:
        return json.load(f)


def parse_benchmarks(data: dict) -> dict:
    """Parse benchmark data into organized structure."""
    results = {"read": {}, "write": {}}

    for benchmark in data["benchmarks"]:
        name = benchmark["name"]
        stats = benchmark["stats"]

        # Extract backend type and operation
        if "read" in name:
            operation = "read"
        elif "write" in name:
            operation = "write"
        else:
            continue

        if "asebytes" in name:
            backend = "ASEIO"
        elif "aselmdb" in name:
            backend = "ASE LMDB"
        elif "lmdb_pickle" in name:
            backend = "LMDB+Pickle"
        elif "xyz" in name:
            backend = "XYZ"
        elif "sqlite" in name:
            backend = "SQLite"
        else:
            continue

        results[operation][backend] = {
            "mean": stats["mean"],
            "stddev": stats["stddev"],
            "min": stats["min"],
            "max": stats["max"],
            "median": stats["median"],
            "rounds": stats["rounds"],
        }

    return results


def create_comparison_figure(results: dict, output_path: str = "benchmark_comparison.png", use_log_scale: bool = True):
    """Create a comprehensive comparison figure.

    Args:
        results: Parsed benchmark results
        output_path: Path to save the figure
        use_log_scale: If True, use log scale for y-axis (better for wide range of values)
    """
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle("ASE Atoms Storage Backend Performance Comparison\n1000 Ethanol Molecules",
                 fontsize=14, fontweight="bold")

    # Define colors for each backend
    colors = {
        "ASEIO": "#2ecc71",
        "ASE LMDB": "#3498db",
        "LMDB+Pickle": "#e74c3c",
        "XYZ": "#f39c12",
        "SQLite": "#9b59b6"
    }

    # 1. Write Performance (left)
    ax = axes[0]
    write_data = results["write"]
    backends = list(write_data.keys())
    means = [write_data[b]["mean"] for b in backends]
    stds = [write_data[b]["stddev"] for b in backends]

    x = np.arange(len(backends))
    bars = ax.bar(x, means, yerr=stds, capsize=5, alpha=0.8,
                  color=[colors[b] for b in backends])

    ax.set_ylabel("Time / s", fontweight="bold")
    ax.set_title("Write Performance", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(backends, rotation=15, ha="right")
    ax.grid(axis="y", alpha=0.3)

    if use_log_scale:
        ax.set_yscale("log")
        # Add value labels on bars for log scale
        for i, mean in enumerate(means):
            ax.text(i, mean, f"{mean:.3f}s",
                    ha="center", va="bottom", fontsize=9)
    else:
        # Add value labels on bars
        for i, (mean, std) in enumerate(zip(means, stds)):
            ax.text(i, mean + std, f"{mean:.3f}s",
                    ha="center", va="bottom", fontsize=9)

    # 2. Read Performance (center)
    ax = axes[1]
    read_data = results["read"]
    backends = list(read_data.keys())
    means = [read_data[b]["mean"] for b in backends]
    stds = [read_data[b]["stddev"] for b in backends]

    x = np.arange(len(backends))
    bars = ax.bar(x, means, yerr=stds, capsize=5, alpha=0.8,
                  color=[colors[b] for b in backends])

    ax.set_ylabel("Time / s", fontweight="bold")
    ax.set_title("Read Performance", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(backends, rotation=15, ha="right")
    ax.grid(axis="y", alpha=0.3)

    if use_log_scale:
        ax.set_yscale("log")
        # Add value labels on bars for log scale
        for i, mean in enumerate(means):
            ax.text(i, mean, f"{mean:.3f}s",
                    ha="center", va="bottom", fontsize=9)
    else:
        # Add value labels on bars
        for i, (mean, std) in enumerate(zip(means, stds)):
            ax.text(i, mean + std, f"{mean:.3f}s",
                    ha="center", va="bottom", fontsize=9)

    # 3. Per-molecule Time (right)
    ax = axes[2]

    num_molecules = 1000
    write_backends = list(write_data.keys())
    write_per_mol = [write_data[b]["mean"] / num_molecules * 1000 for b in write_backends]  # ms
    read_per_mol = [read_data[b]["mean"] / num_molecules * 1000 for b in write_backends]  # ms

    x = np.arange(len(write_backends))
    width = 0.35

    # Use distinct colors that don't overlap with backend colors
    # Teal for write, coral for read - both visually distinct
    ax.bar(x - width/2, write_per_mol, width, label="Write", alpha=0.8, color="#00CED1")
    ax.bar(x + width/2, read_per_mol, width, label="Read", alpha=0.8, color="#FF7F50")

    ax.set_ylabel("Time / ms", fontweight="bold")
    ax.set_title("Time per Molecule", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(write_backends, rotation=15, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    if use_log_scale:
        ax.set_yscale("log")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    scale_note = " (log scale)" if use_log_scale else ""
    print(f"Figure saved to: {output_path}{scale_note}")
    plt.close()


def create_detailed_stats_table(results: dict):
    """Print detailed statistics table."""
    print("\n" + "="*100)
    print("DETAILED BENCHMARK STATISTICS")
    print("="*100)

    for operation in ["write", "read"]:
        print(f"\n{operation.upper()} PERFORMANCE:")
        print("-" * 100)
        print(f"{'Backend':<20} {'Mean (s)':<12} {'StdDev (s)':<12} {'Min (s)':<12} "
              f"{'Max (s)':<12} {'Rounds':<10}")
        print("-" * 100)

        for backend, stats in results[operation].items():
            print(f"{backend:<20} {stats['mean']:<12.4f} {stats['stddev']:<12.4f} "
                  f"{stats['min']:<12.4f} {stats['max']:<12.4f} {stats['rounds']:<10}")

    print("\n" + "="*100)
    print("SPEEDUP ANALYSIS (Relative to ASEIO)")
    print("="*100)

    if "ASEIO" in results["write"] and "ASEIO" in results["read"]:
        aseio_write = results["write"]["ASEIO"]["mean"]
        aseio_read = results["read"]["ASEIO"]["mean"]

        print(f"{'Backend':<20} {'Write Speedup':<20} {'Read Speedup':<20}")
        print("-" * 60)

        for backend in results["write"].keys():
            if backend != "ASEIO":
                write_speedup = results["write"][backend]["mean"] / aseio_write
                read_speedup = results["read"][backend]["mean"] / aseio_read

                write_str = f"{write_speedup:.2f}x {'(slower)' if write_speedup > 1 else '(faster)'}"
                read_str = f"{read_speedup:.2f}x {'(slower)' if read_speedup > 1 else '(faster)'}"

                print(f"{backend:<20} {write_str:<20} {read_str:<20}")

    print("="*100 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Visualize pytest-benchmark results for ASE storage backends"
    )
    parser.add_argument(
        "benchmark_json",
        type=str,
        help="Path to benchmark results JSON file"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="benchmark_comparison.png",
        help="Output figure path (default: benchmark_comparison.png)"
    )
    parser.add_argument(
        "--linear",
        action="store_true",
        help="Use linear scale instead of log scale (default: log scale)"
    )
    parser.add_argument(
        "--split-view",
        action="store_true",
        help="Create separate panels for fast and slow backends"
    )

    args = parser.parse_args()

    # Check if input file exists
    if not Path(args.benchmark_json).exists():
        print(f"Error: Benchmark file '{args.benchmark_json}' not found!")
        print("\nPlease run benchmarks first:")
        print("  uv run pytest -m benchmark --benchmark-only --benchmark-json=benchmark_results.json")
        return 1

    # Load and parse results
    print(f"Loading benchmark results from: {args.benchmark_json}")
    data = load_benchmark_results(args.benchmark_json)
    results = parse_benchmarks(data)

    # Create visualizations
    print("Creating visualization...")
    use_log = not args.linear

    if args.split_view:
        print("Split view not yet implemented - using standard view with log scale")
        use_log = True

    create_comparison_figure(results, args.output, use_log_scale=use_log)

    # Print statistics
    create_detailed_stats_table(results)

    print("\nAnalysis complete!")
    return 0


if __name__ == "__main__":
    exit(main())
