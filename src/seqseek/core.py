"""The identification fan-out: the single public entry point.

``identify`` normalizes the input, runs every registered transform, matches each
candidate against the index, dedupes the same sequence to its best-scoring hit,
and returns ranked results. Keeping the fan-out and dedup here (rather than in the
ranking module) gives the transform loop one home and keeps ranking a pure
function. Every future surface (CLI today; web/API/MCP later) calls this.
"""

from __future__ import annotations

from seqseek import rank
from seqseek.index import Index, frame_terms
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
    seen: set[str] = set()

    # Iterate lowest-distance transforms first so a candidate produced by several
    # transforms is scanned once and attributed to its strongest (lowest-distance)
    # one. The seen-set is a pre-scan skip only; winner selection across distinct
    # candidates remains the best-per-A-number-by-score comparison below.
    ordered = sorted(REGISTRY.items(), key=lambda item: rank.distance(item[0]))
    for name, transform in ordered:
        candidate = transform(normalized)
        if not candidate:
            continue
        framed = frame_terms(candidate)
        if framed in seen:
            continue
        seen.add(framed)
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
