<p align="center">
  <h1 align="center">PyDebFlow</h1>
  <p align="center">
    <strong>Advanced Two-Phase Mass Flow Simulation Software</strong>
  </p>
  <p align="center">
    Open-source debris flow, avalanche & lahar simulation inspired by r.avaflow and RAMMS
  </p>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-documentation">Documentation</a> •
  <a href="#-contributing">Contributing</a>
</p>

<p align="center">
  <a href="https://github.com/ankitdutta428/PyDebFlow"><img src="https://img.shields.io/github/stars/ankitdutta428/PyDebFlow?style=flat-square&color=ff69b4" alt="Stars"></a>
  <a href="https://github.com/ankitdutta428/PyDebFlow/actions/workflows/build.yml"><img src="https://img.shields.io/github/actions/workflow/status/ankitdutta428/PyDebFlow/build.yml?style=flat-square&label=build" alt="Build Status"></a>
  <a href="https://github.com/ankitdutta428/PyDebFlow/github/workflows/tests.yml"><img src="https://img.shields.io/github/actions/workflow/status/ankitdutta428/PyDebFlow/tests.yml?style=flat-square&label=tests" alt="Tests Status"></a>
  <a href="https://github.com/ankitdutta428/PyDebFlow/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-AGPL--3.0-blue?style=flat-square" alt="License"></a>
  <a href="https://github.com/ankitdutta428/PyDebFlow"><img src="https://img.shields.io/badge/website-online-brightgreen?style=flat-square" alt="Website"></a>
  <a href="https://github.com/ankitdutta428/PyDebFlow/releases"><img src="https://img.shields.io/github/v/release/ankitdutta428/PyDebFlow?style=flat-square&color=green" alt="Release"></a>
  <a href="https://github.com/ankitdutta428/PyDebFlow"><img src="https://img.shields.io/badge/Contributor%20Covenant-v2.0%20adopted-ff69b4?style=flat-square" alt="Contributor Covenant"></a>
</p>

<p align="center">
  <a href="https://github.com/ankitdutta428/PyDebFlow"><img src="https://img.shields.io/github/last-commit/ankitdutta428/PyDebFlow?style=flat-square" alt="Last Commit"></a>
  <a href="https://github.com/ankitdutta428/PyDebFlow/issues"><img src="https://img.shields.io/github/issues/ankitdutta428/PyDebFlow?style=flat-square" alt="Issues"></a>
  <a href="https://github.com/ankitdutta428/PyDebFlow"><img src="https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue?style=flat-square&logo=python&logoColor=white" alt="Python Versions"></a>
  <a href="https://github.com/ankitdutta428/PyDebFlow"><img src="https://img.shields.io/badge/code%20style-black-000000?style=flat-square" alt="Code Style"></a>
  <a href="https://github.com/ankitdutta428/PyDebFlow"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square" alt="PRs Welcome"></a>
