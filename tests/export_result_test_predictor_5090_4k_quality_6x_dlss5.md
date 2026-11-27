# GTA VI Hardware & FPS Simulation Report

*Generated: 2026-11-27 14:43 Iran Standard Time*

## 1. System Hardware

| Component | Configuration |
| :--- | :--- |
| **Form Factor** | Desktop Tower |
| **GPU** | RTX 5090 — 32 GB (1792 GB/s, PCIe x16) |
| **CPU** | Ryzen 7 9800X3D (8C / 16T, Sim Score 112) |
| **RAM** | 32 GB DDR5-6000 CL30 |
| **Resizable BAR** | ON |
| **GPU Overclock** | +0% |
| **Storage** | NVMe Gen4 |

## 2. Display & Frame Generation

| Option | Setting |
| :--- | :--- |
| **Output Resolution** | 4K |
| **Upscaler** | DLSS Quality (1.5x) (1.06x effective scale) |
| **Frame Generation** | MFG 6x |
| **DLSS 5 Neural Rendering** | On (3D-Guided) |

## 3. Live Telemetry & Bottleneck Radar

| Metric | Value |
| :--- | :--- |
| **Average Base FPS** | **72.2 FPS** (GPU Ceiling 72.8 / CPU Ceiling 82.7) |
| **1% Low FPS (City/Chaos)** | **60.0 FPS** |
| **With Frame Generation** | **285.3 FPS** (MFG 6x) |
| **Core Loads** | GPU 98% • RT 100% • CPU 84% |
| **VRAM Footprint** | 17.8 / 32 GB (56%) |
| **System RAM Footprint** | 17.7 / 32 GB (55%) |
| **Primary Bottleneck** | **GPU / RT** |

> **Diagnosis:** GPU Bound (Ray Tracing (RTGI / RT Shadows / Reflections)): RTX 5090 limits output to 73 FPS while Ryzen 7 9800X3D can feed 83 FPS. DLSS 5 Neural Rendering trades ~28% GPU FPS + 1.3 GB VRAM for AI-synthesized materials & lighting.
>
> **Recommendation:** Step up Upscaler (Quality/Balanced) or disable DLSS 5 Neural Rendering, or trim RT Shadows, Reflections, and Volumetrics.

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
| ★ RTX 5090 | 72.2 | 60.0 | OK |
| RX 9070 XT | 50.5 | 32.4 | OVERFLOW |
| RX 6900 XT | 33.2 | 21.3 | OVERFLOW |
| RTX 5070 Ti | 30.3 | 8.6 | OVERFLOW |
| 9060 XT 16G | 30.0 | 19.2 | OVERFLOW |
| PS5 Pro (Ref) | 20.7 | 1.8 | OVERFLOW |
| Arc B580 | 11.4 | 2.0 | OVERFLOW |
| 9060 XT 8G | 10.3 | 1.8 | OVERFLOW |
| RTX 4060 8G | 8.1 | 1.4 | OVERFLOW |
| PS5 (Ref) | 8.0 | 1.0 | OVERFLOW |
| RTX 4050 (LP) | 6.0 | 1.0 | OVERFLOW |
| Arc 140V (LP) | 3.6 | 1.0 | OVERFLOW |
