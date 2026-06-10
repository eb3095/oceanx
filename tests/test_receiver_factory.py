from __future__ import annotations

from dataclasses import replace

from oceanx.config import RadioConfig
from oceanx.radio.hackrf import HackRFReceiver
from oceanx.radio.receiver import make_receiver
from oceanx.radio.rtlsdr import RtlSdrReceiver


def test_make_receiver_hackrf():
    receiver = make_receiver(RadioConfig(backend="hackrf"), freq_hz=162_025_000)
    assert isinstance(receiver, HackRFReceiver)


def test_make_receiver_rtlsdr():
    receiver = make_receiver(RadioConfig(backend="rtlsdr"), freq_hz=162_025_000)
    assert isinstance(receiver, RtlSdrReceiver)


def test_make_receiver_defaults_to_hackrf():
    receiver = make_receiver(RadioConfig(), freq_hz=162_025_000)
    assert isinstance(receiver, HackRFReceiver)


def test_make_receiver_unknown_backend_falls_back_to_hackrf():
    config = replace(RadioConfig(), backend="unknown")
    receiver = make_receiver(config, freq_hz=162_025_000)
    assert isinstance(receiver, HackRFReceiver)
