"""Vice City dark glassmorphism color tokens, DWM helpers, and QSS stylesheets."""

from __future__ import annotations

import ctypes
import logging
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

logger = logging.getLogger(__name__)

# Core Vice City Neon & Glass Palette
BG_TOP = "#0B0E17"
BG_BOTTOM = "#18122B"

CYAN = "#00F0FF"
MAGENTA = "#FF2E93"
AMBER = "#FFB800"
EMERALD = "#00E676"
CRIMSON = "#FF4D6D"
VIOLET = "#A78BFA"
TEXT_PRIMARY = "#F1F5F9"
TEXT_SECONDARY = "#94A3B8"
TEXT_MUTED = "#64748B"

BADGE_COLORS: dict[str, tuple[str, str]] = {
    "CPU": ("#00F0FF", "rgba(0, 240, 255, 0.14)"),
    "GPU": ("#A78BFA", "rgba(167, 139, 250, 0.16)"),
    "RT": ("#FF2E93", "rgba(255, 46, 147, 0.16)"),
    "VRAM": ("#FFB800", "rgba(255, 184, 0, 0.15)"),
    "RAM": ("#00E676", "rgba(0, 230, 118, 0.14)"),
}


def apply_windows_backdrop(widget: QWidget) -> None:
    """Enable Windows 11 dark titlebar & Mica/Acrylic backdrop when supported."""
    if sys.platform != "win32":
        return
    try:
        hwnd = int(widget.winId())
        dwmapi = ctypes.windll.dwmapi
        # DWMWA_USE_IMMERSIVE_DARK_MODE (20)
        dark_mode = ctypes.c_int(1)
        dwmapi.DwmSetWindowAttribute(
            hwnd,
            20,
            ctypes.byref(dark_mode),
            ctypes.sizeof(dark_mode),
        )
        # DWMWA_CAPTION_COLOR (35): match dark Vice City header (#0B0E17 -> COLORREF 0x00170E0B)
        caption_color = ctypes.c_int(0x00170E0B)
        dwmapi.DwmSetWindowAttribute(
            hwnd,
            35,
            ctypes.byref(caption_color),
            ctypes.sizeof(caption_color),
        )
        # DWMWA_SYSTEMBACKDROP_TYPE (38): 2 = Mica, 3 = Acrylic
        backdrop_type = ctypes.c_int(2)
        dwmapi.DwmSetWindowAttribute(
            hwnd,
            38,
            ctypes.byref(backdrop_type),
            ctypes.sizeof(backdrop_type),
        )
    except (OSError, AttributeError, ValueError) as exc:
        # Safe fallback on Windows 10, older builds, or headless/offscreen runs.
        logger.debug("DWM backdrop unavailable: %s", exc)


def fps_accent_color(fps: float) -> str:
    """Return Vice City status color for a given FPS threshold."""
    if fps >= 60.0:
        return EMERALD
    if fps >= 45.0:
        return CYAN
    if fps >= 30.0:
        return AMBER
    return CRIMSON


