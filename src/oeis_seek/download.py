"""Acquisition of the OEIS bulk dump.

The offline MVP depends entirely on two public files: ``stripped.gz`` (terms) and
``names.gz`` (titles). This module fetches them, validates that the response is a
genuine, fully decompressible gzip of plausible size, and only then atomically
promotes the decompressed files into the cache. A failed or truncated download
therefore never clobbers a previously good cache.
"""

from __future__ import annotations

import gzip
import shutil
import tempfile
import urllib.request
from pathlib import Path

from platformdirs import user_cache_dir

CACHE_DIR = Path(user_cache_dir("oeis-seek"))
USER_AGENT = "oeis-seek/0.1 (+https://github.com/niarenaw/oeis-seek; OEIS sequence identifier)"
REQUEST_TIMEOUT = 60  # seconds

# A correct dump is tens of MB; anything tiny is an error page or a truncation.
MIN_PLAUSIBLE_BYTES = 1_000_000

FILES = {
    "stripped": "https://oeis.org/stripped.gz",
    "names": "https://oeis.org/names.gz",
}


def cache_path(name: str) -> Path:
    """Path to a decompressed cached dump file (e.g. ``stripped`` or ``names``)."""
    return CACHE_DIR / name


def _fetch(url: str, timeout: int) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _validate_and_decompress(payload: bytes) -> bytes:
    """Confirm the payload is a plausible, fully decompressible gzip; return its bytes."""
    if len(payload) < MIN_PLAUSIBLE_BYTES:
        raise ValueError(
            f"download too small ({len(payload)} bytes); likely an error page or truncation"
        )
    if payload[:2] != b"\x1f\x8b":
        raise ValueError("response is not gzip (bad magic bytes)")
    return gzip.decompress(payload)


def download(timeout: int = REQUEST_TIMEOUT) -> Path:
    """Download, validate, and atomically cache both dump files.

    Returns the cache directory. Raises on any validation failure, leaving any
    prior good cache untouched.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    staged: dict[str, Path] = {}

    # Stage everything to temp files first; only promote once all succeed.
    tmp_dir = Path(tempfile.mkdtemp(prefix="oeis-seek-dl-"))
    try:
        for name, url in FILES.items():
            decompressed = _validate_and_decompress(_fetch(url, timeout))
            tmp_file = tmp_dir / name
            tmp_file.write_bytes(decompressed)
            staged[name] = tmp_file
        for name, tmp_file in staged.items():
            tmp_file.replace(cache_path(name))  # atomic within the same filesystem
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return CACHE_DIR
