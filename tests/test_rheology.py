"""
Test suite for rheological models.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.physics.rheology import (
    MohrCoulomb, Voellmy, Bingham, HerschelBulkley, RheologyResult
)


class TestMohrCoulomb:
    """Tests for Mohr-Coulomb model."""
    
    @pytest.fixture
    def model(self):
        """Create a Mohr-Coulomb model."""
        return MohrCoulomb(friction_angle=25.0)
    
    def test_zero_velocity_stress(self, model):
        """Test stress calculation with zero velocity."""
        h = np.array([[2.0]])
        u = np.array([[0.0]])
        v = np.array([[0.0]])
        rho = np.array([[2200.0]])
        slope_x = np.array([[0.2]])
        slope_y = np.array([[0.2]])
        
        result = model.compute_basal_stress(h, u, v, rho, slope_x, slope_y)
        
        # With zero velocity, stress direction is undefined
        # Model should handle this gracefully
        assert np.isfinite(result.tau_x).all()
        assert np.isfinite(result.tau_y).all()
    
    def test_stress_direction(self, model):
        """Test that stress opposes velocity."""
        h = np.array([[2.0]])
        u = np.array([[5.0]])
        v = np.array([[0.0]])
        rho = np.array([[2200.0]])
        slope_x = np.array([[0.2]])
        slope_y = np.array([[0.2]])
        
        result = model.compute_basal_stress(h, u, v, rho, slope_x, slope_y)
        
        # Stress should oppose velocity
        assert result.tau_x[0, 0] < 0  # Opposes positive u
    
    def test_stress_magnitude_increases_with_height(self, model):
        """Test that stress increases with flow height."""
        h1 = np.array([[1.0]])
        h2 = np.array([[3.0]])
        u = np.array([[5.0]])
        v = np.array([[0.0]])
        rho = np.array([[2200.0]])
        slope_x = np.array([[0.2]])
        slope_y = np.array([[0.2]])
        
        result1 = model.compute_basal_stress(h1, u, v, rho, slope_x, slope_y)
        result2 = model.compute_basal_stress(h2, u, v, rho, slope_x, slope_y)
        
        assert abs(result2.tau_x[0, 0]) > abs(result1.tau_x[0, 0])


class TestVoellmy:
    """Tests for Voellmy model."""
    
    @pytest.fixture
    def model(self):
        """Create a Voellmy model."""
        return Voellmy(mu=0.2, xi=500.0)
    
    def test_coulomb_component(self, model):
        """Test that Coulomb component works."""
        h = np.array([[2.0]])
        u = np.array([[1.0]])
        v = np.array([[0.0]])
        rho = np.array([[2200.0]])
        slope_x = np.array([[0.2]])
        slope_y = np.array([[0.2]])
        
        result = model.compute_basal_stress(h, u, v, rho, slope_x, slope_y)
        
        assert result.tau_x[0, 0] < 0
    
    def test_turbulent_increases_with_velocity(self, model):
        """Test turbulent component increases with velocity."""
        h = np.array([[2.0]])
        u_slow = np.array([[2.0]])
        u_fast = np.array([[10.0]])
        v = np.array([[0.0]])
        rho = np.array([[2200.0]])
        slope_x = np.array([[0.2]])
        slope_y = np.array([[0.2]])
        
        result_slow = model.compute_basal_stress(h, u_slow, v, rho, slope_x, slope_y)
        result_fast = model.compute_basal_stress(h, u_fast, v, rho, slope_x, slope_y)
        
        # Higher velocity should give higher resistance
        assert abs(result_fast.tau_x[0, 0]) > abs(result_slow.tau_x[0, 0])
    
    def test_preset(self):
        """Test Voellmy preset creation."""
        voellmy = Voellmy.from_preset('rock')
        assert voellmy.mu == 0.10
        assert voellmy.xi == 500


class TestBingham:
    """Tests for Bingham fluid model."""
    
    @pytest.fixture
    def model(self):
        """Create a Bingham model."""
        return Bingham(yield_stress=100.0, viscosity=50.0)
    
    def test_yield_stress_included(self, model):
        """Test that yield stress is included."""
        h = np.array([[2.0]])
        u = np.array([[0.01]])  # Very slow flow
        v = np.array([[0.0]])
        rho = np.array([[1100.0]])
        slope_x = np.array([[0.1]])
        slope_y = np.array([[0.1]])
        
        result = model.compute_basal_stress(h, u, v, rho, slope_x, slope_y)
        
        # Even at low velocity, should have significant stress due to yield
        assert abs(result.tau_x[0, 0]) > model.tau_y * 0.5
    
    def test_viscous_component(self, model):
        """Test viscous component increases with velocity."""
        h = np.array([[2.0]])
        u_slow = np.array([[1.0]])
        u_fast = np.array([[5.0]])
        v = np.array([[0.0]])
        rho = np.array([[1100.0]])
        slope_x = np.array([[0.1]])
        slope_y = np.array([[0.1]])
        
        result_slow = model.compute_basal_stress(h, u_slow, v, rho, slope_x, slope_y)
        result_fast = model.compute_basal_stress(h, u_fast, v, rho, slope_x, slope_y)
        
        # Faster flow = higher stress
        assert abs(result_fast.tau_x[0, 0]) > abs(result_slow.tau_x[0, 0])


class TestRheologyConsistency:
    """Cross-model consistency tests."""
    
    def test_all_models_finite_output(self):
        """Test all models produce finite outputs."""
        models = [
            MohrCoulomb(friction_angle=25.0),
            Voellmy(mu=0.15, xi=500.0),
            Bingham(yield_stress=100.0, viscosity=50.0),
            HerschelBulkley(yield_stress=100.0, consistency=50.0, flow_index=0.5),
        ]
        
        h = np.random.rand(10, 10) * 3 + 0.1
        u = np.random.rand(10, 10) * 10
        v = np.random.rand(10, 10) * 5
        rho = np.ones((10, 10)) * 2000.0
        slope_x = np.random.rand(10, 10) * 0.3
        slope_y = np.random.rand(10, 10) * 0.3
        
        for model in models:
            result = model.compute_basal_stress(h, u, v, rho, slope_x, slope_y)
            
            assert np.isfinite(result.tau_x).all(), f"{model.__class__.__name__} produced non-finite tau_x"
            assert np.isfinite(result.tau_y).all(), f"{model.__class__.__name__} produced non-finite tau_y"
    
    def test_stress_opposes_motion(self):
        """Test all models have stress opposing motion."""
        models = [
            MohrCoulomb(friction_angle=25.0),
            Voellmy(mu=0.15, xi=500.0),
            Bingham(yield_stress=100.0, viscosity=50.0),
        ]
        
        h = np.array([[2.0]])
        u = np.array([[5.0]])
        v = np.array([[0.0]])
        rho = np.array([[2000.0]])
        slope_x = np.array([[0.2]])
        slope_y = np.array([[0.2]])
        
        for model in models:
            result = model.compute_basal_stress(h, u, v, rho, slope_x, slope_y)
            
            # Stress in x should oppose positive u
            assert result.tau_x[0, 0] <= 0, f"{model.__class__.__name__} stress doesn't oppose motion"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
