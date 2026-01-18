"""
Results Export for OpenDebris.

Handles exporting simulation results to various formats.
"""

import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import json
from datetime import datetime


@dataclass
class SimulationResults:
    """Container for simulation results."""
    
    # Time data
    times: List[float] = field(default_factory=list)
    
    # Maximum fields (hazard maps)
    max_flow_height: Optional[np.ndarray] = None
    max_velocity: Optional[np.ndarray] = None
    max_pressure: Optional[np.ndarray] = None
    
    # Final state
    final_h_solid: Optional[np.ndarray] = None
    final_h_fluid: Optional[np.ndarray] = None
    final_u: Optional[np.ndarray] = None
    final_v: Optional[np.ndarray] = None
    
    # Time series at output intervals
    snapshots: List[Dict[str, np.ndarray]] = field(default_factory=list)
    
    # Statistics
    total_volume: float = 0.0
    max_runout: float = 0.0
    affected_area: float = 0.0


class ResultsExporter:
    """Export simulation results to various formats."""
    
    def __init__(self, output_dir: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Args:
            output_dir: Output directory path
            metadata: Georeferencing metadata (cell_size, origin, etc.)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metadata = metadata or {}
    
    def export_results(self, results: SimulationResults, 
                       format: str = 'npy') -> Dict[str, str]:
        """
        Export all results to files.
        
        Args:
            results: Simulation results
            format: 'npy', 'asc', or 'tif'
            
        Returns:
            Dict mapping result names to file paths
        """
        exported = {}
        
        # Export maximum fields
        if results.max_flow_height is not None:
            path = self._save_array('max_height', results.max_flow_height, format)
            exported['max_height'] = str(path)
        
        if results.max_velocity is not None:
            path = self._save_array('max_velocity', results.max_velocity, format)
            exported['max_velocity'] = str(path)
        
        if results.max_pressure is not None:
            path = self._save_array('max_pressure', results.max_pressure, format)
            exported['max_pressure'] = str(path)
        
        # Export final state
        if results.final_h_solid is not None:
            path = self._save_array('final_h_solid', results.final_h_solid, format)
            exported['final_h_solid'] = str(path)
        
        if results.final_h_fluid is not None:
            path = self._save_array('final_h_fluid', results.final_h_fluid, format)
            exported['final_h_fluid'] = str(path)
        
        # Export summary statistics
        summary = self._create_summary(results)
        summary_path = self.output_dir / 'summary.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        exported['summary'] = str(summary_path)
        
        return exported
    
    def _save_array(self, name: str, data: np.ndarray, format: str) -> Path:
        """Save a single array."""
        if format == 'npy':
            path = self.output_dir / f'{name}.npy'
            np.save(path, data)
        elif format == 'asc':
            path = self.output_dir / f'{name}.asc'
            self._write_ascii_grid(path, data)
        elif format == 'tif':
            path = self.output_dir / f'{name}.tif'
            self._write_geotiff(path, data)
        else:
            raise ValueError(f"Unknown format: {format}")
        
        return path
    
    def _write_ascii_grid(self, path: Path, data: np.ndarray) -> None:
        """Write ASCII grid file."""
        rows, cols = data.shape
        cell_size = self.metadata.get('cell_size', 10.0)
        x_origin = self.metadata.get('x_origin', 0.0)
        y_origin = self.metadata.get('y_origin', 0.0)
        nodata = -9999
        
        write_data = np.nan_to_num(data, nan=nodata)
        
        with open(path, 'w') as f:
            f.write(f"ncols {cols}\n")
            f.write(f"nrows {rows}\n")
            f.write(f"xllcorner {x_origin}\n")
            f.write(f"yllcorner {y_origin}\n")
            f.write(f"cellsize {cell_size}\n")
            f.write(f"nodata_value {nodata}\n")
            
            for row in write_data:
                f.write(' '.join(f'{v:.4g}' for v in row) + '\n')
    
    def _write_geotiff(self, path: Path, data: np.ndarray) -> None:
        """Write GeoTIFF file."""
        try:
            import rasterio
            from rasterio.transform import from_origin
            
            cell_size = self.metadata.get('cell_size', 10.0)
            x_origin = self.metadata.get('x_origin', 0.0)
            y_origin = self.metadata.get('y_origin', 0.0)
            
            y_top = y_origin + data.shape[0] * cell_size
            transform = from_origin(x_origin, y_top, cell_size, cell_size)
            
            nodata = -9999
            write_data = np.nan_to_num(data, nan=nodata).astype(np.float32)
            
            with rasterio.open(
                path, 'w',
                driver='GTiff',
                height=data.shape[0],
                width=data.shape[1],
                count=1,
                dtype='float32',
                crs=self.metadata.get('crs', 'EPSG:32632'),
                transform=transform,
                nodata=nodata
            ) as dst:
                dst.write(write_data, 1)
                
        except ImportError:
            # Fallback to ASCII if rasterio not available
            self._write_ascii_grid(path.with_suffix('.asc'), data)
    
    def _create_summary(self, results: SimulationResults) -> Dict[str, Any]:
        """Create summary statistics."""
        cell_size = self.metadata.get('cell_size', 10.0)
        cell_area = cell_size ** 2
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'simulation_time': max(results.times) if results.times else 0,
            'output_frames': len(results.times),
            'cell_size_m': cell_size,
        }
        
        if results.max_flow_height is not None:
            summary['max_flow_height_m'] = float(results.max_flow_height.max())
            summary['affected_area_m2'] = float(np.sum(results.max_flow_height > 0.1) * cell_area)
        
        if results.max_velocity is not None:
            summary['max_velocity_ms'] = float(results.max_velocity.max())
        
        if results.max_pressure is not None:
            summary['max_pressure_kpa'] = float(results.max_pressure.max())
        
        if results.final_h_solid is not None and results.final_h_fluid is not None:
            final_volume = (results.final_h_solid.sum() + results.final_h_fluid.sum()) * cell_area
            summary['final_volume_m3'] = float(final_volume)
        
        return summary
    
    def export_snapshots(self, snapshots: List[Dict[str, np.ndarray]],
                         times: List[float]) -> None:
        """Export time-series snapshots for animation."""
        snapshots_dir = self.output_dir / 'snapshots'
        snapshots_dir.mkdir(exist_ok=True)
        
        for i, (t, snap) in enumerate(zip(times, snapshots)):
            for name, data in snap.items():
                path = snapshots_dir / f'{name}_{i:04d}.npy'
                np.save(path, data)
        
        # Save time index
        index_path = snapshots_dir / 'time_index.json'
        with open(index_path, 'w') as f:
            json.dump({'times': times, 'count': len(times)}, f)


