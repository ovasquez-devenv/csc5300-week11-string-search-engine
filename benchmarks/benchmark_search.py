"""Compare KMP, Rabin Karp, suffix array, and suffix tree.

Writes CSV rows and four PNG charts. Uses a fixed seed.
Numbers in the report must come from a run on Omar's machine.

Run from the project root:
    python -m benchmarks.benchmark_search
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import csv
import statistics
import time

import matplotlib.pyplot as plt

from core.kmp import kmp_search
from core.rabin_karp import RabinKarp
from core.suffix_array import binary_search, build_lcp, build_suffix_array
from core.suffix_tree import SuffixTree
from utils.generators import englishish, random_text

SEED = 5300
RESULTS = Path(__file__).resolve().parent / "results"


def _time_call(fn, repeats: int = 3) -> tuple[float, float]:
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        samples.append(time.perf_counter() - start)
    return statistics.mean(samples), statistics.pstdev(samples)


def run() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    sizes = {"small": 10_000, "medium": 1_000_000}
    rows = []
    runtime = {}
    for label, size in sizes.items():
        text = englishish(size, seed=SEED)
        pattern = "search"
        methods = {
            "kmp": lambda: kmp_search(text, pattern),
            "rk": lambda: RabinKarp().search(text, pattern),
            "sa": lambda: binary_search(text, build_suffix_array(text), pattern),
        }
        if size <= 50_000:
            methods["tree"] = lambda: SuffixTree(text).find_substring(pattern)
        runtime[label] = {}
        for name, fn in methods.items():
            mean, std = _time_call(fn)
            runtime[label][name] = mean
            rows.append(
                {
                    "dataset": label,
                    "size": size,
                    "method": name,
                    "mean_seconds": f"{mean:.6f}",
                    "std_seconds": f"{std:.6f}",
                    "seed": SEED,
                }
            )
    csv_path = RESULTS / "runtime.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    fig, ax = plt.subplots()
    labels = list(runtime["small"].keys())
    ax.bar(labels, [runtime["small"][k] for k in labels], color="#2c5f8a")
    ax.set_title("Search time on 10 KB text (seed 5300)")
    ax.set_ylabel("Mean seconds")
    fig.tight_layout()
    fig.savefig(RESULTS / "runtime_comparison.png")
    plt.close(fig)

    text = random_text(20_000, seed=SEED)
    pattern = text[100:108]
    moduli = [101, 1009, 10007, 100003]
    rates = []
    for mod in moduli:
        rk = RabinKarp(modulus=mod)
        rk.search(text, pattern)
        rate = rk.collisions / max(1, rk.hash_hits)
        rates.append(rate)
    fig, ax = plt.subplots()
    ax.bar([str(m) for m in moduli], rates, color="#c47b2b")
    ax.set_title("Rabin Karp collision rate by modulus (seed 5300)")
    ax.set_ylabel("Collisions / hash hits")
    fig.tight_layout()
    fig.savefig(RESULTS / "collision_analysis.png")
    plt.close(fig)

    sample = englishish(2_000, seed=SEED)
    sa = build_suffix_array(sample)
    lcp = build_lcp(sample, sa)
    fig, ax = plt.subplots()
    ax.plot(lcp, color="#2c5f8a")
    ax.set_title("LCP array on 2,000 character sample (seed 5300)")
    ax.set_xlabel("Adjacent suffix rank")
    ax.set_ylabel("LCP length")
    fig.tight_layout()
    fig.savefig(RESULTS / "sa_lcp_stats.png")
    plt.close(fig)

    fig, ax = plt.subplots()
    methods_h = ["kmp", "rk", "sa"]
    data = [[runtime[ds].get(m, 0.0) for m in methods_h] for ds in ("small", "medium")]
    im = ax.imshow(data, aspect="auto", cmap="Blues")
    ax.set_xticks(range(len(methods_h)), methods_h)
    ax.set_yticks(range(2), ["10 KB", "1 MB"])
    ax.set_title("Mean search time heatmap (seed 5300)")
    fig.colorbar(im, ax=ax, label="seconds")
    fig.tight_layout()
    fig.savefig(RESULTS / "heatmap_dataset_sizes.png")
    plt.close(fig)
    print(f"Wrote {csv_path}")


if __name__ == "__main__":
    run()
