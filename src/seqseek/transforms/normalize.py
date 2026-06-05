"""Input normalization applied before matching.

OEIS strips leading 0s and 1s when searching, because those prefixes are weakly
discriminating and frequently absent from the canonical offset of a sequence.
Mirroring that behavior materially improves the hit rate.

Signs are respected by default simply by leaving them untouched. The deferred
"ignore signs" mode is the only place sign manipulation will eventually live.
"""

from __future__ import annotations


def strip_leading_zeros_and_ones(terms: list[int]) -> list[int]:
    """Drop a leading run of 0s and 1s, preserving at least the final term.

    A sequence made entirely of 0s and 1s is returned with its last term intact
    so that normalization never yields an empty list.
    """
    index = 0
    while index < len(terms) - 1 and terms[index] in (0, 1):
        index += 1
    return terms[index:]
