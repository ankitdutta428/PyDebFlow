"""
Test suite for NOC-TVD solver.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.terrain import Terrain
from src.core.flow_model import TwoPhaseFlowModel, FlowState, FlowParameters
from src.core.noc_tvd_solver import NOCTVDSolver, SolverConfig


class TestNOCTVDSolver:
    """Tests for the NOC-TVD solver."""
    
    @pytest.fixture
    def terrain(self):
        """Create a test terrain."""
        return Terrain.create_synthetic_slope(
            rows=30, cols=30, cell_size=10.0, slope_angle=20.0
        )
    
    @pytest.fixture
    def model(self):
        """Create a flow model."""
        return TwoPhaseFlowModel()
    
    @pytest.fixture
    def solver(self, terrain, model):
        """Create a solver."""
        config = SolverConfig(cfl_number=0.4, max_timestep=0.5)
        return NOCTVDSolver(terrain, model, config)
    
    @pytest.fixture
    def initial_state(self, terrain):
        """Create an initial flow state."""
        state = FlowState.zeros((terrain.rows, terrain.cols))
        release = terrain.create_release_zone(8, 15, 4, 2.0)
        state.h_solid = release * 0.7
        state.h_fluid = release * 0.3
        return state
    
    def test_solver_initialization(self, solver, terrain):
        """Test solver initializes correctly."""
        assert solver.dx == terrain.cell_size
        # Access terrain through solver.terrain
        assert solver.terrain.rows == terrain.rows
        assert solver.terrain.cols == terrain.cols
    
    def test_single_step(self, solver, initial_state):
        """Test a single solver step."""
        dt = solver.compute_timestep(initial_state)
        new_state = solver.step(initial_state, dt)
        
        assert dt > 0
        assert isinstance(new_state, FlowState)
        assert new_state.h_solid.shape == initial_state.h_solid.shape
    
    def test_mass_conservation(self, solver, initial_state, terrain):
        """Test that mass is approximately conserved."""
        cell_area = terrain.cell_size ** 2
        
        initial_mass_solid = initial_state.h_solid.sum() * cell_area
        initial_mass_fluid = initial_state.h_fluid.sum() * cell_area
        
        # Run several steps
        state = initial_state
        for _ in range(20):
            dt = solver.compute_timestep(state)
            state = solver.step(state, dt)
        
        final_mass_solid = state.h_solid.sum() * cell_area
        final_mass_fluid = state.h_fluid.sum() * cell_area
        
        # Allow some loss due to outflow boundaries
        assert final_mass_solid <= initial_mass_solid * 1.01  # No mass creation
        assert final_mass_fluid <= initial_mass_fluid * 1.01
    
    def test_non_negative_heights(self, solver, initial_state):
        """Test that heights remain non-negative."""
        state = initial_state
        
        for _ in range(50):
            dt = solver.compute_timestep(state)
            state = solver.step(state, dt)
        
        assert (state.h_solid >= 0).all()
        assert (state.h_fluid >= 0).all()
    
    def test_cfl_timestep(self, solver, initial_state):
        """Test CFL timestep calculation."""
        dt = solver.compute_timestep(initial_state)
        
        assert dt > 0
        assert dt <= solver.config.max_timestep
    
    def test_run_simulation(self, solver, initial_state):
        """Test complete simulation run."""
        outputs = solver.run_simulation(
            initial_state,
            t_end=2.0,
            output_interval=0.5
        )
        
        assert len(outputs) >= 3  # At least initial, mid, final
        
        # Check that time increases
        times = [t for t, _ in outputs]
        assert all(times[i] <= times[i+1] for i in range(len(times)-1))
    
    def test_flow_propagation(self, solver, initial_state, terrain):
        """Test that flow actually propagates downslope."""
        # Find center of mass initially
        initial_com_y = np.sum(
            np.arange(terrain.rows)[:, np.newaxis] * initial_state.h_solid
        ) / (initial_state.h_solid.sum() + 1e-10)
        
        # Run simulation
        state = initial_state
        for _ in range(100):
            dt = solver.compute_timestep(state)
            state = solver.step(state, dt)
        
        # Flow should have moved downslope
        # Synthetic terrain has elevation increasing with row index (row 0 = low, row N = high)
        # So downslope means flow moves toward LOWER row indices
        final_com_y = np.sum(
            np.arange(terrain.rows)[:, np.newaxis] * state.h_solid
        ) / (state.h_solid.sum() + 1e-10)
        
        assert final_com_y < initial_com_y, f"Flow should move downslope (toward row 0): {final_com_y} should be < {initial_com_y}"


class TestFluxLimiters:
    """Tests for flux limiters."""
    
    def test_minmod_limiter(self):
        """Test minmod limiter."""
        from src.core.noc_tvd_solver import minmod
        
        # Same sign positive: min of absolute values
        assert minmod(1.0, 2.0) == 1.0
        
        # Same sign negative: min of absolute values with sign
        assert minmod(-1.0, -0.5) == -0.5
        
        # Different signs: zero
        assert minmod(2.0, -1.0) == 0.0
        assert minmod(0.0, 3.0) == 0.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
