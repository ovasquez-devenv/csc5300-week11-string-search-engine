"""Compare KMP, Rabin Karp, a suffix array, and a compressed suffix trie.

The script writes separate preprocessing time, search latency, tracemalloc
peak memory, and Rabin Karp collision rates. Timing repeats run with
tracemalloc stopped. Memory repeats are a later pass. The historical
combined timer file benchmarks/results/runtime.csv is never written.

Seeded text uses random.Random(seed). Means and population standard
deviations use statistics.mean and statistics.pstdev, which is the same
spread function the earlier runtime.csv used.

From the project root on Windows, with Python 3.14:

    py -3.14 -m benchmarks.benchmark_search

That command uses seed 5300, a 10,000 character text, a 1,000,000 character
text, and 3 repeats. All four methods, including the Ukkonen trie, run at
both lengths. If the output folder already holds measurement files, the run
stops instead of replacing them or nesting another folder. The finished PC
run is benchmarks/results/final_run.
"""

from __future__ import annotations

import argparse
import csv
import gc
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from core.kmp import compute_failure_function
from core.rabin_karp import RabinKarp
from core.suffix_array import BUILD_ID as SA_BUILD_ID
from core.suffix_array import binary_search, build_lcp, build_suffix_array
from core.suffix_tree import SuffixTree
from utils.generators import englishish, random_text

SEED = 5300
DEFAULT_SEED = SEED
DEFAULT_REPEATS = 3
DEFAULT_SMALL = 10_000
DEFAULT_MEDIUM = 1_000_000
DEFAULT_TREE_MAX_CHARS = 1_000_000
DEFAULT_TEXT_MAX_CHARS = 1_000_000
DEFAULT_PATTERN = "search"
DEFAULT_MODULUS = 1_000_000_007
DEFAULT_COLLISION_TEXT_SIZE = 20_000
DEFAULT_LCP_SAMPLE_SIZE = 2_000
COLLISION_MODULI = (101, 1009, 10007, 100003)
RESULTS = Path(__file__).resolve().parent / "results"
METHODS = ("kmp", "rk", "sa", "tree")
CHART_FILES = (
    "runtime_comparison.png",
    "collision_analysis.png",
    "sa_lcp_stats.png",
    "heatmap_dataset_sizes.png",
)
PROTECTED_RESULTS = (
    "runtime.csv",
    "metrics.csv",
    "collision_rates.csv",
    *CHART_FILES,
)

METRIC_FIELDS = [
    "dataset",
    "size",
    "method",
    "pattern",
    "seed",
    "repeats",
    "preprocess_mean_seconds",
    "preprocess_std_seconds",
    "search_mean_seconds",
    "search_std_seconds",
    "preprocess_tracemalloc_peak_mean_bytes",
    "preprocess_tracemalloc_peak_std_bytes",
    "search_tracemalloc_peak_mean_bytes",
    "search_tracemalloc_peak_std_bytes",
    "rk_modulus",
    "rk_hash_hits_mean",
    "rk_collisions_mean",
    "rk_collision_rate_mean",
    "rk_collision_rate_std",
    "status",
    "note",
]

COLLISION_FIELDS = [
    "modulus",
    "text_size",
    "pattern",
    "seed",
    "repeats",
    "hash_hits_mean",
    "collisions_mean",
    "collision_rate_mean",
    "collision_rate_std",
]


def mean_std(samples: list[float]) -> tuple[float, float]:
    """Return the mean and the population standard deviation.

    statistics.pstdev divides by the number of samples. The earlier
    runtime.csv used this same function.
    """
    if not samples:
        raise ValueError("need at least one sample")
    return statistics.mean(samples), statistics.pstdev(samples)


def prepare(method: str, text: str, pattern: str, modulus: int = DEFAULT_MODULUS):
    """Build only the structure used by a later search."""
    if method == "kmp":
        return compute_failure_function(pattern)
    if method == "rk":
        matcher = RabinKarp(modulus=modulus)
        target = matcher.hasher.hash_string(pattern) if pattern else 0
        power = matcher.hasher.window_power(len(pattern))
        return matcher, target, power
    if method == "sa":
        return build_suffix_array(text)
    if method == "tree":
        return SuffixTree(text)
    raise ValueError(f"Unknown method: {method}")


