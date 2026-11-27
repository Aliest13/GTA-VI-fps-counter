"""Deterministic mathematical engine for GTA VI FPS, 1% Low, memory, and bottleneck estimation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from data.hardware_db import (
    CONSOLE_REFERENCES,
    CPU_BY_ID,
    GPU_BY_ID,
    GPUS,
    RAM_SPEED_BY_ID,
    CPUProfile,
    GPUProfile,
    RAMSpeedProfile,
    StorageType,
    get_platform_compatibility_notes,
)
from data.settings_db import (
    FRAME_GEN_BY_ID,
    RESOLUTION_BY_ID,
    SETTING_BY_ID,
    SETTINGS,
    UPSCALER_BY_ID,
)

BottleneckKind = Literal["GPU / RT", "CPU", "VRAM Overflow", "RAM / Unified Overflow", "Balanced"]

_RES_OVERHEAD_SCALE: dict[str, float] = {
    "720p": 1.05,
    "900p": 1.00,
    "1080p": 0.96,
    "1440p": 0.80,
    "4k": 0.72,
}


@dataclass(frozen=True, slots=True)
class SimulationInput:
    """Complete snapshot of hardware, display, and graphics parameters."""

    gpu_id: str
    cpu_id: str
    ram_gb: int
    ram_speed_id: str
    rebar_enabled: bool
    gpu_oc_percent: int
    storage_type: StorageType
    is_laptop_mode: bool
    resolution_id: str
    upscaler_id: str
    frame_gen_id: str
    settings: dict[str, str]


@dataclass(frozen=True, slots=True)
class WarningMessage:
    """Severity-tagged telemetry alert with bilingual explanation."""

    severity: Literal["warning", "critical", "info"]
    code: str
    title_en: str
    detail_en: str
    title_fa: str
    detail_fa: str


@dataclass(frozen=True, slots=True)
class SimulationResult:
    """Full live telemetry output for the UI and multi-GPU comparisons."""

    base_fps: float
    low_1pct_fps: float
    fg_fps: float
    effective_fg_id: str
    fg_fallback_note: str | None
    raw_gpu_fps: float
    raw_cpu_fps: float
    gpu_load_pct: float
    rt_load_pct: float
    cpu_load_pct: float
    vram_used_gb: float
    vram_total_gb: float
    vram_overflow_gb: float
    ram_used_gb: float
    ram_total_gb: float
    ram_overflow_gb: float
    is_unified_pool: bool
    unified_pool_used_gb: float
    unified_pool_total_gb: float
    effective_res_factor: float
    total_raster_cost: float
    total_rt_cost: float
    total_cpu_cost: float
    primary_bottleneck: BottleneckKind
    diagnosis_en: str
    diagnosis_fa: str
    recommendation_en: str
    recommendation_fa: str
    warnings: tuple[WarningMessage, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class GPUComparisonEntry:
    """Single row for the live Multi-GPU comparison bar chart."""

    gpu_id: str
    label: str
    base_fps: float
    low_1pct_fps: float
    is_selected: bool
    is_reference_console: bool
    has_vram_overflow: bool
    notes: str


@dataclass(frozen=True, slots=True)
class AutoOptimizeResult:
    """Output of the Auto-Optimize for 60 FPS algorithm."""

    settings: dict[str, str]
    upscaler_id: str
    changed_items: tuple[str, ...]
    reached_target: bool
    resulting_base_fps: float
    summary_en: str
    summary_fa: str


def _damp_cost_above_baseline(cost: float, slope: float = 0.32, floor: float = 0.45) -> float:
    """Preserve <=1.0 savings linearly while modeling engine pass overlap above 1.0."""
    clamped = max(floor, cost)
    if clamped <= 1.0:
        return clamped
    return 1.0 + slope * (clamped - 1.0)


def _smooth_min(a: float, b: float, power: float = 16.0) -> float:
    """Smooth min(a, b) with realistic ~4% frame-time contention when CPU and GPU match."""
    safe_a = max(1.0, a)
    safe_b = max(1.0, b)
    return 1.0 / ((safe_a ** (-power) + safe_b ** (-power)) ** (1.0 / power))


def _resolve_fg(gpu: GPUProfile, requested_fg_id: str) -> tuple[str, float, float, str | None]:
    """Validate frame generation compatibility against the selected GPU."""
    fg = FRAME_GEN_BY_ID.get(requested_fg_id, FRAME_GEN_BY_ID["off"])
    if fg.id == "off":
        return "off", 1.0, 0.0, None
    if not gpu.supports_fg:
        return "off", 1.0, 0.0, f"{gpu.name} does not support PC Frame Generation; reverted to Off."
    if fg.requires_mfg and not gpu.supports_mfg:
        fallback = FRAME_GEN_BY_ID["2x"]
        return (
            fallback.id,
            fallback.fps_multiplier,
            fallback.base_overhead,
            f"MFG ({fg.label}) requires RTX 50-series; fell back to 2x FG ({gpu.fg_label}).",
        )
    return fg.id, fg.fps_multiplier, fg.base_overhead, None


def _accumulate_costs(settings_map: dict[str, str]) -> tuple[float, float, float, float, float]:
    """Sum setting deltas relative to PS5 / Series X baseline."""
    raster = 1.0
    rt = 1.0
    cpu = 1.0
    vram_mb = 0.0
    ram_mb = 0.0

    for definition in SETTINGS:
        chosen = settings_map.get(definition.id, definition.default_option)
        opt = definition.get_option(chosen)
        raster += opt.raster_cost
        rt += opt.rt_cost
        cpu += opt.cpu_cost
        vram_mb += opt.vram_mb
        ram_mb += opt.ram_mb

    return raster, rt, cpu, vram_mb, ram_mb


def simulate(
    sim_input: SimulationInput,
    gpu_override: GPUProfile | None = None,
    cpu_override: CPUProfile | None = None,
) -> SimulationResult:
    """Run deterministic telemetry simulation for the provided hardware and settings."""
    gpu = gpu_override or GPU_BY_ID[sim_input.gpu_id]
    cpu: CPUProfile = cpu_override or CPU_BY_ID[sim_input.cpu_id]
    ram_speed: RAMSpeedProfile = RAM_SPEED_BY_ID[sim_input.ram_speed_id]
    res = RESOLUTION_BY_ID[sim_input.resolution_id]
    upscaler = UPSCALER_BY_ID[sim_input.upscaler_id]

    eff_fg_id, fg_mult, _fg_overhead, fg_note = _resolve_fg(gpu, sim_input.frame_gen_id)
    # Fixed RT & shader overhead prevents sub-540p internal scales from scaling linearly.
    effective_res_factor = max(0.26, res.base_res_factor * upscaler.render_multiplier)

    raw_raster, raw_rt, raw_cpu, delta_vram_mb, delta_ram_mb = _accumulate_costs(sim_input.settings)

    damped_raster = _damp_cost_above_baseline(raw_raster, slope=0.32)
    damped_rt = _damp_cost_above_baseline(raw_rt, slope=0.32)
    damped_cpu = _damp_cost_above_baseline(raw_cpu, slope=0.32, floor=0.70)

    if cpu.has_3d_vcache and damped_cpu > 1.0:
        # 96MB 3D V-Cache mitigates Ultra BVH/AI cache thrashing.
        damped_cpu = 1.0 + 0.85 * (damped_cpu - 1.0)

    # 1. VRAM & System RAM demand
    fg_vram_gb = 0.55 if eff_fg_id != "off" else 0.0
    vram_used_gb = max(
        3.0,
        7.4 + res.vram_delta_gb + fg_vram_gb + (delta_vram_mb / 1024.0),
    )
    os_ram_gb = 4.2
    game_ram_gb = max(4.5, 8.2 + (delta_ram_mb / 1024.0))
    ram_used_gb = os_ram_gb + game_ram_gb

    is_unified_pool = gpu.is_unified_memory
    if is_unified_pool:
        unified_pool_total_gb = float(sim_input.ram_gb)
        unified_pool_used_gb = os_ram_gb + game_ram_gb + (vram_used_gb * 0.72)
        vram_total_gb = unified_pool_total_gb
        ram_total_gb = unified_pool_total_gb
        vram_overflow_gb = max(0.0, unified_pool_used_gb - unified_pool_total_gb)
        ram_overflow_gb = vram_overflow_gb
    else:
        unified_pool_total_gb = float(sim_input.ram_gb)
        unified_pool_used_gb = ram_used_gb
        vram_total_gb = gpu.vram_gb
        ram_total_gb = float(sim_input.ram_gb)
        vram_overflow_gb = max(0.0, vram_used_gb - (gpu.vram_gb - 0.3))
        ram_overflow_gb = max(0.0, ram_used_gb - float(sim_input.ram_gb))

    # 2. Raw GPU FPS ceiling (calibrated around PS5 GPU = 100 baseline)
    rt_share = 0.45 * (damped_rt / max(0.5, 0.55 * damped_raster + 0.45 * damped_rt))
    rt_share = min(0.62, max(0.30, rt_share))
    raster_share = 1.0 - rt_share

    weighted_gpu_score = (raster_share * gpu.raster_score + rt_share * gpu.rt_score) / 100.0
    oc_mult = 1.0 + (max(0, min(7, sim_input.gpu_oc_percent)) / 100.0)
    weighted_gpu_demand = raster_share * damped_raster + rt_share * damped_rt

    raw_gpu_fps = (weighted_gpu_score * oc_mult / weighted_gpu_demand) * 32.0 / effective_res_factor

    # Dedicated VRAM or Unified Pool GPU spillover penalty
    if is_unified_pool:
        vram_avg_mult = max(0.50, 1.0 - vram_overflow_gb * 0.10) if vram_overflow_gb > 0 else 1.0
        vram_low_mult = max(0.30, 1.0 - vram_overflow_gb * 0.24) if vram_overflow_gb > 0 else 1.0
    else:
        pcie_penalty = 0.22 if gpu.pcie_lanes == "x8" else 0.16
        vram_avg_mult = max(0.30, 1.0 - vram_overflow_gb * pcie_penalty) if vram_overflow_gb > 0 else 1.0
        vram_low_mult = max(0.20, 1.0 - vram_overflow_gb * 0.32) if vram_overflow_gb > 0 else 1.0

    # 3. Raw CPU FPS ceiling
    if gpu.is_reference_console:
        driver_overhead = 0.0
    else:
        base_overhead = (
            gpu.driver_cpu_overhead if sim_input.rebar_enabled else gpu.driver_cpu_overhead_no_rebar
        )
        driver_overhead = base_overhead * _RES_OVERHEAD_SCALE.get(res.id, 0.90)

    effective_cpu_score = cpu.gaming_score * ram_speed.cpu_multiplier * (1.0 - driver_overhead)
    raw_cpu_fps = (effective_cpu_score * 0.88) / damped_cpu

    # 4. System RAM swap penalty (desktop dedicated or unified pool)
    if ram_overflow_gb > 0 and not is_unified_pool:
        ram_avg_mult = 0.65
        ram_low_mult = 0.40
    elif ram_overflow_gb > 0 and is_unified_pool:
        ram_avg_mult = 0.80
        ram_low_mult = 0.58
    else:
        ram_avg_mult = 1.0
        ram_low_mult = 1.0

    # 5. Laptop thermal & power coupling penalty (20-25W shared TDP)
    is_thermal_coupled = (
        (sim_input.is_laptop_mode or gpu.is_laptop_thermal or cpu.is_laptop_thermal)
        and not gpu.is_reference_console
    )
    thermal_mult = 0.82 if is_thermal_coupled else 1.0

    effective_gpu_fps = raw_gpu_fps * vram_avg_mult * thermal_mult
    effective_cpu_fps = raw_cpu_fps * ram_avg_mult * thermal_mult

    # 6. Smooth bottleneck blending & 1% Low FPS
    base_fps = _smooth_min(effective_gpu_fps, effective_cpu_fps, power=16.0)

    # 1% Low calculation
    cpu_low_ram_ratio = ram_speed.low_1pct_multiplier / ram_speed.cpu_multiplier
    cpu_low_fps = effective_cpu_fps * 0.785 * cpu_low_ram_ratio
    gpu_low_fps = effective_gpu_fps * 0.86

    low_1pct_fps = _smooth_min(cpu_low_fps, gpu_low_fps, power=12.0)
    low_1pct_fps *= vram_low_mult
    if not is_unified_pool:
        low_1pct_fps *= ram_low_mult
    if sim_input.storage_type == "SATA / HDD":
        low_1pct_fps *= 0.72
    low_1pct_fps = min(base_fps * 0.94, max(1.0, low_1pct_fps))

    # Frame generation output
    fg_fps = base_fps * fg_mult if eff_fg_id != "off" else base_fps

    # Component Load % estimates
    gpu_load_pct = min(100.0, max(12.0, (base_fps / max(1.0, effective_gpu_fps)) * 99.0))
    rt_load_pct = min(100.0, max(10.0, gpu_load_pct * min(1.12, 0.78 * damped_rt)))
    cpu_load_pct = min(100.0, max(10.0, (base_fps / max(1.0, effective_cpu_fps)) * 96.0))

    # Determine primary bottleneck and warnings
    warnings: list[WarningMessage] = []
    if vram_overflow_gb > 0 and not is_unified_pool:
        primary_bottleneck: BottleneckKind = "VRAM Overflow"
    elif ram_overflow_gb > 0:
        primary_bottleneck = "RAM / Unified Overflow"
    elif abs(effective_gpu_fps - effective_cpu_fps) / max(effective_gpu_fps, effective_cpu_fps) <= 0.08:
        primary_bottleneck = "Balanced"
    elif effective_gpu_fps < effective_cpu_fps:
        primary_bottleneck = "GPU / RT"
    else:
        primary_bottleneck = "CPU"

    if not gpu.is_reference_console:
        warnings.extend(
            _build_warnings(
                sim_input=sim_input,
                gpu=gpu,
                cpu=cpu,
                ram_speed=ram_speed,
                base_fps=base_fps,
                eff_fg_id=eff_fg_id,
                fg_note=fg_note,
                vram_used_gb=vram_used_gb,
                vram_total_gb=vram_total_gb,
                vram_overflow_gb=vram_overflow_gb,
                ram_used_gb=ram_used_gb,
                ram_total_gb=ram_total_gb,
                ram_overflow_gb=ram_overflow_gb,
                is_unified_pool=is_unified_pool,
                unified_pool_used_gb=unified_pool_used_gb,
                unified_pool_total_gb=unified_pool_total_gb,
            )
        )

    diag_en, diag_fa, rec_en, rec_fa = _build_diagnosis(
        primary_bottleneck=primary_bottleneck,
        gpu=gpu,
        cpu=cpu,
        ram_speed=ram_speed,
        rebar_enabled=sim_input.rebar_enabled,
        effective_gpu_fps=effective_gpu_fps,
        effective_cpu_fps=effective_cpu_fps,
        vram_used_gb=vram_used_gb,
        vram_total_gb=vram_total_gb,
        vram_overflow_gb=vram_overflow_gb,
        ram_overflow_gb=ram_overflow_gb,
        is_unified_pool=is_unified_pool,
        unified_pool_used_gb=unified_pool_used_gb,
        unified_pool_total_gb=unified_pool_total_gb,
        damped_rt=damped_rt,
        damped_raster=damped_raster,
        is_thermal_coupled=is_thermal_coupled,
        storage_type=sim_input.storage_type,
    )

    return SimulationResult(
        base_fps=round(base_fps, 1),
        low_1pct_fps=round(low_1pct_fps, 1),
        fg_fps=round(fg_fps, 1),
        effective_fg_id=eff_fg_id,
        fg_fallback_note=fg_note,
        raw_gpu_fps=round(effective_gpu_fps, 1),
        raw_cpu_fps=round(effective_cpu_fps, 1),
        gpu_load_pct=round(gpu_load_pct, 1),
        rt_load_pct=round(rt_load_pct, 1),
        cpu_load_pct=round(cpu_load_pct, 1),
        vram_used_gb=round(vram_used_gb, 2),
        vram_total_gb=round(vram_total_gb, 1),
        vram_overflow_gb=round(vram_overflow_gb, 2),
        ram_used_gb=round(ram_used_gb, 2),
        ram_total_gb=round(ram_total_gb, 1),
        ram_overflow_gb=round(ram_overflow_gb, 2),
        is_unified_pool=is_unified_pool,
        unified_pool_used_gb=round(unified_pool_used_gb, 2),
        unified_pool_total_gb=round(unified_pool_total_gb, 1),
        effective_res_factor=round(effective_res_factor, 3),
        total_raster_cost=round(raw_raster, 2),
        total_rt_cost=round(raw_rt, 2),
        total_cpu_cost=round(raw_cpu, 2),
        primary_bottleneck=primary_bottleneck,
        diagnosis_en=diag_en,
        diagnosis_fa=diag_fa,
        recommendation_en=rec_en,
        recommendation_fa=rec_fa,
        warnings=tuple(warnings),
    )


def _build_warnings(
    *,
    sim_input: SimulationInput,
    gpu: GPUProfile,
    cpu: CPUProfile,
    ram_speed: RAMSpeedProfile,
    base_fps: float,
    eff_fg_id: str,
    fg_note: str | None,
    vram_used_gb: float,
    vram_total_gb: float,
    vram_overflow_gb: float,
    ram_used_gb: float,
    ram_total_gb: float,
    ram_overflow_gb: float,
    is_unified_pool: bool,
    unified_pool_used_gb: float,
    unified_pool_total_gb: float,
) -> list[WarningMessage]:
    warnings: list[WarningMessage] = []

    if is_unified_pool:
        ratio = unified_pool_used_gb / max(1.0, unified_pool_total_gb)
        if vram_overflow_gb > 0:
            warnings.append(
                WarningMessage(
                    severity="critical",
                    code="unified_overflow",
                    title_en=f"Unified Memory Overflow (+{vram_overflow_gb:.1f} GB)",
                    detail_en=(
                        f"Combined OS + GTA VI + VRAM pool needs {unified_pool_used_gb:.1f} GB on a "
                        f"{unified_pool_total_gb:.0f} GB shared pool. Expect pagefile thrashing & heavy stutters."
                    ),
                    title_fa=f"سرریز حافظه یکپارچه لپ‌تاپ (+{vram_overflow_gb:.1f} گیگابایت)",
                    detail_fa=(
                        f"مجموع مصرف سیستم‌عامل، بازی و VRAM به {unified_pool_used_gb:.1f} گیگابایت رسیده "
                        f"که از کل ظرفیت {unified_pool_total_gb:.0f} گیگابایتی بیشتر است و باعث لگ شدید می‌شود."
                    ),
                )
            )
        elif ratio >= 0.88:
            warnings.append(
                WarningMessage(
                    severity="warning",
                    code="unified_tight",
                    title_en=f"Tight Unified Pool ({unified_pool_used_gb:.1f} / {unified_pool_total_gb:.0f} GB)",
                    detail_en="Shared memory is above 88% utilization; background apps may trigger stutter.",
                    title_fa=f"فشار بالای حافظه یکپارچه ({unified_pool_used_gb:.1f} از {unified_pool_total_gb:.0f} گیگابایت)",
                    detail_fa="بیش از ۸۸٪ حافظه مشترک پر شده است؛ برنامه‌های پس‌زمینه می‌توانند افت فریم بدهند.",
                )
            )
    else:
        if vram_overflow_gb > 0:
            bus_note = " over PCIe x8!" if gpu.pcie_lanes == "x8" else "."
            warnings.append(
                WarningMessage(
                    severity="critical",
                    code="vram_overflow",
                    title_en=f"{vram_total_gb:.0f}GB VRAM Overflow (+{vram_overflow_gb:.1f} GB)",
                    detail_en=(
                        f"Requested {vram_used_gb:.1f} GB exceeds {vram_total_gb:.0f} GB VRAM, spilling "
                        f"into system RAM{bus_note} Severe 1% Low collapse."
                    ),
                    title_fa=f"سرریز حافظه VRAM کارت {vram_total_gb:.0f} گیگابایتی (+{vram_overflow_gb:.1f} GB)",
                    detail_fa=(
                        f"مصرف {vram_used_gb:.1f} گیگابایت از ظرفیت {vram_total_gb:.0f} گیگابایت کارت عبور کرده "
                        "و باعث افت شدید فریم لحظه‌ای (1% Low) می‌شود."
                    ),
                )
            )
        elif (vram_used_gb / max(1.0, vram_total_gb)) >= 0.88:
            warnings.append(
                WarningMessage(
                    severity="warning",
                    code="vram_near_limit",
                    title_en=f"High VRAM Pressure ({vram_used_gb:.1f} / {vram_total_gb:.0f} GB)",
                    detail_en="VRAM usage exceeds 88%; dense downtown scenes may spike textures.",
                    title_fa=f"مصرف بالای VRAM ({vram_used_gb:.1f} از {vram_total_gb:.0f} گیگابایت)",
                    detail_fa="مصرف VRAM بالای ۸۸٪ است و در مناطق شلوغ شهر ممکن است نوسان ایجاد کند.",
                )
            )

        if ram_overflow_gb > 0:
            warnings.append(
                WarningMessage(
                    severity="critical",
                    code="ram_overflow",
                    title_en=f"System RAM Overflow (+{ram_overflow_gb:.1f} GB)",
                    detail_en=(
                        f"{ram_used_gb:.1f} GB required on {ram_total_gb:.0f} GB RAM — Windows pagefile "
                        "swapping cuts 1% Lows dramatically."
                    ),
                    title_fa=f"کمبود رم سیستم (+{ram_overflow_gb:.1f} گیگابایت)",
                    detail_fa=(
                        f"مصرف {ram_used_gb:.1f} گیگابایت از رم {ram_total_gb:.0f} گیگابایتی بیشتر است "
                        "و Swap دیسک باعث لگ شدید می‌شود."
                    ),
                )
            )

    if not sim_input.rebar_enabled and gpu.id == "arc_b580":
        warnings.append(
            WarningMessage(
                severity="critical",
                code="arc_no_rebar",
                title_en="Resizable BAR OFF on Intel Arc B580",
                detail_en="Intel Arc driver CPU overhead jumps from 7% to 28% without ReBAR!",
                title_fa="خاموش بودن Resizable BAR روی کارت Intel Arc B580",
                detail_fa="بدون ReBAR سربار پردازنده درایور اینتل از ۷٪ به ۲۸٪ جهش می‌کند!",
            )
        )

    if eff_fg_id != "off" and base_fps < 38.0:
        warnings.append(
            WarningMessage(
                severity="warning",
                code="fg_low_base",
                title_en="High Input Latency / Artifacts Risk (Base FPS < 38)",
                detail_en=(
                    f"Base FPS is {base_fps:.1f}; enabling Frame Generation below 38 FPS causes sluggish "
                    "controls and HUD/motion artifacts."
                ),
                title_fa="تاخیر ورودی بالا / ریسک آرتیفکت تصویر (فریم پایه زیر ۳۸)",
                detail_fa=(
                    f"فریم پایه {base_fps:.1f} است؛ فعال‌سازی Frame Gen زیر ۳۸ فریم باعث کندی کنترل و خطای تصویر می‌شود."
                ),
            )
        )

    if sim_input.storage_type == "SATA / HDD":
        warnings.append(
            WarningMessage(
                severity="warning",
                code="slow_storage",
                title_en="SATA / HDD Streaming Penalty",
                detail_en="High-speed driving streams RAGE 9 assets too slowly on SATA/HDD (-28% 1% Lows).",
                title_fa="جریمه سرعت دیسک SATA / HDD",
                detail_fa="بارگذاری سریع بافت‌ها هنگام رانندگی روی SATA/HDD با افت ۲۸٪ در 1% Low همراه است.",
            )
        )

    if fg_note:
        warnings.append(
            WarningMessage(
                severity="info",
                code="fg_fallback",
                title_en="Frame Gen Adjusted",
                detail_en=fg_note,
                title_fa="تنظیم خودکار Frame Gen",
                detail_fa=fg_note,
            )
        )

    for note in get_platform_compatibility_notes(gpu, cpu, ram_speed, sim_input.is_laptop_mode):
        warnings.append(
            WarningMessage(
                severity="info",
                code="platform_hint",
                title_en="Platform Note",
                detail_en=note,
                title_fa="نکته سخت‌افزاری",
                detail_fa=note,
            )
        )

    return warnings


def _build_diagnosis(
    *,
    primary_bottleneck: BottleneckKind,
    gpu: GPUProfile,
    cpu: CPUProfile,
    ram_speed: RAMSpeedProfile,
    rebar_enabled: bool,
    effective_gpu_fps: float,
    effective_cpu_fps: float,
    vram_used_gb: float,
    vram_total_gb: float,
    vram_overflow_gb: float,
    ram_overflow_gb: float,
    is_unified_pool: bool,
    unified_pool_used_gb: float,
    unified_pool_total_gb: float,
    damped_rt: float,
    damped_raster: float,
    is_thermal_coupled: bool,
    storage_type: StorageType,
) -> tuple[str, str, str, str]:
    thermal_suffix_en = (
        " Shared 20-25W laptop TDP also caps sustained boost." if is_thermal_coupled else ""
    )
    thermal_suffix_fa = (
        " محدودیت توان مشترک ۲۰ تا ۲۵ واتی لپ‌تاپ نیز سقف کلاک را پایین می‌آورد."
        if is_thermal_coupled
        else ""
    )

    if primary_bottleneck == "VRAM Overflow":
        diag_en = (
            f"VRAM Spillover Bottleneck: GTA VI requests {vram_used_gb:.1f} GB on {gpu.name}'s "
            f"{vram_total_gb:.0f} GB buffer (+{vram_overflow_gb:.1f} GB spill over {gpu.pcie_lanes})."
        )
        diag_fa = (
            f"گلوگاه سرریز VRAM: بازی به {vram_used_gb:.1f} گیگابایت نیاز دارد در حالی که کارت "
            f"{vram_total_gb:.0f} گیگابایت حافظه دارد (+{vram_overflow_gb:.1f} GB سرریز)."
        )
        rec_en = (
            "Drop Texture Quality to High/Medium, Vehicle HD Count to High, or disable RT Shadows "
            "to keep allocation under the VRAM cap."
        )
        rec_fa = (
            "کیفیت بافت (Texture) و بافت خودروها را یک پله کم کنید یا RT Shadows را ببندید "
            "تا مصرف به زیر سقف VRAM برگردد."
        )
        return diag_en, diag_fa, rec_en, rec_fa

    if primary_bottleneck == "RAM / Unified Overflow":
        if is_unified_pool:
            diag_en = (
                f"Unified Memory Pool Bottleneck: Shared OS + CPU + GPU demand is "
                f"{unified_pool_used_gb:.1f} GB vs {unified_pool_total_gb:.0f} GB LPDDR5X.{thermal_suffix_en}"
            )
            diag_fa = (
                f"گلوگاه حافظه یکپارچه لپ‌تاپ: مجموع مصرف سیستم و گرافیک به {unified_pool_used_gb:.1f} از "
                f"{unified_pool_total_gb:.0f} گیگابایت رسیده است.{thermal_suffix_fa}"
            )
            rec_en = (
                "Lower Resolution to 720p, Texture Quality to Medium, and Pedestrian Density to Medium/Low."
            )
            rec_fa = (
                "رزولوشن را روی 720p بگذارید و Texture Quality و تراکم جمعیت را روی Medium/Low قرار دهید."
            )
        else:
            diag_en = (
                f"System RAM Overflow: {ram_overflow_gb:.1f} GB beyond physical RAM forces Windows "
                "disk paging during streaming."
            )
            diag_fa = (
                f"گلوگاه کمبود رم سیستم: {ram_overflow_gb:.1f} گیگابایت سرریز به دیسک باعث افت شدید فریم می‌شود."
            )
            rec_en = "Drop Pedestrian & Vehicle Density to Medium/Low and close background browsers."
            rec_fa = "تراکم عابران و خودروها را کاهش دهید و برنامه‌های پس‌زمینه را ببندید."
        return diag_en, diag_fa, rec_en, rec_fa

    if primary_bottleneck == "CPU":
        overhead_txt = (
            " + Arc ReBAR-OFF overhead (28%)"
            if (gpu.id == "arc_b580" and not rebar_enabled)
            else ""
        )
        diag_en = (
            f"CPU Simulation Bottleneck: {cpu.name} + {ram_speed.name}{overhead_txt} caps FPS around "
            f"{effective_cpu_fps:.0f} FPS while GPU headroom reaches {effective_gpu_fps:.0f} FPS."
            f"{thermal_suffix_en}"
        )
        diag_fa = (
            f"گلوگاه پردازنده (CPU): ترکیب {cpu.name} و {ram_speed.name} سقف فریم را روی حدود "
            f"{effective_cpu_fps:.0f} فریم محدود کرده، در حالی که کارت گرافیک توان {effective_gpu_fps:.0f} فریم را دارد."
            f"{thermal_suffix_fa}"
        )
        if gpu.id == "arc_b580" and not rebar_enabled:
            rec_en = "Enable Resizable BAR in BIOS immediately, then reduce Pedestrian Density or BVH Quality."
            rec_fa = "حتماً Resizable BAR را در بایوس روشن کنید و سپس تراکم جمعیت یا BVH Quality را کم کنید."
        else:
            rec_en = (
                "Lower Pedestrian & Vehicle Density, AI/Physics Quality, BVH Quality, or LOD Scale — "
                "changing resolution/upscaler will NOT lift a CPU cap."
            )
            rec_fa = (
                "تراکم جمعیت، کیفیت هوش مصنوعی/فیزیک، BVH یا LOD Scale را کم کنید؛ "
                "کاهش رزولوشن گلوگاه CPU را برطرف نمی‌کند."
            )
        return diag_en, diag_fa, rec_en, rec_fa

    if primary_bottleneck == "GPU / RT":
        rt_heavy = damped_rt >= damped_raster * 1.08
        aspect_en = "Ray Tracing (RTGI / RT Shadows / Reflections)" if rt_heavy else "Shader / Pixel Fillrate"
        aspect_fa = "ردیابی پرتو (RTGI / سایه RT / بازتاب‌ها)" if rt_heavy else "پردازش شیدر و پیکسل"
        diag_en = (
            f"GPU Bound ({aspect_en}): {gpu.name} limits output to {effective_gpu_fps:.0f} FPS "
            f"while {cpu.name} can feed {effective_cpu_fps:.0f} FPS.{thermal_suffix_en}"
        )
        diag_fa = (
            f"گلوگاه کارت گرافیک ({aspect_fa}): کارت {gpu.name} خروجی را روی {effective_gpu_fps:.0f} فریم "
            f"محدود کرده در حالی که CPU تا {effective_cpu_fps:.0f} فریم توان دارد.{thermal_suffix_fa}"
        )
        rec_en = (
            "Step up Upscaler (Quality/Balanced) or trim RT Shadows, Reflections, and Volumetrics."
        )
        rec_fa = (
            "حالت آپ‌اسکیلر را به Quality/Balanced تغییر دهید یا RT Shadows، Reflections و Volumetrics را پایین بیاورید."
        )
        return diag_en, diag_fa, rec_en, rec_fa

    # Balanced
    storage_hint_en = " (Upgrade to NVMe Gen4 to remove streaming dips.)" if storage_type == "SATA / HDD" else ""
    storage_hint_fa = " (ارتقا به NVMe Gen4 لگ‌های بارگذاری مسیر را حذف می‌کند.)" if storage_type == "SATA / HDD" else ""
    diag_en = (
        f"Well-Balanced System: GPU ({effective_gpu_fps:.0f} FPS) and CPU ({effective_cpu_fps:.0f} FPS) "
        f"are tightly matched with healthy headroom.{thermal_suffix_en}{storage_hint_en}"
    )
    diag_fa = (
        f"سیستم متعادل: توان کارت گرافیک ({effective_gpu_fps:.0f} فریم) و پردازنده ({effective_cpu_fps:.0f} فریم) "
        f"هماهنگی بسیار خوبی دارند.{thermal_suffix_fa}{storage_hint_fa}"
    )
    rec_en = "Great balance! Fine-tune Upscaler or Volumetrics/RT Shadows only if targeting higher refresh."
    rec_fa = "تعادل عالی است! تنها در صورت نیاز به فریم بالاتر، آپ‌اسکیلر یا Volumetrics را تنظیم کنید."
    return diag_en, diag_fa, rec_en, rec_fa


def compare_all_gpus(sim_input: SimulationInput) -> list[GPUComparisonEntry]:
    """Compute Base FPS and 1% Low across all 9 GPUs + PS5 / PS5 Pro console references."""
    entries: list[GPUComparisonEntry] = []

    for gpu in GPUS:
        # Compare each GPU fairly on the user's CPU/RAM/settings; if comparing Arc 140V from desktop,
        # simulate its coupled 16GB shared pool and thermal envelope accurately.
        if gpu.id == sim_input.gpu_id:
            res = simulate(sim_input)
        elif gpu.is_unified_memory:
            laptop_input = SimulationInput(
                gpu_id=gpu.id,
                cpu_id="ultra_7_256v" if sim_input.is_laptop_mode else sim_input.cpu_id,
                ram_gb=16,
                ram_speed_id="lpddr5x_8533",
                rebar_enabled=True,
                gpu_oc_percent=0,
                storage_type=sim_input.storage_type,
                is_laptop_mode=True,
                resolution_id=sim_input.resolution_id,
                upscaler_id=sim_input.upscaler_id,
                frame_gen_id="off",
                settings=sim_input.settings,
            )
            res = simulate(laptop_input, gpu_override=gpu)
        else:
            res = simulate(sim_input, gpu_override=gpu)

        entries.append(
            GPUComparisonEntry(
                gpu_id=gpu.id,
                label=gpu.short_name,
                base_fps=res.base_fps,
                low_1pct_fps=res.low_1pct_fps,
                is_selected=(gpu.id == sim_input.gpu_id),
                is_reference_console=False,
                has_vram_overflow=(res.vram_overflow_gb > 0),
                notes=gpu.notes,
            )
        )

    for console in CONSOLE_REFERENCES:
        console_cpu = CPUProfile(
            id=f"{console.id}_cpu",
            name="Console Zen 2",
            gaming_score=58.0 if console.id == "ps5_ref" else 63.0,
            cores_threads="8C / 16T",
            architecture_notes="Custom AMD Zen 2 Console APU",
            socket_hint="Console",
        )
        console_input = SimulationInput(
            gpu_id=console.id,
            cpu_id="ryzen_5600x",
            ram_gb=16,
            ram_speed_id="ddr5_5600",
            rebar_enabled=True,
            gpu_oc_percent=0,
            storage_type="NVMe Gen4",
            is_laptop_mode=False,
            resolution_id=sim_input.resolution_id,
            upscaler_id=sim_input.upscaler_id,
            frame_gen_id="off",
            settings=sim_input.settings,
        )
        res = simulate(console_input, gpu_override=console, cpu_override=console_cpu)
        entries.append(
            GPUComparisonEntry(
                gpu_id=console.id,
                label=console.short_name,
                base_fps=res.base_fps,
                low_1pct_fps=res.low_1pct_fps,
                is_selected=False,
                is_reference_console=True,
                has_vram_overflow=(res.vram_overflow_gb > 0),
                notes=console.notes,
            )
        )

    entries.sort(key=lambda item: item.base_fps, reverse=True)
    return entries


_VRAM_PRIORITY: tuple[str, ...] = (
    "vehicle_textures",
    "texture_quality",
    "rt_shadows",
    "rtgi",
    "reflections",
    "bvh_quality",
    "lod_scale",
    "volumetrics",
)

_CPU_PRIORITY: tuple[str, ...] = (
    "ped_vehicle_density",
    "ai_physics",
    "bvh_quality",
    "rt_shadows",
    "lod_scale",
    "trees_terrain_grass",
    "hair_quality",
    "water_tessellation",
)

_GPU_PRIORITY: tuple[str, ...] = (
    "rt_shadows",
    "reflections",
    "volumetrics",
    "rtgi",
    "trees_terrain_grass",
    "lod_scale",
    "raster_shadows",
    "hair_quality",
    "water_tessellation",
    "bvh_quality",
)

_UPSCALER_STEP_ORDER: tuple[str, ...] = ("native_aa", "native", "quality", "balanced")


def _step_down_setting(settings_map: dict[str, str], setting_id: str) -> str | None:
    """Lower one setting by one quality tier; return new label or None if already minimum."""
    definition = SETTING_BY_ID[setting_id]
    current = settings_map.get(setting_id, definition.default_option)
    labels = definition.option_labels()
    if current not in labels:
        return None
    idx = labels.index(current)
    if idx <= 0:
        return None
    new_label = labels[idx - 1]
    settings_map[setting_id] = new_label
    return new_label


def auto_optimize_for_60_fps(sim_input: SimulationInput, target_fps: float = 60.0) -> AutoOptimizeResult:
    """Intelligently lower only settings causing the active bottleneck toward 60 Base FPS."""
    working_settings = dict(sim_input.settings)
    working_upscaler = sim_input.upscaler_id
    changed: list[str] = []

    def _current_sim() -> SimulationResult:
        return simulate(
            SimulationInput(
                gpu_id=sim_input.gpu_id,
                cpu_id=sim_input.cpu_id,
                ram_gb=sim_input.ram_gb,
                ram_speed_id=sim_input.ram_speed_id,
                rebar_enabled=sim_input.rebar_enabled,
                gpu_oc_percent=sim_input.gpu_oc_percent,
                storage_type=sim_input.storage_type,
                is_laptop_mode=sim_input.is_laptop_mode,
                resolution_id=sim_input.resolution_id,
                upscaler_id=working_upscaler,
                frame_gen_id=sim_input.frame_gen_id,
                settings=working_settings,
            )
        )

    res = _current_sim()

    # Step 1: Clear VRAM or RAM/Unified overflow first.
    for _ in range(24):
        if res.vram_overflow_gb <= 0 and res.ram_overflow_gb <= 0:
            break
        order = (
            ("ped_vehicle_density",) + _VRAM_PRIORITY
            if res.ram_overflow_gb > 0
            else _VRAM_PRIORITY
        )
        progressed = False
        for sid in order:
            old_val = working_settings.get(sid, SETTING_BY_ID[sid].default_option)
            new_val = _step_down_setting(working_settings, sid)
            if new_val is not None:
                changed.append(f"{SETTING_BY_ID[sid].name}: {old_val} -> {new_val}")
                progressed = True
                break
        if not progressed:
            break
        res = _current_sim()

    # Step 2: Iteratively trim settings targeting whichever ceiling is limiting FPS.
    for _ in range(40):
        if res.base_fps >= target_fps:
            break
        if res.raw_cpu_fps <= res.raw_gpu_fps * 1.05:
            priority = _CPU_PRIORITY
        else:
            priority = _GPU_PRIORITY

        progressed = False
        for sid in priority:
            old_val = working_settings.get(sid, SETTING_BY_ID[sid].default_option)
            new_val = _step_down_setting(working_settings, sid)
            if new_val is not None:
                changed.append(f"{SETTING_BY_ID[sid].name}: {old_val} -> {new_val}")
                progressed = True
                break
        if not progressed:
            break
        res = _current_sim()

    # Step 3: If GPU is still capping below 60 FPS, step Upscaler up to Balanced (never touch Res/FG).
    while res.base_fps < target_fps and res.raw_gpu_fps < res.raw_cpu_fps * 1.15:
        if working_upscaler in ("balanced", "performance"):
            break
        if working_upscaler in ("native", "native_aa"):
            next_upscaler = "quality"
        elif working_upscaler == "quality":
            next_upscaler = "balanced"
        else:
            break
        changed.append(
            f"Upscaler: {UPSCALER_BY_ID[working_upscaler].generic_label} -> "
            f"{UPSCALER_BY_ID[next_upscaler].generic_label}"
        )
        working_upscaler = next_upscaler
        res = _current_sim()

    reached = res.base_fps >= target_fps
    if not changed and reached:
        summary_en = f"Already achieving {res.base_fps:.1f} Base FPS — no downgrades needed."
        summary_fa = f"در حال حاضر به {res.base_fps:.1f} فریم پایه رسیده‌اید؛ نیازی به کاهش تنظیمات نیست."
    elif reached:
        summary_en = (
            f"Reached {res.base_fps:.1f} Base FPS with {len(changed)} targeted adjustment(s)."
        )
        summary_fa = (
            f"با {len(changed)} تغییر هدفمند روی گلوگاه اصلی به {res.base_fps:.1f} فریم پایه رسیدید."
        )
    else:
        summary_en = (
            f"Maximized to {res.base_fps:.1f} Base FPS ({len(changed)} adjustment(s)); "
            f"hardware/resolution cap prevents 60 Base FPS without lowering Resolution or enabling FG."
        )
        summary_fa = (
            f"بیشینه فریم به {res.base_fps:.1f} فریم پایه رسید ({len(changed)} تغییر)؛ "
            "سقف سخت‌افزار/رزولوشن اجازه ۶۰ فریم پایه بدون کاهش رزولوشن یا Frame Gen را نمی‌دهد."
        )

    return AutoOptimizeResult(
        settings=working_settings,
        upscaler_id=working_upscaler,
        changed_items=tuple(changed),
        reached_target=reached,
        resulting_base_fps=res.base_fps,
        summary_en=summary_en,
        summary_fa=summary_fa,
    )
