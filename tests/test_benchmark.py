"""Smoke tests for separated benchmark metrics.

These tests use tiny texts. They do not run the 10 KB or 1 MB benchmark.
"""

from __future__ import annotations

import csv
import sys
import time
import tracemalloc
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import benchmarks.benchmark_search as bench
from benchmarks.benchmark_search import (
    CHART_FILES,
    COLLISION_FIELDS,
    COLLISION_MODULI,
    DEFAULT_MEDIUM,
    DEFAULT_REPEATS,
    DEFAULT_SEED,
    DEFAULT_SMALL,
    DEFAULT_TEXT_MAX_CHARS,
    DEFAULT_TREE_MAX_CHARS,
    collision_chart_title,
    heatmap_chart_title,
    lcp_chart_title,
    method_character_limit,
    runtime_chart_title,
    METRIC_FIELDS,
    collision_stats,
    main,
    mean_std,
    parse_args,
    prepare,
    query,
    run,
    time_prepare,
    time_search,
)
from core.kmp import compute_failure_function, kmp_search
from core.rabin_karp import RabinKarp
from core.suffix_array import binary_search, build_suffix_array
from core.suffix_tree import SuffixTree

RUNTIME_CSV = ROOT / "benchmarks" / "results" / "runtime.csv"
HISTORICAL_MEANS = [
    "0.000666",
    "0.002190",
    "0.021563",
    "0.033104",
    "0.051032",
    "0.233437",
    "6.761709",
]


def test_defaults_cover_required_sizes() -> None:
    assert DEFAULT_SEED == 5300
    assert DEFAULT_REPEATS == 3
    assert DEFAULT_SMALL == 10_000
    assert 1_000_000 <= DEFAULT_MEDIUM <= 5_000_000
    assert DEFAULT_TREE_MAX_CHARS >= DEFAULT_MEDIUM
    assert DEFAULT_TREE_MAX_CHARS == 1_000_000
    assert DEFAULT_TEXT_MAX_CHARS == DEFAULT_MEDIUM
    assert method_character_limit("tree", tree_max_chars=50_000, text_max_chars=1_000_000) == 50_000
    assert method_character_limit("sa", tree_max_chars=50_000, text_max_chars=1_000_000) == 1_000_000
    assert COLLISION_MODULI == (101, 1009, 10007, 100003)


def test_mean_std_uses_population_formula() -> None:
    mean, std = mean_std([1.0, 2.0, 3.0])
    assert mean == pytest.approx(2.0)
    assert std == pytest.approx((2.0 / 3.0) ** 0.5)


def test_kmp_query_matches_library_and_skips_rebuild(monkeypatch) -> None:
    calls = {"n": 0}
    real = compute_failure_function

    def wrapped(pattern: str) -> list[int]:
        calls["n"] += 1
        return real(pattern)

    monkeypatch.setattr(bench, "compute_failure_function", wrapped)
    text = "AAAAA"
    pattern = "AA"
    time_search("kmp", text, pattern, repeats=4)
    assert calls["n"] == 1
    failure = prepare("kmp", text, pattern)
    assert query("kmp", text, pattern, failure) == kmp_search(text, pattern)


def test_rk_query_matches_library_counts() -> None:
    text = "ABCABC"
    pattern = "XYZ"
    state = prepare("rk", text, pattern, modulus=3)
    positions = query("rk", text, pattern, state)
    library = RabinKarp(modulus=3)
    assert library.search(text, pattern) == positions
    assert library.hash_hits == state[0].hash_hits
    assert library.collisions == state[0].collisions
    assert library.collisions > 0


def test_suffix_array_search_timer_builds_once(monkeypatch) -> None:
    calls = {"n": 0}
    real = build_suffix_array

    def wrapped(text: str) -> list[int]:
        calls["n"] += 1
        return real(text)

    monkeypatch.setattr(bench, "build_suffix_array", wrapped)
    text = "BANANA BANDANA"
    pattern = "ANA"
    time_search("sa", text, pattern, repeats=4)
    assert calls["n"] == 1
    array = prepare("sa", text, pattern)
    assert query("sa", text, pattern, array) == binary_search(text, array, pattern)
    assert query("sa", text, pattern, array) == kmp_search(text, pattern)


