"""Knuth Morris Pratt string matching.

Builds the failure function (longest proper prefix that is also a suffix)
and matches in O(n + m) time. The text pointer never moves backward.
"""

from __future__ import annotations


def compute_failure_function(pattern: str) -> list[int]:
    """Return the LPS (longest proper prefix suffix) table for pattern.

    failure[i] is the length of the longest proper prefix of pattern[0..i]
    that is also a suffix of pattern[0..i].
    """
    m = len(pattern)
    failure = [0] * m
    if m == 0:
        return failure
    length = 0
    i = 1
    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            failure[i] = length
            i += 1
        else:
            if length != 0:
                length = failure[length - 1]
            else:
                failure[i] = 0
                i += 1
    return failure


def kmp_search_with_failure(text: str, pattern: str, failure: list[int]) -> list[int]:
    """Scan text with a failure table that was already built."""
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


def kmp_fallback_trace(text: str, pattern: str) -> list[dict[str, int | str]]:
    """Show each mismatch that falls back through the failure table.

    A record is written only when the pattern index is not zero and the
    characters differ. from_index is the pattern index before the jump.
    to_index is failure[from_index - 1], the index used after the fallback.
    The text index stays on the same character. Matches that do not mismatch
    are not listed. The returned positions still come from kmp_search.
    """
    n = len(text)
    m = len(pattern)
    if m == 0 or m > n:
        return []
    failure = compute_failure_function(pattern)
    steps: list[dict[str, int | str]] = []
    i = 0
    j = 0
    while i < n:
        if pattern[j] == text[i]:
            i += 1
            j += 1
            if j == m:
                j = failure[j - 1]
        else:
            if j != 0:
                steps.append(
                    {
                        "text_index": i,
                        "text_char": text[i],
                        "pattern_char": pattern[j],
                        "from_index": j,
                        "to_index": failure[j - 1],
                    }
                )
                j = failure[j - 1]
            else:
                i += 1
    return steps


def kmp_search(text: str, pattern: str) -> list[int]:
    """Return starting positions of pattern in text.

    Empty pattern returns an empty list. Pattern longer than text returns
    an empty list. Time is O(n + m).
    """
    if len(pattern) == 0 or len(pattern) > len(text):
        return []
    return kmp_search_with_failure(text, pattern, compute_failure_function(pattern))


class KMPMatcher:
    """Reusable KMP matcher. Precomputes the failure table once."""

    def __init__(self, pattern: str) -> None:
        self.pattern = pattern
        self.failure = compute_failure_function(pattern)

    def search(self, text: str) -> list[int]:
        return kmp_search_with_failure(text, self.pattern, self.failure)
