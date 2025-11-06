# Benchmarking

```bash
uv run pytest -m benchmark --benchmark-only --benchmark-json=benchmark_results.json
uv run docs/visualize_benchmarks.py benchmark_results.json
```
