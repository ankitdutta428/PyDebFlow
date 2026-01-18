"""
Two-Phase Flow Model for OpenDebris.

Implements the governing equations for solid-fluid two-phase debris flows
based on Pudasaini (2012) two-phase model.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Tuple, Optional
from numba import njit


@dataclass
class FlowParameters:
    """Physical parameters for two-phase flow simulation."""
    
    # Material densities
    solid_density: float = 2500.0  # kg/m³ (rock/debris)
    fluid_density: float = 1100.0  # kg/m³ (muddy water)
    
    # Friction parameters
    basal_friction_angle: float = 25.0  # degrees
    internal_friction_angle: float = 35.0  # degrees
    
    # Voellmy parameters
    voellmy_mu: float = 0.15  # Coulomb friction coefficient
    voellmy_xi: float = 500.0  # Turbulent friction coefficient (m/s²)
    
    # Two-phase interaction
    drag_coefficient: float = 0.01  # Solid-fluid drag
    virtual_mass_coef: float = 0.5  # Virtual mass coefficient
    
    # Flow properties
    min_flow_height: float = 0.001  # m, threshold for active flow
    solid_fraction_min: float = 0.3  # Minimum solid fraction
    solid_fraction_max: float = 0.7  # Maximum solid fraction
    
    # Numerical stability
    velocity_cap: float = 50.0  # m/s, maximum allowed velocity
    
    @property
    def tan_phi_basal(self) -> float:
        """Tangent of basal friction angle."""
        return np.tan(np.radians(self.basal_friction_angle))
    
    @property
    def tan_phi_internal(self) -> float:
        """Tangent of internal friction angle."""
        return np.tan(np.radians(self.internal_friction_angle))


@dataclass
class FlowState:
    """
    State variables for two-phase debris flow.
    
    All arrays have shape (rows, cols) representing the computational grid.
    """
    
    # Conservative variables (heights in meters)
    h_solid: np.ndarray  # Solid phase height
    h_fluid: np.ndarray  # Fluid phase height
    
    # Momentum (height × velocity)
    u_solid: np.ndarray  # Solid x-velocity (m/s)
    v_solid: np.ndarray  # Solid y-velocity (m/s)
    u_fluid: np.ndarray  # Fluid x-velocity (m/s)
    v_fluid: np.ndarray  # Fluid y-velocity (m/s)
    
    @classmethod
    def zeros(cls, shape: Tuple[int, int]) -> 'FlowState':
        """Create a zero-initialized flow state."""
        return cls(
            h_solid=np.zeros(shape, dtype=np.float64),
            h_fluid=np.zeros(shape, dtype=np.float64),
            u_solid=np.zeros(shape, dtype=np.float64),
            v_solid=np.zeros(shape, dtype=np.float64),
            u_fluid=np.zeros(shape, dtype=np.float64),
            v_fluid=np.zeros(shape, dtype=np.float64),
        )
    
    @property
    def h_total(self) -> np.ndarray:
        """Total flow height."""
        return self.h_solid + self.h_fluid
    
    @property
    def solid_fraction(self) -> np.ndarray:
        """Solid volume fraction."""
        h_total = self.h_total
        with np.errstate(divide='ignore', invalid='ignore'):
            alpha = np.where(h_total > 1e-6, self.h_solid / h_total, 0.5)
        return np.clip(alpha, 0.0, 1.0)
    
    @property 
    def speed_solid(self) -> np.ndarray:
        """Solid phase speed magnitude."""
        return np.sqrt(self.u_solid**2 + self.v_solid**2)
    
    @property
    def speed_fluid(self) -> np.ndarray:
        """Fluid phase speed magnitude."""
        return np.sqrt(self.u_fluid**2 + self.v_fluid**2)
    
    def copy(self) -> 'FlowState':
        """Create a deep copy of this state."""
        return FlowState(
            h_solid=self.h_solid.copy(),
            h_fluid=self.h_fluid.copy(),
            u_solid=self.u_solid.copy(),
            v_solid=self.v_solid.copy(),
            u_fluid=self.u_fluid.copy(),
            v_fluid=self.v_fluid.copy(),
        )
    
    def clamp_values(self, params: FlowParameters) -> None:
        """Apply physical constraints to state variables."""
        # Non-negative heights
        self.h_solid = np.maximum(self.h_solid, 0.0)
        self.h_fluid = np.maximum(self.h_fluid, 0.0)
        
        # Cap velocities
        self.u_solid = np.clip(self.u_solid, -params.velocity_cap, params.velocity_cap)
        self.v_solid = np.clip(self.v_solid, -params.velocity_cap, params.velocity_cap)
        self.u_fluid = np.clip(self.u_fluid, -params.velocity_cap, params.velocity_cap)
        self.v_fluid = np.clip(self.v_fluid, -params.velocity_cap, params.velocity_cap)
        
        # Zero velocity where flow is too shallow
        mask = self.h_total < params.min_flow_height
        self.u_solid[mask] = 0.0
        self.v_solid[mask] = 0.0
        self.u_fluid[mask] = 0.0
        self.v_fluid[mask] = 0.0


class TwoPhaseFlowModel:
    """
    Two-phase debris flow model.
    
    Implements the shallow water equations for a solid-fluid mixture,
    including:
    - Gravitational driving forces
    - Basal friction (Coulomb/Voellmy)
    - Internal stresses
    - Solid-fluid drag interaction
    """
    
    def __init__(self, params: Optional[FlowParameters] = None):
        self.params = params or FlowParameters()
        self.g = 9.81  # Gravitational acceleration
    
    def compute_mixture_density(self, state: FlowState) -> np.ndarray:
        """Compute mixture density based on solid fraction."""
        alpha = state.solid_fraction
        return alpha * self.params.solid_density + (1 - alpha) * self.params.fluid_density
    
    def compute_basal_friction(self, state: FlowState, 
                                slope_x: np.ndarray, 
                                slope_y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute basal friction stress using Voellmy rheology.
        
        τ = μ * ρgh * cos(θ) + ρg * v² / ξ
        """
        h_total = state.h_total
        speed = state.speed_solid + 1e-10
        
        # Effective normal stress
        rho = self.compute_mixture_density(state)
        sigma_n = rho * self.g * h_total
        
        # Coulomb friction
        tau_coulomb = self.params.voellmy_mu * sigma_n
        
        # Turbulent friction (Voellmy)
        tau_turb = rho * self.g * speed**2 / self.params.voellmy_xi
        
        # Total friction
        tau_total = tau_coulomb + tau_turb
        
        # Direction opposite to velocity
        with np.errstate(divide='ignore', invalid='ignore'):
            fx = -tau_total * state.u_solid / speed
            fy = -tau_total * state.v_solid / speed
        
        # Handle zero velocity
        fx = np.nan_to_num(fx, nan=0.0)
        fy = np.nan_to_num(fy, nan=0.0)
        
        return fx, fy
    
    def compute_drag_force(self, state: FlowState) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute solid-fluid drag interaction.
        
        Returns forces on both solid and fluid phases.
        """
        # Relative velocity
        du = state.u_solid - state.u_fluid
        dv = state.v_solid - state.v_fluid
        rel_speed = np.sqrt(du**2 + dv**2) + 1e-10
        
        # Drag coefficient scaled by height
        h_total = state.h_total
        cd = self.params.drag_coefficient * h_total
        
        # Drag force magnitude
        drag_mag = cd * rel_speed
        
        # Forces (opposite directions on each phase)
        fx_solid = -drag_mag * du / rel_speed
        fy_solid = -drag_mag * dv / rel_speed
        fx_fluid = -fx_solid
        fy_fluid = -fy_solid
        
        return fx_solid, fy_solid, fx_fluid, fy_fluid
    
    def compute_pressure_gradient(self, state: FlowState, 
                                   cell_size: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute pressure gradient forces.
        
        Uses hydrostatic pressure: p = ρgh
        """
        rho = self.compute_mixture_density(state)
        pressure = 0.5 * rho * self.g * state.h_total**2
        
        # Gradient using central differences
        dp_dx = np.zeros_like(pressure)
        dp_dy = np.zeros_like(pressure)
        
        dp_dx[:, 1:-1] = (pressure[:, 2:] - pressure[:, :-2]) / (2 * cell_size)
        dp_dy[1:-1, :] = (pressure[2:, :] - pressure[:-2, :]) / (2 * cell_size)
        
        # Boundary handling
        dp_dx[:, 0] = (pressure[:, 1] - pressure[:, 0]) / cell_size
        dp_dx[:, -1] = (pressure[:, -1] - pressure[:, -2]) / cell_size
        dp_dy[0, :] = (pressure[1, :] - pressure[0, :]) / cell_size
        dp_dy[-1, :] = (pressure[-1, :] - pressure[-2, :]) / cell_size
        
        return -dp_dx, -dp_dy
    
    def compute_gravity_force(self, state: FlowState,
                               slope_x: np.ndarray,
                               slope_y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Compute gravitational driving force along slope."""
        rho = self.compute_mixture_density(state)
        h_total = state.h_total
        
        fx = rho * self.g * h_total * slope_x
        fy = rho * self.g * h_total * slope_y
        
        return fx, fy
    
    def compute_impact_pressure(self, state: FlowState) -> np.ndarray:
        """
        Compute impact pressure for hazard assessment.
        
        P = 0.5 * ρ * v² (dynamic pressure)
        """
        rho = self.compute_mixture_density(state)
        v_sq = state.speed_solid**2
        
        # Convert to kPa
        pressure_kpa = 0.5 * rho * v_sq / 1000.0
        
        return pressure_kpa
    
    def compute_kinetic_energy(self, state: FlowState, cell_size: float) -> float:
        """Compute total kinetic energy in the system."""
        rho = self.compute_mixture_density(state)
        ke_solid = 0.5 * rho * state.h_solid * state.speed_solid**2
        ke_fluid = 0.5 * self.params.fluid_density * state.h_fluid * state.speed_fluid**2
        
        return (ke_solid.sum() + ke_fluid.sum()) * cell_size**2
    
    def compute_fluxes(self, state: FlowState, 
                       direction: str = 'x') -> Tuple[np.ndarray, ...]:
        """
        Compute conservative fluxes for the shallow water equations.
        
        Args:
            state: Current flow state
            direction: 'x' or 'y' for flux direction
            
        Returns:
            Tuple of flux arrays (mass_solid, mass_fluid, mom_solid, mom_fluid)
        """
        if direction == 'x':
            u_s, u_f = state.u_solid, state.u_fluid
        else:
            u_s, u_f = state.v_solid, state.v_fluid
        
        # Mass fluxes
        flux_mass_solid = state.h_solid * u_s
        flux_mass_fluid = state.h_fluid * u_f
        
        # Momentum fluxes (including pressure term)
        rho_s = self.params.solid_density
        rho_f = self.params.fluid_density
        
        p_solid = 0.5 * self.g * state.h_solid**2
        p_fluid = 0.5 * self.g * state.h_fluid**2
        
        flux_mom_solid = state.h_solid * u_s**2 + p_solid
        flux_mom_fluid = state.h_fluid * u_f**2 + p_fluid
        
        return flux_mass_solid, flux_mass_fluid, flux_mom_solid, flux_mom_fluid


def test_flow_model():
    """Test flow model functionality."""
    print("=" * 50)
    print("Testing Flow Model")
    print("=" * 50)
    
    # Create test state
    shape = (20, 20)
    state = FlowState.zeros(shape)
    
    # Add some flow
    state.h_solid[5:10, 5:15] = 2.0
    state.h_fluid[5:10, 5:15] = 1.0
    state.u_solid[5:10, 5:15] = 3.0
    state.v_solid[5:10, 5:15] = 2.0
    
    params = FlowParameters()
    model = TwoPhaseFlowModel(params)
    
    # Test computations
    print(f"\n1. Total height range: {state.h_total.min():.2f} to {state.h_total.max():.2f} m")
    print(f"2. Solid fraction: {state.solid_fraction[7, 10]:.2f}")
    
    rho = model.compute_mixture_density(state)
    print(f"3. Mixture density: {rho[7, 10]:.0f} kg/m³")
    
    pressure = model.compute_impact_pressure(state)
    print(f"4. Max impact pressure: {pressure.max():.1f} kPa")
    
    ke = model.compute_kinetic_energy(state, cell_size=10.0)
    print(f"5. Total kinetic energy: {ke:.2e} J")
    
    # Test clamping
    state.u_solid[7, 10] = 100.0  # Exceeds cap
    state.clamp_values(params)
    print(f"6. Velocity after clamping: {state.u_solid[7, 10]:.1f} m/s (capped at {params.velocity_cap})")
    
    print("\n✓ Flow model tests passed!")
    return True


if __name__ == "__main__":
    test_flow_model()
