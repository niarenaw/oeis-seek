"""Generate the embedded OEIS core-set data file.

Run once at authoring time to refresh ``src/seqseek/data/core_sequences.txt``
from OEIS's ``keyword:core`` query. The file is a committed, reviewed artifact;
this script exists so the refresh is reproducible and validated rather than a
one-off manual fetch. It is not shipped in the wheel and never runs at lookup
time.

The fetch is validated before anything is written: the HTTP status must be 200,
the union of the two windows must reconcile with the total OEIS reports, the final
count must fall inside a plausible band, and every entry must be a canonical
A-number. A truncated or malformed fetch therefore fails loudly rather than
freezing a partial list into the package.

OEIS blocks anonymous pagination past ``start=100`` (a login wall), so a single
query reaches only the first 110 results while the core set is larger. To cover
the whole set, this fetches the first window sorted by A-number ascending and the
first window sorted descending, then unions them. The two windows overlap in the
middle, so the union is complete as long as the total fits within their combined
reach.

Usage:
    uv run python tools/generate_core_set.py
"""

from __future__ import annotations

import json
import re
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from seqseek.download import USER_AGENT

SEARCH_URL = "https://oeis.org/search"
QUERY = "keyword:core"
MIN_EXPECTED = 160
MAX_EXPECTED = 250
PAGE_LIMIT = 100  # OEIS serves anonymous results only for start <= 100
WINDOW_REACH = PAGE_LIMIT + 10  # results retrievable in one sort direction
TWO_WINDOW_REACH = 2 * WINDOW_REACH  # ceiling the asc+desc union can cover
OUTPUT = Path(__file__).resolve().parents[1] / "src" / "seqseek" / "data" / "core_sequences.txt"

_A_NUMBER = re.compile(r"^A\d{6}$")
_TOTAL = re.compile(r"Showing\s+\d+-\d+\s+of\s+(\d+)")


def _fetch(url: str) -> tuple[int, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.status, response.read().decode("utf-8")


def _reported_total() -> int:
    """The total result count OEIS reports for the query, used to detect truncation."""
    status, body = _fetch(f"{SEARCH_URL}?q={QUERY}&fmt=text&start=0")
    if status != 200:
        raise RuntimeError(f"OEIS returned HTTP {status} for the count query")
    match = _TOTAL.search(body)
    if not match:
        raise RuntimeError("could not parse the result count from the OEIS response")
    return int(match.group(1))


def _fetch_window(sort: str) -> list[str]:
    """Collect one sort direction's reachable window (start 0..PAGE_LIMIT)."""
    collected: list[str] = []
    start = 0
    while start <= PAGE_LIMIT:
        status, body = _fetch(f"{SEARCH_URL}?q={QUERY}&fmt=json&sort={sort}&start={start}")
        if status != 200:
            raise RuntimeError(f"OEIS returned HTTP {status} at sort={sort} start={start}")
        body = body.strip()
        if not body or not body.startswith("["):  # login wall or empty page
            break
        page = json.loads(body)
        if not page:
            break
        collected.extend(f"A{int(entry['number']):06d}" for entry in page)
        start += len(page)
    return collected


def fetch_core_a_numbers() -> list[str]:
    """Union the ascending and descending windows, reconciling against the total."""
    total = _reported_total()
    if total > TWO_WINDOW_REACH:
        raise RuntimeError(
            f"core-set total {total} exceeds the two-window reach {TWO_WINDOW_REACH}; "
            "the union can no longer be guaranteed complete"
        )
    union = set(_fetch_window("number")) | set(_fetch_window("-number"))
    if len(union) != total:
        raise RuntimeError(f"incomplete fetch: unioned {len(union)} of {total} reported")
    return sorted(union)


def main() -> int:
    unique = sorted(set(fetch_core_a_numbers()))
    count = len(unique)
    if not all(_A_NUMBER.match(a) for a in unique):
        raise RuntimeError("fetched an entry that is not a canonical A-number")
    if not MIN_EXPECTED <= count <= MAX_EXPECTED:
        raise RuntimeError(
            f"core-set count {count} outside expected band [{MIN_EXPECTED}, {MAX_EXPECTED}]"
        )

    retrieved = datetime.now(UTC).date().isoformat()
    header = (
        "# OEIS core sequences (keyword:core)\n"
        f"# Source: {SEARCH_URL}?q={QUERY}\n"
        f"# Retrieved: {retrieved}\n"
        f"# Count: {count}\n"
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(header + "\n".join(unique) + "\n", encoding="utf-8")
    print(f"Wrote {count} core A-numbers to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
