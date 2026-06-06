"""Ranking and the identification fan-out: ordering, dedup, explanation."""

from __future__ import annotations

from seqseek import core, rank
from seqseek.models import Match


def test_raw_outranks_transformed():
    m = Match(a_number="A1", name="x", matched_terms=[2, 3, 4, 5])
    assert rank.score(m, "raw") > rank.score(m, "first_differences")


def test_more_terms_scores_higher():
    short = Match(a_number="A1", name="x", matched_terms=[2, 3, 4])
    long = Match(a_number="A1", name="x", matched_terms=[2, 3, 4, 5, 6])
    assert rank.score(long, "raw") > rank.score(short, "raw")


def test_explanation_names_the_transform():
    m = Match(a_number="A1", name="x", matched_terms=[2, 3, 4])
    assert "first_differences" in rank.explain(m, "first_differences")


def test_cross_transform_dedup_keeps_best(built_index):
    # 0,1,1,2,3,5,8,13 normalizes to 2,3,5,8,13 and matches Fibonacci raw;
    # it should appear exactly once, attributed to the raw transform.
    results = core.identify([0, 1, 1, 2, 3, 5, 8, 13], index=built_index)
    fib = [r for r in results if r.a_number == "A000045"]
    assert len(fib) == 1
    assert fib[0].transform == "raw"


def test_difference_based_identification(built_index):
    # 2,6,12,20,30,42 is not in the corpus, but its first differences are.
    results = core.identify([2, 6, 12, 20, 30, 42], index=built_index)
    even = next(r for r in results if r.a_number == "A005843")
    assert even.transform == "first_differences"


def test_core_outranks_non_core_at_equal_base():
    # Identical terms, transform, and position; only core membership differs.
    assert rank.is_core("A000045") and not rank.is_core("A000044")
    core_match = Match(a_number="A000045", name="Fibonacci", matched_terms=[2, 3, 5, 8], position=0)
    other = Match(a_number="A000044", name="Dying rabbits", matched_terms=[2, 3, 5, 8], position=0)
    assert rank.score(core_match, "raw") > rank.score(other, "raw")


def test_popularity_dominates_position():
    # A non-core match at the earliest offset must still rank below a core match
    # buried deeper: the popularity boost exceeds the largest possible position bonus.
    assert rank.WEIGHT_POPULARITY > rank.WEIGHT_POSITION  # the stated invariant
    non_core_early = Match(a_number="A000044", name="x", matched_terms=[2, 3, 5, 8], position=0)
    core_late = Match(a_number="A000045", name="y", matched_terms=[2, 3, 5, 8], position=9)
    assert rank.score(core_late, "raw") > rank.score(non_core_early, "raw")


def test_longer_match_beats_popularity():
    # A clearly stronger (longer) non-core match outranks a shorter core one.
    longer = Match(a_number="A000044", name="x", matched_terms=[2, 3, 5, 8, 13], position=0)
    shorter_core = Match(a_number="A000045", name="y", matched_terms=[2, 3, 5, 8], position=0)
    assert rank.score(longer, "raw") > rank.score(shorter_core, "raw")


def test_earlier_position_scores_higher():
    early = Match(a_number="A000044", name="x", matched_terms=[2, 3, 5, 8], position=0)
    late = Match(a_number="A000044", name="x", matched_terms=[2, 3, 5, 8], position=5)
    assert rank.score(early, "raw") > rank.score(late, "raw")


def test_headline_core_outranks_non_core(built_index):
    # The flagship case: Fibonacci (core) must rank above Dying rabbits (non-core),
    # which shares the run; both score the same on base, so popularity decides.
    results = core.identify([1, 1, 2, 3, 5, 8, 13, 21], index=built_index)
    order = [r.a_number for r in results]
    assert "A000045" in order and "A000044" in order
    assert order.index("A000045") < order.index("A000044")


def test_results_sort_deterministically(built_index):
    first = [r.a_number for r in core.identify([1, 1, 2, 3, 5, 8, 13, 21], index=built_index)]
    second = [r.a_number for r in core.identify([1, 1, 2, 3, 5, 8, 13, 21], index=built_index)]
    assert first == second
