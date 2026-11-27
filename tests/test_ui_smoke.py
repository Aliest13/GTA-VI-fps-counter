"""Offscreen PySide6 smoke tests for MainWindow wiring and live updates."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

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

    # Initial Desktop preset -> ~50-56 Base FPS
    initial_fps = float(window._hero_card._avg_value.text())
    assert 48.0 <= initial_fps <= 58.0

    # Switch to High-End (9800X3D + 5090) and verify MFG 4x unlocks
    window._apply_hardware_preset("high_end")
    qapp.processEvents()
    assert window._fg_pills._buttons["4x"].isEnabled() is True
    window._fg_pills.set_selected("4x")
    window._fg_pills.changed.emit("4x")
    qapp.processEvents()
    assert float(window._hero_card._fg_value.text()) >= 200.0

    # Switch back to Laptop preset -> MFG 4x auto-falls back and disables
    window._apply_hardware_preset("my_laptop")
    qapp.processEvents()
    assert window._fg_pills._buttons["4x"].isEnabled() is False
    assert window._fg_pills.current_id() == "2x"
    assert "Unified" in window._vram_bar._title

    # Desktop preset + Auto-Optimize -> reaches >= 60 Base FPS and enables Undo
    window._apply_hardware_preset("my_desktop")
    window._apply_settings_preset("ps5_xsx")
    window._fg_pills.set_selected("off")
    window._fg_pills.changed.emit("off")
    qapp.processEvents()
    window._on_auto_optimize()
    qapp.processEvents()
    assert float(window._hero_card._avg_value.text()) >= 60.0
    assert window._undo_btn.isVisible() is True

    # Undo restores original < 60 Base FPS
    window._on_undo_optimize()
    qapp.processEvents()
    assert float(window._hero_card._avg_value.text()) < 60.0

    # Toggle EN / Persian language
    window._lang_btn.click()
    qapp.processEvents()
    assert window._lang == "fa"
    window._lang_btn.click()
    qapp.processEvents()
    assert window._lang == "en"

    window.close()
