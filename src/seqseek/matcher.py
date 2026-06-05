"""Contiguous-subsequence matching against the index.

A query term list is rendered with the same comma-framing the index uses, and a
sequence matches when its stored terms contain that framed run as a substring.
Framing on both sides makes substring containment exactly the contiguous-
subsequence predicate: term boundaries are enforced (``2,3`` cannot match inside
``23``), adjacency is required, and signs are respected by exact text equality.
"""

from __future__ import annotations

from seqseek.index import Index, frame_terms
from seqseek.models import Match


def find_matches(terms: list[int], index: Index) -> list[Match]:
    """Find sequences whose stored terms contain ``terms`` as a contiguous run."""
    if not terms:
        return []
    framed = frame_terms(terms)  # frame_terms canonicalizes terms to int
    rows = index.find_containing(framed)
    return [Match(a_number=a, name=name, matched_terms=list(terms)) for a, name, _ in rows]
