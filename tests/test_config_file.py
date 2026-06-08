from __future__ import annotations

import json
from pathlib import Path

from oceanx.config_file import ConfigStore, UserConfig


def test_user_config_defaults():
    cfg = UserConfig.defaults()
    assert cfg.lna == 32
    assert cfg.vga == 48
    assert cfg.sound_enabled is True


def test_user_config_round_trip():
    cfg = UserConfig(lna=24, vga=40)
    restored = UserConfig.from_dict(cfg.to_dict())
    assert restored.lna == 24
    assert restored.vga == 40


def test_config_store_creates_default_file(tmp_path: Path):
    path = tmp_path / "oceanx" / "config.json"
    store = ConfigStore(path)
    cfg = store.ensure()
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["show_banner"] is True
    assert cfg.show_banner is True


def test_to_sniffer_config_has_ais_and_radio():
    cfg = UserConfig.defaults()
    sn = cfg.to_sniffer_config()
    assert len(sn.ais_channels) >= 2
    assert len(sn.radio_channels) >= 10
