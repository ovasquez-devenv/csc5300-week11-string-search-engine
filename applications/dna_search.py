"""DNA motif search using the suffix array and the suffix tree."""

from __future__ import annotations

from pathlib import Path

from core.suffix_array import binary_search, build_suffix_array
from core.suffix_tree import SuffixTree
from utils.text_loader import load_fasta


class DNASearch:
    def __init__(self, sequence: str) -> None:
        self.sequence = sequence.upper()
        self.sa = build_suffix_array(self.sequence)
        self.tree = SuffixTree(self.sequence)

    @classmethod
    def from_fasta(cls, path: str | Path) -> "DNASearch":
        return cls(load_fasta(path))

    def find_motif(self, motif: str) -> list[int]:
        return binary_search(self.sequence, self.sa, motif.upper())

    def has_motif(self, motif: str) -> bool:
        return self.tree.find_substring(motif.upper())

    def motif_count(self, motif: str) -> int:
        return len(self.find_motif(motif))
