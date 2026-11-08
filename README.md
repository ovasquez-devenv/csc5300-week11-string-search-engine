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

Run that last command as written. It uses seed 5300, a text of 10,000 characters, a text of 1,000,000 characters, and 3 repeats. It writes benchmarks/results/metrics.csv and benchmarks/results/collision_rates.csv, and it redraws the four PNG files in that folder. It leaves benchmarks/results/runtime.csv as the earlier combined timer run from this PC.

Safe default limits, so a longer text is skipped instead of run:

| Method | Measured up to | At the default 1,000,000 character text |
| --- | --- | --- |
| KMP | 1,000,000 characters | measured |
| Rabin Karp | 1,000,000 characters | measured |
| suffix array | 1,000,000 characters | measured |
| compressed trie | 50,000 characters | skipped |

The trie limit is 50,000 because the build keeps a Python node for each piece of every suffix, and the script rebuilds it for the preprocessing samples and again for the memory samples. The 10,000 character text is under that limit. The 1,000,000 character trie is over it, so that row says skipped and gives the length and the limit. KMP, Rabin Karp, and the suffix array use a 1,000,000 character limit. The default command does not go past those limits. The medium suffix array is the slow part, because the script rebuilds it for the preprocessing samples and again for the memory samples.

Every search, including the trie, returns the list of starting positions. Chart titles name the generator, the seed, the pattern, and the quantity. The collision chart uses a separate random ACGT text. The LCP chart is one build on a 2,000 character englishish sample.

## Put the new numbers in the report

1. Run `py -3.14 -m benchmarks.benchmark_search` from the project folder. Wait until it prints the metrics path. Let it finish. The 1,000,000 character suffix array is the long part, and the memory repeats are slower because tracemalloc is on only for those samples. The trie row for that text will say skipped. That is the expected default.
2. Open benchmarks/results/metrics.csv. Each row with status ok has a mean and a population standard deviation for preprocessing seconds, search seconds, and both tracemalloc peaks. Rabin Karp rows also have the collision rate.
3. Open analysis/chapter10_report.md. Leave the combined time table as it is. Those seven numbers are the earlier run in runtime.csv.
4. Under that table, add the new means from metrics.csv. Keep the column names next to the digits so a reader can see preprocessing, search, and the tracemalloc peak. Copy the digits from the CSV. For the skipped trie row, copy the note and leave the time cells blank.
5. This run replaces the four PNG files. Read the title on each picture: it names the text, the seed, and the quantity. runtime_comparison.png shows preprocessing beside search on the small text from this run. The heatmap shows search latency for methods measured on both sizes, so the trie is absent there. The collision chart is the ACGT modulus sweep. The LCP chart is one 2,000 character sample. The collision numbers are also in collision_rates.csv.
6. Save the report, both CSV files, and the four PNG files together so the words match the files.

## What the metric names mean

Preprocessing time is the setup before the lookup. Search latency is the lookup after that setup already exists. The mean is the average of the three repeats. The standard deviation is the population kind from statistics.pstdev, the same kind already used in runtime.csv. A small standard deviation means the repeats landed close together.

The tracemalloc peak is the highest number of bytes Python allocated during that one call. The preprocessing peak includes the build. The search peak is the lookup. Quote the column name when you write the number down, because a Task Manager reading is a different measurement.

The Rabin Karp collision rate is the share of hash hits that failed the character check. The characters are still compared, so a collision is extra work and the list of matches stays correct. On the main texts the modulus is 1000000007, so that rate can sit at 0. The collision chart uses smaller moduli, which lets the rate rise.

## Layout

core holds the four matchers and the facade. applications holds plagiarism, DNA, and autocomplete. visualization holds the two plot scripts. utils holds loaders, the rolling hash, and seeded generators. analysis/chapter10_report.md is the writeup.
