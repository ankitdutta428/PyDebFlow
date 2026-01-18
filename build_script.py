#!/usr/bin/env python
"""
Build script for PyDebFlow.
Creates a standalone executable using PyInstaller.
"""

import subprocess
import sys
import shutil
from pathlib import Path


def check_dependencies():
    """Check that required dependencies are installed."""
    print("Checking dependencies...")
    
    required = ['numpy', 'matplotlib', 'scipy']
    optional = ['PyQt6', 'numba', 'rasterio']
    
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
            print(f"  ✓ {pkg}")
        except ImportError:
            print(f"  ✗ {pkg} - REQUIRED")
            missing.append(pkg)
    
    for pkg in optional:
        try:
            __import__(pkg)
            print(f"  ✓ {pkg}")
        except ImportError:
            print(f"  ⚠ {pkg} - optional")
    
    try:
        import PyInstaller
        print(f"  ✓ PyInstaller")
    except ImportError:
        print(f"  ✗ PyInstaller - REQUIRED for building")
        missing.append('pyinstaller')
    
    if missing:
        print(f"\nMissing required packages: {', '.join(missing)}")
        print("Install with: pip install " + ' '.join(missing))
        return False
    
    return True


def clean_build():
    """Clean previous build artifacts."""
    print("\nCleaning previous build...")
    
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  Removed {dir_name}/")
    
    # Remove .spec files
    for spec_file in Path('.').glob('*.spec'):
        spec_file.unlink()
        print(f"  Removed {spec_file}")


def build_executable():
    """Build the executable with PyInstaller."""
    print("\nBuilding executable...")
    
    # PyInstaller options
    options = [
        'main.py',
        '--name=PyDebFlow',
        '--onefile',
        '--windowed',  # No console window for GUI
        '--noconfirm',
        
        # Include all source modules
        '--add-data=src;src',
        
        # Hidden imports for dynamic imports
        '--hidden-import=numpy',
        '--hidden-import=scipy',
        '--hidden-import=matplotlib',
        '--hidden-import=matplotlib.backends.backend_qtagg',
        
        # Exclude unnecessary packages to reduce size
        '--exclude-module=tkinter',
        '--exclude-module=test',
        '--exclude-module=unittest',
    ]
    
    # Check if PyQt6 is available
    try:
        import PyQt6
        options.extend([
            '--hidden-import=PyQt6',
            '--hidden-import=PyQt6.QtWidgets',
            '--hidden-import=PyQt6.QtCore',
            '--hidden-import=PyQt6.QtGui',
        ])
    except ImportError:
        print("  Note: PyQt6 not found, building CLI-only version")
        options.remove('--windowed')
    
    # Check for numba
    try:
        import numba
        options.append('--hidden-import=numba')
    except ImportError:
        pass
    
    # Run PyInstaller
    cmd = [sys.executable, '-m', 'PyInstaller'] + options
    print(f"  Command: {' '.join(cmd[:5])}...")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("\n  Build failed!")
        print(result.stderr)
        return False
    
    print("  Build successful!")
    return True


def verify_build():
    """Verify the built executable."""
    print("\nVerifying build...")
    
    exe_path = Path('dist/PyDebFlow.exe')
    if not exe_path.exists():
        # Try without .exe for non-Windows
        exe_path = Path('dist/PyDebFlow')
    
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"  ✓ Executable created: {exe_path}")
        print(f"  ✓ Size: {size_mb:.1f} MB")
        return True
    else:
        print("  ✗ Executable not found")
        return False


def create_distribution():
    """Create a distribution package."""
    print("\nCreating distribution package...")
    
    dist_dir = Path('dist')
    
    # Create a sample config file
    config_content = """{
    "terrain": {
        "use_synthetic": true,
        "synthetic_rows": 100,
        "synthetic_cols": 80,
        "cell_size": 10.0,
        "synthetic_slope": 25.0
    },
    "release": {
        "center_row": 15,
        "center_col": 40,
        "radius": 10,
        "solid_height": 5.0,
        "fluid_height": 2.0,
        "solid_fraction": 0.7
    },
    "flow": {
        "solid_density": 2500,
        "fluid_density": 1100,
        "basal_friction_angle": 22.0,
        "voellmy_mu": 0.15,
        "voellmy_xi": 500
    },
    "simulation": {
        "t_end": 60.0,
        "output_interval": 1.0
    },
    "output": {
        "output_dir": "./output",
        "output_format": "npy"
    }
}"""
    
    config_path = dist_dir / 'sample_config.json'
    config_path.write_text(config_content)
    print(f"  Created: {config_path}")
    
    # Create README
    readme_content = """# PyDebFlow

Mass Flow Simulation Tool - r.avaflow Replica

## Quick Start

### GUI Mode
Double-click `PyDebFlow.exe` to launch the graphical interface.

### Command Line
```
PyDebFlow.exe --help
```

### Run with Config File
```
PyDebFlow.exe run --config sample_config.json
```

## Features

- Two-phase (solid + fluid) mass flow simulation
- Debris flows, avalanches, and lahars
- NOC-TVD numerical solver
- Mohr-Coulomb and Voellmy rheology
- GeoTIFF and ASCII Grid support

## Presets

- **Debris Flow**: High-density granular-fluid mixture
- **Snow Avalanche**: Low-density dry powder/wet snow
- **Volcanic Lahar**: Volcanic mudflow

## Output Files

- `max_height.npy` - Maximum flow height reached
- `max_velocity.npy` - Maximum velocity reached
- `max_pressure.npy` - Maximum impact pressure (kPa)
- `summary.json` - Statistics and metadata

## License

Open source software.
"""
    
    readme_path = dist_dir / 'README.md'
    readme_path.write_text(readme_content)
    print(f"  Created: {readme_path}")
    
    print("\nDistribution package created in: dist/")


def main():
    """Main build process."""
    print("=" * 60)
    print("PyDebFlow Build Script")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        print("\nBuild aborted due to missing dependencies.")
        return 1
    
    # Clean previous build
    clean_build()
    
    # Build executable
    if not build_executable():
        print("\nBuild failed.")
        return 1
    
    # Verify build
    if not verify_build():
        print("\nVerification failed.")
        return 1
    
    # Create distribution
    create_distribution()
    
    print("\n" + "=" * 60)
    print("BUILD COMPLETE")
    print("=" * 60)
    print("\nExecutable: dist/PyDebFlow.exe")
    print("\nTo run the GUI:")
    print("  dist\\PyDebFlow.exe")
    print("\nTo run CLI:")
    print("  dist\\PyDebFlow.exe run --synthetic --t-end 60")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
