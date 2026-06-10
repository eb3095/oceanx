"""Radio receiver factory."""

from __future__ import annotations

from oceanx.config import SAMPLE_RATE, RadioConfig
from oceanx.radio.hackrf import HackRFReceiver
from oceanx.radio.rtlsdr import RtlSdrReceiver


def make_receiver(
    config: RadioConfig, *, freq_hz: int, sample_rate: int = SAMPLE_RATE
) -> HackRFReceiver | RtlSdrReceiver:
    if config.backend == "rtlsdr":
        return RtlSdrReceiver(config, freq_hz=freq_hz, sample_rate=sample_rate)
    return HackRFReceiver(config, freq_hz=freq_hz, sample_rate=sample_rate)
