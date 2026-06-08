"""AIS channel parsing helpers."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from oceanx.ais.channel_defaults import DEFAULT_AIS_CHANNELS
from oceanx.config import AisChannel


def parse_ais_channels(
    entries: Optional[Sequence[Mapping[str, Any]]],
) -> list[AisChannel]:
    source = DEFAULT_AIS_CHANNELS if not entries else entries
    channels: list[AisChannel] = []
    for item in source:
        freq_mhz = float(item["freq_mhz"])
        channels.append(
            AisChannel(
                channel_id=str(item.get("id") or f"{freq_mhz:.3f}"),
                name=str(item.get("name") or f"AIS {freq_mhz:.3f}"),
                freq_hz=int(round(freq_mhz * 1_000_000)),
                description=str(item.get("description") or "AIS channel"),
            )
        )
    return channels