</p>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
  - [GUI Mode](#gui-mode)
  - [Command Line Interface](#command-line-interface)
  - [Python API](#python-api)
- [Physical Models](#-physical-models)
- [Input/Output Formats](#-inputoutput-formats)
- [Examples](#-examples)
- [Architecture](#-architecture)
- [Testing](#-testing)
- [Building Executable](#-building-executable)
- [Contributing](#-contributing)
- [Acknowledgments](#-acknowledgments)
- [License](#-license)

---

## 🌍 Overview

**PyDebFlow** is a professional-grade, open-source mass flow simulation tool designed for geoscientists, hazard analysts, and researchers. It simulates the dynamics of:

- 🏔️ **Debris flows** - Rapid, gravity-driven flows of saturated debris
- ❄️ **Snow avalanches** - Dry and wet snow mass movements  
- 🌋 **Volcanic lahars** - Volcanic mudflows and debris flows
- 🪨 **Rock avalanches** - High-velocity rock mass failures
- 💧 **Hyperconcentrated flows** - Sediment-laden flood events

PyDebFlow implements a **two-phase (solid + fluid) shallow water model** with advanced numerical schemes, making it a powerful replica of established software like [r.avaflow](https://www.avaflow.org/) and [RAMMS](https://ramms.slf.ch/).

### Why PyDebFlow?

| Feature | PyDebFlow | r.avaflow | RAMMS |
|---------|-----------|-----------|-------|
| **Open Source** | ✅ AGPL-3.0 | ✅ GPL | ❌ Commercial |
| **Two-Phase Flow** | ✅ | ✅ | ❌ |
| **Python API** | ✅ Native | ❌ GRASS GIS | ❌ |
| **Modern GUI** | ✅ PyQt6 | ❌ | ✅ |
| **3D Visualization** | ✅ PyVista | ✅ ParaView | ✅ |
| **Cross-Platform** | ✅ Win/Linux | ✅ Linux | ❌ Windows |
| **Standalone .exe** | ✅ PyInstaller | ❌ | ✅ |

---

## ✨ Features

### 🧮 Numerical Solver

- **NOC-TVD Scheme** - Non-Oscillatory Central with Total Variation Diminishing limiters
- **CFL-Adaptive Timestep** - Automatic stable timestep calculation
- **Multiple Flux Limiters** - Minmod, Superbee, Van Leer
- **Dimensional Splitting** - Efficient 2D computation via x/y sweeps
- **Numba JIT Acceleration** - Near-C performance with Python simplicity

### 🔬 Physics Engine

- **Two-Phase Flow Model** - Solid granular + viscous fluid phases
- **Multiple Rheology Models:**
  - Mohr-Coulomb (dry granular friction)
  - Voellmy-Salm (avalanche standard model)
  - Bingham (viscoplastic mudflows)
  - Herschel-Bulkley (general viscoplastic)
- **Entrainment/Erosion** - Bed material incorporation
- **Solid-Fluid Drag** - Phase interaction forces
- **Impact Pressure** - Hazard assessment calculations

### 🗺️ Terrain & I/O

- **DEM Formats:** GeoTIFF (.tif), ESRI ASCII Grid (.asc), NumPy (.npy)
- **Synthetic Terrain** - Built-in slope/channel generators for testing
- **Georeferenced Output** - Maintains spatial reference from input DEMs
- **Results Export:** NumPy arrays, JSON summaries, raster outputs

### 🎨 Visualization

- **Premium 3D Viewer** - Interactive PyVista/VTK terrain rendering
- **Animated Debris Flow** - Time-series flow progression on DEM
- **Video Export** - MP4/GIF animation generation
- **Publication-Ready Plots** - Matplotlib multi-panel summaries
- **Real-Time Progress** - Console progress bars during simulation

### 🖥️ User Interface

- **Modern PyQt6 GUI** - Dark-themed professional desktop application
- **Parameter Presets** - Quick setup for debris/snow/lahar scenarios
- **Background Simulation** - Non-blocking threaded execution
- **Interactive Controls** - Load DEM, configure, run, visualize, export

### 📦 Distribution

- **Standalone Executable** - Single `.exe` file via PyInstaller
- **No Dependencies** - End users don't need Python installed
- **Sample Data** - Included test DEMs for immediate use

---

## 💾 Installation

### Prerequisites

- **Python 3.10, 3.11, or 3.12** (recommended: 3.12)
- **pip** package manager
- **Git** (for cloning)

### Method 1: Install from PyPI (Easiest)

```bash
# Basic installation
pip install pydebflow

# With visualization support (3D viewer, animations)
pip install pydebflow[visualization]

# With GUI support
pip install pydebflow[gui]

# Full installation (all features)
pip install pydebflow[all]
```

### Method 2: Quick Install with Scripts

```bash
# Clone the repository
git clone https://github.com/ankitdutta428/PyDebFlow.git
cd PyDebFlow

# Run the install script
# On Windows:
scripts\install.bat

# On Linux/macOS:
chmod +x scripts/install.sh
./scripts/install.sh
```

### Method 2: Manual Install

```bash
# Clone the repository
git clone https://github.com/ankitdutta428/PyDebFlow.git
cd PyDebFlow

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Method 2: Direct Installation

```bash
pip install numpy>=1.24.0 numba>=0.57.0 rasterio>=1.3.0 matplotlib>=3.7.0 \
    PyQt6>=6.5.0 scipy>=1.10.0 pyvista>=0.42.0 imageio>=2.31.0 \
    imageio-ffmpeg>=0.4.0 pyyaml>=6.0.0 pytest>=7.4.0
```

### Verify Installation

```bash
python -c "import numpy; import numba; print('Core dependencies OK')"
python run_simulation.py --test-all
```

### Optional: Rasterio on Windows

If you encounter issues installing `rasterio` on Windows:

```bash
# Option 1: Use conda
conda install -c conda-forge rasterio

# Option 2: Download wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/
pip install rasterio-x.x.x-cpXX-cpXX-win_amd64.whl
```

---

## 🚀 Quick Start

### Using CLI Scripts (Recommended)

```bash
# On Windows:
scripts\run.bat --synthetic-test      # Quick demo simulation
scripts\run.bat --gui                 # Launch GUI

# On Linux/macOS:
./scripts/run.sh --synthetic-test     # Quick demo simulation
./scripts/run.sh --gui                # Launch GUI
```

### Using the pydebflow CLI

```bash
# Professional CLI (after installation)
python pydebflow.py simulate --synthetic    # Quick demo
python pydebflow.py gui                     # Launch GUI
python pydebflow.py info                    # System info
python pydebflow.py simulate --dem terrain.tif --time 60 --animate
```

### Direct Python Commands

```bash
# Test with synthetic terrain
python run_simulation.py --synthetic-test

# Launch GUI
python main.py

# Run with your DEM file
python run_simulation.py --dem-file your_terrain.tif --t-end 120 --animate-3d

# Export animation video
python run_simulation.py --dem-file terrain.asc --t-end 60 --export-video
```

---

## 📖 Usage

### GUI Mode

Launch the graphical interface for an intuitive simulation experience:

```bash
python main.py
```

**GUI Features:**
- 📂 **Load DEM** - Import GeoTIFF or ASCII Grid terrain files
- ⚙️ **Parameter Panel** - Configure flow properties, rheology, simulation time
- 🎯 **Presets** - Quick-select debris flow, snow avalanche, or lahar settings
- ▶️ **Run Simulation** - Execute with real-time progress tracking
- 🖼️ **3D Visualization** - Interactive terrain and flow rendering
- 💾 **Export Results** - Save outputs and animation videos

### Command Line Interface

Full CLI for scripted/batch simulations:

```bash
python run_simulation.py [OPTIONS]
```

#### Simulation Options

| Option | Description | Default |
|--------|-------------|---------|
| `--synthetic-test` | Run with generated terrain | - |
| `--dem-file PATH` | Path to DEM file (.tif, .asc) | - |
| `--t-end SECONDS` | Simulation duration | 30.0 |
| `--output-dir PATH` | Results output directory | ./output |

#### Release Zone Configuration

| Option | Description | Default |
|--------|-------------|---------|
| `--release-row I` | Release zone center row | Auto |
| `--release-col J` | Release zone center column | Auto |
| `--release-radius N` | Radius in grid cells | 10 |
| `--release-height M` | Initial height in meters | 5.0 |

#### Visualization Options

| Option | Description | Default |
|--------|-------------|---------|
| `--animate-3d` | Show interactive 3D animation | - |
| `--export-video` | Export to MP4 video | - |
| `--no-viz` | Disable all visualization | - |

#### Testing Options

| Option | Description |
|--------|-------------|
| `--test-all` | Run all component tests |
| `--test-flow-model` | Test flow model only |
| `--test-solver` | Test NOC-TVD solver only |
| `--test-rheology` | Test rheology models only |
| `--test-3d` | Test 3D visualization |

#### Example Commands

```bash
# Quick synthetic test
python run_simulation.py --synthetic-test

# Full simulation with 3D viewer
python run_simulation.py --dem-file ./sample_dem.asc --t-end 120 --animate-3d

# Custom release zone
python run_simulation.py --dem-file terrain.tif --release-row 50 --release-col 100 \
    --release-radius 15 --release-height 8.0

# Batch processing (no visualization)
python run_simulation.py --dem-file dem1.tif --t-end 300 --output-dir ./results/run1 --no-viz

# Export animation video
python run_simulation.py --dem-file study_area.asc --t-end 60 --export-video
```

### Python API

Use PyDebFlow as a library in your own scripts:

```python
from src.core.terrain import Terrain
from src.core.flow_model import TwoPhaseFlowModel, FlowState, FlowParameters
from src.core.noc_tvd_solver import NOCTVDSolver, SolverConfig
from src.physics.rheology import Voellmy

# Load terrain
terrain = Terrain.load("your_dem.tif")

# Configure flow parameters
params = FlowParameters(
    solid_density=2500.0,      # kg/m³
    fluid_density=1100.0,      # kg/m³
    basal_friction_angle=22.0, # degrees
    voellmy_mu=0.15,           # Coulomb coefficient
    voellmy_xi=500.0           # Turbulent coefficient (m/s²)
)

# Create model and solver
model = TwoPhaseFlowModel(params)
solver = NOCTVDSolver(terrain, model)

# Initialize release zone
state = FlowState.zeros((terrain.rows, terrain.cols))
release = terrain.create_release_zone(
    center_i=20, center_j=50, radius=10, height=5.0
)
state.h_solid = release * 0.7  # 70% solid
state.h_fluid = release * 0.3  # 30% fluid

# Run simulation
outputs = solver.run_simulation(state, t_end=60.0, output_interval=1.0)

# Process results
for time, flow_state in outputs:
    h_total = flow_state.h_solid + flow_state.h_fluid
    print(f"t={time:.1f}s: max height = {h_total.max():.2f} m")
```

---

## 🔬 Physical Models

### Two-Phase Flow Equations

PyDebFlow solves the shallow water equations for a two-phase (solid + fluid) mixture:

**Mass Conservation:**
```
∂h_s/∂t + ∂(h_s·u_s)/∂x + ∂(h_s·v_s)/∂y = E_s - D_s
∂h_f/∂t + ∂(h_f·u_f)/∂x + ∂(h_f·v_f)/∂y = E_f - D_f
```

**Momentum Conservation:**
```
∂(h_s·u_s)/∂t + ... = -g·h_s·∂z/∂x - τ_s/ρ_s + F_drag
∂(h_f·u_f)/∂t + ... = -g·h_f·∂z/∂x - τ_f/ρ_f - F_drag
```

Where:
- `h_s, h_f` = solid/fluid flow heights (m)
- `u, v` = velocity components (m/s)
- `E, D` = erosion/deposition rates (m/s)
- `τ` = basal shear stress (Pa)
- `F_drag` = solid-fluid drag force

### Rheology Models

#### Mohr-Coulomb (Dry Granular)
```
τ = μ · σ_n = tan(φ) · ρgh·cos(θ)
```
Suitable for dry rockslides and granular flows.

#### Voellmy-Salm (Standard Avalanche Model)
```
τ = μ · ρgh·cos(θ) + ρg · v² / ξ
```
- `μ` = Coulomb friction coefficient (0.1–0.4)
- `ξ` = Turbulent friction coefficient (200–2000 m/s²)

Standard model for snow avalanches (RAMMS, r.avaflow).

**Presets:**
| Preset | μ | ξ | Application |
|--------|---|---|-------------|
| Snow (dry) | 0.15 | 2000 | Powder avalanches |
| Snow (wet) | 0.25 | 1000 | Wet slab avalanches |
| Rock | 0.20 | 500 | Rock avalanches |
| Debris | 0.12 | 400 | Debris flows |

#### Bingham (Viscoplastic)
```
τ = τ_y + η · (v/h)
```
For mudflows and lahars with yield strength.

#### Herschel-Bulkley (General Viscoplastic)
```
τ = τ_y + K · (γ̇)^n
```
Generalized power-law rheology.

### Entrainment Model

Erosion rate based on velocity:
```
E = e · (v - v_crit)² · (1 - α)
```

Deposition rate based on concentration:
```
D = d · α · h / (1 + v²)
```

---

## 📁 Input/Output Formats

### Supported Input Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| GeoTIFF | `.tif`, `.tiff` | Standard geospatial raster (requires rasterio) |
| ESRI ASCII Grid | `.asc` | Text-based elevation grid |
| NumPy Array | `.npy` | Native Python array format |

### ASCII Grid Format Example

```
ncols         100
nrows         80
xllcorner     500000.0
yllcorner     4000000.0
cellsize      10.0
NODATA_value  -9999
1245.3 1244.8 1244.2 ...
...
```

### Output Files

After simulation, results are saved to the output directory:

| File | Description |
|------|-------------|
| `max_height.npy` | Maximum flow height reached at each cell (m) |
| `max_velocity.npy` | Maximum velocity at each cell (m/s) |
| `max_pressure.npy` | Maximum impact pressure (kPa) |
| `final_h_solid.npy` | Final solid phase height (m) |
| `final_h_fluid.npy` | Final fluid phase height (m) |
| `final_u.npy` | Final x-velocity (m/s) |
| `final_v.npy` | Final y-velocity (m/s) |
| `summary.json` | Metadata and statistics |
| `results_summary.png` | Multi-panel visualization |
| `debris_flow.mp4` | Animation video (if exported) |

---

## 📚 Examples

### Example 1: Basic Debris Flow Simulation

```python
from src.core.terrain import Terrain
from src.core.flow_model import TwoPhaseFlowModel, FlowState, FlowParameters
from src.core.noc_tvd_solver import NOCTVDSolver

# Create synthetic terrain (25° slope with channel)
terrain = Terrain.create_synthetic_slope(
    rows=100, cols=80, cell_size=10.0,
    slope_angle=25.0, add_channel=True
)

# Standard debris flow parameters
params = FlowParameters(
    solid_density=2600.0,
    fluid_density=1100.0,
    basal_friction_angle=20.0,
    voellmy_mu=0.12,
    voellmy_xi=400.0
)

model = TwoPhaseFlowModel(params)
solver = NOCTVDSolver(terrain, model)

# Initialize 10,000 m³ release
state = FlowState.zeros((100, 80))
release = terrain.create_release_zone(15, 40, 12, 6.0)
state.h_solid = release * 0.65
state.h_fluid = release * 0.35

# Simulate 2 minutes
outputs = solver.run_simulation(state, t_end=120.0)
```

### Example 2: Snow Avalanche with Voellmy Preset

```python
from src.physics.rheology import Voellmy

# Use dry snow avalanche preset
rheology = Voellmy.from_preset('snow_dry')
# Equivalent to: Voellmy(mu=0.15, xi=2000.0)
```

### Example 3: 3D Visualization

```python
from src.visualization.dem_viewer import DEMViewer3D

# Create viewer
viewer = DEMViewer3D(
    elevation=terrain.elevation,
    cell_size=terrain.cell_size,
    vertical_exaggeration=2.0
)

# Load simulation snapshots
snapshots = [state.h_solid + state.h_fluid for _, state in outputs]
times = [t for t, _ in outputs]
viewer.load_snapshots(snapshots, times)

# Show interactive animation
viewer.show_animation("Debris Flow Simulation")

# Or export to video
viewer.export_animation("debris_flow.mp4", fps=15)
```

---

## 🏗️ Architecture

```
PyDebFlow/
├── main.py                 # GUI entry point
├── run_simulation.py       # CLI entry point
├── build_script.py         # PyInstaller build script
├── requirements.txt        # Python dependencies
├── sample_dem.asc          # Sample ASCII DEM for testing
│
├── src/
│   ├── __init__.py
│   │
│   ├── core/               # Core simulation engine
│   │   ├── flow_model.py       # Two-phase flow model & state
│   │   ├── noc_tvd_solver.py   # NOC-TVD numerical solver
│   │   └── terrain.py          # Terrain/DEM handling
│   │
│   ├── physics/            # Physical models
│   │   ├── rheology.py         # Mohr-Coulomb, Voellmy, Bingham
│   │   └── entrainment.py      # Erosion/deposition models
│   │
│   ├── io/                 # Input/Output
│   │   ├── raster_io.py        # GeoTIFF, ASCII Grid reading
│   │   ├── parameters.py       # Simulation parameters
│   │   └── results.py          # Results export
│   │
│   ├── visualization/      # Visualization
│   │   ├── dem_viewer.py       # 3D PyVista viewer
│   │   └── plot_utils.py       # Matplotlib plotting
│   │
│   └── gui/                # Graphical interface
│       └── main_window.py      # PyQt6 main window
│
├── scripts/                # CLI helper scripts
│   ├── install.sh/.bat         # Installation scripts
│   ├── run.sh/.bat             # Quick simulation runner
│   ├── test.sh/.bat            # Test runner
│   ├── build.sh/.bat           # Build executable
│   └── pydebflow/.bat          # CLI wrapper
│
├── tests/                  # Test suite
│   ├── test_integration.py     # Integration tests
│   ├── test_rheology.py        # Rheology unit tests
│   ├── test_solver.py          # Solver unit tests
│   └── test_scripts.py         # CLI script tests
│
└── .github/
    └── workflows/
        └── tests.yml           # CI/CD pipeline
```

### Module Responsibilities

| Module | Purpose |
|--------|---------|
| `core/flow_model.py` | `FlowState`, `FlowParameters`, `TwoPhaseFlowModel` classes |
| `core/noc_tvd_solver.py` | `NOCTVDSolver` with TVD flux limiters |
| `core/terrain.py` | `Terrain` class for DEM handling |
| `physics/rheology.py` | `MohrCoulomb`, `Voellmy`, `Bingham`, `HerschelBulkley` |
| `physics/entrainment.py` | `EntrainmentModel`, `McDougallHungr` |
| `visualization/dem_viewer.py` | `DEMViewer3D` with PyVista |
| `gui/main_window.py` | `MainWindow` PyQt6 application |

---

## 🧪 Testing

### Run All Tests

```bash
# Using test scripts (recommended)
# On Windows:
scripts\test.bat

# On Linux/macOS:
./scripts/test.sh

# Using pytest directly
python -m pytest tests/ -v

# Using built-in test runner
python run_simulation.py --test-all
```

### Run Specific Test Modules

```bash
# Test flow model
python run_simulation.py --test-flow-model

# Test NOC-TVD solver
python run_simulation.py --test-solver

# Test rheology models
python run_simulation.py --test-rheology

# Test 3D visualization
python run_simulation.py --test-3d
```

### Run Tests with Coverage

```bash
python -m pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

### CI/CD Pipeline

The project includes GitHub Actions workflows that:
- Run tests on Python 3.10, 3.11, 3.12
- Test on both Ubuntu and Windows
- Check code formatting (black, isort)
- Run linting (flake8)
- Upload coverage reports

---

## 📦 Building Executable

Create a standalone Windows executable:

```bash
# Using build scripts (recommended)
# On Windows:
scripts\build.bat

# On Linux/macOS:
./scripts/build.sh

# Or using the build script directly
python build_script.py
```

This produces:
- `dist/PyDebFlow.exe` - Standalone executable (~50-100 MB)
- `dist/sample_config.json` - Example configuration
- `dist/README.md` - Quick start guide

### Manual PyInstaller Build

```bash
python -m PyInstaller main.py --name=PyDebFlow --onefile --windowed \
    --add-data "src;src" \
    --hidden-import=numpy --hidden-import=PyQt6
```

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

### Development Setup

```bash
# Fork and clone
git clone https://github.com/ankitdutta428/PyDebFlow.git
cd PyDebFlow

# Use install script (creates venv and installs deps)
# Windows: scripts\install.bat
# Linux/macOS: ./scripts/install.sh

# Or manual setup:
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install black isort flake8 pytest-cov
```

### Code Style

```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint
flake8 src/ tests/ --max-line-length=100
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`python -m pytest tests/ -v`)
5. Commit changes (`git commit -m "Add amazing feature"`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Areas for Contribution

- 🌍 **Additional DEM formats** (NetCDF, HDF5)
- 🧮 **New rheology models** (μ(I) rheology)
- 📊 **Enhanced visualization** (cross-sections, time series plots)
- 📝 **Documentation** improvements
- 🐛 **Bug fixes** and optimizations

---

## 🙏 Acknowledgments

PyDebFlow is inspired by and draws concepts from:

- **[r.avaflow](https://www.avaflow.org/)** - The open-source GRASS GIS mass flow simulation tool by Martin Mergili et al.
- **[RAMMS](https://ramms.slf.ch/)** - The Swiss Federal Institute WSL's rapid mass movement simulation software
- **[DAN3D](https://www.intechopen.com/chapters/6153)** - Dynamic Analysis of Landslides by Oldrich Hungr

### Key References

- Pudasaini, S.P. (2012). A general two-phase debris flow model. *Journal of Geophysical Research*, 117(F3).
- Mergili, M., et al. (2017). r.avaflow v1, an advanced open-source computational framework for the propagation and interaction of two-phase mass flows. *Geoscientific Model Development*, 10(2), 553-569.
- Voellmy, A. (1955). Über die Zerstörungskraft von Lawinen. *Schweizerische Bauzeitung*, 73(12).
- Hungr, O. & McDougall, S. (2009). Two numerical models for landslide dynamic analysis. *Computers & Geosciences*, 35(5), 978-992.

---

## 📄 License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)** - see the [LICENSE](LICENSE) file for details.

The AGPL-3.0 license ensures that:
- ✅ You can freely use, modify, and distribute the software
- ✅ Modified versions must also be open-sourced under AGPL-3.0
- ✅ If used in a network service, source code must be made available to users
- ✅ Proper attribution must be maintained

For commercial licensing inquiries, please contact the maintainers.

---

<p align="center">
  <strong>⭐ Star this repository if PyDebFlow helps your research! ⭐</strong>
</p>

<p align="center">
  Made with ❤️ for the geoscience community
</p>

---

## 📞 Contact & Support

- 📧 **Issues**: [GitHub Issues](https://github.com/ankitdutta428/PyDebFlow/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/ankitdutta428/PyDebFlow/discussions)

---

<p align="center">
  <sub>PyDebFlow v0.1.0 • Last updated: January 2026</sub>
</p>
