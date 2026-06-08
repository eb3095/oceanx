from __future__ import annotations

from oceanx.models.vessel import Vessel
from oceanx.ui.formatters import fmt_optional, message_summary


def test_fmt_optional_missing():
    assert fmt_optional(None) == "—"


def test_fmt_optional_float():
    assert fmt_optional(123.456, "°") == "123.5°"


def test_message_summary_fields():
    v = Vessel(mmsi="123", name="TUG", sog=9.7, cog=181.2, lat=40.1, lon=-73.9)
    summary = message_summary(v)
    assert "TUG" in summary
    assert "9.7 kt" in summary
    assert "181°" in summary
    assert "40.1000" in summary
