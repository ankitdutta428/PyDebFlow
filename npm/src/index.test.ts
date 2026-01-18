/**
 * PyDebFlow Tests
 * ================
 */

import { PyDebFlow } from './index';

describe('PyDebFlow', () => {
    let pydebflow: PyDebFlow;

    beforeAll(() => {
        pydebflow = new PyDebFlow({ debug: false });
    });

    describe('constructor', () => {
        it('should create a PyDebFlow instance', () => {
            expect(pydebflow).toBeInstanceOf(PyDebFlow);
        });

        it('should accept custom options', () => {
            const customInstance = new PyDebFlow({
                pythonPath: 'python3',
                debug: true,
            });
            expect(customInstance).toBeInstanceOf(PyDebFlow);
        });
    });

    describe('checkInstallation', () => {
        it('should check if Python is available', async () => {
            const result = await pydebflow.checkInstallation();

            expect(result).toHaveProperty('python');
            expect(result).toHaveProperty('pydebflow');
            expect(result).toHaveProperty('version');
            expect(typeof result.python).toBe('boolean');
            expect(typeof result.pydebflow).toBe('boolean');
        }, 30000);
    });

    describe('getVersion', () => {
        it('should return version string', async () => {
            const result = await pydebflow.checkInstallation();
            if (!result.pydebflow) {
                console.log('PyDebFlow not installed, skipping test');
                return;
            }

            const version = await pydebflow.getVersion();
            expect(typeof version).toBe('string');
            expect(version).toMatch(/^\d+\.\d+\.\d+/);
        }, 30000);
    });

    describe('createSyntheticSlope', () => {
        it('should create synthetic terrain', async () => {
            const result = await pydebflow.checkInstallation();
            if (!result.pydebflow) {
                console.log('PyDebFlow not installed, skipping test');
                return;
            }

            const terrain = await pydebflow.createSyntheticSlope({
                rows: 20,
                cols: 15,
                cellSize: 10.0,
                slopeAngle: 20.0,
            });

            expect(terrain.rows).toBe(20);
            expect(terrain.cols).toBe(15);
            expect(terrain.cellSize).toBe(10.0);
            expect(terrain.elevation).toHaveLength(20);
            expect(terrain.elevation[0]).toHaveLength(15);
            expect(terrain.elevationMin).toBeLessThan(terrain.elevationMax);
        }, 60000);
    });
});

describe('Type exports', () => {
    it('should export all types', async () => {
        // This test ensures types are properly exported
        const types = await import('./types');
        expect(types).toBeDefined();
    });
});

