"""Plot suffix array order and LCP values.

Run from the project root:
    python -m visualization.plot_suffix_array
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt

from core.suffix_array import build_lcp, build_suffix_array


def plot_suffix_array(text: str, out_path: str | Path) -> None:
    sa = build_suffix_array(text)
    lcp = build_lcp(text, sa)
    fig, axes = plt.subplots(2, 1, figsize=(8, 6))
    axes[0].bar(range(len(sa)), sa, color="#2c5f8a")
    axes[0].set_title("Suffix array starting positions")
    axes[0].set_xlabel("Rank")
    axes[0].set_ylabel("Start index")
    if lcp:
        axes[1].bar(range(len(lcp)), lcp, color="#c47b2b")
    axes[1].set_title("LCP of adjacent suffixes")
    axes[1].set_xlabel("Rank")
    axes[1].set_ylabel("LCP length")
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


if __name__ == "__main__":
    sample = "BANANA" * 20
    out = Path(__file__).resolve().parents[1] / "benchmarks" / "results" / "suffix_array_sample.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    plot_suffix_array(sample, out)
    print(f"Wrote {out}")
