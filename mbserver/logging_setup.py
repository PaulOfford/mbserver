from __future__ import annotations

import logging
import os
import sys
import time
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from typing import Optional


@dataclass(frozen=True)
class _TerminatorFilter(logging.Filter):
    terminator: str

    # noinspection PyBroadException
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
            if self.terminator and self.terminator in msg:
                record.msg = msg.replace(self.terminator, "")
                record.args = ()
        except Exception:
            # Logging must never break the application
            pass
        return True


class _UTCFormatter(logging.Formatter):
    converter = time.gmtime


def configure_logging(
    *,
    level: int,
    terminator: str = "",
    stream=None,
    log_file: Optional[str] = None,
    max_bytes: int = 5_000_000,
    backup_count: int = 5,
    console: bool = True,
    fmt: str = "%(asctime)s.%(msecs)03d - %(levelname)s - %(name)s - %(message)s",
    datefmt: str = "%Y-%m-%d %H:%M:%S",
) -> None:
    if stream is None:
        stream = sys.stdout

    root = logging.getLogger()
    root.handlers.clear()

    formatter = _UTCFormatter(fmt=fmt, datefmt=datefmt)
    terminator_filter = _TerminatorFilter(terminator) if terminator else None

    if console:
        sh = logging.StreamHandler(stream)
        sh.setFormatter(formatter)
        if terminator_filter:
            sh.addFilter(terminator_filter)
        root.addHandler(sh)

    if log_file:
        # Create parent directory if needed.
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        fh = RotatingFileHandler(
            log_file,
            maxBytes=int(max_bytes),
            backupCount=int(backup_count),
            encoding="utf-8",
            delay=True,
        )
        fh.setFormatter(formatter)
        if terminator_filter:
            fh.addFilter(terminator_filter)
        root.addHandler(fh)

    root.setLevel(level)
