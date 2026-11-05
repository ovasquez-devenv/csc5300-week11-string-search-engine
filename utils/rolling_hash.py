"""Rolling hash used by Rabin Karp.

Hash(s) = (s[0]*base^(m-1) + s[1]*base^(m-2) + ... + s[m-1]) mod modulus.
Sliding the window updates the hash in O(1).
"""

from __future__ import annotations


class RollingHash:
    """Polynomial rolling hash with a fixed base and prime modulus."""

    def __init__(self, base: int = 256, modulus: int = 1_000_000_007) -> None:
        if base < 2:
            raise ValueError("base must be at least 2")
        if modulus < 2:
            raise ValueError("modulus must be at least 2")
        self.base = base
        self.modulus = modulus

    def hash_string(self, s: str) -> int:
        h = 0
        for ch in s:
            h = (h * self.base + ord(ch)) % self.modulus
        return h

    def window_power(self, length: int) -> int:
        """Return base^(length-1) mod modulus, or 1 if length is 0."""
        if length <= 1:
            return 1
        return pow(self.base, length - 1, self.modulus)

    def roll(self, current: int, outgoing: str, incoming: str, power: int) -> int:
        """Slide the window one character to the right."""
        removed = (ord(outgoing) * power) % self.modulus
        current = (current - removed) % self.modulus
        current = (current * self.base + ord(incoming)) % self.modulus
        return current
