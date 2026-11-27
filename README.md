# GTA VI Hardware & FPS Simulator

Glassmorphic `PySide6` desktop dashboard estimating real-time GTA VI **Average FPS**, **1% Lows**, **Frame Generation output**, **VRAM / System RAM / Unified Pool usage**, and **CPU vs GPU/RT bottlenecks** based on the leaked Tex2 console settings table and 2025/2026 PC hardware profiles.

## Features

- **Live Telemetry (Zero "Calculate" Button):** Every hardware change, toggle, display tweak, or graphics setting updates all gauges, warnings, and multi-GPU charts instantaneously.
- **System Hardware Configurator:**
  - 9 PC GPUs (`RTX 5090` down to `Laptop Arc 140V`) + `PS5` and `PS5 Pro` reference baselines
  - 8 CPUs (`Ryzen 7 9800X3D`, `i5-13400F`, `Core Ultra 7 256V`, etc.)
  - RAM capacity (`16/32/64 GB`), RAM speed profiles (`DDR4-3200` to `DDR5-6000 CL30` & `LPDDR5X-8533`), `Resizable BAR`, `GPU OC (+0% to +7%)`, `NVMe Gen4 vs SATA/HDD`, and `Laptop 20–25W Thermal Coupling`
  - Quick hardware presets (`Mainstream (7600X + 9060 XT 16G)`, `Ultrabook (Ultra 7 256V + Arc 140V)`, `High-End (9800X3D + 5090)`)
- **Tex2 Graphics Matrix & Presets:** `Series S`, `PS5 / Series X`, `PS5 Pro`, `900p Sweet Spot`, and `All Ultra` across all 6 categories (`Lighting & RT`, `Textures & World`, `Water`, `Volumetrics & Particles`, `Hair`, `Population / AI / Physics`) with `CPU`/`GPU`/`RT`/`VRAM`/`RAM` impact badges and optional `EN / فارسی` diagnosis & tooltip toggle.
- **Auto-Optimize for 60 FPS + Undo:** Intelligently reduces only the settings causing the active bottleneck (with one-click Undo).
- **Live Multi-GPU Comparison Chart:** Compares Base FPS of all GPUs plus PS5 / PS5 Pro references with 30 FPS & 60 FPS marker lines.

## Prerequisites

- **Python 3.11+** (ensure `Add python.exe to PATH` is checked during Windows installation)

## Quick Start (Windows PowerShell — Recommended)

### 1. First-Time Setup (create `.venv` & install dependencies)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

*(If `python` is not recognized, use `py -m venv .venv` instead.)*

### 2. Run the App

```powershell
.\.venv\Scripts\python.exe main.py
```

### Alternative: Run Without `.venv` (Global Python)

```powershell
pip install -r requirements.txt
python main.py
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Run Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```
