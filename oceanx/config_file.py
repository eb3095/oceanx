"""Persistent user configuration at ~/.config/oceanx/config.json."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any, List, Optional

from oceanx.ais.channel_defaults import DEFAULT_AIS_CHANNELS
from oceanx.ais.channels import parse_ais_channels
from oceanx.config import SnifferConfig
from oceanx.radio.channel_defaults import DEFAULT_RADIO_CHANNELS
from oceanx.radio.channels import parse_config_channels

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "oceanx"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.json"


@dataclass
class UserConfig:
    backend: str = "auto"
    lna: int = 32
    vga: int = 48
    amp_enable: bool = True
    tuner_gain: int = 40
    ppm_error: int = 0
    sound_enabled: bool = True
    refresh_hz: float = 2.0
    show_banner: bool = True
    replay_file: Optional[str] = None
    radio_channels: Optional[List[dict[str, Any]]] = None
    ais_channels: Optional[List[dict[str, Any]]] = None

    @classmethod
    def defaults(cls) -> UserConfig:
        return cls(
            radio_channels=[dict(ch) for ch in DEFAULT_RADIO_CHANNELS],
            ais_channels=[dict(ch) for ch in DEFAULT_AIS_CHANNELS],
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UserConfig:
        known = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_sniffer_config(self) -> SnifferConfig:
        radio = parse_config_channels(self.radio_channels)
        ais = parse_ais_channels(self.ais_channels)
        from oceanx.radio.backends import resolve_backend

        return SnifferConfig.from_preset(
            backend=resolve_backend(self.backend),
            lna=self.lna,
            vga=self.vga,
            amp_enable=self.amp_enable,
            tuner_gain=self.tuner_gain,
            ppm_error=self.ppm_error,
            refresh_hz=self.refresh_hz,
            sound_enabled=self.sound_enabled,
            radio_channels=radio,
            ais_channels=ais,
        )


class ConfigStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or DEFAULT_CONFIG_PATH

    def ensure(self) -> UserConfig:
        if not self.path.exists():
            self.write(UserConfig.defaults())
        return self.load()

    def load(self) -> UserConfig:
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError(f"Config must be a JSON object: {self.path}")
        return UserConfig.from_dict(raw)

    def write(self, config: UserConfig) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(config.to_dict(), indent=2, sort_keys=True)
        self.path.write_text(payload + "\n", encoding="utf-8")
