# GTA VI Hardware & FPS Simulation Report

*Generated: 2026-11-27 13:30 Iran Standard Time*

## 1. System Hardware

| Component | Configuration |
| :--- | :--- |
| **Form Factor** | Desktop Tower |
| **GPU** | RTX 4060 (8GB) — 8 GB (272 GB/s, PCIe x8) |
| **CPU** | Core i5-13400F (10C (6P+4E) / 16T, Sim Score 73) |
| **RAM** | 32 GB DDR5-4800 (H610 Cap) |
| **Resizable BAR** | ON |
| **GPU Overclock** | +3% |
| **Storage** | NVMe Gen4 |

## 2. Display & Frame Generation

| Option | Setting |
| :--- | :--- |
| **Output Resolution** | 1440p |
| **Upscaler** | DLSS Quality (1.5x) (0.55x effective scale) |
| **Frame Generation** | 2x FG |
| **DLSS 5 Neural Rendering** | Off |

## 3. Live Telemetry & Bottleneck Radar

| Metric | Value |
| :--- | :--- |
| **Average Base FPS** | **16.1 FPS** (GPU Ceiling 16.1 / CPU Ceiling 46.6) |
| **1% Low FPS (City/Chaos)** | **2.8 FPS** |
| **With Frame Generation** | **27.7 FPS** (2x FG) |
| **Core Loads** | GPU 99% • RT 100% • CPU 33% |
| **VRAM Footprint** | 15.3 / 8 GB (+7.6 GB SPILL) |
| **System RAM Footprint** | 17.7 / 32 GB (55%) |
| **Primary Bottleneck** | **VRAM Overflow** |

> **Diagnosis:** VRAM Spillover Bottleneck: GTA VI requests 15.3 GB on RTX 4060 (8GB)'s 8 GB buffer (+7.6 GB spill over x8).
>
> **Recommendation:** Drop Texture Quality to High/Medium, Vehicle HD Count to High, or disable RT Shadows to keep allocation under the VRAM cap.

### Active Warnings

- **[CRITICAL] 8GB VRAM Overflow (+7.6 GB):** Requested 15.3 GB exceeds 8 GB VRAM, spilling into system RAM over PCIe x8! Severe 1% Low collapse.
- **[WARNING] High Input Latency / Artifacts Risk (Base FPS < 38):** Base FPS is 16.1; enabling Frame Generation below 38 FPS causes sluggish controls and HUD/motion artifacts.

## 4. Tex2 Graphics Settings

| Category | Setting | Selected | Primary Load |
| :--- | :--- | :--- | :--- |
| Lighting & RT | Global Illumination (RTGI) | **Ultra** | RT, VRAM |
| Lighting & RT | Ray-Traced Shadows (Dir + Local + LOD) | **High** | RT, CPU, VRAM |
| Lighting & RT | Reflection Quality | **High** | RT, GPU, VRAM |
| Lighting & RT | BVH Quality | **Ultra** | CPU, RT, VRAM |
| Lighting & RT | Directional & Local Raster Shadows | **Ultra** | GPU, VRAM |
| Textures & World | Texture Quality | **Ultra** | VRAM, GPU |
| Textures & World | Vehicle Max Texture & HD Count | **Ultra** | VRAM |
| Textures & World | Trees / Terrain / Grass & Alpha Shadows | **High** | GPU, CPU, VRAM |
| Textures & World | LOD Scale | **1.2** | CPU, GPU, VRAM |
| Water | Water & Tessellation Quality | **Ultra** | GPU, VRAM |
| Volumetrics & Particles | Volumetrics Lighting & Scattering | **Ultra** | GPU, VRAM |
| Hair | Hair Quality & Simulation | **Ultra** | GPU, CPU, VRAM |
| Population / AI / Physics | Pedestrian & Vehicle Density | **Ultra** | CPU, RAM, VRAM |
| Population / AI / Physics | AI Behavior / Motion / Physics Quality | **Ultra** | CPU |

## 5. Multi-GPU Comparison (Current CPU / RAM / Settings)

| GPU / Console Reference | Base Avg FPS | 1% Low FPS | VRAM Status |
| :--- | ---: | ---: | :--- |
| RX 9070 XT | 47.0 | 35.3 | OK |
| RX 6900 XT | 47.0 | 35.3 | OK |
| 9060 XT 16G | 47.0 | 35.3 | OK |
| RTX 5090 | 46.6 | 35.0 | OK |
| RTX 5070 Ti | 46.6 | 35.0 | OK |
| Arc B580 | 22.6 | 3.9 | OVERFLOW |
| PS5 Pro (Ref) | 20.7 | 4.3 | OVERFLOW |
| 9060 XT 8G | 20.4 | 3.5 | OVERFLOW |
| PS5 (Ref) | 18.8 | 1.2 | OVERFLOW |
| ★ RTX 4060 8G | 16.1 | 2.8 | OVERFLOW |
| Arc 140V (LP) | 7.0 | 1.8 | OVERFLOW |