def query(method: str, text: str, pattern: str, state):
    """Run the lookup on a structure that already exists."""
    if method == "kmp":
        return _kmp_search(text, pattern, state)
    if method == "rk":
        return _rk_search(text, pattern, state)
    if method == "sa":
        return binary_search(text, state, pattern)
    if method == "tree":
        return state.find_positions(pattern)
    raise ValueError(f"Unknown method: {method}")


def _kmp_search(text: str, pattern: str, failure: list[int]) -> list[int]:
    """Scan text with a failure table that was built ahead of this call."""
    n = len(text)
    m = len(pattern)
    if m == 0 or m > n:
        return []
    positions: list[int] = []
    i = 0
    j = 0
    while i < n:
        if pattern[j] == text[i]:
            i += 1
            j += 1
            if j == m:
                positions.append(i - j)
                j = failure[j - 1]
        else:
            if j != 0:
                j = failure[j - 1]
            else:
                i += 1
    return positions


def _rk_search(text: str, pattern: str, state) -> list[int]:
    """Slide the window. The pattern hash and window power are already known."""
    matcher, target, power = state
    n = len(text)
    m = len(pattern)
    matcher.collisions = 0
    matcher.hash_hits = 0
    if m == 0 or m > n:
        return []
    window = matcher.hasher.hash_string(text[:m])
    positions: list[int] = []
    if window == target:
        matcher.hash_hits += 1
        if text[:m] == pattern:
            positions.append(0)
        else:
            matcher.collisions += 1
    for i in range(1, n - m + 1):
        window = matcher.hasher.roll(window, text[i - 1], text[i + m - 1], power)
        if window == target:
            matcher.hash_hits += 1
            if text[i : i + m] == pattern:
                positions.append(i)
            else:
                matcher.collisions += 1
    return positions


def method_character_limit(
    method: str, *, tree_max_chars: int, text_max_chars: int
) -> int:
    """Largest text length this method will measure.

    The Ukkonen trie is allowed through the default medium size. A longer
    text, including the optional 100 MB size, is skipped unless the limit is
    raised. KMP, Rabin Karp, and the suffix array share the text limit.
    """
    if method == "tree":
        return tree_max_chars
    if method in ("kmp", "rk", "sa"):
        return text_max_chars
    raise ValueError(f"Unknown method: {method}")


def _elapsed(fn) -> float:
    """Time fn without counting CPython's free of its return value.

    The temporary result of a bare call is destroyed before the next line.
    For a suffix array or a trie that free is part of teardown, not the build,
    so the result stays bound until the clock has stopped.
    """
    if tracemalloc.is_tracing():
        raise RuntimeError("timers run with tracemalloc stopped")
    start = time.perf_counter()
    result = fn()
    elapsed = time.perf_counter() - start
    del result
    return elapsed


def time_prepare(method: str, text: str, pattern: str, repeats: int) -> tuple[float, float]:
    samples = [_elapsed(lambda: prepare(method, text, pattern)) for _ in range(repeats)]
    return mean_std(samples)


def time_search(method: str, text: str, pattern: str, repeats: int) -> tuple[float, float]:
    state = prepare(method, text, pattern)
    samples = [_elapsed(lambda: query(method, text, pattern, state)) for _ in range(repeats)]
    return mean_std(samples)


def peak_allocated_bytes(fn) -> int:
    """Peak bytes Python allocated during fn, as reported by tracemalloc.

    gc.collect() runs before tracing starts so leftover objects from the
    timing pass are not part of this peak. The peak is the high water mark
    of traced allocations for this call. It is not the process size shown
    by the operating system.
    """
    gc.collect()
    tracemalloc.start()
    try:
        fn()
        _current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return peak


def memory_peaks(fn, repeats: int) -> tuple[float, float]:
    samples = [float(peak_allocated_bytes(fn)) for _ in range(repeats)]
    return mean_std(samples)


