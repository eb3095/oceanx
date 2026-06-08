from __future__ import annotations

from oceanx.app.sniffer import OceanXSniffer
from oceanx.config import AIS_CENTER_HZ, SnifferConfig


def test_dashboard_switch_retunes_hackrf():
    sniffer = OceanXSniffer(SnifferConfig.from_preset())
    assert sniffer.dashboard == "ais"
    assert sniffer.receiver.freq_hz == AIS_CENTER_HZ
    sniffer.set_dashboard("radio")
    assert sniffer.dashboard == "radio"
    assert sniffer.receiver.freq_hz == sniffer.voice_monitor.selected_channel().freq_hz
    sniffer.set_dashboard("ais")
    assert sniffer.receiver.freq_hz == AIS_CENTER_HZ
