"""Process IQ chunks and decode AIS messages."""

from __future__ import annotations

import time
from typing import List, Sequence

import numpy as np

from oceanx.config import AIS_CENTER_HZ, AisChannel
from oceanx.decode.tracker import VesselTracker
from oceanx.dsp.gmsk_demodulator import GMSKDemodulator
from oceanx.dsp.iq import IQConverter
from oceanx.log_writer import LogWriter


class AisMonitor:
    def __init__(
        self,
        channels: Sequence[AisChannel],
        tracker: VesselTracker,
        *,
        log_writer: LogWriter | None = None,
        backend: str = "hackrf",
    ) -> None:
        self.channels = list(channels)
        self.tracker = tracker
        self.backend = backend
        self._demod = GMSKDemodulator()
        self._log = log_writer
        self.recent_messages: List[str] = []

    def process_iq(self, raw: bytes | np.ndarray, now: float | None = None) -> int:
        now = now or time.time()
        iq = (
            IQConverter.from_radio_bytes(raw, self.backend)
            if isinstance(raw, (bytes, bytearray))
            else raw
        )
        if iq.size == 0:
            return 0
        decoded_count = 0
        for index, channel in enumerate(self.channels):
            offset = channel.freq_hz - AIS_CENTER_HZ
            frames = self._demod.decode_channel(iq, offset_hz=float(offset))
            for frame in frames:
                nmea = self._demod.to_nmea(
                    frame.payload, frame.fill_bits, channel="A" if index == 0 else "B"
                )
                msg = self._decode_nmea(nmea)
                if msg is None:
                    continue
                vessel = self.tracker.ingest(msg, now=now)
                if vessel is None:
                    continue
                decoded_count += 1
                self.recent_messages.append(nmea)
                self.recent_messages = self.recent_messages[-200:]
                if self._log is not None:
                    self._log.log_ais(
                        f"{time.strftime('%H:%M:%S', time.localtime(now))} {vessel.mmsi} {nmea}"
                    )
        return decoded_count

    @staticmethod
    def _decode_nmea(nmea: str) -> object | None:
        try:
            from pyais import decode  # type: ignore

            return decode(nmea)
        except Exception:
            return None
