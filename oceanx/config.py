"""Runtime configuration and RF constants for OceanX."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

SAMPLE_RATE = 2_000_000
CHUNK_SAMPLES = 256 * 1024

AIS_CENTER_HZ = 162_000_000
AIS_BAUD = 9600
AIS_CHANNEL_PAGE_SIZE = 12

MARINE_MIN_MHZ = 156.0
MARINE_MAX_MHZ = 163.0
AIRBAND_AUDIO_RATE = 16_000
AIRBAND_VOLUME_DEFAULT = 3.0
AIRBAND_VOLUME_MIN = 0.0
AIRBAND_VOLUME_MAX = 12.0
AIRBAND_VOLUME_STEP = 0.25
WAVEFORM_HEIGHT = 7
RADIO_CHANNEL_PAGE_SIZE = 15

RECENT_MESSAGES_DISPLAY = 10
MAX_RECENT_MESSAGES_STORE = 500
MAX_RADIO_TRANSCRIPTS = 50
MAX_VESSELS = 20_000

HACKRF_BINARY_PATHS = (
    "hackrf_transfer",
    "/opt/homebrew/bin/hackrf_transfer",
    "/usr/local/bin/hackrf_transfer",
)


@dataclass(frozen=True)
class RadioConfig:
    lna_gain: int = 24
    vga_gain: int = 40
    amp_enable: bool = True


@dataclass(frozen=True)
class AisChannel:
    channel_id: str
    name: str
    freq_hz: int
    description: str

    @property
    def freq_mhz(self) -> float:
        return self.freq_hz / 1_000_000


@dataclass(frozen=True)
class SnifferConfig:
    radio: RadioConfig = RadioConfig()
    refresh_hz: float = 2.0
    sound_enabled: bool = True
    radio_channels: Tuple[AisChannel, ...] = ()
    ais_channels: Tuple[AisChannel, ...] = ()

    @classmethod
    def from_preset(
        cls,
        *,
        lna: int = 24,
        vga: int = 40,
        amp_enable: bool = True,
        refresh_hz: float = 2.0,
        sound_enabled: bool = True,
        radio_channels: Optional[List[AisChannel]] = None,
        ais_channels: Optional[List[AisChannel]] = None,
    ) -> SnifferConfig:
        return cls(
            radio=RadioConfig(lna_gain=lna, vga_gain=vga, amp_enable=amp_enable),
            refresh_hz=refresh_hz,
            sound_enabled=sound_enabled,
            radio_channels=tuple(radio_channels or ()),
            ais_channels=tuple(ais_channels or ()),
        )
