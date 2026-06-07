"""Data carriers passed between the matcher, ranking, and output layers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Match:
    """A sequence whose stored terms contain the queried run as a contiguous block.

    Produced by the matcher for a single candidate term list (which may be the
    raw input or a transform of it).
    """

    a_number: str
    name: str
    matched_terms: list[int]
    # 0-based term offset of the run's first occurrence within the stored
    # sequence; an earlier offset is weak evidence the match is at the opening.
    position: int = 0


@dataclass(frozen=True)
class Result:
    """A ranked identification, the public output of :func:`oeis_seek.identify`.

    ``score`` is the raw deterministic ranking key; the CLI presents it under the
    display label "confidence". It is a sort key, not a calibrated probability.
    """

    a_number: str
    name: str
    transform: str
    score: float
    matched_terms: list[int]
    explanation: str

    @property
    def url(self) -> str:
        return f"https://oeis.org/{self.a_number}"