def test_tree_query_returns_the_same_positions_as_kmp() -> None:
    samples = [
        ("BANANA", "ANA"),
        ("BANANA", "A"),
        ("BANANA", "NA"),
        ("BANANA", "BANANA"),
        ("BANANA", "XYZ"),
        ("AAAA", "AA"),
        ("AAAAA", "AA"),
        ("the cat sat on the mat", "the"),
        ("START middle END", "END"),
        ("ABC", "ABCD"),
        (bench.englishish(1500, seed=5300), "search"),
    ]
    for text, pattern in samples:
        tree = prepare("tree", text, pattern)
        assert isinstance(tree, SuffixTree)
        assert query("tree", text, pattern, tree) == kmp_search(text, pattern)


def test_timer_refuses_to_run_while_tracing() -> None:
    tracemalloc.start()
    try:
        with pytest.raises(RuntimeError):
            time_prepare("kmp", "abc", "a", repeats=1)
    finally:
        tracemalloc.stop()


def test_search_memory_does_not_rebuild_suffix_array(monkeypatch) -> None:
    calls = {"n": 0}
    real = build_suffix_array

    def wrapped(text: str) -> list[int]:
        calls["n"] += 1
        return real(text)

    monkeypatch.setattr(bench, "build_suffix_array", wrapped)
    text = "ABABABAB"
    state = prepare("sa", text, "ABA")
    calls["n"] = 0
    mean, _std = bench.memory_peaks(lambda: query("sa", text, "ABA", state), repeats=2)
    assert calls["n"] == 0
    assert mean > 0
    assert tracemalloc.is_tracing() is False


def test_historical_runtime_csv_values_stay() -> None:
    with RUNTIME_CSV.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["mean_seconds"] for row in rows] == HISTORICAL_MEANS
    assert [row["method"] for row in rows] == ["kmp", "rk", "sa", "tree", "kmp", "rk", "sa"]
    assert rows[3]["dataset"] == "small"
    assert all(row["seed"] == "5300" for row in rows)
    assert set(rows[0]) == {"dataset", "size", "method", "mean_seconds", "std_seconds", "seed"}


def test_smoke_run_writes_separated_metrics(tmp_path: Path) -> None:
    before = RUNTIME_CSV.read_bytes()
    paths = run(
        output_dir=tmp_path,
        small=180,
        medium=420,
        repeats=2,
        seed=5300,
        pattern="search",
        tree_max_chars=250,
        collision_text_size=400,
        lcp_sample_size=80,
    )
    assert RUNTIME_CSV.read_bytes() == before
    with paths["metrics"].open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert list(rows[0]) == METRIC_FIELDS
    assert len(rows) == 8
    skipped = [row for row in rows if row["status"] == "skipped"]
    assert len(skipped) == 1
    assert skipped[0]["dataset"] == "medium"
    assert skipped[0]["method"] == "tree"
    assert skipped[0]["preprocess_mean_seconds"] == ""
    assert skipped[0]["search_mean_seconds"] == ""
    assert "420" in skipped[0]["note"]
    assert "250" in skipped[0]["note"]
    ok_rows = [row for row in rows if row["status"] == "ok"]
    assert len(ok_rows) == 7
    for row in ok_rows:
        assert row["seed"] == "5300"
        assert row["repeats"] == "2"
        assert row["preprocess_mean_seconds"].count(".") == 1
        assert len(row["preprocess_mean_seconds"].split(".")[1]) == 9
        assert len(row["search_std_seconds"].split(".")[1]) == 9
        assert float(row["preprocess_tracemalloc_peak_mean_bytes"]) > 0
    rk_rows = [row for row in ok_rows if row["method"] == "rk"]
    assert rk_rows
    assert all(row["rk_modulus"] == "1000000007" for row in rk_rows)
    assert all(row["rk_collision_rate_mean"] != "" for row in rk_rows)
    kmp_rows = [row for row in ok_rows if row["method"] == "kmp"]
    assert all(row["rk_collision_rate_mean"] == "" for row in kmp_rows)
    for name in CHART_FILES:
        chart = paths["metrics"].parent / name
        assert chart.is_file()
        assert chart.stat().st_size > 1000
    with paths["collisions"].open(newline="", encoding="utf-8") as handle:
        collision_rows = list(csv.DictReader(handle))
    assert list(collision_rows[0]) == COLLISION_FIELDS
    assert [row["modulus"] for row in collision_rows] == ["101", "1009", "10007", "100003"]
    assert float(collision_rows[0]["collision_rate_mean"]) > 0


