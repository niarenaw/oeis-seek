"""Transform and normalization behavior - the executable form of the engine spec."""

from __future__ import annotations

from seqseek.transforms import REGISTRY, builtin
from seqseek.transforms.normalize import strip_leading_zeros_and_ones


def test_registry_maps_names_to_callables_only():
    assert set(REGISTRY) == {
        "raw",
        "first_differences",
        "partial_sums",
        "consecutive_ratios",
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


def test_normalization_strips_leading_zeros_and_ones():
    assert strip_leading_zeros_and_ones([0, 1, 1, 2, 3, 5]) == [2, 3, 5]
    # never empties the list
    assert strip_leading_zeros_and_ones([1, 1, 1]) == [1]
    # leaves a list with no leading 0/1 untouched
    assert strip_leading_zeros_and_ones([2, 4, 6]) == [2, 4, 6]
