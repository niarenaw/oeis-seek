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


def nth_differences(terms: list[int], order: int) -> list[int] | None:
    """The ``order``-th finite difference, computed by applying first differences repeatedly.

    This composes :func:`first_differences`, so its short-input ``None`` propagates
    naturally: an order-``k`` difference needs at least ``k + 1`` terms, and any
    intermediate result too short to difference again collapses the whole candidate
    to ``None``. Example: ``1, 4, 9, 16, 25`` has second differences ``2, 2, 2``.
    """
    result: list[int] | None = list(terms)
    for _ in range(order):
        if result is None:
            return None
        result = first_differences(result)
    return result


def minus_index(terms: list[int]) -> list[int] | None:
    """Subtract each term's 0-based position: ``a(n) - n``.

    Recognizes a sequence that is a known one shifted by its index. The index ``n``
    is the position within the (already-normalized) term list this transform
    receives. Example: ``2, 3, 5, 8`` yields ``2, 2, 3, 5``.
    """
    return [a - n for n, a in enumerate(terms)]


def divided_by_index(terms: list[int]) -> list[int] | None:
    """Divide each term by its 0-based position: ``a(n) / n`` for ``n >= 1``.

    The first position has no defined quotient (``a(0) / 0``), so it is omitted
    rather than divided by zero. As with :func:`consecutive_ratios`, the candidate
    is skipped entirely (returns ``None``) when any division is not exact, since the
    index stores only integers. Example: ``0, 2, 6, 12, 20`` yields ``2, 3, 4, 5``.
    """
    if len(terms) < 2:
        return None
    quotients: list[int] = []
    for n, a in enumerate(terms):
        if n == 0:
            continue
        if a % n != 0:
            return None
        quotients.append(a // n)
    return quotients


def absolute(terms: list[int]) -> list[int] | None:
    """Absolute values, ``abs(a(n))``: recognize a signed sequence by its magnitudes.

    This is a per-candidate transform producing one candidate; it is distinct from
    the deferred whole-search "ignore signs" mode, which would relax matching across
    the entire query rather than yielding a single magnitude candidate.
    """
    return [abs(a) for a in terms]
