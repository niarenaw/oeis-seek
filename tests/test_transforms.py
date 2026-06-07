"""Transform and normalization behavior - the executable form of the engine spec."""

from __future__ import annotations

from oeis_seek.transforms import REGISTRY, builtin
from oeis_seek.transforms.normalize import strip_leading_zeros_and_ones


def test_registry_maps_names_to_callables_only():
    assert set(REGISTRY) == {
        "raw",
        "first_differences",
        "partial_sums",
        "consecutive_ratios",
        "second_differences",
        "third_differences",
        "minus_index",
        "divided_by_index",
        "absolute",
    }
    assert all(callable(fn) for fn in REGISTRY.values())


def test_raw_is_identity():
    assert builtin.raw([2, 3, 5]) == [2, 3, 5]


def test_first_differences():
    assert builtin.first_differences([2, 6, 12, 20, 30, 42]) == [4, 6, 8, 10, 12]
    assert builtin.first_differences([5]) is None


def test_partial_sums():
    assert builtin.partial_sums([1, 2, 3, 4]) == [1, 3, 6, 10]
    assert builtin.partial_sums([]) is None


def test_consecutive_ratios_direction_and_skip():
    # later over earlier: 1,2,6,24 -> 2,3,4
    assert builtin.consecutive_ratios([1, 2, 6, 24]) == [2, 3, 4]
    # skipped when a ratio is not an exact integer
    assert builtin.consecutive_ratios([1, 2, 3, 5]) is None
    # skipped on a zero denominator rather than dividing by zero
    assert builtin.consecutive_ratios([0, 4, 8]) is None


def test_nth_differences_compose_and_propagate_none():
    # second differences of n**2 are constant; third differences of n**3 are constant
    assert builtin.nth_differences([1, 4, 9, 16, 25], 2) == [2, 2, 2]
    assert builtin.nth_differences([0, 1, 8, 27, 64], 3) == [6, 6]
    # too few terms for the order collapses to None (needs order + 1 terms)
    assert builtin.nth_differences([1, 2], 2) is None
    assert builtin.nth_differences([1, 2, 3], 3) is None


def test_second_and_third_difference_registry_entries():
    assert REGISTRY["second_differences"]([1, 4, 9, 16, 25]) == [2, 2, 2]
    assert REGISTRY["third_differences"]([0, 1, 8, 27, 64]) == [6, 6]


def test_minus_index_is_zero_based():
    # a(n) - n with 0-based n: 2-0, 3-1, 5-2, 8-3
    assert builtin.minus_index([2, 3, 5, 8]) == [2, 2, 3, 5]


def test_divided_by_index_skips_first_position_and_inexact():
    # a(n) / n for n >= 1; the undefined n=0 position is omitted
    assert builtin.divided_by_index([0, 2, 6, 12, 20]) == [2, 3, 4, 5]
    # any inexact division skips the whole candidate
    assert builtin.divided_by_index([0, 2, 5]) is None
    # needs at least one n >= 1 position
    assert builtin.divided_by_index([5]) is None


def test_absolute_takes_magnitudes():
    assert builtin.absolute([-2, 3, -5]) == [2, 3, 5]
    assert builtin.absolute([2, 3, 5]) == [2, 3, 5]


def test_normalization_strips_leading_zeros_and_ones():
    assert strip_leading_zeros_and_ones([0, 1, 1, 2, 3, 5]) == [2, 3, 5]
    # never empties the list
    assert strip_leading_zeros_and_ones([1, 1, 1]) == [1]
    # leaves a list with no leading 0/1 untouched
    assert strip_leading_zeros_and_ones([2, 4, 6]) == [2, 4, 6]
