#!/usr/bin/env python
"""
run_simulation.py - Standalone test script for PyDebFlow

This script allows testing the simulation components without the GUI.
Supports both synthetic terrain and real DEM files.
Includes 3D PyVista animation visualization.

Run with --help for usage information.
"""

import sys
import os
import argparse
import numpy as np
from pathlib import Path

# Add src to path if running directly
sys.path.insert(0, str(Path(__file__).parent))

from src.core.terrain import Terrain
from src.core.flow_model import TwoPhaseFlowModel, FlowState, FlowParameters
from src.core.noc_tvd_solver import NOCTVDSolver, SolverConfig
from src.physics.rheology import MohrCoulomb, Voellmy
from src.physics.entrainment import EntrainmentModel
from src.io.parameters import SimulationParameters
from src.io.results import ResultsExporter, SimulationResults
from src.visualization.plot_utils import FlowVisualizer


def run_synthetic_test(output_dir: str = "./test_output", 
                        t_end: float = 30.0,
                        visualize: bool = True) -> None:
    """
    Run a complete simulation with synthetic terrain.
    
    Args:
        output_dir: Output directory for results
        t_end: Simulation end time
        visualize: Whether to show plots
    """
    print("=" * 70)
    print("PyDebFlow - Synthetic Test Simulation")
    print("=" * 70)
    
    # Create synthetic terrain
    print("\n[1/5] Creating synthetic terrain...")
    terrain = Terrain.create_synthetic_slope(
        rows=80,
        cols=60,
        cell_size=10.0,
        slope_angle=25.0,
        add_channel=True
    )
    print(f"  Grid: {terrain.rows} x {terrain.cols} cells")
    print(f"  Cell size: {terrain.cell_size} m")
    print(f"  Elevation range: {terrain.elevation.min():.1f} to {terrain.elevation.max():.1f} m")
    
    # Set up flow model
    print("\n[2/5] Configuring flow model...")
    params = FlowParameters(
        solid_density=2500.0,
        fluid_density=1100.0,
        basal_friction_angle=22.0,
        voellmy_mu=0.15,
        voellmy_xi=500.0
    )
    model = TwoPhaseFlowModel(params)
    print(f"  Solid density: {params.solid_density} kg/m³")
    print(f"  Fluid density: {params.fluid_density} kg/m³")
    print(f"  Basal friction: {params.basal_friction_angle}°")
    
    # Configure solver
    solver_config = SolverConfig(
        cfl_number=0.4,
        max_timestep=0.5,
        flux_limiter="minmod",
        boundary_type="outflow"
    )
    solver = NOCTVDSolver(terrain, model, solver_config)
    
    # Initialize release zone
    print("\n[3/5] Creating release zone...")
    state = FlowState.zeros((terrain.rows, terrain.cols))
    
    release = terrain.create_release_zone(
        center_i=15,
        center_j=30,
        radius=8,
        height=5.0
    )
    
    state.h_solid = release * 0.7
    state.h_fluid = release * 0.3
    
    initial_volume = (state.h_solid.sum() + state.h_fluid.sum()) * terrain.cell_size**2
    print(f"  Release center: ({15}, {30})")
    print(f"  Release radius: 8 cells")
    print(f"  Max height: {release.max():.1f} m")
    print(f"  Initial volume: {initial_volume:.0f} m³")
    print(f"  Solid fraction: 70%")
    
    # Run simulation
    print(f"\n[4/5] Running simulation (t_end = {t_end}s)...")
    
    def progress_callback(progress, time, step):
        bar_len = 50
        filled = int(bar_len * progress)
        bar = '█' * filled + '░' * (bar_len - filled)
        print(f"\r  [{bar}] {progress*100:5.1f}% | t={time:6.1f}s | step={step:5d}", 
              end='', flush=True)
    
    outputs = solver.run_simulation(
        state,
        t_end=t_end,
        output_interval=1.0,
        progress_callback=progress_callback
    )
    print("\n  Simulation complete!")
    
    # Process results
    print("\n[5/5] Processing and exporting results...")
    
    max_height = np.zeros((terrain.rows, terrain.cols))
    max_velocity = np.zeros((terrain.rows, terrain.cols))
    max_pressure = np.zeros((terrain.rows, terrain.cols))
    
    for t, s in outputs:
        h_total = s.h_solid + s.h_fluid
        speed = np.sqrt(s.u_solid**2 + s.v_solid**2)
        pressure = model.compute_impact_pressure(s)
        
        max_height = np.maximum(max_height, h_total)
        max_velocity = np.maximum(max_velocity, speed)
        max_pressure = np.maximum(max_pressure, pressure)
    
    _, final_state = outputs[-1]
    
    # Export
    results = SimulationResults(
        times=[t for t, _ in outputs],
        max_flow_height=max_height,
        max_velocity=max_velocity,
        max_pressure=max_pressure,
        final_h_solid=final_state.h_solid,
        final_h_fluid=final_state.h_fluid,
        final_u=final_state.u_solid,
        final_v=final_state.v_solid
    )
    
    metadata = {
        'cell_size': terrain.cell_size,
        'x_origin': terrain.x_origin,
        'y_origin': terrain.y_origin
    }
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    exporter = ResultsExporter(output_dir, metadata)
    exported = exporter.export_results(results, format='npy')
    
    print(f"  Output directory: {output_dir}")
    for name in exported:
        print(f"    - {name}")
    
    # Summary statistics
    print("\n" + "=" * 70)
    print("SIMULATION RESULTS")
    print("=" * 70)
    
    final_volume = (final_state.h_solid.sum() + final_state.h_fluid.sum()) * terrain.cell_size**2
    affected_area = np.sum(max_height > 0.1) * terrain.cell_size**2
    runout = np.argmax(max_height.sum(axis=1) > 0)
    
    print(f"  Simulation time:    {t_end} s")
    print(f"  Time steps:         {len(outputs)}")
    print(f"  Max flow height:    {max_height.max():.2f} m")
    print(f"  Max velocity:       {max_velocity.max():.2f} m/s")
    print(f"  Max impact pressure:{max_pressure.max():.1f} kPa")
    print(f"  Initial volume:     {initial_volume:.0f} m³")
    print(f"  Final volume:       {final_volume:.0f} m³")
    print(f"  Affected area:      {affected_area:.0f} m²")
    print(f"  Approximate runout: {runout * terrain.cell_size:.0f} m")
    
    # Visualization
    if visualize:
        print("\nGenerating visualization...")
        import matplotlib.pyplot as plt
        
        viz = FlowVisualizer()
        
        fig = viz.plot_results_summary(
            max_height, max_velocity, max_pressure, terrain.elevation,
            cell_size=terrain.cell_size,
            title=f"PyDebFlow Synthetic Test (t={t_end}s)"
        )
        
        fig_path = Path(output_dir) / "results_summary.png"
        viz.save_figure(fig, str(fig_path))
        print(f"  Saved: {fig_path}")
        
        plt.show()
    
    print("\n✓ Test complete!")


