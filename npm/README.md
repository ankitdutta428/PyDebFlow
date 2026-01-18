# PyDebFlow (npm)

JavaScript/TypeScript wrapper for [PyDebFlow](https://github.com/ankitdutta428/PyDebFlow) - Advanced Two-Phase Mass Flow Simulation.

## Prerequisites

- **Node.js** >= 16.0.0
- **Python** >= 3.10 with PyDebFlow installed

```bash
pip install pydebflow
```

## Installation

```bash
npm install pydebflow
```

## Quick Start

```typescript
import { PyDebFlow } from 'pydebflow';

async function main() {
  const sim = new PyDebFlow();
  
  // Check installation
  const status = await sim.checkInstallation();
  console.log('PyDebFlow version:', status.version);
  
  // Create synthetic terrain
  const terrain = await sim.createSyntheticSlope({
    rows: 80,
    cols: 60,
    cellSize: 10.0,
    slopeAngle: 25.0,
    addChannel: true,
  });
  
  // Run simulation
  const results = await sim.runSimulation(
    terrain,
    { centerI: 15, centerJ: 30, radius: 8, height: 5.0 },
    { tEnd: 30 }
  );
  
  console.log('Max flow height:', Math.max(...results.maxHeight.flat()));
  console.log('Affected area:', results.affectedArea, 'm²');
}

main();
```

## API

### `new PyDebFlow(options?)`

Create a new PyDebFlow instance.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `pythonPath` | `string` | `'python'` | Path to Python executable |
| `debug` | `boolean` | `false` | Enable debug logging |

### `checkInstallation(): Promise<object>`

Check if Python and PyDebFlow are installed.

### `getVersion(): Promise<string>`

Get PyDebFlow version.

### `createSyntheticSlope(config): Promise<TerrainData>`

Create synthetic terrain for testing.

```typescript
const terrain = await sim.createSyntheticSlope({
  rows: 80,
  cols: 60,
  cellSize: 10.0,    // meters
  slopeAngle: 25.0,  // degrees
  addChannel: true,
});
```

### `loadTerrain(filePath): Promise<TerrainData>`

Load terrain from a DEM file (GeoTIFF or ASCII Grid).

```typescript
const terrain = await sim.loadTerrain('/path/to/dem.tif');
```

### `runSimulation(terrain, releaseZone, simConfig, flowParams?, solverConfig?): Promise<SimulationResults>`

Run a complete debris flow simulation.

```typescript
const results = await sim.runSimulation(
  terrain,
  { centerI: 15, centerJ: 30, radius: 8, height: 5.0 },
  { tEnd: 60, outputInterval: 2.0 },
  { solidDensity: 2500, fluidDensity: 1100 },
  { cflNumber: 0.4, fluxLimiter: 'minmod' }
);
```

### `runSyntheticTest(tEnd?): Promise<SimulationResults>`

Run a quick synthetic test simulation.

```typescript
const results = await sim.runSyntheticTest(30);
```

## TypeScript Types

All types are exported:

```typescript
import {
  TerrainConfig,
  TerrainData,
  FlowParameters,
  ReleaseZoneConfig,
  SolverConfig,
  SimulationConfig,
  SimulationResults,
} from 'pydebflow';
```

## License

AGPL-3.0
