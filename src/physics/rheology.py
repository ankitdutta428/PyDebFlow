"""
Rheology Models for OpenDebris.

Implements various basal friction and flow resistance models:
- Mohr-Coulomb (dry granular)
- Voellmy (snow avalanche, rock avalanche)
- Bingham (viscoplastic mud)
- Herschel-Bulkley (general viscoplastic)
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple
from abc import ABC, abstractmethod


@dataclass
class RheologyResult:
    """Result of rheology computation."""
    tau_x: np.ndarray  # Basal shear stress, x-component (Pa)
    tau_y: np.ndarray  # Basal shear stress, y-component (Pa)
    effective_mu: np.ndarray  # Effective friction coefficient


class BaseRheology(ABC):
    """Abstract base class for rheology models."""
    
    @abstractmethod
    def compute_basal_stress(self, 
                              h: np.ndarray, 
                              u: np.ndarray, 
                              v: np.ndarray,
                              rho: np.ndarray,
                              slope_x: np.ndarray,
                              slope_y: np.ndarray) -> RheologyResult:
        """
        Compute basal shear stress.
        
        Args:
            h: Flow height (m)
            u: x-velocity (m/s)
            v: y-velocity (m/s)
            rho: Mixture density (kg/m³)
            slope_x: x-component of slope gradient
            slope_y: y-component of slope gradient
            
        Returns:
            RheologyResult with stress components
        """
        pass


class MohrCoulomb(BaseRheology):
    """
    Mohr-Coulomb friction model.
    
    τ = μ * σ_n = tan(φ) * ρgh*cos(θ)
    
    Suitable for dry granular flows.
    """
    
    def __init__(self, friction_angle: float = 25.0):
        """
        Args:
            friction_angle: Basal friction angle in degrees
        """
        self.friction_angle = friction_angle
        self.tan_phi = np.tan(np.radians(friction_angle))
        self.g = 9.81
    
    def compute_basal_stress(self,
                              h: np.ndarray,
                              u: np.ndarray,
                              v: np.ndarray,
                              rho: np.ndarray,
                              slope_x: np.ndarray,
                              slope_y: np.ndarray) -> RheologyResult:
        
        # Slope angle
        slope_mag = np.sqrt(slope_x**2 + slope_y**2)
        cos_theta = 1.0 / np.sqrt(1 + slope_mag**2)
        
        # Normal stress
        sigma_n = rho * self.g * h * cos_theta
        
        # Friction magnitude
        tau_mag = self.tan_phi * sigma_n
        
        # Velocity direction
        speed = np.sqrt(u**2 + v**2) + 1e-10
        
        # Stress components (opposite to velocity)
        tau_x = -tau_mag * u / speed
        tau_y = -tau_mag * v / speed
        
        # Handle zero velocity (static friction)
        tau_x = np.where(speed > 0.01, tau_x, 0)
        tau_y = np.where(speed > 0.01, tau_y, 0)
        
        return RheologyResult(
            tau_x=tau_x,
            tau_y=tau_y,
            effective_mu=np.full_like(h, self.tan_phi)
        )


class Voellmy(BaseRheology):
    """
    Voellmy-Salm friction model.
    
    τ = μ * ρgh*cos(θ) + ρg * v² / ξ
    
    Combines Coulomb friction with velocity-dependent turbulent friction.
    Standard model for snow/rock avalanches (RAMMS, r.avaflow).
    """
    
    def __init__(self, mu: float = 0.15, xi: float = 500.0):
        """
        Args:
            mu: Coulomb friction coefficient (typically 0.1-0.4)
            xi: Turbulent friction coefficient (m/s², typically 200-2000)
        """
        self.mu = mu
        self.xi = xi
        self.g = 9.81
    
    def compute_basal_stress(self,
                              h: np.ndarray,
                              u: np.ndarray,
                              v: np.ndarray,
                              rho: np.ndarray,
                              slope_x: np.ndarray,
                              slope_y: np.ndarray) -> RheologyResult:
        
        # Slope correction
        slope_mag = np.sqrt(slope_x**2 + slope_y**2)
        cos_theta = 1.0 / np.sqrt(1 + slope_mag**2)
        
        # Normal stress and Coulomb term
        sigma_n = rho * self.g * h * cos_theta
        tau_coulomb = self.mu * sigma_n
        
        # Turbulent term
        speed = np.sqrt(u**2 + v**2)
        tau_turb = rho * self.g * speed**2 / self.xi
        
        # Total friction
        tau_mag = tau_coulomb + tau_turb
        
        # Direction
        speed_safe = speed + 1e-10
        tau_x = -tau_mag * u / speed_safe
        tau_y = -tau_mag * v / speed_safe
        
        # Effective friction coefficient
        with np.errstate(divide='ignore', invalid='ignore'):
            eff_mu = np.where(sigma_n > 0, tau_mag / sigma_n, self.mu)
        
        return RheologyResult(
            tau_x=tau_x,
            tau_y=tau_y,
            effective_mu=np.clip(eff_mu, 0, 2.0)
        )
    
    @classmethod
    def from_preset(cls, preset: str) -> 'Voellmy':
        """
        Create Voellmy model from preset.
        
        Presets:
            'snow_dry': Dry snow avalanche
            'snow_wet': Wet snow avalanche
            'rock': Rock avalanche
            'debris': Debris flow
        """
        presets = {
            'snow_dry': (0.15, 2000),
            'snow_wet': (0.20, 1000),
            'rock': (0.10, 500),
            'debris': (0.12, 400),
        }
        if preset not in presets:
            raise ValueError(f"Unknown preset: {preset}. Available: {list(presets.keys())}")
        
        mu, xi = presets[preset]
        return cls(mu=mu, xi=xi)


class Bingham(BaseRheology):
    """
    Bingham viscoplastic model.
    
    τ = τ_y + η * (v/h)
    
    Suitable for mudflows and lahars.
    """
    
    def __init__(self, yield_stress: float = 100.0, viscosity: float = 50.0):
        """
        Args:
            yield_stress: τ_y in Pa (typically 50-500 for mud)
            viscosity: η in Pa·s (typically 10-100)
        """
        self.tau_y = yield_stress
        self.eta = viscosity
        self.g = 9.81
    
    def compute_basal_stress(self,
                              h: np.ndarray,
                              u: np.ndarray,
                              v: np.ndarray,
                              rho: np.ndarray,
                              slope_x: np.ndarray,
                              slope_y: np.ndarray) -> RheologyResult:
        
        speed = np.sqrt(u**2 + v**2)
        h_safe = np.maximum(h, 0.01)
        
        # Shear rate
        gamma_dot = speed / h_safe
        
        # Bingham stress
        tau_mag = self.tau_y + self.eta * gamma_dot
        
        # Direction
        speed_safe = speed + 1e-10
        tau_x = -tau_mag * u / speed_safe
        tau_y = -tau_mag * v / speed_safe
        
        # Effective friction
        sigma_n = rho * self.g * h
        with np.errstate(divide='ignore', invalid='ignore'):
            eff_mu = np.where(sigma_n > 0, tau_mag / sigma_n, 0.3)
        
        return RheologyResult(
            tau_x=tau_x,
            tau_y=tau_y,
            effective_mu=np.clip(eff_mu, 0, 2.0)
        )


class HerschelBulkley(BaseRheology):
    """
    Herschel-Bulkley viscoplastic model.
    
    τ = τ_y + K * (γ̇)^n
    
    Generalization of Bingham model with power-law behavior.
    """
    
    def __init__(self, yield_stress: float = 100.0, 
                 consistency: float = 50.0,
                 flow_index: float = 0.5):
        """
        Args:
            yield_stress: τ_y in Pa
            consistency: K (Pa·s^n)
            flow_index: n (0.5 = shear-thinning, 1 = Bingham, 1.5 = shear-thickening)
        """
        self.tau_y = yield_stress
        self.K = consistency
        self.n = flow_index
        self.g = 9.81
    
    def compute_basal_stress(self,
                              h: np.ndarray,
                              u: np.ndarray,
                              v: np.ndarray,
                              rho: np.ndarray,
                              slope_x: np.ndarray,
                              slope_y: np.ndarray) -> RheologyResult:
        
        speed = np.sqrt(u**2 + v**2)
        h_safe = np.maximum(h, 0.01)
        
        # Shear rate
        gamma_dot = speed / h_safe
        
        # Herschel-Bulkley stress
        tau_mag = self.tau_y + self.K * np.power(gamma_dot + 1e-6, self.n)
        
        # Direction
        speed_safe = speed + 1e-10
        tau_x = -tau_mag * u / speed_safe
        tau_y = -tau_mag * v / speed_safe
        
        # Effective friction
        sigma_n = rho * self.g * h
        with np.errstate(divide='ignore', invalid='ignore'):
            eff_mu = np.where(sigma_n > 0, tau_mag / sigma_n, 0.3)
        
        return RheologyResult(
            tau_x=tau_x,
            tau_y=tau_y,
            effective_mu=np.clip(eff_mu, 0, 2.0)
        )


def test_rheology():
    """Test rheology models."""
    print("=" * 50)
    print("Testing Rheology Models")
    print("=" * 50)
    
    # Test data
    shape = (10, 10)
    h = np.ones(shape) * 2.0  # 2m height
    u = np.ones(shape) * 5.0  # 5 m/s
    v = np.ones(shape) * 3.0  # 3 m/s
    rho = np.ones(shape) * 2000.0  # 2000 kg/m³
    slope_x = np.ones(shape) * 0.2
    slope_y = np.ones(shape) * 0.3
    
    # Test each model
    models = [
        ("Mohr-Coulomb", MohrCoulomb(friction_angle=25.0)),
        ("Voellmy", Voellmy(mu=0.15, xi=500.0)),
        ("Bingham", Bingham(yield_stress=100.0, viscosity=50.0)),
        ("Herschel-Bulkley", HerschelBulkley(yield_stress=100.0, consistency=50.0, flow_index=0.5)),
    ]
    
    for name, model in models:
        result = model.compute_basal_stress(h, u, v, rho, slope_x, slope_y)
        tau = np.sqrt(result.tau_x**2 + result.tau_y**2)[5, 5]
        mu_eff = result.effective_mu[5, 5]
        print(f"\n{name}:")
        print(f"  τ = {tau:.0f} Pa")
        print(f"  μ_eff = {mu_eff:.3f}")
    
    # Test Voellmy preset
    voellmy_rock = Voellmy.from_preset('rock')
    print(f"\nVoellmy 'rock' preset: μ={voellmy_rock.mu}, ξ={voellmy_rock.xi}")
    
    print("\n✓ Rheology tests passed!")
    return True


if __name__ == "__main__":
    test_rheology()
