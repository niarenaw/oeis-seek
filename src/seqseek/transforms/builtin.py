"""The core-tier transforms.

Each transform maps an input term list to a candidate term list to look up, or
returns ``None`` when it cannot produce a meaningful integer candidate. Every
transform operates on Python ``int`` so arbitrary-precision terms flow through
losslessly.
"""

from __future__ import annotations

import itertools


def raw(terms: list[int]) -> list[int] | None:
    """The identity transform: look the input up as given."""
    return list(terms)


def first_differences(terms: list[int]) -> list[int] | None:
    """Consecutive differences ``a(n+1) - a(n)``.

    Requires at least two terms to produce a difference.
    """
    if len(terms) < 2:
        return None
    return [b - a for a, b in zip(terms, terms[1:], strict=False)]


def partial_sums(terms: list[int]) -> list[int] | None:
    """Running totals ``sum(a(0)..a(n))``."""
    if not terms:
        return None
    return list(itertools.accumulate(terms))


def consecutive_ratios(terms: list[int]) -> list[int] | None:
    """Ratios of consecutive terms, later over earlier: ``a(n+1) / a(n)``.

    The index stores integer sequences, so a ratio candidate is only meaningful
    when every consecutive ratio divides exactly. Otherwise the transform is
    skipped rather than coerced to a lossy value. Example: ``1, 2, 6, 24`` yields
    ``2, 3, 4``.
    """
    if len(terms) < 2:
        return None
    ratios: list[int] = []
    for a, b in zip(terms, terms[1:], strict=False):
        if a == 0 or b % a != 0:
            return None
        ratios.append(b // a)
    return ratios