def collision_stats(text: str, pattern: str, modulus: int, repeats: int) -> dict[str, float]:
    """Count Rabin Karp collisions with the library search, outside the timers."""
    hits: list[float] = []
    collisions: list[float] = []
    rates: list[float] = []
    for _ in range(repeats):
        if tracemalloc.is_tracing():
            raise RuntimeError("collision counts run with tracemalloc stopped")
        matcher = RabinKarp(modulus=modulus)
        matcher.search(text, pattern)
        hits.append(float(matcher.hash_hits))
        collisions.append(float(matcher.collisions))
        if matcher.hash_hits == 0:
            rates.append(0.0)
        else:
            rates.append(matcher.collisions / matcher.hash_hits)
    hit_mean, _hit_std = mean_std(hits)
    collision_mean, _collision_std = mean_std(collisions)
    rate_mean, rate_std = mean_std(rates)
    return {
        "hash_hits_mean": hit_mean,
        "collisions_mean": collision_mean,
        "collision_rate_mean": rate_mean,
        "collision_rate_std": rate_std,
    }


def _fmt_seconds(value: float) -> str:
    return f"{value:.9f}"


def _fmt_number(value: float) -> str:
    return f"{value:.3f}"


def _fmt_rate(value: float) -> str:
    return f"{value:.6f}"


def _method_note(method: str) -> str:
    if method == "sa":
        return (
            f"Preprocess times build_suffix_array ({SA_BUILD_ID}). "
            "Each doubling round is a linear radix sort, so the build is O(n log n). "
            "Search times binary_search on that array. "
            "The LCP array is built for the LCP chart. "
            "Not the comparison-sort rows in final_run/metrics.csv."
        )
    if method == "tree":
        return (
            f"Ukkonen compressed trie ({SuffixTree.BUILD_ID}). "
            "Search lists every starting position. "
            "This builder is not the earlier insertion trie in the saved metrics.csv."
        )
    if method == "kmp":
        return "Preprocess times the failure table. Search times the text scan."
    if method == "rk":
        return (
            "Preprocess times the pattern hash and window power. "
            "Search times the sliding window. "
            "Collision columns use RabinKarp.search on this same text and pattern."
        )
    return ""


def _skip_note(method: str, size: int, limit: int) -> str:
    labels = {
        "kmp": "KMP",
        "rk": "Rabin Karp",
        "sa": "suffix array",
        "tree": "compressed trie",
    }
    return (
        f"{labels[method]} skipped because the text length is {size} characters "
        f"and the limit for this method is {limit} characters."
    )


def _empty_metric_row(
    dataset: str,
    size: int,
    method: str,
    pattern: str,
    seed: int,
    repeats: int,
    status: str,
    note: str,
) -> dict[str, str]:
    row = {field: "" for field in METRIC_FIELDS}
    row["dataset"] = dataset
    row["size"] = str(size)
    row["method"] = method
    row["pattern"] = pattern
    row["seed"] = str(seed)
    row["repeats"] = str(repeats)
    row["status"] = status
    row["note"] = note
    return row


