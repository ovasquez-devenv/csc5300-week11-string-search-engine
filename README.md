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
python -m benchmarks.benchmark_search
```

The benchmark uses seed 5300 and writes CSV plus four PNG files under benchmarks/results.

## Layout

core holds the four matchers and the facade. applications holds plagiarism, DNA, and autocomplete. visualization holds the two plot scripts. utils holds loaders, the rolling hash, and seeded generators. analysis/chapter10_report.md is the writeup.
