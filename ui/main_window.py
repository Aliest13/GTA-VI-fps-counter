"""3-column responsive Glassmorphic dashboard for the GTA VI Hardware & FPS Simulator."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QLinearGradient,
    QPainter,
    QPaintEvent,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from data.hardware_db import (
    CPU_BY_ID,
    CPUS,
    GPU_BY_ID,
    GPUS,
    HARDWARE_PRESETS,
    PRESET_BY_ID,
    RAM_CAPACITIES_GB,
    RAM_SPEED_BY_ID,
    RAM_SPEEDS,
    STORAGE_OPTIONS,
    StorageType,
    get_platform_compatibility_notes,
)
from data.settings_db import (
    FRAME_GEN_BY_ID,
    FRAME_GEN_MODES,
    RESOLUTIONS,
    SETTING_CATEGORIES,
    SETTINGS,
    SETTINGS_PRESET_BY_ID,
    SETTINGS_PRESETS,
    UPSCALERS,
    default_settings_map,
    resolve_upscaler_for_vendor,
)
from engine.predictor import (
    SimulationInput,
    auto_optimize_for_60_fps,
    compare_all_gpus,
    export_simulation_markdown,
    simulate,
)
from ui.styles import (
    BG_BOTTOM,
    BG_TOP,
    CYAN,
    EMERALD,
    GLOBAL_STYLESHEET,
    MAGENTA,
    VIOLET,
    apply_windows_backdrop,
)
from ui.widgets import (
    BottleneckDiagnosisBox,
    GlassCard,
    HeroTelemetryCard,
    MultiGPUComparisonChart,
    NeonMeterBar,
    SegmentedPills,
    SettingRow,
)


class ViceCityBackdropWidget(QWidget):
    """Root container painting the deep Vice City dark gradient & ambient neon glows."""

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        base_grad = QLinearGradient(0, 0, rect.width(), rect.height())
        base_grad.setColorAt(0.0, QColor(BG_TOP))
        base_grad.setColorAt(0.55, QColor("#111022"))
        base_grad.setColorAt(1.0, QColor(BG_BOTTOM))
        painter.fillRect(rect, base_grad)

        # Ambient Vice City neon cyan glow (top-left)
        cyan_glow = QRadialGradient(QPointF(rect.width() * 0.12, rect.height() * 0.14), rect.width() * 0.42)
        cyan_glow.setColorAt(0.0, QColor(0, 240, 255, 36))
        cyan_glow.setColorAt(1.0, QColor(0, 240, 255, 0))
        painter.fillRect(rect, cyan_glow)

        # Ambient Vice City neon magenta glow (bottom-right)
        mag_glow = QRadialGradient(QPointF(rect.width() * 0.88, rect.height() * 0.86), rect.width() * 0.46)
        mag_glow.setColorAt(0.0, QColor(255, 46, 147, 34))
        mag_glow.setColorAt(1.0, QColor(255, 46, 147, 0))
        painter.fillRect(rect, mag_glow)

        super().paintEvent(event)


class MainWindow(QMainWindow):
    """Main 3-column live simulator window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GTA VI Hardware & FPS Simulator — Vice City Telemetry")
        self.resize(1440, 880)
        self.setMinimumSize(1120, 720)
        self.setStyleSheet(GLOBAL_STYLESHEET)

        self._suppress_recalc = False
        self._lang = "en"
        self._settings_state: dict[str, str] = default_settings_map()
        self._undo_snapshot: tuple[dict[str, str], str] | None = None
        self._setting_rows: dict[str, SettingRow] = {}
        self._category_cards: list[GlassCard] = []
        self._hw_preset_buttons: dict[str, QPushButton] = {}
        self._settings_preset_buttons: dict[str, QPushButton] = {}

        root = ViceCityBackdropWidget()
        root.setObjectName("CentralRoot")
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(10)

        outer.addWidget(self._build_header())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(8)
        splitter.setChildrenCollapsible(False)
        splitter.setStyleSheet("QSplitter::handle { background: transparent; }")

        left_scroll = self._wrap_scroll(self._build_left_hardware_panel())
        center_scroll = self._wrap_scroll(self._build_center_settings_panel())
        right_scroll = self._wrap_scroll(self._build_right_telemetry_panel())

        splitter.addWidget(left_scroll)
        splitter.addWidget(center_scroll)
        splitter.addWidget(right_scroll)
        splitter.setStretchFactor(0, 30)
        splitter.setStretchFactor(1, 40)
        splitter.setStretchFactor(2, 30)
        splitter.setSizes([420, 560, 420])

        outer.addWidget(splitter, 1)

        apply_windows_backdrop(self)

        # Initialize default Mainstream Desktop preset + 1440p Quality + PS5 Settings
        self._apply_hardware_preset("mid_range_desktop", recalculate=False)
        self._res_pills.set_selected("1440p")
        self._upscaler_pills.set_selected("quality")
        self._fg_pills.set_selected("off")
        self._apply_settings_preset("ps5_xsx", recalculate=False)
        self._sync_gpu_tech_labels()
        self._recalculate()

    def _wrap_scroll(self, content: QWidget) -> QScrollArea:
        content.setMinimumWidth(0)
        scroll = QScrollArea()
        scroll.setMinimumWidth(0)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(content)
        return scroll

    @staticmethod
    def _configure_compact_combo(combo: QComboBox) -> None:
        combo.setMinimumWidth(0)
        combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        combo.setMinimumContentsLength(10)
        combo.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)

    def _build_header(self) -> QWidget:
        bar = GlassCard()
        bar._root_layout.setContentsMargins(14, 9, 14, 9)
        row = QHBoxLayout()
        row.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        title = QLabel("GTA VI  //  HARDWARE & FPS SIMULATOR")
        title.setObjectName("AppTitle")
        subtitle = QLabel("Tex2 Console Datamine Engine  •  Real-Time Bottleneck, VRAM Spillover & Multi-GPU Telemetry")
        subtitle.setObjectName("AppSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        row.addLayout(title_col)
        row.addStretch(1)

        self._render_scale_chip = QLabel("Render: 1440p • XeSS Quality (0.55x)")
        self._render_scale_chip.setStyleSheet(
            f"color: {CYAN}; background-color: rgba(0, 240, 255, 0.10); "
            "border: 1px solid rgba(0, 240, 255, 0.35); border-radius: 8px; "
            "padding: 5px 10px; font-size: 11px; font-weight: 700;"
        )
        row.addWidget(self._render_scale_chip)

        self._lang_btn = QPushButton("EN / فارسی")
        self._lang_btn.setObjectName("GhostBtn")
        self._lang_btn.setCheckable(True)
        self._lang_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._lang_btn.setToolTip("Toggle Bottleneck Diagnosis & Setting Tooltips between English and Persian")
        self._lang_btn.clicked.connect(self._toggle_language)
        row.addWidget(self._lang_btn)

        self._export_btn = QPushButton("Export .md")
        self._export_btn.setObjectName("GhostBtn")
        self._export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._export_btn.setToolTip("Export full hardware, settings, telemetry, and GPU comparison report as Markdown (.md)")
        self._export_btn.clicked.connect(self._on_export_markdown)
        row.addWidget(self._export_btn)

        bar.body_layout.addLayout(row)
        return bar

    # ------------------------------------------------------------------
    # LEFT PANEL (~30%): System Hardware Configurator
    # ------------------------------------------------------------------
    def _build_left_hardware_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(2, 0, 10, 0)
        layout.setSpacing(10)

        # Quick Hardware Presets Card
        presets_card = GlassCard("QUICK HARDWARE PRESETS")
        for preset in HARDWARE_PRESETS:
            btn = QPushButton(preset.label)
            btn.setObjectName("PresetBtn")
            btn.setMinimumWidth(0)
            btn.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _checked=False, pid=preset.id: self._apply_hardware_preset(pid))
            presets_card.body_layout.addWidget(btn)
            self._hw_preset_buttons[preset.id] = btn
        layout.addWidget(presets_card)

        # Core Components Card
        hw_card = GlassCard("SYSTEM HARDWARE")

        # Form Factor / Thermal Envelope toggle
        self._laptop_pills = SegmentedPills(
            [
                ("desktop", "Desktop Tower"),
                ("gaming_laptop", "Gaming Laptop"),
                ("laptop", "Ultrabook (20-25W)"),
            ],
            selected_id="desktop",
        )
        self._laptop_pills.changed.connect(self._on_hardware_changed)
        hw_card.body_layout.addWidget(self._make_field_label("Form Factor / Thermal Envelope"))
        hw_card.body_layout.addWidget(self._laptop_pills)

        # GPU Selector
        hw_card.body_layout.addWidget(self._make_field_label("Graphics Card (GPU)"))
        self._gpu_combo = QComboBox()
        self._configure_compact_combo(self._gpu_combo)
        for gpu in GPUS:
            self._gpu_combo.addItem(gpu.name, userData=gpu.id)
        self._gpu_combo.currentIndexChanged.connect(self._on_gpu_changed)
        hw_card.body_layout.addWidget(self._gpu_combo)

        self._gpu_spec_chip = QLabel()
        self._gpu_spec_chip.setObjectName("SpecChip")
        self._gpu_spec_chip.setWordWrap(True)
        self._gpu_spec_chip.setMinimumWidth(0)
        hw_card.body_layout.addWidget(self._gpu_spec_chip)

        # CPU Selector
        hw_card.body_layout.addWidget(self._make_field_label("Processor (CPU)"))
        self._cpu_combo = QComboBox()
        self._configure_compact_combo(self._cpu_combo)
        for cpu in CPUS:
            self._cpu_combo.addItem(f"{cpu.name} ({cpu.cores_threads})", userData=cpu.id)
        self._cpu_combo.currentIndexChanged.connect(self._on_hardware_changed)
        hw_card.body_layout.addWidget(self._cpu_combo)

        self._cpu_spec_chip = QLabel()
        self._cpu_spec_chip.setObjectName("SpecChip")
        self._cpu_spec_chip.setWordWrap(True)
        self._cpu_spec_chip.setMinimumWidth(0)
        hw_card.body_layout.addWidget(self._cpu_spec_chip)

        # RAM Capacity & Speed
        hw_card.body_layout.addWidget(self._make_field_label("System RAM Capacity"))
        self._ram_cap_pills = SegmentedPills(
            [(str(cap), f"{cap} GB") for cap in RAM_CAPACITIES_GB],
            selected_id="32",
        )
        self._ram_cap_pills.changed.connect(self._on_hardware_changed)
        hw_card.body_layout.addWidget(self._ram_cap_pills)

        hw_card.body_layout.addWidget(self._make_field_label("RAM Speed / Bandwidth Profile"))
        self._ram_speed_combo = QComboBox()
        self._configure_compact_combo(self._ram_speed_combo)
        for speed in RAM_SPEEDS:
            self._ram_speed_combo.addItem(speed.name, userData=speed.id)
        self._ram_speed_combo.currentIndexChanged.connect(self._on_hardware_changed)
        hw_card.body_layout.addWidget(self._ram_speed_combo)

        self._platform_hint_chip = QLabel()
        self._platform_hint_chip.setWordWrap(True)
        self._platform_hint_chip.setStyleSheet(
            "font-size: 10.5px; color: #FFD166; background-color: rgba(255, 184, 0, 0.10); "
            "border: 1px solid rgba(255, 184, 0, 0.35); border-radius: 7px; padding: 5px 8px;"
        )
        self._platform_hint_chip.setVisible(False)
        hw_card.body_layout.addWidget(self._platform_hint_chip)

        layout.addWidget(hw_card)

        # Tuning & Platform Toggles Card
        toggles_card = GlassCard("PLATFORM TUNING & STORAGE")

        toggles_card.body_layout.addWidget(self._make_field_label("Resizable BAR (PCIe ReBAR)"))
        self._rebar_pills = SegmentedPills(
            [("on", "ReBAR ON"), ("off", "ReBAR OFF")],
            selected_id="on",
        )
        self._rebar_pills.changed.connect(self._on_hardware_changed)
        toggles_card.body_layout.addWidget(self._rebar_pills)

        oc_header = QHBoxLayout()
        oc_header.addWidget(self._make_field_label("GPU Core / Mem Overclock"))
        oc_header.addStretch(1)
        self._oc_val_label = QLabel("+0%")
        self._oc_val_label.setStyleSheet(f"font-size: 11.5px; font-weight: 800; color: {CYAN};")
        oc_header.addWidget(self._oc_val_label)
        toggles_card.body_layout.addLayout(oc_header)

        self._oc_slider = QSlider(Qt.Orientation.Horizontal)
        self._oc_slider.setRange(0, 7)
        self._oc_slider.setValue(0)
        self._oc_slider.valueChanged.connect(self._on_oc_changed)
        toggles_card.body_layout.addWidget(self._oc_slider)

        toggles_card.body_layout.addWidget(self._make_field_label("Storage Drive"))
        self._storage_pills = SegmentedPills(
            [(st, st) for st in STORAGE_OPTIONS],
            selected_id="NVMe Gen4",
        )
        self._storage_pills.changed.connect(self._on_hardware_changed)
        toggles_card.body_layout.addWidget(self._storage_pills)

        layout.addWidget(toggles_card)
        layout.addStretch(1)
        return panel

    # ------------------------------------------------------------------
    # CENTER PANEL (~40%): GTA VI Graphics & Display Settings
    # ------------------------------------------------------------------
    def _build_center_settings_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(2, 0, 10, 0)
        layout.setSpacing(10)

        # Display & Upscaling Card
        display_card = GlassCard("DISPLAY, UPSCALING & FRAME GENERATION")

        display_card.body_layout.addWidget(self._make_field_label("Target Output Resolution"))
        self._res_pills = SegmentedPills(
            [(r.id, r.label) for r in RESOLUTIONS],
            selected_id="1440p",
        )
        self._res_pills.changed.connect(self._on_display_or_setting_changed)
        display_card.body_layout.addWidget(self._res_pills)

        display_card.body_layout.addWidget(self._make_field_label("Upscaler Quality"))
        self._upscaler_pills = SegmentedPills(
            [(u.id, u.generic_label) for u in UPSCALERS],
            selected_id="quality",
            max_cols=2,
        )
        self._upscaler_pills.changed.connect(self._on_display_or_setting_changed)
        display_card.body_layout.addWidget(self._upscaler_pills)

        display_card.body_layout.addWidget(self._make_field_label("Frame Generation"))
        self._fg_pills = SegmentedPills(
            [(f.id, f.label) for f in FRAME_GEN_MODES],
            selected_id="off",
        )
        self._fg_pills.changed.connect(self._on_display_or_setting_changed)
        display_card.body_layout.addWidget(self._fg_pills)

        dlss5_lbl = self._make_field_label("DLSS 5 Neural Rendering")
        dlss5_lbl.setToolTip(
            "DLSS 5 Neural Rendering trades ~28% GPU FPS + 1.3 GB VRAM for AI-synthesized materials & lighting"
        )
        display_card.body_layout.addWidget(dlss5_lbl)
        self._dlss5_pills = SegmentedPills(
            [("off", "Off"), ("on", "On (3D-Guided)")],
            selected_id="off",
        )
        self._dlss5_pills.changed.connect(self._on_display_or_setting_changed)
        display_card.body_layout.addWidget(self._dlss5_pills)

        layout.addWidget(display_card)

        # Quick Setting Presets Card
        presets_card = GlassCard("TEX2 CONSOLE & PC PRESETS")
        grid_presets = QGridLayout()
        grid_presets.setSpacing(6)
        for idx, preset in enumerate(SETTINGS_PRESETS):
            btn = QPushButton(preset.label)
            btn.setObjectName("PresetBtn")
            btn.setMinimumWidth(0)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            btn.setToolTip(preset.description_en)
            btn.clicked.connect(lambda _c=False, pid=preset.id: self._apply_settings_preset(pid))
            grid_presets.addWidget(btn, idx // 3, idx % 3)
            self._settings_preset_buttons[preset.id] = btn
        presets_card.body_layout.addLayout(grid_presets)

        # Quick expand/collapse controls
        cat_ctrl_row = QHBoxLayout()
        cat_ctrl_row.setSpacing(6)
        cat_hint = QLabel("Click headers to fold • Hover settings for Tex2 notes")
        cat_hint.setWordWrap(True)
        cat_hint.setMinimumWidth(0)
        cat_hint.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        cat_hint.setStyleSheet("font-size: 10px; color: #94A3B8;")
        cat_ctrl_row.addWidget(cat_hint, 1)

        expand_btn = QPushButton("Expand All")
        expand_btn.setObjectName("PillBtn")
        expand_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        expand_btn.clicked.connect(lambda: self._set_all_categories_collapsed(False))
        cat_ctrl_row.addWidget(expand_btn)

        collapse_btn = QPushButton("Collapse All")
        collapse_btn.setObjectName("PillBtn")
        collapse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        collapse_btn.clicked.connect(lambda: self._set_all_categories_collapsed(True))
        cat_ctrl_row.addWidget(collapse_btn)
        presets_card.body_layout.addLayout(cat_ctrl_row)

        layout.addWidget(presets_card)

        # Categorized Graphics Sliders (Accordion Glass Cards)
        for category in SETTING_CATEGORIES:
            cat_card = GlassCard(category.upper(), collapsible=True, collapsed=False)
            cat_settings = [s for s in SETTINGS if s.category == category]
            for s in cat_settings:
                row_widget = SettingRow(s, self._settings_state[s.id])
                row_widget.value_changed.connect(self._on_setting_row_changed)
                cat_card.body_layout.addWidget(row_widget)
                self._setting_rows[s.id] = row_widget
            self._category_cards.append(cat_card)
            layout.addWidget(cat_card)

        layout.addStretch(1)
        return panel

    # ------------------------------------------------------------------
    # RIGHT PANEL (~30%): Live Telemetry, Bottleneck Radar & Multi-GPU Chart
    # ------------------------------------------------------------------
    def _build_right_telemetry_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(2, 0, 10, 0)
        layout.setSpacing(10)

        self._hero_card = HeroTelemetryCard()
        layout.addWidget(self._hero_card)

        # Component Load & Memory Spillover Meters
        meters_card = GlassCard("COMPONENT LOAD & MEMORY POOL")
        self._gpu_load_bar = NeonMeterBar("GPU Core Load")
        self._rt_load_bar = NeonMeterBar("Ray Tracing Core Load")
        self._cpu_load_bar = NeonMeterBar("CPU Simulation Load")
        self._vram_bar = NeonMeterBar("VRAM Footprint")
        self._ram_bar = NeonMeterBar("System RAM")

        for bar in (
            self._gpu_load_bar,
            self._rt_load_bar,
            self._cpu_load_bar,
            self._vram_bar,
            self._ram_bar,
        ):
            meters_card.body_layout.addWidget(bar)
        layout.addWidget(meters_card)

        # Magic Auto-Optimize Card
        opt_card = GlassCard()
        opt_row = QHBoxLayout()
        opt_row.setSpacing(8)

        self._magic_btn = QPushButton("Auto-Optimize for 60 FPS")
        self._magic_btn.setObjectName("MagicBtn")
        self._magic_btn.setMinimumWidth(0)
        self._magic_btn.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self._magic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._magic_btn.clicked.connect(self._on_auto_optimize)
        opt_row.addWidget(self._magic_btn, 1)

        self._undo_btn = QPushButton("Undo")
        self._undo_btn.setObjectName("GhostBtn")
        self._undo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._undo_btn.setVisible(False)
        self._undo_btn.clicked.connect(self._on_undo_optimize)
        opt_row.addWidget(self._undo_btn)

        opt_card.body_layout.addLayout(opt_row)

        self._opt_status_lbl = QLabel()
        self._opt_status_lbl.setWordWrap(True)
        self._opt_status_lbl.setVisible(False)
        self._opt_status_lbl.setStyleSheet(
            f"font-size: 10.5px; color: {EMERALD}; background-color: rgba(0, 230, 118, 0.08); "
            "border: 1px solid rgba(0, 230, 118, 0.30); border-radius: 7px; padding: 5px 8px;"
        )
        opt_card.body_layout.addWidget(self._opt_status_lbl)
        layout.addWidget(opt_card)

        # Bottleneck Diagnosis Box
        self._diagnosis_box = BottleneckDiagnosisBox()
        layout.addWidget(self._diagnosis_box)

        # Multi-GPU Comparison Chart Card
        chart_card = GlassCard("LIVE MULTI-GPU COMPARISON (BASE FPS)")
        legend = QLabel("Selected GPU in Neon Cyan/Pink  •  Console Baselines in Violet  •  Hover bars for 1% Lows")
        legend.setWordWrap(True)
        legend.setStyleSheet("font-size: 10px; color: #94A3B8;")
        chart_card.body_layout.addWidget(legend)

        self._gpu_chart = MultiGPUComparisonChart()
        chart_card.body_layout.addWidget(self._gpu_chart)
        layout.addWidget(chart_card)

        layout.addStretch(1)
        return panel

    # ------------------------------------------------------------------
    # Event Handlers & Helpers
    # ------------------------------------------------------------------
    def _make_field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("FieldLabel")
        return lbl

    def _set_all_categories_collapsed(self, collapsed: bool) -> None:
        for card in self._category_cards:
            card.set_collapsed(collapsed)

    def _toggle_language(self) -> None:
        self._lang = "fa" if self._lang_btn.isChecked() else "en"
        self._lang_btn.setText("فارسی ✓" if self._lang == "fa" else "EN / فارسی")
        for row in self._setting_rows.values():
            row.set_language(self._lang)
        self._diagnosis_box.set_language(self._lang)

    def _on_export_markdown(self) -> None:
        default_name = "gta6_fps_report.md"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export GTA VI Telemetry Report",
            default_name,
            "Markdown Files (*.md);;All Files (*)",
        )
        if not file_path:
            return
        target = Path(file_path)
        if target.suffix.lower() != ".md":
            target = target.with_suffix(".md")
        try:
            self._export_markdown_to_path(target)
        except OSError as exc:
            QMessageBox.warning(self, "Export Failed", f"Could not save report:\n{exc}")
            return

        self._export_btn.setText("Exported ✓")
        QTimer.singleShot(2200, lambda: self._export_btn.setText("Export .md"))

    def _export_markdown_to_path(self, target: Path) -> Path:
        sim_input = self._collect_input()
        markdown = export_simulation_markdown(sim_input)
        target.write_text(markdown, encoding="utf-8")
        return target

    def _apply_hardware_preset(self, preset_id: str, recalculate: bool = True) -> None:
        preset = PRESET_BY_ID[preset_id]
        self._suppress_recalc = True
        try:
            self._set_combo_by_data(self._gpu_combo, preset.gpu_id)
            self._set_combo_by_data(self._cpu_combo, preset.cpu_id)
            self._ram_cap_pills.set_selected(str(preset.ram_gb))
            self._set_combo_by_data(self._ram_speed_combo, preset.ram_speed_id)
            self._rebar_pills.set_selected("on" if preset.rebar_enabled else "off")
            self._oc_slider.setValue(preset.gpu_oc_percent)
            self._oc_val_label.setText(f"+{preset.gpu_oc_percent}%")
            self._storage_pills.set_selected(preset.storage_type)
            self._laptop_pills.set_selected(preset.form_factor)
            self._sync_gpu_tech_labels()
            self._highlight_hw_preset(preset_id)
        finally:
            self._suppress_recalc = False
        if recalculate:
            self._recalculate()

    def _apply_settings_preset(self, preset_id: str, recalculate: bool = True) -> None:
        preset = SETTINGS_PRESET_BY_ID[preset_id]
        self._suppress_recalc = True
        try:
            self._settings_state = dict(preset.values)
            for sid, val in self._settings_state.items():
                if sid in self._setting_rows:
                    self._setting_rows[sid].set_value(val)
            if preset.resolution_id:
                self._res_pills.set_selected(preset.resolution_id)
            if preset.upscaler_id:
                self._upscaler_pills.set_selected(preset.upscaler_id)
            self._undo_snapshot = None
            self._undo_btn.setVisible(False)
            self._opt_status_lbl.setVisible(False)
            self._highlight_settings_preset(preset_id)
        finally:
            self._suppress_recalc = False
        if recalculate:
            self._recalculate()

    def _on_gpu_changed(self) -> None:
        if not self._suppress_recalc:
            self._highlight_hw_preset(None)
            self._sync_gpu_tech_labels()
            self._recalculate()

    def _on_hardware_changed(self) -> None:
        if not self._suppress_recalc:
            self._highlight_hw_preset(None)
            self._recalculate()

    def _on_oc_changed(self, value: int) -> None:
        self._oc_val_label.setText(f"+{value}%")
        if not self._suppress_recalc:
            self._highlight_hw_preset(None)
            self._recalculate()

    def _on_display_or_setting_changed(self) -> None:
        if not self._suppress_recalc:
            self._highlight_settings_preset(None)
            self._recalculate()

    def _on_setting_row_changed(self, setting_id: str, new_value: str) -> None:
        self._settings_state[setting_id] = new_value
        if not self._suppress_recalc:
            self._highlight_settings_preset(None)
            self._recalculate()

    def _on_auto_optimize(self) -> None:
        current = self._collect_input()
        self._undo_snapshot = (dict(self._settings_state), current.upscaler_id)

        opt = auto_optimize_for_60_fps(current, target_fps=60.0)
        self._suppress_recalc = True
        try:
            self._settings_state = dict(opt.settings)
            for sid, val in self._settings_state.items():
                if sid in self._setting_rows:
                    self._setting_rows[sid].set_value(val)
            self._upscaler_pills.set_selected(opt.upscaler_id)
            self._highlight_settings_preset(None)
        finally:
            self._suppress_recalc = False

        self._undo_btn.setVisible(len(opt.changed_items) > 0)
        msg = opt.summary_fa if self._lang == "fa" else opt.summary_en
        if opt.changed_items:
            preview = "; ".join(opt.changed_items[:4])
            if len(opt.changed_items) > 4:
                preview += f" (+{len(opt.changed_items) - 4} more)"
            msg = f"{msg}\nChanges: {preview}"
        self._opt_status_lbl.setText(msg)
        self._opt_status_lbl.setVisible(True)
        self._recalculate()

    def _on_undo_optimize(self) -> None:
        if not self._undo_snapshot:
            return
        prev_settings, prev_upscaler = self._undo_snapshot
        self._undo_snapshot = None
        self._suppress_recalc = True
        try:
            self._settings_state = dict(prev_settings)
            for sid, val in self._settings_state.items():
                if sid in self._setting_rows:
                    self._setting_rows[sid].set_value(val)
            self._upscaler_pills.set_selected(prev_upscaler)
        finally:
            self._suppress_recalc = False
        self._undo_btn.setVisible(False)
        self._opt_status_lbl.setVisible(False)
        self._recalculate()

    def _sync_gpu_tech_labels(self) -> None:
        gpu_id = self._gpu_combo.currentData()
        gpu = GPU_BY_ID[gpu_id]

        for u in UPSCALERS:
            self._upscaler_pills.update_label(u.id, u.display_label(gpu.upscaler_brand, gpu.vendor))
            supported = u.is_supported_by(gpu.vendor)
            tip = u.description_en if supported else u.disabled_tooltip(gpu.vendor)
            self._upscaler_pills.set_option_enabled(u.id, supported, tip)

        cur_upscaler = self._upscaler_pills.current_id()
        resolved_upscaler = resolve_upscaler_for_vendor(cur_upscaler, gpu.vendor)
        if resolved_upscaler != cur_upscaler:
            self._upscaler_pills.set_selected(resolved_upscaler)

        # Dynamically enable/disable 2x FG, 3x/4x MFG (RTX 50 & XeSS 3), and 6x MFG (DLSS 4.5)
        self._fg_pills.set_option_enabled("2x", gpu.supports_fg and gpu.max_fg_factor >= 2, "")
        mfg_tip = (
            ""
            if gpu.max_fg_factor >= 3
            else f"Multi-Frame Gen requires RTX 50-series or Intel XeSS 3 ({gpu.name} supports up to 2x FG)."
        )
        self._fg_pills.set_option_enabled("3x", gpu.supports_fg and gpu.max_fg_factor >= 3, mfg_tip)
        self._fg_pills.set_option_enabled("4x", gpu.supports_fg and gpu.max_fg_factor >= 4, mfg_tip)
        mfg6_tip = (
            ""
            if gpu.max_fg_factor >= 6
            else f"6x Multi-Frame Gen (DLSS 4.5) requires RTX 50-series ({gpu.name} supports up to {gpu.max_fg_factor}x)."
        )
        self._fg_pills.set_option_enabled("6x", gpu.supports_fg and gpu.max_fg_factor >= 6, mfg6_tip)

        cur_fg = self._fg_pills.current_id()
        cur_fg_mode = FRAME_GEN_BY_ID.get(cur_fg)
        if cur_fg_mode is not None and cur_fg_mode.max_factor > gpu.max_fg_factor:
            supported_modes = [m for m in FRAME_GEN_MODES if m.max_factor <= gpu.max_fg_factor]
            self._fg_pills.set_selected(supported_modes[-1].id if supported_modes else "off")

        dlss5_on_tip = (
            "DLSS 5 Neural Rendering trades ~28% GPU FPS + 1.3 GB VRAM for AI-synthesized materials & lighting"
            if gpu.supports_dlss5
            else "DLSS 5 3D-Guided Neural Rendering requires RTX 50-series Tensor Cores"
        )
        self._dlss5_pills.set_option_enabled("on", gpu.supports_dlss5, dlss5_on_tip)
        self._dlss5_pills.set_option_enabled("off", True, dlss5_on_tip)
        if not gpu.supports_dlss5 and self._dlss5_pills.current_id() == "on":
            self._dlss5_pills.set_selected("off")

    def _collect_input(self) -> SimulationInput:
        storage_str = self._storage_pills.current_id()
        storage: StorageType = "SATA / HDD" if storage_str == "SATA / HDD" else "NVMe Gen4"
        form_factor = self._laptop_pills.current_id()
        return SimulationInput(
            gpu_id=self._gpu_combo.currentData(),
            cpu_id=self._cpu_combo.currentData(),
            ram_gb=int(self._ram_cap_pills.current_id()),
            ram_speed_id=self._ram_speed_combo.currentData(),
            rebar_enabled=(self._rebar_pills.current_id() == "on"),
            gpu_oc_percent=int(self._oc_slider.value()),
            storage_type=storage,
            is_laptop_mode=(form_factor == "laptop"),
            resolution_id=self._res_pills.current_id(),
            upscaler_id=self._upscaler_pills.current_id(),
            frame_gen_id=self._fg_pills.current_id(),
            settings=dict(self._settings_state),
            dlss5_enabled=(self._dlss5_pills.current_id() == "on"),
            is_gaming_laptop=(form_factor == "gaming_laptop"),
        )

    def _recalculate(self) -> None:
        sim_input = self._collect_input()
        gpu = GPU_BY_ID[sim_input.gpu_id]
        cpu = CPU_BY_ID[sim_input.cpu_id]
        ram_speed = RAM_SPEED_BY_ID[sim_input.ram_speed_id]

        # Hardware info chips
        vram_txt = "16 GB Shared Pool" if gpu.is_unified_memory else f"{gpu.vram_gb:.0f} GB VRAM"
        self._gpu_spec_chip.setText(
            f"{vram_txt}  •  {gpu.bandwidth_gbps:.0f} GB/s  •  PCIe {gpu.pcie_lanes}  •  "
            f"Raster {gpu.raster_score:.0f} / RT {gpu.rt_score:.0f}  •  {gpu.fg_label}"
        )
        self._cpu_spec_chip.setText(
            f"Sim Score {cpu.gaming_score:.0f}  •  {cpu.cores_threads}  •  {cpu.architecture_notes}"
        )

        notes = get_platform_compatibility_notes(gpu, cpu, ram_speed, sim_input.is_laptop_mode)
        if notes:
            self._platform_hint_chip.setText(" | ".join(notes))
            self._platform_hint_chip.setVisible(True)
        else:
            self._platform_hint_chip.setVisible(False)

        result = simulate(sim_input)
        comparisons = compare_all_gpus(sim_input)

        # Header render scale badge
        res_lbl = next((r.label for r in RESOLUTIONS if r.id == sim_input.resolution_id), sim_input.resolution_id)
        up_obj = next((u for u in UPSCALERS if u.id == sim_input.upscaler_id), UPSCALERS[0])
        dlss5_tag = " • DLSS 5" if result.effective_dlss5 else ""
        self._render_scale_chip.setText(
            f"Render: {res_lbl} • {up_obj.display_label(gpu.upscaler_brand, gpu.vendor)} ({result.effective_res_factor:.2f}x){dlss5_tag}"
        )

        # Right column telemetry updates
        self._hero_card.update_telemetry(result)
        self._gpu_load_bar.set_percentage("GPU Core Load", result.gpu_load_pct, VIOLET)
        self._rt_load_bar.set_percentage("Ray Tracing Core Load", result.rt_load_pct, MAGENTA)
        self._cpu_load_bar.set_percentage("CPU Simulation Load", result.cpu_load_pct, CYAN)

        if result.is_unified_pool:
            self._vram_bar.set_memory(
                "Unified Pool (OS+CPU+GPU)",
                result.unified_pool_used_gb,
                result.unified_pool_total_gb,
                result.vram_overflow_gb,
            )
            self._ram_bar.set_memory(
                "VRAM Share (In Pool)",
                result.vram_used_gb,
                result.unified_pool_total_gb,
                0.0,
            )
        else:
            self._vram_bar.set_memory(
                "Dedicated VRAM Footprint",
                result.vram_used_gb,
                result.vram_total_gb,
                result.vram_overflow_gb,
            )
            self._ram_bar.set_memory(
                "System RAM Footprint",
                result.ram_used_gb,
                result.ram_total_gb,
                result.ram_overflow_gb,
            )

        self._diagnosis_box.update_diagnosis(result)
        self._gpu_chart.set_entries(comparisons)

    def _set_combo_by_data(self, combo: QComboBox, target_id: str) -> None:
        for i in range(combo.count()):
            if combo.itemData(i) == target_id:
                combo.setCurrentIndex(i)
                return

    def _highlight_hw_preset(self, active_id: str | None) -> None:
        for pid, btn in self._hw_preset_buttons.items():
            btn.setProperty("active", "true" if pid == active_id else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _highlight_settings_preset(self, active_id: str | None) -> None:
        for pid, btn in self._settings_preset_buttons.items():
            btn.setProperty("active", "true" if pid == active_id else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
