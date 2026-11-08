# Fast Pattern Matching

Omar Vasquez
Concordia University Texas
CSC 5300 Week 11

## Executive summary

This project implements four ways to find a pattern inside a text: Knuth Morris Pratt (KMP), Rabin Karp, a suffix array, and a compressed suffix tree. KMP is the default for one pattern. It preprocesses the pattern into a failure table and never moves backward in the text. Rabin Karp hashes a sliding window and is the better fit when many patterns share one pass. The suffix array and the suffix tree cost more to build and pay off when the same text is queried many times.

The code lives in a Python package named StringSearchEngine. Tests cover the failure table, repeated characters, a pattern longer than the text, hash collisions that must be verified, suffix array order, and tree queries. Seed 5300 produced the combined times below on this PC. The split times, peak bytes, and collision counts were measured on this PC with Python 3.14.7.

## String matching complexity

The naive search tries the pattern at every position. If the text length is n and the pattern length is m, the worst case is about n times m character comparisons.

KMP removes that waste. Section 10.3 of Amakobe describes the failure function. For each position in the pattern, the table stores the length of the longest proper prefix that is also a suffix. Building the table is linear in m. The search walks the text once and jumps with the table on a mismatch. Total time is O(n + m). Space is O(m) for the table.

Rabin Karp, in section 10.4, turns the pattern into a number. A window of length m slides across the text and the hash updates in constant time. A matching hash is only a candidate, so the characters are still compared. Expected time is O(n + m). The worst case is O(n m) when collisions keep happening. Many patterns can share one pass.

A suffix array lists every suffix start in sorted order. The prefix doubling build used here is O(n log n). Kasai's algorithm builds the LCP array in linear time, and a query is a binary search. A suffix tree stores the same suffixes in a compressed trie, so substring and prefix queries walk the edges.

## Implementation details

KMP lives in core/kmp.py. For ABABD the failure table is 0, 0, 1, 2, 0, as in section 10.3.2. For AABAAB it is 0, 1, 0, 1, 2, 3. kmp_search returns every start. An empty pattern, or a pattern longer than the text, returns an empty list. Overlaps stay, as when AAAAA is searched for AA.

Rabin Karp lives in core/rabin_karp.py. The base is 256 and the modulus is 1000000007. Every hash hit is checked against the characters, and the object counts hits and collisions.

The suffix array in core/suffix_array.py uses prefix doubling and Kasai's LCP, and binary_search returns the matching starts. The suffix tree in core/suffix_tree.py is a compressed trie built by inserting every suffix. It can test a substring, list prefixes, find a longest repeated substring, and count distinct substrings.

StringSearchEngine(text).find(pattern, method) accepts kmp, rk, sa, or tree.

## Benchmark analysis

The first table is the earlier run on this PC. One timer covered the whole call, with three repeats, seed 5300, and the pattern search. The mean is statistics.mean. The std is statistics.pstdev, the population kind, which divides by three. Those seven rows are in benchmarks/results/runtime.csv and stay as measured. That run left out the 1 MB trie.

| Dataset | Method | Mean seconds | Std seconds |
| --- | --- | --- | --- |
| 10 KB | kmp | 0.000666 | 0.000056 |
| 10 KB | rk | 0.002190 | 0.000266 |
| 10 KB | sa | 0.021563 | 0.000376 |
| 10 KB | tree | 0.033104 | 0.011877 |
| 1 MB | kmp | 0.051032 | 0.003464 |
| 1 MB | rk | 0.233437 | 0.007826 |
| 1 MB | sa | 6.761709 | 0.079170 |

The split rows were measured on this PC with Python 3.14.7, seed 5300, pattern search, and three repeats. 10 KB is 10000 characters and 1 MB is 1000000 characters. Setup and search used separate timers, with tracemalloc stopped. Memory came later. After garbage collection, tracemalloc stored the peak bytes Python allocated during that call. Setup peak includes the build. Search peak is the query only, with the structure already built. The byte std is the same population kind. A Task Manager figure is a different measurement.

