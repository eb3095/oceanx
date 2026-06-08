from __future__ import annotations

from oceanx.radio.channels import COMMON_MARINE_CHANNELS, in_marine_band


def test_common_channels_have_unique_ids():
    ids = [ch.channel_id for ch in COMMON_MARINE_CHANNELS]
    assert len(ids) == len(set(ids))


def test_channel_freq_in_marine_band():
    for ch in COMMON_MARINE_CHANNELS:
        assert in_marine_band(ch)


def test_common_has_channel_16():
    ids = [ch.channel_id for ch in COMMON_MARINE_CHANNELS]
    assert "16" in ids
