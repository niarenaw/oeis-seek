"""The ``seqseek`` command: a thin formatter over :func:`seqseek.core.identify`.

Input parsing, the minimum-terms rule, input bounds, output formatting, and the
``update`` subcommand all live here. Identification itself is delegated to the
library core, so the deferred web/API/MCP surfaces reuse that core unchanged.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

from seqseek import core, download, index
from seqseek.models import Result

DEFAULT_MIN_TERMS = 4
DEFAULT_LIMIT = 10
MAX_TERMS = 10_000
MAX_TERM_DIGITS = 5_000

_TOKEN_SPLIT = re.compile(r"[,\s]+")


def parse_terms(raw: str) -> list[int]:
    """Parse comma- and/or whitespace-separated integers, with sane bounds."""
    tokens = [t for t in _TOKEN_SPLIT.split(raw.strip()) if t]
    if len(tokens) > MAX_TERMS:
        raise ValueError(f"too many terms (max {MAX_TERMS})")
    terms: list[int] = []
    for token in tokens:
        if len(token.lstrip("-")) > MAX_TERM_DIGITS:
            raise ValueError(f"term too large (max {MAX_TERM_DIGITS} digits)")
        terms.append(int(token))
    return terms


def _read_input(args_terms: list[str]) -> str:
    if args_terms:
        return " ".join(args_terms)
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return ""


def format_human(results: list[Result], snapshot: str) -> str:
    lines: list[str] = []
    if not results:
        lines.append("No matches found.")
    for i, r in enumerate(results, 1):
        preview = ", ".join(str(t) for t in r.matched_terms[:8])
        lines.append(f"{i}. {r.a_number}  {r.name}")
        lines.append(f"   transform: {r.transform}   confidence: {r.score:g}")
        lines.append(f"   matched: {preview}")
        lines.append(f"   {r.url}")
        lines.append(f"   {r.explanation}")
    lines.append("")
    lines.append(f"(OEIS snapshot: {snapshot})")
    return "\n".join(lines)


def format_json(results: list[Result], snapshot: str) -> str:
    payload = {
        "snapshot": snapshot,
        "results": [
            {
                "a_number": r.a_number,
                "name": r.name,
                "transform": r.transform,
                "confidence": r.score,
                "matched_terms": r.matched_terms,
                "url": r.url,
                "explanation": r.explanation,
            }
            for r in results
        ],
    }
    return json.dumps(payload, indent=2)


def _run_update() -> int:
    print("Downloading OEIS dump ...", file=sys.stderr)
    download.download()
    print("Building index ...", file=sys.stderr)
    count = index.build()
    handle = index.open_index()
    try:
        print(f"Indexed {count} sequences (snapshot: {handle.snapshot_date}).")
    finally:
        handle.close()
    return 0


def _run_lookup(args: argparse.Namespace) -> int:
    raw = _read_input(args.terms)
    if not raw.strip():
        print("No terms given. Example: seqseek 2,6,12,20,30", file=sys.stderr)
        return 2
    try:
        terms = parse_terms(raw)
    except ValueError as exc:
        print(f"Invalid input: {exc}", file=sys.stderr)
        return 2

    if len(terms) < args.min_terms:
        print(
            f"Need at least {args.min_terms} terms (got {len(terms)}). "
            f"Use --min-terms to lower the threshold.",
            file=sys.stderr,
        )
        return 2

    try:
        handle = index.open_index()
    except FileNotFoundError:
        print("No local data - run `seqseek update` first.", file=sys.stderr)
        return 3

    try:
        results = core.identify(terms, handle, limit=args.limit)
        snapshot = handle.snapshot_date
    finally:
        handle.close()

    print(format_json(results, snapshot) if args.json else format_human(results, snapshot))
    return 0 if results else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="seqseek",
        description="Identify the OEIS sequence a list of integers belongs to.",
        epilog="Run `seqseek update` to download and index the OEIS bulk dump.",
    )
    parser.add_argument("terms", nargs="*", help="integer terms (comma/space separated)")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="max results")
    parser.add_argument(
        "--min-terms", type=int, default=DEFAULT_MIN_TERMS, help="minimum input terms"
    )
    parser.add_argument("--json", action="store_true", help="emit JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "update":
        return _run_update()
    args = build_parser().parse_args(argv)
    return _run_lookup(args)


if __name__ == "__main__":
    raise SystemExit(main())
