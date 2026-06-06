"""The transform registry: the single extension point for the engine.

Adding a post-MVP transform is one function in ``builtin.py`` (or a new tier
module) plus one entry here. The registry maps a transform name to its callable
only; scoring weights live in :mod:`seqseek.rank` so the two concerns stay
separate. ``core.identify`` iterates this registry rather than naming transforms,
so a newly registered transform participates without touching the fan-out.
"""

from __future__ import annotations

import functools
from collections.abc import Callable

from seqseek.transforms import builtin

Transform = Callable[[list[int]], "list[int] | None"]

# Difference orders are bound here so each registry entry keeps the single-argument
# Transform contract; adding order 4 is one more line plus its rank.TRANSFORM_DISTANCE.
REGISTRY: dict[str, Transform] = {
    "raw": builtin.raw,
    "first_differences": builtin.first_differences,
    "partial_sums": builtin.partial_sums,
    "consecutive_ratios": builtin.consecutive_ratios,
    "second_differences": functools.partial(builtin.nth_differences, order=2),
    "third_differences": functools.partial(builtin.nth_differences, order=3),
    "minus_index": builtin.minus_index,
    "divided_by_index": builtin.divided_by_index,
    "absolute": builtin.absolute,
}
