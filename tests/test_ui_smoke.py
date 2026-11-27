"""Offscreen PySide6 smoke tests for MainWindow wiring and live updates."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFileDialog

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
    assert window._upscaler_pills._buttons["ultra_quality_plus"].isEnabled() is False
    assert window._upscaler_pills._buttons["ultra_quality"].isEnabled() is True
    assert window._dlss5_pills._buttons["on"].isEnabled() is False
    assert (
        window._dlss5_pills._buttons["on"].toolTip()
        == "DLSS 5 3D-Guided Neural Rendering requires RTX 50-series Tensor Cores"
    )

    # Switch to High-End (9800X3D + 5090) and verify MFG 4x/6x + DLSS 5 unlock and UQ presets lock
    window._apply_hardware_preset("high_end")
    qapp.processEvents()
    assert window._fg_pills._buttons["4x"].isEnabled() is True
    assert window._fg_pills._buttons["6x"].isEnabled() is True
    assert window._dlss5_pills._buttons["on"].isEnabled() is True
    assert window._upscaler_pills._buttons["ultra_quality_plus"].isEnabled() is False
    assert window._upscaler_pills._buttons["ultra_quality"].isEnabled() is False
    assert (
        window._upscaler_pills._buttons["ultra_quality_plus"].toolTip()
        == "Intel XeSS 3 exclusive preset (1.3x)"
    )
    assert (
        window._upscaler_pills._buttons["ultra_quality"].toolTip()
        == "DLSS uses Quality (1.5x) or DLSS Override; no native Ultra Quality preset"
    )

    window._fg_pills.set_selected("6x")
    window._fg_pills.changed.emit("6x")
    qapp.processEvents()
    fg6_fps_no_dlss5 = float(window._hero_card._fg_value.text())
    assert fg6_fps_no_dlss5 >= 250.0

    # Enable DLSS 5 Neural Rendering at 4K All Ultra (GPU-bound) -> lowers GPU FPS (~28%) and adds 1.3 GB VRAM
    window._res_pills.set_selected("4k")
    window._res_pills.changed.emit("4k")
    window._apply_settings_preset("all_ultra")
    qapp.processEvents()
    base_no_dlss5 = float(window._hero_card._avg_value.text())
    vram_before = window._vram_bar._right_text
    window._dlss5_pills.set_selected("on")
    window._dlss5_pills.changed.emit("on")
    qapp.processEvents()
    base_with_dlss5 = float(window._hero_card._avg_value.text())
    vram_after = window._vram_bar._right_text
    assert base_with_dlss5 < base_no_dlss5
    assert vram_before != vram_after
    assert "DLSS 5 Neural Rendering trades ~28% GPU FPS + 1.3 GB VRAM" in window._diagnosis_box._diag_label.text()

    # Switch to Ultrabook (Arc 140V) -> DLSS 5 auto-resets Off, 6x FG falls back to XeSS 3 4x MFG, UQ+ unlocks
    window._apply_hardware_preset("ultrabook_igpu")
    qapp.processEvents()
    assert window._dlss5_pills.current_id() == "off"
    assert window._dlss5_pills._buttons["on"].isEnabled() is False
    assert window._fg_pills._buttons["4x"].isEnabled() is True
    assert window._fg_pills._buttons["6x"].isEnabled() is False
    assert window._fg_pills.current_id() == "4x"
    assert window._upscaler_pills._buttons["ultra_quality_plus"].isEnabled() is True
    assert window._upscaler_pills._buttons["ultra_quality"].isEnabled() is True
    assert window._vram_bar._title == "Unified Pool (OS+CPU+GPU)"
    assert window._ram_bar._title == "VRAM Share (In Pool)"

    # Select XeSS Ultra Quality Plus (1.3x) on Intel -> switch to NVIDIA -> safely steps to Quality
    window._upscaler_pills.set_selected("ultra_quality_plus")
    window._upscaler_pills.changed.emit("ultra_quality_plus")
    qapp.processEvents()
    window._apply_hardware_preset("high_end")
    qapp.processEvents()
    assert window._upscaler_pills.current_id() == "quality"
    window._apply_hardware_preset("ultrabook_igpu")
    qapp.processEvents()

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


def test_export_markdown_button_writes_report(
    qapp: QApplication,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = MainWindow()
    window.resize(1440, 880)
    window.show()
    qapp.processEvents()

    out_file = tmp_path / "telemetry_export"
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *_args, **_kwargs: (str(out_file), "Markdown Files (*.md)"),
    )
    window._export_btn.click()
    qapp.processEvents()

    expected_path = tmp_path / "telemetry_export.md"
    assert expected_path.exists()
    content = expected_path.read_text(encoding="utf-8")
    assert "# GTA VI Hardware & FPS Simulation Report" in content
    assert "RX 9060 XT (16GB)" in content
    assert "FSR Quality (1.5x)" in content
    assert "| **DLSS 5 Neural Rendering** | Off |" in content
    assert window._export_btn.text() == "Exported ✓"
    window.close()
