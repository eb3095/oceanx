"""Rich terminal dashboard for OceanX AIS."""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, List, Optional, Set

from rich import box
from rich.align import Align
from rich.console import Console, Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from oceanx import __app_name__
from oceanx.config import (
    AIS_CHANNEL_PAGE_SIZE,
    MAX_RECENT_MESSAGES_STORE,
    RECENT_MESSAGES_DISPLAY,
    RadioConfig,
    SnifferConfig,
)
from oceanx.decode.tracker import VesselTracker
from oceanx.log_writer import LogWriter
from oceanx.models.vessel import Vessel
from oceanx.ui.bars import FullWidthBar
from oceanx.ui.formatters import fmt_optional, message_summary
from oceanx.ui.sounds import DiscoverySound

def _dim_text(content: str) -> Text:
    return Text.from_markup(f"[dim]{content}[/]")


@dataclass
class RecentMessage:
    timestamp: str
    mmsi: str
    summary: str
    is_new_vessel: bool


class ConsoleDisplay:
    def __init__(
        self, config: SnifferConfig, log_writer: LogWriter | None = None
    ) -> None:
        self.console = Console()
        self.sound_enabled = config.sound_enabled
        self._log = log_writer
        self.recent: Deque[RecentMessage] = deque(maxlen=MAX_RECENT_MESSAGES_STORE)
        self.seen_mmsi: Set[str] = set()
        self.notified_mmsi: Set[str] = set()
        self.page_index = 0
        self.newest_first = True

    def push_message(self, vessel: Vessel, now: float) -> None:
        is_new = vessel.mmsi not in self.seen_mmsi
        self.seen_mmsi.add(vessel.mmsi)
        entry = RecentMessage(
            timestamp=time.strftime("%H:%M:%S", time.localtime(now)),
            mmsi=vessel.mmsi,
            summary=message_summary(vessel),
            is_new_vessel=is_new,
        )
        self.recent.append(entry)
        self.maybe_play_discovery(vessel)
        if self._log is not None:
            self._log.log_ais(f"{entry.timestamp} {entry.mmsi} {entry.summary}")

    def maybe_play_discovery(self, vessel: Vessel) -> None:
        if not self.sound_enabled or vessel.mmsi in self.notified_mmsi:
            return
        self.notified_mmsi.add(vessel.mmsi)
        DiscoverySound.play()

    def handle_key(self, key: str, total_rows: int) -> None:
        pages = max(1, math.ceil(total_rows / AIS_CHANNEL_PAGE_SIZE))
        if key == "prev":
            self.page_index = max(0, self.page_index - 1)
        elif key == "next":
            self.page_index = min(pages - 1, self.page_index + 1)
        elif key == "first":
            self.newest_first = False
            self.page_index = 0
        elif key == "last":
            self.newest_first = True
            self.page_index = 0

    def sync_page(self, total_rows: int) -> None:
        pages = max(1, math.ceil(total_rows / AIS_CHANNEL_PAGE_SIZE) if total_rows else 1)
        self.page_index = min(self.page_index, pages - 1)

    def _ordered_vessels(self, tracker: VesselTracker) -> List[Vessel]:
        rows = list(tracker.vessels.values())
        if self.newest_first:
            return sorted(rows, key=lambda v: (-v.first_seen, v.mmsi))
        return sorted(rows, key=lambda v: (v.first_seen, v.mmsi))

    def render(self, tracker: VesselTracker, now: float, radio: RadioConfig) -> Group:
        ordered = self._ordered_vessels(tracker)
        self.sync_page(len(ordered))
        return Group(
            self._header(),
            self._status_line(tracker, radio),
            self._vessel_table(ordered, now),
            self._recent_panel(),
            self._footer(),
        )

    def print_once(
        self, tracker: VesselTracker, now: float, radio: RadioConfig
    ) -> None:
        self.console.print(self.render(tracker, now, radio))

    @staticmethod
    def _header() -> FullWidthBar:
        return FullWidthBar(f" {__app_name__} — AIS Monitor 162 MHz ")

    def _status_line(self, tracker: VesselTracker, radio: RadioConfig) -> Text:
        text = Text()
        text.append("AIS A/B 161.975 / 162.025", style="bold cyan")
        text.append("  │  ")
        text.append(f"LNA {radio.lna_gain}", style="dim")
        text.append("  ")
        text.append(f"VGA {radio.vga_gain}", style="dim")
        text.append("  ")
        text.append(f"amp {'on' if radio.amp_enable else 'off'}", style="dim")
        text.append("  │  ")
        text.append(f"{len(tracker.vessels)} vessels", style="bold green")
        text.append("  │  ")
        text.append(f"{tracker.total_messages} decoded", style="dim")
        return text

    def _vessel_table(self, ordered: List[Vessel], now: float) -> Table:
        total = len(ordered)
        pages = max(1, math.ceil(total / AIS_CHANNEL_PAGE_SIZE) if total else 1)
        start = self.page_index * AIS_CHANNEL_PAGE_SIZE
        shown = ordered[start : start + AIS_CHANNEL_PAGE_SIZE]
        title = f"Vessels · page {self.page_index + 1}/{pages}" if total else "Vessels"
        table = Table(
            title=title,
            box=box.ROUNDED,
            header_style="bold magenta",
            border_style="blue",
            show_lines=False,
            expand=True,
        )
        table.add_column("MMSI", style="bold white")
        table.add_column("Name", style="cyan")
        table.add_column("SOG (kt)", justify="right", style="green")
        table.add_column("COG (°)", justify="right")
        table.add_column("HDG (°)", justify="right")
        table.add_column("Lat", style="dim")
        table.add_column("Lon", style="dim")
        table.add_column("Status")
        table.add_column("N", justify="right", style="dim")
        table.add_column("Age", justify="right", style="dim")
        if not shown:
            table.add_row("—", "listening…", "—", "—", "—", "—", "—", "—", "—", "—")
            return table
        for v in shown:
            table.add_row(
                v.mmsi,
                v.name or "—",
                fmt_optional(v.sog),
                fmt_optional(v.cog),
                fmt_optional(v.heading),
                fmt_optional(v.lat, "", na="—"),
                fmt_optional(v.lon, "", na="—"),
                v.nav_status or "—",
                str(v.message_count),
                f"{now - v.last_seen:.0f}s",
            )
        return table

    def _recent_panel(self) -> Panel:
        recent = list(self.recent)[-RECENT_MESSAGES_DISPLAY:]
        if not recent:
            body: RenderableType = _dim_text("Waiting for AIS messages…")
        else:
            lines: list[Text] = []
            for msg in reversed(recent):
                line = Text()
                line.append(f"{msg.timestamp}  ", style="dim")
                if msg.is_new_vessel:
                    line.append("NEW ", style="bold green")
                line.append(msg.mmsi, style="bold")
                line.append("  ")
                line.append(msg.summary, style="cyan")
                lines.append(line)
            body = Text("\n").join(lines)
        return Panel(
            body,
            title=f"[bold]Last {RECENT_MESSAGES_DISPLAY} AIS Messages[/bold]",
            border_style="green",
            padding=(0, 1),
            style="none",
        )

    def _footer(self) -> RenderableType:
        text = Text()
        text.append("←", style="bold cyan")
        text.append(" ")
        text.append("→", style="bold cyan")
        text.append("  [ ] pages", style="dim")
        text.append("  ·  ")
        text.append("g", style="bold cyan")
        text.append(" oldest", style="dim")
        text.append("  ·  ")
        text.append("G", style="bold cyan")
        text.append(" newest", style="dim")
        text.append("  ·  ")
        text.append("R", style="bold cyan")
        text.append(" radio", style="dim")
        text.append("  ·  ")
        text.append("A", style="bold cyan")
        text.append(" AIS", style="dim")
        text.append("  ·  ")
        text.append_text(_dim_text("Ctrl+C stop"))
        return Align.center(text)
