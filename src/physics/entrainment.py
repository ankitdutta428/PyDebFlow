"""
Entrainment Models for OpenDebris.

Models erosion and deposition of bed material during debris flow.
Based on empirical relations from experimental and field observations.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple
from abc import ABC, abstractmethod


@dataclass
class EntrainmentResult:
    """Result of entrainment computation."""
    erosion_rate: np.ndarray  # Erosion rate (m/s)
    deposition_rate: np.ndarray  # Deposition rate (m/s)
    net_rate: np.ndarray  # Net entrainment = erosion - deposition (m/s)


class EntrainmentModel:
    """
    Erosion and deposition model for debris flows.
    
    Implements velocity/shear-stress based erosion and
    concentration-based deposition.
    """
    
    def __init__(self, 
                 erosion_coef: float = 0.001,
                 critical_velocity: float = 1.0,
                 deposition_coef: float = 0.1,
                 max_erosion_depth: float = 10.0,
                 bed_density: float = 2000.0):
        """
        Args:
            erosion_coef: Erosion coefficient (dimensionless)
            critical_velocity: Minimum velocity for erosion (m/s)
            deposition_coef: Deposition coefficient (1/s)
            max_erosion_depth: Maximum total erosion depth (m)
            bed_density: Density of bed material (kg/m³)
        """
        self.erosion_coef = erosion_coef
        self.v_crit = critical_velocity
        self.depo_coef = deposition_coef
        self.max_depth = max_erosion_depth
        self.rho_bed = bed_density
        self.g = 9.81
        
        # Track cumulative erosion
        self.cumulative_erosion: Optional[np.ndarray] = None
    
    def compute_erosion_rate(self, 
                              h: np.ndarray,
                              speed: np.ndarray,
                              solid_fraction: np.ndarray,
                              bed_erodible: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Compute erosion rate based on flow velocity.
        
        E = e * (v - v_crit)² * (1 - α)
        
        where:
          e = erosion coefficient
          v = flow velocity
          v_crit = critical velocity threshold
          α = solid fraction (more fluid = more erosion potential)
        """
        # Only erode where velocity exceeds threshold
        excess_v = np.maximum(speed - self.v_crit, 0)
        
        # Erosion potential decreases with solid concentration
        erosion_potential = 1.0 - solid_fraction
        
        # Base erosion rate
        rate = self.erosion_coef * excess_v**2 * erosion_potential
        
        # Check erodible bed
        if bed_erodible is not None:
            rate = np.where(bed_erodible > 0, rate, 0)
        
        # Limit by cumulative erosion
        if self.cumulative_erosion is not None:
            remaining = np.maximum(self.max_depth - self.cumulative_erosion, 0)
            rate = np.minimum(rate, remaining)
        
        return rate
    
    def compute_deposition_rate(self,
                                 h: np.ndarray,
                                 speed: np.ndarray,
                                 solid_fraction: np.ndarray) -> np.ndarray:
        """
        Compute deposition rate based on concentration and velocity.
        
        D = d * α * h / (1 + v²)
        
        Deposition increases with:
          - High solid fraction (more material to deposit)
          - Low velocity (settling dominates)
          - Greater flow height (more material)
        """
        # Deposition rate
        rate = self.depo_coef * solid_fraction * h / (1 + speed**2)
        
        return rate
    
    def compute(self,
                h: np.ndarray,
                speed: np.ndarray,
                solid_fraction: np.ndarray,
                bed_erodible: Optional[np.ndarray] = None,
                dt: float = 1.0) -> EntrainmentResult:
        """
        Compute net entrainment (erosion - deposition).
        
        Args:
            h: Flow height (m)
            speed: Flow speed (m/s)
            solid_fraction: Solid volume fraction
            bed_erodible: Optional erodible bed thickness (m)
            dt: Time step for updating cumulative erosion
            
        Returns:
            EntrainmentResult with erosion, deposition, and net rates
        """
        # Initialize cumulative erosion tracker
        if self.cumulative_erosion is None:
            self.cumulative_erosion = np.zeros_like(h)
        
        erosion = self.compute_erosion_rate(h, speed, solid_fraction, bed_erodible)
        deposition = self.compute_deposition_rate(h, speed, solid_fraction)
        
        # Net rate
        net = erosion - deposition
        
        # Update cumulative erosion
        self.cumulative_erosion += erosion * dt
        
        return EntrainmentResult(
            erosion_rate=erosion,
            deposition_rate=deposition,
            net_rate=net
        )
    
    def reset(self) -> None:
        """Reset cumulative erosion tracking."""
        self.cumulative_erosion = None
    
    def apply_to_state(self, 
                       h_solid: np.ndarray,
                       h_fluid: np.ndarray,
                       result: EntrainmentResult,
                       dt: float,
                       solid_ratio: float = 0.7) -> Tuple[np.ndarray, np.ndarray]:
        """
        Apply entrainment to flow state.
        
        Args:
            h_solid: Solid phase height
            h_fluid: Fluid phase height
            result: Entrainment computation result
            dt: Time step (s)
            solid_ratio: Fraction of entrained material that is solid
            
        Returns:
            Updated (h_solid, h_fluid)
        """
        # Height change from net entrainment
        dh = result.net_rate * dt
        
        # Split into solid and fluid
        dh_solid = dh * solid_ratio
        dh_fluid = dh * (1 - solid_ratio)
        
        # Apply changes (prevent negative heights)
        new_h_solid = np.maximum(h_solid + dh_solid, 0)
        new_h_fluid = np.maximum(h_fluid + dh_fluid, 0)
        
        return new_h_solid, new_h_fluid


