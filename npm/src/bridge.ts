/**
 * PyDebFlow Python Bridge
 * =======================
 * 
 * Handles communication with Python subprocess.
 */

import { spawn } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import { PyDebFlowOptions } from './types';

/**
 * Bridge to Python subprocess for running PyDebFlow commands
 */
export class PythonBridge {
    private pythonPath: string;
    private packagePath: string;
    private debug: boolean;

    constructor(options: PyDebFlowOptions = {}) {
        this.pythonPath = options.pythonPath || 'python';
        this.packagePath = options.packagePath || this.detectPackagePath();
        this.debug = options.debug || false;
    }

    /**
     * Auto-detect the PyDebFlow package path
     */
    private detectPackagePath(): string {
        // Try to find pydebflow in common locations
        const possiblePaths = [
            path.join(__dirname, '..', '..', '..'), // Development: npm/../..
            path.join(__dirname, '..', '..', 'python'), // Installed: npm/python
        ];

        // Return first existing path or empty string (rely on pip-installed pydebflow)
        for (const p of possiblePaths) {
            try {
                fs.accessSync(p);
                return p;
            } catch {
                // Path doesn't exist, continue
            }
        }
        return '';
    }

    /**
     * Execute a Python script and return the result
     */
    async execute<T>(script: string): Promise<T> {
        return new Promise((resolve, reject) => {
            const fullScript = `
import sys
import json
sys.path.insert(0, '${this.packagePath.replace(/\\/g, '\\\\')}')
${script}
`;

            if (this.debug) {
                console.log('[PyDebFlow] Executing Python script:');
                console.log(fullScript);
            }

            const process = spawn(this.pythonPath, ['-c', fullScript], {
                stdio: ['pipe', 'pipe', 'pipe'],
            });

            let stdout = '';
            let stderr = '';

            process.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            process.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            process.on('close', (code) => {
                if (this.debug) {
                    console.log('[PyDebFlow] Exit code:', code);
                    console.log('[PyDebFlow] stdout:', stdout);
                    if (stderr) console.log('[PyDebFlow] stderr:', stderr);
                }

                if (code !== 0) {
                    reject(new Error(`Python process exited with code ${code}: ${stderr}`));
                    return;
                }

                try {
                    // Find JSON output (last line that starts with { or [)
                    const lines = stdout.trim().split('\n');
                    let jsonLine = '';
                    for (let i = lines.length - 1; i >= 0; i--) {
                        const line = lines[i].trim();
                        if (line.startsWith('{') || line.startsWith('[')) {
                            jsonLine = line;
                            break;
                        }
                    }

                    if (!jsonLine) {
                        // No JSON output, return raw stdout
                        resolve(stdout.trim() as unknown as T);
                        return;
                    }

                    const result = JSON.parse(jsonLine);
                    resolve(result as T);
                } catch (error) {
                    reject(new Error(`Failed to parse Python output: ${error}`));
                }
            });

            process.on('error', (error) => {
                reject(new Error(`Failed to start Python process: ${error.message}`));
            });
        });
    }

    /**
     * Check if Python and PyDebFlow are available
     */
    async checkInstallation(): Promise<{ python: boolean; pydebflow: boolean; version: string }> {
        try {
            const result = await this.execute<{ version: string }>(`
try:
    from src import __version__
    print(json.dumps({"version": __version__}))
except ImportError:
    try:
        import pydebflow
        print(json.dumps({"version": pydebflow.__version__}))
    except ImportError:
        print(json.dumps({"version": "not_installed"}))
`);
            return {
                python: true,
                pydebflow: result.version !== 'not_installed',
                version: result.version,
            };
        } catch (error) {
            return {
                python: false,
                pydebflow: false,
                version: 'unknown',
            };
        }
    }
}
