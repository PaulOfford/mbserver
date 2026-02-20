from __future__ import annotations

import configparser
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

_CONFIG_NAME = "config.ini"


def _repo_root() -> Path:
    """
    Returns the repo root assuming each app package/module folder lives one level
    below it (i.e., config.py is at <repo>/<app>/config.py).
    """
    return Path(__file__).resolve().parents[1]


def _config_path() -> Path:
    return _repo_root() / _CONFIG_NAME


def _as_bool(cfg: configparser.ConfigParser, section: str, option: str, default: bool) -> bool:
    try:
        return cfg.getboolean(section, option, fallback=default)
    except ValueError:
        return default


def _as_int(cfg: configparser.ConfigParser, section: str, option: str, default: int) -> int:
    try:
        return cfg.getint(section, option, fallback=default)
    except ValueError:
        return default


def _as_str(cfg: configparser.ConfigParser, section: str, option: str, default: str) -> str:
    val = cfg.get(section, option, fallback=default)
    return val if val is not None else default


def _parse_log_level(value: str, default: int) -> int:
    if not value:
        return default
    v = value.strip()
    # Accept "INFO", "logging.INFO", or an integer.
    if v.isdigit():
        try:
            return int(v)
        except ValueError:
            return default
    if v.lower().startswith("logging."):
        v = v.split(".", 1)[1]
    return getattr(logging, v.upper(), default)


@dataclass(frozen=True)
class Settings:
    # Server / protocol
    server: Tuple[str, int]
    msg_terminator: str
    announce: bool
    mb_announcement_timer: int  # minutes

    # Posts (server-focused, but harmless for client)
    posts_url_root: str
    posts_dir: str
    lst_limit: int
    replace_nl: bool

    # Database (client-focused, but harmless for server)
    db_path: str

    # GUI (client-focused, but harmless for server)
    scan_time: int
    clock_tick_ms: int
    process_wait_ms: int

    # Comms (used by both)
    max_queue_size: int
    release_time_increment: int
    release_time_increment_short: int
    age_out_time: int

    # Debug
    debug: bool

    # Logging
    log_level: int
    log_to_file: bool
    log_file: str
    log_max_bytes: int
    log_backup_count: int


def load_settings() -> Settings:
    # Use interpolation=None to avoid configparser interpolation issues with values
    # like "%AppData%/..." (as in your MbClient defaults).
    cfg = configparser.ConfigParser(interpolation=None)
    path = _config_path()

    # Combined defaults from both apps (union of settings)
    defaults = {
        "server": {
            "host": "127.0.0.1",
            "port": "2442",
            "msg_terminator": "♢",
            "announce": "true",
            "mb_announcement_timer": "60",
        },
        "posts": {
            "posts_url_root": "",
            "posts_dir": r"posts\\",
            "lst_limit": "5",
            "replace_nl": "false",
        },
        "database": {
            "db_path": "%AppData%/MbClient/",
        },
        "gui": {
            "scan_time": "120",
            "clock_tick_ms": "20",
            "process_wait_ms": "20",
        },
        "comms": {
            "max_queue_size": "20",
            "release_time_increment": "15",
            "release_time_increment_short": "5",
            "age_out_time": "3600",
        },
        "debug": {
            "debug": "false",
        },
        "logging": {
            "log_level": "INFO",
            "log_to_file": "true",
            "log_file": "logs/mbserver.log",
            "log_max_bytes": "5000000",
            "log_backup_count": "5",
        },
    }

    # Apply defaults first, then override from file if present.
    cfg.read_dict(defaults)
    if path.exists():
        cfg.read(path, encoding="utf-8")

    # Server / protocol
    host = _as_str(cfg, "server", "host", "127.0.0.1")
    port = _as_int(cfg, "server", "port", 2442)
    msg_terminator = _as_str(cfg, "server", "msg_terminator", "♢")
    announce = _as_bool(cfg, "server", "announce", True)
    mb_announcement_timer = _as_int(cfg, "server", "mb_announcement_timer", 60)

    # Posts
    posts_url_root = _as_str(cfg, "posts", "posts_url_root", "")
    posts_dir = _as_str(cfg, "posts", "posts_dir", r"posts\\")
    lst_limit = _as_int(cfg, "posts", "lst_limit", 5)
    replace_nl = _as_bool(cfg, "posts", "replace_nl", False)

    # Database
    db_path = _as_str(cfg, "database", "db_path", "%AppData%/MbClient/")

    # GUI
    scan_time = _as_int(cfg, "gui", "scan_time", 120)
    clock_tick_ms = _as_int(cfg, "gui", "clock_tick_ms", 20)
    process_wait_ms = _as_int(cfg, "gui", "process_wait_ms", 20)

    # Comms
    max_queue_size = _as_int(cfg, "comms", "max_queue_size", 20)
    release_time_increment = _as_int(cfg, "comms", "release_time_increment", 15)
    release_time_increment_short = _as_int(cfg, "comms", "release_time_increment_short", 5)
    age_out_time = _as_int(cfg, "comms", "age_out_time", 3600)

    # Debug
    debug = _as_bool(cfg, "debug", "debug", False)

    # Logging
    log_level = _parse_log_level(_as_str(cfg, "logging", "log_level", "INFO"), logging.INFO)
    log_to_file = _as_bool(cfg, "logging", "log_to_file", True)
    log_file = _as_str(cfg, "logging", "log_file", "logs/mbserver.log")
    log_max_bytes = _as_int(cfg, "logging", "log_max_bytes", 5_000_000)
    log_backup_count = _as_int(cfg, "logging", "log_backup_count", 5)

    return Settings(
        server=(host, port),
        msg_terminator=msg_terminator,
        announce=announce,
        mb_announcement_timer=mb_announcement_timer,
        posts_url_root=posts_url_root,
        posts_dir=posts_dir,
        lst_limit=lst_limit,
        replace_nl=replace_nl,
        db_path=db_path,
        scan_time=scan_time,
        clock_tick_ms=clock_tick_ms,
        process_wait_ms=process_wait_ms,
        max_queue_size=max_queue_size,
        release_time_increment=release_time_increment,
        release_time_increment_short=release_time_increment_short,
        age_out_time=age_out_time,
        debug=debug,
        log_level=log_level,
        log_to_file=log_to_file,
        log_file=log_file,
        log_max_bytes=log_max_bytes,
        log_backup_count=log_backup_count,
    )


# Load once at import time for simplicity.
SETTINGS: Settings = load_settings()
