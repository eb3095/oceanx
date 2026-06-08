from __future__ import annotations

from oceanx.models.vessel import Vessel


def test_vessel_defaults():
    v = Vessel(mmsi="123456789")
    assert v.name == ""
    assert v.message_count == 0
    assert v.first_seen <= v.last_seen
