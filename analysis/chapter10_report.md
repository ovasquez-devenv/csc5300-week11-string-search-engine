# Fast Pattern Matching

Omar Vasquez
Concordia University Texas
CSC 5300 Week 11

## Executive summary

This project implements four ways to find a pattern inside a text: Knuth Morris Pratt (KMP), Rabin Karp, a suffix array, and a compressed suffix tree. KMP is the default for one pattern. It preprocesses the pattern into a failure table and never moves backward in the text. Rabin Karp hashes a sliding window and is the better fit when many patterns share one pass. The suffix array and the suffix tree cost more to build and pay off when the same text is queried many times.

The code lives in a Python package named StringSearchEngine. Tests cover the failure table, repeated characters, a pattern longer than the text, hash collisions that must be verified, suffix array order, and tree queries. Seed 5300 produced the combined times below on this PC. Preprocessing time, search latency, tracemalloc peak, and collision rate are copied from metrics.csv after this PC runs the updated script.

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

The table is the earlier run on this PC: one timer on the whole call, three repeats, seed 5300, pattern search, generator random.Random. Mean is statistics.mean. Standard deviation is statistics.pstdev, the population kind, dividing by the repeat count. The file is benchmarks/results/runtime.csv, and this run left out the 1 MB trie.

| Dataset | Method | Mean seconds | Std seconds |
| --- | --- | --- | --- |
| 10 KB | kmp | 0.000666 | 0.000056 |
| 10 KB | rk | 0.002190 | 0.000266 |
| 10 KB | sa | 0.021563 | 0.000376 |
| 10 KB | tree | 0.033104 | 0.011877 |
| 1 MB | kmp | 0.051032 | 0.003464 |
| 1 MB | rk | 0.233437 | 0.007826 |
| 1 MB | sa | 6.761709 | 0.079170 |

metrics.csv is new. runtime.csv stays as the table. Preprocessing and search use separate timers, and tracemalloc is stopped for both. KMP builds the failure table, then scans. Rabin Karp hashes the pattern and computes the window power, then slides and checks characters. The suffix array uses build_suffix_array, then binary_search. The LCP array is for its chart, outside those timers. The trie inserts every suffix, then the search lists every starting position. Each phase runs three times, and search starts after the build.

Memory comes afterward. Garbage collection runs, then tracemalloc records the peak bytes Python allocated in that call. The build peak includes the structure. The search peak is the query. Quote columns ending in tracemalloc_peak_mean_bytes, since a Task Manager figure measures something else.

Collision rate is collisions divided by hash hits, from the library at modulus 1000000007. No hash hits stores 0, and the rate can stay 0 when search really occurs. The collision chart uses moduli 101, 1009, 10007, and 100003 on 20,000 random characters, stored in collision_rates.csv. The LCP sample has 2,000 characters. The four chart names stay the same. The bar chart shows both phases on the small text. The heatmap is mean search latency, and a skipped method stays off it. Current PNG files come from that same run.

Lengths are 10,000 and 1,000,000 characters. Medium is the low end of the 1 MB to 5 MB range. KMP, Rabin Karp, and the suffix array stop above 1,000,000 characters. The trie stops above 50,000 characters, so the medium trie row is skipped and the note gives the length and the limit. The trie keeps a Python node for each piece of every suffix, and the default leaves the 1,000,000 character trie unmeasured.

From the project root with Python 3.14:

```
py -3.14 -m benchmarks.benchmark_search
```

Paste the means under the table. The README lists the save steps.

## Trade offs

KMP has a small preprocess and a fast single pattern search. It does not help when the pattern changes every query and the text is huge, because each new pattern rebuilds only a small table while the text is scanned again.

Rabin Karp spends its advantage on many patterns. A single pattern is often no faster than KMP, and a bad modulus adds verification work. Collisions are not wrong answers, because every hit is checked, but they waste time.

The suffix array is the better long term structure when the text is fixed and the patterns vary. The O(n log n) build is the cost. After that, each query is a binary search. The LCP array also supports longest common substring between two documents, which the plagiarism application uses.

The compressed trie answers substring and prefix questions directly and can count distinct substrings from edge lengths. On the 10 KB combined timer the trie took longer than the suffix array. For a one time search the trie is the wrong tool.

## Applications

plagiarism.py finds overlapping phrases with Rabin Karp, then uses the suffix array and LCP on a combined string to get a longest common substring. The similarity score is the share of unique phrase windows in the first document that also appear in the second. highlight wraps matched phrases in brackets.

dna_search.py loads a FASTA file, builds a suffix array and a suffix tree, and searches motifs. The sample file data/sample.fasta is a short synthetic gene so the path can be tested without a real genome.

autocomplete.py stores word frequencies and returns the top k completions for a prefix, sorted by count and then by the word.

## Conclusion

KMP is the right default for one pattern. Rabin Karp is the right tool for a set of patterns. A suffix array or a compressed trie is the right tool when one text will be queried many times. The project implements all four and tests the edge cases from the chapter. The combined table was measured on this PC. Split metrics are added from metrics.csv after this PC runs the updated script.

## Source

Amakobe, M. (2025). Advanced algorithms: A journey through computational problem solving. Chapter 10.

