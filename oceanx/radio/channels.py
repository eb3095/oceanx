"""Marine channel model and config parsing."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Sequence

from oceanx.config import AisChannel, MARINE_MAX_MHZ, MARINE_MIN_MHZ
from oceanx.radio.channel_defaults import DEFAULT_RADIO_CHANNELS


def channel_from_dict(data: Mapping[str, Any]) -> AisChannel:
    freq_mhz = float(data["freq_mhz"])
    channel_id = str(data.get("id") or f"{freq_mhz:.3f}")
    name = str(data.get("name") or channel_id)
    description = str(data.get("description") or name)
    freq_hz = int(round(freq_mhz * 1_000_000))
    return AisChannel(
        channel_id=channel_id,
        name=name,
        freq_hz=freq_hz,
        description=description,
    )


def channel_to_dict(channel: AisChannel) -> Dict[str, Any]:
    return {
        "id": channel.channel_id,
        "name": channel.name,
        "freq_mhz": round(channel.freq_mhz, 3),
        "description": channel.description,
    }


def parse_config_channels(
    entries: Optional[Sequence[Mapping[str, Any]]],
) -> list[AisChannel]:
    source = DEFAULT_RADIO_CHANNELS if not entries else entries
    return [channel_from_dict(item) for item in source]


def in_marine_band(channel: AisChannel) -> bool:
    return MARINE_MIN_MHZ <= channel.freq_mhz <= MARINE_MAX_MHZ


COMMON_MARINE_CHANNELS = parse_config_channels(None)
