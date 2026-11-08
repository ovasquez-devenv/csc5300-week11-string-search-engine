"""Small deterministic demonstrations for KMP fallback and Rabin Karp bases.

Run from the project root:
    python -m demonstrations.kmp_rk_demo
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.kmp import compute_failure_function, kmp_fallback_trace, kmp_search
from core.rabin_karp import RabinKarp

KMP_TEXT = "ABABABAB"
KMP_PATTERN = "ABAC"
BASES = (2, 3, 256)
MODULI = (17, 101, 1_000_000_007)
RK_TEXT = "ABCABCXYZABCABC"
RK_PATTERN = "XYZ"


def kmp_lines() -> list[str]:
    failure = compute_failure_function(KMP_PATTERN)
    steps = kmp_fallback_trace(KMP_TEXT, KMP_PATTERN)
    lines = [
        "KMP mismatch fallback",
        f"text {KMP_TEXT}",
        f"pattern {KMP_PATTERN}",
        f"failure table {failure}",
        f"matches {kmp_search(KMP_TEXT, KMP_PATTERN)}",
    ]
    for step in steps:
        lines.append(
            "mismatch at text index {text_index}: text char {text_char} "
            "vs pattern char {pattern_char}. pattern index falls back from "
            "{from_index} to {to_index}. the text index stays put.".format(**step)
        )
    lines.append("periodic check ABABABAB searched for ABAB gives " + str(kmp_search("ABABABAB", "ABAB")))
    lines.append("failure table for ABAB is " + str(compute_failure_function("ABAB")))
    return lines


def rk_rows() -> list[dict[str, int | float]]:
    verified = kmp_search(RK_TEXT, RK_PATTERN)
    rows = []
    for base in BASES:
        for modulus in MODULI:
            matcher = RabinKarp(base=base, modulus=modulus)
            positions = matcher.search(RK_TEXT, RK_PATTERN)
            if positions != verified:
                raise RuntimeError("verified positions changed")
            hits = matcher.hash_hits
            collisions = matcher.collisions
            rate = 0.0 if hits == 0 else collisions / hits
            rows.append(
                {
                    "base": base,
                    "modulus": modulus,
                    "hash_hits": hits,
                    "collisions": collisions,
                    "rate": rate,
                    "verified_positions": len(positions),
                }
            )
    return rows


def render() -> str:
    lines = [
        "# KMP and Rabin Karp demonstrations",
        "",
        "These rows were produced by running the code on fixed strings.",
        "Returned matches are the positions that passed the character check.",
        "A hash hit that fails that check is a collision, not a match.",
        "",
    ]
    lines.extend(kmp_lines())
    lines.append("")
    lines.append(
        f"Rabin Karp text {RK_TEXT} pattern {RK_PATTERN}. "
        f"Verified matches {kmp_search(RK_TEXT, RK_PATTERN)}."
    )
    lines.append("base modulus hash_hits collisions rate verified_positions")
    for row in rk_rows():
        lines.append(
            f"{row['base']} {row['modulus']} {row['hash_hits']} {row['collisions']} "
            f"{row['rate']:.6f} {row['verified_positions']}"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    destination = ROOT / "analysis" / "demonstrations.md"
    destination.write_text(render(), encoding="utf-8")
    print(f"Wrote {destination}")


if __name__ == "__main__":
    main()
