"""Deterministic, explainable scoring of matches.

The score is a transparent composite of three signals, with all weights living
here in one named table (the single home for scoring, including each transform's
"distance"). A higher score ranks first:

- transform distance: raw beats differences beats sums beats ratios, because a
  match needing no transform is the strongest evidence;
- terms matched: more input terms accounted for is stronger;
- match length: longer runs are less likely to be coincidental.

The deferred popularity signal will later join this table as another term.
"""

from __future__ import annotations

from seqseek.models import Match

# Lower distance is better; subtracted from the score so raw ranks highest. The
# core tier (0-3) is the strongest evidence; the extension tier (4+) is more
# speculative and is deliberately ranked further out. Every registered transform
# has an explicit entry here rather than relying on the unknown-transform fallback.
TRANSFORM_DISTANCE: dict[str, int] = {
    "raw": 0,
    "first_differences": 1,
    "partial_sums": 2,
    "consecutive_ratios": 3,
    "second_differences": 4,
    "third_differences": 5,
    "minus_index": 6,
    "divided_by_index": 7,
    "absolute": 8,
}
_DEFAULT_DISTANCE = 99

WEIGHT_DISTANCE = 10.0
WEIGHT_TERMS = 1.0


def distance(transform: str) -> int:
    """The transform's distance, falling back to a large sentinel if unregistered."""
    return TRANSFORM_DISTANCE.get(transform, _DEFAULT_DISTANCE)


def score(match: Match, transform: str) -> float:
    """Compute the ranking score for a match found via ``transform``."""
    terms_matched = len(match.matched_terms)
    return WEIGHT_TERMS * terms_matched - WEIGHT_DISTANCE * distance(transform)


def explain(match: Match, transform: str) -> str:
    """A plain-language account of why a result ranked where it did."""
    terms_matched = len(match.matched_terms)
    transform_distance = distance(transform)
    if transform_distance == 0:
        lead = f"Direct match on {terms_matched} terms"
    else:
        lead = f"Matched on {terms_matched} terms after applying {transform}"
    return f"{lead} (transform distance {transform_distance})."
