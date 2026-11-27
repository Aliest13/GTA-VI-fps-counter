# GTA VI Hardware & FPS Simulation Report

*Generated: 2026-11-27 14:43 Iran Standard Time*

## 1. System Hardware

| Component | Configuration |
| :--- | :--- |
| **Form Factor** | Gaming Laptop (Dedicated TGP) |
| **GPU** | Laptop: RTX 4050 (6GB) — 6 GB (192 GB/s, PCIe x8) |
| **CPU** | Laptop: Core i5-13450HX (10C (6P+4E) / 16T, Sim Score 72) |
| **RAM** | 16 GB DDR5-4800 (H610 / Mobile HX) |
| **Resizable BAR** | ON |
| **GPU Overclock** | +0% |
| **Storage** | NVMe Gen4 |

## 2. Display & Frame Generation

| Option | Setting |
| :--- | :--- |
| **Output Resolution** | 1080p |
| **Upscaler** | Native (1.0x) (0.62x effective scale) |
| **Frame Generation** | Off |
| **DLSS 5 Neural Rendering** | Off |

## 3. Live Telemetry & Bottleneck Radar

| Metric | Value |
| :--- | :--- |
| **Average Base FPS** | **53.0 FPS** (GPU Ceiling 53.0 / CPU Ceiling 80.8) |
| **1% Low FPS (City/Chaos)** | **45.4 FPS** |
| **With Frame Generation** | Off |
| **Core Loads** | GPU 99% • RT 77% • CPU 63% |
| **VRAM Footprint** | 5.5 / 6 GB (91%) |
| **System RAM Footprint** | 12.1 / 16 GB (76%) |
| **Primary Bottleneck** | **GPU / RT** |

> **Diagnosis:** GPU Bound (Ray Tracing (RTGI / RT Shadows / Reflections)): Laptop: RTX 4050 (6GB) limits output to 53 FPS while Laptop: Core i5-13450HX can feed 81 FPS.
>
> **Recommendation:** Step up Upscaler (Quality/Balanced), or trim RT Shadows, Reflections, and Volumetrics.

### Active Warnings

- **[WARNING] High VRAM Pressure (5.5 / 6 GB):** VRAM usage exceeds 88%; dense downtown scenes may spike textures.

## 4. Tex2 Graphics Settings

| Category | Setting | Selected | Primary Load |
| :--- | :--- | :--- | :--- |
| Lighting & RT | Global Illumination (RTGI) | **Medium** | RT, VRAM |
| Lighting & RT | Ray-Traced Shadows (Dir + Local + LOD) | **Off / None** | RT, CPU, VRAM |
| Lighting & RT | Reflection Quality | **Low** | RT, GPU, VRAM |
| Lighting & RT | BVH Quality | **Medium** | CPU, RT, VRAM |
| Lighting & RT | Directional & Local Raster Shadows | **Medium** | GPU, VRAM |
| Textures & World | Texture Quality | **Medium** | VRAM, GPU |
| Textures & World | Vehicle Max Texture & HD Count | **Medium** | VRAM |
| Textures & World | Trees / Terrain / Grass & Alpha Shadows | **Low** | GPU, CPU, VRAM |
| Textures & World | LOD Scale | **0.8** | CPU, GPU, VRAM |
| Water | Water & Tessellation Quality | **Medium** | GPU, VRAM |
| Volumetrics & Particles | Volumetrics Lighting & Scattering | **Low** | GPU, VRAM |
| Hair | Hair Quality & Simulation | **Medium** | GPU, CPU, VRAM |
| Population / AI / Physics | Pedestrian & Vehicle Density | **Medium** | CPU, RAM, VRAM |
| Population / AI / Physics | AI Behavior / Motion / Physics Quality | **Medium** | CPU |

## 5. Multi-GPU Comparison (Current CPU / RAM / Settings)

| GPU / Console Reference | Base Avg FPS | 1% Low FPS | VRAM Status |
| :--- | ---: | ---: | :--- |
| RX 9070 XT | 81.6 | 61.2 | OK |
| RX 6900 XT | 81.3 | 61.1 | OK |
| RTX 5090 | 80.8 | 60.6 | OK |
| RTX 5070 Ti | 80.8 | 60.6 | OK |
| 9060 XT 16G | 80.6 | 60.9 | OK |
| 9060 XT 8G | 80.6 | 60.9 | OK |
| Arc B580 | 75.3 | 57.2 | OK |
| RTX 4060 8G | 70.9 | 57.6 | OK |
| PS5 Pro (Ref) | 56.1 | 43.6 | OK |
| ★ RTX 4050 (LP) | 53.0 | 45.4 | OK |
| PS5 (Ref) | 49.2 | 39.0 | OK |
| Arc 140V (LP) | 15.5 | 13.2 | OVERFLOW |
