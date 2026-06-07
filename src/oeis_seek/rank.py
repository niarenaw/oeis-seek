"""Deterministic, explainable scoring of matches.

The score is a transparent composite of independent signals, with all weights
living here in one named table (the single home for scoring, including each
transform's "distance"). A higher score ranks first:

- transform distance: raw beats differences beats sums beats ratios, because a
  match needing no transform is the strongest evidence;
- terms matched: more input terms accounted for is stronger;
- popularity: a sequence in OEIS's curated ``core`` set is far more likely to be
  the one a user means than an obscure sequence that merely shares a run, so core
  membership adds a small boost - enough to break a tie between equally strong
  matches, but never enough to override a clearly stronger raw match;
- position: a run found at a sequence's opening is stronger evidence than one
  buried deep inside it, so an earlier offset adds a smaller, bounded bonus that
  only refines otherwise-equal results.

The popularity boost is set strictly larger than the largest possible position
bonus, so popularity always wins when the two disagree, and below the per-term
weight, so a genuinely longer match still outranks a merely-more-popular one.
"""

from __future__ import annotations

import importlib.resources

from oeis_seek.models import Match


def _load_core_set() -> frozenset[str]:
    """Load the packaged OEIS core A-numbers, skipping the provenance header."""
    text = (
        importlib.resources.files("oeis_seek")
        .joinpath("data/core_sequences.txt")
        .read_text(encoding="utf-8")
    )
    return frozenset(
        stripped
        for line in text.splitlines()
        if (stripped := line.strip()) and not stripped.startswith("#")
    )


_CORE_SET = _load_core_set()


def is_core(a_number: str) -> bool:
    """Whether ``a_number`` is in OEIS's curated core set (packaged static data)."""
    return a_number in _CORE_SET


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
WEIGHT_POPULARITY = 0.5
# The position bonus is WEIGHT_POSITION / (1 + position), so it lies in
# (0, WEIGHT_POSITION]. Keeping it below WEIGHT_POPULARITY guarantees popularity
# wins whenever the two disagree, and below WEIGHT_TERMS keeps it a tie-level
# refinement that never overrides an extra matched term.
WEIGHT_POSITION = 0.25


def distance(transform: str) -> int:
    """The transform's distance, falling back to a large sentinel if unregistered."""
    return TRANSFORM_DISTANCE.get(transform, _DEFAULT_DISTANCE)


def score(match: Match, transform: str) -> float:
    """Compute the ranking score for a match found via ``transform``.

    ``match.position`` is the offset the matcher reported; for derived transforms
    it measures earliness within the derived run rather than the canonical
    sequence offset, so it contributes only a small tie-level refinement.
    """
    terms_matched = len(match.matched_terms)
    base = WEIGHT_TERMS * terms_matched - WEIGHT_DISTANCE * distance(transform)
    popularity = WEIGHT_POPULARITY if is_core(match.a_number) else 0.0
    position_bonus = WEIGHT_POSITION / (1 + match.position)
    return base + popularity + position_bonus


def explain(match: Match, transform: str) -> str:
    """A plain-language account of why a result ranked where it did."""
    terms_matched = len(match.matched_terms)
    transform_distance = distance(transform)
    if transform_distance == 0:
        lead = f"Direct match on {terms_matched} terms"
    else:
        lead = f"Matched on {terms_matched} terms after applying {transform}"
    return f"{lead} (transform distance {transform_distance})."
