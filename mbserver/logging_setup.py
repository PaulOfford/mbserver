"""Logging configuration for mbserver.

This module uses the Python standard library `logging` package.

The original project used numeric log levels 0..4:
  0 = off
  1 = normal
  2 = verbose
  3 = debug
  4 = verbose debug / trace

We preserve the intent by mapping these to standard logging levels,
including two custom levels: VERBOSE (15) and TRACE (5).
"""

from __future__ import annotations

import logging
import sys
import time
from dataclasses import dataclass
from typing import Optional


# Custom levels (still within stdlib logging)
TRACE: int = 5
VERBOSE: int = 15

logging.addLevelName(TRACE, "TRACE")
logging.addLevelName(VERBOSE, "VERBOSE")


def level_from_int(level: int) -> int:
    """Map legacy numeric levels (0..4) to stdlib logging levels."""
    if level <= 0:
        # effectively off
        return logging.CRITICAL + 1
    if level == 1:
        return logging.INFO
    if level == 2:
        return VERBOSE
    if level == 3:
        return logging.DEBUG
    # 4 or higher
    return TRACE


@dataclass(frozen=True)
class _TerminatorFilter(logging.Filter):
    """Remove the message terminator character from log output."""

    terminator: str

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
            if self.terminator and self.terminator in msg:
                # Replace in-place by rewriting record.msg and clearing args
                record.msg = msg.replace(self.terminator, "")
                record.args = ()
        except Exception:
            # Never break logging
            pass
        return True


class _UTCFormatter(logging.Formatter):
    """Formatter that renders timestamps in UTC (like the original logger)."""

    converter = time.gmtime


def configure_logging(
    legacy_level: int,
    *,
    terminator: str = "",
    stream=None,
    fmt: str = "%(asctime)sZ - %(levelname)s - %(name)s - %(message)s",
    datefmt: str = "%Y-%m-%d %H:%M:%S",
) -> None:
    """Configure root logging for the application."""
    if stream is None:
        stream = sys.stdout

    root = logging.getLogger()
    root.handlers.clear()

    handler = logging.StreamHandler(stream)
    handler.setFormatter(_UTCFormatter(fmt=fmt, datefmt=datefmt))
    if terminator:
        handler.addFilter(_TerminatorFilter(terminator))

    root.addHandler(handler)
    root.setLevel(level_from_int(legacy_level))
