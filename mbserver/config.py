from __future__ import annotations

import configparser
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

_CONFIG_NAME = "config.ini"

def _repo_root() -> Path:
    # mbserver/ lives one level below the repo root (where mbserver.bat lives)
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
    role: str

    # Server / protocol
    server: Tuple[str, int]
    msg_terminator: str
    announce: bool
    mb_announcement_timer: int  # minutes

    # Posts
    posts_url_root: str
    posts_dir: str
    lst_limit: int
    replace_nl: bool

    # Debug
    debug: bool

    # Logging
    log_level: int
    log_to_file: bool
    log_file: str
    log_max_bytes: int
    log_backup_count: int

def load_settings() -> Settings:
    cfg = configparser.ConfigParser()
    path = _config_path()

    # Defaults mirror the old server_settings.py
    defaults = {
        "server": {
            "host": "127.0.0.1",
            "port": "2443",
            "msg_terminator": "♢",
            "announce": "true",
            "mb_announcement_timer": "60",
        },
        "posts": {
            "posts_url_root": "",
            "posts_dir": "posts\\",
            "lst_limit": "5",
            "replace_nl": "false",
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

    host = _as_str(cfg, "server", "host", "127.0.0.1")
    port = _as_int(cfg, "server", "port", 2443)
    msg_terminator = _as_str(cfg, "server", "msg_terminator", "♢")
    announce = _as_bool(cfg, "server", "announce", True)
    mb_announcement_timer = _as_int(cfg, "server", "mb_announcement_timer", 60)

    posts_url_root = _as_str(cfg, "posts", "posts_url_root", "")
    posts_dir = _as_str(cfg, "posts", "posts_dir", "posts\\")
    lst_limit = _as_int(cfg, "posts", "lst_limit", 5)
    replace_nl = _as_bool(cfg, "posts", "replace_nl", False)

    debug = _as_bool(cfg, "debug", "debug", False)

    log_level = _parse_log_level(_as_str(cfg, "logging", "log_level", "INFO"), logging.INFO)
    log_to_file = _as_bool(cfg, "logging", "log_to_file", True)
    log_file = _as_str(cfg, "logging", "log_file", "logs/mbserver.log")
    log_max_bytes = _as_int(cfg, "logging", "log_max_bytes", 5_000_000)
    log_backup_count = _as_int(cfg, "logging", "log_backup_count", 5)

    return Settings(
        role='mb_server',
        server=(host, port),
        msg_terminator=msg_terminator,
        announce=announce,
        mb_announcement_timer=mb_announcement_timer,
        posts_url_root=posts_url_root,
        posts_dir=posts_dir,
        lst_limit=lst_limit,
        replace_nl=replace_nl,
        debug=debug,
        log_level=log_level,
        log_to_file=log_to_file,
        log_file=log_file,
        log_max_bytes=log_max_bytes,
        log_backup_count=log_backup_count,
    )

# Load once at import time for simplicity.
SETTINGS: Settings = load_settings()
