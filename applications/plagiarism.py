"""Plagiarism style comparison using Rabin Karp phrases and suffix array LCS."""

from __future__ import annotations

from core.rabin_karp import RabinKarp
from core.suffix_array import binary_search, build_suffix_array


def overlapping_phrases(doc_a: str, doc_b: str, phrase_len: int = 8) -> list[str]:
    """Find phrases of phrase_len that appear in both documents."""
    if phrase_len <= 0 or len(doc_a) < phrase_len or len(doc_b) < phrase_len:
        return []
    phrases = []
    seen = set()
    for i in range(len(doc_a) - phrase_len + 1):
        phrase = doc_a[i : i + phrase_len]
        if phrase in seen:
            continue
        seen.add(phrase)
        phrases.append(phrase)
    rk = RabinKarp()
    hits = rk.search_multiple(doc_b, phrases)
    return [p for p, positions in hits.items() if positions]


def longest_common_substring(doc_a: str, doc_b: str) -> str:
    """Longest common substring via a combined string and its LCP."""
    if not doc_a or not doc_b:
        return ""
    sep = "\0"
    combined = doc_a + sep + doc_b
    sa = build_suffix_array(combined)
    from core.suffix_array import build_lcp

    lcp = build_lcp(combined, sa)
    best = ""
    split = len(doc_a)
    for i, length in enumerate(lcp):
        a = sa[i]
        b = sa[i + 1]
        if (a < split) != (b < split) and length > len(best):
            best = combined[a : a + length]
    return best


def similarity_score(doc_a: str, doc_b: str, phrase_len: int = 8) -> float:
    """Share of phrase windows in A that also appear in B, as a percent."""
    if not doc_a or not doc_b:
        return 0.0
    phrases = overlapping_phrases(doc_a, doc_b, phrase_len)
    windows = max(1, len(doc_a) - phrase_len + 1)
    unique = len({doc_a[i : i + phrase_len] for i in range(windows)})
    return 100.0 * len(phrases) / max(1, unique)


def highlight(doc: str, matches: list[str]) -> str:
    """Wrap matched phrases in brackets."""
    out = doc
    for phrase in sorted(set(matches), key=len, reverse=True):
        out = out.replace(phrase, f"[{phrase}]")
    return out
