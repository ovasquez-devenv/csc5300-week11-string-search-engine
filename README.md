# StringSearchEngine

CSC 5300 Week 11 Fast Pattern Matching. Python implementations of Knuth Morris Pratt, Rabin Karp, a suffix array, and a compressed suffix tree.

## What it does

Search a text for a pattern with four methods. KMP builds a failure table and never moves backward in the text. Rabin Karp uses a rolling hash and can search many patterns in one pass. The suffix array is built with prefix doubling and supports binary search plus a Kasai LCP array. The suffix tree is a compressed trie with substring, prefix, longest repeated substring, and distinct substring count.

## Install

```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

From the project root:

```
python -m pytest tests
py -3.14 -m benchmarks.benchmark_search
```

On Windows, use Python 3.14 from the project folder in PowerShell:

```
py -3.14 -m venv .venv
.venv\Scripts\Activate.ps1
py -3.14 -m pip install -r requirements.txt
py -3.14 -m benchmarks.benchmark_search
```

The saved files in benchmarks/results are the earlier PC run. A new run is sent to benchmarks/results/pending_rerun when those files are present, so runtime.csv, metrics.csv, collision_rates.csv, and the four PNG files stay put.

The trie is now Ukkonen's compressed trie and is measured through 1,000,000 characters. KMP, Rabin Karp, and the suffix array keep that same limit. Only the trie rows in the saved metrics.csv are from the older insertion trie. Remeasure just the trie, without touching the saved files:

```
py -3.14 -m benchmarks.benchmark_search --methods tree --output-dir benchmarks\results\pending_rerun
```

That uses seed 5300, 10,000 and 1,000,000 characters, and 3 repeats. The 1,000,000 character build is the slow part. Do not pass --allow-replace unless you intend to overwrite the saved measurements.

Every search, including the trie, returns the list of starting positions. Chart titles name the generator, the seed, the pattern, and the quantity. The collision chart uses a separate random ACGT text. The LCP chart is one build on a 2,000 character englishish sample.

## After the trie rerun

1. Run the tree command above from the project folder. Wait until it prints the pending_rerun path.
2. Open benchmarks/results/pending_rerun/metrics.csv. It should contain a 10000 character tree row and a 1000000 character tree row, both with status ok, and the note should say ukkonen-v1.
3. In analysis/chapter10_report.md, leave the first combined table and the KMP, Rabin Karp, suffix array, and collision numbers as they are. Replace only the trie lines that are labeled as the earlier insertion trie. Copy the new setup mean, setup std, search mean, search std, and both peak byte pairs from the pending file. Say those cells are ukkonen-v1 measured on this PC.
4. The bar chart in benchmarks/results still includes the earlier trie. The new bar chart, if you want one picture with all four methods, requires a full rerun into pending_rerun with no --methods filter. Do not copy that picture over the saved PNG until you mean to replace it. The heatmap, collision chart, and LCP chart in benchmarks/results do not use the trie and can stay.
5. Do not edit runtime.csv, the saved metrics.csv, or collision_rates.csv while copying numbers into the report.

## What the metric names mean

Preprocessing time is the setup before the lookup. Search latency is the lookup after that setup already exists. The mean is the average of the three repeats. The standard deviation is the population kind from statistics.pstdev, the same kind already used in runtime.csv. A small standard deviation means the repeats landed close together.

The tracemalloc peak is the highest number of bytes Python allocated during that one call. The preprocessing peak includes the build. The search peak is the lookup. Quote the column name when you write the number down, because a Task Manager reading is a different measurement.

The Rabin Karp collision rate is the share of hash hits that failed the character check. The characters are still compared, so a collision is extra work and the list of matches stays correct. On the main texts the modulus is 1000000007, so that rate can sit at 0. The collision chart uses smaller moduli, which lets the rate rise.

## Layout

core holds the four matchers and the facade. applications holds plagiarism, DNA, and autocomplete. visualization holds the two plot scripts. utils holds loaders, the rolling hash, and seeded generators. analysis/chapter10_report.md is the writeup.
