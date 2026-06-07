"""Contiguous-subsequence matching against the index.

A query term list is rendered with the same comma-framing the index uses, and a
sequence matches when its stored terms contain that framed run as a substring.
Framing on both sides makes substring containment exactly the contiguous-
subsequence predicate: term boundaries are enforced (``2,3`` cannot match inside
``23``), adjacency is required, and signs are respected by exact text equality.
"""

from __future__ import annotations

from oeis_seek.index import Index, frame_terms
from oeis_seek.models import Match


def find_matches(terms: list[int], index: Index) -> list[Match]:
    """Find sequences whose stored terms contain ``terms`` as a contiguous run."""
    if not terms:
        return []
    framed = frame_terms(terms)  # frame_terms canonicalizes terms to int
    rows = index.find_containing(framed)
    matches: list[Match] = []
    for a_number, name, stored in rows:
        # The stored string is comma-framed, so counting commas before the run's
        # first occurrence yields its 0-based term offset (the leading comma is
        # the boundary before term 0, so it is not counted).
        offset = stored.index(framed)
        position = stored.count(",", 0, offset)
        matches.append(
            Match(a_number=a_number, name=name, matched_terms=list(terms), position=position)
        )
    return matches
