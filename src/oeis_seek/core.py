"""The identification fan-out: the single public entry point.

``identify`` normalizes the input, runs every registered transform, matches each
candidate against the index, dedupes the same sequence to its best-scoring hit,
and returns ranked results. Keeping the fan-out and dedup here (rather than in the
ranking module) gives the transform loop one home and keeps ranking a pure
function. Every future surface (CLI today; web/API/MCP later) calls this.
"""

from __future__ import annotations

from oeis_seek import rank
from oeis_seek.index import Index
from oeis_seek.matcher import find_matches
from oeis_seek.models import Result
from oeis_seek.transforms import REGISTRY
from oeis_seek.transforms.normalize import strip_leading_zeros_and_ones

# Lowest-distance transforms first, computed once: a candidate produced by several
# transforms is then scanned and attributed to its strongest (lowest-distance) one.
_ORDERED_TRANSFORMS = sorted(REGISTRY.items(), key=lambda item: rank.distance(item[0]))


def identify(terms: list[int], index: Index, limit: int = 10) -> list[Result]:
    """Identify the OEIS sequences ``terms`` most likely belong to.

    Runs the input and each transform of it against ``index``, ranking all hits.
    The caller owns the index handle; acquisition (and its "no local data" error)
    is a boundary concern, so every surface opens the index itself.
    """
    normalized = strip_leading_zeros_and_ones([int(t) for t in terms])
    best: dict[str, Result] = {}
    seen: set[tuple[int, ...]] = set()

    # The seen-set skips a redundant index scan when two transforms yield the same
    # candidate; because _ORDERED_TRANSFORMS runs lowest-distance first, the kept
    # scan is the strongest one. Winner selection across distinct candidates is the
    # best-per-A-number-by-score comparison below.
    for name, transform in _ORDERED_TRANSFORMS:
        candidate = transform(normalized)
        if not candidate:
            continue
        key = tuple(candidate)
        if key in seen:
            continue
        seen.add(key)
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

    # Highest score first, ascending A-number as the deterministic tiebreak so
    # equal-scoring results always order the same way.
    ranked = sorted(best.values(), key=lambda r: (-r.score, r.a_number))
    return ranked[:limit]
