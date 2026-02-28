"""
Tests for release zone creation functionality.

Tests the new polygon and mask-based release zone methods
added to the Terrain class.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.terrain import Terrain


@pytest.fixture
def terrain():
    """Create a standard synthetic terrain for testing."""
    return Terrain.create_synthetic(rows=50, cols=40, cell_size=10.0, slope_angle=25.0)


class TestCircularReleaseZone:
    """Test existing circular release zone (regression tests)."""
    
    def test_basic_release(self, terrain):
        """Test basic circular release zone."""
        release = terrain.create_release_zone(10, 20, 5, 3.0)
        assert release.shape == (50, 40)
        assert release.max() <= 3.0
        assert release.max() > 0
        assert release[10, 20] == pytest.approx(3.0)  # Center should be max
    
    def test_zero_outside_radius(self, terrain):
        """Test that release is zero outside radius."""
        release = terrain.create_release_zone(25, 20, 5, 3.0)
        assert release[0, 0] == 0.0
        assert release[49, 39] == 0.0
    
    def test_edge_release(self, terrain):
        """Test release zone at terrain edge doesn't crash."""
        release = terrain.create_release_zone(0, 0, 5, 3.0)
        assert release.shape == (50, 40)
        assert release.max() > 0


class TestPolygonReleaseZone:
    """Test polygon-based release zone creation."""
    
    def test_triangle_release(self, terrain):
        """Test triangular polygon release zone."""
        vertices = [(10, 15), (10, 25), (20, 20)]
        release = terrain.create_polygon_release_zone(vertices, height=5.0)
        
        assert release.shape == (50, 40)
        assert release.max() <= 5.0
        assert release.max() > 0
        # Outside polygon should be zero
        assert release[0, 0] == 0.0
        assert release[49, 39] == 0.0
    
    def test_rectangle_release(self, terrain):
        """Test rectangular polygon release zone."""
        vertices = [(5, 10), (5, 30), (15, 30), (15, 10)]
        release = terrain.create_polygon_release_zone(vertices, height=4.0)
        
        assert release.shape == (50, 40)
        assert release.max() <= 4.0
        assert release.max() > 0
        # Center of rectangle should have material
        assert release[10, 20] > 0
    
    def test_polygon_uniform_height(self, terrain):
        """Test polygon with uniform (non-smooth) height."""
        vertices = [(5, 10), (5, 30), (15, 30), (15, 10)]
        release = terrain.create_polygon_release_zone(vertices, height=4.0, smooth=False)
        
        # All interior cells should have exactly height=4.0
        interior_values = release[release > 0]
        assert np.allclose(interior_values, 4.0)
    
    def test_polygon_smooth_height(self, terrain):
        """Test polygon with smooth (parabolic) height falloff."""
        vertices = [(5, 10), (5, 30), (15, 30), (15, 10)]
        release = terrain.create_polygon_release_zone(vertices, height=4.0, smooth=True)
        
        # Should have some variation (not all the same)
        interior_values = release[release > 0]
        assert interior_values.std() > 0, "Smooth height should vary across polygon"
    
    def test_polygon_too_few_vertices(self, terrain):
        """Test that < 3 vertices raises ValueError."""
        with pytest.raises(ValueError, match="at least 3"):
            terrain.create_polygon_release_zone([(10, 10), (20, 20)], height=5.0)
    
    def test_large_polygon(self, terrain):
        """Test polygon covering a large portion of terrain."""
        vertices = [(2, 2), (2, 37), (47, 37), (47, 2)]
        release = terrain.create_polygon_release_zone(vertices, height=3.0)
        
        assert release.max() <= 3.0
        affected_cells = np.sum(release > 0)
        total_cells = terrain.rows * terrain.cols
        assert affected_cells > total_cells * 0.5  # Should cover > 50%
    
    def test_polygon_outside_bounds(self, terrain):
        """Test polygon partially outside terrain bounds."""
        vertices = [(-5, 10), (-5, 30), (10, 30), (10, 10)]
        release = terrain.create_polygon_release_zone(vertices, height=5.0)
        
        # Should still produce valid output, just clipped
        assert release.shape == (50, 40)
        assert not np.isnan(release).any()
    
    def test_pentagon_release(self, terrain):
        """Test a 5-sided polygon."""
        vertices = [(10, 20), (15, 28), (25, 25), (25, 15), (15, 12)]
        release = terrain.create_polygon_release_zone(vertices, height=6.0)
        
        assert release.shape == (50, 40)
        assert release.max() <= 6.0
        assert release.max() > 0


