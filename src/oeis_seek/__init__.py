"""oeis-seek - a transform-aware identifier for OEIS integer sequences."""

from oeis_seek.core import identify
from oeis_seek.models import Match, Result

__all__ = ["identify", "Match", "Result"]
__version__ = "0.1.0"