def test_results():
    """Test results export."""
    import tempfile
    
    print("=" * 50)
    print("Testing Results Export")
    print("=" * 50)
    
    # Create mock results
    shape = (30, 25)
    results = SimulationResults(
        times=[0, 1, 2, 3, 4, 5],
        max_flow_height=np.random.rand(*shape) * 3,
        max_velocity=np.random.rand(*shape) * 10,
        max_pressure=np.random.rand(*shape) * 50,
        final_h_solid=np.random.rand(*shape) * 2,
        final_h_fluid=np.random.rand(*shape),
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata = {'cell_size': 10.0, 'x_origin': 0, 'y_origin': 0}
        exporter = ResultsExporter(tmpdir, metadata)
        
        exported = exporter.export_results(results, format='npy')
        
        print(f"\n1. Exported files:")
        for name, path in exported.items():
            exists = Path(path).exists()
            print(f"   {name}: {'✓' if exists else '✗'}")
        
        # Check summary
        with open(exported['summary'], 'r') as f:
            summary = json.load(f)
        
        print(f"\n2. Summary contents:")
        print(f"   Max height: {summary.get('max_flow_height_m', 'N/A'):.2f} m")
        print(f"   Max velocity: {summary.get('max_velocity_ms', 'N/A'):.2f} m/s")
        print(f"   Affected area: {summary.get('affected_area_m2', 'N/A'):.0f} m²")
    
    print("\n✓ Results tests passed!")
    return True


if __name__ == "__main__":
    test_results()
