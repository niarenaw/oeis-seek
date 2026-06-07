"""CLI surface: parsing, integration lookups, JSON shape, and messaging paths."""

from __future__ import annotations

import json

import pytest

from oeis_seek import cli
from oeis_seek import index as index_mod
from oeis_seek.models import Result

_GOLDEN_RESULTS = [
    Result(
        a_number="A000045",
        name="Fibonacci numbers",
        transform="raw",
        score=6.5,
        matched_terms=[2, 3, 5, 8, 13, 21],
        explanation="Direct match on 6 terms (transform distance 0).",
    ),
    Result(
        a_number="A000044",
        name="Dying rabbits",
        transform="raw",
        score=6.0,
        matched_terms=[2, 3, 5, 8, 13, 21],
        explanation="Direct match on 6 terms (transform distance 0).",
    ),
]

_GOLDEN_HUMAN = """\
Snapshot: January 01 2026

1. A000045  Fibonacci numbers
   transform  raw
   confidence 6.5
   matched    2, 3, 5, 8, 13, 21
   why        Direct match on 6 terms (transform distance 0).
   https://oeis.org/A000045

2. A000044  Dying rabbits
   transform  raw
   confidence 6
   matched    2, 3, 5, 8, 13, 21
   why        Direct match on 6 terms (transform distance 0).
   https://oeis.org/A000044"""


def test_format_human_matches_golden():
    out = cli.format_human(_GOLDEN_RESULTS, "January 01 2026", color=False)
    assert out == _GOLDEN_HUMAN


def test_format_human_separates_blocks_with_blank_line():
    out = cli.format_human(_GOLDEN_RESULTS, "January 01 2026", color=False)
    assert "\n\n2. A000044" in out


def test_format_human_is_plain_without_color():
    colored = cli.format_human(_GOLDEN_RESULTS, "January 01 2026", color=True)
    plain = cli.format_human(_GOLDEN_RESULTS, "January 01 2026", color=False)
    assert "\033[" in colored  # color requested -> escape codes present
    assert "\033[" not in plain  # plain requested -> none


def test_color_off_when_piped(monkeypatch):
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert cli._use_color() is False


def test_color_off_when_no_color_set(monkeypatch):
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    monkeypatch.setenv("NO_COLOR", "1")
    assert cli._use_color() is False


def test_parse_terms_accepts_commas_and_whitespace():
    assert cli.parse_terms("2,6,12,20") == [2, 6, 12, 20]
    assert cli.parse_terms("2 6 12 20") == [2, 6, 12, 20]
    assert cli.parse_terms("2, 6  12 ,20") == [2, 6, 12, 20]


def test_parse_terms_rejects_oversized_terms():
    with pytest.raises(ValueError):
        cli.parse_terms("1" * (cli.MAX_TERM_DIGITS + 1))


@pytest.fixture
def cli_index(monkeypatch, built_index):
    """Point the CLI's index.open_index at the in-memory fixture index."""
    monkeypatch.setattr(index_mod, "open_index", lambda *a, **k: built_index)
    # keep the handle open across the call; the CLI closes it, so re-stub close
    monkeypatch.setattr(built_index, "close", lambda: None)
    return built_index


def test_raw_lookup_integration(cli_index, capsys):
    rc = cli.main(["0,1,1,2,3,5,8,13"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "A000045" in out


def test_difference_lookup_integration(cli_index, capsys):
    rc = cli.main(["2,6,12,20,30,42"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "A005843" in out
    assert "first_differences" in out


def test_json_output_shape(cli_index, capsys):
    rc = cli.main(["0,1,1,2,3,5,8,13", "--json"])
    out = capsys.readouterr().out
    assert rc == 0
    payload = json.loads(out)
    assert "snapshot" in payload
    assert payload["results"][0]["a_number"] == "A000045"
    assert "confidence" in payload["results"][0]


def test_min_terms_blocks_short_input(cli_index, capsys):
    rc = cli.main(["2,3"])
    assert rc == 2
    assert "at least 4 terms" in capsys.readouterr().err


def test_no_matches_message(cli_index, capsys):
    rc = cli.main(["7,7,7,7,7"])
    assert rc == 1
    assert "No matches found." in capsys.readouterr().out


def test_missing_index_message(monkeypatch, capsys):
    def raise_missing(*a, **k):
        raise FileNotFoundError

    monkeypatch.setattr(index_mod, "open_index", raise_missing)
    rc = cli.main(["2,3,5,8,13"])
    assert rc == 3
    assert "oeis-seek update" in capsys.readouterr().err
