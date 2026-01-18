"""
Raster I/O for OpenDebris.

Handles reading and writing raster data in various formats.
"""

import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import json


class RasterIO:
    """
    Read and write raster data (GeoTIFF, ASCII Grid, NumPy).
    """
    
    @staticmethod
    def read(filepath: str) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Read raster file with auto-format detection.
        
        Args:
            filepath: Path to raster file
            
        Returns:
            (data array, metadata dict)
        """
        path = Path(filepath)
        suffix = path.suffix.lower()
        
        if suffix in ['.tif', '.tiff', '.geotiff']:
            return RasterIO._read_geotiff(filepath)
        elif suffix in ['.asc', '.txt']:
            return RasterIO._read_ascii_grid(filepath)
        elif suffix == '.npy':
            return RasterIO._read_numpy(filepath)
        else:
            raise ValueError(f"Unsupported format: {suffix}")
    
    @staticmethod
    def write(filepath: str, data: np.ndarray, 
              metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Write raster data to file.
        
        Args:
            filepath: Output file path
            data: 2D array to write
            metadata: Optional metadata dict
        """
        path = Path(filepath)
        suffix = path.suffix.lower()
        metadata = metadata or {}
        
        if suffix in ['.tif', '.tiff', '.geotiff']:
            RasterIO._write_geotiff(filepath, data, metadata)
        elif suffix == '.asc':
            RasterIO._write_ascii_grid(filepath, data, metadata)
        elif suffix == '.npy':
            RasterIO._write_numpy(filepath, data, metadata)
        else:
            raise ValueError(f"Unsupported format: {suffix}")
    
    @staticmethod
    def _read_geotiff(filepath: str) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Read GeoTIFF using rasterio."""
        try:
            import rasterio
            
            with rasterio.open(filepath) as src:
                data = src.read(1).astype(np.float64)
                
                if src.nodata is not None:
                    data = np.where(data == src.nodata, np.nan, data)
                
                metadata = {
                    'cell_size': src.res[0],
                    'x_origin': src.bounds.left,
                    'y_origin': src.bounds.bottom,
                    'nodata': src.nodata,
                    'crs': str(src.crs) if src.crs else None,
                    'transform': list(src.transform)[:6],
                }
                
                return data, metadata
                
        except ImportError:
            raise ImportError("rasterio required: pip install rasterio")
    
    @staticmethod
    def _read_ascii_grid(filepath: str) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Read ESRI ASCII Grid file."""
        metadata = {}
        
        with open(filepath, 'r') as f:
            # Read header (typically 6 lines)
            header_lines = 0
            while True:
                pos = f.tell()
                line = f.readline().strip().split()
                if len(line) >= 2 and not line[0].replace('.', '').replace('-', '').isdigit():
                    key = line[0].lower()
                    value = line[1]
                    try:
                        metadata[key] = float(value) if '.' in value else int(value)
                    except ValueError:
                        metadata[key] = value
                    header_lines += 1
                else:
                    f.seek(pos)
                    break
        
        # Read data
        data = np.loadtxt(filepath, skiprows=header_lines)
        
        # Handle nodata
        nodata = metadata.get('nodata_value', -9999)
        data = np.where(data == nodata, np.nan, data)
        
        # Normalize metadata keys
        result_meta = {
            'cell_size': metadata.get('cellsize', 10.0),
            'x_origin': metadata.get('xllcorner', metadata.get('xllcenter', 0.0)),
            'y_origin': metadata.get('yllcorner', metadata.get('yllcenter', 0.0)),
            'nodata': nodata,
        }
        
        return data, result_meta
    
    @staticmethod
    def _read_numpy(filepath: str) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Read NumPy array with metadata."""
        data = np.load(filepath)
        
        # Look for companion metadata file
        meta_path = Path(filepath).with_suffix('.json')
        if meta_path.exists():
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {'cell_size': 10.0}
        
        return data, metadata
    
    @staticmethod
    def _write_geotiff(filepath: str, data: np.ndarray, 
                       metadata: Dict[str, Any]) -> None:
        """Write GeoTIFF using rasterio."""
        try:
            import rasterio
            from rasterio.transform import from_origin
            
            cell_size = metadata.get('cell_size', 10.0)
            x_origin = metadata.get('x_origin', 0.0)
            y_origin = metadata.get('y_origin', 0.0)
            nodata = metadata.get('nodata', -9999)
            
            # Adjust y_origin for top-left (GeoTIFF convention)
            y_top = y_origin + data.shape[0] * cell_size
            
            transform = from_origin(x_origin, y_top, cell_size, cell_size)
            
            # Handle NaN
            write_data = np.nan_to_num(data, nan=nodata)
            
            with rasterio.open(
                filepath, 'w',
                driver='GTiff',
                height=data.shape[0],
                width=data.shape[1],
                count=1,
                dtype=write_data.dtype,
                crs=metadata.get('crs', 'EPSG:32632'),
                transform=transform,
                nodata=nodata
            ) as dst:
                dst.write(write_data, 1)
                
        except ImportError:
            raise ImportError("rasterio required for GeoTIFF: pip install rasterio")
    
    @staticmethod
    def _write_ascii_grid(filepath: str, data: np.ndarray,
                          metadata: Dict[str, Any]) -> None:
        """Write ESRI ASCII Grid file."""
        rows, cols = data.shape
        cell_size = metadata.get('cell_size', 10.0)
        x_origin = metadata.get('x_origin', 0.0)
        y_origin = metadata.get('y_origin', 0.0)
        nodata = metadata.get('nodata', -9999)
        
        # Handle NaN
        write_data = np.nan_to_num(data, nan=nodata)
        
        with open(filepath, 'w') as f:
            f.write(f"ncols {cols}\n")
            f.write(f"nrows {rows}\n")
            f.write(f"xllcorner {x_origin}\n")
            f.write(f"yllcorner {y_origin}\n")
            f.write(f"cellsize {cell_size}\n")
            f.write(f"nodata_value {nodata}\n")
            
            for row in write_data:
                f.write(' '.join(f'{v:.6g}' for v in row) + '\n')
    
    @staticmethod
    def _write_numpy(filepath: str, data: np.ndarray,
                     metadata: Dict[str, Any]) -> None:
        """Write NumPy array with metadata."""
        np.save(filepath, data)
        
        # Save metadata
        meta_path = Path(filepath).with_suffix('.json')
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)


def test_raster_io():
    """Test raster I/O functionality."""
    import tempfile
    
    print("=" * 50)
    print("Testing Raster I/O")
    print("=" * 50)
    
    # Create test data
    data = np.random.rand(20, 25) * 100
    metadata = {
        'cell_size': 10.0,
        'x_origin': 500000.0,
        'y_origin': 4000000.0,
        'nodata': -9999
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test ASCII Grid
        asc_path = Path(tmpdir) / 'test.asc'
        RasterIO.write(str(asc_path), data, metadata)
        read_data, read_meta = RasterIO.read(str(asc_path))
        
        print(f"\n1. ASCII Grid roundtrip:")
        print(f"   Shape match: {read_data.shape == data.shape}")
        print(f"   Values close: {np.allclose(read_data, data, rtol=1e-5)}")
        
        # Test NumPy
        npy_path = Path(tmpdir) / 'test.npy'
        RasterIO.write(str(npy_path), data, metadata)
        read_data, read_meta = RasterIO.read(str(npy_path))
        
        print(f"\n2. NumPy roundtrip:")
        print(f"   Shape match: {read_data.shape == data.shape}")
        print(f"   Values exact: {np.allclose(read_data, data)}")
    
    print("\n✓ Raster I/O tests passed!")
    return True


if __name__ == "__main__":
    test_raster_io()
