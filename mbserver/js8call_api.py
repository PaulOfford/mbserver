from __future__ import annotations

import json
import logging
import select
import time
from socket import AF_INET, SOCK_STREAM, socket
from typing import Any, Optional

logger = logging.getLogger(__name__)


class Js8CallApi:
    """Thin TCP client for the JS8Call TCP Server API.

    JS8Call typically sends JSON objects separated by newlines, but it may also
    send multiple objects in a single recv(). This client normalizes raw socket
    frames into a list of parsed dict messages.

    Notes:
        - `connect()` raises ConnectionRefusedError if the API server is not reachable.
        - `listen()` returns [{'type': 'DISCONNECT'}] when the socket closes.
    """

    my_station: str = ""
    my_grid: str = ""

    def __init__(self, addr: tuple[str, int]) -> None:
        self.addr = addr
        self.sock = socket(AF_INET, SOCK_STREAM)

    def connect(self) -> None:
        """Connect to the configured JS8Call TCP API server."""
        logger.info("Connecting to JS8Call at %s:%s", *self.addr)
        try:
            self.sock.connect(self.addr)
            logger.info("Connected to JS8Call")
        except ConnectionRefusedError:
            logger.error("Connection to JS8Call has been refused.")
            logger.error("Check that:")
            logger.error("* JS8Call is running")
            logger.error("* Enable TCP Server API and Accept TCP Requests are checked")
            logger.error("* API server port matches this script (default 2442)")
            logger.error("* No firewall rules prevent the connection")
            raise

    def close(self) -> None:
        """Close the TCP socket."""
        try:
            self.sock.close()
        except OSError:
            pass

    @staticmethod
    def to_message(msg_type: str, value: str = "", params: Optional[dict[str, Any]] = None) -> str:
        """Create a JS8Call API JSON message string."""
        return json.dumps({"type": msg_type, "value": value, "params": params or {}})

    def send(self, msg_type: str, value: str = "", *, params: Optional[dict[str, Any]] = None) -> None:
        """Send a message to JS8Call.

        Adds a millisecond `_ID` if not provided.
        Always appends a newline (required by JS8Call).
        """
        params = dict(params or {})
        params.setdefault("_ID", f"{int(time.time() * 1000)}")

        message = self.to_message(msg_type, value=value, params=params)
        # Helps with message window formatting in some JS8Call versions
        message = message.replace("\n\n", "\n \n")

        payload = (message + "\n").encode()
        logger.debug("tx - %s", payload)
        self.sock.send(payload)

    def listen(self, timeout_s: float = 0.5) -> list[dict[str, Any]]:
        """Receive and parse zero or more JS8Call messages.

        Uses non-blocking I/O with select() to avoid stalling the main loop.

        Returns:
            Parsed messages, or [{'type': 'DISCONNECT'}] if the socket closes.
        """
        self.sock.setblocking(False)
        ready, _, _ = select.select([self.sock], [], [], timeout_s)
        if not ready:
            return []

        content = self.sock.recv(65500)
        logger.debug("rx - %s", content)

        if not content:
            logger.info("Connection to JS8Call has closed")
            return [{"type": "DISCONNECT"}]

        return self._parse_frames(content)

    @staticmethod
    def _parse_frames(raw: bytes) -> list[dict[str, Any]]:
        """Convert raw bytes from JS8Call into a list of JSON-decoded dicts.

        JS8Call may send multiple JSON objects separated by newlines. This function
        normalizes the stream into a JSON list and loads it. If a partial frame
        is received, returns an empty list (caller can recover next iteration).
        """
        raw = raw.replace("♢".encode("utf8"), b"")
        raw = raw.replace(b"  '}", b"'}")

        raw = raw.replace(b"}\n{", b"},{")
        raw = b"[" + raw + b"]"
        raw = raw.replace(b"}\n]", b"}]")

        try:
            decoded = json.loads(raw)
        except ValueError:
            return []

        if isinstance(decoded, list):
            return [m for m in decoded if isinstance(m, dict)]
        return []