def measure_method(
    dataset: str,
    size: int,
    method: str,
    text: str,
    pattern: str,
    repeats: int,
    seed: int,
    tree_max_chars: int,
    text_max_chars: int,
) -> dict[str, str]:
    limit = method_character_limit(
        method, tree_max_chars=tree_max_chars, text_max_chars=text_max_chars
    )
    if size > limit:
        return _empty_metric_row(
            dataset,
            size,
            method,
            pattern,
            seed,
            repeats,
            "skipped",
            _skip_note(method, size, limit),
        )
    pre_mean, pre_std = time_prepare(method, text, pattern, repeats)
    search_mean, search_std = time_search(method, text, pattern, repeats)
    pre_mem_mean, pre_mem_std = memory_peaks(
        lambda: prepare(method, text, pattern), repeats
    )
    state = prepare(method, text, pattern)
    search_mem_mean, search_mem_std = memory_peaks(
        lambda: query(method, text, pattern, state), repeats
    )
    row = _empty_metric_row(
        dataset, size, method, pattern, seed, repeats, "ok", _method_note(method)
    )
    row["preprocess_mean_seconds"] = _fmt_seconds(pre_mean)
    row["preprocess_std_seconds"] = _fmt_seconds(pre_std)
    row["search_mean_seconds"] = _fmt_seconds(search_mean)
    row["search_std_seconds"] = _fmt_seconds(search_std)
    row["preprocess_tracemalloc_peak_mean_bytes"] = _fmt_number(pre_mem_mean)
    row["preprocess_tracemalloc_peak_std_bytes"] = _fmt_number(pre_mem_std)
    row["search_tracemalloc_peak_mean_bytes"] = _fmt_number(search_mem_mean)
    row["search_tracemalloc_peak_std_bytes"] = _fmt_number(search_mem_std)
    if method == "rk":
        stats = collision_stats(text, pattern, DEFAULT_MODULUS, repeats)
        row["rk_modulus"] = str(DEFAULT_MODULUS)
        row["rk_hash_hits_mean"] = _fmt_number(stats["hash_hits_mean"])
        row["rk_collisions_mean"] = _fmt_number(stats["collisions_mean"])
        row["rk_collision_rate_mean"] = _fmt_rate(stats["collision_rate_mean"])
        row["rk_collision_rate_std"] = _fmt_rate(stats["collision_rate_std"])
        if stats["hash_hits_mean"] == 0:
            row["note"] = row["note"] + " No hash hits, so the collision rate is recorded as 0."
    return row


def collision_pattern(text: str) -> str:
    if len(text) <= 8:
        return text
    start = min(100, len(text) - 8)
    return text[start : start + 8]


def measure_collision_table(
    text_size: int,
    seed: int,
    repeats: int,
    moduli: tuple[int, ...] = COLLISION_MODULI,
) -> list[dict[str, str]]:
    text = random_text(text_size, seed=seed)
    pattern = collision_pattern(text)
    rows = []
    for modulus in moduli:
        stats = collision_stats(text, pattern, modulus, repeats)
        rows.append(
            {
                "modulus": str(modulus),
                "text_size": str(text_size),
                "pattern": pattern,
                "seed": str(seed),
                "repeats": str(repeats),
                "hash_hits_mean": _fmt_number(stats["hash_hits_mean"]),
                "collisions_mean": _fmt_number(stats["collisions_mean"]),
                "collision_rate_mean": _fmt_rate(stats["collision_rate_mean"]),
                "collision_rate_std": _fmt_rate(stats["collision_rate_std"]),
            }
        )
    return rows


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _completed(rows: list[dict[str, str]], dataset: str) -> dict[str, dict[str, str]]:
    return {
        row["method"]: row
        for row in rows
        if row["dataset"] == dataset and row["status"] == "ok"
    }


def runtime_chart_title(small: int, seed: int, repeats: int, pattern: str) -> str:
    return (
        f"This run, mean seconds, {repeats} repeats, seed {seed}\n"
        f"englishish {small} characters, pattern {pattern}\n"
        "Left bar: preprocessing. Right bar: search after the build."
    )


def collision_chart_title(text_size: int, seed: int, repeats: int) -> str:
    return (
        f"Mean collisions / hash hits, {repeats} repeats, seed {seed}\n"
        f"random ACGT text, {text_size} characters, 8 character slice from inside it\n"
        "Separate from the benchmark text rows in metrics.csv"
    )


def lcp_chart_title(sample_size: int, seed: int) -> str:
    return (
        f"LCP length of adjacent suffixes, one build, seed {seed}\n"
        f"englishish {sample_size} characters. Deterministic sample, not a timed row."
    )


def heatmap_chart_title(seed: int, repeats: int, pattern: str) -> str:
    return (
        f"Mean search seconds after the build, {repeats} repeats, seed {seed}\n"
        f"englishish texts, pattern {pattern}\n"
        "A method is drawn only when it was measured on every size shown"
    )


