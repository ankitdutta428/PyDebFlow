/**
 * PyDebFlow TypeScript Type Definitions
 * ======================================
 * 
 * Type definitions for the PyDebFlow simulation API.
 */

/**
 * Configuration for terrain creation
 */
export interface TerrainConfig {
    /** Number of rows in the grid */
    rows: number;
    /** Number of columns in the grid */
    cols: number;
    /** Cell size in meters (default: 10.0) */
    cellSize?: number;
    /** Slope angle in degrees (default: 25.0) */
    slopeAngle?: number;
    /** Add a channel to the terrain (default: false) */
    addChannel?: boolean;
}

/**
 * Terrain data returned from Python
 */
export interface TerrainData {
    rows: number;
    cols: number;
    cellSize: number;
    elevation: number[][];
    elevationMin: number;
    elevationMax: number;
}

/**
 * Flow parameters for the simulation
 */
export interface FlowParameters {
    /** Solid phase density in kg/m³ (default: 2500) */
    solidDensity?: number;
    /** Fluid phase density in kg/m³ (default: 1100) */
    fluidDensity?: number;
    /** Basal friction angle in degrees (default: 22) */
    basalFrictionAngle?: number;
    /** Voellmy mu coefficient (default: 0.15) */
    voellmyMu?: number;
    /** Voellmy xi coefficient in m/s² (default: 500) */
    voellmyXi?: number;
}

/**
 * Release zone configuration
 */
export interface ReleaseZoneConfig {
    /** Center row index */
    centerI: number;
    /** Center column index */
    centerJ: number;
    /** Radius in cells */
    radius: number;
    /** Maximum height in meters */
    height: number;
    /** Solid fraction (0-1, default: 0.7) */
    solidFraction?: number;
}

/**
 * Solver configuration
 */
export interface SolverConfig {
    /** CFL number for stability (default: 0.4) */
    cflNumber?: number;
    /** Maximum timestep in seconds (default: 0.5) */
    maxTimestep?: number;
    /** Flux limiter type (default: 'minmod') */
    fluxLimiter?: 'minmod' | 'superbee' | 'vanleer';
}

/**
 * Simulation configuration
 */
export interface SimulationConfig {
    /** Simulation end time in seconds */
    tEnd: number;
    /** Output interval in seconds (default: 1.0) */
    outputInterval?: number;
}

/**
 * Snapshot of simulation state at a given time
 */
export interface SimulationSnapshot {
    /** Simulation time in seconds */
    time: number;
    /** Total flow height (solid + fluid) */
    height: number[][];
    /** Flow velocity magnitude */
    velocity: number[][];
}

/**
 * Final simulation results
 */
export interface SimulationResults {
    /** List of time snapshots */
    times: number[];
    /** Maximum flow height at each cell */
    maxHeight: number[][];
    /** Maximum velocity at each cell */
    maxVelocity: number[][];
    /** Maximum impact pressure at each cell (kPa) */
    maxPressure: number[][];
    /** Final solid height */
    finalSolidHeight: number[][];
    /** Final fluid height */
    finalFluidHeight: number[][];
    /** Initial volume in m³ */
    initialVolume: number;
    /** Final volume in m³ */
    finalVolume: number;
    /** Affected area in m² */
    affectedArea: number;
}

/**
 * Progress callback function type
 */
export type ProgressCallback = (progress: number, time: number, step: number) => void;

/**
 * PyDebFlow configuration options
 */
export interface PyDebFlowOptions {
    /** Path to Python executable (default: 'python') */
    pythonPath?: string;
    /** Path to PyDebFlow Python package (default: auto-detect) */
    packagePath?: string;
    /** Enable debug logging (default: false) */
    debug?: boolean;
}
