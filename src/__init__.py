"""
PyDebFlow - Advanced Two-Phase Mass Flow Simulation Software
=============================================================

An open-source simulation tool for debris flows, avalanches, and lahars.
Inspired by r.avaflow and RAMMS.

Basic Usage
-----------
>>> import pydebflow
>>> terrain = pydebflow.Terrain.create_synthetic_slope(rows=80, cols=60)
>>> params = pydebflow.FlowParameters(solid_density=2500.0, fluid_density=1100.0)
>>> model = pydebflow.TwoPhaseFlowModel(params)
>>> solver = pydebflow.NOCTVDSolver(terrain, model)

For more information, see: https://github.com/ankitdutta428/PyDebFlow
"""

__version__ = "0.1.0"
__author__ = "Ankit Dutta"
__email__ = "ankitdutta428@gmail.com"
__license__ = "AGPL-3.0"

# Core simulation components
from .core.terrain import Terrain
from .core.flow_model import TwoPhaseFlowModel, FlowState, FlowParameters
from .core.noc_tvd_solver import NOCTVDSolver, SolverConfig

# Physics models
from .physics.rheology import MohrCoulomb, Voellmy, Bingham, HerschelBulkley
from .physics.entrainment import EntrainmentModel

# I/O utilities
from .io.parameters import SimulationParameters
from .io.results import SimulationResults, ResultsExporter

# Visualization (optional - may not be installed)
try:
    from .visualization.dem_viewer import DEMViewer3D
    from .visualization.plot_utils import FlowVisualizer
    _HAS_VISUALIZATION = True
except ImportError:
    _HAS_VISUALIZATION = False
    DEMViewer3D = None
    FlowVisualizer = None

# Public API
__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    
    # Core classes
    "Terrain",
    "TwoPhaseFlowModel",
    "FlowState",
    "FlowParameters",
    "NOCTVDSolver",
    "SolverConfig",
    
    # Physics
    "MohrCoulomb",
    "Voellmy",
    "Bingham",
    "HerschelBulkley",
    "EntrainmentModel",
    
    # I/O
    "SimulationParameters",
    "SimulationResults",
    "ResultsExporter",
    
    # Visualization (optional)
    "DEMViewer3D",
    "FlowVisualizer",
]


def main():
    """CLI entry point."""
    import sys
    from pathlib import Path
    
    # Add parent to path for pydebflow.py
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    try:
        from pydebflow import main as cli_main
        cli_main()
    except ImportError:
        # Fallback: run directly
        import subprocess
        subprocess.run([sys.executable, str(Path(__file__).parent.parent / "pydebflow.py")] + sys.argv[1:])


def get_version():
    """Return the current version."""
    return __version__


def has_visualization():
    """Check if visualization dependencies are installed."""
    return _HAS_VISUALIZATION
