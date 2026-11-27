"""Offscreen PySide6 smoke tests for MainWindow wiring and live updates."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if isinstance(app, QApplication):
        return app
    return QApplication([])


def test_main_window_presets_and_live_updates(qapp: QApplication) -> None:
    window = MainWindow()
    window.resize(1440, 880)
    window.show()
    qapp.processEvents()

    # Initial Mainstream Desktop preset (7600X + RX 9060 XT 16GB @ 1440p FSR Quality PS5)
    initial_fps = float(window._hero_card._avg_value.text())
    assert 60.0 <= initial_fps <= 75.0

    # Switch to High-End (9800X3D + 5090) and verify MFG 4x unlocks
    window._apply_hardware_preset("high_end")
    qapp.processEvents()
    assert window._fg_pills._buttons["4x"].isEnabled() is True
    window._fg_pills.set_selected("4x")
    window._fg_pills.changed.emit("4x")
    qapp.processEvents()
    assert float(window._hero_card._fg_value.text()) >= 200.0

    # Switch to Ultrabook preset -> MFG 4x auto-falls back and disables, concise meter labels
    window._apply_hardware_preset("ultrabook_igpu")
    qapp.processEvents()
    assert window._fg_pills._buttons["4x"].isEnabled() is False
    assert window._fg_pills.current_id() == "2x"
    assert window._vram_bar._title == "Unified Pool (OS+CPU+GPU)"
    assert window._ram_bar._title == "VRAM Share (In Pool)"

    # Laptop at 720p + XeSS Balanced + Auto-Optimize stays realistically capped <= 44 FPS
    window._res_pills.set_selected("720p")
    window._res_pills.changed.emit("720p")
    window._upscaler_pills.set_selected("balanced")
    window._upscaler_pills.changed.emit("balanced")
    window._fg_pills.set_selected("off")
    window._fg_pills.changed.emit("off")
    qapp.processEvents()
    window._on_auto_optimize()
    qapp.processEvents()
    assert float(window._hero_card._avg_value.text()) <= 44.0

    # Mainstream Desktop + All Ultra (<60 FPS) + Auto-Optimize -> reaches >= 60 Base FPS and enables Undo
    window._apply_hardware_preset("mid_range_desktop")
    window._res_pills.set_selected("1440p")
    window._res_pills.changed.emit("1440p")
    window._upscaler_pills.set_selected("quality")
    window._upscaler_pills.changed.emit("quality")
    window._apply_settings_preset("all_ultra")
    window._fg_pills.set_selected("off")
    window._fg_pills.changed.emit("off")
    qapp.processEvents()
    assert float(window._hero_card._avg_value.text()) < 60.0
    window._on_auto_optimize()
    qapp.processEvents()
    assert float(window._hero_card._avg_value.text()) >= 60.0
    assert window._undo_btn.isVisible() is True

    # Undo restores original < 60 Base FPS
    window._on_undo_optimize()
    qapp.processEvents()
    assert float(window._hero_card._avg_value.text()) < 60.0

    # Toggle EN / Persian language and check RTL/LTR layout direction
    window._lang_btn.click()
    qapp.processEvents()
    assert window._lang == "fa"
    assert window._diagnosis_box.layoutDirection() == Qt.LayoutDirection.RightToLeft
    window._lang_btn.click()
    qapp.processEvents()
    assert window._lang == "en"
    assert window._diagnosis_box.layoutDirection() == Qt.LayoutDirection.LeftToRight

    window.close()
