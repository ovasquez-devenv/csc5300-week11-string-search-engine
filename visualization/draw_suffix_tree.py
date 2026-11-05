"""Draw a compressed suffix tree as a simple edge list figure.

Run from the project root:
    python -m visualization.draw_suffix_tree
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt

from core.suffix_tree import SuffixTree


def draw_suffix_tree(text: str, out_path: str | Path) -> None:
    tree = SuffixTree(text)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_title(f"Suffix tree edges for text of length {len(text)}")
    ax.axis("off")
    y = 1.0

    def walk(node, depth: int) -> None:
        nonlocal y
        edge = tree.text[node.start : node.end] if node.start >= 0 else "root"
        ax.text(0.05 + depth * 0.12, y, edge, fontsize=9)
        y -= 0.06
        for child in node.children.values():
            walk(child, depth + 1)

    walk(tree.root, 0)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "benchmarks" / "results" / "suffix_tree_sample.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    draw_suffix_tree("BANANA", out)
    print(f"Wrote {out}")
