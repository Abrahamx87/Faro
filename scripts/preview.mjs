// Adaptador de vista previa; la aplicación se inicia normalmente con python -m faro.
import { existsSync } from 'node:fs';
import { spawn } from 'node:child_process';
import { resolve } from 'node:path';
const runtimePython = '/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python';
const python = process.env.FARO_PYTHON || process.env.CODEX_PRIMARY_RUNTIME_PYTHON || (existsSync(runtimePython) ? runtimePython : process.platform === 'win32' ? 'python' : 'python3');
const args = process.argv.slice(2).filter(a => a !== '--strictPort');
const env = {...process.env};
const previewDeps = resolve('.preview-deps');
if (existsSync(previewDeps)) env.PYTHONPATH = previewDeps + (env.PYTHONPATH ? (process.platform === 'win32' ? ';' : ':') + env.PYTHONPATH : '');
const child = spawn(python, ['-m', 'faro', 'serve', ...args], {stdio:'inherit', env});
child.on('exit', code => process.exit(code || 0));
child.on('error', err => { console.error(err.message); process.exit(1); });
process.on('SIGTERM', () => child.kill('SIGTERM'));
process.on('SIGINT', () => child.kill('SIGINT'));
