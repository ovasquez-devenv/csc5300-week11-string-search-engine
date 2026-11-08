"""Facade that runs KMP, Rabin Karp, suffix array, or suffix tree search.

find() builds the pattern or text structure once, then repeats the same
search and stores the mean of those search clocks in search_time.
preprocessing_time is only the setup. The setup work is not inside the
search samples.

For the suffix array, setup is build_suffix_array. For the trie, setup is
the Ukkonen build. Tree positions come from that trie, not from a second
KMP scan.
"""

from __future__ import annotations

import statistics
import time
from dataclasses import dataclass

from core.kmp import KMPMatcher
from core.rabin_karp import RabinKarp
from core.suffix_array import binary_search, build_suffix_array
from core.suffix_tree import SuffixTree


@dataclass
class SearchResult:
    method: str
    positions: list[int]
    match_count: int
    preprocessing_time: float
    search_time: float
    recommendation: str
    repeats: int = 1


class StringSearchEngine:
    """Search one text with a chosen method."""

    def __init__(self, text: str) -> None:
        self.text = text
        self._sa: list[int] | None = None
        self._tree: SuffixTree | None = None
        self._sa_time = 0.0
        self._tree_time = 0.0

    def find(self, pattern: str, method: str = "kmp", repeats: int = 3) -> SearchResult:
        """Search and average `repeats` equivalent lookups after one setup.

        search_time is that average. preprocessing_time is the setup clock
        from the first time the structure is built on this engine. Later
        calls reuse a suffix array or trie and still report that original
        setup time. KMP and Rabin Karp setup depends on the pattern, so
        each call times that pattern setup again.
        """
        if repeats < 1:
            raise ValueError("repeats must be at least 1")
        method = method.lower()
        if method == "kmp":
            return self._kmp(pattern, repeats)
        if method in ("rk", "rabin", "rabin_karp"):
            return self._rk(pattern, repeats)
        if method in ("sa", "suffix_array"):
            return self._sa_search(pattern, repeats)
        if method in ("tree", "suffix_tree"):
            return self._tree_search(pattern, repeats)
        raise ValueError(f"Unknown method: {method}")

    def _recommend(self, method: str) -> str:
        if method == "kmp":
            return "KMP is a good default for one pattern."
        if method == "rk":
            return "Rabin Karp fits when you will search many patterns."
        if method in ("sa", "suffix_array"):
            return "Suffix array pays off when the same text is queried often."
        return "Suffix tree fits many substring and prefix queries on one text."

    def _kmp(self, pattern: str, repeats: int) -> SearchResult:
        start = time.perf_counter()
        matcher = KMPMatcher(pattern)
        pre = time.perf_counter() - start
        positions, search = _repeat_search(lambda: matcher.search(self.text), repeats)
        return SearchResult("kmp", positions, len(positions), pre, search, self._recommend("kmp"), repeats)

    def _rk(self, pattern: str, repeats: int) -> SearchResult:
        rk = RabinKarp()
        start = time.perf_counter()
        rk.preprocess(pattern)
        pre = time.perf_counter() - start
        positions, search = _repeat_search(lambda: rk.search_prepared(self.text), repeats)
        return SearchResult("rk", positions, len(positions), pre, search, self._recommend("rk"), repeats)

    def _sa_search(self, pattern: str, repeats: int) -> SearchResult:
        if self._sa is None:
            start = time.perf_counter()
            self._sa = build_suffix_array(self.text)
            self._sa_time = time.perf_counter() - start
        sa = self._sa
        positions, search = _repeat_search(
            lambda: binary_search(self.text, sa, pattern), repeats
        )
        return SearchResult(
            "sa", positions, len(positions), self._sa_time, search, self._recommend("sa"), repeats
        )

    def _tree_search(self, pattern: str, repeats: int) -> SearchResult:
        if self._tree is None:
            start = time.perf_counter()
            self._tree = SuffixTree(self.text)
            self._tree_time = time.perf_counter() - start
        tree = self._tree
        positions, search = _repeat_search(lambda: tree.find_positions(pattern), repeats)
        return SearchResult(
            "tree", positions, len(positions), self._tree_time, search, self._recommend("tree"), repeats
        )


def _repeat_search(fn, repeats: int) -> tuple[list[int], float]:
    """Run the same lookup `repeats` times and average those clocks.

    The function must not build the structure. The first result is the
    position list that is returned.
    """
    positions: list[int] | None = None
    samples: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter()
        found = fn()
        samples.append(time.perf_counter() - start)
        if positions is None:
            positions = found
    return positions or [], statistics.mean(samples)
