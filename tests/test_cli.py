"""CLI surface: parsing, integration lookups, JSON shape, and messaging paths."""

from __future__ import annotations

import json

import pytest

from seqseek import cli
from seqseek import index as index_mod


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
    assert "seqseek update" in capsys.readouterr().err
