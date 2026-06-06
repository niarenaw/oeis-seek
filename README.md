# seqseek

[![CI](https://github.com/niarenaw/seqseek/actions/workflows/ci.yml/badge.svg)](https://github.com/niarenaw/seqseek/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/oeis-seek.svg)](https://pypi.org/project/oeis-seek/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Identify the OEIS sequence a list of integers belongs to - even when the raw
numbers are not in OEIS but a simple transform of them is.

`seqseek` works offline against a local copy of the
[OEIS](https://oeis.org/) bulk dump. You download the dump once, then look up
sequences with no network calls and no rate limits.

## Install

Install the released CLI from PyPI (the package is `oeis-seek`; it installs a
`seqseek` command):

```bash
uv tool install oeis-seek    # or: pipx install oeis-seek, or: pip install oeis-seek
```

Or work from a clone:

```bash
uv sync
```

## Usage

First, download and index the OEIS dump (one time; re-run to refresh):

```bash
seqseek update
```

Then identify a sequence:

```bash
seqseek 0,1,1,2,3,5,8,13          # -> A000045 (Fibonacci), raw match
seqseek 2,6,12,20,30,42           # -> hit via first differences
echo "1 2 6 24 120" | seqseek     # terms from stdin
seqseek 2,6,12,20 --json          # machine-readable output
seqseek 2,6,12,20 --limit 5       # cap results (default 10)
```

Terms may be comma- or whitespace-separated, passed as arguments or piped on
stdin. At least four terms are required by default (`--min-terms` lowers it).

## How it works

Three ideas do the work.

### The matcher (framed-substring contiguous match)

The index stores each sequence's terms as a comma-framed string,
`,0,1,1,2,3,5,`. A lookup frames the query the same way, `,1,2,3,5,`, and asks
which stored sequences contain that substring. Framing the run on both sides
makes substring containment exactly the contiguous-subsequence predicate OEIS
itself uses: term boundaries hold (`2,3` cannot match inside `23`), terms must be
adjacent, and signs are respected. At ~370k sequences this resolves well under a
second, so the MVP needs no inverted index.

### The transforms

Before matching, `seqseek` also tries simple transforms of your input and looks
each result up:

- **raw** - the input as given
- **first differences** - `a(n+1) - a(n)`
- **partial sums** - running totals
- **consecutive ratios** - `a(n+1) / a(n)` (later over earlier), used only when
  every ratio divides exactly, e.g. `1, 2, 6, 24` becomes `2, 3, 4`
- **higher-order differences** - first differences applied repeatedly (orders 2
  and 3)
- **a(n) - n** and **a(n) / n** - subtract or divide by the 0-based index (the
  latter integer-only)
- **absolute values** - `abs(a(n))`, to recognize a signed sequence by magnitude

Transforms live in a registry, so adding more later is one function plus one
registration.

### The ranking

Every hit gets a deterministic, explainable score. Matches needing no transform
rank above transformed ones, more matched terms rank higher, and sequences in
OEIS's curated `core` set are boosted so canonical sequences outrank obscure ones
that merely share a run. A run found near a sequence's opening is weak extra
evidence over one buried deep inside, and ties resolve by ascending A-number so
output is stable. All scoring weights live in one place, and each result tells
you which transform found it and why it ranked where it did.

## Development

Lint, format, and test:

```bash
uv run ruff check .
uv run ruff format .
uv run pytest
```

CI runs ruff and pytest on every push and pull request.

To refresh the embedded OEIS core set:

```bash
uv run python tools/generate_core_set.py
```
