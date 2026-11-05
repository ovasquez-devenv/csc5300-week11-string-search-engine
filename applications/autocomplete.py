"""Prefix autocomplete with frequency weighting."""

from __future__ import annotations

from collections import Counter


class Autocomplete:
    def __init__(self, words: list[str]) -> None:
        self.counts = Counter(w.lower() for w in words if w)

    def complete(self, prefix: str, top_k: int = 5) -> list[tuple[str, int]]:
        prefix = prefix.lower()
        hits = [
            (word, count)
            for word, count in self.counts.items()
            if word.startswith(prefix)
        ]
        hits.sort(key=lambda item: (-item[1], item[0]))
        return hits[:top_k]
