"""OceanX command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from oceanx import __app_name__, __version__
from oceanx.app.sniffer import OceanXSniffer
from oceanx.config import SnifferConfig
from oceanx.config_file import DEFAULT_CONFIG_PATH, ConfigStore, UserConfig
from oceanx.radio.channels import parse_config_channels
from oceanx.ais.channels import parse_ais_channels

BANNER = r"""
   ___                    __  __
  /___\___ ___  __ _ _ __ \ \/ /
 //  // __/ _ \/ _` | '_ \ \  / 
/ \_// (_|  __/ (_| | | | |/  \ 
\___/ \___\___|\__,_|_| |_/_/\_\
                                 
"""


def build_parser(defaults: UserConfig) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=__app_name__,
        description=f"{__app_name__} v{__version__} — marine AIS + VHF receiver for HackRF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            f"Config file: {DEFAULT_CONFIG_PATH}\n"
            "CLI options override config values.\n"
            "Setup: brew install hackrf && make dev-install"
        ),
    )
    parser.add_argument(
        "--config",
        type=Path,
        help=f"Path to config JSON (default: {DEFAULT_CONFIG_PATH})",
    )
    parser.add_argument(
        "--file",
        default=defaults.replay_file,
        help="Replay raw HackRF IQ capture instead of live RX",
    )
    parser.add_argument(
        "--lna", type=int, default=defaults.lna, help="LNA gain 0-40 dB"
    )
    parser.add_argument(
        "--vga", type=int, default=defaults.vga, help="VGA gain 0-62 dB"
    )
    amp = parser.add_mutually_exclusive_group()
    amp.add_argument(
        "--amp",
        dest="amp_enable",
        action="store_true",
        help="Enable HackRF RF amplifier (+11 dB)",
    )
    amp.add_argument(
        "--no-amp",
        dest="amp_enable",
        action="store_false",
        help="Disable HackRF RF amplifier",
    )
    parser.set_defaults(amp_enable=defaults.amp_enable)
    sound = parser.add_mutually_exclusive_group()
    sound.add_argument(
        "--sound",
        dest="sound_enabled",
        action="store_true",
        help="Play sound on first new MMSI",
    )
    sound.add_argument(
        "--no-sound",
        dest="sound_enabled",
        action="store_false",
        help="Disable discovery sound",
    )
    parser.set_defaults(sound_enabled=defaults.sound_enabled)
    parser.add_argument(
        "--refresh",
        type=float,
        default=defaults.refresh_hz,
        help="Dashboard refresh rate in Hz",
    )
    banner = parser.add_mutually_exclusive_group()
    banner.add_argument(
        "--banner",
        dest="show_banner",
        action="store_true",
        help="Show ASCII banner on startup",
    )
    banner.add_argument(
        "--no-banner",
        dest="show_banner",
        action="store_false",
        help="Skip ASCII banner on startup",
    )
    parser.set_defaults(show_banner=defaults.show_banner)
    return parser


def resolve_config(args: argparse.Namespace, user: UserConfig) -> SnifferConfig:
    radio = parse_config_channels(user.radio_channels)
    ais = parse_ais_channels(user.ais_channels)
    return SnifferConfig.from_preset(
        lna=args.lna,
        vga=args.vga,
        amp_enable=args.amp_enable,
        refresh_hz=args.refresh,
        sound_enabled=args.sound_enabled,
        radio_channels=radio,
        ais_channels=ais,
    )


def main(argv: list[str] | None = None) -> None:
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--config", type=Path, default=None)
    pre_args, remaining = pre_parser.parse_known_args(argv)
    store = ConfigStore(pre_args.config)
    user_defaults = store.ensure()
    parser = build_parser(user_defaults)
    args = parser.parse_args(remaining)
    if args.config is not None:
        store = ConfigStore(args.config)
        store.ensure()
    if args.show_banner:
        print(BANNER)
    user_cfg = store.load()
    config = resolve_config(args, user_cfg)
    sniffer = OceanXSniffer(config)
    replay = args.file or user_defaults.replay_file
    if replay:
        sniffer.run_file(replay)
    else:
        sniffer.run_live()


if __name__ == "__main__":
    main(sys.argv[1:])
