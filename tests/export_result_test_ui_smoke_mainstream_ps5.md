# GTA VI Hardware & FPS Simulation Report

*Generated: 2026-11-27 14:43 Iran Standard Time*

## 1. System Hardware

| Component | Configuration |
| :--- | :--- |
| **Form Factor** | Desktop Tower |
| **GPU** | RX 9060 XT (16GB) — 16 GB (320 GB/s, PCIe x16) |
| **CPU** | Ryzen 5 7600X (6C / 12T, Sim Score 80) |
| **RAM** | 32 GB DDR5-5600 |
| **Resizable BAR** | ON |
| **GPU Overclock** | +0% |
| **Storage** | NVMe Gen4 |

## 2. Display & Frame Generation

| Option | Setting |
| :--- | :--- |
| **Output Resolution** | 1440p |
| **Upscaler** | FSR Quality (1.5x) (0.55x effective scale) |
| **Frame Generation** | Off |
| **DLSS 5 Neural Rendering** | Off |

## 3. Live Telemetry & Bottleneck Radar

| Metric | Value |
| :--- | :--- |
| **Average Base FPS** | **67.7 FPS** (GPU Ceiling 88.2 / CPU Ceiling 67.7) |
| **1% Low FPS (City/Chaos)** | **52.6 FPS** |
| **With Frame Generation** | Off |
| **Core Loads** | GPU 76% • RT 59% • CPU 96% |
| **VRAM Footprint** | 8.3 / 16 GB (52%) |
| **System RAM Footprint** | 12.4 / 32 GB (39%) |
| **Primary Bottleneck** | **CPU** |

> **Diagnosis:** CPU Simulation Bottleneck: Ryzen 5 7600X + DDR5-5600 caps FPS around 68 FPS while GPU headroom reaches 88 FPS.
>
> **Recommendation:** Lower Pedestrian & Vehicle Density, AI/Physics Quality, BVH Quality, or LOD Scale — changing resolution/upscaler will NOT lift a CPU cap.

## 4. Tex2 Graphics Settings

| Category | Setting | Selected | Primary Load |
| :--- | :--- | :--- | :--- |
| Lighting & RT | Global Illumination (RTGI) | **Medium** | RT, VRAM |
| Lighting & RT | Ray-Traced Shadows (Dir + Local + LOD) | **Off / None** | RT, CPU, VRAM |
| Lighting & RT | Reflection Quality | **Low** | RT, GPU, VRAM |
| Lighting & RT | BVH Quality | **High** | CPU, RT, VRAM |
| Lighting & RT | Directional & Local Raster Shadows | **High** | GPU, VRAM |
| Textures & World | Texture Quality | **High** | VRAM, GPU |
| Textures & World | Vehicle Max Texture & HD Count | **Ultra** | VRAM |
| Textures & World | Trees / Terrain / Grass & Alpha Shadows | **Medium** | GPU, CPU, VRAM |
| Textures & World | LOD Scale | **1.0** | CPU, GPU, VRAM |
| Water | Water & Tessellation Quality | **High** | GPU, VRAM |
| Volumetrics & Particles | Volumetrics Lighting & Scattering | **Medium** | GPU, VRAM |
| Hair | Hair Quality & Simulation | **High** | GPU, CPU, VRAM |
| Population / AI / Physics | Pedestrian & Vehicle Density | **High** | CPU, RAM, VRAM |
| Population / AI / Physics | AI Behavior / Motion / Physics Quality | **High** | CPU |

## 5. Multi-GPU Comparison (Current CPU / RAM / Settings)

| GPU / Console Reference | Base Avg FPS | 1% Low FPS | VRAM Status |
| :--- | ---: | ---: | :--- |
| RX 9070 XT | 67.7 | 52.6 | OK |
| RX 6900 XT | 67.7 | 52.6 | OK |
| ★ 9060 XT 16G | 67.7 | 52.6 | OK |
| 9060 XT 8G | 67.4 | 42.4 | OVERFLOW |
| RTX 5090 | 67.2 | 52.2 | OK |
| RTX 5070 Ti | 67.2 | 52.2 | OK |
| Arc B580 | 64.5 | 50.1 | OK |
| RTX 4060 8G | 59.7 | 39.7 | OVERFLOW |
| PS5 Pro (Ref) | 39.3 | 30.5 | OK |
| PS5 (Ref) | 35.8 | 27.8 | OK |
| RTX 4050 (LP) | 22.1 | 3.8 | OVERFLOW |
| Arc 140V (LP) | 14.3 | 5.3 | OVERFLOW |