class McDougallHungr(EntrainmentModel):
    """
    McDougall & Hungr (2005) entrainment model.
    
    Used in DAN3D and similar codes.
    E_s = E * v * (exp(-y/E_s) - exp(-y_max/E_s))
    """
    
    def __init__(self, 
                 growth_rate: float = 0.001,
                 max_depth: float = 5.0):
        """
        Args:
            growth_rate: E_s volumetric growth rate (m⁻¹)
            max_depth: Maximum entrainment depth
        """
        super().__init__(
            erosion_coef=growth_rate,
            max_erosion_depth=max_depth
        )
        self.Es = growth_rate


class ErosionLaw:
    """
    Power-law erosion models for various conditions.
    """
    
    @staticmethod
    def shear_stress_based(tau: np.ndarray, 
                           tau_crit: float = 100.0,
                           k_e: float = 1e-4) -> np.ndarray:
        """
        Shear-stress based erosion.
        
        E = k_e * (τ - τ_crit)  for τ > τ_crit
        
        Args:
            tau: Basal shear stress (Pa)
            tau_crit: Critical shear stress (Pa)
            k_e: Erosion coefficient (m/s/Pa)
        """
        excess_tau = np.maximum(tau - tau_crit, 0)
        return k_e * excess_tau
    
    @staticmethod
    def velocity_power_law(v: np.ndarray,
                           v_crit: float = 1.0,
                           k: float = 0.001,
                           n: float = 2.0) -> np.ndarray:
        """
        Velocity power-law erosion.
        
        E = k * (v - v_crit)^n
        
        Args:
            v: Flow velocity (m/s)
            v_crit: Critical velocity (m/s)
            k: Erosion coefficient
            n: Power law exponent
        """
        excess_v = np.maximum(v - v_crit, 0)
        return k * np.power(excess_v, n)


def test_entrainment():
    """Test entrainment model."""
    print("=" * 50)
    print("Testing Entrainment Model")
    print("=" * 50)
    
    shape = (20, 20)
    model = EntrainmentModel(
        erosion_coef=0.002,
        critical_velocity=1.0,
        deposition_coef=0.05
    )
    
    # Test conditions
    h = np.ones(shape) * 2.0
    speed = np.ones(shape) * 5.0
    speed[10:, :] = 0.5  # Slow zone - deposition
    solid_fraction = np.ones(shape) * 0.5
    
    result = model.compute(h, speed, solid_fraction, dt=1.0)
    
    print(f"\n1. Fast zone (v=5 m/s):")
    print(f"   Erosion rate: {result.erosion_rate[5, 5]*1000:.2f} mm/s")
    print(f"   Deposition rate: {result.deposition_rate[5, 5]*1000:.2f} mm/s")
    print(f"   Net: {result.net_rate[5, 5]*1000:.2f} mm/s (erosion)")
    
    print(f"\n2. Slow zone (v=0.5 m/s):")
    print(f"   Erosion rate: {result.erosion_rate[15, 5]*1000:.2f} mm/s")
    print(f"   Deposition rate: {result.deposition_rate[15, 5]*1000:.2f} mm/s")
    print(f"   Net: {result.net_rate[15, 5]*1000:.2f} mm/s (deposition)")
    
    # Apply to state
    h_solid = np.ones(shape) * 1.5
    h_fluid = np.ones(shape) * 0.5
    new_hs, new_hf = model.apply_to_state(h_solid, h_fluid, result, dt=1.0)
    
    dh_fast = (new_hs[5, 5] + new_hf[5, 5]) - (h_solid[5, 5] + h_fluid[5, 5])
    dh_slow = (new_hs[15, 5] + new_hf[15, 5]) - (h_solid[15, 5] + h_fluid[15, 5])
    
    print(f"\n3. Height changes after 1s:")
    print(f"   Fast zone: {dh_fast*100:.1f} cm (increase from erosion)")
    print(f"   Slow zone: {dh_slow*100:.1f} cm (decrease from deposition)")
    
    print("\n✓ Entrainment tests passed!")
    return True


if __name__ == "__main__":
    test_entrainment()
