from __future__ import annotations

import time
from io import StringIO
from unittest.mock import patch

from rich.console import Console

from oceanx.config import AIS_CHANNEL_PAGE_SIZE, SnifferConfig
from oceanx.decode.tracker import VesselTracker
from oceanx.models.vessel import Vessel
from oceanx.ui.display import ConsoleDisplay
from oceanx.ui.sounds import DiscoverySound


def test_push_message_tracks_recent_newest_on_top():
    display = ConsoleDisplay(SnifferConfig.from_preset())
    v1 = Vessel(mmsi="111111111")
    v2 = Vessel(mmsi="222222222")
    display.push_message(v1, 100.0)
    display.push_message(v2, 101.0)
    panel = display._recent_panel()
    rendered = Console(file=StringIO(), width=120, record=True)
    rendered.print(panel)
    text = rendered.export_text()
    assert text.index("222222222") < text.index("111111111")


def test_vessel_table_pagination_oldest_first():
    display = ConsoleDisplay(SnifferConfig.from_preset())
    display.newest_first = False
    tracker = VesselTracker()
    now = 1000.0
    ordered = []
    for i in range(AIS_CHANNEL_PAGE_SIZE + 3):
        v = Vessel(
            mmsi=f"{i:09d}", first_seen=now + i, last_seen=now + i, message_count=1
        )
        tracker.vessels[v.mmsi] = v
        ordered.append(v)
    display.page_index = 1
    table = display._vessel_table(ordered, now + AIS_CHANNEL_PAGE_SIZE)
    assert "page 2/2" in table.title
    assert len(table.rows) == 3


def test_g_and_g_keys_switch_sort():
    display = ConsoleDisplay(SnifferConfig.from_preset())
    display.page_index = 2
    display.handle_key("first", 100)
    assert display.newest_first is False
    assert display.page_index == 0
    display.handle_key("last", 100)
    assert display.newest_first is True
    assert display.page_index == 0


def test_discovery_sound_once_per_mmsi():
    display = ConsoleDisplay(SnifferConfig.from_preset(sound_enabled=True))
    v = Vessel(mmsi="123123123")
    with patch.object(DiscoverySound, "play") as play:
        display.push_message(v, time.time())
        display.push_message(v, time.time() + 1)
        assert play.call_count == 1
