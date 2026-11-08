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

The trie is Ukkonen's compressed trie and the full PC run is already in benchmarks/results/pending_rerun. Do not rerun it. The four PNG files were missing from that commit because .gitignore ignores *.png and only un-ignores benchmarks/results/*.png, not the pending_rerun folder. Charts can be drawn from the saved CSV with no new timing:

```
py -3.14 -m benchmarks.benchmark_search --plot-only --metrics benchmarks/results/pending_rerun/metrics.csv --collisions benchmarks/results/pending_rerun/collision_rates.csv
```

That writes the four PNG files next to those CSV files. It does not change the CSV files or the older files in benchmarks/results. Do not pass --allow-replace.

Every search, including the trie, returns the list of starting positions. Chart titles name the generator, the seed, the pattern, and the quantity. The collision chart uses a separate random ACGT text. The LCP chart is one build on a 2,000 character englishish sample.

## Charts already measured

The report uses benchmarks/results/pending_rerun/metrics.csv and collision_rates.csv. Leave runtime.csv, the older metrics.csv, and collision_rates.csv in benchmarks/results unchanged. If pull stops because four PNG files already sit in pending_rerun, move those local pictures aside and pull. Do not rerun the benchmark. If you want those exact local pictures in git instead of the plots made from the CSV, use this after the ignore fix, and do not force-add any other file:

```
git add -f benchmarks/results/pending_rerun/runtime_comparison.png benchmarks/results/pending_rerun/collision_analysis.png benchmarks/results/pending_rerun/sa_lcp_stats.png benchmarks/results/pending_rerun/heatmap_dataset_sizes.png
```

## What the metric names mean

Preprocessing time is the setup before the lookup. Search latency is the lookup after that setup already exists. The mean is the average of the three repeats. The standard deviation is the population kind from statistics.pstdev, the same kind already used in runtime.csv. A small standard deviation means the repeats landed close together.

The tracemalloc peak is the highest number of bytes Python allocated during that one call. The preprocessing peak includes the build. The search peak is the lookup. Quote the column name when you write the number down, because a Task Manager reading is a different measurement.

The Rabin Karp collision rate is the share of hash hits that failed the character check. The characters are still compared, so a collision is extra work and the list of matches stays correct. On the main texts the modulus is 1000000007, so that rate can sit at 0. The collision chart uses smaller moduli, which lets the rate rise.

## Layout

core holds the four matchers and the facade. applications holds plagiarism, DNA, and autocomplete. visualization holds the two plot scripts. utils holds loaders, the rolling hash, and seeded generators. analysis/chapter10_report.md is the writeup.
