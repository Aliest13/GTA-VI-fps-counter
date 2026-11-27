# GTA VI Hardware & FPS Simulation Report

*Generated: 2026-11-27 13:30 Iran Standard Time*

## 1. System Hardware

| Component | Configuration |
| :--- | :--- |
| **Form Factor** | Desktop Tower |
| **GPU** | RTX 5090 — 32 GB (1792 GB/s, PCIe x16) |
| **CPU** | Ryzen 7 9800X3D (8C / 16T, Sim Score 112) |
| **RAM** | 16 GB DDR5-6000 CL30 |
| **Resizable BAR** | ON |
| **GPU Overclock** | +0% |
| **Storage** | NVMe Gen4 |

## 2. Display & Frame Generation

| Option | Setting |
| :--- | :--- |
| **Output Resolution** | 4K |
| **Upscaler** | DLAA (1.0x) (2.00x effective scale) |
| **Frame Generation** | Off |
| **DLSS 5 Neural Rendering** | Off |

## 3. Live Telemetry & Bottleneck Radar

| Metric | Value |
| :--- | :--- |
| **Average Base FPS** | **51.2 FPS** (GPU Ceiling 53.1 / CPU Ceiling 53.7) |
| **1% Low FPS (City/Chaos)** | **16.4 FPS** |
| **With Frame Generation** | Off |
| **Core Loads** | GPU 95% • RT 100% • CPU 91% |
| **VRAM Footprint** | 15.9 / 32 GB (50%) |
| **System RAM Footprint** | 17.7 / 16 GB (+1.7 GB SWAP) |
| **Primary Bottleneck** | **RAM / Unified Overflow** |

> **Diagnosis:** System RAM Overflow: 1.7 GB beyond physical RAM forces Windows disk paging during streaming.
>
> **Recommendation:** Drop Pedestrian & Vehicle Density to Medium/Low and close background browsers.

### Active Warnings

- **[CRITICAL] System RAM Overflow (+1.7 GB):** 17.7 GB required on 16 GB RAM — Windows pagefile swapping cuts 1% Lows dramatically.

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
| ★ RTX 5090 | 51.2 | 16.4 | OK |
| RTX 5070 Ti | 32.0 | 10.1 | OVERFLOW |
| RX 9070 XT | 29.4 | 9.3 | OVERFLOW |
| RX 6900 XT | 19.3 | 6.1 | OVERFLOW |
| 9060 XT 16G | 17.4 | 5.5 | OVERFLOW |
| PS5 Pro (Ref) | 13.6 | 1.3 | OVERFLOW |
| 9060 XT 8G | 5.4 | 1.0 | OVERFLOW |
| Arc B580 | 4.9 | 1.0 | OVERFLOW |
| RTX 4060 8G | 4.3 | 1.0 | OVERFLOW |
| PS5 (Ref) | 4.2 | 1.0 | OVERFLOW |
| Arc 140V (LP) | 1.6 | 1.0 | OVERFLOW |
