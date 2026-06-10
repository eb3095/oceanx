"""RTL-SDR IQ capture via rtl_sdr."""

from __future__ import annotations

import os
import select
import shutil
import subprocess
import time
from typing import Optional

from oceanx.config import CHUNK_SAMPLES, RTL_SDR_BINARY_PATHS, SAMPLE_RATE, RadioConfig
from oceanx.radio.process_util import stop_subprocess

_USB_SETTLE_SEC = 0.25
_last_usb_release = 0.0


class RtlSdrReceiver:
    def __init__(
        self,
        config: RadioConfig,
        *,
        freq_hz: int,
        sample_rate: int = SAMPLE_RATE,
    ) -> None:
        self._config = config
        self._freq_hz = freq_hz
        self._sample_rate = sample_rate
        self._proc: Optional[subprocess.Popen[bytes]] = None
        self._stderr: bytes = b""

    @staticmethod
    def find_binary() -> Optional[str]:
        for candidate in RTL_SDR_BINARY_PATHS:
            path = shutil.which(candidate) if "/" not in candidate else candidate
            if path and os.path.isfile(path) and os.access(path, os.X_OK):
                return path
        return None

    def start(self) -> None:
        global _last_usb_release
        delay = _USB_SETTLE_SEC - (time.monotonic() - _last_usb_release)
        if delay > 0:
            time.sleep(delay)
        rtl_sdr = self.find_binary()
        if not rtl_sdr:
            raise RuntimeError("rtl_sdr not found. Install with: brew install rtl-sdr")
        cmd = [
            rtl_sdr,
            "-f",
            str(self._freq_hz),
            "-s",
            str(self._sample_rate),
            "-g",
            str(self._config.tuner_gain),
            "-p",
            str(self._config.ppm_error),
            "-",
        ]
        self._stderr = b""
        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )

    def read_chunk(self, timeout: float = 0.05) -> bytes:
        if not self._proc or not self._proc.stdout:
            return b""
        self._poll_stderr()
        fd = self._proc.stdout.fileno()
        ready, _, _ = select.select([fd], [], [], timeout)
        if not ready:
            return b""
        return os.read(fd, CHUNK_SAMPLES * 2)

    def set_frequency(self, freq_hz: int) -> None:
        if freq_hz == self._freq_hz:
            return
        running = self._proc is not None
        if running:
            self.stop()
        self._freq_hz = freq_hz
        if running:
            self.start()

    @property
    def freq_hz(self) -> int:
        return self._freq_hz

    @property
    def running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    @property
    def exited(self) -> bool:
        return self._proc is not None and self._proc.poll() is not None

    def exit_message(self) -> str:
        detail = self._stderr.decode("utf-8", errors="replace").strip()
        if detail:
            line = detail.splitlines()[-1]
            return f"rtl_sdr exited: {line}"
        return "rtl_sdr exited. Check RTL-SDR USB connection."

    def stop(self, *, fast: bool = False) -> None:
        global _last_usb_release
        if self._proc:
            stop_subprocess(self._proc, fast=fast, prefer_sigint=not fast)
            self._proc = None
            _last_usb_release = time.monotonic()

    def _poll_stderr(self) -> None:
        if not self._proc or not self._proc.stderr:
            return
        while True:
            ready, _, _ = select.select([self._proc.stderr.fileno()], [], [], 0)
            if not ready:
                break
            chunk = os.read(self._proc.stderr.fileno(), 4096)
            if not chunk:
                break
            self._stderr += chunk
