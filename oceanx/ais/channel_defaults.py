"""Default AIS channels for marine monitoring."""

from __future__ import annotations

from typing import Any, Dict, List

DEFAULT_AIS_CHANNELS: List[Dict[str, Any]] = [
    {
        "id": "AIS-A",
        "name": "AIS Channel A",
        "freq_mhz": 161.975,
        "description": "International AIS channel A",
    },
    {
        "id": "AIS-B",
        "name": "AIS Channel B",
        "freq_mhz": 162.025,
        "description": "International AIS channel B",
    },
]
