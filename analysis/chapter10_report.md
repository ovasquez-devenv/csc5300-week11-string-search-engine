# Fast Pattern Matching

Omar Vasquez
Concordia University Texas
CSC 5300 Week 11

## Executive summary

This project implements four ways to find a pattern inside a text: Knuth Morris Pratt (KMP), Rabin Karp, a suffix array, and a compressed suffix tree. KMP is the default for one pattern. It preprocesses the pattern into a failure table and never moves backward in the text. Rabin Karp hashes a sliding window and is the better fit when many patterns share one pass. The suffix array and the suffix tree cost more to build and pay off when the same text is queried many times.

The code lives in a Python package named StringSearchEngine. Tests cover the failure table, repeated characters, a pattern longer than the text, hash collisions that must be verified, suffix array order, and tree queries. Benchmarks use a fixed seed of 5300 and report the mean and the standard deviation. The timing numbers in the analysis section were measured on this machine using the seeded benchmark.

## String matching complexity

The naive search tries the pattern at every position. If the text length is n and the pattern length is m, the worst case is about n times m character comparisons. A text of repeated letters with a pattern that almost matches is the classic slow case.

KMP removes that waste. Section 10.3 of Amakobe describes the failure function. For each position in the pattern, the table stores the length of the longest proper prefix that is also a suffix. Building the table is linear in m. The search then walks the text once. On a mismatch the pattern pointer jumps using the table instead of restarting. Total time is O(n + m). Space is O(m) for the table.

Rabin Karp, in section 10.4, turns the pattern into a number. A window of length m slides across the text and the hash updates in constant time. A matching hash is only a candidate. The characters are still compared, because two different strings can share a hash. Expected time is O(n + m). The worst case is still O(n m) if collisions are constant. The useful case is many patterns: hash them all, then one pass checks the window against the set.

A suffix array lists the starting positions of every suffix in sorted order. The prefix doubling build used here is O(n log n). Kasai's algorithm then builds the longest common prefix (LCP) array in linear time. A pattern query is a binary search over the sorted suffixes. A suffix tree stores the same suffixes in a compressed trie. Substring and prefix queries walk the trie. The longest repeated substring and the count of distinct substrings come from the edge structure.

## Implementation details

KMP lives in core/kmp.py. compute_failure_function builds the table. For the pattern ABABD the table is 0, 0, 1, 2, 0, matching the worked example in section 10.3.2. For AABAAB it is 0, 1, 0, 1, 2, 3. kmp_search returns every starting position. An empty pattern or a pattern longer than the text returns an empty list. After a full match the pattern pointer is set from the table so overlapping matches are found, as in AAAAA searched for AA.

Rabin Karp lives in core/rabin_karp.py and uses utils/rolling_hash.py. The default base is 256 and the default modulus is 1000000007. search handles one pattern. search_multiple groups patterns by length and does one pass per length. Every hash hit is verified. The object counts hash hits and collisions so the benchmark can show how the modulus changes the collision rate.

The suffix array is in core/suffix_array.py. build_suffix_array uses prefix doubling. build_lcp is Kasai. binary_search finds the range of suffixes that start with the pattern. The suffix tree in core/suffix_tree.py is Option A, a compressed trie built by inserting every suffix and splitting edges on mismatch. It supports find_substring, find_prefix, longest_repeated_substring, and count_distinct_substrings.

search_engine.py is the facade. StringSearchEngine(text).find(pattern, method) accepts kmp, rk, sa, or tree. The result holds positions, match count, preprocessing time, search time, and a short recommendation.

## Benchmark analysis

The script benchmarks/benchmark_search.py builds a 10 KB text and a 1 MB text with seed 5300. It times KMP, Rabin Karp, and the suffix array on both sizes. The suffix tree is timed on the small text only, because the compressed trie is heavier to build. Each method is run three times. The script writes the mean and the standard deviation to benchmarks/results/runtime.csv and draws four charts: runtime_comparison.png, collision_analysis.png, sa_lcp_stats.png, and heatmap_dataset_sizes.png.

Measured results from this PC are shown below. Each value summarizes three runs with seed 5300.

| Dataset | Method | Mean seconds | Std seconds |
| --- | --- | --- | --- |
| 10 KB | kmp | 0.000666 | 0.000056 |
| 10 KB | rk | 0.002190 | 0.000266 |
| 10 KB | sa | 0.021563 | 0.000376 |
| 10 KB | tree | 0.033104 | 0.011877 |
| 1 MB | kmp | 0.051032 | 0.003464 |
| 1 MB | rk | 0.233437 | 0.007826 |
| 1 MB | sa | 6.761709 | 0.079170 |

The collision chart varies the modulus over 101, 1009, 10007, and 100003 on a seeded random text. A smaller modulus produces more hash hits that fail the character check. A larger prime cuts that rate. The LCP chart plots adjacent suffix overlap on a 2,000 character sample. The heatmap compares mean time across dataset size and method.

## Trade offs

KMP has a small preprocess and a fast single pattern search. It does not help when the pattern changes every query and the text is huge, because each new pattern rebuilds only a small table while the text is scanned again.

Rabin Karp spends its advantage on many patterns. A single pattern is often no faster than KMP, and a bad modulus adds verification work. Collisions are not wrong answers, because every hit is checked, but they waste time.

The suffix array is the better long term structure when the text is fixed and the patterns vary. The O(n log n) build is the cost. After that, each query is a binary search. The LCP array also supports longest common substring between two documents, which the plagiarism application uses.

The compressed trie answers substring and prefix questions directly and can count distinct substrings from edge lengths. It uses more memory than the suffix array and is slower to build in this straightforward implementation. For a one time search it is the wrong tool.

## Applications

plagiarism.py finds overlapping phrases with Rabin Karp, then uses the suffix array and LCP on a combined string to get a longest common substring. The similarity score is the share of unique phrase windows in the first document that also appear in the second. highlight wraps matched phrases in brackets.

dna_search.py loads a FASTA file, builds a suffix array and a suffix tree, and searches motifs. The sample file data/sample.fasta is a short synthetic gene so the path can be tested without a real genome.

autocomplete.py stores word frequencies and returns the top k completions for a prefix, sorted by count and then by the word.

## Conclusion

KMP is the right default for one pattern. Rabin Karp is the right tool for a set of patterns. A suffix array or a compressed trie is the right tool when one text will be queried many times. The project implements all four, tests the edge cases from the chapter, and reports a seeded benchmark run on this machine so every timing number in the final report is measured, not assumed.

## Source

Amakobe, M. (2025). Advanced algorithms: A journey through computational problem solving. Chapter 10.

