"""Hardware profiles database for the GTA VI Hardware & FPS Simulator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

VendorType = Literal["NVIDIA", "AMD", "Intel", "Console"]
PCIeType = Literal["x16", "x8", "Unified"]
DDRGenType = Literal["DDR4", "DDR5", "LPDDR5X"]
StorageType = Literal["NVMe Gen4", "SATA / HDD"]


@dataclass(frozen=True, slots=True)
class GPUProfile:
    """Represents a GPU's raster, ray tracing, memory, and driver characteristics."""

    id: str
    name: str
    short_name: str
    vendor: VendorType
    vram_gb: float
    bandwidth_gbps: float
    raster_score: float
    rt_score: float
    pcie_lanes: PCIeType
    driver_cpu_overhead: float
    driver_cpu_overhead_no_rebar: float
    upscaler_brand: str
    fg_label: str
    supports_fg: bool
    supports_mfg: bool
    notes: str
    max_fg_factor: int = 2
    supports_dlss5: bool = False
    is_unified_memory: bool = False
    is_laptop_thermal: bool = False
    is_reference_console: bool = False


@dataclass(frozen=True, slots=True)
class CPUProfile:
    """Represents a CPU's simulation/gaming capability and platform attributes."""

    id: str
    name: str
    gaming_score: float
    cores_threads: str
    architecture_notes: str
    socket_hint: str
    has_3d_vcache: bool = False
    is_laptop_thermal: bool = False


@dataclass(frozen=True, slots=True)
class RAMSpeedProfile:
    """Represents a memory speed/latency profile and its CPU/1%-low multipliers."""

    id: str
    name: str
    ddr_gen: DDRGenType
    cpu_multiplier: float
    low_1pct_multiplier: float
    notes: str


@dataclass(frozen=True, slots=True)
class HardwarePreset:
    """Quick hardware configuration preset."""

    id: str
    label: str
    gpu_id: str
    cpu_id: str
    ram_gb: int
    ram_speed_id: str
    rebar_enabled: bool
    gpu_oc_percent: int
    storage_type: StorageType
    is_laptop_mode: bool