def test_collision_table_is_stable_for_a_seed(tmp_path: Path) -> None:
    kwargs = dict(
        small=120,
        medium=200,
        repeats=2,
        seed=5300,
        tree_max_chars=10_000,
        collision_text_size=350,
        lcp_sample_size=40,
    )
    first = run(output_dir=tmp_path / "a", **kwargs)
    second = run(output_dir=tmp_path / "b", **kwargs)
    assert first["collisions"].read_text(encoding="utf-8") == second["collisions"].read_text(
        encoding="utf-8"
    )


def test_collision_stats_match_one_library_call() -> None:
    text = "ABCABCXYZ"
    stats = collision_stats(text, "XYZ", modulus=3, repeats=3)
    matcher = RabinKarp(modulus=3)
    matcher.search(text, "XYZ")
    assert stats["hash_hits_mean"] == pytest.approx(matcher.hash_hits)
    assert stats["collisions_mean"] == pytest.approx(matcher.collisions)
    assert stats["collision_rate_std"] == pytest.approx(0.0)


def test_main_forwards_cli_without_running_full_sizes(monkeypatch, tmp_path: Path) -> None:
    seen = {}

    def fake_run(**kwargs):
        seen.update(kwargs)
        return {}

    monkeypatch.setattr(bench, "run", fake_run)
    main(
        [
            "--small",
            "10",
            "--medium",
            "20",
            "--repeats",
            "2",
            "--seed",
            "7",
            "--tree-max-chars",
            "15",
            "--output-dir",
            str(tmp_path),
            "--pattern",
            "ab",
        ]
    )
    assert seen["small"] == 10
    assert seen["medium"] == 20
    assert seen["repeats"] == 2
    assert seen["seed"] == 7
    assert seen["tree_max_chars"] == 15
    assert seen["pattern"] == "ab"
    assert seen["output_dir"] == tmp_path


def test_parse_args_defaults_match_assignment() -> None:
    args = parse_args([])
    assert args.small == 10_000
    assert args.medium == 1_000_000
    assert args.repeats == 3
    assert args.seed == 5300
    assert args.tree_max_chars == 1_000_000
    assert args.text_max_chars == 1_000_000


def test_default_medium_trie_is_skipped_and_scans_run(tmp_path: Path, monkeypatch) -> None:
    built: list[int] = []
    real_init = SuffixTree.__init__

    def wrapped(self, text: str) -> None:
        built.append(len(text))
        real_init(self, text)

    monkeypatch.setattr(SuffixTree, "__init__", wrapped)
    paths = run(
        output_dir=tmp_path,
        small=80,
        medium=500,
        repeats=1,
        tree_max_chars=100,
        text_max_chars=200,
        collision_text_size=120,
        lcp_sample_size=40,
    )
    assert built and max(built) <= 80
    with paths["metrics"].open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    skipped = {(row["dataset"], row["method"]) for row in rows if row["status"] == "skipped"}
    assert skipped == {
        ("medium", "kmp"),
        ("medium", "rk"),
        ("medium", "sa"),
        ("medium", "tree"),
    }
    medium_tree = next(row for row in rows if row["dataset"] == "medium" and row["method"] == "tree")
    medium_sa = next(row for row in rows if row["dataset"] == "medium" and row["method"] == "sa")
    assert "500" in medium_tree["note"] and "100" in medium_tree["note"]
    assert "200" in medium_sa["note"]
    assert medium_tree["search_mean_seconds"] == ""
    assert medium_sa["preprocess_mean_seconds"] == ""


