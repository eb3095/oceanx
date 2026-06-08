"""Default marine VHF channels stored in user config."""

from __future__ import annotations

from typing import Any, Dict, List

DEFAULT_RADIO_CHANNELS: List[Dict[str, Any]] = [
    {
        "id": "16",
        "name": "Channel 16 Distress",
        "freq_mhz": 156.8,
        "description": "International distress, safety, and calling",
    },
    {
        "id": "13",
        "name": "Channel 13 Bridge",
        "freq_mhz": 156.65,
        "description": "Bridge-to-bridge navigation safety",
    },
    {
        "id": "14",
        "name": "Channel 14 Port Ops",
        "freq_mhz": 156.7,
        "description": "Port operations and vessel traffic",
    },
    {
        "id": "22A",
        "name": "USCG Liaison",
        "freq_mhz": 157.1,
        "description": "USCG working channel (US)",
    },
    {
        "id": "68",
        "name": "Ship-Shore 68",
        "freq_mhz": 156.425,
        "description": "Non-commercial operations and marinas",
    },
    {
        "id": "69",
        "name": "Ship-Shore 69",
        "freq_mhz": 156.475,
        "description": "Non-commercial operations",
    },
    {
        "id": "71",
        "name": "Ship-Shore 71",
        "freq_mhz": 156.575,
        "description": "Non-commercial working channel",
    },
    {
        "id": "72",
        "name": "Intership 72",
        "freq_mhz": 156.625,
        "description": "Intership safety and working channel",
    },
    {
        "id": "73",
        "name": "Intership 73",
        "freq_mhz": 156.675,
        "description": "Intership working channel",
    },
    {
        "id": "09",
        "name": "Channel 09 Calling",
        "freq_mhz": 156.45,
        "description": "Alternative hailing channel",
    },
    {
        "id": "06",
        "name": "Channel 06 Safety",
        "freq_mhz": 156.3,
        "description": "Intership safety and SAR coordination",
    },
    {
        "id": "81A",
        "name": "Port Ops 81A",
        "freq_mhz": 157.075,
        "description": "US port operations / VTS",
    },
]
