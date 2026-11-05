"""Facade that runs KMP, Rabin Karp, suffix array, or suffix tree search.

Records preprocessing time, search time, match count, and a short
recommendation based on the method.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from core.kmp import KMPMatcher
from core.rabin_karp import RabinKarp
from core.suffix_array import binary_search, build_lcp, build_suffix_array
from core.suffix_tree import SuffixTree


@dataclass
class SearchResult:
    method: str
    positions: list[int]
    match_count: int
    preprocessing_time: float
    search_time: float
    recommendation: str


class StringSearchEngine:
    """Search one text with a chosen method."""

    def __init__(self, text: str) -> None:
        self.text = text
        self._sa: list[int] | None = None
        self._lcp: list[int] | None = None
        self._tree: SuffixTree | None = None
        self._sa_time = 0.0
        self._tree_time = 0.0

    def _ensure_sa(self) -> tuple[list[int], list[int]]:
        if self._sa is None:
            start = time.perf_counter()
            self._sa = build_suffix_array(self.text)
            self._lcp = build_lcp(self.text, self._sa)
            self._sa_time = time.perf_counter() - start
        return self._sa, self._lcp or []

    def _ensure_tree(self) -> SuffixTree:
        if self._tree is None:
            start = time.perf_counter()
            self._tree = SuffixTree(self.text)
            self._tree_time = time.perf_counter() - start
        return self._tree

    def find(self, pattern: str, method: str = "kmp") -> SearchResult:
        method = method.lower()
        if method == "kmp":
            return self._kmp(pattern)
        if method in ("rk", "rabin", "rabin_karp"):
            return self._rk(pattern)
        if method in ("sa", "suffix_array"):
            return self._sa_search(pattern)
        if method in ("tree", "suffix_tree"):
            return self._tree_search(pattern)
        raise ValueError(f"Unknown method: {method}")

    def _recommend(self, method: str) -> str:
        if method == "kmp":
            return "KMP is a good default for one pattern."
        if method == "rk":
            return "Rabin Karp fits when you will search many patterns."
        if method in ("sa", "suffix_array"):
            return "Suffix array pays off when the same text is queried often."
        return "Suffix tree fits many substring and prefix queries on one text."

    def _kmp(self, pattern: str) -> SearchResult:
        start = time.perf_counter()
        matcher = KMPMatcher(pattern)
        pre = time.perf_counter() - start
        start = time.perf_counter()
        positions = matcher.search(self.text)
        search = time.perf_counter() - start
        return SearchResult("kmp", positions, len(positions), pre, search, self._recommend("kmp"))

    def _rk(self, pattern: str) -> SearchResult:
        rk = RabinKarp()
        start = time.perf_counter()
        positions = rk.search(self.text, pattern)
        search = time.perf_counter() - start
        return SearchResult("rk", positions, len(positions), 0.0, search, self._recommend("rk"))

    def _sa_search(self, pattern: str) -> SearchResult:
        sa, _ = self._ensure_sa()
        start = time.perf_counter()
        positions = binary_search(self.text, sa, pattern)
        search = time.perf_counter() - start
        return SearchResult(
            "sa", positions, len(positions), self._sa_time, search, self._recommend("sa")
        )

    def _tree_search(self, pattern: str) -> SearchResult:
        tree = self._ensure_tree()
        start = time.perf_counter()
        found = tree.find_substring(pattern)
        search = time.perf_counter() - start
        positions = self._kmp(pattern).positions if found else []
        return SearchResult(
            "tree", positions, len(positions), self._tree_time, search, self._recommend("tree")
        )
