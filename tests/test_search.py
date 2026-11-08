"""Tests for KMP, Rabin Karp, suffix array, suffix tree, applications, and the facade."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from applications.autocomplete import Autocomplete
from applications.dna_search import DNASearch
from applications.plagiarism import (
    highlight,
    longest_common_substring,
    overlapping_phrases,
    similarity_score,
)
from core.kmp import compute_failure_function, kmp_search
from core.rabin_karp import RabinKarp
from core.search_engine import StringSearchEngine
from core.suffix_array import binary_search, build_lcp, build_suffix_array
from core.suffix_tree import SuffixTree
from utils.rolling_hash import RollingHash
from utils.text_loader import load_fasta

FASTA = ROOT / "data" / "sample.fasta"


def test_failure_ababab() -> None:
    assert compute_failure_function("ABABD") == [0, 0, 1, 2, 0]


def test_failure_aabaab() -> None:
    assert compute_failure_function("AABAAB") == [0, 1, 0, 1, 2, 3]


def test_failure_empty() -> None:
    assert compute_failure_function("") == []


def test_kmp_basic() -> None:
    text = "ABABDABACDABABCABABA"
    pattern = "ABABCABABA"
    assert kmp_search(text, pattern) == [10]


def test_kmp_repeated() -> None:
    assert kmp_search("AAAAA", "AA") == [0, 1, 2, 3]


def test_kmp_pattern_longer() -> None:
    assert kmp_search("ABC", "ABCD") == []


def test_kmp_empty_pattern() -> None:
    assert kmp_search("ABC", "") == []


def test_kmp_no_match() -> None:
    assert kmp_search("ABCDEF", "XYZ") == []


def test_kmp_pattern_at_start() -> None:
    assert kmp_search("HELLO WORLD", "HELLO") == [0]


def test_kmp_pattern_at_end() -> None:
    assert kmp_search("HELLO WORLD", "WORLD") == [6]


def test_kmp_overlapping_aaaa_aa() -> None:
    assert kmp_search("AAAA", "AA") == [0, 1, 2]


def test_kmp_periodic_abab() -> None:
    assert compute_failure_function("ABAB") == [0, 0, 1, 2]
    assert kmp_search("ABABABAB", "ABAB") == [0, 2, 4]


def test_kmp_mismatch_falls_back_through_failure_table() -> None:
    from core.kmp import kmp_fallback_trace

    steps = kmp_fallback_trace("ABABABAB", "ABAC")
    assert steps
    fallback = steps[0]
    assert fallback["text_index"] == 3
    assert fallback["text_char"] == "B"
    assert fallback["pattern_char"] == "C"
    assert fallback["from_index"] == 3
    assert fallback["to_index"] == 1
    assert fallback["from_index"] > fallback["to_index"]
    assert kmp_search("ABABABAB", "ABAC") == []


def test_rabin_karp_matches_kmp() -> None:
    text = "the quick brown fox jumps over the lazy dog"
    pattern = "the"
    assert RabinKarp().search(text, pattern) == kmp_search(text, pattern)


def test_rabin_karp_multiple() -> None:
    text = "banana bandana"
    hits = RabinKarp().search_multiple(text, ["ban", "ana"])
    assert hits["ban"] == [0, 7]
    assert 1 in hits["ana"]


def test_rabin_karp_no_match() -> None:
    assert RabinKarp().search("ABCDEF", "XYZ") == []


def test_rabin_karp_pattern_at_start_and_end() -> None:
    text = "CATS AND CATS"
    assert RabinKarp().search(text, "CATS") == [0, 9]


def test_saved_demonstration_matches_the_code() -> None:
    from demonstrations.kmp_rk_demo import render

    saved = (ROOT / "analysis" / "demonstrations.md").read_text(encoding="utf-8")
    assert saved == render()
    assert "falls back from 3 to 1" in saved
    assert "3 17 3 2" in saved


def test_rabin_karp_base_changes_collisions_but_not_matches() -> None:
    text = "ABCABCXYZABCABC"
    pattern = "XYZ"
    verified = kmp_search(text, pattern)
    rates = []
    for base in (2, 3, 256):
        for modulus in (17, 101, 1_000_000_007):
            matcher = RabinKarp(base=base, modulus=modulus)
            positions = matcher.search(text, pattern)
            assert positions == verified
            assert matcher.collisions <= matcher.hash_hits
            if matcher.hash_hits:
                rates.append(matcher.collisions / matcher.hash_hits)
            else:
                rates.append(0.0)
    assert any(rate > 0 for rate in rates)
    assert rates[-1] == 0.0


def test_rabin_karp_forced_collision() -> None:
    """A small modulus produces a hash hit that fails the character check."""
    rk = RabinKarp(modulus=3)
    text = "ABCABC"
    pattern = "XYZ"
    positions = rk.search(text, pattern)
    assert positions == []
    assert rk.hash_hits > 0
    assert rk.collisions > 0


def test_rolling_hash_roll_matches_fresh() -> None:
    hasher = RollingHash()
    text = "ABCDEFGH"
    window = "CDEF"
    power = hasher.window_power(len(window))
    start = hasher.hash_string(text[0:4])
    rolled = hasher.roll(start, text[0], text[4], power)
    assert rolled == hasher.hash_string(text[1:5])


def test_suffix_array_banana() -> None:
    text = "BANANA"
    sa = build_suffix_array(text)
    suffixes = [text[i:] for i in sa]
    assert suffixes == sorted(suffixes)


def test_lcp_and_search() -> None:
    text = "ABABABAB"
    sa = build_suffix_array(text)
    lcp = build_lcp(text, sa)
    assert len(lcp) == len(text) - 1
    assert binary_search(text, sa, "ABAB") == kmp_search(text, "ABAB")


def test_suffix_array_no_match() -> None:
    text = "BANANA"
    sa = build_suffix_array(text)
    assert binary_search(text, sa, "XYZ") == []


def _naive_suffix_array(text: str) -> list[int]:
    return sorted(range(len(text)), key=lambda index: text[index:])


def _naive_lcp(text: str, sa: list[int]) -> list[int]:
    values = []
    for left, right in zip(sa, sa[1:]):
        length = 0
        while (
            left + length < len(text)
            and right + length < len(text)
            and text[left + length] == text[right + length]
        ):
            length += 1
        values.append(length)
    return values


def test_suffix_array_matches_full_string_order() -> None:
    samples = [
        "BANANA",
        "AAA",
        "ABABABAB",
        "abcabc",
        "café",
        "αβγαβγ",
        "a🙂a🙂",
        "",
        "a",
    ]
    for text in samples:
        sa = build_suffix_array(text)
        assert sa == _naive_suffix_array(text)
        assert build_lcp(text, sa) == _naive_lcp(text, sa)
        if text:
            pattern = text[:2] if len(text) >= 2 else text
            assert binary_search(text, sa, pattern) == kmp_search(text, pattern)


def test_suffix_array_tie_order_is_stable() -> None:
    text = "AAA"
    assert build_suffix_array(text) == [2, 1, 0]
    assert build_lcp(text, build_suffix_array(text)) == [1, 2]


def test_radix_sort_keeps_equal_keys_in_input_order() -> None:
    from core.suffix_array import _counting_sort

    items = [0, 1, 2, 3]
    ordered = _counting_sort(items, lambda index: 0, 0)
    assert ordered == [0, 1, 2, 3]


def test_suffix_tree_substring_and_count() -> None:
    text = "BANANA"
    tree = SuffixTree(text)
    assert tree.find_substring("ANA")
    assert not tree.find_substring("XYZ")
    assert tree.count_distinct_substrings() > 0
    repeated = tree.longest_repeated_substring()
    assert repeated in text


def test_suffix_tree_exact_banana_properties() -> None:
    tree = SuffixTree("BANANA")
    assert tree.longest_repeated_substring() == "ANA"
    assert tree.count_distinct_substrings() == 15
    assert sorted(tree.find_prefix("ANA")) == ["ANA", "ANANA"]
    assert tree.find_positions("ANA") == [1, 3]


def test_suffix_tree_prefix() -> None:
    tree = SuffixTree("BANANA")
    prefixes = tree.find_prefix("ANA")
    assert any(item.startswith("ANA") for item in prefixes)


def test_engine_times_are_separated_and_averaged(monkeypatch) -> None:
    import core.search_engine as engine_mod

    values = iter([0.0, 0.2, 0.2, 0.5, 0.5, 0.9])
    monkeypatch.setattr(engine_mod.time, "perf_counter", lambda: next(values))
    positions, mean = engine_mod._repeat_search(lambda: [7, 8], 3)
    assert positions == [7, 8]
    assert mean == pytest.approx(0.3)


def test_engine_kmp_builds_failure_table_once(monkeypatch) -> None:
    calls = {"n": 0}
    real = compute_failure_function

    def wrapped(pattern: str) -> list[int]:
        calls["n"] += 1
        return real(pattern)

    monkeypatch.setattr("core.kmp.compute_failure_function", wrapped)
    result = StringSearchEngine("AAAAA").find("AA", method="kmp", repeats=5)
    assert calls["n"] == 1
    assert result.positions == [0, 1, 2, 3]
    assert result.repeats == 5
    assert result.match_count == 4


def test_engine_rk_hashes_pattern_before_the_scan(monkeypatch) -> None:
    from utils.rolling_hash import RollingHash

    calls: list[str] = []
    real = RollingHash.hash_string

    def wrapped(self, value: str) -> int:
        calls.append(value)
        return real(self, value)

    monkeypatch.setattr(RollingHash, "hash_string", wrapped)
    result = StringSearchEngine("ABCABC").find("BC", method="rk", repeats=3)
    assert result.positions == [1, 4]
    assert calls.count("BC") == 1
    assert calls.count("AB") == 3


def test_engine_tree_positions_do_not_call_kmp(monkeypatch) -> None:
    from core.kmp import KMPMatcher

    calls = {"n": 0}
    real = KMPMatcher.__init__

    def wrapped(self, pattern: str) -> None:
        calls["n"] += 1
        real(self, pattern)

    monkeypatch.setattr(KMPMatcher, "__init__", wrapped)
    text = "BANANA"
    result = StringSearchEngine(text).find("ANA", method="tree", repeats=4)
    assert calls["n"] == 0
    assert result.positions == kmp_search(text, "ANA")
    assert result.match_count == 2
    assert result.repeats == 4


def test_engine_suffix_array_is_built_once(monkeypatch) -> None:
    calls = {"n": 0}
    real = build_suffix_array

    def wrapped(text: str) -> list[int]:
        calls["n"] += 1
        return real(text)

    monkeypatch.setattr("core.search_engine.build_suffix_array", wrapped)
    engine = StringSearchEngine("BANANA")
    first = engine.find("AN", method="sa", repeats=4)
    second = engine.find("NA", method="sa", repeats=2)
    assert calls["n"] == 1
    assert first.preprocessing_time == second.preprocessing_time
    assert first.positions == kmp_search("BANANA", "AN")
    assert second.positions == kmp_search("BANANA", "NA")


def test_engine_all_methods_agree() -> None:
    text = "the cat sat on the mat"
    pattern = "the"
    engine = StringSearchEngine(text)
    expected = kmp_search(text, pattern)
    for method in ("kmp", "rk", "sa", "tree"):
        result = engine.find(pattern, method=method)
        assert result.positions == expected
        assert result.match_count == len(expected)
        assert result.method == method


def test_engine_no_match() -> None:
    engine = StringSearchEngine("ABCDEF")
    for method in ("kmp", "rk", "sa", "tree"):
        result = engine.find("XYZ", method=method)
        assert result.positions == []
        assert result.match_count == 0


def test_engine_overlapping() -> None:
    engine = StringSearchEngine("AAAA")
    expected = [0, 1, 2]
    for method in ("kmp", "rk", "sa", "tree"):
        assert engine.find("AA", method=method).positions == expected


def test_engine_start_and_end() -> None:
    engine = StringSearchEngine("START middle END")
    assert engine.find("START", method="kmp").positions == [0]
    assert engine.find("END", method="rk").positions == [13]


def test_plagiarism_overlap_and_lcs() -> None:
    a = "the quick brown fox jumps"
    b = "a quick brown fox ran"
    phrases = overlapping_phrases(a, b, phrase_len=5)
    assert any("quick" in p or "brown" in p for p in phrases)
    lcs = longest_common_substring(a, b)
    assert "quick brown fox" in lcs or len(lcs) >= 5
    score = similarity_score(a, b, phrase_len=5)
    assert 0.0 < score <= 100.0


def test_plagiarism_highlight() -> None:
    out = highlight("the quick brown", ["quick"])
    assert "[quick]" in out


def test_dna_from_fasta() -> None:
    searcher = DNASearch.from_fasta(FASTA)
    assert "ACGT" in searcher.sequence
    positions = searcher.find_motif("ACGT")
    assert positions
    assert searcher.has_motif("ACGT")
    assert searcher.motif_count("ACGT") == len(positions)


def test_dna_no_motif() -> None:
    searcher = DNASearch.from_fasta(FASTA)
    assert searcher.find_motif("NNNN") == []
    assert not searcher.has_motif("NNNN")


def test_autocomplete_top_k() -> None:
    words = ["cat", "car", "card", "dog", "cat", "car", "car"]
    ac = Autocomplete(words)
    hits = ac.complete("ca", top_k=2)
    assert hits[0] == ("car", 3)
    assert hits[1][0] == "cat" or hits[1][0] == "card"


def test_autocomplete_empty_prefix() -> None:
    ac = Autocomplete(["alpha", "beta"])
    hits = ac.complete("", top_k=5)
    assert len(hits) == 2


def test_fasta_loader_skips_header() -> None:
    seq = load_fasta(FASTA)
    assert not seq.startswith(">")
    assert seq == seq.upper()
