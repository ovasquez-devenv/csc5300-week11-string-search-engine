"""Load plain text and FASTA files."""

from __future__ import annotations

from pathlib import Path


def load_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def load_fasta(path: str | Path) -> str:
    """Return the concatenated sequence from a FASTA file, uppercase."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    seq = "".join(line.strip() for line in lines if line and not line.startswith(">"))
    return seq.upper()
