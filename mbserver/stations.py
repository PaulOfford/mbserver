from __future__ import annotations

import time
from dataclasses import dataclass, field
from queue import Queue
from typing import Iterable


@dataclass
class Station:
    """Represents a destination station and its transmit throttling state."""

    callsign: str
    absolute_frequency: int
    tx_release_time: float
    tx_q: Queue = field(default_factory=Queue)


class StationRegistry:
    """Tracks stations and per-destination transmit throttling queues.

    The driver uses this registry to:
    - buffer outbound messages per destination callsign
    - throttle sends per destination and per frequency activity
    - age out inactive stations to prevent unbounded growth

    A special station with callsign ``UNSEEN`` is used as a sink queue for
    outbound messages whose destination has not been observed via RX yet.
    """

    def __init__(
        self,
        *,
        max_queue_size: int,
        release_time_increment: float,
        age_out_time: float,
    ) -> None:
        self.max_queue_size = max_queue_size
        self.release_time_increment = release_time_increment
        self.age_out_time = age_out_time

        self._stations: dict[str, Station] = {
            "UNSEEN": Station(
                callsign="UNSEEN",
                absolute_frequency=0,
                tx_release_time=0.0,
                tx_q=Queue(maxsize=max_queue_size),
            )
        }

    def station_for_destination(self, callsign: str) -> Station:
        """Return a Station for callsign, or the UNSEEN buffer if unknown."""
        return self._stations.get(callsign) or self._stations["UNSEEN"]

    def touch(self, callsign: str, absolute_frequency: int) -> None:
        """Update/create a station entry after seeing activity from it."""
        now = time.time()
        station = self._stations.get(callsign)

        if station is None:
            self._stations[callsign] = Station(
                callsign=callsign,
                absolute_frequency=absolute_frequency,
                tx_release_time=now + self.release_time_increment,
                tx_q=Queue(maxsize=self.max_queue_size),
            )
            return

        station.absolute_frequency = absolute_frequency
        station.tx_release_time = now + self.release_time_increment

    def bump_release_by_frequency(self, absolute_frequency: int) -> None:
        """Defer transmit permission for any station currently on a given absolute frequency."""
        now = time.time()
        for st in self._stations.values():
            if st.absolute_frequency == absolute_frequency:
                st.tx_release_time = now + self.release_time_increment

    def age_out(self) -> None:
        """Remove station entries that haven't been touched recently (keeps UNSEEN)."""
        cutoff = time.time() - self.age_out_time
        stale = [
            k for k, st in self._stations.items()
            if k != "UNSEEN" and st.tx_release_time < cutoff
        ]
        for k in stale:
            self._stations.pop(k, None)

    def iter_stations(self) -> Iterable[Station]:
        """Iterate over all stations including UNSEEN."""
        return self._stations.values()
