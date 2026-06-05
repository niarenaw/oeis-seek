# seqseek

Identify the OEIS sequence a list of integers belongs to - even when the raw
numbers are not in OEIS but a simple transform of them is.

`seqseek` works offline against a local copy of the
[OEIS](https://oeis.org/) bulk dump. You download the dump once, then look up
sequences with no network calls and no rate limits.

## Install

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

Transforms live in a registry, so adding more later is one function plus one
registration.

### The ranking

Every hit gets a deterministic, explainable score: matches needing no transform
rank above transformed ones, more matched terms rank higher, and the scoring
weights live in one place. Each result tells you which transform found it and
why it ranked where it did.

## Development

```bash
uv run pytest
```
