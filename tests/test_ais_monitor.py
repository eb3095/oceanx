from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from oceanx.ais.channels import parse_ais_channels
from oceanx.ais.monitor import AisMonitor
from oceanx.decode.tracker import VesselTracker
from oceanx.dsp.gmsk_demodulator import DecodedFrame


def test_ais_monitor_processes_frame_and_updates_tracker():
    tracker = VesselTracker()
    channels = parse_ais_channels(None)
    monitor = AisMonitor(channels, tracker)
    fake_msg = SimpleNamespace(mmsi=111000111, shipname="TEST")
    with (
        patch.object(
            monitor._demod,
            "decode_channel",
            return_value=[DecodedFrame(payload=b"\x01\x02", fill_bits=0)],
        ),
        patch.object(monitor._demod, "to_nmea", return_value="!AIVDM,1,1,,A,15,0*00"),
        patch.object(monitor, "_decode_nmea", return_value=fake_msg),
    ):
        count = monitor.process_iq(np.ones(100, dtype=np.complex64), now=100.0)
    assert count >= 1
    assert "111000111" in tracker.vessels


def test_ais_monitor_handles_empty_iq():
    tracker = VesselTracker()
    monitor = AisMonitor(parse_ais_channels(None), tracker)
    assert monitor.process_iq(np.array([], dtype=np.complex64)) == 0
