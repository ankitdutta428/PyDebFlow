"""
Visualization Utilities for OpenDebris.

Provides 2D plotting functions for results display.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.figure import Figure
from typing import Optional, Tuple, List
from pathlib import Path


class FlowVisualizer:
    """2D visualization for debris flow simulation results."""
    
    def __init__(self, figsize: Tuple[int, int] = (12, 10), dpi: int = 150):
        self.figsize = figsize
        self.dpi = dpi
        
        # Custom colormaps
        self._create_colormaps()
    
    def _create_colormaps(self) -> None:
        """Create custom colormaps for flow visualization."""
        # Flow height colormap (blue to red)
        self.height_cmap = plt.cm.YlOrRd
        
        # Velocity colormap
        self.velocity_cmap = plt.cm.plasma
        
        # Pressure colormap (hazard)
        colors = ['#2b83ba', '#abdda4', '#ffffbf', '#fdae61', '#d7191c']
        self.pressure_cmap = mcolors.LinearSegmentedColormap.from_list('hazard', colors)
        
        # Terrain colormap
        self.terrain_cmap = plt.cm.terrain
    
    def plot_flow_height(self, h: np.ndarray, 
                          terrain: Optional[np.ndarray] = None,
                          cell_size: float = 10.0,
                          title: str = "Flow Height",
                          ax: Optional[plt.Axes] = None) -> plt.Axes:
        """
        Plot flow height with optional terrain hillshade.
        
        Args:
            h: Flow height array (m)
            terrain: Optional terrain elevation for hillshade
            cell_size: Cell size in meters
            title: Plot title
            ax: Matplotlib axes (creates new if None)
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)
        
        extent = [0, h.shape[1] * cell_size, 0, h.shape[0] * cell_size]
        
        # Hillshade background
        if terrain is not None:
            hillshade = self._compute_hillshade(terrain)
            ax.imshow(hillshade, extent=extent, cmap='gray', 
                      vmin=0, vmax=1, origin='lower', alpha=0.5)
        
        # Flow height (transparent where zero)
        masked = np.ma.masked_where(h < 0.01, h)
        im = ax.imshow(masked, extent=extent, cmap=self.height_cmap,
                       origin='lower', alpha=0.8, vmin=0, vmax=max(h.max(), 0.1))
        
        cbar = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
        cbar.set_label('Flow Height (m)')
        
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_title(title)
        ax.set_aspect('equal')
        
        return ax
    
    def plot_velocity(self, u: np.ndarray, v: np.ndarray,
                       h: np.ndarray,
                       cell_size: float = 10.0,
                       title: str = "Flow Velocity",
                       ax: Optional[plt.Axes] = None) -> plt.Axes:
        """Plot velocity field with magnitude and arrows."""
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)
        
        speed = np.sqrt(u**2 + v**2)
        extent = [0, h.shape[1] * cell_size, 0, h.shape[0] * cell_size]
        
        # Velocity magnitude
        masked = np.ma.masked_where(h < 0.01, speed)
        im = ax.imshow(masked, extent=extent, cmap=self.velocity_cmap,
                       origin='lower', alpha=0.8)
        
        cbar = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
        cbar.set_label('Velocity (m/s)')
        
        # Velocity arrows (subsampled)
        step = max(1, min(h.shape) // 20)
        y, x = np.mgrid[0:h.shape[0]:step, 0:h.shape[1]:step]
        x = x * cell_size + cell_size / 2
        y = y * cell_size + cell_size / 2
        
        u_sub = u[::step, ::step]
        v_sub = v[::step, ::step]
        h_sub = h[::step, ::step]
        
        # Only plot arrows where there's flow
        mask = h_sub > 0.1
        if mask.any():
            ax.quiver(x[mask], y[mask], u_sub[mask], v_sub[mask],
                      color='white', alpha=0.7, scale=50)
        
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_title(title)
        ax.set_aspect('equal')
        
        return ax
    
    def plot_pressure(self, pressure: np.ndarray,
                       cell_size: float = 10.0,
                       title: str = "Impact Pressure",
                       ax: Optional[plt.Axes] = None) -> plt.Axes:
        """Plot impact pressure (hazard map)."""
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)
        
        extent = [0, pressure.shape[1] * cell_size, 0, pressure.shape[0] * cell_size]
        
        masked = np.ma.masked_where(pressure < 0.1, pressure)
        im = ax.imshow(masked, extent=extent, cmap=self.pressure_cmap,
                       origin='lower', alpha=0.9)
        
        cbar = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
        cbar.set_label('Impact Pressure (kPa)')
        
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_title(title)
        ax.set_aspect('equal')
        
        return ax
    
    def plot_results_summary(self, max_height: np.ndarray,
                              max_velocity: np.ndarray,
                              max_pressure: np.ndarray,
                              terrain: np.ndarray,
                              cell_size: float = 10.0,
                              title: str = "Simulation Results") -> Figure:
        """Create a 2x2 summary plot."""
        fig, axes = plt.subplots(2, 2, figsize=(14, 12))
        
        # Terrain with hillshade
        hillshade = self._compute_hillshade(terrain)
        extent = [0, terrain.shape[1] * cell_size, 0, terrain.shape[0] * cell_size]
        
        axes[0, 0].imshow(terrain, extent=extent, cmap=self.terrain_cmap, origin='lower')
        axes[0, 0].set_title('Terrain Elevation')
        axes[0, 0].set_xlabel('X (m)')
        axes[0, 0].set_ylabel('Y (m)')
        
        # Max height
        self.plot_flow_height(max_height, terrain, cell_size, 
                              'Maximum Flow Height', axes[0, 1])
        
        # Max velocity
        masked = np.ma.masked_where(max_height < 0.01, max_velocity)
        im = axes[1, 0].imshow(masked, extent=extent, cmap=self.velocity_cmap,
                                origin='lower', alpha=0.9)
        plt.colorbar(im, ax=axes[1, 0], shrink=0.8).set_label('m/s')
        axes[1, 0].set_title('Maximum Velocity')
        axes[1, 0].set_xlabel('X (m)')
        axes[1, 0].set_ylabel('Y (m)')
        
        # Max pressure
        self.plot_pressure(max_pressure, cell_size, 'Maximum Impact Pressure', axes[1, 1])
        
        fig.suptitle(title, fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        return fig
    
    def _compute_hillshade(self, elevation: np.ndarray,
                            azimuth: float = 315,
                            altitude: float = 45) -> np.ndarray:
        """Compute hillshade from elevation."""
        # Gradient
        dy, dx = np.gradient(elevation)
        
        # Slope and aspect
        slope = np.arctan(np.sqrt(dx**2 + dy**2))
        aspect = np.arctan2(-dx, -dy)
        
        # Light direction
        az_rad = np.radians(azimuth)
        alt_rad = np.radians(altitude)
        
        # Hillshade
        hillshade = (np.cos(alt_rad) * np.cos(slope) +
                     np.sin(alt_rad) * np.sin(slope) * np.cos(az_rad - aspect))
        
        return np.clip(hillshade, 0, 1)
    
    def save_figure(self, fig: Figure, filepath: str) -> None:
        """Save figure to file."""
        fig.savefig(filepath, dpi=self.dpi, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
    
    def create_animation_frames(self, snapshots: List[np.ndarray],
                                  times: List[float],
                                  terrain: np.ndarray,
                                  cell_size: float = 10.0,
                                  output_dir: str = './frames') -> List[str]:
        """Create animation frames from snapshots."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        frame_paths = []
        
        for i, (h, t) in enumerate(zip(snapshots, times)):
            fig, ax = plt.subplots(figsize=(10, 8))
            
            self.plot_flow_height(h, terrain, cell_size, 
                                   f'Flow Height at t = {t:.1f}s', ax)
            
            frame_path = output_path / f'frame_{i:04d}.png'
            self.save_figure(fig, str(frame_path))
            plt.close(fig)
            
            frame_paths.append(str(frame_path))
        
        return frame_paths


def test_plot_utils():
    """Test visualization utilities."""
    print("=" * 50)
    print("Testing Visualization")
    print("=" * 50)
    
    # Create test data
    shape = (50, 60)
    terrain = np.fromfunction(lambda i, j: i * 5, shape)
    
    h = np.zeros(shape)
    h[20:35, 25:40] = np.random.rand(15, 15) * 2 + 0.5
    
    u = np.zeros(shape)
    v = np.zeros(shape)
    u[20:35, 25:40] = 3.0
    v[20:35, 25:40] = 5.0
    
    pressure = 0.5 * 2000 * (u**2 + v**2) / 1000
    
    viz = FlowVisualizer()
    
    print("\n1. Creating summary plot...")
    fig = viz.plot_results_summary(h, np.sqrt(u**2 + v**2), pressure, terrain)
    print("   ✓ Summary plot created")
    
    plt.close(fig)
    
    print("\n✓ Visualization tests passed!")
    return True


if __name__ == "__main__":
    test_plot_utils()
