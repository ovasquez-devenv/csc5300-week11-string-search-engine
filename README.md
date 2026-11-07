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

The benchmark command uses seed 5300, a text of 10,000 characters, a text of 1,000,000 characters, and 3 repeats. It writes benchmarks/results/metrics.csv and benchmarks/results/collision_rates.csv, and it redraws the four PNG files in that folder: runtime_comparison.png, collision_analysis.png, sa_lcp_stats.png, and heatmap_dataset_sizes.png. The script leaves benchmarks/results/runtime.csv as the earlier combined timer run from this PC.

The compressed trie is included on both default lengths. The tree max chars setting defaults to 1000000. A longer text gets a metrics row with status skipped, and the note states the length and the limit. KMP, Rabin Karp, and the suffix array are still measured at that longer length. An optional longer trie run looks like this:

```
py -3.14 -m benchmarks.benchmark_search --tree-max-chars 5000000 --medium 5000000
```

The required medium text for the writeup is the default 1,000,000 characters.

## Put the new numbers in the report

1. Run the Python 3.14 command above on your PC. Wait until it prints the metrics path. The 1 MB suffix array and the 1 MB trie take longer than the small text. The memory pass is slower because tracemalloc is on for those samples only.
2. Open benchmarks/results/metrics.csv. Each row with status ok has a mean and a population standard deviation for preprocessing seconds, search seconds, and both tracemalloc peaks. Rabin Karp rows also have the collision rate.
3. Open analysis/chapter10_report.md. Leave the combined time table as it is. Those seven numbers are the earlier run in runtime.csv.
4. Under that table, add the new means from metrics.csv. Keep the column names next to the digits so a reader can see preprocessing, search, and the tracemalloc peak. Copy the digits from the CSV. If a row says skipped, copy the note and leave the time cells blank.
5. This run replaces the four PNG files. runtime_comparison.png shows preprocessing beside search on the small text. The heatmap shows search latency. The collision chart and the LCP chart stay the same kinds of plots, and the collision numbers are also in collision_rates.csv.
6. Save the report, both CSV files, and the four PNG files together so the words match the files.

## What the metric names mean

Preprocessing time is the setup before the lookup. Search latency is the lookup after that setup already exists. The mean is the average of the three repeats. The standard deviation is the population kind from statistics.pstdev, the same kind already used in runtime.csv. A small standard deviation means the repeats landed close together.

The tracemalloc peak is the highest number of bytes Python allocated during that one call. The preprocessing peak includes the build. The search peak is the lookup. Quote the column name when you write the number down, because a Task Manager reading is a different measurement.

The Rabin Karp collision rate is the share of hash hits that failed the character check. The characters are still compared, so a collision is extra work and the list of matches stays correct. On the main texts the modulus is 1000000007, so that rate can sit at 0. The collision chart uses smaller moduli, which lets the rate rise.

## Layout

core holds the four matchers and the facade. applications holds plagiarism, DNA, and autocomplete. visualization holds the two plot scripts. utils holds loaders, the rolling hash, and seeded generators. analysis/chapter10_report.md is the writeup.
