"""OceanX live capture and replay orchestrator."""

from __future__ import annotations

import signal
import time
from typing import Literal

import numpy as np
from rich.live import Live

from oceanx.ais.monitor import AisMonitor
from oceanx.config import AIS_CENTER_HZ, SnifferConfig
from oceanx.decode.tracker import VesselTracker
from oceanx.log_writer import LogWriter
from oceanx.radio.hackrf import HackRFReceiver
from oceanx.radio.voice_monitor import VoiceMonitor
from oceanx.ui.display import ConsoleDisplay
from oceanx.ui.keyboard import drain_keys, restore_terminal, terminal_session
from oceanx.ui.radio_display import RadioDisplay

DashboardMode = Literal["ais", "radio"]


class OceanXSniffer:
    def __init__(self, config: SnifferConfig) -> None:
        self.config = config
        self._log_writer = LogWriter()
        self.tracker = VesselTracker()
        self.display = ConsoleDisplay(config, self._log_writer)
        self.voice_monitor = VoiceMonitor(
            config.radio_channels, log_writer=self._log_writer
        )
        self.radio_display = RadioDisplay(self.voice_monitor, config.radio)
        self.ais_monitor = AisMonitor(
            config.ais_channels, self.tracker, log_writer=self._log_writer
        )
        self.dashboard: DashboardMode = "ais"
        self.receiver = HackRFReceiver(config.radio, freq_hz=self._tuned_frequency())

    def _tuned_frequency(self) -> int:
        if self.dashboard == "radio":
            return self.voice_monitor.selected_channel().freq_hz
        return AIS_CENTER_HZ

    def _apply_tuning(self) -> None:
        self.receiver.set_frequency(self._tuned_frequency())

    def set_dashboard(self, mode: DashboardMode) -> None:
        if self.dashboard == mode:
            return
        self.dashboard = mode
        self._apply_tuning()

    def _render(self, now: float):
        if self.dashboard == "radio":
            return self.radio_display.render()
        return self.display.render(self.tracker, now, self.config.radio)

    def _handle_keys(self, live: Live, last_render: float) -> tuple[bool, float]:
        for key in drain_keys():
            if key == "quit":
                return False, last_render
            if key == "dashboard_radio":
                self.set_dashboard("radio")
            elif key == "dashboard_ais":
                self.set_dashboard("ais")
            elif self.dashboard == "radio":
                if key == "channel_up":
                    self.voice_monitor.channel_up()
                    self._apply_tuning()
                elif key == "channel_down":
                    self.voice_monitor.channel_down()
                    self._apply_tuning()
                elif key == "first":
                    self.voice_monitor.channel_page_up()
                elif key == "last":
                    self.voice_monitor.channel_page_down()
                elif key == "prev":
                    self.voice_monitor.squelch_down()
                elif key == "next":
                    self.voice_monitor.squelch_up()
                elif key == "volume_up":
                    self.voice_monitor.volume_up()
                elif key == "volume_down":
                    self.voice_monitor.volume_down()
            else:
                self.display.handle_key(key, len(self.tracker.vessels))
            now = time.time()
            live.update(self._render(now))
            last_render = now
        return True, last_render

    def run_live(self) -> None:
        self.receiver.start()
        running = True

        def handle_sigint(_signum: int, _frame: object) -> None:
            nonlocal running
            running = False

        signal.signal(signal.SIGINT, handle_sigint)
        last_render = 0.0
        try:
            with terminal_session():
                with Live(
                    self._render(time.time()),
                    console=self.display.console,
                    refresh_per_second=self.config.refresh_hz,
                    screen=True,
                    transient=False,
                ) as live:
                    while running:
                        now = time.time()
                        running, last_render = self._handle_keys(live, last_render)
                        if not running:
                            break
                        chunk = self.receiver.read_chunk()
                        if chunk:
                            if self.dashboard == "ais":
                                self.ais_monitor.process_iq(chunk, now=now)
                                for vessel in self.tracker.vessels.values():
                                    if vessel.last_seen >= now - 0.2:
                                        self.display.push_message(vessel, now)
                            else:
                                self.voice_monitor.process_iq(chunk, now)
                        elif self.receiver.exited:
                            raise RuntimeError(
                                "hackrf_transfer exited. Check HackRF USB connection."
                            )
                        if now - last_render >= 1.0 / self.config.refresh_hz:
                            live.update(self._render(now))
                            last_render = now
        finally:
            self.voice_monitor.shutdown()
            self.receiver.stop()
            self._log_writer.close()
            restore_terminal()

    def run_file(self, path: str) -> None:
        try:
            with open(path, "rb") as fh:
                data = fh.read()
            iq = np.frombuffer(data, dtype=np.int8).tobytes()
            self.ais_monitor.process_iq(iq, now=time.time())
            self.display.print_once(self.tracker, time.time(), self.config.radio)
        finally:
            self._log_writer.close()
