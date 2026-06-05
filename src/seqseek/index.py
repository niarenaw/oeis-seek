"""Parsing the dump into a persisted, queryable SQLite index.

The index is a single ``sequences`` table whose ``terms`` column holds each
sequence's terms as a comma-framed string (``,t0,t1,...,tn,``). Framing the run
on both sides lets the matcher express a contiguous-subsequence query as a plain
substring match with correct term boundaries and sign handling. A full-corpus
in-memory structure would be GB-scale, so an on-disk store queried without
loading everything is the right call; SQLite is stdlib and durable.

The build writes to a temporary database and swaps it into place on success, so a
failed rebuild never destroys a working index.
"""

from __future__ import annotations

import os
import re
import sqlite3
import tempfile
from collections.abc import Iterator
from pathlib import Path

from seqseek.download import CACHE_DIR

INDEX_PATH = CACHE_DIR / "index.sqlite3"

_LAST_MODIFIED = re.compile(r"#\s*Last Modified:\s*(.+)$")


def frame_terms(terms: list[int]) -> str:
    """Render a term list as a comma-framed string using canonical decimal form.

    Both the index build and the matcher route terms through this function so the
    stored and queried representations always agree byte-for-byte.
    """
    return "," + ",".join(str(int(t)) for t in terms) + ","


def _read_snapshot_date(stripped_path: Path) -> str | None:
    with stripped_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.startswith("#"):
                break
            match = _LAST_MODIFIED.search(line)
            if match:
                return match.group(1).strip()
    return None


def _parse_terms(value: str) -> list[int]:
    """Parse the value portion of a stripped.gz line into integers.

    The value is framed by a leading and trailing comma; both are stripped before
    splitting so no empty field reaches ``int()``.
    """
    return [int(token) for token in value.strip().strip(",").split(",") if token]


def _iter_stripped(stripped_path: Path) -> Iterator[tuple[str, list[int]]]:
    with stripped_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("#") or not line.strip():
                continue
            a_number, _, value = line.partition(" ")
            terms = _parse_terms(value)
            if terms:
                yield a_number.strip(), terms


def _read_names(names_path: Path) -> dict[str, str]:
    names: dict[str, str] = {}
    with names_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("#") or not line.strip():
                continue
            a_number, _, name = line.partition(" ")
            names[a_number.strip()] = name.strip()
    return names


def build(
    stripped_path: Path | None = None,
    names_path: Path | None = None,
    index_path: Path = INDEX_PATH,
) -> int:
    """Build the SQLite index from the cached dump. Returns the sequence count."""
    stripped_path = stripped_path or (CACHE_DIR / "stripped")
    names_path = names_path or (CACHE_DIR / "names")

    snapshot = _read_snapshot_date(stripped_path) or "unknown"
    names = _read_names(names_path)

    index_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_name = tempfile.mkstemp(suffix=".sqlite3", dir=index_path.parent)
    os.close(tmp_fd)
    tmp_path = Path(tmp_name)

    count = 0
    try:
        connection = sqlite3.connect(tmp_path)
        try:
            connection.execute(
                "CREATE TABLE sequences ("
                "a_number TEXT PRIMARY KEY, name TEXT, terms TEXT, snapshot_date TEXT)"
            )
            rows = (
                (a_number, names.get(a_number, ""), frame_terms(terms), snapshot)
                for a_number, terms in _iter_stripped(stripped_path)
            )
            connection.executemany(
                "INSERT OR REPLACE INTO sequences VALUES (?, ?, ?, ?)", rows
            )
            connection.commit()
            count = connection.execute("SELECT count(*) FROM sequences").fetchone()[0]
        finally:
            connection.close()
        tmp_path.replace(index_path)  # swap on success
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise

    return count


class Index:
    """A read handle over a built index, exposing lookups and snapshot metadata."""

    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection

    @property
    def snapshot_date(self) -> str:
        row = self._connection.execute(
            "SELECT snapshot_date FROM sequences LIMIT 1"
        ).fetchone()
        return row[0] if row else "unknown"

    @property
    def sequence_count(self) -> int:
        return self._connection.execute("SELECT count(*) FROM sequences").fetchone()[0]

    def find_containing(self, framed_query: str) -> list[tuple[str, str, str]]:
        """Return (a_number, name, terms) rows whose terms contain the framed query."""
        cursor = self._connection.execute(
            "SELECT a_number, name, terms FROM sequences WHERE terms LIKE ?",
            (f"%{framed_query}%",),
        )
        return cursor.fetchall()

    def close(self) -> None:
        self._connection.close()


def open_index(index_path: Path = INDEX_PATH) -> Index:
    """Open the built index for reading. Raises FileNotFoundError if absent."""
    if not index_path.exists():
        raise FileNotFoundError(index_path)
    return Index(sqlite3.connect(index_path))
