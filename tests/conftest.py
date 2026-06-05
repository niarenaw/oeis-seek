"""Shared test fixtures: a built index over the tiny offline corpus."""

from __future__ import annotations

from pathlib import Path

import pytest

from seqseek import index as index_mod

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def built_index(tmp_path):
    """Build the fixture corpus into a temp SQLite index and yield an open handle."""
    index_path = tmp_path / "index.sqlite3"
    index_mod.build(
        stripped_path=FIXTURES / "mini-stripped.txt",
        names_path=FIXTURES / "mini-names.txt",
        index_path=index_path,
    )
    handle = index_mod.open_index(index_path)
    yield handle
    handle.close()