def _draw_runtime_chart(
    path: Path,
    small_rows: dict[str, dict[str, str]],
    small: int,
    seed: int,
    repeats: int,
    pattern: str,
    note: str = "",
) -> None:
    methods = [method for method in METHODS if method in small_rows]
    fig, ax = plt.subplots()
    if methods:
        indexes = list(range(len(methods)))
        width = 0.36
        preprocess = [float(small_rows[method]["preprocess_mean_seconds"]) for method in methods]
        search = [float(small_rows[method]["search_mean_seconds"]) for method in methods]
        ax.bar(
            [i - width / 2 for i in indexes],
            preprocess,
            width,
            label="preprocessing",
            color="#2c5f8a",
        )
        ax.bar(
            [i + width / 2 for i in indexes],
            search,
            width,
            label="search",
            color="#c47b2b",
        )
        ax.set_xticks(indexes, methods)
        ax.legend()
    title = runtime_chart_title(small, seed, repeats, pattern)
    if note:
        title = title + "\n" + note
    ax.set_title(title, fontsize=9)
    ax.set_ylabel("Mean seconds from this run")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _draw_collision_chart(
    path: Path, rows: list[dict[str, str]], seed: int, repeats: int, note: str = ""
) -> None:
    text_size = int(rows[0]["text_size"]) if rows else 0
    fig, ax = plt.subplots()
    ax.bar(
        [row["modulus"] for row in rows],
        [float(row["collision_rate_mean"]) for row in rows],
        color="#c47b2b",
    )
    title = collision_chart_title(text_size, seed, repeats)
    if note:
        title = title + "\n" + note
    ax.set_title(title, fontsize=9)
    ax.set_ylabel("Mean collisions / hash hits")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _draw_lcp_chart(path: Path, sample_size: int, seed: int) -> None:
    sample = englishish(sample_size, seed=seed)
    suffix_array = build_suffix_array(sample)
    lcp = build_lcp(sample, suffix_array)
    fig, ax = plt.subplots()
    ax.plot(lcp, color="#2c5f8a")
    ax.set_title(lcp_chart_title(sample_size, seed), fontsize=9)
    ax.set_xlabel("Adjacent suffix rank")
    ax.set_ylabel("LCP length")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _draw_heatmap(
    path: Path,
    rows: list[dict[str, str]],
    datasets: list[tuple[str, int]],
    seed: int,
    repeats: int,
    pattern: str,
    note: str = "",
) -> None:
    by_dataset = {label: _completed(rows, label) for label, _size in datasets}
    methods = [
        method
        for method in METHODS
        if all(method in by_dataset[label] for label, _size in datasets)
    ]
    fig, ax = plt.subplots()
    if methods:
        data = [
            [float(by_dataset[label][method]["search_mean_seconds"]) for method in methods]
            for label, _size in datasets
        ]
        image = ax.imshow(data, aspect="auto", cmap="Blues")
        ax.set_xticks(range(len(methods)), methods)
        ax.set_yticks(
            range(len(datasets)),
            [f"{size} chars" for _label, size in datasets],
        )
        fig.colorbar(image, ax=ax, label="mean search seconds")
    title = heatmap_chart_title(seed, repeats, pattern)
    if note:
        title = title + "\n" + note
    ax.set_title(title, fontsize=9)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def run(
    output_dir: Path | None = None,
    *,
    small: int = DEFAULT_SMALL,
    medium: int = DEFAULT_MEDIUM,
    repeats: int = DEFAULT_REPEATS,
    seed: int = DEFAULT_SEED,
    pattern: str = DEFAULT_PATTERN,
    tree_max_chars: int = DEFAULT_TREE_MAX_CHARS,
    text_max_chars: int = DEFAULT_TEXT_MAX_CHARS,
    collision_text_size: int = DEFAULT_COLLISION_TEXT_SIZE,
    lcp_sample_size: int = DEFAULT_LCP_SAMPLE_SIZE,
    collision_moduli: tuple[int, ...] = COLLISION_MODULI,
    methods: tuple[str, ...] = METHODS,
    allow_replace: bool = False,
) -> dict[str, Path]:
    if repeats < 1:
        raise ValueError("repeats must be at least 1")
    if small < 1 or medium < 1:
        raise ValueError("text sizes must be positive")
    if tree_max_chars < 0 or text_max_chars < 0:
        raise ValueError("character limits cannot be negative")
    if collision_text_size < 1 or lcp_sample_size < 1:
        raise ValueError("chart sample sizes must be positive")

    unknown = [name for name in methods if name not in METHODS]
    if unknown or not methods:
        raise ValueError("methods must be chosen from kmp, rk, sa, tree")
    destination, replaced = resolve_output_dir(
        RESULTS if output_dir is None else Path(output_dir),
        allow_replace=allow_replace,
    )
    datasets = (("small", small), ("medium", medium))
    rows: list[dict[str, str]] = []
    for label, size in datasets:
        text = englishish(size, seed=seed)
        for method in methods:
            rows.append(
                measure_method(
                    label,
                    size,
                    method,
                    text,
                    pattern,
                    repeats,
                    seed,
                    tree_max_chars,
                    text_max_chars,
                )
            )
    metrics_path = destination / "metrics.csv"
    _write_csv(metrics_path, METRIC_FIELDS, rows)
    written: dict[str, Path] = {"metrics": metrics_path}
    side_charts = set(methods) == set(METHODS)
    if side_charts:
        collision_rows = measure_collision_table(
            collision_text_size, seed, repeats, collision_moduli
        )
        collision_path = destination / "collision_rates.csv"
        _write_csv(collision_path, COLLISION_FIELDS, collision_rows)
        written["collisions"] = collision_path
        _draw_collision_chart(destination / CHART_FILES[1], collision_rows, seed, repeats)
        _draw_lcp_chart(destination / CHART_FILES[2], lcp_sample_size, seed)
        written["collision_analysis"] = destination / CHART_FILES[1]
        written["sa_lcp_stats"] = destination / CHART_FILES[2]
    _draw_runtime_chart(
        destination / CHART_FILES[0], _completed(rows, "small"), small, seed, repeats, pattern
    )
    _draw_heatmap(destination / CHART_FILES[3], rows, list(datasets), seed, repeats, pattern)
    written["runtime_comparison"] = destination / CHART_FILES[0]
    written["heatmap"] = destination / CHART_FILES[3]
    print(f"Wrote {metrics_path}")
    if "collisions" in written:
        print(f"Wrote {written['collisions']}")
    if replaced:
        print(f"Replaced existing measurement files in {destination}.")
    else:
        print(f"Wrote measurement files to {destination}.")
    for row in rows:
        if row["status"] == "skipped":
            print(f"Skipped {row['dataset']} {row['method']}: {row['note']}")
    return written