GLOBAL_STYLESHEET = """
QMainWindow, QWidget#CentralRoot {
    background: transparent;
    color: #F1F5F9;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 12px;
}

QLabel {
    color: #F1F5F9;
    background: transparent;
}

QLabel#AppTitle {
    font-size: 20px;
    font-weight: 800;
    letter-spacing: 0.8px;
    color: #FFFFFF;
}

QLabel#AppSubtitle {
    font-size: 11px;
    color: #94A3B8;
}

QLabel#SectionTitle {
    font-size: 13px;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: 0.4px;
}

QLabel#FieldLabel {
    font-size: 11px;
    font-weight: 600;
    color: #CBD5E1;
}

QLabel#SpecChip {
    font-size: 10.5px;
    color: #94A3B8;
    background-color: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 7px;
    padding: 4px 8px;
}

QFrame#GlassCard {
    background-color: rgba(255, 255, 255, 0.055);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 14px;
}

QFrame#GlassCard:hover {
    border: 1px solid rgba(255, 255, 255, 0.22);
}

QFrame#SettingRow {
    background-color: rgba(255, 255, 255, 0.035);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 10px;
}

QFrame#SettingRow:hover {
    background-color: rgba(255, 255, 255, 0.065);
    border: 1px solid rgba(0, 240, 255, 0.30);
}

QFrame#HeroTile {
    background-color: rgba(11, 14, 23, 0.55);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 12px;
}

QScrollArea {
    background: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background: transparent;
}

QScrollBar:vertical {
    background: transparent;
    width: 7px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.18);
    border-radius: 3px;
    min-height: 28px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(0, 240, 255, 0.45);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
    height: 0px;
}

QComboBox {
    background-color: rgba(15, 20, 34, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 9px;
    padding: 5px 10px;
    color: #F8FAFC;
    font-weight: 600;
    min-height: 20px;
    min-width: 0px;
}

QComboBox:hover {
    border: 1px solid rgba(0, 240, 255, 0.55);
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #121726;
    border: 1px solid rgba(0, 240, 255, 0.45);
    border-radius: 8px;
    selection-background-color: rgba(0, 240, 255, 0.22);
    selection-color: #FFFFFF;
    color: #E2E8F0;
    padding: 4px;
    outline: none;
}

QPushButton#PresetBtn {
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 8px;
    padding: 5px 8px;
    color: #E2E8F0;
    font-size: 11px;
    font-weight: 600;
    min-width: 0px;
}

QPushButton#PresetBtn:hover {
    background-color: rgba(0, 240, 255, 0.14);
    border: 1px solid rgba(0, 240, 255, 0.55);
    color: #FFFFFF;
}

QPushButton#PresetBtn[active="true"] {
    background-color: rgba(0, 240, 255, 0.22);
    border: 1px solid #00F0FF;
    color: #FFFFFF;
}

QPushButton#MagicBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00C2FF, stop:1 #FF2E93);
    border: 1px solid rgba(255, 255, 255, 0.35);
    border-radius: 10px;
    padding: 9px 14px;
    color: #FFFFFF;
    font-size: 12.5px;
    font-weight: 800;
    letter-spacing: 0.3px;
}

QPushButton#MagicBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2CF2FF, stop:1 #FF52A8);
    border: 1px solid #FFFFFF;
}

QPushButton#MagicBtn:pressed {
    padding-top: 10px;
    padding-bottom: 8px;
}

QPushButton#GhostBtn {
    background-color: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 10px;
    padding: 8px 12px;
    color: #E2E8F0;
    font-size: 11.5px;
    font-weight: 600;
}

QPushButton#GhostBtn:hover {
    background-color: rgba(255, 255, 255, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.32);
}

QPushButton#AccordionHeader {
    background: transparent;
    border: none;
    text-align: left;
    color: #FFFFFF;
    font-size: 12.5px;
    font-weight: 700;
    padding: 2px 0px;
}

QPushButton#PillBtn {
    background-color: rgba(255, 255, 255, 0.045);
    border: 1px solid rgba(255, 255, 255, 0.11);
    border-radius: 7px;
    padding: 4px 6px;
    color: #CBD5E1;
    font-size: 10.5px;
    font-weight: 600;
    min-width: 0px;
}

QPushButton#PillBtn:hover {
    background-color: rgba(255, 255, 255, 0.10);
    border: 1px solid rgba(255, 255, 255, 0.28);
    color: #FFFFFF;
}

QPushButton#PillBtn:checked {
    background-color: rgba(0, 240, 255, 0.22);
    border: 1px solid #00F0FF;
    color: #FFFFFF;
}

QPushButton#PillBtn:disabled {
    background-color: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    color: #475569;
}

QSlider::groove:horizontal {
    height: 6px;
    background: rgba(255, 255, 255, 0.10);
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00F0FF, stop:1 #FF2E93);
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #FFFFFF;
    border: 2px solid #00F0FF;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 8px;
}

QToolTip {
    background-color: #111625;
    color: #F1F5F9;
    border: 1px solid #00F0FF;
    border-radius: 6px;
    padding: 6px 9px;
    font-size: 11.5px;
}
"""
