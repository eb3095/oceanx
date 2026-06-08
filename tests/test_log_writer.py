from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import numpy as np
import time

from oceanx.log_writer import LogWriter, mhz_log_name
from oceanx.radio.channels import COMMON_MARINE_CHANNELS
from oceanx.radio.voice_monitor import VoiceMonitor


def test_mhz_log_name():
    assert mhz_log_name("radio", 156.8) == "radio_156.800"


def test_ais_log_written(tmp_path: Path):
    writer = LogWriter(tmp_path)
    writer.log_ais("12:00:00 123456789 TEST")
    writer.close()
    text = (tmp_path / "ais.log").read_text(encoding="utf-8")
    assert "123456789" in text


def test_radio_logs_transcript_only(tmp_path: Path):
    writer = LogWriter(tmp_path)
    monitor = VoiceMonitor(channels=COMMON_MARINE_CHANNELS[:1], log_writer=writer)
    monitor._transcriber = type(
        "Stub",
        (),
        {
            "transcribe": staticmethod(lambda _audio: "coast guard"),
            "available": True,
            "status": "ok",
        },
    )()
    audio = np.ones(8_000, dtype=np.float32) * 0.5
    with (
        patch("oceanx.radio.voice_monitor.demod_am", return_value=audio),
        patch(
            "oceanx.radio.voice_monitor.IQConverter.from_bytes",
            return_value=np.ones(100, dtype=np.complex64),
        ),
        patch.object(monitor._segmenter, "feed", return_value=[audio]),
    ):
        monitor.process_iq(b"\x00" * 200)
        time.sleep(0.1)
    writer.close()
    channel = monitor.selected_channel()
    log_path = tmp_path / f"radio_{channel.freq_mhz:.3f}.log"
    assert log_path.exists()
