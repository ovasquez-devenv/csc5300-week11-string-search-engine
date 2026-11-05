"""Seeded text generators for tests and benchmarks."""

from __future__ import annotations

import random


def seeded_rng(seed: int = 5300) -> random.Random:
    return random.Random(seed)


def random_text(length: int, alphabet: str = "ACGT", seed: int = 5300) -> str:
    rng = seeded_rng(seed)
    return "".join(rng.choice(alphabet) for _ in range(length))


def englishish(length: int, seed: int = 5300) -> str:
    words = [
        "the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog",
        "string", "search", "pattern", "match", "text", "engine",
    ]
    rng = seeded_rng(seed)
    parts: list[str] = []
    total = 0
    while total < length:
        word = rng.choice(words)
        parts.append(word)
        total += len(word) + 1
    return " ".join(parts)[:length]
