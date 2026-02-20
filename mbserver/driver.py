from __future__ import annotations

import logging
import re
import time
from queue import Empty
from typing import Any, Optional

from .config import SETTINGS
from .general_functions import add_progress_m
from .js8call_api import Js8CallApi
from .message_q import (
    MessageParameter,
    MessageType,
    MessageVerb,
    UnifiedMessage,
    b2c_q_p0,
    b2c_q_p1,
    c2b_q,
)
from .stations import StationRegistry

logger = logging.getLogger(__name__)

# NOTE: mb_client.py historically overrides js8call_addr at runtime based on CLI args.
# We keep that behaviour via this module-level variable. Override it by setting:
#   mbclient.driver.JS8CALL_ADDR = (host, port)
JS8CALL_ADDR: tuple[str, int] = SETTINGS.server

DEBUG = SETTINGS.debug
MAX_QUEUE_SIZE = SETTINGS.max_queue_size

QUEUE_GET_TIMEOUT = 0  # non-blocking queue reads
RELEASE_TIME_INCREMENT = SETTINGS.release_time_increment
AGE_OUT_TIME = SETTINGS.age_out_time


class Js8CallDriver:
    """Main driver loop bridging backend queues to the JS8Call TCP API."""

    rx_ind_timeout: float = 0.0
    rx_duration: float = 0.5

    ptt_release_time: float = 0.0
    is_connected: bool = False

    def __init__(self) -> None:
        self.js8call_api = Js8CallApi(JS8CALL_ADDR)
        self.js8call_api.connect()
        self.is_connected = True

        self.stations = StationRegistry(
            max_queue_size=MAX_QUEUE_SIZE,
            release_time_increment=RELEASE_TIME_INCREMENT,
            age_out_time=AGE_OUT_TIME,
        )

    # -------------------------
    # Backend -> JS8Call (TX)
    # -------------------------

    def _send(self, msg_type: str, value: str = "", *, params: Optional[dict[str, Any]] = None) -> None:
        """Send a message to JS8Call, with optional DEBUG TX suppression."""
        if DEBUG and msg_type.startswith("TX."):
            logger.debug("DEBUG enabled: suppressing TX message: %s %s", msg_type, value)
            return
        self.js8call_api.send(msg_type, value, params=params)

    def set_radio_frequency(self, freq: int) -> None:
        """Set the radio dial frequency via JS8Call."""
        logger.debug("call: RIG.SET_FREQ")
        self._send("RIG.SET_FREQ", params={"DIAL": freq})

    def process_mb_msg(self, m: UnifiedMessage) -> None:
        """Send a microblog message via JS8Call TX.SEND_MESSAGE."""
        req_msg = f"{m.get_param(MessageParameter.DESTINATION)} {m.get_param(MessageParameter.MB_MSG)}"
        self._send("TX.SEND_MESSAGE", req_msg)

    def process_control(self, m: UnifiedMessage) -> None:
        """Handle control messages coming from the backend."""
        verb = m.get_verb()

        if verb == MessageVerb.SHUTDOWN:
            self.is_connected = False
            return

        if verb == MessageVerb.SET_FREQ:
            self.set_radio_frequency(m.get_param(MessageParameter.FREQUENCY))
            return

        if verb in (MessageVerb.GET_FREQ, MessageVerb.GET_OFFSET):
            self._send("RIG.GET_FREQ", "")
            return

        if verb == MessageVerb.GET_CALLSIGN:
            self._send("STATION.GET_CALLSIGN", "")
            return

    def process_comms_tx(self, m: UnifiedMessage) -> None:
        """Dispatch an outbound backend message to the appropriate JS8Call action."""
        if m.get_typ() == MessageType.MB_MSG:
            self.process_mb_msg(m)
        elif m.get_typ() == MessageType.CONTROL:
            self.process_control(m)
        else:
            logger.error("Invalid message received from backend, typ=%s", m.get_typ())

    def process_p0_queue(self) -> None:
        """Process priority-0 backend messages (immediate actions)."""
        try:
            comms_tx: UnifiedMessage = b2c_q_p0.get(timeout=QUEUE_GET_TIMEOUT)
        except Empty:
            return

        try:
            logger.debug("Received from BACKEND: %s", comms_tx.get_params())
            self.process_comms_tx(comms_tx)
            add_progress_m(comms_tx)
        finally:
            b2c_q_p0.task_done()

    def process_p1_queue(self) -> None:
        """Process priority-1 backend messages (per-station throttled TX)."""
        try:
            comms_tx: UnifiedMessage = b2c_q_p1.get(timeout=QUEUE_GET_TIMEOUT)
        except Empty:
            return

        try:
            logger.debug("Received from BACKEND: %s", comms_tx.get_params())
            destination = comms_tx.get_param(MessageParameter.DESTINATION)
            self.stations.station_for_destination(destination).tx_q.put(comms_tx)
        finally:
            b2c_q_p1.task_done()

    def process_b2c_q(self) -> None:
        """Process outbound messages from the backend."""
        self.process_p0_queue()
        self.process_p1_queue()

    def process_station_queues(self) -> None:
        """Transmit at most one queued message if allowed by PTT and per-station timers."""
        now = time.time()
        if now < self.ptt_release_time:
            return

        self.stations.age_out()

        for station in self.stations.iter_stations():
            if now <= station.tx_release_time:
                continue

            try:
                comms_tx: UnifiedMessage = station.tx_q.get(timeout=QUEUE_GET_TIMEOUT)
            except Empty:
                continue

            try:
                logger.info(
                    "Transmit ->: %s %s",
                    comms_tx.get_param(MessageParameter.DESTINATION),
                    comms_tx.get_param(MessageParameter.MB_MSG),
                )
                self.process_comms_tx(comms_tx)

                station.tx_release_time = time.time() + RELEASE_TIME_INCREMENT
                add_progress_m(comms_tx)
                return
            finally:
                station.tx_q.task_done()

    # -------------------------
    # JS8Call -> Backend (RX)
    # -------------------------

    @staticmethod
    def signal_backend(verb: MessageVerb, param: dict[str, Any]) -> None:
        """Send a signal message to the backend (status updates, etc.)."""
        m = UnifiedMessage.create(
            priority=0,
            target="BACKEND",
            typ="SIGNAL",
            verb=verb,
            params=param,
        )
        c2b_q.put(m)

    @staticmethod
    def inform_backend(source: str, frequency: int, destination: str, mb_message: str) -> None:
        """Forward an inbound microblog message to the backend (INFORM)."""
        m = UnifiedMessage.create(
            priority=1,
            target="BACKEND",
            typ="MB_MSG",
            verb="INFORM",
            params={
                "source": source,
                "destination": destination,
                "mb_msg": mb_message,
                "frequency": frequency,
            },
        )
        c2b_q.put(m)
        add_progress_m(m)

    @staticmethod
    def announce_to_backend(source: str, frequency: int, destination: str, mb_message: str) -> None:
        """Forward an inbound microblog message to the backend (ANNOUNCE)."""
        m = UnifiedMessage.create(
            priority=1,
            target="BACKEND",
            typ="MB_MSG",
            verb="ANNOUNCE",
            params={
                "source": source,
                "destination": destination,
                "mb_msg": mb_message,
                "frequency": frequency,
            },
        )
        c2b_q.put(m)
        add_progress_m(m)

    # -------------------------
    # Main loop
    # -------------------------

    def run_comms(self) -> None:
        """Main event loop: drives backend TX + JS8Call RX until shutdown/disconnect."""
        if self.is_connected:
            logger.debug("Send STATION.GET_CALLSIGN")
            self._send("STATION.GET_CALLSIGN", "")

            logger.debug("Send RIG.GET_FREQ")
            self._send("RIG.GET_FREQ", "")

        try:
            while self.is_connected:
                self.process_b2c_q()
                self.process_station_queues()

                messages = self.js8call_api.listen()

                # RX indicator timeout handling
                if 0 < self.rx_ind_timeout < time.time():
                    self.signal_backend(MessageVerb.NOTE_RX, {MessageParameter.RX: False})
                    self.rx_ind_timeout = 0.0

                for message in messages:
                    msg_type = message.get("type", "")
                    value = message.get("value", "")
                    params = message.get("params", {}) or {}

                    # Signal RX activity window
                    if self.rx_ind_timeout == 0.0:
                        self.signal_backend(MessageVerb.NOTE_RX, {MessageParameter.RX: True})
                    self.rx_ind_timeout = time.time() + self.rx_duration

                    if not msg_type:
                        continue

                    if msg_type == "DISCONNECT":
                        self.is_connected = False
                        self.signal_backend(MessageVerb.NOTE_DISCONNECT, {})
                        continue

                    if msg_type == "RIG.PTT":
                        ptt_state = value == "on"
                        self.ptt_release_time = time.time() + RELEASE_TIME_INCREMENT
                        logger.debug("PTT %s", "ON" if ptt_state else "OFF")
                        self.signal_backend(MessageVerb.NOTE_PTT, {MessageParameter.PTT: ptt_state})
                        continue

                    if msg_type == "STATION.CALLSIGN":
                        self.signal_backend(MessageVerb.NOTE_CALLSIGN, {"callsign": value})
                        continue

                    if msg_type in ("RIG.FREQ", "STATION.STATUS"):
                        dial = int(params["DIAL"])
                        offset = int(params["OFFSET"])

                        self.signal_backend(MessageVerb.NOTE_FREQ, {"frequency": dial})
                        logger.debug("q_put: NOTE_FREQ - %s", dial)

                        self.signal_backend(MessageVerb.NOTE_OFFSET, {"offset": offset})
                        logger.debug("q_put: NOTE_OFFSET - %s", offset)
                        continue

                    if msg_type == "RX.DIRECTED":
                        logger.debug("RX.DIRECTED %s", value)

                        msg_elements = re.findall(r"^\S+: +\S+ +([\S\s]+)", value)
                        if not msg_elements:
                            continue
                        mb_message = msg_elements[0]

                        from_call = str(params.get("FROM", ""))
                        to_call = str(params.get("TO", ""))
                        freq = int(params.get("FREQ", 0))
                        dial = int(params.get("DIAL", 0))

                        if from_call:
                            self.stations.touch(from_call, freq)

                        if to_call == "@MB":
                            self.announce_to_backend(from_call, dial, to_call, mb_message)
                        else:
                            self.inform_backend(from_call, dial, to_call, mb_message)

                        logger.debug("q_put: INFORM - %s", mb_message)
                        continue

                    if msg_type == "RX.ACTIVITY":
                        absolute_frequency = int(params["FREQ"])
                        logger.debug("Seeing RX.ACTIVITY messages for FREQ: %s", absolute_frequency)
                        self.stations.bump_release_by_frequency(absolute_frequency)
                        continue

        finally:
            self.js8call_api.close()
