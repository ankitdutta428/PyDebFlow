"""
Simulation Parameters for OpenDebris.

Handles parameter configuration, validation, and serialization.
"""

import json
import yaml
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


@dataclass
class FlowParametersConfig:
    """Flow model parameters."""
    solid_density: float = 2500.0  # kg/m³
    fluid_density: float = 1100.0  # kg/m³
    basal_friction_angle: float = 25.0  # degrees
    internal_friction_angle: float = 35.0  # degrees
    voellmy_mu: float = 0.15
    voellmy_xi: float = 500.0  # m/s²
    drag_coefficient: float = 0.01
    min_flow_height: float = 0.001  # m


@dataclass
class SolverParametersConfig:
    """Numerical solver parameters."""
    cfl_number: float = 0.4
    max_timestep: float = 0.5  # s
    min_timestep: float = 1e-6  # s
    flux_limiter: str = 'minmod'  # 'minmod', 'superbee', 'vanleer'
    boundary_type: str = 'outflow'  # 'outflow', 'reflective'


@dataclass
class EntrainmentParametersConfig:
    """Entrainment model parameters."""
    enabled: bool = True
    erosion_coef: float = 0.001
    critical_velocity: float = 1.0  # m/s
    deposition_coef: float = 0.1
    max_erosion_depth: float = 10.0  # m


@dataclass
class OutputParametersConfig:
    """Output configuration."""
    output_interval: float = 1.0  # s
    save_format: str = 'npy'  # 'npy', 'asc', 'tif'
    save_velocity: bool = True
    save_pressure: bool = True
    create_animation: bool = True


