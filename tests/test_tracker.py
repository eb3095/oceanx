from __future__ import annotations

import time
from types import SimpleNamespace

from oceanx.decode.tracker import VesselTracker


def test_tracker_ingest_and_update():
    tracker = VesselTracker()
    msg = SimpleNamespace(mmsi=123456789, shipname="FERRY", speed=10.5, course=90.0)
    vessel = tracker.ingest(msg, now=100.0)
    assert vessel is not None
    assert vessel.mmsi == "123456789"
    assert vessel.name == "FERRY"
    assert vessel.sog == 10.5
    assert vessel.cog == 90.0
    assert vessel.message_count == 1
    msg2 = SimpleNamespace(mmsi=123456789, speed=11.0)
    vessel2 = tracker.ingest(msg2, now=120.0)
    assert vessel2 is not None
    assert vessel2.message_count == 2
    assert vessel2.sog == 11.0


def test_tracker_ignores_missing_mmsi():
    tracker = VesselTracker()
    msg = SimpleNamespace(name="NO-ID")
    assert tracker.ingest(msg) is None
    assert tracker.total_messages == 0


def test_tracker_purge_stale():
    tracker = VesselTracker()
    tracker.ingest(SimpleNamespace(mmsi=1), now=time.time() - 1_000)
    tracker.ingest(SimpleNamespace(mmsi=2), now=time.time())
    tracker.purge_stale(time.time(), stale_sec=100.0)
    assert "1" not in tracker.vessels
    assert "2" in tracker.vessels
