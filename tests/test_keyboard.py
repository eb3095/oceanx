from __future__ import annotations

from unittest.mock import patch

from oceanx.ui import keyboard
from oceanx.ui.keyboard import (
    _decode_key,
    _take_first_key,
    drain_keys,
    poll_key,
    reset_pending,
)


def setup_function() -> None:
    reset_pending()


def test_decode_key_modes():
    assert _decode_key("A") == "dashboard_ais"
    assert _decode_key("R") == "dashboard_radio"


def test_decode_key_brackets_and_arrows():
    assert _decode_key("[") == "prev"
    assert _decode_key("]") == "next"
    assert _decode_key("\x1b[D") == "prev"
    assert _decode_key("\x1b[C") == "next"
    assert _decode_key("\x1b[A") == "channel_up"
    assert _decode_key("\x1b[B") == "channel_down"


def test_take_first_key_leaves_remainder():
    key, rest = _take_first_key("\x1b[D\x1b[C")
    assert key == "\x1b[D"
    assert rest == "\x1b[C"


def test_poll_key_and_drain():
    keyboard._pending = ""
    with patch("oceanx.ui.keyboard.sys.stdin.isatty", return_value=True):
        with patch(
            "oceanx.ui.keyboard.select.select",
            side_effect=[([object()], [], []), ([], [], [])],
        ):
            with patch(
                "oceanx.ui.keyboard._read_available", side_effect=["\x1b[D", ""]
            ):
                assert poll_key() == "prev"
                assert drain_keys() == []
