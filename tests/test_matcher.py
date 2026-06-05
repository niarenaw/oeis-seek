"""Matcher behavior: contiguous-subsequence semantics, boundaries, signs, big ints."""

from __future__ import annotations

from seqseek.index import frame_terms
from seqseek.matcher import find_matches


def test_mid_sequence_run_matches(built_index):
    # 2,3,5,8 is a contiguous run inside Fibonacci, not a prefix
    matches = find_matches([2, 3, 5, 8], built_index)
    assert any(m.a_number == "A000045" for m in matches)


def test_term_boundaries_are_respected():
    # The framed run ,2,3, must not appear inside a term like 23.
    assert frame_terms([2, 3]) not in frame_terms([5, 23, 99])
    # ...but a genuine adjacency does.
    assert frame_terms([2, 3]) in frame_terms([1, 2, 3, 4])


def test_signs_are_respected(built_index):
    # The fixture has only non-negative terms, so a negative run finds nothing.
    assert find_matches([-2, -3, -4], built_index) == []
    assert any(m.a_number == "A000027" for m in find_matches([2, 3, 4], built_index))


def test_big_integer_round_trip(built_index):
    big = 2**400
    run = [big, big + 1, big + 2, big + 3]
    matches = find_matches(run, built_index)
    assert any(m.a_number == "A999999" for m in matches)
    match = next(m for m in matches if m.a_number == "A999999")
    assert match.matched_terms == run  # 121-digit terms preserved exactly
