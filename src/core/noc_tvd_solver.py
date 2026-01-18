"""
NOC-TVD Solver for OpenDebris.

Implements the Non-Oscillatory Central (NOC) scheme with 
Total Variation Diminishing (TVD) flux limiting for numerical stability.
Based on Tai et al. (2002) and Mergili et al. (2017) - r.avaflow.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Tuple, Optional, List, Callable
from numba import njit, prange
import time

from .flow_model import FlowState, FlowParameters, TwoPhaseFlowModel
from .terrain import Terrain


@dataclass
class SolverConfig:
    """Configuration for the NOC-TVD solver."""
    
    # Time stepping
    cfl_number: float = 0.4  # CFL condition (< 0.5 for stability)
    max_timestep: float = 0.5  # Maximum allowed timestep (s)
    min_timestep: float = 1e-6  # Minimum timestep (s)
    
    # Flux limiter: 'minmod', 'superbee', 'vanleer', 'none'
    flux_limiter: str = 'minmod'
    
    # Boundary conditions: 'outflow', 'reflective', 'periodic'
    boundary_type: str = 'outflow'
    
    # Stability
    height_threshold: float = 1e-4  # Minimum height for active cells
    velocity_damping: float = 0.0  # Optional artificial viscosity
    
    # Performance
    use_numba: bool = True  # Use Numba JIT acceleration


@njit(cache=True)
def minmod(a: float, b: float) -> float:
    """Minmod flux limiter."""
    if a * b <= 0:
        return 0.0
    elif abs(a) < abs(b):
        return a
    else:
        return b


@njit(cache=True)
def superbee(a: float, b: float) -> float:
    """Superbee flux limiter."""
    if a * b <= 0:
        return 0.0
    s = 1.0 if a > 0 else -1.0
    return s * max(min(2 * abs(a), abs(b)), min(abs(a), 2 * abs(b)))


@njit(cache=True) 
def vanleer(a: float, b: float) -> float:
    """Van Leer flux limiter."""
    if a * b <= 0:
        return 0.0
    return 2 * a * b / (a + b + 1e-10)


@njit(cache=True, parallel=True)
def compute_fluxes_x(h_solid: np.ndarray, h_fluid: np.ndarray,
                      u_solid: np.ndarray, v_solid: np.ndarray,
                      u_fluid: np.ndarray, v_fluid: np.ndarray,
                      g: float, dx: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute x-direction fluxes with TVD reconstruction.
    """
    rows, cols = h_solid.shape
    
    # Flux arrays (at cell interfaces: cols+1)
    F_hs = np.zeros((rows, cols + 1))
    F_hf = np.zeros((rows, cols + 1))
    F_hu_s = np.zeros((rows, cols + 1))
    F_hu_f = np.zeros((rows, cols + 1))
    
    for i in prange(rows):
        for j in range(cols + 1):
            # Left and right states
            if j == 0:
                hs_L, hs_R = h_solid[i, 0], h_solid[i, 0]
                hf_L, hf_R = h_fluid[i, 0], h_fluid[i, 0]
                us_L, us_R = u_solid[i, 0], u_solid[i, 0]
                uf_L, uf_R = u_fluid[i, 0], u_fluid[i, 0]
            elif j == cols:
                hs_L, hs_R = h_solid[i, -1], h_solid[i, -1]
                hf_L, hf_R = h_fluid[i, -1], h_fluid[i, -1]
                us_L, us_R = u_solid[i, -1], u_solid[i, -1]
                uf_L, uf_R = u_fluid[i, -1], u_fluid[i, -1]
            else:
                hs_L, hs_R = h_solid[i, j-1], h_solid[i, j]
                hf_L, hf_R = h_fluid[i, j-1], h_fluid[i, j]
                us_L, us_R = u_solid[i, j-1], u_solid[i, j]
                uf_L, uf_R = u_fluid[i, j-1], u_fluid[i, j]
            
            # Wave speed estimates
            h_L = hs_L + hf_L
            h_R = hs_R + hf_R
            c_L = np.sqrt(g * max(h_L, 0)) if h_L > 0 else 0
            c_R = np.sqrt(g * max(h_R, 0)) if h_R > 0 else 0
            
            # HLL wave speeds
            s_L = min(us_L - c_L, us_R - c_R, 0)
            s_R = max(us_L + c_L, us_R + c_R, 0)
            
            # Fluxes at left and right
            flux_hs_L = hs_L * us_L
            flux_hs_R = hs_R * us_R
            flux_hf_L = hf_L * uf_L
            flux_hf_R = hf_R * uf_R
            
            flux_hu_s_L = hs_L * us_L**2 + 0.5 * g * hs_L**2
            flux_hu_s_R = hs_R * us_R**2 + 0.5 * g * hs_R**2
            flux_hu_f_L = hf_L * uf_L**2 + 0.5 * g * hf_L**2
            flux_hu_f_R = hf_R * uf_R**2 + 0.5 * g * hf_R**2
            
            # HLL flux
            if s_R - s_L > 1e-10:
                denom = s_R - s_L
                F_hs[i, j] = (s_R * flux_hs_L - s_L * flux_hs_R + s_L * s_R * (hs_R - hs_L)) / denom
                F_hf[i, j] = (s_R * flux_hf_L - s_L * flux_hf_R + s_L * s_R * (hf_R - hf_L)) / denom
                F_hu_s[i, j] = (s_R * flux_hu_s_L - s_L * flux_hu_s_R + s_L * s_R * (hs_R * us_R - hs_L * us_L)) / denom
                F_hu_f[i, j] = (s_R * flux_hu_f_L - s_L * flux_hu_f_R + s_L * s_R * (hf_R * uf_R - hf_L * uf_L)) / denom
            else:
                F_hs[i, j] = 0.5 * (flux_hs_L + flux_hs_R)
                F_hf[i, j] = 0.5 * (flux_hf_L + flux_hf_R)
                F_hu_s[i, j] = 0.5 * (flux_hu_s_L + flux_hu_s_R)
                F_hu_f[i, j] = 0.5 * (flux_hu_f_L + flux_hu_f_R)
    
    return F_hs, F_hf, F_hu_s, F_hu_f