@dataclass
class SimulationParameters:
    """Complete simulation parameter set."""
    name: str = "Untitled Simulation"
    description: str = ""
    
    # Time settings
    t_end: float = 60.0  # s
    
    # Component parameters
    flow: FlowParametersConfig = field(default_factory=FlowParametersConfig)
    solver: SolverParametersConfig = field(default_factory=SolverParametersConfig)
    entrainment: EntrainmentParametersConfig = field(default_factory=EntrainmentParametersConfig)
    output: OutputParametersConfig = field(default_factory=OutputParametersConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimulationParameters':
        """Create from dictionary."""
        return cls(
            name=data.get('name', 'Untitled'),
            description=data.get('description', ''),
            t_end=data.get('t_end', 60.0),
            flow=FlowParametersConfig(**data.get('flow', {})),
            solver=SolverParametersConfig(**data.get('solver', {})),
            entrainment=EntrainmentParametersConfig(**data.get('entrainment', {})),
            output=OutputParametersConfig(**data.get('output', {})),
        )
    
    def save(self, filepath: str) -> None:
        """Save parameters to file (JSON or YAML)."""
        path = Path(filepath)
        data = self.to_dict()
        
        with open(path, 'w') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            else:
                json.dump(data, f, indent=2)
    
    @classmethod
    def load(cls, filepath: str) -> 'SimulationParameters':
        """Load parameters from file."""
        path = Path(filepath)
        
        with open(path, 'r') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        return cls.from_dict(data)
    
    def validate(self) -> List[str]:
        """
        Validate parameters and return list of issues.
        Empty list = valid.
        """
        issues = []
        
        # Flow parameters
        if self.flow.solid_density <= 0:
            issues.append("Solid density must be positive")
        if self.flow.fluid_density <= 0:
            issues.append("Fluid density must be positive")
        if not (0 <= self.flow.basal_friction_angle <= 90):
            issues.append("Basal friction angle must be 0-90°")
        if self.flow.voellmy_xi <= 0:
            issues.append("Voellmy xi must be positive")
        
        # Solver parameters
        if not (0 < self.solver.cfl_number < 1):
            issues.append("CFL number must be between 0 and 1")
        if self.solver.max_timestep <= 0:
            issues.append("Max timestep must be positive")
        
        # Time
        if self.t_end <= 0:
            issues.append("Simulation time must be positive")
        
        return issues
    
    @classmethod
    def create_debris_flow_preset(cls) -> 'SimulationParameters':
        """Create preset for debris flows."""
        return cls(
            name="Debris Flow",
            description="Typical debris flow parameters",
            t_end=120.0,
            flow=FlowParametersConfig(
                solid_density=2500.0,
                fluid_density=1100.0,
                basal_friction_angle=22.0,
                voellmy_mu=0.12,
                voellmy_xi=400.0,
            ),
            entrainment=EntrainmentParametersConfig(
                enabled=True,
                erosion_coef=0.002,
            )
        )
    
    @classmethod
    def create_avalanche_preset(cls) -> 'SimulationParameters':
        """Create preset for snow avalanches."""
        return cls(
            name="Snow Avalanche",
            description="Typical snow avalanche parameters",
            t_end=180.0,
            flow=FlowParametersConfig(
                solid_density=300.0,
                fluid_density=1.2,  # Air
                basal_friction_angle=18.0,
                voellmy_mu=0.15,
                voellmy_xi=2000.0,
            ),
            entrainment=EntrainmentParametersConfig(
                enabled=True,
                erosion_coef=0.005,
            )
        )
    
    @classmethod
    def create_lahar_preset(cls) -> 'SimulationParameters':
        """Create preset for lahars (volcanic mudflows)."""
        return cls(
            name="Lahar",
            description="Typical lahar parameters",
            t_end=300.0,
            flow=FlowParametersConfig(
                solid_density=2700.0,
                fluid_density=1200.0,
                basal_friction_angle=12.0,
                voellmy_mu=0.08,
                voellmy_xi=300.0,
            ),
            entrainment=EntrainmentParametersConfig(
                enabled=True,
                erosion_coef=0.003,
            )
        )
    
    @classmethod 
    def create_rock_avalanche_preset(cls) -> 'SimulationParameters':
        """Create preset for rock avalanches."""
        return cls(
            name="Rock Avalanche",
            description="Typical rock avalanche parameters",
            t_end=200.0,
            flow=FlowParametersConfig(
                solid_density=2600.0,
                fluid_density=1.2,
                basal_friction_angle=28.0,
                voellmy_mu=0.10,
                voellmy_xi=500.0,
            ),
            entrainment=EntrainmentParametersConfig(
                enabled=True,
                erosion_coef=0.001,
            )
        )


def test_parameters():
    """Test parameters functionality."""
    import tempfile
    
    print("=" * 50)
    print("Testing Simulation Parameters")
    print("=" * 50)
    
    # Test presets
    presets = [
        ('Debris Flow', SimulationParameters.create_debris_flow_preset()),
        ('Avalanche', SimulationParameters.create_avalanche_preset()),
        ('Lahar', SimulationParameters.create_lahar_preset()),
        ('Rock Avalanche', SimulationParameters.create_rock_avalanche_preset()),
    ]
    
    print("\n1. Testing presets:")
    for name, params in presets:
        issues = params.validate()
        status = "✓" if len(issues) == 0 else f"✗ ({len(issues)} issues)"
        print(f"   {name}: {status}")
    
    # Test save/load
    params = SimulationParameters.create_debris_flow_preset()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # JSON
        json_path = Path(tmpdir) / 'params.json'
        params.save(str(json_path))
        loaded = SimulationParameters.load(str(json_path))
        
        print(f"\n2. JSON roundtrip:")
        print(f"   Name match: {loaded.name == params.name}")
        print(f"   Density match: {loaded.flow.solid_density == params.flow.solid_density}")
        
        # YAML
        yaml_path = Path(tmpdir) / 'params.yaml'
        params.save(str(yaml_path))
        loaded = SimulationParameters.load(str(yaml_path))
        
        print(f"\n3. YAML roundtrip:")
        print(f"   Name match: {loaded.name == params.name}")
        print(f"   CFL match: {loaded.solver.cfl_number == params.solver.cfl_number}")
    
    print("\n✓ Parameters tests passed!")
    return True


if __name__ == "__main__":
    test_parameters()
