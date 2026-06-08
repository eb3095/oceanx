"""String formatting helpers for terminal UI."""

from __future__ import annotations

from typing import List

from oceanx.models.vessel import Vessel


def fmt_optional(value: object, suffix: str = "", na: str = "—") -> str:
    if value is None or value == "":
        return na
    if isinstance(value, float):
        return f"{value:.1f}{suffix}"
    return f"{value}{suffix}"


def message_summary(vessel: Vessel) -> str:
    parts: List[str] = []
    if vessel.name:
        parts.append(vessel.name)
    if vessel.sog is not None:
        parts.append(f"{vessel.sog:.1f} kt")
    if vessel.cog is not None:
        parts.append(f"{vessel.cog:.0f}°")
    if vessel.lat is not None and vessel.lon is not None:
        parts.append(f"{vessel.lat:.4f}, {vessel.lon:.4f}")
    return " · ".join(parts) if parts else "—"
