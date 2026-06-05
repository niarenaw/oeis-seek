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