def test_chart_titles_name_measurement_and_source() -> None:
    runtime = runtime_chart_title(10_000, 5300, 3, "search")
    assert "10000" in runtime
    assert "5300" in runtime
    assert "search" in runtime
    assert "englishish" in runtime
    assert "preprocessing" in runtime
    assert "metrics" not in runtime or "This run" in runtime
    collision = collision_chart_title(20_000, 5300, 3)
    assert "ACGT" in collision
    assert "20000" in collision
    assert "metrics.csv" in collision
    lcp = lcp_chart_title(2_000, 5300)
    assert "2000" in lcp
    assert "englishish" in lcp
    assert "one build" in lcp
    heatmap = heatmap_chart_title(5300, 3, "search")
    assert "search seconds" in heatmap
    assert "every size" in heatmap


def test_elapsed_stops_before_the_destructor_runs() -> None:
    released: list[float] = []

    class SlowDeath:
        def __del__(self) -> None:
            released.append(time.perf_counter())
            time.sleep(0.05)

    start = time.perf_counter()
    elapsed = bench._elapsed(lambda: SlowDeath())
    finished = time.perf_counter()
    assert elapsed < 0.03
    assert released
    assert start + elapsed <= released[0] <= finished


def test_saved_measurement_files_are_not_replaced(tmp_path: Path) -> None:
    sentinel = "keep-omar-metrics\n"
    (tmp_path / "metrics.csv").write_text(sentinel, encoding="utf-8")
    (tmp_path / "runtime.csv").write_text("keep-runtime\n", encoding="utf-8")
    with pytest.raises(ValueError, match="final_run"):
        run(
            output_dir=tmp_path,
            small=40,
            medium=80,
            repeats=1,
            methods=("kmp",),
            tree_max_chars=1_000_000,
            text_max_chars=1_000_000,
            collision_text_size=80,
            lcp_sample_size=20,
        )
    assert (tmp_path / "metrics.csv").read_text(encoding="utf-8") == sentinel
    assert (tmp_path / "runtime.csv").read_text(encoding="utf-8") == "keep-runtime\n"
    assert not (tmp_path / "pending_rerun").exists()


def test_plot_from_saved_does_not_rewrite_csv_or_historical_charts(tmp_path: Path) -> None:
    metrics = tmp_path / "metrics.csv"
    collisions = tmp_path / "collision_rates.csv"
    row = {field: "" for field in METRIC_FIELDS}
    row.update(
        dataset="small",
        size="20",
        method="kmp",
        pattern="ab",
        seed="5300",
        repeats="3",
        preprocess_mean_seconds="0.100000000",
        preprocess_std_seconds="0.000000000",
        search_mean_seconds="0.200000000",
        search_std_seconds="0.000000000",
        preprocess_tracemalloc_peak_mean_bytes="10.000",
        preprocess_tracemalloc_peak_std_bytes="0.000",
        search_tracemalloc_peak_mean_bytes="11.000",
        search_tracemalloc_peak_std_bytes="0.000",
        status="ok",
    )
    medium = dict(row)
    medium.update(
        dataset="medium",
        size="40",
        preprocess_mean_seconds="0.300000000",
        search_mean_seconds="0.400000000",
    )
    with metrics.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=METRIC_FIELDS)
        writer.writeheader()
        writer.writerows([row, medium])
    with collisions.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLLISION_FIELDS)
        writer.writeheader()
        writer.writerow(
            {
                "modulus": "101",
                "text_size": "20",
                "pattern": "ACGTACGT",
                "seed": "5300",
                "repeats": "3",
                "hash_hits_mean": "4.000",
                "collisions_mean": "2.000",
                "collision_rate_mean": "0.500000",
                "collision_rate_std": "0.000000",
            }
        )
    before = metrics.read_bytes()
    paths = bench.plot_from_saved(metrics, collisions, lcp_sample_size=30)
    assert metrics.read_bytes() == before
    for key in ("runtime_comparison", "collision_analysis", "sa_lcp_stats", "heatmap"):
        assert paths[key].is_file()
        assert paths[key].stat().st_size > 500
    with pytest.raises(ValueError):
        bench.plot_from_saved(metrics, collisions, output_dir=bench.RESULTS, lcp_sample_size=30)


def test_run_rejects_bad_repeats(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        run(output_dir=tmp_path, small=20, medium=30, repeats=0, tree_max_chars=100)
