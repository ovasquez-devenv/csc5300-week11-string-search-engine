"""Rabin Karp string matching with a rolling hash.

Supports one pattern or many patterns. A hash hit is verified by a
character compare so collisions do not produce false matches.
"""

from __future__ import annotations

from collections import defaultdict

from utils.rolling_hash import RollingHash


class RabinKarp:
    """Single and multi pattern Rabin Karp matcher."""

    def __init__(self, base: int = 256, modulus: int = 1_000_000_007) -> None:
        self.hasher = RollingHash(base=base, modulus=modulus)
        self.collisions = 0
        self.hash_hits = 0
        self._pattern = ""
        self._target = 0
        self._power = 1

    def preprocess(self, pattern: str) -> None:
        """Hash the pattern and store the window power. Does not scan the text."""
        self._pattern = pattern
        self._target = self.hasher.hash_string(pattern) if pattern else 0
        self._power = self.hasher.window_power(len(pattern))

    def search_prepared(self, text: str) -> list[int]:
        """Slide the window using the hash from preprocess."""
        pattern = self._pattern
        n = len(text)
        m = len(pattern)
        self.collisions = 0
        self.hash_hits = 0
        if m == 0 or m > n:
            return []
        target = self._target
        power = self._power
        window = self.hasher.hash_string(text[:m])
        positions: list[int] = []
        if window == target:
            self.hash_hits += 1
            if text[:m] == pattern:
                positions.append(0)
            else:
                self.collisions += 1
        for i in range(1, n - m + 1):
            window = self.hasher.roll(window, text[i - 1], text[i + m - 1], power)
            if window == target:
                self.hash_hits += 1
                if text[i : i + m] == pattern:
                    positions.append(i)
                else:
                    self.collisions += 1
        return positions

    def search(self, text: str, pattern: str) -> list[int]:
        """Return starting positions of pattern in text."""
        self.preprocess(pattern)
        return self.search_prepared(text)

    def search_multiple(self, text: str, patterns: list[str]) -> dict[str, list[int]]:
        """Search for many patterns of the same length in one pass.

        Patterns of different lengths are grouped and searched per length.
        """
        result: dict[str, list[int]] = {p: [] for p in patterns}
        by_length: dict[int, list[str]] = defaultdict(list)
        for p in patterns:
            if p:
                by_length[len(p)].append(p)
        for length, group in by_length.items():
            if length > len(text):
                continue
            targets: dict[int, list[str]] = defaultdict(list)
            for p in group:
                targets[self.hasher.hash_string(p)].append(p)
            power = self.hasher.window_power(length)
            window = self.hasher.hash_string(text[:length])
            self._check_window(text, 0, length, window, targets, result)
            for i in range(1, len(text) - length + 1):
                window = self.hasher.roll(
                    window, text[i - 1], text[i + length - 1], power
                )
                self._check_window(text, i, length, window, targets, result)
        return result

    def _check_window(
        self,
        text: str,
        start: int,
        length: int,
        window: int,
        targets: dict[int, list[str]],
        result: dict[str, list[int]],
    ) -> None:
        candidates = targets.get(window)
        if not candidates:
            return
        self.hash_hits += 1
        chunk = text[start : start + length]
        matched = False
        for pattern in candidates:
            if chunk == pattern:
                result[pattern].append(start)
                matched = True
        if not matched:
            self.collisions += 1