KMP setup is the failure table, and the search scans the text. Rabin Karp setup is the pattern hash and the window power, and the search slides the window. Suffix array setup builds the array, and the search is binary search. The LCP array stays in its own chart. Trie setup inserts every suffix, and every search lists starting positions. The 1000000 character trie was skipped, above the 50000 character limit, so that row has no times.

Split times, in seconds:

```
dataset method setup_mean setup_std search_mean search_std
10KB kmp 0.000002533 0.000001901 0.000504000 0.000004830
10KB rk 0.000008667 0.000007193 0.002213100 0.000245433
10KB sa 0.018412467 0.000190463 0.000028133 0.000020888
10KB tree 0.022238167 0.000747761 0.000052667 0.000027521
1MB kmp 0.000002633 0.000002877 0.046856067 0.000577501
1MB rk 0.000005333 0.000005008 0.197431533 0.006002717
1MB sa 6.539244333 0.032478870 0.002394300 0.000759526
1MB tree skipped
```

Peak Python allocation, in bytes:

```
dataset method setup_peak_mean setup_peak_std search_peak_mean search_peak_std
10KB kmp 168 0 5336 0
10KB rk 1270.667 19.956 5636 0
10KB sa 1505432 0 2790 0
10KB tree 3700837.333 9.978 6560 0
1MB kmp 168 0 508056 0
1MB rk 1068 13.064 508366.667 15.085
1MB sa 151987288 0 159206 0
1MB tree skipped
```

The older row used one clock for both phases, so it is a different measurement from a setup cell plus a search cell. KMP setup is a few microseconds and its std is about as large as the mean, so that clock is noisy. The large peaks are the 1 MB suffix array build and the 10 KB trie build.

The collision rate is collisions divided by hash hits. It is the share of hash hits that failed the character check. Windows with no hash hit stay outside the rate. Modulus 1000000007 gave 129 hits and 0 collisions on 10 KB, and 12506 hits and 0 collisions on 1 MB, so both rates are 0. The std is 0 because the three repeats used the same seeded text. That 0 is the spread of this run.

The modulus rows used a separate 20000 character ACGT text, pattern GGTGCTTA, seed 5300, and three repeats. They are collision_rates.csv.

```
modulus hash_hits collisions rate rate_std
101 196 194 0.989796 0
1009 18 16 0.888889 0
10007 4 2 0.500000 0
100003 2 0 0 0
```

A smaller modulus fails the character check more often. That rate std is also 0, from repeating the seeded text. The LCP chart is one 2000 character sample and sits outside these rows.

This PC drew the four chart files from these split measurements. The bar chart is setup beside search on the 10 KB text, and the heatmap is mean search time with the trie left off. Pictures of the first table are a separate drawing.

## Trade offs

KMP has a small setup and a fast scan for one pattern. A new pattern still walks the whole text.

Rabin Karp pays off when many patterns share a pass. One pattern is often no faster than KMP, and a small modulus adds checks. Every hash hit is still verified.

The suffix array fits a fixed text and many patterns. The O(n log n) build is the cost, and each later query is a binary search. The LCP array also feeds the plagiarism longest common substring.

The trie answers substring and prefix questions from its edges. In the split table its 10 KB build is a little slower than the suffix array build, and the 1 MB trie was skipped. For one search it is the wrong tool.

## Applications

plagiarism.py finds shared phrases with Rabin Karp, then uses the suffix array and LCP for a longest common substring. The score is the share of phrase windows from the first document that also appear in the second.

dna_search.py loads data/sample.fasta, a short synthetic gene, and searches motifs with the suffix array and the suffix tree.

autocomplete.py returns the top completions for a prefix, by count and then by the word.

## Conclusion

KMP is the right default for one pattern. Rabin Karp is the right tool for a set of patterns. A suffix array or a compressed trie is the right tool when one text will be queried many times. The combined table and the split tables were measured on this PC. The 1 MB trie row records the 50000 character limit and has no time.

## Source

Amakobe, M. (2025). Advanced algorithms: A journey through computational problem solving. Chapter 10.

