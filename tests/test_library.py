"""
test_library.py - Library Import and Initialization Tests
==========================================================

Tests that verify the PyDebFlow library can be imported correctly
and that all public API components are accessible.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for development testing
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestLibraryImports:
    """Test that all library imports work correctly."""
    
    def test_import_package(self):
        """Test that the main package can be imported."""
        import src as pydebflow
        assert pydebflow is not None
    
    def test_version_accessible(self):
        """Test that version info is accessible."""
        import src as pydebflow
        assert hasattr(pydebflow, '__version__')
        assert pydebflow.__version__ == "0.1.0"
    
    def test_author_info(self):
        """Test that author info is accessible."""
        import src as pydebflow
        assert hasattr(pydebflow, '__author__')
        assert hasattr(pydebflow, '__email__')
        assert hasattr(pydebflow, '__license__')
    
    def test_get_version_function(self):
        """Test the get_version() helper function."""
        import src as pydebflow
        assert pydebflow.get_version() == "0.1.0"


class TestCoreImports:
    """Test that core simulation components are importable."""
    
    def test_import_terrain(self):
        """Test Terrain class import."""
        from src import Terrain
        assert Terrain is not None
    
    def test_import_flow_model(self):
        """Test flow model imports."""
        from src import TwoPhaseFlowModel, FlowState, FlowParameters
        assert TwoPhaseFlowModel is not None
        assert FlowState is not None
        assert FlowParameters is not None
    
    def test_import_solver(self):
        """Test solver imports."""
        from src import NOCTVDSolver, SolverConfig
        assert NOCTVDSolver is not None
        assert SolverConfig is not None


class TestPhysicsImports:
    """Test that physics models are importable."""
    
    def test_import_rheology_models(self):
        """Test rheology model imports."""
        from src import MohrCoulomb, Voellmy, Bingham, HerschelBulkley
        assert MohrCoulomb is not None
        assert Voellmy is not None
        assert Bingham is not None
        assert HerschelBulkley is not None
    
    def test_import_entrainment(self):
        """Test entrainment model import."""
        from src import EntrainmentModel
        assert EntrainmentModel is not None


class TestIOImports:
    """Test that I/O components are importable."""
    
    def test_import_parameters(self):
        """Test parameters import."""
        from src import SimulationParameters
        assert SimulationParameters is not None
    
    def test_import_results(self):
        """Test results imports."""
        from src import SimulationResults, ResultsExporter
        assert SimulationResults is not None
        assert ResultsExporter is not None


class TestOptionalImports:
    """Test optional visualization imports."""
    
    def test_has_visualization_function(self):
        """Test the has_visualization() helper."""
        import src as pydebflow
        assert hasattr(pydebflow, 'has_visualization')
        # Should return True or False, not raise an error
        result = pydebflow.has_visualization()
        assert isinstance(result, bool)
    
    def test_visualization_in_all(self):
        """Test that visualization classes are in __all__."""
        import src as pydebflow
        assert 'DEMViewer3D' in pydebflow.__all__
        assert 'FlowVisualizer' in pydebflow.__all__


class TestPublicAPI:
    """Test that __all__ contains expected exports."""
    
    def test_all_exports_exist(self):
        """Test that all items in __all__ are actually exported."""
        import src as pydebflow
        
        for name in pydebflow.__all__:
            if name.startswith('__'):
                # Version info
                assert hasattr(pydebflow, name), f"Missing: {name}"
            else:
                # Class or function
                obj = getattr(pydebflow, name, None)
                # Optional dependencies may be None, that's OK
                assert name in dir(pydebflow), f"Not in dir: {name}"