class TestMaskReleaseZone:
    """Test mask-based release zone creation."""
    
    def test_basic_mask(self, terrain):
        """Test basic boolean mask release zone."""
        mask = np.zeros((terrain.rows, terrain.cols), dtype=bool)
        mask[10:20, 15:25] = True
        
        release = terrain.create_mask_release_zone(mask, height=5.0)
        
        assert release.shape == (50, 40)
        assert release.max() <= 5.0
        assert release.max() > 0
        assert release[0, 0] == 0.0
    
    def test_mask_uniform(self, terrain):
        """Test mask with uniform height (no smooth)."""
        mask = np.zeros((terrain.rows, terrain.cols), dtype=bool)
        mask[10:20, 15:25] = True
        
        release = terrain.create_mask_release_zone(mask, height=5.0, smooth=False)
        
        # All masked cells should be exactly 5.0
        assert np.allclose(release[mask], 5.0)
        assert np.allclose(release[~mask], 0.0)
    
    def test_empty_mask(self, terrain):
        """Test empty mask returns all zeros."""
        mask = np.zeros((terrain.rows, terrain.cols), dtype=bool)
        release = terrain.create_mask_release_zone(mask, height=5.0)
        
        assert np.allclose(release, 0.0)
    
    def test_wrong_mask_shape(self, terrain):
        """Test that wrong mask shape raises ValueError."""
        mask = np.zeros((10, 10), dtype=bool)
        with pytest.raises(ValueError, match="doesn't match"):
            terrain.create_mask_release_zone(mask, height=5.0)
    
    def test_single_cell_mask(self, terrain):
        """Test single-cell mask."""
        mask = np.zeros((terrain.rows, terrain.cols), dtype=bool)
        mask[25, 20] = True
        
        release = terrain.create_mask_release_zone(mask, height=3.0)
        assert release[25, 20] > 0
    
    def test_mask_smooth_has_max_at_centroid(self, terrain):
        """Test that smooth mask has maximum near centroid."""
        mask = np.zeros((terrain.rows, terrain.cols), dtype=bool)
        mask[10:20, 15:25] = True
        
        release = terrain.create_mask_release_zone(mask, height=5.0, smooth=True)
        
        # Centroid of 10:20, 15:25 is roughly (14.5, 19.5)
        # Maximum should be near the center
        max_pos = np.unravel_index(release.argmax(), release.shape)
        assert 10 <= max_pos[0] <= 20
        assert 15 <= max_pos[1] <= 25


class TestReleaseZoneIntegration:
    """Integration tests verifying release zones work in simulations."""
    
    def test_polygon_zone_in_simulation(self):
        """Test that a polygon release zone can drive a simulation."""
        from src.core.flow_model import TwoPhaseFlowModel, FlowState, FlowParameters
        from src.core.noc_tvd_solver import NOCTVDSolver, SolverConfig
        
        terrain = Terrain.create_synthetic(rows=30, cols=25, cell_size=10.0, slope_angle=25.0)
        
        # Create polygon release zone
        vertices = [(3, 8), (3, 17), (8, 17), (8, 8)]
        release = terrain.create_polygon_release_zone(vertices, height=3.0)
        
        # Setup simulation
        params = FlowParameters(solid_density=2500.0, fluid_density=1100.0)
        model = TwoPhaseFlowModel(params)
        config = SolverConfig(cfl_number=0.4, max_timestep=0.5)
        solver = NOCTVDSolver(terrain, model, config)
        
        state = FlowState.zeros((terrain.rows, terrain.cols))
        state.h_solid = release * 0.7
        state.h_fluid = release * 0.3
        
        initial_volume = (state.h_solid.sum() + state.h_fluid.sum()) * terrain.cell_size**2
        
        # Run short simulation
        outputs = solver.run_simulation(state, t_end=2.0, output_interval=1.0)
        
        assert len(outputs) >= 2
        _, final = outputs[-1]
        final_volume = (final.h_solid.sum() + final.h_fluid.sum()) * terrain.cell_size**2
        
        # Volume should not increase significantly
        assert final_volume <= initial_volume * 1.05


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
