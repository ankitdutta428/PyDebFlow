"""
Terrain handling module for OpenDebris.
Supports loading real DEM files (GeoTIFF, ASCII Grid) and synthetic terrain.
"""

import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class TerrainMetadata:
    """Metadata for terrain raster."""
    rows: int
    cols: int
    cell_size: float
    x_origin: float = 0.0
    y_origin: float = 0.0
    nodata_value: float = -9999.0
    crs: Optional[str] = None


class Terrain:
    """
    Digital Elevation Model handler.
    
    Supports:
    - GeoTIFF files (.tif, .tiff)
    - ESRI ASCII Grid files (.asc)
    - Synthetic terrain generation
    """
    
    def __init__(self, elevation: np.ndarray, cell_size: float = 10.0,
                 x_origin: float = 0.0, y_origin: float = 0.0):
        """Initialize terrain from elevation array."""
        self.elevation = np.nan_to_num(elevation.astype(np.float64), nan=0.0)
        self.original_elevation = self.elevation.copy()
        self.cell_size = cell_size
        self.x_origin = x_origin
        self.y_origin = y_origin
        
        self.rows, self.cols = self.elevation.shape
        self._compute_slope_aspect()
    
    @property
    def metadata(self) -> TerrainMetadata:
        """Get terrain metadata."""
        return TerrainMetadata(
            rows=self.rows, cols=self.cols,
            cell_size=self.cell_size,
            x_origin=self.x_origin, y_origin=self.y_origin
        )
    
    def _compute_slope_aspect(self) -> None:
        """Compute slope angle and aspect from elevation."""
        # Pad edges to handle boundaries
        padded = np.pad(self.elevation, 1, mode='edge')
        
        # Central differences
        dy = (padded[2:, 1:-1] - padded[:-2, 1:-1]) / (2 * self.cell_size)
        dx = (padded[1:-1, 2:] - padded[1:-1, :-2]) / (2 * self.cell_size)
        
        # Slope magnitude and angle
        self.slope = np.arctan(np.sqrt(dx**2 + dy**2))
        self.aspect = np.arctan2(-dx, -dy)
        
        # Slope gradients for flow calculations
        # IMPORTANT: Negate to get downhill direction (gravity acts opposite to gradient)
        # Positive gradient means elevation increases => gravity pushes negative direction
        self.slope_x = np.clip(-dx, -2.0, 2.0)  # Limit extreme slopes
        self.slope_y = np.clip(-dy, -2.0, 2.0)
    
    def create_release_zone(self, center_i: int, center_j: int,
                            radius: int, height: float) -> np.ndarray:
        """Create a circular release zone."""
        release = np.zeros_like(self.elevation)
        
        for i in range(max(0, center_i - radius), min(self.rows, center_i + radius + 1)):
            for j in range(max(0, center_j - radius), min(self.cols, center_j + radius + 1)):
                dist = np.sqrt((i - center_i)**2 + (j - center_j)**2)
                if dist <= radius:
                    release[i, j] = height * (1 - (dist / radius)**2)
        
        return release
    
    @classmethod
    def from_geotiff(cls, filepath: str) -> 'Terrain':
        """Load terrain from GeoTIFF file."""
        try:
            import rasterio
            
            with rasterio.open(filepath) as src:
                data = src.read(1).astype(np.float64)
                
                # Handle nodata
                if src.nodata is not None:
                    data = np.where(data == src.nodata, np.nan, data)
                
                cell_size = src.res[0]
                x_origin = src.bounds.left
                y_origin = src.bounds.bottom
                
                # Detect geographic coordinates (degrees) vs projected (meters)
                # If cell_size < 0.01, it's likely in degrees (lat/lon)
                is_geographic = cell_size < 0.01
                
                if is_geographic:
                    # Convert degrees to approximate meters
                    # At equator: 1 degree ≈ 111,320 meters
                    # Adjust for latitude using mean latitude from bounds
                    mean_lat = (src.bounds.top + src.bounds.bottom) / 2
                    meters_per_degree_lat = 111320.0
                    meters_per_degree_lon = 111320.0 * np.cos(np.radians(mean_lat))
                    
                    # Use average of lat/lon scale
                    cell_size_meters = cell_size * (meters_per_degree_lat + meters_per_degree_lon) / 2
                    
                    print(f"Loaded GeoTIFF: {data.shape[0]}x{data.shape[1]} cells")
                    print(f"⚠ Detected geographic coordinates (lat/lon)")
                    print(f"  Original cell size: {cell_size:.8f}° (degrees)")
                    print(f"  Mean latitude: {mean_lat:.4f}°")
                    print(f"  Converted cell size: {cell_size_meters:.2f} m")
                    print(f"Elevation range: {np.nanmin(data):.1f} to {np.nanmax(data):.1f} m")
                    
                    cell_size = cell_size_meters
                else:
                    print(f"Loaded GeoTIFF: {data.shape[0]}x{data.shape[1]} cells")
                    print(f"Cell size: {cell_size}m")
                    print(f"Elevation range: {np.nanmin(data):.1f} to {np.nanmax(data):.1f} m")
                
                return cls(data, cell_size, x_origin, y_origin)
                
        except ImportError:
            raise ImportError("rasterio required for GeoTIFF. Install: pip install rasterio")
    
    @classmethod
    def from_ascii_grid(cls, filepath: str) -> 'Terrain':
        """Load terrain from ESRI ASCII Grid file."""
        metadata = {}
        
        with open(filepath, 'r') as f:
            # Read header (6 lines typically)
            for _ in range(6):
                line = f.readline().strip().split()
                if len(line) >= 2:
                    key = line[0].lower()
                    metadata[key] = float(line[1]) if '.' in line[1] else int(line[1])
        
        # Read data
        data = np.loadtxt(filepath, skiprows=6)
        
        # Handle nodata
        nodata = metadata.get('nodata_value', -9999)
        data = np.where(data == nodata, np.nan, data)
        
        cell_size = metadata.get('cellsize', 10.0)
        x_origin = metadata.get('xllcorner', 0.0)
        y_origin = metadata.get('yllcorner', 0.0)
        
        print(f"Loaded ASCII Grid: {data.shape[0]}x{data.shape[1]} cells")
        print(f"Cell size: {cell_size}m")
        print(f"Elevation range: {np.nanmin(data):.1f} to {np.nanmax(data):.1f} m")
        
        return cls(data, cell_size, x_origin, y_origin)
    
    @classmethod
    def load(cls, filepath: str) -> 'Terrain':
        """Auto-detect format and load DEM file."""
        path = Path(filepath)
        suffix = path.suffix.lower()
        
        if suffix in ['.tif', '.tiff', '.geotiff']:
            return cls.from_geotiff(filepath)
        elif suffix in ['.asc', '.txt']:
            return cls.from_ascii_grid(filepath)
        else:
            raise ValueError(f"Unsupported format: {suffix}. Use .tif or .asc")
    
    @classmethod
    def create_synthetic(cls, rows: int = 100, cols: int = 80,
                         cell_size: float = 10.0,
                         slope_angle: float = 25.0,
                         add_channel: bool = True) -> 'Terrain':
        """Create synthetic inclined terrain for testing."""
        # Base inclined plane
        slope_rad = np.radians(slope_angle)
        y_coords = np.arange(rows) * cell_size
        elevation = y_coords[:, np.newaxis] * np.tan(slope_rad)
        elevation = np.broadcast_to(elevation, (rows, cols)).copy()
        
        # Add channel
        if add_channel:
            x_center = cols // 2
            for j in range(cols):
                dist = abs(j - x_center)
                channel_depth = 8.0 * np.exp(-(dist / (cols / 8))**2)
                elevation[:, j] += channel_depth
        
        # Add some roughness
        np.random.seed(42)
        elevation += np.random.randn(rows, cols) * 0.5
        
        print(f"Created synthetic terrain: {rows}x{cols} cells")
        print(f"Slope: {slope_angle}°, Cell size: {cell_size}m")
        
        return cls(elevation=elevation, cell_size=cell_size)
    
    def get_hillshade(self, azimuth: float = 315, altitude: float = 45) -> np.ndarray:
        """Compute hillshade for visualization."""
        az_rad = np.radians(azimuth)
        alt_rad = np.radians(altitude)
        
        hillshade = (np.cos(alt_rad) * np.cos(self.slope) +
                    np.sin(alt_rad) * np.sin(self.slope) * 
                    np.cos(az_rad - self.aspect))
        
        return np.clip(hillshade, 0, 1)


def test_terrain():
    """Test terrain functionality."""
    print("=" * 50)
    print("Testing Terrain Module")
    print("=" * 50)
    
    # Test synthetic terrain
    terrain = Terrain.create_synthetic(rows=50, cols=40, slope_angle=25.0)
    
    print(f"\nTerrain shape: {terrain.rows}x{terrain.cols}")
    print(f"Mean slope: {np.degrees(terrain.slope.mean()):.1f}°")
    
    # Test release zone
    release = terrain.create_release_zone(10, 20, 5, 3.0)
    print(f"Release max height: {release.max():.2f}m")
    print(f"Release volume: {release.sum() * terrain.cell_size**2:.0f} m³")
    
    print("\n✓ Terrain tests passed!")
    return True


if __name__ == "__main__":
    test_terrain()
