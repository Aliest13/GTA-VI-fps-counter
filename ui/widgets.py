"""Reusable Vice City Glassmorphic PySide6 widgets and custom QPainter charts."""

from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPaintEvent,
    QPen,
)
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from data.settings_db import SettingDefinition
from engine.predictor import GPUComparisonEntry, SimulationResult, WarningMessage
from ui.styles import (
    AMBER,
    BADGE_COLORS,
    CRIMSON,
    CYAN,
    EMERALD,
    MAGENTA,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    VIOLET,
    fps_accent_color,
)


class GlassCard(QFrame):
    """Translucent glass panel with crisp border and optional collapsible body."""

    def __init__(
        self,
        title: str = "",
        collapsible: bool = False,
        collapsed: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("GlassCard")
        self._collapsible = collapsible
        self._collapsed = collapsed
        self._base_title = title

        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(14, 12, 14, 12)
        self._root_layout.setSpacing(10)

        self._header_row = QHBoxLayout()
        self._header_row.setSpacing(8)
        self._title_btn: QPushButton | None = None
        self._title_label: QLabel | None = None

        if title:
            if collapsible:
                escaped = title.replace("&", "&&")
                btn = QPushButton(f"▾  {escaped}")
                btn.setObjectName("AccordionHeader")
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(self.toggle_collapsed)
                self._title_btn = btn
                self._header_row.addWidget(btn)
            else:
                lbl = QLabel(title)
                lbl.setObjectName("SectionTitle")
                self._title_label = lbl
                self._header_row.addWidget(lbl)

            self._header_row.addStretch(1)
            self._root_layout.addLayout(self._header_row)

        self._body_container = QWidget()
        self.body_layout = QVBoxLayout(self._body_container)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(8)
        self._root_layout.addWidget(self._body_container)

        if self._collapsed:
            self._apply_collapsed_state()

    def add_header_widget(self, widget: QWidget) -> None:
        self._header_row.addWidget(widget)

    def toggle_collapsed(self) -> None:
        if not self._collapsible:
            return
        self._collapsed = not self._collapsed
        self._apply_collapsed_state()

    def set_collapsed(self, collapsed: bool) -> None:
        if not self._collapsible:
            return
        self._collapsed = collapsed
        self._apply_collapsed_state()

    def _apply_collapsed_state(self) -> None:
        self._body_container.setVisible(not self._collapsed)
        if self._title_btn is not None:
            escaped = self._base_title.replace("&", "&&")
            arrow = "▸" if self._collapsed else "▾"
            self._title_btn.setText(f"{arrow}  {escaped}")


class SegmentedPills(QWidget):
    """Row or grid of pill buttons acting as a sleek mutually-exclusive selector."""

    changed = Signal(str)

    def __init__(
        self,
        options: Iterable[tuple[str, str]],
        selected_id: str | None = None,
        max_cols: int | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._max_cols = max_cols
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: dict[str, QPushButton] = {}
        self._id_order: list[str] = []

        self.set_options(options, selected_id)

    def set_options(
        self,
        options: Iterable[tuple[str, str]],
        selected_id: str | None = None,
    ) -> None:
        for btn in self._buttons.values():
            self._group.removeButton(btn)
            self._layout.removeWidget(btn)
            btn.deleteLater()
        self._buttons.clear()
        self._id_order.clear()

        opts_list = list(options)
        cols = self._max_cols or max(1, len(opts_list))

        for idx, (opt_id, label) in enumerate(opts_list):
            btn = QPushButton(label)
            btn.setObjectName("PillBtn")
            btn.setCheckable(True)
            btn.setMinimumWidth(0)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(lambda _checked, oid=opt_id: self.changed.emit(oid))
            self._group.addButton(btn)
            self._layout.addWidget(btn, idx // cols, idx % cols)
            self._buttons[opt_id] = btn
            self._id_order.append(opt_id)

        if selected_id and selected_id in self._buttons:
            self._buttons[selected_id].setChecked(True)
        elif self._id_order:
            self._buttons[self._id_order[0]].setChecked(True)

    def set_selected(self, option_id: str) -> None:
        btn = self._buttons.get(option_id)
        if btn is not None:
            btn.blockSignals(True)
            btn.setChecked(True)
            btn.blockSignals(False)

    def current_id(self) -> str:
        for oid in self._id_order:
            if self._buttons[oid].isChecked():
                return oid
        return self._id_order[0] if self._id_order else ""

    def update_label(self, option_id: str, new_label: str) -> None:
        btn = self._buttons.get(option_id)
        if btn is not None:
            btn.setText(new_label)

    def set_option_enabled(self, option_id: str, enabled: bool, tooltip: str = "") -> None:
        btn = self._buttons.get(option_id)
        if btn is not None:
            btn.setEnabled(enabled)
            btn.setToolTip(tooltip)


class SettingRow(QFrame):
    """Single categorized GTA VI graphics control with load badges and pills."""

    value_changed = Signal(str, str)

    def __init__(
        self,
        definition: SettingDefinition,
        selected_option: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("SettingRow")
        self.definition = definition

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        self._name_label = QLabel(definition.name)
        self._name_label.setWordWrap(True)
        self._name_label.setMinimumWidth(0)
        self._name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._name_label.setStyleSheet("font-weight: 600; font-size: 11.5px; color: #F1F5F9;")
        top_row.addWidget(self._name_label, 1)

        for badge in definition.badges:
            fg, bg = BADGE_COLORS.get(badge, ("#E2E8F0", "rgba(255,255,255,0.1)"))
            pill = QLabel(badge)
            pill.setStyleSheet(
                f"color: {fg}; background-color: {bg}; border: 1px solid {fg}; "
                "border-radius: 5px; padding: 1px 5px; font-size: 9.5px; font-weight: 700;"
            )
            top_row.addWidget(pill)

        layout.addLayout(top_row)

        options = [(opt.label, opt.label) for opt in definition.options]
        self.pills = SegmentedPills(options, selected_id=selected_option)
        self.pills.changed.connect(lambda val: self.value_changed.emit(self.definition.id, val))
        layout.addWidget(self.pills)

        self.set_language("en")

    def set_value(self, value: str) -> None:
        self.pills.set_selected(value)

    def set_language(self, lang: str) -> None:
        detail = self.definition.tooltip_fa if lang == "fa" else self.definition.tooltip_en
        tip = (
            f"<b>{self.definition.name}</b><br/>"
            f"{detail}<br/>"
            f"<span style='color:#94A3B8'>Tex2 Parameters: {self.definition.tex2_subsettings}</span>"
        )
        self.setToolTip(tip)


class HeroTelemetryCard(GlassCard):
    """Big glass hero display for Avg FPS, 1% Low FPS, Frame Gen FPS, and active bottleneck."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("", collapsible=False, parent=parent)

        header = QHBoxLayout()
        header.setSpacing(6)
        title = QLabel("LIVE TELEMETRY")
        title.setObjectName("SectionTitle")
        title.setMinimumWidth(0)
        header.addWidget(title)
        header.addStretch(1)

        self.bottleneck_badge = QLabel("BALANCED")
        self.bottleneck_badge.setStyleSheet(
            f"color: {CYAN}; background-color: rgba(0, 240, 255, 0.14); "
            f"border: 1px solid {CYAN}; border-radius: 7px; padding: 3px 8px; "
            "font-size: 10px; font-weight: 800;"
        )
        header.addWidget(self.bottleneck_badge)
        self.body_layout.addLayout(header)

        tiles_row = QHBoxLayout()
        tiles_row.setSpacing(6)

        self._avg_value, self._avg_sub = self._create_kpi_tile(
            tiles_row, "AVG FPS", "--", "Base Render"
        )
        self._low_value, self._low_sub = self._create_kpi_tile(
            tiles_row, "1% LOW", "--", "City Floor"
        )
        self._fg_value, self._fg_sub = self._create_kpi_tile(
            tiles_row, "FRAME GEN", "--", "Off"
        )
        self.body_layout.addLayout(tiles_row)

    def _create_kpi_tile(
        self,
        parent_layout: QHBoxLayout,
        caption: str,
        initial_val: str,
        initial_sub: str,
    ) -> tuple[QLabel, QLabel]:
        tile = QFrame()
        tile.setObjectName("HeroTile")
        tile.setMinimumWidth(0)
        tile.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        v = QVBoxLayout(tile)
        v.setContentsMargins(6, 8, 6, 8)
        v.setSpacing(2)

        cap_lbl = QLabel(caption)
        cap_lbl.setMinimumWidth(0)
        cap_lbl.setStyleSheet("font-size: 9px; font-weight: 700; color: #94A3B8; letter-spacing: 0.5px;")
        cap_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(cap_lbl)

        val_lbl = QLabel(initial_val)
        val_lbl.setMinimumWidth(0)
        val_lbl.setStyleSheet("font-size: 24px; font-weight: 800; color: #00F0FF;")
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(val_lbl)

        sub_lbl = QLabel(initial_sub)
        sub_lbl.setMinimumWidth(0)
        sub_lbl.setStyleSheet("font-size: 9.5px; color: #94A3B8;")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(sub_lbl)

        parent_layout.addWidget(tile, 1)
        return val_lbl, sub_lbl

    def update_telemetry(self, result: SimulationResult) -> None:
        avg_color = fps_accent_color(result.base_fps)
        low_color = fps_accent_color(result.low_1pct_fps)
        fg_color = fps_accent_color(result.fg_fps) if result.effective_fg_id != "off" else TEXT_MUTED

        self._avg_value.setText(f"{result.base_fps:.0f}")
        self._avg_value.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {avg_color};")
        self._avg_sub.setText(f"G {result.raw_gpu_fps:.0f} | C {result.raw_cpu_fps:.0f}")

        self._low_value.setText(f"{result.low_1pct_fps:.0f}")
        self._low_value.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {low_color};")
        self._low_sub.setText("City / Chaos")

        if result.effective_fg_id == "off":
            self._fg_value.setText("OFF")
            self._fg_value.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {fg_color};")
            self._fg_sub.setText("Native")
        else:
            self._fg_value.setText(f"{result.fg_fps:.0f}")
            self._fg_value.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {fg_color};")
            mode_txt = "2x FG" if result.effective_fg_id == "2x" else f"MFG {result.effective_fg_id.upper()}"
            if result.base_fps < 38.0:
                self._fg_sub.setText(f"{mode_txt} • Low!")
                self._fg_sub.setStyleSheet(f"font-size: 9.5px; color: {AMBER}; font-weight: 700;")
            else:
                self._fg_sub.setText(mode_txt)
                self._fg_sub.setStyleSheet("font-size: 9.5px; color: #94A3B8;")

        bn_color_map = {
            "Balanced": EMERALD,
            "GPU / RT": VIOLET,
            "CPU": CYAN,
            "VRAM Overflow": CRIMSON,
            "RAM / Unified Overflow": CRIMSON,
        }
        bn_color = bn_color_map.get(result.primary_bottleneck, CYAN)
        self.bottleneck_badge.setText(result.primary_bottleneck.upper())
        self.bottleneck_badge.setStyleSheet(
            f"color: {bn_color}; background-color: rgba(15, 23, 42, 0.72); "
            f"border: 1px solid {bn_color}; border-radius: 7px; padding: 3px 9px; "
            "font-size: 10.5px; font-weight: 800;"
        )


class NeonMeterBar(QWidget):
    """Custom QPainter load/memory meter with 88% amber threshold and pulsing >100% overflow."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title = title
        self._right_text = "0%"
        self._ratio = 0.0
        self._base_color = QColor(CYAN)
        self._is_overflow = False
        self._pulse_phase = 0.0
        self._pulse_dir = 1

        self.setMinimumHeight(38)
        self.setMaximumHeight(42)

        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(45)
        self._pulse_timer.timeout.connect(self._tick_pulse)

    def _tick_pulse(self) -> None:
        self._pulse_phase += 0.09 * self._pulse_dir
        if self._pulse_phase >= 1.0:
            self._pulse_phase = 1.0
            self._pulse_dir = -1
        elif self._pulse_phase <= 0.0:
            self._pulse_phase = 0.0
            self._pulse_dir = 1
        self.update()

    def set_percentage(self, title: str, pct: float, accent_hex: str) -> None:
        self._title = title
        self._ratio = max(0.0, pct / 100.0)
        self._right_text = f"{pct:.0f}%"
        self._is_overflow = pct > 100.0
        if pct >= 95.0:
            self._base_color = QColor(MAGENTA)
        elif pct >= 85.0:
            self._base_color = QColor(AMBER)
        else:
            self._base_color = QColor(accent_hex)
        self._sync_pulse_timer()
        self.update()

    def set_memory(
        self,
        title: str,
        used_gb: float,
        total_gb: float,
        overflow_gb: float,
    ) -> None:
        self._title = title
        ratio = used_gb / max(0.1, total_gb)
        self._ratio = ratio
        self._is_overflow = overflow_gb > 0.0
        if self._is_overflow:
            self._right_text = f"{used_gb:.1f} / {total_gb:.0f} GB (+{overflow_gb:.1f} SPILL!)"
            self._base_color = QColor(CRIMSON)
        elif ratio >= 0.88:
            self._right_text = f"{used_gb:.1f} / {total_gb:.0f} GB ({ratio * 100:.0f}%)"
            self._base_color = QColor(AMBER)
        else:
            self._right_text = f"{used_gb:.1f} / {total_gb:.0f} GB ({ratio * 100:.0f}%)"
            self._base_color = QColor(EMERALD if ratio < 0.72 else CYAN)
        self._sync_pulse_timer()
        self.update()

    def _sync_pulse_timer(self) -> None:
        if self._is_overflow:
            if not self._pulse_timer.isActive():
                self._pulse_timer.start()
        else:
            if self._pulse_timer.isActive():
                self._pulse_timer.stop()
            self._pulse_phase = 0.0

    def paintEvent(self, _event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        label_font = QFont("Segoe UI", 9)
        label_font.setBold(True)
        painter.setFont(label_font)

        painter.setPen(QColor(TEXT_PRIMARY))
        painter.drawText(QRectF(0, 0, w * 0.55, 18), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._title)

        right_color = QColor(CRIMSON if self._is_overflow else TEXT_SECONDARY)
        painter.setPen(right_color)
        painter.drawText(QRectF(w * 0.35, 0, w * 0.65, 18), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, self._right_text)

        bar_rect = QRectF(0, 21, w, 12)
        track_color = QColor(255, 255, 255, 20)
        painter.setPen(QPen(QColor(255, 255, 255, 34), 1.0))
        painter.setBrush(track_color)
        painter.drawRoundedRect(bar_rect, 6, 6)

        clamped = min(1.0, max(0.02, self._ratio))
        fill_w = max(8.0, (w - 2.0) * clamped)
        fill_rect = QRectF(1, 22, fill_w, 10)

        if self._is_overflow:
            alpha = int(175 + 80 * self._pulse_phase)
            c1 = QColor(255, 46, 147, alpha)
            c2 = QColor(255, 77, 109, alpha)
            glow_pen = QPen(QColor(255, 77, 109, int(120 + 130 * self._pulse_phase)), 1.5)
            painter.setPen(glow_pen)
            painter.drawRoundedRect(bar_rect, 6, 6)
        else:
            c1 = QColor(self._base_color)
            c2 = QColor(self._base_color).lighter(125)
            c1.setAlpha(210)
            c2.setAlpha(245)

        grad = QLinearGradient(fill_rect.topLeft(), fill_rect.topRight())
        grad.setColorAt(0.0, c1)
        grad.setColorAt(1.0, c2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(grad)
        painter.drawRoundedRect(fill_rect, 5, 5)

        # Subtle 88% marker line
        marker_x = w * 0.88
        painter.setPen(QPen(QColor(255, 255, 255, 70), 1.0, Qt.PenStyle.DotLine))
        painter.drawLine(QPointF(marker_x, 21), QPointF(marker_x, 33))


class BottleneckDiagnosisBox(GlassCard):
    """Plain-English (or Persian) bottleneck diagnosis, actionable tip, and warnings."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("BOTTLENECK RADAR & DIAGNOSIS", collapsible=False, parent=parent)
        self._lang = "en"
        self._last_result: SimulationResult | None = None

        self._diag_label = QLabel()
        self._diag_label.setWordWrap(True)
        self._diag_label.setStyleSheet("font-size: 11.5px; color: #F1F5F9; line-height: 1.35;")
        self.body_layout.addWidget(self._diag_label)

        self._rec_label = QLabel()
        self._rec_label.setWordWrap(True)
        self._rec_label.setStyleSheet(
            "font-size: 11px; color: #00F0FF; background-color: rgba(0, 240, 255, 0.08); "
            "border: 1px solid rgba(0, 240, 255, 0.28); border-radius: 8px; padding: 6px 8px;"
        )
        self.body_layout.addWidget(self._rec_label)

        self._warnings_container = QVBoxLayout()
        self._warnings_container.setSpacing(5)
        self.body_layout.addLayout(self._warnings_container)

    def set_language(self, lang: str) -> None:
        self._lang = lang
        if self._last_result is not None:
            self.update_diagnosis(self._last_result)

    def update_diagnosis(self, result: SimulationResult) -> None:
        self._last_result = result
        is_fa = self._lang == "fa"
        self.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft if is_fa else Qt.LayoutDirection.LeftToRight
        )

        diag = result.diagnosis_fa if is_fa else result.diagnosis_en
        rec = result.recommendation_fa if is_fa else result.recommendation_en
        align = Qt.AlignmentFlag.AlignRight if is_fa else Qt.AlignmentFlag.AlignLeft

        self._diag_label.setAlignment(align)
        self._rec_label.setAlignment(align)
        self._diag_label.setText(diag)
        self._rec_label.setText(f"{'پیشنهاد بهینه‌سازی:' if is_fa else 'Fix:'} {rec}")

        while self._warnings_container.count():
            item = self._warnings_container.takeAt(0)
            if item and (old_w := item.widget()):
                old_w.hide()
                old_w.setParent(None)
                old_w.deleteLater()

        for warn in result.warnings:
            self._warnings_container.addWidget(self._make_warning_chip(warn, is_fa))
        self.updateGeometry()

    def _make_warning_chip(self, warn: WarningMessage, is_fa: bool) -> QFrame:
        chip = QFrame()
        if warn.severity == "critical":
            border_c, bg_c, title_c = CRIMSON, "rgba(255, 77, 109, 0.14)", "#FF8FA3"
        elif warn.severity == "warning":
            border_c, bg_c, title_c = AMBER, "rgba(255, 184, 0, 0.12)", "#FFD166"
        else:
            border_c, bg_c, title_c = CYAN, "rgba(0, 240, 255, 0.08)", "#67E8F9"

        chip.setStyleSheet(
            f"QFrame {{ background-color: {bg_c}; border: 1px solid {border_c}; border-radius: 8px; }}"
        )
        v = QVBoxLayout(chip)
        v.setContentsMargins(8, 5, 8, 5)
        v.setSpacing(2)

        title = QLabel(warn.title_fa if is_fa else warn.title_en)
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignmentFlag.AlignRight if is_fa else Qt.AlignmentFlag.AlignLeft)
        title.setStyleSheet(f"font-size: 10.5px; font-weight: 800; color: {title_c}; border: none; background: transparent;")
        v.addWidget(title)

        detail = QLabel(warn.detail_fa if is_fa else warn.detail_en)
        detail.setWordWrap(True)
        detail.setAlignment(Qt.AlignmentFlag.AlignRight if is_fa else Qt.AlignmentFlag.AlignLeft)
        detail.setStyleSheet("font-size: 10px; color: #CBD5E1; border: none; background: transparent;")
        v.addWidget(detail)
        return chip


class MultiGPUComparisonChart(QWidget):
    """Live QPainter horizontal bar chart comparing all GPUs + PS5 / PS5 Pro console baselines."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._entries: list[GPUComparisonEntry] = []
        self._bar_rects: list[tuple[QRectF, GPUComparisonEntry]] = []
        self.setMouseTracking(True)
        self.setMinimumHeight(330)

    def set_entries(self, entries: list[GPUComparisonEntry]) -> None:
        self._entries = entries
        needed_h = max(310, 34 + len(entries) * 26)
        self.setMinimumHeight(needed_h)
        self.update()

    def mouseMoveEvent(self, event) -> None:
        pos = event.position()
        for rect, entry in self._bar_rects:
            if rect.contains(pos):
                spill = " | VRAM OVERFLOW!" if entry.has_vram_overflow else ""
                QToolTip.showText(
                    event.globalPosition().toPoint(),
                    f"<b>{entry.label}</b><br/>"
                    f"Base Avg: {entry.base_fps:.1f} FPS | 1% Low: {entry.low_1pct_fps:.1f} FPS{spill}<br/>"
                    f"<span style='color:#94A3B8'>{entry.notes}</span>",
                    self,
                )
                return
        QToolTip.hideText()
        super().mouseMoveEvent(event)

    def paintEvent(self, _event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        self._bar_rects.clear()
        if not self._entries:
            return

        w = float(self.width())
        label_col_w = min(102.0, max(76.0, w * 0.29))
        right_pad = 38.0
        chart_left = label_col_w
        chart_w = max(80.0, w - chart_left - right_pad)
        top_offset = 24.0
        row_h = 25.0

        max_fps = max([75.0] + [e.base_fps for e in self._entries]) * 1.08

        # Header reference lines (30 FPS PS5 Target & 60 FPS Smooth Target)
        ref_font = QFont("Segoe UI", 8)
        ref_font.setBold(True)
        painter.setFont(ref_font)

        chart_bottom = top_offset + len(self._entries) * row_h
        for target_fps, label, color_hex in (
            (30.0, "30 FPS", AMBER),
            (60.0, "60 FPS", EMERALD),
        ):
            if target_fps <= max_fps:
                rx = chart_left + (target_fps / max_fps) * chart_w
                c = QColor(color_hex)
                c.setAlpha(155)
                pen = QPen(c, 1.2, Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.drawLine(QPointF(rx, top_offset - 4), QPointF(rx, chart_bottom))

                painter.setPen(QColor(color_hex))
                lbl_x = max(chart_left - 10.0, min(w - 52.0, rx - 26.0))
                painter.drawText(
                    QRectF(lbl_x, 0, 52, 18),
                    Qt.AlignmentFlag.AlignCenter,
                    label,
                )

        name_font = QFont("Segoe UI", 8)
        val_font = QFont("Segoe UI", 8)
        val_font.setBold(True)

        for idx, entry in enumerate(self._entries):
            y = top_offset + idx * row_h
            row_rect = QRectF(0, y, w, row_h - 2)
            self._bar_rects.append((row_rect, entry))

            if entry.is_selected:
                painter.setPen(QPen(QColor(0, 240, 255, 130), 1.0))
                painter.setBrush(QColor(0, 240, 255, 24))
                painter.drawRoundedRect(row_rect, 5, 5)

            # GPU name
            f = QFont(name_font)
            f.setBold(entry.is_selected or entry.is_reference_console)
            painter.setFont(f)
            if entry.is_selected:
                painter.setPen(QColor(CYAN))
            elif entry.is_reference_console:
                painter.setPen(QColor(VIOLET))
            else:
                painter.setPen(QColor(TEXT_PRIMARY))

            painter.drawText(
                QRectF(4, y, label_col_w - 8, row_h - 2),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                entry.label,
            )

            # Bar track
            bar_y = y + 5
            bar_h = row_h - 12
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 255, 255, 14))
            painter.drawRoundedRect(QRectF(chart_left, bar_y, chart_w, bar_h), 4, 4)

            # Bar fill
            bar_w = max(4.0, min(chart_w, (entry.base_fps / max_fps) * chart_w))
            fill_rect = QRectF(chart_left, bar_y, bar_w, bar_h)

            if entry.is_reference_console:
                grad = QLinearGradient(fill_rect.topLeft(), fill_rect.topRight())
                grad.setColorAt(0.0, QColor(124, 58, 237, 155))
                grad.setColorAt(1.0, QColor(167, 139, 250, 210))
            elif entry.is_selected:
                grad = QLinearGradient(fill_rect.topLeft(), fill_rect.topRight())
                grad.setColorAt(0.0, QColor(CYAN))
                grad.setColorAt(1.0, QColor(MAGENTA))
            elif entry.has_vram_overflow:
                grad = QLinearGradient(fill_rect.topLeft(), fill_rect.topRight())
                grad.setColorAt(0.0, QColor(255, 77, 109, 175))
                grad.setColorAt(1.0, QColor(255, 184, 0, 200))
            else:
                accent = QColor(fps_accent_color(entry.base_fps))
                accent.setAlpha(185)
                grad = QLinearGradient(fill_rect.topLeft(), fill_rect.topRight())
                grad.setColorAt(0.0, accent.darker(125))
                grad.setColorAt(1.0, accent)

            painter.setBrush(grad)
            painter.drawRoundedRect(fill_rect, 4, 4)

            # Value label
            painter.setFont(val_font)
            val_color = QColor(CRIMSON if entry.has_vram_overflow else TEXT_PRIMARY)
            painter.setPen(val_color)
            suffix = " !" if entry.has_vram_overflow else ""
            painter.drawText(
                QRectF(chart_left + bar_w + 5, y, right_pad - 6, row_h - 2),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                f"{entry.base_fps:.0f}{suffix}",
            )
