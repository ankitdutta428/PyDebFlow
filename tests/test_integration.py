"""
Integration tests for full simulation workflow.
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.terrain import Terrain
from src.core.flow_model import TwoPhaseFlowModel, FlowState, FlowParameters
from src.core.noc_tvd_solver import NOCTVDSolver, SolverConfig
from src.io.parameters import SimulationParameters
from src.io.results import ResultsExporter, SimulationResults
from src.io.raster_io import RasterIO


class TestFullSimulation:
    """Integration tests for complete simulation workflow."""
    
    def test_synthetic_debris_flow(self):
        """Test a complete debris flow simulation."""
        # Setup
        terrain = Terrain.create_synthetic_slope(
            rows=50, cols=40, cell_size=10.0, slope_angle=25.0
        )
        
        params = FlowParameters(
            solid_density=2500.0,
            fluid_density=1100.0,
            basal_friction_angle=20.0
        )
        model = TwoPhaseFlowModel(params)
        
        config = SolverConfig(cfl_number=0.4, max_timestep=0.5)
        solver = NOCTVDSolver(terrain, model, config)
        
        # Initial state
        state = FlowState.zeros((terrain.rows, terrain.cols))
        release = terrain.create_release_zone(10, 20, 5, 3.0)
        state.h_solid = release * 0.7
        state.h_fluid = release * 0.3
        
        initial_volume = (state.h_solid.sum() + state.h_fluid.sum()) * terrain.cell_size**2
        
        # Run simulation
        outputs = solver.run_simulation(
            state, t_end=5.0, output_interval=1.0
        )
        
        # Verify
        assert len(outputs) >= 5
        
        _, final_state = outputs[-1]
        final_volume = (final_state.h_solid.sum() + final_state.h_fluid.sum()) * terrain.cell_size**2
        
        # Volume should not increase
        assert final_volume <= initial_volume * 1.05
        
        # Heights remain non-negative
        assert (final_state.h_solid >= 0).all()
        assert (final_state.h_fluid >= 0).all()
    
    def test_results_export(self):
        """Test results export workflow."""
        # Quick simulation
        terrain = Terrain.create_synthetic_slope(rows=30, cols=30)
        model = TwoPhaseFlowModel()
        solver = NOCTVDSolver(terrain, model)
        
        state = FlowState.zeros((terrain.rows, terrain.cols))
        release = terrain.create_release_zone(5, 15, 3, 2.0)
        state.h_solid = release * 0.7
        state.h_fluid = release * 0.3
        
        outputs = solver.run_simulation(state, t_end=2.0, output_interval=0.5)
        
        # Create results
        max_height = np.zeros((terrain.rows, terrain.cols))
        max_velocity = np.zeros((terrain.rows, terrain.cols))
        max_pressure = np.zeros((terrain.rows, terrain.cols))
        
        for _, s in outputs:
            h_total = s.h_solid + s.h_fluid
            speed = np.sqrt(s.u_solid**2 + s.v_solid**2)
            pressure = model.compute_impact_pressure(s)
            
            max_height = np.maximum(max_height, h_total)
            max_velocity = np.maximum(max_velocity, speed)
            max_pressure = np.maximum(max_pressure, pressure)
        
        _, final_state = outputs[-1]
        
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
        
        # Export
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata = {'cell_size': terrain.cell_size}
            exporter = ResultsExporter(tmpdir, metadata)
            exported = exporter.export_results(results, format='npy')
            
            # Check files exist
            assert 'max_height' in exported
            assert 'summary' in exported
            assert Path(exported['max_height']).exists()
            assert Path(exported['summary']).exists()
    
    def test_parameter_save_load(self):
        """Test parameter serialization."""
        params = SimulationParameters.create_debris_flow_preset()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / 'params.json'
            yaml_path = Path(tmpdir) / 'params.yaml'
            
            # Save and load JSON
            params.save(str(json_path))
            loaded_json = SimulationParameters.load(str(json_path))
            
            assert loaded_json.flow.solid_density == params.flow.solid_density
            assert loaded_json.flow.basal_friction_angle == params.flow.basal_friction_angle
            
            # Save and load YAML
            params.save(str(yaml_path))
            loaded_yaml = SimulationParameters.load(str(yaml_path))
            
            assert loaded_yaml.flow.solid_density == params.flow.solid_density
    
    def test_raster_io_roundtrip(self):
        """Test raster save/load roundtrip."""
        data = np.random.rand(20, 25) * 100
        metadata = {
            'cell_size': 10.0,
            'x_origin': 500000.0,
            'y_origin': 4000000.0,
            'nodata': -9999
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # ASCII Grid
            asc_path = Path(tmpdir) / 'test.asc'
            RasterIO.write(str(asc_path), data, metadata)
            read_data, read_meta = RasterIO.read(str(asc_path))
            
            assert read_data.shape == data.shape
            assert np.allclose(read_data, data, rtol=1e-5)
            
            # NumPy
            npy_path = Path(tmpdir) / 'test.npy'
            RasterIO.write(str(npy_path), data, metadata)
            read_data, read_meta = RasterIO.read(str(npy_path))
            
            assert np.allclose(read_data, data)


class TestPresets:
    """Test simulation presets work correctly."""
    
    @pytest.mark.parametrize("preset_name,expected_density", [
        ("debris", 2500),
        ("avalanche", 300),
        ("lahar", 2700),
    ])
    def test_presets_density(self, preset_name, expected_density):
        """Test preset densities are correct."""
        if preset_name == "debris":
            params = SimulationParameters.create_debris_flow_preset()
        elif preset_name == "avalanche":
            params = SimulationParameters.create_avalanche_preset()
        else:
            params = SimulationParameters.create_lahar_preset()
        
        assert params.flow.solid_density == expected_density
    
    def test_presets_valid(self):
        """Test presets pass validation."""
        presets = [
            SimulationParameters.create_debris_flow_preset(),
            SimulationParameters.create_avalanche_preset(),
            SimulationParameters.create_lahar_preset(),
        ]
        
        for params in presets:
            issues = params.validate()
            assert len(issues) == 0, f"Preset has validation issues: {issues}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
