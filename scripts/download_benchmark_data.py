"""Download LeMat-Traj benchmark data from HuggingFace.

Downloads the first 1000 frames from LeMaterial/LeMat-Traj compatible_pbe
and saves them to tests/data/lemat_1000.lmdb for use in benchmarks.

Usage:
    uv run python scripts/download_benchmark_data.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from asebytes import ASEIO  # noqa: E402


def main() -> None:
    out_path = ROOT / "tests" / "data" / "lemat_1000.lmdb"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.exists():
        print(f"Already exists: {out_path}")
        db = ASEIO(str(out_path), readonly=True)
        print(f"  {len(db)} frames")
        return

    print("Downloading LeMat-Traj compatible_pbe (first 1000 frames)...")
    src = ASEIO(
        "optimade://LeMaterial/LeMat-Traj",
        split="train",
        name="compatible_pbe",
        streaming=True,
    )

    frames = []
    for i, atoms in enumerate(src):
        frames.append(atoms)
        if (i + 1) % 100 == 0:
            print(f"  {i + 1} frames downloaded")
        if i + 1 >= 1000:
            break

    print(f"Writing {len(frames)} frames to {out_path}...")
    db = ASEIO(str(out_path))
    db.extend(frames)
    print("Done.")


if __name__ == "__main__":
    main()
