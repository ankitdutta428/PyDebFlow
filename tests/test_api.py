"""
test_api.py - Public API Integration Tests
============================================

Tests that verify the PyDebFlow public API works correctly,
including creating terrain, running simulations, and processing results.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add src to path for development testing
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestTerrainAPI:
    """Test Terrain class public API."""
    
    def test_create_synthetic_slope(self):
        """Test creating synthetic terrain."""
        from src import Terrain
        
        terrain = Terrain.create_synthetic_slope(
            rows=40,
            cols=30,
            cell_size=10.0,
            slope_angle=20.0
        )
        
        assert terrain.rows == 40
        assert terrain.cols == 30
        assert terrain.cell_size == 10.0
        assert terrain.elevation.shape == (40, 30)
    
    def test_terrain_properties(self):
        """Test Terrain properties."""
        from src import Terrain
        
        terrain = Terrain.create_synthetic_slope(rows=50, cols=40)
        
        # Should have these properties
        assert hasattr(terrain, 'elevation')
        assert hasattr(terrain, 'rows')
        assert hasattr(terrain, 'cols')
        assert hasattr(terrain, 'cell_size')
        assert hasattr(terrain, 'slope_x')
        assert hasattr(terrain, 'slope_y')
    
    def test_create_release_zone(self):
        """Test creating a release zone."""
        from src import Terrain
        
        terrain = Terrain.create_synthetic_slope(rows=50, cols=40)
        release = terrain.create_release_zone(
            center_i=10,
            center_j=20,
            radius=5,
            height=3.0
        )
        
        assert release.shape == (50, 40)
        assert release.max() <= 3.0
        assert release.max() > 0.0


class TestFlowModelAPI:
    """Test FlowModel public API."""
    
    def test_create_flow_parameters(self):
        """Test creating flow parameters."""
        from src import FlowParameters
        
        params = FlowParameters(
            solid_density=2500.0,
            fluid_density=1100.0,
            basal_friction_angle=22.0
        )
        
        assert params.solid_density == 2500.0
        assert params.fluid_density == 1100.0
        assert params.basal_friction_angle == 22.0
    
    def test_create_flow_state(self):
        """Test creating flow state."""
        from src import FlowState
        
        state = FlowState.zeros((50, 40))
        
        assert state.h_solid.shape == (50, 40)
        assert state.h_fluid.shape == (50, 40)
        assert state.u_solid.shape == (50, 40)
        assert state.v_solid.shape == (50, 40)
    
    def test_create_two_phase_model(self):
        """Test creating two-phase flow model."""
        from src import TwoPhaseFlowModel, FlowParameters
        
        params = FlowParameters(
            solid_density=2500.0,
            fluid_density=1100.0
        )
        model = TwoPhaseFlowModel(params)
        
        assert model is not None
        assert model.params.solid_density == 2500.0


class TestSolverAPI:
    """Test Solver public API."""
    
    def test_create_solver_config(self):
        """Test creating solver configuration."""
        from src import SolverConfig
        
        config = SolverConfig(
            cfl_number=0.4,
            max_timestep=0.5,
            flux_limiter="minmod"
        )
        
        assert config.cfl_number == 0.4
        assert config.max_timestep == 0.5
    
    def test_create_solver(self):
        """Test creating NOC-TVD solver."""
        from src import Terrain, TwoPhaseFlowModel, FlowParameters, NOCTVDSolver
        
        terrain = Terrain.create_synthetic_slope(rows=30, cols=25)
        params = FlowParameters(solid_density=2500.0, fluid_density=1100.0)
        model = TwoPhaseFlowModel(params)
        
        solver = NOCTVDSolver(terrain, model)
        
        assert solver is not None


class TestRheologyAPI:
    """Test Rheology models public API."""
    
    def test_voellmy_creation(self):
        """Test Voellmy model creation."""
        from src import Voellmy
        
        voellmy = Voellmy(mu=0.15, xi=500.0)
        assert voellmy.mu == 0.15
        assert voellmy.xi == 500.0
    
    def test_voellmy_preset(self):
        """Test Voellmy preset factory."""
        from src import Voellmy
        
        voellmy = Voellmy.from_preset('debris')
        assert voellmy is not None
        assert voellmy.mu > 0
        assert voellmy.xi > 0
    
    def test_mohr_coulomb_creation(self):
        """Test Mohr-Coulomb model."""
        from src import MohrCoulomb
        
        mc = MohrCoulomb(friction_angle=30.0)
        assert mc is not None


class TestIOAPI:
    """Test I/O components public API."""
    
    def test_simulation_parameters(self):
        """Test SimulationParameters."""
        from src import SimulationParameters
        
        params = SimulationParameters()
        assert params is not None
    
    def test_simulation_results(self):
        """Test SimulationResults."""
        from src import SimulationResults
        import numpy as np
        
        results = SimulationResults(
            times=[0.0, 1.0, 2.0],
            max_flow_height=np.zeros((10, 10)),
            max_velocity=np.zeros((10, 10)),
            max_pressure=np.zeros((10, 10)),
            final_h_solid=np.zeros((10, 10)),
            final_h_fluid=np.zeros((10, 10)),
            final_u=np.zeros((10, 10)),
            final_v=np.zeros((10, 10))
        )
        assert results is not None


class TestMinimalSimulation:
    """Test running a minimal simulation."""
    
    def test_quick_simulation(self):
        """Test running a very short simulation."""
        from src import (
            Terrain, TwoPhaseFlowModel, FlowParameters,
            FlowState, NOCTVDSolver, SolverConfig
        )
        
        # Create small terrain
        terrain = Terrain.create_synthetic_slope(
            rows=20, cols=15, 
            cell_size=10.0,
            slope_angle=25.0
        )
        
        # Setup model
        params = FlowParameters(
            solid_density=2500.0,
            fluid_density=1100.0,
            basal_friction_angle=22.0
        )
        model = TwoPhaseFlowModel(params)
        
        # Configure solver for quick test
        config = SolverConfig(cfl_number=0.4, max_timestep=0.5)
        solver = NOCTVDSolver(terrain, model, config)
        
        # Initial state with small release
        state = FlowState.zeros((20, 15))
        release = terrain.create_release_zone(5, 7, 3, 2.0)
        state.h_solid = release * 0.7
        state.h_fluid = release * 0.3
        
        # Run very short simulation (2 seconds)
        outputs = solver.run_simulation(
            state,
            t_end=2.0,
            output_interval=1.0
        )
        
        # Should have outputs
        assert len(outputs) >= 2
        
        # Each output should be (time, state) tuple
        t, final_state = outputs[-1]
        assert t >= 2.0
        assert final_state.h_solid.shape == (20, 15)
