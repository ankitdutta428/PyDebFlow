/**
 * PyDebFlow - JavaScript API
 * ==========================
 * 
 * Main entry point for the PyDebFlow npm package.
 * Provides a JavaScript wrapper around the Python simulation library.
 */

import { PythonBridge } from './bridge';
import {
    PyDebFlowOptions,
    TerrainConfig,
    TerrainData,
    FlowParameters,
    ReleaseZoneConfig,
    SolverConfig,
    SimulationConfig,
    SimulationResults,
    ProgressCallback,
} from './types';

export * from './types';

/**
 * PyDebFlow - Mass Flow Simulation Library
 * 
 * @example
 * ```typescript
 * import { PyDebFlow } from 'pydebflow';
 * 
 * const sim = new PyDebFlow();
 * const terrain = await sim.createSyntheticSlope({ rows: 80, cols: 60 });
 * const results = await sim.runSimulation(terrain, { tEnd: 30 });
 * ```
 */
export class PyDebFlow {
    private bridge: PythonBridge;

    constructor(options: PyDebFlowOptions = {}) {
        this.bridge = new PythonBridge(options);
    }

    /**
     * Check if Python and PyDebFlow are properly installed
     */
    async checkInstallation(): Promise<{ python: boolean; pydebflow: boolean; version: string }> {
        return this.bridge.checkInstallation();
    }

    /**
     * Get the PyDebFlow version
     */
    async getVersion(): Promise<string> {
        const result = await this.bridge.execute<{ version: string }>(`
from src import __version__
import json
print(json.dumps({"version": __version__}))
`);
        return result.version;
    }

    /**
     * Create synthetic terrain for testing
     */
    async createSyntheticSlope(config: TerrainConfig): Promise<TerrainData> {
        const { rows, cols, cellSize = 10.0, slopeAngle = 25.0, addChannel = false } = config;

        return this.bridge.execute<TerrainData>(`
import json
from src import Terrain

terrain = Terrain.create_synthetic_slope(
    rows=${rows},
    cols=${cols},
    cell_size=${cellSize},
    slope_angle=${slopeAngle},
    add_channel=${addChannel ? 'True' : 'False'}
)

result = {
    "rows": terrain.rows,
    "cols": terrain.cols,
    "cellSize": terrain.cell_size,
    "elevation": terrain.elevation.tolist(),
    "elevationMin": float(terrain.elevation.min()),
    "elevationMax": float(terrain.elevation.max())
}
print(json.dumps(result))
`);
    }

    /**
     * Load terrain from a DEM file (GeoTIFF or ASCII Grid)
     */
    async loadTerrain(filePath: string): Promise<TerrainData> {
        const escapedPath = filePath.replace(/\\/g, '\\\\');

        return this.bridge.execute<TerrainData>(`
import json
from src import Terrain

terrain = Terrain.load("${escapedPath}")

result = {
    "rows": terrain.rows,
    "cols": terrain.cols,
    "cellSize": terrain.cell_size,
    "elevation": terrain.elevation.tolist(),
    "elevationMin": float(terrain.elevation.min()),
    "elevationMax": float(terrain.elevation.max())
}
print(json.dumps(result))
`);
    }

    /**
     * Run a complete simulation
     */
    async runSimulation(
        terrain: TerrainData,
        releaseZone: ReleaseZoneConfig,
        simConfig: SimulationConfig,
        flowParams: FlowParameters = {},
        solverConfig: SolverConfig = {}
    ): Promise<SimulationResults> {
        const {
            solidDensity = 2500.0,
            fluidDensity = 1100.0,
            basalFrictionAngle = 22.0,
            voellmyMu = 0.15,
            voellmyXi = 500.0,
        } = flowParams;

        const {
            cflNumber = 0.4,
            maxTimestep = 0.5,
            fluxLimiter = 'minmod',
        } = solverConfig;

        const {
            tEnd,
            outputInterval = 1.0,
        } = simConfig;

        const {
            centerI,
            centerJ,
            radius,
            height,
            solidFraction = 0.7,
        } = releaseZone;

        // Convert elevation array to Python list string
        const elevationStr = JSON.stringify(terrain.elevation);

        return this.bridge.execute<SimulationResults>(`
import json
import numpy as np
from src import (
    Terrain, TwoPhaseFlowModel, FlowParameters,
    FlowState, NOCTVDSolver, SolverConfig
)

# Recreate terrain
elevation = np.array(${elevationStr})
terrain = Terrain(elevation, cell_size=${terrain.cellSize})

# Flow parameters
params = FlowParameters(
    solid_density=${solidDensity},
    fluid_density=${fluidDensity},
    basal_friction_angle=${basalFrictionAngle},
    voellmy_mu=${voellmyMu},
    voellmy_xi=${voellmyXi}
)

# Model and solver
model = TwoPhaseFlowModel(params)
solver_config = SolverConfig(
    cfl_number=${cflNumber},
    max_timestep=${maxTimestep},
    flux_limiter="${fluxLimiter}"
)
solver = NOCTVDSolver(terrain, model, solver_config)

# Release zone
state = FlowState.zeros((${terrain.rows}, ${terrain.cols}))
release = terrain.create_release_zone(${centerI}, ${centerJ}, ${radius}, ${height})
state.h_solid = release * ${solidFraction}
state.h_fluid = release * ${1 - solidFraction}
initial_volume = (state.h_solid.sum() + state.h_fluid.sum()) * terrain.cell_size**2

# Run simulation
outputs = solver.run_simulation(
    state,
    t_end=${tEnd},
    output_interval=${outputInterval}
)

# Process results
max_height = np.zeros((${terrain.rows}, ${terrain.cols}))
max_velocity = np.zeros((${terrain.rows}, ${terrain.cols}))
max_pressure = np.zeros((${terrain.rows}, ${terrain.cols}))

for t, s in outputs:
    h_total = s.h_solid + s.h_fluid
    speed = np.sqrt(s.u_solid**2 + s.v_solid**2)
    pressure = model.compute_impact_pressure(s)
    
    max_height = np.maximum(max_height, h_total)
    max_velocity = np.maximum(max_velocity, speed)
    max_pressure = np.maximum(max_pressure, pressure)

_, final_state = outputs[-1]
final_height = final_state.h_solid + final_state.h_fluid
final_volume = final_height.sum() * terrain.cell_size**2
affected_area = np.sum(max_height > 0.1) * terrain.cell_size**2

result = {
    "times": [t for t, _ in outputs],
    "maxHeight": max_height.tolist(),
    "maxVelocity": max_velocity.tolist(),
    "maxPressure": max_pressure.tolist(),
    "finalSolidHeight": final_state.h_solid.tolist(),
    "finalFluidHeight": final_state.h_fluid.tolist(),
    "initialVolume": float(initial_volume),
    "finalVolume": float(final_volume),
    "affectedArea": float(affected_area)
}
print(json.dumps(result))
`);
    }

    /**
     * Run a quick synthetic test simulation
     */
    async runSyntheticTest(tEnd: number = 30): Promise<SimulationResults> {
        const terrain = await this.createSyntheticSlope({
            rows: 80,
            cols: 60,
            cellSize: 10.0,
            slopeAngle: 25.0,
            addChannel: true,
        });

        return this.runSimulation(
            terrain,
            { centerI: 15, centerJ: 30, radius: 8, height: 5.0 },
            { tEnd, outputInterval: 1.0 }
        );
    }
}

// Default export
export default PyDebFlow;
