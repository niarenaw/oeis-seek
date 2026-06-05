"""The identification fan-out: the single public entry point.

``identify`` normalizes the input, runs every registered transform, matches each
candidate against the index, dedupes the same sequence to its best-scoring hit,
and returns ranked results. Keeping the fan-out and dedup here (rather than in the
ranking module) gives the transform loop one home and keeps ranking a pure
function. Every future surface (CLI today; web/API/MCP later) calls this.
"""

from __future__ import annotations

from seqseek import rank
from seqseek.index import Index
from seqseek.matcher import find_matches
from seqseek.models import Result
from seqseek.transforms import REGISTRY
from seqseek.transforms.normalize import strip_leading_zeros_and_ones


def identify(terms: list[int], index: Index, limit: int = 10) -> list[Result]:
    """Identify the OEIS sequences ``terms`` most likely belong to.

    Runs the input and each transform of it against ``index``, ranking all hits.
    The caller owns the index handle; acquisition (and its "no local data" error)
    is a boundary concern, so every surface opens the index itself.
    """
    normalized = strip_leading_zeros_and_ones([int(t) for t in terms])
    best: dict[str, Result] = {}

    for name, transform in REGISTRY.items():
        candidate = transform(normalized)
        if not candidate:
            continue
        for match in find_matches(candidate, index):
            result = Result(
                a_number=match.a_number,
                name=match.name,
                transform=name,
                score=rank.score(match, name),
                matched_terms=match.matched_terms,
                explanation=rank.explain(match, name),
            )
            incumbent = best.get(match.a_number)
            if incumbent is None or result.score > incumbent.score:
                best[match.a_number] = result

    ranked = sorted(best.values(), key=lambda r: r.score, reverse=True)
    return ranked[:limit]
