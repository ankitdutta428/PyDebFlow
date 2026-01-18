#!/usr/bin/env python
"""
pydebflow - Professional CLI Entry Point for PyDebFlow
=======================================================

This is the main command-line interface for PyDebFlow.
It provides a clean, professional CLI similar to tools like git, docker, etc.

Usage:
    pydebflow simulate --dem terrain.tif
    pydebflow test --all
    pydebflow gui
    pydebflow info

Installation:
    pip install -e .  (when setup.py is configured)
    OR
    python -m pydebflow [command]
"""

import sys
import argparse
from pathlib import Path

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent))


def cmd_simulate(args):
    """Run a simulation."""
    from run_simulation import run_dem_simulation, run_synthetic_test
    
    if args.synthetic:
        run_synthetic_test(
            output_dir=args.output,
            t_end=args.time,
            visualize=not args.no_viz
        )
    elif args.dem:
        run_dem_simulation(
            dem_file=args.dem,
            output_dir=args.output,
            t_end=args.time,
            release_i=args.release_row,
            release_j=args.release_col,
            release_radius=args.release_radius,
            release_height=args.release_height,
            animate_3d=args.animate and not args.no_viz,
            export_video=args.video
        )
    else:
        print("Error: Specify --dem FILE or --synthetic")
        print("Run 'pydebflow simulate --help' for usage")
        sys.exit(1)


def cmd_gui(args):
    """Launch the graphical interface."""
    print("Launching PyDebFlow GUI...")
    from main import main
    main()


def cmd_test(args):
    """Run tests."""
    if args.all:
        from run_simulation import test_all
        test_all()
    elif args.module:
        import subprocess
        subprocess.run([sys.executable, "-m", "pytest", f"tests/test_{args.module}.py", "-v"])
    else:
        import subprocess
        subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"])


def cmd_info(args):
    """Display system and version information."""
    import platform
    
    print("=" * 66)
    print("               PyDebFlow Information")
    print("=" * 66)
    print()
    print("Version:      0.1.0")
    print(f"Python:       {platform.python_version()}")
    print(f"Platform:     {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print()
    
    # Check dependencies
    print("Dependencies:")
    deps = [
        ('numpy', 'numpy'),
        ('numba', 'numba'),
        ('scipy', 'scipy'),
        ('matplotlib', 'matplotlib'),
        ('PyQt6', 'PyQt6'),
        ('pyvista', 'pyvista'),
        ('rasterio', 'rasterio'),
    ]
    
    for name, module in deps:
        try:
            mod = __import__(module)
            version = getattr(mod, '__version__', 'installed')
            print(f"  {name:12s} {version}")
        except ImportError:
            print(f"  {name:12s} NOT INSTALLED")
    
    print()
    print("Project Location:")
    print(f"  {Path(__file__).parent.resolve()}")


def cmd_version(args):
    """Display version."""
    print("PyDebFlow version 0.1.0")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='pydebflow',
        description='PyDebFlow - Advanced Two-Phase Mass Flow Simulation',
        epilog='Run "pydebflow <command> --help" for command-specific help',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--version', '-V', action='store_true',
                        help='Show version and exit')
    
    subparsers = parser.add_subparsers(dest='command', title='Commands')
    
    # =====================================================================
    # simulate command
    # =====================================================================
    sim_parser = subparsers.add_parser(
        'simulate', 
        help='Run a debris flow simulation',
        description='Run simulation on synthetic terrain or a DEM file'
    )
    
    sim_input = sim_parser.add_argument_group('Input')
    sim_input.add_argument('--dem', '-d', type=str, metavar='FILE',
                           help='Path to DEM file (GeoTIFF or ASCII Grid)')
    sim_input.add_argument('--synthetic', '-s', action='store_true',
                           help='Use synthetic terrain for testing')
    
    sim_params = sim_parser.add_argument_group('Parameters')
    sim_params.add_argument('--time', '-t', type=float, default=30.0,
                            help='Simulation duration in seconds (default: 30)')
    sim_params.add_argument('--output', '-o', type=str, default='./output',
                            help='Output directory (default: ./output)')
    
    sim_release = sim_parser.add_argument_group('Release Zone')
    sim_release.add_argument('--release-row', type=int, metavar='I',
                             help='Release zone center row')
    sim_release.add_argument('--release-col', type=int, metavar='J',
                             help='Release zone center column')
    sim_release.add_argument('--release-radius', type=int, default=10,
                             help='Release zone radius in cells (default: 10)')
    sim_release.add_argument('--release-height', type=float, default=5.0,
                             help='Release zone height in meters (default: 5.0)')
    
    sim_viz = sim_parser.add_argument_group('Visualization')
    sim_viz.add_argument('--animate', '-a', action='store_true',
                         help='Show 3D animated visualization')
    sim_viz.add_argument('--video', '-v', action='store_true',
                         help='Export animation to MP4 video')
    sim_viz.add_argument('--no-viz', action='store_true',
                         help='Disable all visualization')
    
    sim_parser.set_defaults(func=cmd_simulate)
    
    # =====================================================================
    # gui command
    # =====================================================================
    gui_parser = subparsers.add_parser(
        'gui',
        help='Launch the graphical user interface',
        description='Open the PyDebFlow desktop application'
    )
    gui_parser.set_defaults(func=cmd_gui)
    
    # =====================================================================
    # test command
    # =====================================================================
    test_parser = subparsers.add_parser(
        'test',
        help='Run tests',
        description='Run unit tests and integration tests'
    )
    test_parser.add_argument('--all', '-a', action='store_true',
                              help='Run all built-in component tests')
    test_parser.add_argument('--module', '-m', type=str,
                              help='Run specific test module (e.g., rheology, solver)')
    test_parser.set_defaults(func=cmd_test)
    
    # =====================================================================
    # info command
    # =====================================================================
    info_parser = subparsers.add_parser(
        'info',
        help='Display system information',
        description='Show version, dependencies, and system info'
    )
    info_parser.set_defaults(func=cmd_info)
    
    # Parse and execute
    args = parser.parse_args()
    
    if args.version:
        cmd_version(args)
        return
    
    if not args.command:
        parser.print_help()
        print()
        print("Quick Start:")
        print("  pydebflow simulate --synthetic    # Quick demo")
        print("  pydebflow gui                     # Launch GUI")
        print("  pydebflow info                    # System info")
        return
    
    # Execute command
    args.func(args)


if __name__ == '__main__':
    main()