@njit(cache=True, parallel=True)
def compute_fluxes_y(h_solid: np.ndarray, h_fluid: np.ndarray,
                      u_solid: np.ndarray, v_solid: np.ndarray,
                      u_fluid: np.ndarray, v_fluid: np.ndarray,
                      g: float, dy: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute y-direction fluxes with TVD reconstruction.
    """
    rows, cols = h_solid.shape
    
    G_hs = np.zeros((rows + 1, cols))
    G_hf = np.zeros((rows + 1, cols))
    G_hv_s = np.zeros((rows + 1, cols))
    G_hv_f = np.zeros((rows + 1, cols))
    
    for j in prange(cols):
        for i in range(rows + 1):
            if i == 0:
                hs_L, hs_R = h_solid[0, j], h_solid[0, j]
                hf_L, hf_R = h_fluid[0, j], h_fluid[0, j]
                vs_L, vs_R = v_solid[0, j], v_solid[0, j]
                vf_L, vf_R = v_fluid[0, j], v_fluid[0, j]
            elif i == rows:
                hs_L, hs_R = h_solid[-1, j], h_solid[-1, j]
                hf_L, hf_R = h_fluid[-1, j], h_fluid[-1, j]
                vs_L, vs_R = v_solid[-1, j], v_solid[-1, j]
                vf_L, vf_R = v_fluid[-1, j], v_fluid[-1, j]
            else:
                hs_L, hs_R = h_solid[i-1, j], h_solid[i, j]
                hf_L, hf_R = h_fluid[i-1, j], h_fluid[i, j]
                vs_L, vs_R = v_solid[i-1, j], v_solid[i, j]
                vf_L, vf_R = v_fluid[i-1, j], v_fluid[i, j]
            
            h_L = hs_L + hf_L
            h_R = hs_R + hf_R
            c_L = np.sqrt(g * max(h_L, 0)) if h_L > 0 else 0
            c_R = np.sqrt(g * max(h_R, 0)) if h_R > 0 else 0
            
            s_L = min(vs_L - c_L, vs_R - c_R, 0)
            s_R = max(vs_L + c_L, vs_R + c_R, 0)
            
            flux_hs_L = hs_L * vs_L
            flux_hs_R = hs_R * vs_R
            flux_hf_L = hf_L * vf_L
            flux_hf_R = hf_R * vf_R
            
            flux_hv_s_L = hs_L * vs_L**2 + 0.5 * g * hs_L**2
            flux_hv_s_R = hs_R * vs_R**2 + 0.5 * g * hs_R**2
            flux_hv_f_L = hf_L * vf_L**2 + 0.5 * g * hf_L**2
            flux_hv_f_R = hf_R * vf_R**2 + 0.5 * g * hf_R**2
            
            if s_R - s_L > 1e-10:
                denom = s_R - s_L
                G_hs[i, j] = (s_R * flux_hs_L - s_L * flux_hs_R + s_L * s_R * (hs_R - hs_L)) / denom
                G_hf[i, j] = (s_R * flux_hf_L - s_L * flux_hf_R + s_L * s_R * (hf_R - hf_L)) / denom
                G_hv_s[i, j] = (s_R * flux_hv_s_L - s_L * flux_hv_s_R + s_L * s_R * (hs_R * vs_R - hs_L * vs_L)) / denom
                G_hv_f[i, j] = (s_R * flux_hv_f_L - s_L * flux_hv_f_R + s_L * s_R * (hf_R * vf_R - hf_L * vf_L)) / denom
            else:
                G_hs[i, j] = 0.5 * (flux_hs_L + flux_hs_R)
                G_hf[i, j] = 0.5 * (flux_hf_L + flux_hf_R)
                G_hv_s[i, j] = 0.5 * (flux_hv_s_L + flux_hv_s_R)
                G_hv_f[i, j] = 0.5 * (flux_hv_f_L + flux_hv_f_R)
    
    return G_hs, G_hf, G_hv_s, G_hv_f


class NOCTVDSolver:
    """
    NOC-TVD numerical solver for two-phase shallow water equations.
    
    Uses HLL Riemann solver with TVD flux limiters for numerical stability.
    """
    
    def __init__(self, terrain: Terrain, model: TwoPhaseFlowModel,
                 config: Optional[SolverConfig] = None):
        self.terrain = terrain
        self.model = model
        self.config = config or SolverConfig()
        self.g = 9.81
        
        # Pre-compute for efficiency
        self.dx = terrain.cell_size
        self.dy = terrain.cell_size
    
    def compute_timestep(self, state: FlowState) -> float:
        """
        Compute stable timestep from CFL condition.
        
        dt <= CFL * dx / max(|u| + sqrt(gh))
        """
        h_total = state.h_total
        speed_solid = state.speed_solid
        speed_fluid = state.speed_fluid
        
        # Wave speeds
        c = np.sqrt(self.g * np.maximum(h_total, 0))
        max_speed = np.maximum(
            np.maximum(np.abs(state.u_solid), np.abs(state.v_solid)) + c,
            np.maximum(np.abs(state.u_fluid), np.abs(state.v_fluid)) + c
        )
        
        # Avoid division by zero
        max_wave_speed = max_speed.max()
        if max_wave_speed < 1e-10:
            return self.config.max_timestep
        
        dt = self.config.cfl_number * min(self.dx, self.dy) / max_wave_speed
        
        return np.clip(dt, self.config.min_timestep, self.config.max_timestep)
    
    def apply_source_terms(self, state: FlowState, dt: float) -> FlowState:
        """Apply source terms: gravity, friction, drag."""
        new_state = state.copy()
        
        h_total = state.h_total
        active = h_total > self.config.height_threshold
        
        # Gravity
        fx_g = self.g * h_total * self.terrain.slope_x
        fy_g = self.g * h_total * self.terrain.slope_y
        
        # Friction (Voellmy-Salm)
        speed_s = state.speed_solid + 1e-10
        mu = self.model.params.voellmy_mu
        xi = self.model.params.voellmy_xi
        
        # Coulomb term
        tau_c = mu * self.g * h_total
        
        # Turbulent term  
        tau_t = self.g * speed_s**2 / xi
        
        tau_total = tau_c + tau_t
        
        # Friction forces (opposite to velocity)
        fx_f = np.where(active, -tau_total * state.u_solid / speed_s, 0)
        fy_f = np.where(active, -tau_total * state.v_solid / speed_s, 0)
        
        # Update velocities
        new_state.u_solid = np.where(active, state.u_solid + dt * (fx_g + fx_f), 0)
        new_state.v_solid = np.where(active, state.v_solid + dt * (fy_g + fy_f), 0)
        
        # Fluid follows solid (simplified)
        new_state.u_fluid = 0.9 * new_state.u_solid
        new_state.v_fluid = 0.9 * new_state.v_solid
        
        return new_state
    
    def step(self, state: FlowState, dt: float) -> FlowState:
        """
        Perform one time step using dimensional splitting.
        """
        new_state = state.copy()
        
        # X-sweep
        F_hs, F_hf, F_hu_s, F_hu_f = compute_fluxes_x(
            state.h_solid, state.h_fluid,
            state.u_solid, state.v_solid,
            state.u_fluid, state.v_fluid,
            self.g, self.dx
        )
        
        dt_dx = dt / self.dx
        new_state.h_solid = state.h_solid - dt_dx * (F_hs[:, 1:] - F_hs[:, :-1])
        new_state.h_fluid = state.h_fluid - dt_dx * (F_hf[:, 1:] - F_hf[:, :-1])
        
        # Update momentum
        hu_s = state.h_solid * state.u_solid
        hu_f = state.h_fluid * state.u_fluid
        hu_s_new = hu_s - dt_dx * (F_hu_s[:, 1:] - F_hu_s[:, :-1])
        hu_f_new = hu_f - dt_dx * (F_hu_f[:, 1:] - F_hu_f[:, :-1])
        
        # Recover velocity
        with np.errstate(divide='ignore', invalid='ignore'):
            new_state.u_solid = np.where(new_state.h_solid > 1e-6, 
                                          hu_s_new / new_state.h_solid, 0)
            new_state.u_fluid = np.where(new_state.h_fluid > 1e-6,
                                          hu_f_new / new_state.h_fluid, 0)
        
        # Y-sweep
        G_hs, G_hf, G_hv_s, G_hv_f = compute_fluxes_y(
            new_state.h_solid, new_state.h_fluid,
            new_state.u_solid, new_state.v_solid,
            new_state.u_fluid, new_state.v_fluid,
            self.g, self.dy
        )
        
        dt_dy = dt / self.dy
        new_state.h_solid = new_state.h_solid - dt_dy * (G_hs[1:, :] - G_hs[:-1, :])
        new_state.h_fluid = new_state.h_fluid - dt_dy * (G_hf[1:, :] - G_hf[:-1, :])
        
        hv_s = state.h_solid * state.v_solid
        hv_f = state.h_fluid * state.v_fluid
        hv_s_new = hv_s - dt_dy * (G_hv_s[1:, :] - G_hv_s[:-1, :])
        hv_f_new = hv_f - dt_dy * (G_hv_f[1:, :] - G_hv_f[:-1, :])
        
        with np.errstate(divide='ignore', invalid='ignore'):
            new_state.v_solid = np.where(new_state.h_solid > 1e-6,
                                          hv_s_new / new_state.h_solid, 0)
            new_state.v_fluid = np.where(new_state.h_fluid > 1e-6,
                                          hv_f_new / new_state.h_fluid, 0)
        
        # Source terms
        new_state = self.apply_source_terms(new_state, dt)
        
        # Clamp values
        new_state.clamp_values(self.model.params)
        
        return new_state
    
    def apply_boundary_conditions(self, state: FlowState) -> FlowState:
        """Apply boundary conditions."""
        if self.config.boundary_type == 'outflow':
            # Zero gradient at boundaries (free outflow)
            pass
        elif self.config.boundary_type == 'reflective':
            state.u_solid[:, 0] = -state.u_solid[:, 1]
            state.u_solid[:, -1] = -state.u_solid[:, -2]
            state.v_solid[0, :] = -state.v_solid[1, :]
            state.v_solid[-1, :] = -state.v_solid[-2, :]
        
        return state
    
    def run_simulation(self, initial_state: FlowState, 
                       t_end: float,
                       output_interval: float = 1.0,
                       progress_callback: Optional[Callable] = None) -> List[Tuple[float, FlowState]]:
        """
        Run the simulation from initial state to t_end.
        
        Args:
            initial_state: Initial flow conditions
            t_end: End time (seconds)
            output_interval: Time interval for saving outputs
            progress_callback: Optional callback(progress, time, step)
            
        Returns:
            List of (time, state) tuples at output intervals
        """
        outputs = [(0.0, initial_state.copy())]
        state = initial_state.copy()
        
        t = 0.0
        step = 0
        next_output = output_interval
        
        start_time = time.time()
        
        while t < t_end:
            # Compute timestep
            dt = self.compute_timestep(state)
            
            # Don't overshoot end time
            if t + dt > t_end:
                dt = t_end - t
            
            # Perform step
            state = self.step(state, dt)
            state = self.apply_boundary_conditions(state)
            
            t += dt
            step += 1
            
            # Output
            if t >= next_output:
                outputs.append((t, state.copy()))
                next_output += output_interval
            
            # Progress callback
            if progress_callback and step % 10 == 0:
                progress = t / t_end
                progress_callback(progress, t, step)
        
        # Final output
        if outputs[-1][0] < t:
            outputs.append((t, state.copy()))
        
        elapsed = time.time() - start_time
        print(f"\n  Simulation completed in {elapsed:.1f}s ({step} steps)")
        
        return outputs


# Alias for backward compatibility
Terrain.create_synthetic_slope = Terrain.create_synthetic


def test_solver():
    """Test solver functionality."""
    print("=" * 50)
    print("Testing NOC-TVD Solver")
    print("=" * 50)
    
    # Create terrain
    terrain = Terrain.create_synthetic(rows=30, cols=25, slope_angle=25.0)
    
    # Create model and solver
    params = FlowParameters()
    model = TwoPhaseFlowModel(params)
    config = SolverConfig(cfl_number=0.4)
    solver = NOCTVDSolver(terrain, model, config)
    
    # Initial state
    state = FlowState.zeros((terrain.rows, terrain.cols))
    release = terrain.create_release_zone(5, 12, 3, 2.0)
    state.h_solid = release * 0.7
    state.h_fluid = release * 0.3
    
    initial_volume = (state.h_solid.sum() + state.h_fluid.sum()) * terrain.cell_size**2
    print(f"\n1. Initial volume: {initial_volume:.0f} m³")
    
    # Run short simulation
    print("\n2. Running 3s simulation...")
    outputs = solver.run_simulation(state, t_end=3.0, output_interval=1.0)
    
    print(f"3. Output frames: {len(outputs)}")
    
    _, final = outputs[-1]
    final_volume = (final.h_solid.sum() + final.h_fluid.sum()) * terrain.cell_size**2
    print(f"4. Final volume: {final_volume:.0f} m³")
    print(f"5. Volume change: {(final_volume - initial_volume) / initial_volume * 100:.1f}%")
    
    # Check stability
    assert not np.any(np.isnan(final.h_solid)), "NaN in solid height"
    assert not np.any(np.isnan(final.h_fluid)), "NaN in fluid height"
    assert (final.h_solid >= 0).all(), "Negative solid height"
    
    print("\n✓ Solver tests passed!")
    return True


if __name__ == "__main__":
    test_solver()