GPUS: tuple[GPUProfile, ...] = (
    GPUProfile(
        id="rtx_5090",
        name="RTX 5090",
        short_name="RTX 5090",
        vendor="NVIDIA",
        vram_gb=32.0,
        bandwidth_gbps=1792.0,
        raster_score=405.0,
        rt_score=485.0,
        pcie_lanes="x16",
        driver_cpu_overhead=0.02,
        driver_cpu_overhead_no_rebar=0.04,
        upscaler_brand="DLSS",
        fg_label="DLSS 4.5 + MFG (6x)",
        supports_fg=True,
        supports_mfg=True,
        notes="Flagship Blackwell; DLSS 4.5 6x MFG & DLSS 5 Neural Rendering",
        max_fg_factor=6,
        supports_dlss5=True,
    ),
    GPUProfile(
        id="rtx_5070_ti",
        name="RTX 5070 Ti",
        short_name="RTX 5070 Ti",
        vendor="NVIDIA",
        vram_gb=16.0,
        bandwidth_gbps=896.0,
        raster_score=262.0,
        rt_score=295.0,
        pcie_lanes="x16",
        driver_cpu_overhead=0.02,
        driver_cpu_overhead_no_rebar=0.04,
        upscaler_brand="DLSS",
        fg_label="DLSS 4.5 + MFG (6x)",
        supports_fg=True,
        supports_mfg=True,
        notes="Strong RT, DLSS 4.5 6x MFG & DLSS 5 Neural Rendering",
        max_fg_factor=6,
        supports_dlss5=True,
    ),
    GPUProfile(
        id="rx_9070_xt",
        name="RX 9070 XT",
        short_name="RX 9070 XT",
        vendor="AMD",
        vram_gb=16.0,
        bandwidth_gbps=640.0,
        raster_score=265.0,
        rt_score=245.0,
        pcie_lanes="x16",
        driver_cpu_overhead=0.01,
        driver_cpu_overhead_no_rebar=0.04,
        upscaler_brand="FSR",
        fg_label="FSR 4.1 Redstone + FG (2x)",
        supports_fg=True,
        supports_mfg=False,
        notes="Strong RDNA 4 raster & improved RT (FSR Redstone 2x FG)",
        max_fg_factor=2,
    ),
    GPUProfile(
        id="rx_6900_xt",
        name="RX 6900 XT",
        short_name="RX 6900 XT",
        vendor="AMD",
        vram_gb=16.0,
        bandwidth_gbps=512.0,
        raster_score=205.0,
        rt_score=128.0,
        pcie_lanes="x16",
        driver_cpu_overhead=0.01,
        driver_cpu_overhead_no_rebar=0.04,
        upscaler_brand="FSR",
        fg_label="FSR 4.1 (INT8 ML) + FSR FG (2x)",
        supports_fg=True,
        supports_mfg=False,
        notes="High raster, FSR 4.1 (INT8 ML) + FSR FG (2x), weak RDNA 2 RT!",
        max_fg_factor=2,
    ),
    GPUProfile(
        id="rx_9060_xt_16",
        name="RX 9060 XT (16GB)",
        short_name="9060 XT 16G",
        vendor="AMD",
        vram_gb=16.0,
        bandwidth_gbps=320.0,
        raster_score=153.0,
        rt_score=150.0,
        pcie_lanes="x16",
        driver_cpu_overhead=0.01,
        driver_cpu_overhead_no_rebar=0.04,
        upscaler_brand="FSR",
        fg_label="FSR 4.1 Redstone + FG (2x)",
        supports_fg=True,
        supports_mfg=False,
        notes="Safe VRAM headroom (FSR Redstone 2x FG)",
        max_fg_factor=2,
    ),
    GPUProfile(
        id="rx_9060_xt_8",
        name="RX 9060 XT (8GB)",
        short_name="9060 XT 8G",
        vendor="AMD",
        vram_gb=8.0,
        bandwidth_gbps=320.0,
        raster_score=153.0,
        rt_score=150.0,
        pcie_lanes="x16",
        driver_cpu_overhead=0.01,
        driver_cpu_overhead_no_rebar=0.04,
        upscaler_brand="FSR",
        fg_label="FSR 4.1 Redstone + FG (2x)",
        supports_fg=True,
        supports_mfg=False,
        notes="Vulnerable to 8GB VRAM overflow (FSR Redstone 2x FG)",
        max_fg_factor=2,
    ),
    GPUProfile(
        id="arc_b580",
        name="Intel Arc B580",
        short_name="Arc B580",
        vendor="Intel",
        vram_gb=12.0,
        bandwidth_gbps=456.0,
        raster_score=135.0,
        rt_score=140.0,
        pcie_lanes="x8",
        driver_cpu_overhead=0.07,
        driver_cpu_overhead_no_rebar=0.28,
        upscaler_brand="XeSS",
        fg_label="XeSS 3 MFG (4x)",
        supports_fg=True,
        supports_mfg=True,
        notes="Sensitive to ReBAR & VRAM spillover over x8; supports XeSS 3 4x MFG",
        max_fg_factor=4,
    ),
    GPUProfile(
        id="rtx_4060",
        name="RTX 4060 (8GB)",
        short_name="RTX 4060 8G",
        vendor="NVIDIA",
        vram_gb=8.0,
        bandwidth_gbps=272.0,
        raster_score=115.0,
        rt_score=125.0,
        pcie_lanes="x8",
        driver_cpu_overhead=0.02,
        driver_cpu_overhead_no_rebar=0.05,
        upscaler_brand="DLSS",
        fg_label="DLSS 3/4 FG (2x)",
        supports_fg=True,
        supports_mfg=False,
        notes="8GB VRAM limit hits hard in GTA VI (2x FG max)",
        max_fg_factor=2,
    ),
    GPUProfile(
        id="arc_140v",
        name="Laptop: Arc 140V (Lunar Lake iGPU)",
        short_name="Arc 140V (LP)",
        vendor="Intel",
        vram_gb=16.0,
        bandwidth_gbps=136.0,
        raster_score=34.0,
        rt_score=30.0,
        pcie_lanes="Unified",
        driver_cpu_overhead=0.06,
        driver_cpu_overhead_no_rebar=0.14,
        upscaler_brand="XeSS",
        fg_label="XeSS 3 MFG (4x)",
        supports_fg=True,
        supports_mfg=True,
        notes="Coupled 17-25W thermal budget + shared 16GB RAM/VRAM pool (XeSS 3 4x MFG)",
        max_fg_factor=4,
        is_unified_memory=True,
        is_laptop_thermal=True,
    ),
)

