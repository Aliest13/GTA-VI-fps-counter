"""Calibration and behavioral tests for engine.predictor."""

from __future__ import annotations

from dataclasses import replace

import pytest

from data.settings_db import (
    SETTINGS,
    SETTINGS_PRESET_BY_ID,
    UPSCALER_BY_ID,
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


def test_calibration_desktop_1440p_xess_quality_ps5() -> None:
    """13400F + Arc B580 (ReBAR ON) + 32GB DDR5-4800 | 1440p XeSS Quality | PS5 Settings."""
    sim_input = SimulationInput(
        gpu_id="arc_b580",
        cpu_id="i5_13400f",
        ram_gb=32,
        ram_speed_id="ddr5_4800",
        rebar_enabled=True,
        gpu_oc_percent=0,
        storage_type="NVMe Gen4",
        is_laptop_mode=False,
        resolution_id="1440p",
        upscaler_id="quality",
        frame_gen_id="off",
        settings=SETTINGS_PRESET_BY_ID["ps5_xsx"].values,
    )
    res = simulate(sim_input)
    assert 48.0 <= res.base_fps <= 58.0
    assert 36.0 <= res.low_1pct_fps <= 42.0
    assert res.vram_overflow_gb == 0.0


def test_calibration_desktop_900p_native_aa_sweet_spot() -> None:
    """13400F + Arc B580 (ReBAR ON) + 32GB DDR5-4800 | 900p Native AA | Sweet Spot."""
    sweet = SETTINGS_PRESET_BY_ID["sweet_spot_900p"]
    sim_input = SimulationInput(
        gpu_id="arc_b580",
        cpu_id="i5_13400f",
        ram_gb=32,
        ram_speed_id="ddr5_4800",
        rebar_enabled=True,
        gpu_oc_percent=0,
        storage_type="NVMe Gen4",
        is_laptop_mode=False,
        resolution_id=sweet.resolution_id or "900p",
        upscaler_id=sweet.upscaler_id or "native_aa",
        frame_gen_id="off",
        settings=sweet.values,
    )
    res = simulate(sim_input)
    assert 48.0 <= res.base_fps <= 58.0
    assert 38.0 <= res.low_1pct_fps <= 44.0


def test_calibration_rtx4060_1440p_ultra_vram_overflow() -> None:
    """13400F + RTX 4060 (8GB) + 32GB DDR5-4800 | 1440p | All Ultra -> 8GB VRAM Overflow."""
    sim_input = SimulationInput(
        gpu_id="rtx_4060",
        cpu_id="i5_13400f",
        ram_gb=32,
        ram_speed_id="ddr5_4800",
        rebar_enabled=True,
        gpu_oc_percent=0,
        storage_type="NVMe Gen4",
        is_laptop_mode=False,
        resolution_id="1440p",
        upscaler_id="native",
        frame_gen_id="off",
        settings=SETTINGS_PRESET_BY_ID["all_ultra"].values,
    )
    res = simulate(sim_input)
    assert res.vram_overflow_gb > 2.0
    assert res.primary_bottleneck == "VRAM Overflow"
    assert res.low_1pct_fps < 15.0
    assert any(w.code == "vram_overflow" for w in res.warnings)


def test_calibration_9800x3d_5090_4k_dlss_quality_ultra_mfg4x() -> None:
    """9800X3D + RTX 5090 + 32GB DDR5-6000 | 4K DLSS Quality | All Ultra -> ~75-90 Base, 200+ MFG 4x."""
    sim_input = SimulationInput(
        gpu_id="rtx_5090",
        cpu_id="ryzen_9800x3d",
        ram_gb=32,
        ram_speed_id="ddr5_6000",
        rebar_enabled=True,
        gpu_oc_percent=0,
        storage_type="NVMe Gen4",
        is_laptop_mode=False,
        resolution_id="4k",
        upscaler_id="quality",
        frame_gen_id="4x",
        settings=SETTINGS_PRESET_BY_ID["all_ultra"].values,
    )
    res = simulate(sim_input)
    assert 75.0 <= res.base_fps <= 90.0
    assert res.effective_fg_id == "4x"
    assert res.fg_fps >= 200.0


def test_calibration_laptop_arc140v_series_s_vs_1080p_medium() -> None:
    """Laptop (Ultra 7 256V + Arc 140V + 16GB Shared) | 720p Series S vs 1080p Medium."""
    series_s_input = SimulationInput(
        gpu_id="arc_140v",
        cpu_id="ultra_7_256v",
        ram_gb=16,
        ram_speed_id="lpddr5x_8533",
        rebar_enabled=True,
        gpu_oc_percent=0,
        storage_type="NVMe Gen4",
        is_laptop_mode=True,
        resolution_id="720p",
        upscaler_id="native",
        frame_gen_id="off",
        settings=SETTINGS_PRESET_BY_ID["series_s"].values,
    )
    res_720 = simulate(series_s_input)
    assert 24.0 <= res_720.base_fps <= 32.0
    assert res_720.is_unified_pool is True
    assert res_720.vram_overflow_gb == 0.0

    # 1080p Medium textures/RTGI/volumetrics on 16GB shared pool -> 12-18 FPS + Unified Overflow Warning
    medium_settings = default_settings_map()
    medium_settings["texture_quality"] = "Medium"
    medium_settings["volumetrics"] = "Medium"
    medium_settings["ped_vehicle_density"] = "High"
    input_1080 = SimulationInput(
        gpu_id="arc_140v",
        cpu_id="ultra_7_256v",
        ram_gb=16,
        ram_speed_id="lpddr5x_8533",
        rebar_enabled=True,
        gpu_oc_percent=0,
        storage_type="NVMe Gen4",
        is_laptop_mode=True,
        resolution_id="1080p",
        upscaler_id="native",
        frame_gen_id="off",
        settings=medium_settings,
    )
    res_1080 = simulate(input_1080)
    assert 12.0 <= res_1080.base_fps <= 18.0
    assert res_1080.vram_overflow_gb > 0.0
    assert any(w.code == "unified_overflow" for w in res_1080.warnings)


def test_arc_b580_rebar_off_penalty_and_xess3_mfg() -> None:
    """Arc B580 supports XeSS 3 4x MFG, falls back 6x -> 4x, and penalizes ReBAR OFF."""
    base_input = SimulationInput(
        gpu_id="arc_b580",
        cpu_id="i5_13400f",
        ram_gb=32,
        ram_speed_id="ddr5_4800",
        rebar_enabled=True,
        gpu_oc_percent=0,
        storage_type="NVMe Gen4",
        is_laptop_mode=False,
        resolution_id="1080p",
        upscaler_id="quality",
        frame_gen_id="4x",
        settings=default_settings_map(),
    )
    res_on = simulate(base_input)
    res_off = simulate(replace(base_input, rebar_enabled=False))
    assert res_on.effective_fg_id == "4x"
    assert res_on.fg_fallback_note is None
    assert res_on.fg_fps == pytest.approx(res_on.base_fps * 3.00, abs=0.3)
    assert res_off.raw_cpu_fps < res_on.raw_cpu_fps * 0.85
    assert any(w.code == "arc_no_rebar" for w in res_off.warnings)

    res_6x = simulate(replace(base_input, frame_gen_id="6x"))
    assert res_6x.effective_fg_id == "4x"
    assert res_6x.fg_fallback_note is not None

    res_4060 = simulate(replace(base_input, gpu_id="rtx_4060", frame_gen_id="4x"))
    assert res_4060.effective_fg_id == "2x"
    assert res_4060.fg_fallback_note is not None


def test_auto_optimize_targets_60_fps_smartly() -> None:
    """Auto-Optimize relieves the CPU bottleneck on 13400F + B580 to achieve 60 Base FPS."""
    sim_input = SimulationInput(
        gpu_id="arc_b580",
        cpu_id="i5_13400f",
        ram_gb=32,
        ram_speed_id="ddr5_4800",
        rebar_enabled=True,
        gpu_oc_percent=0,
        storage_type="NVMe Gen4",
        is_laptop_mode=False,
        resolution_id="1440p",
        upscaler_id="quality",
        frame_gen_id="off",
        settings=default_settings_map(),
    )
    initial = simulate(sim_input)
    assert initial.base_fps < 60.0

    opt = auto_optimize_for_60_fps(sim_input, target_fps=60.0)
    assert opt.reached_target is True
    assert opt.resulting_base_fps >= 60.0
    assert opt.settings["ped_vehicle_density"] != "High"
    assert opt.upscaler_id == "quality"


def test_compare_all_gpus_includes_all_gpus_and_consoles() -> None:
    """Multi-GPU chart returns 9 GPUs plus PS5 and PS5 Pro with realistic Zen 2 CPU caps."""
    sim_input = SimulationInput(
        gpu_id="arc_b580",
        cpu_id="i5_13400f",
        ram_gb=32,
        ram_speed_id="ddr5_4800",
        rebar_enabled=True,
        gpu_oc_percent=0,
        storage_type="NVMe Gen4",
        is_laptop_mode=False,
        resolution_id="1440p",
        upscaler_id="quality",
        frame_gen_id="off",
        settings=default_settings_map(),
    )
    entries = compare_all_gpus(sim_input)
    assert len(entries) == 11
    assert sum(1 for e in entries if e.is_selected) == 1
    assert sum(1 for e in entries if e.is_reference_console) == 2

    by_id = {e.gpu_id: e for e in entries}
    assert 30.0 <= by_id["ps5_ref"].base_fps <= 38.0
    assert 34.0 <= by_id["ps5_pro_ref"].base_fps <= 40.0

    pro_entries = compare_all_gpus(
        replace(sim_input, settings=SETTINGS_PRESET_BY_ID["ps5_pro"].values)
    )
    pro_by_id = {e.gpu_id: e for e in pro_entries}
    assert 30.0 <= pro_by_id["ps5_ref"].base_fps <= 38.0
    assert 30.0 <= pro_by_id["ps5_pro_ref"].base_fps <= 39.0


def test_laptop_720p_xess_balanced_floor_and_cpu_ceiling() -> None:
    """720p XeSS Balanced clamps res factor >= 0.26 and 256V CPU caps ~40-44 FPS."""
    laptop_input = SimulationInput(
        gpu_id="arc_140v",
        cpu_id="ultra_7_256v",
        ram_gb=16,
        ram_speed_id="lpddr5x_8533",
        rebar_enabled=True,
        gpu_oc_percent=0,
        storage_type="NVMe Gen4",
        is_laptop_mode=True,
        resolution_id="720p",
        upscaler_id="balanced",
        frame_gen_id="off",
        settings=default_settings_map(),
    )
    base_res = simulate(laptop_input)
    assert base_res.effective_res_factor == 0.26

    perf_res = simulate(replace(laptop_input, upscaler_id="performance"))
    assert perf_res.effective_res_factor == 0.26

    opt = auto_optimize_for_60_fps(laptop_input, target_fps=60.0)
    assert opt.reached_target is False
    assert opt.resulting_base_fps <= 44.0

    opt_res = simulate(replace(laptop_input, settings=opt.settings, upscaler_id=opt.upscaler_id))
    assert 38.0 <= opt_res.raw_cpu_fps <= 44.5


def test_13400f_minimum_cpu_settings_ceiling_stays_above_65_fps() -> None:
    """Raising CPU cost floor to 0.70 still lets 13400F hit 65-75+ FPS when tuned."""
    min_settings = {s.id: s.options[0].label for s in SETTINGS}
    sim_input = SimulationInput(
        gpu_id="arc_b580",
        cpu_id="i5_13400f",
        ram_gb=32,
        ram_speed_id="ddr5_4800",
        rebar_enabled=True,
        gpu_oc_percent=0,
        storage_type="NVMe Gen4",
        is_laptop_mode=False,
        resolution_id="1440p",
        upscaler_id="quality",
        frame_gen_id="off",
        settings=min_settings,
    )
    res = simulate(sim_input)
    assert 65.0 <= res.raw_cpu_fps <= 85.0
    assert res.base_fps >= 65.0


def test_calibration_all_ultra_4k_dlaa_16gb_ram_overflow_and_export() -> None:
    """4K DLAA + All Ultra hits ~16.0-16.5 GB VRAM and ~17.7 GB RAM, triggering 16GB RAM overflow."""
    sim_input = SimulationInput(
        gpu_id="rtx_5090",
        cpu_id="ryzen_9800x3d",
        ram_gb=16,
        ram_speed_id="ddr5_6000",
        rebar_enabled=True,
        gpu_oc_percent=0,
        storage_type="NVMe Gen4",
        is_laptop_mode=False,
        resolution_id="4k",
        upscaler_id="native_aa",
        frame_gen_id="off",
        settings=SETTINGS_PRESET_BY_ID["all_ultra"].values,
    )
    res = simulate(sim_input)
    assert 15.8 <= res.vram_used_gb <= 16.5
    assert 17.3 <= res.ram_used_gb <= 18.0
    assert res.ram_overflow_gb > 1.5
    assert res.primary_bottleneck == "RAM / Unified Overflow"
    assert any(w.code == "ram_overflow" for w in res.warnings)

    res_fg = simulate(replace(sim_input, frame_gen_id="2x"))
    assert 16.0 <= res_fg.vram_used_gb <= 16.6

    md = export_simulation_markdown(sim_input)
    assert "System RAM Overflow" in md
    assert "17.7 / 16 GB (+1.7 GB SWAP)" in md


def test_vendor_upscaler_presets_and_multipliers() -> None:
    """Verify 8 vendor-specific upscaler presets, XeSS shifted scales, and fallback rules."""
    base_1440p = SimulationInput(
        gpu_id="arc_b580",
        cpu_id="i5_13400f",
        ram_gb=32,
        ram_speed_id="ddr5_4800",
        rebar_enabled=True,
        gpu_oc_percent=0,
        storage_type="NVMe Gen4",
        is_laptop_mode=False,
        resolution_id="1440p",
        upscaler_id="ultra_quality_plus",
        frame_gen_id="off",
        settings=default_settings_map(),
    )
    # Intel XeSS 3 scale factors
    assert simulate(base_1440p).effective_res_factor == 0.68
    assert simulate(replace(base_1440p, upscaler_id="ultra_quality")).effective_res_factor == 0.55
    assert simulate(replace(base_1440p, upscaler_id="quality")).effective_res_factor == 0.45
    assert simulate(replace(base_1440p, upscaler_id="balanced")).effective_res_factor == 0.37
    assert simulate(replace(base_1440p, upscaler_id="performance")).effective_res_factor == 0.30
    assert simulate(replace(base_1440p, upscaler_id="ultra_performance")).effective_res_factor == 0.26

    # AMD FSR scale factors (Ultra Quality = 1.3x / 0.68)
    amd_1440p = replace(base_1440p, gpu_id="rx_9070_xt")
    assert simulate(replace(amd_1440p, upscaler_id="ultra_quality")).effective_res_factor == 0.68
    assert simulate(replace(amd_1440p, upscaler_id="quality")).effective_res_factor == 0.55
    assert simulate(replace(amd_1440p, upscaler_id="balanced")).effective_res_factor == 0.45
    assert simulate(replace(amd_1440p, upscaler_id="performance")).effective_res_factor == 0.37

    # NVIDIA DLSS availability & fallback resolution
    assert UPSCALER_BY_ID["ultra_quality_plus"].is_supported_by("Intel") is True
    assert UPSCALER_BY_ID["ultra_quality_plus"].is_supported_by("AMD") is False
    assert UPSCALER_BY_ID["ultra_quality_plus"].is_supported_by("NVIDIA") is False
    assert UPSCALER_BY_ID["ultra_quality"].is_supported_by("AMD") is True
    assert UPSCALER_BY_ID["ultra_quality"].is_supported_by("NVIDIA") is False
    assert resolve_upscaler_for_vendor("ultra_quality_plus", "AMD") == "ultra_quality"
    assert resolve_upscaler_for_vendor("ultra_quality_plus", "NVIDIA") == "quality"
    assert resolve_upscaler_for_vendor("ultra_quality", "NVIDIA") == "quality"

    # 900p Sweet Spot keeps 900p + Native AA
    sweet = SETTINGS_PRESET_BY_ID["sweet_spot_900p"]
    assert sweet.resolution_id == "900p"
    assert sweet.upscaler_id == "native_aa"


def test_rtx5090_dlss45_6x_mfg_and_dlss5_neural_rendering_cost() -> None:
    """RTX 5090 supports 6x MFG (3.95x) and DLSS 5 (1.38x GPU tax, +1.3GB VRAM); non-50 GPUs lock DLSS 5."""
    base_5090 = SimulationInput(
        gpu_id="rtx_5090",
        cpu_id="ryzen_9800x3d",
        ram_gb=32,
        ram_speed_id="ddr5_6000",
        rebar_enabled=True,
        gpu_oc_percent=0,
        storage_type="NVMe Gen4",
        is_laptop_mode=False,
        resolution_id="4k",
        upscaler_id="quality",
        frame_gen_id="6x",
        settings=SETTINGS_PRESET_BY_ID["all_ultra"].values,
        dlss5_enabled=False,
    )
    res_off = simulate(base_5090)
    res_on = simulate(replace(base_5090, dlss5_enabled=True))

    assert res_off.effective_fg_id == "6x"
    assert res_off.fg_fps == pytest.approx(res_off.base_fps * 3.95, abs=0.4)
    assert res_off.effective_dlss5 is False

    assert res_on.effective_dlss5 is True
    assert round(res_on.vram_used_gb - res_off.vram_used_gb, 2) == 1.3
    ratio = res_on.raw_gpu_fps / res_off.raw_gpu_fps
    assert 0.70 <= ratio <= 0.75
    assert "DLSS 5 Neural Rendering trades ~28% GPU FPS + 1.3 GB VRAM" in res_on.diagnosis_en

    md_dlss5 = export_simulation_markdown(replace(base_5090, dlss5_enabled=True))
    assert "| **DLSS 5 Neural Rendering** | On (3D-Guided) |" in md_dlss5
    assert "DLSS Quality (1.5x)" in md_dlss5

    # Non-RTX 50 GPU cannot enable DLSS 5
    non50_base = replace(base_5090, gpu_id="rtx_4060", frame_gen_id="off", resolution_id="1440p")
    assert simulate(replace(non50_base, dlss5_enabled=True)) == simulate(non50_base)


def test_export_simulation_markdown_contains_all_sections() -> None:
    """Markdown report includes hardware, telemetry, warnings, Tex2 settings, and GPU table."""
    sim_input = SimulationInput(
        gpu_id="rtx_4060",
        cpu_id="i5_13400f",
        ram_gb=32,
        ram_speed_id="ddr5_4800",
        rebar_enabled=True,
        gpu_oc_percent=3,
        storage_type="NVMe Gen4",
        is_laptop_mode=False,
        resolution_id="1440p",
        upscaler_id="quality",
        frame_gen_id="2x",
        settings=SETTINGS_PRESET_BY_ID["all_ultra"].values,
    )
    md = export_simulation_markdown(sim_input)
    assert "# GTA VI Hardware & FPS Simulation Report" in md
    assert "RTX 4060 (8GB)" in md
    assert "Core i5-13400F" in md
    assert "+3%" in md
    assert "DLSS Quality (1.5x)" in md
    assert "| **DLSS 5 Neural Rendering** | Off |" in md
    assert "### Active Warnings" in md
    assert "Global Illumination (RTGI)" in md
    assert "★ RTX 4060 8G" in md
    assert "PS5 (Ref)" in md