def test_flow_model() -> None:
    """Test flow model component."""
    print("\n--- Testing Flow Model ---")
    from src.core.flow_model import test_flow_model as _test
    _test()


def test_solver() -> None:
    """Test NOC-TVD solver component."""
    print("\n--- Testing Solver ---")
    from src.core.noc_tvd_solver import test_solver as _test
    _test()


def test_rheology() -> None:
    """Test rheology models."""
    print("\n--- Testing Rheology ---")
    from src.physics.rheology import test_rheology as _test
    _test()


def test_all() -> None:
    """Run all component tests."""
    print("=" * 70)
    print("PyDebFlow - Component Tests")
    print("=" * 70)
    
    tests = [
        ("Terrain", lambda: __import__('src.core.terrain', fromlist=['test_terrain']).test_terrain()),
        ("Flow Model", lambda: __import__('src.core.flow_model', fromlist=['test_flow_model']).test_flow_model()),
        ("Solver", lambda: __import__('src.core.noc_tvd_solver', fromlist=['test_solver']).test_solver()),
        ("Rheology", lambda: __import__('src.physics.rheology', fromlist=['test_rheology']).test_rheology()),
        ("Entrainment", lambda: __import__('src.physics.entrainment', fromlist=['test_entrainment']).test_entrainment()),
        ("Raster I/O", lambda: __import__('src.io.raster_io', fromlist=['test_raster_io']).test_raster_io()),
        ("Parameters", lambda: __import__('src.io.parameters', fromlist=['test_parameters']).test_parameters()),
        ("Results", lambda: __import__('src.io.results', fromlist=['test_results']).test_results()),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n--- {name} ---")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = 0
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")


def run_dem_simulation(dem_file: str,
                        output_dir: str = "./dem_output",
                        t_end: float = 60.0,
                        release_i: int = None,
                        release_j: int = None,
                        release_radius: int = 10,
                        release_height: float = 5.0,
                        animate_3d: bool = True,
                        export_video: bool = False) -> None:
    """
    Run simulation on a real DEM file.
    
    Args:
        dem_file: Path to DEM file (GeoTIFF or ASCII Grid)
        output_dir: Output directory
        t_end: Simulation end time (s)
        release_i, release_j: Release zone center (auto if None)
        release_radius: Release zone radius in cells
        release_height: Initial release height (m)
        animate_3d: Show 3D animation
        export_video: Export animation to MP4
    """
    print("=" * 70)
    print("PyDebFlow - DEM Simulation")
    print("=" * 70)
    
    # Load DEM
    print(f"\n[1/6] Loading DEM: {dem_file}")
    terrain = Terrain.load(dem_file)
    print(f"  Grid: {terrain.rows} x {terrain.cols} cells")
    print(f"  Cell size: {terrain.cell_size} m")
    print(f"  Elevation range: {terrain.elevation.min():.1f} to {terrain.elevation.max():.1f} m")
    
    # Auto-detect release zone if not specified
    if release_i is None:
        release_i = terrain.rows // 5  # Upper portion
    if release_j is None:
        release_j = terrain.cols // 2  # Center
    
    # Setup model
    print("\n[2/6] Configuring flow model...")
    params = FlowParameters(
        solid_density=2500.0,
        fluid_density=1100.0,
        basal_friction_angle=22.0,
        voellmy_mu=0.12,
        voellmy_xi=400.0
    )
    model = TwoPhaseFlowModel(params)
    
    solver_config = SolverConfig(cfl_number=0.4, max_timestep=0.5)
    solver = NOCTVDSolver(terrain, model, solver_config)
    
    # Initialize release
    print(f"\n[3/6] Creating release zone at ({release_i}, {release_j})...")
    state = FlowState.zeros((terrain.rows, terrain.cols))
    release = terrain.create_release_zone(release_i, release_j, release_radius, release_height)
    state.h_solid = release * 0.7
    state.h_fluid = release * 0.3
    
    initial_volume = (state.h_solid.sum() + state.h_fluid.sum()) * terrain.cell_size**2
    print(f"  Initial volume: {initial_volume:.0f} m³")
    
    # Run simulation with snapshot collection
    print(f"\n[4/6] Running simulation (t_end = {t_end}s)...")
    
    def progress_callback(progress, time, step):
        bar_len = 50
        filled = int(bar_len * progress)
        bar = '█' * filled + '░' * (bar_len - filled)
        print(f"\r  [{bar}] {progress*100:5.1f}% | t={time:6.1f}s | step={step:5d}", 
              end='', flush=True)
    
    outputs = solver.run_simulation(
        state,
        t_end=t_end,
        output_interval=max(1.0, t_end / 60),  # ~60 frames max
        progress_callback=progress_callback
    )
    print("\n  Simulation complete!")
    
    # Process results
    print("\n[5/6] Processing results...")
    max_height = np.zeros((terrain.rows, terrain.cols))
    max_velocity = np.zeros((terrain.rows, terrain.cols))
    max_pressure = np.zeros((terrain.rows, terrain.cols))
    snapshots = []
    times = []
    
    for t, s in outputs:
        h_total = s.h_solid + s.h_fluid
        speed = np.sqrt(s.u_solid**2 + s.v_solid**2)
        pressure = model.compute_impact_pressure(s)
        
        max_height = np.maximum(max_height, h_total)
        max_velocity = np.maximum(max_velocity, speed)
        max_pressure = np.maximum(max_pressure, pressure)
        
        snapshots.append(h_total.copy())
        times.append(t)
    
    _, final_state = outputs[-1]
    
    # Export
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    results = SimulationResults(
        times=times,
        max_flow_height=max_height,
        max_velocity=max_velocity,
        max_pressure=max_pressure,
        final_h_solid=final_state.h_solid,
        final_h_fluid=final_state.h_fluid,
        final_u=final_state.u_solid,
        final_v=final_state.v_solid
    )
    
    metadata = {
        'cell_size': terrain.cell_size,
        'x_origin': terrain.x_origin,
        'y_origin': terrain.y_origin
    }
    exporter = ResultsExporter(output_dir, metadata)
    exported = exporter.export_results(results, format='npy')
    
    print(f"  Results saved to: {output_dir}")
    
    # 3D Animation
    print("\n[6/6] 3D Visualization...")
    if animate_3d or export_video:
        try:
            from src.visualization.dem_viewer import DEMViewer3D
            
            viewer = DEMViewer3D(terrain.elevation, terrain.cell_size)
            viewer.load_snapshots(snapshots, times)
            
            if export_video:
                # Ensure output directory exists
                Path(output_dir).mkdir(parents=True, exist_ok=True)
                video_path = Path(output_dir).resolve() / 'debris_flow.mp4'
                # Use forward slashes for ffmpeg compatibility on Windows
                viewer.export_animation(str(video_path).replace('\\', '/'))
            
            if animate_3d:
                print("  Opening 3D viewer...")
                viewer.show_static(max_height, f"PyDebFlow - {Path(dem_file).stem}")
                
        except ImportError as e:
            print(f"  ⚠ 3D visualization unavailable: {e}")
            print("    Install PyVista: pip install pyvista")
    
    print("\n✓ DEM simulation complete!")


def main():
    parser = argparse.ArgumentParser(
        description="PyDebFlow - Mass Flow Simulation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with synthetic terrain (quick demo)
  python run_simulation.py --synthetic-test
  python run_simulation.py --synthetic-test --t-end 120 --animate-3d
  
  # Run with real DEM file
  python run_simulation.py --dem-file terrain.tif --t-end 60
  python run_simulation.py --dem-file terrain.asc --animate-3d --export-video
  
  # Run component tests
  python run_simulation.py --test-all
        """
    )
    
    # Simulation options
    sim_group = parser.add_argument_group('Simulation')
    sim_group.add_argument('--synthetic-test', action='store_true',
                           help='Run simulation with synthetic terrain')
    sim_group.add_argument('--dem-file', type=str, metavar='PATH',
                           help='Path to DEM file (GeoTIFF or ASCII Grid)')
    sim_group.add_argument('--t-end', type=float, default=30.0,
                           help='Simulation end time in seconds (default: 30)')
    sim_group.add_argument('--output-dir', type=str, default='./output',
                           help='Output directory (default: ./output)')
    
    # Release zone
    release_group = parser.add_argument_group('Release Zone')
    release_group.add_argument('--release-row', type=int, metavar='I',
                               help='Release zone center row (auto if not set)')
    release_group.add_argument('--release-col', type=int, metavar='J',
                               help='Release zone center column (auto if not set)')
    release_group.add_argument('--release-radius', type=int, default=10,
                               help='Release zone radius in cells (default: 10)')
    release_group.add_argument('--release-height', type=float, default=5.0,
                               help='Release zone height in meters (default: 5.0)')
    
    # Visualization
    viz_group = parser.add_argument_group('Visualization')
    viz_group.add_argument('--animate-3d', action='store_true',
                           help='Show 3D PyVista animation')
    viz_group.add_argument('--export-video', action='store_true',
                           help='Export animation to MP4 video')
    viz_group.add_argument('--no-viz', action='store_true',
                           help='Disable all visualization')
    
    # Tests
    test_group = parser.add_argument_group('Testing')
    test_group.add_argument('--test-all', action='store_true',
                            help='Run all component tests')
    test_group.add_argument('--test-flow-model', action='store_true',
                            help='Test flow model')
    test_group.add_argument('--test-solver', action='store_true',
                            help='Test NOC-TVD solver')
    test_group.add_argument('--test-rheology', action='store_true',
                            help='Test rheology models')
    test_group.add_argument('--test-3d', action='store_true',
                            help='Test 3D visualization')
    
    args = parser.parse_args()
    
    # DEM simulation
    if args.dem_file:
        run_dem_simulation(
            dem_file=args.dem_file,
            output_dir=args.output_dir,
            t_end=args.t_end,
            release_i=args.release_row,
            release_j=args.release_col,
            release_radius=args.release_radius,
            release_height=args.release_height,
            animate_3d=args.animate_3d and not args.no_viz,
            export_video=args.export_video
        )
    elif args.synthetic_test:
        run_synthetic_test(
            output_dir=args.output_dir,
            t_end=args.t_end,
            visualize=not args.no_viz
        )
    elif args.test_all:
        test_all()
    elif args.test_flow_model:
        test_flow_model()
    elif args.test_solver:
        test_solver()
    elif args.test_rheology:
        test_rheology()
    elif args.test_3d:
        from src.visualization.dem_viewer import test_dem_viewer
        test_dem_viewer()
    else:
        parser.print_help()
        print("\n" + "=" * 50)
        print("Quick Start:")
        print("  python run_simulation.py --synthetic-test")
        print("  python run_simulation.py --dem-file your_dem.tif --animate-3d")
        print("=" * 50)


if __name__ == '__main__':
    main()
