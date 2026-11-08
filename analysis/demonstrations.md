# KMP and Rabin Karp demonstrations

These rows were produced by running the code on fixed strings.
Returned matches are the positions that passed the character check.
A hash hit that fails that check is a collision, not a match.

KMP mismatch fallback
text ABABABAB
pattern ABAC
failure table [0, 0, 1, 0]
matches []
mismatch at text index 3: text char B vs pattern char C. pattern index falls back from 3 to 1. the text index stays put.
mismatch at text index 5: text char B vs pattern char C. pattern index falls back from 3 to 1. the text index stays put.
mismatch at text index 7: text char B vs pattern char C. pattern index falls back from 3 to 1. the text index stays put.
periodic check ABABABAB searched for ABAB gives [0, 2, 4]
failure table for ABAB is [0, 0, 1, 2]

Rabin Karp text ABCABCXYZABCABC pattern XYZ. Verified matches [6].
base modulus hash_hits collisions rate verified_positions
2 17 1 0 0.000000 1
2 101 1 0 0.000000 1
2 1000000007 1 0 0.000000 1
3 17 3 2 0.666667 1
3 101 1 0 0.000000 1
3 1000000007 1 0 0.000000 1
256 17 1 0 0.000000 1
256 101 1 0 0.000000 1
256 1000000007 1 0 0.000000 1