def resolve_output_dir(destination: Path, allow_replace: bool) -> tuple[Path, bool]:
    """Return the folder to write, and whether that folder already had results.

    A folder that already holds measurement files is refused. The run does not
    create a nested pending_rerun directory, and it does not overwrite those
    files unless allow_replace is true.
    """
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    protected = [name for name in PROTECTED_RESULTS if (destination / name).exists()]
    if protected and not allow_replace:
        names = ", ".join(protected)
        raise ValueError(
            f"Refusing to write into {destination} because it already has {names}. "
            "Use an empty folder such as benchmarks/results/final_run. "
            "Pass --allow-replace only to overwrite those files."
        )
    return destination, bool(protected)


def plot_from_saved(
    metrics_path: Path,
    collision_path: Path,
    output_dir: Path | None = None,
    lcp_sample_size: int = DEFAULT_LCP_SAMPLE_SIZE,
) -> dict[str, Path]:
    """Draw the four charts from saved CSV rows. Does not time any search.

    The LCP chart is the existing deterministic sample: englishish text,
    lcp_sample_size characters, seed taken from the metrics file. It is not
    a new benchmark measurement.
    """
    metrics_path = Path(metrics_path)
    collision_path = Path(collision_path)
    destination = Path(output_dir) if output_dir is not None else metrics_path.parent
    if destination.resolve() == RESULTS.resolve():
        raise ValueError("refusing to overwrite historical charts in benchmarks/results")
    destination.mkdir(parents=True, exist_ok=True)
    with metrics_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("metrics file has no rows")
    seed = int(rows[0]["seed"])
    repeats = int(rows[0]["repeats"])
    pattern = rows[0]["pattern"]
    small_rows = [row for row in rows if row["dataset"] == "small" and row["status"] == "ok"]
    if not small_rows:
        raise ValueError("metrics file has no small rows")
    small = int(small_rows[0]["size"])
    datasets = []
    for label in ("small", "medium"):
        sized = [row for row in rows if row["dataset"] == label]
        if sized:
            datasets.append((label, int(sized[0]["size"])))
    with collision_path.open(newline="", encoding="utf-8") as handle:
        collision_rows = list(csv.DictReader(handle))
    if not collision_rows:
        raise ValueError("collision file has no rows")
    paths = {
        "runtime_comparison": destination / CHART_FILES[0],
        "collision_analysis": destination / CHART_FILES[1],
        "sa_lcp_stats": destination / CHART_FILES[2],
        "heatmap": destination / CHART_FILES[3],
    }
    _draw_runtime_chart(paths["runtime_comparison"], _completed(rows, "small"), small, seed, repeats, pattern)
    _draw_collision_chart(paths["collision_analysis"], collision_rows, seed, repeats)
    _draw_lcp_chart(paths["sa_lcp_stats"], lcp_sample_size, seed)
    _draw_heatmap(paths["heatmap"], rows, datasets, seed, repeats, pattern)
    print(f"Plotted saved rows into {destination}")
    return paths


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark KMP, Rabin Karp, a suffix array, and a compressed trie. "
            "Writes metrics.csv and does not change runtime.csv."
        )
    )
    parser.add_argument("--output-dir", type=Path, default=RESULTS)
    parser.add_argument("--small", type=int, default=DEFAULT_SMALL)
    parser.add_argument("--medium", type=int, default=DEFAULT_MEDIUM)
    parser.add_argument("--repeats", type=int, default=DEFAULT_REPEATS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--pattern", default=DEFAULT_PATTERN)
    parser.add_argument("--tree-max-chars", type=int, default=DEFAULT_TREE_MAX_CHARS)
    parser.add_argument("--text-max-chars", type=int, default=DEFAULT_TEXT_MAX_CHARS)
    parser.add_argument("--collision-text-size", type=int, default=DEFAULT_COLLISION_TEXT_SIZE)
    parser.add_argument("--lcp-sample-size", type=int, default=DEFAULT_LCP_SAMPLE_SIZE)
    parser.add_argument(
        "--methods",
        default="kmp,rk,sa,tree",
        help="Comma separated subset. Use tree to remeasure only the trie.",
    )
    parser.add_argument(
        "--allow-replace",
        action="store_true",
        help="Write into a folder that already holds saved PC measurements.",
    )
    parser.add_argument(
        "--plot-only",
        action="store_true",
        help="Draw charts from saved CSV files. Does not time any method.",
    )
    parser.add_argument("--metrics", type=Path, default=None)
    parser.add_argument("--collisions", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.plot_only:
        if args.metrics is None or args.collisions is None:
            raise ValueError("plot only needs --metrics and --collisions")
        plot_from_saved(
            args.metrics,
            args.collisions,
            output_dir=None if args.output_dir == RESULTS else args.output_dir,
            lcp_sample_size=args.lcp_sample_size,
        )
        return
    run(
        output_dir=args.output_dir,
        small=args.small,
        medium=args.medium,
        repeats=args.repeats,
        seed=args.seed,
        pattern=args.pattern,
        tree_max_chars=args.tree_max_chars,
        text_max_chars=args.text_max_chars,
        collision_text_size=args.collision_text_size,
        lcp_sample_size=args.lcp_sample_size,
        methods=_parse_methods(args.methods),
        allow_replace=args.allow_replace,
    )


def _parse_methods(text: str) -> tuple[str, ...]:
    names = tuple(part.strip() for part in text.split(",") if part.strip())
    if not names or any(name not in METHODS for name in names):
        raise ValueError("methods must be chosen from kmp, rk, sa, tree")
    return names


if __name__ == "__main__":
    main()
