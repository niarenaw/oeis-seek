"""seqseek - a transform-aware identifier for OEIS integer sequences."""

from seqseek.core import identify
from seqseek.models import Match, Result

__all__ = ["identify", "Match", "Result"]
__version__ = "0.1.0"
