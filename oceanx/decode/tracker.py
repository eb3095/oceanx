"""Maintain MMSI-keyed vessel state from decoded AIS messages."""

from __future__ import annotations

import time
from typing import Dict, Optional

from oceanx.config import MAX_VESSELS
from oceanx.models.vessel import Vessel


class VesselTracker:
    def __init__(self) -> None:
        self.vessels: Dict[str, Vessel] = {}
        self.total_messages = 0

    def ingest(self, message: object, now: Optional[float] = None) -> Optional[Vessel]:
        now = now or time.time()
        mmsi = getattr(message, "mmsi", None)
        if mmsi is None:
            return None
        key = str(mmsi)
        vessel = self.vessels.get(key)
        if vessel is None:
            vessel = Vessel(mmsi=key, first_seen=now, last_seen=now)
            self.vessels[key] = vessel
        vessel.last_seen = now
        vessel.message_count += 1
        self.total_messages += 1

        vessel.name = _pick_str(message, "shipname", "name", current=vessel.name)
        vessel.nav_status = _pick_str(
            message, "status", "nav_status", current=vessel.nav_status
        )
        vessel.ship_type = _pick_str(message, "ship_type", current=vessel.ship_type)
        vessel.sog = _pick_float(message, "speed", "sog", current=vessel.sog)
        vessel.cog = _pick_float(message, "course", "cog", current=vessel.cog)
        vessel.heading = _pick_float(message, "heading", current=vessel.heading)
        vessel.lat = _pick_float(message, "lat", "latitude", current=vessel.lat)
        vessel.lon = _pick_float(message, "lon", "longitude", current=vessel.lon)

        self._enforce_cap()
        return vessel

    def purge_stale(self, now: float, stale_sec: float = 600.0) -> None:
        stale = [
            mmsi for mmsi, v in self.vessels.items() if now - v.last_seen > stale_sec
        ]
        for mmsi in stale:
            del self.vessels[mmsi]

    def _enforce_cap(self) -> None:
        if len(self.vessels) <= MAX_VESSELS:
            return
        oldest = sorted(self.vessels.items(), key=lambda item: item[1].last_seen)
        for mmsi, _ in oldest[: len(self.vessels) - MAX_VESSELS]:
            del self.vessels[mmsi]


def _pick_str(message: object, *keys: str, current: str = "") -> str:
    for key in keys:
        value = getattr(message, key, None)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return current


def _pick_float(
    message: object, *keys: str, current: float | None = None
) -> float | None:
    for key in keys:
        value = getattr(message, key, None)
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return current
