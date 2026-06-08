from __future__ import annotations

from io import StringIO

from rich.console import Console

from oceanx.config import SnifferConfig
from oceanx.radio.voice_monitor import TranscriptLine, VoiceMonitor
from oceanx.ui.radio_display import RadioDisplay


def test_radio_dashboard_renders_channel_and_transcript():
    monitor = VoiceMonitor()
    channel = monitor.selected_channel()
    monitor.buffer_for(channel.channel_id).append(
        TranscriptLine(
            timestamp="12:00:00",
            text="vessel traffic service active",
            channel_id=channel.channel_id,
        )
    )
    display = RadioDisplay(monitor, SnifferConfig.from_preset().radio)
    buf = StringIO()
    console = Console(file=buf, width=120, force_terminal=True)
    console.print(display.render())
    text = buf.getvalue()
    assert "Marine VHF Radio" in text
    assert channel.name in text
    assert "vessel traffic service active" in text
    assert "A AIS" in text
