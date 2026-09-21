"""OMS Engine visual tokens (aligned with oms-engine-mockup reference)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    bg: str
    panel: str
    line: str
    ink: str
    ink_muted: str
    navy: str
    navy_2: str
    teal: str
    green: str
    green_soft: str
    red: str
    red_soft: str
    amber: str
    amber_soft: str
    blue: str
    log_bg: str
    log_fg: str
    hover: str
    sub: str
    mono: str = "Consolas"
    ui: str = "Segoe UI"


LIGHT = Palette(
    bg="#f4f6f9",
    panel="#ffffff",
    line="#e3e8ef",
    ink="#0f1b2d",
    ink_muted="#6b7788",
    navy="#0f1b2d",
    navy_2="#182640",
    teal="#14b8a6",
    green="#16a34a",
    green_soft="#e7f6ec",
    red="#dc2626",
    red_soft="#fdeaea",
    amber="#f59e0b",
    amber_soft="#fff4dc",
    blue="#2563eb",
    log_bg="#0b1220",
    log_fg="#c9d4e4",
    hover="#eef8f6",
    sub="#fafbfd",
)

DARK = Palette(
    bg="#0b1220",
    panel="#111a2b",
    line="#1e2a40",
    ink="#e6ecf5",
    ink_muted="#8b99b0",
    navy="#070d18",
    navy_2="#121c2e",
    teal="#14b8a6",
    green="#34d399",
    green_soft="#1a2e28",
    red="#f87171",
    red_soft="#2a1c1c",
    amber="#fbbf24",
    amber_soft="#2a2418",
    blue="#60a5fa",
    log_bg="#0b1220",
    log_fg="#c9d4e4",
    hover="#0f2a2c",
    sub="#0e1626",
)