CONSOLE_REFERENCES: tuple[GPUProfile, ...] = (
    GPUProfile(
        id="ps5_ref",
        name="PS5 Reference",
        short_name="PS5 (Ref)",
        vendor="Console",
        vram_gb=12.5,
        bandwidth_gbps=448.0,
        raster_score=100.0,
        rt_score=75.0,
        pcie_lanes="Unified",
        driver_cpu_overhead=0.00,
        driver_cpu_overhead_no_rebar=0.00,
        upscaler_brand="FSR",
        fg_label="Console Fixed",
        supports_fg=False,
        supports_mfg=False,
        notes="Base PS5 GPU target reference (Score 100/75, 12.5GB pool)",
        max_fg_factor=1,
        is_reference_console=True,
    ),
    GPUProfile(
        id="ps5_pro_ref",
        name="PS5 Pro Reference",
        short_name="PS5 Pro (Ref)",
        vendor="Console",
        vram_gb=14.0,
        bandwidth_gbps=576.0,
        raster_score=180.0,
        rt_score=175.0,
        pcie_lanes="Unified",
        driver_cpu_overhead=0.00,
        driver_cpu_overhead_no_rebar=0.00,
        upscaler_brand="PSSR",
        fg_label="Console Fixed",
        supports_fg=False,
        supports_mfg=False,
        notes="PS5 Pro GPU target reference (Score 180/175, 14GB pool)",
        max_fg_factor=1,
        is_reference_console=True,
    ),
)

CPUS: tuple[CPUProfile, ...] = (
    CPUProfile(
        id="ryzen_9800x3d",
        name="Ryzen 7 9800X3D",
        gaming_score=112.0,
        cores_threads="8C / 16T",
        architecture_notes="96MB 3D V-Cache; excels in GTA VI AI & BVH",
        socket_hint="AM5",
        has_3d_vcache=True,
    ),
    CPUProfile(
        id="ryzen_7800x3d",
        name="Ryzen 7 7800X3D",
        gaming_score=100.0,
        cores_threads="8C / 16T",
        architecture_notes="96MB 3D V-Cache baseline",
        socket_hint="AM5",
        has_3d_vcache=True,
    ),
    CPUProfile(
        id="i5_14600k",
        name="Core i5-14600K",
        gaming_score=87.0,
        cores_threads="14C (6P+8E) / 20T",
        architecture_notes="Best LGA1700 gaming upgrade",
        socket_hint="LGA1700",
    ),
    CPUProfile(
        id="i7_12700k",
        name="Core i7-12700K",
        gaming_score=82.0,
        cores_threads="12C (8P+4E) / 20T",
        architecture_notes="Strong clocks & P-core count",
        socket_hint="LGA1700",
    ),
    CPUProfile(
        id="ryzen_7600x",
        name="Ryzen 5 7600X",
        gaming_score=80.0,
        cores_threads="6C / 12T",
        architecture_notes="Mainstream AM5",
        socket_hint="AM5",
    ),
    CPUProfile(
        id="i5_13400f",
        name="Core i5-13400F",
        gaming_score=73.0,
        cores_threads="10C (6P+4E) / 16T",
        architecture_notes="DDR5-4800 capped on H610 boards",
        socket_hint="LGA1700",
    ),
    CPUProfile(
        id="ryzen_5600x",
        name="Ryzen 5 5600X",
        gaming_score=65.0,
        cores_threads="6C / 12T",
        architecture_notes="Zen 3 AM4",
        socket_hint="AM4",
    ),
    CPUProfile(
        id="ultra_7_256v",
        name="Laptop: Core Ultra 7 256V",
        gaming_score=48.0,
        cores_threads="8C (4P+4LP-E) / 8T",
        architecture_notes="No HT; shares 17-25W TDP with Arc 140V",
        socket_hint="Mobile",
        is_laptop_thermal=True,
    ),
)

RAM_CAPACITIES_GB: tuple[int, ...] = (16, 32, 64)

