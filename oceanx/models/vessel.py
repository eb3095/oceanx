"""In-memory state for a tracked AIS vessel."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Vessel:
    mmsi: str
    name: str = ""
    sog: Optional[float] = None
    cog: Optional[float] = None
    heading: Optional[float] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    nav_status: str = ""
    ship_type: str = ""
    message_count: int = 0
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
