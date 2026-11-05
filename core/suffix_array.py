"""Suffix array with O(n log n) prefix doubling and Kasai LCP.

The suffix array lists starting positions of all suffixes in sorted order.
The LCP array stores the longest common prefix length of adjacent suffixes.
"""

from __future__ import annotations


def build_suffix_array(text: str) -> list[int]:
    """Build a suffix array with the prefix doubling method.

    Time is O(n log n). Returns starting indices of suffixes in sorted order.
    """
    n = len(text)
    if n == 0:
        return []
    sa = list(range(n))
    rank = [ord(ch) for ch in text]
    k = 1
    while k < n:
        sa.sort(key=lambda i: (rank[i], rank[i + k] if i + k < n else -1))
        new_rank = [0] * n
        for i in range(1, n):
            prev = sa[i - 1]
            cur = sa[i]
            prev_key = (rank[prev], rank[prev + k] if prev + k < n else -1)
            cur_key = (rank[cur], rank[cur + k] if cur + k < n else -1)
            new_rank[cur] = new_rank[prev] + (prev_key != cur_key)
        rank = new_rank
        if rank[sa[-1]] == n - 1:
            break
        k *= 2
    return sa


def build_lcp(text: str, sa: list[int]) -> list[int]:
    """Kasai algorithm. lcp[i] is the LCP of sa[i] and sa[i+1].

    The returned list has length n - 1 (or 0 if n < 2). Time is O(n).
    """
    n = len(text)
    if n < 2:
        return []
    rank = [0] * n
    for i, pos in enumerate(sa):
        rank[pos] = i
    lcp = [0] * (n - 1)
    h = 0
    for i in range(n):
        r = rank[i]
        if r == n - 1:
            h = 0
            continue
        j = sa[r + 1]
        while i + h < n and j + h < n and text[i + h] == text[j + h]:
            h += 1
        lcp[r] = h
        if h:
            h -= 1
    return lcp


def binary_search(text: str, sa: list[int], pattern: str) -> list[int]:
    """Find all starting positions of pattern using the suffix array.

    Binary search finds the range of suffixes that start with pattern.
    """
    n = len(text)
    m = len(pattern)
    if m == 0 or m > n or not sa:
        return []

    def suffix_cmp(idx: int) -> int:
        end = min(n, idx + m)
        chunk = text[idx:end]
        if chunk < pattern:
            return -1
        if chunk > pattern and not chunk.startswith(pattern):
            return 1
        if len(chunk) < m:
            return -1
        return 0

    lo, hi = 0, n
    while lo < hi:
        mid = (lo + hi) // 2
        if suffix_cmp(sa[mid]) < 0:
            lo = mid + 1
        else:
            hi = mid
    left = lo
    lo, hi = left, n
    while lo < hi:
        mid = (lo + hi) // 2
        chunk = text[sa[mid] : sa[mid] + m]
        if chunk.startswith(pattern):
            lo = mid + 1
        else:
            hi = mid
    right = lo
    return sorted(sa[i] for i in range(left, right))