RAM_SPEEDS: tuple[RAMSpeedProfile, ...] = (
    RAMSpeedProfile(
        id="ddr5_6000",
        name="DDR5-6000 CL30",
        ddr_gen="DDR5",
        cpu_multiplier=1.02,
        low_1pct_multiplier=1.02,
        notes="Optimal desktop DDR5 bandwidth & latency",
    ),
    RAMSpeedProfile(
        id="ddr5_5600",
        name="DDR5-5600",
        ddr_gen="DDR5",
        cpu_multiplier=0.97,
        low_1pct_multiplier=0.96,
        notes="Solid mid-range DDR5 kit",
    ),
    RAMSpeedProfile(
        id="ddr5_4800",
        name="DDR5-4800 (H610 Cap)",
        ddr_gen="DDR5",
        cpu_multiplier=0.91,
        low_1pct_multiplier=0.87,
        notes="Higher latency reduces city 1% Lows",
    ),
    RAMSpeedProfile(
        id="ddr4_3600",
        name="DDR4-3600",
        ddr_gen="DDR4",
        cpu_multiplier=0.96,
        low_1pct_multiplier=0.95,
        notes="Sweet-spot DDR4 timing",
    ),
    RAMSpeedProfile(
        id="ddr4_3200",
        name="DDR4-3200",
        ddr_gen="DDR4",
        cpu_multiplier=0.91,
        low_1pct_multiplier=0.89,
        notes="Entry DDR4 kit",
    ),
    RAMSpeedProfile(
        id="lpddr5x_8533",
        name="LPDDR5X-8533 (Laptop Shared)",
        ddr_gen="LPDDR5X",
        cpu_multiplier=0.88,
        low_1pct_multiplier=0.85,
        notes="Shared CPU/GPU contention on 136 GB/s bus",
    ),
)

STORAGE_OPTIONS: tuple[StorageType, ...] = ("NVMe Gen4", "SATA / HDD")

HARDWARE_PRESETS: tuple[HardwarePreset, ...] = (
    HardwarePreset(
        id="mid_range_desktop",
        label="Mainstream (7600X + 9060 XT 16G)",
        gpu_id="rx_9060_xt_16",
        cpu_id="ryzen_7600x",
        ram_gb=32,
        ram_speed_id="ddr5_5600",
        rebar_enabled=True,
        gpu_oc_percent=0,
        storage_type="NVMe Gen4",
        is_laptop_mode=False,
    ),
    HardwarePreset(
        id="ultrabook_igpu",
        label="Ultrabook (Ultra 7 256V + Arc 140V)",
        gpu_id="arc_140v",
        cpu_id="ultra_7_256v",
        ram_gb=16,
        ram_speed_id="lpddr5x_8533",
        rebar_enabled=True,
        gpu_oc_percent=0,
        storage_type="NVMe Gen4",
        is_laptop_mode=True,
    ),
    HardwarePreset(
        id="high_end",
        label="High-End (9800X3D + 5090)",
        gpu_id="rtx_5090",
        cpu_id="ryzen_9800x3d",
        ram_gb=32,
        ram_speed_id="ddr5_6000",
        rebar_enabled=True,
        gpu_oc_percent=0,
        storage_type="NVMe Gen4",
        is_laptop_mode=False,
    ),
)

GPU_BY_ID: dict[str, GPUProfile] = {g.id: g for g in GPUS}
CONSOLE_BY_ID: dict[str, GPUProfile] = {c.id: c for c in CONSOLE_REFERENCES}
CPU_BY_ID: dict[str, CPUProfile] = {c.id: c for c in CPUS}
RAM_SPEED_BY_ID: dict[str, RAMSpeedProfile] = {r.id: r for r in RAM_SPEEDS}
PRESET_BY_ID: dict[str, HardwarePreset] = {p.id: p for p in HARDWARE_PRESETS}


def get_platform_compatibility_notes(
    gpu: GPUProfile,
    cpu: CPUProfile,
    ram_speed: RAMSpeedProfile,
    is_laptop_mode: bool,
) -> list[str]:
    """Return informational (non-blocking) hardware pairing hints."""
    notes: list[str] = []
    if cpu.socket_hint == "AM5" and ram_speed.ddr_gen == "DDR4":
        notes.append("Hint: AM5 CPUs require DDR5 memory on real motherboards.")
    elif cpu.socket_hint == "AM4" and ram_speed.ddr_gen != "DDR4":
        notes.append("Hint: AM4 CPUs use DDR4 memory on real motherboards.")
    elif cpu.socket_hint == "LGA1700" and ram_speed.ddr_gen == "LPDDR5X":
        notes.append("Hint: LPDDR5X is soldered mobile memory (Lunar Lake).")

    if is_laptop_mode and (not gpu.is_laptop_thermal or not cpu.is_laptop_thermal):
        notes.append("Laptop thermal throttling (20-25W TDP) is active in Laptop Mode.")
    if gpu.is_unified_memory and ram_speed.ddr_gen != "LPDDR5X":
        notes.append("Hint: Arc 140V relies on on-package LPDDR5X-8533 unified RAM.")
    return notes
