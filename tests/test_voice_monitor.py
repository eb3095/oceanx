from __future__ import annotations

import time
from unittest.mock import patch

import numpy as np

from oceanx.config import MAX_RADIO_TRANSCRIPTS, RADIO_CHANNEL_PAGE_SIZE
from oceanx.radio.channels import COMMON_MARINE_CHANNELS
from oceanx.radio.voice_monitor import TranscriptLine, VoiceMonitor


def test_per_channel_buffer_cap():
    monitor = VoiceMonitor(channels=COMMON_MARINE_CHANNELS)
    ch_a = monitor.channels[0].channel_id
    ch_b = monitor.channels[1].channel_id
    buf = monitor._buffers[ch_a]
    for i in range(MAX_RADIO_TRANSCRIPTS + 5):
        buf.append(TranscriptLine(timestamp="t", text=str(i), channel_id=ch_a))
    assert len(buf) == MAX_RADIO_TRANSCRIPTS
    assert buf[-1].text == str(MAX_RADIO_TRANSCRIPTS + 4)
    assert len(monitor.buffer_for(ch_b)) == 0


def test_channel_select_retunes_index():
    monitor = VoiceMonitor(channels=COMMON_MARINE_CHANNELS)
    last = len(monitor.channels) - 1
    monitor.select_index(last)
    assert monitor.selected_index == last
    monitor.channel_up()
    assert monitor.selected_index == last - 1


def test_channel_pagination():
    many = COMMON_MARINE_CHANNELS * 2
    monitor = VoiceMonitor(channels=many)
    monitor.select_index(RADIO_CHANNEL_PAGE_SIZE)
    assert monitor.page_index == 1
    assert len(monitor.page_channels()) <= RADIO_CHANNEL_PAGE_SIZE
    monitor.channel_page_up()
    assert monitor.page_index == 0


def test_process_iq_queues_transcription():
    monitor = VoiceMonitor(channels=COMMON_MARINE_CHANNELS[:1])
    monitor._transcriber = type(
        "Stub",
        (),
        {
            "transcribe": staticmethod(lambda _audio: "distress call"),
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
        monitor.process_iq(b"\x00" * 200, now=time.time())
        time.sleep(0.1)
    lines = list(monitor.buffer_for())
    assert len(lines) == 1
    assert "distress" in lines[0].text
