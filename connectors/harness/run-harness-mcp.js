/**
 * Cursor MCP entry: load .env, spawn harness-mcp-v2 with inherited stdio.
 * PowerShell wrappers often break MCP stdio on Windows; Node spawn is reliable.
 */
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const root = __dirname;
const envPath = path.join(root, '.env');

if (!fs.existsSync(envPath)) {
  console.error(`Missing ${envPath} — copy .env.example to .env and set HARNESS_API_KEY.`);
  process.exit(1);
}

for (const line of fs.readFileSync(envPath, 'utf8').split(/\r?\n/)) {
  const trimmed = line.trim();
  if (!trimmed || trimmed.startsWith('#')) continue;
  const eq = trimmed.indexOf('=');
  if (eq < 1) continue;
  const key = trimmed.slice(0, eq).trim();
  const value = trimmed.slice(eq + 1).trim();
  if (key) process.env[key] = value;
}

if (!process.env.HARNESS_API_KEY) {
  console.error('HARNESS_API_KEY is empty in .env');
  process.exit(1);
}

const nodeDir = path.dirname(process.execPath);
const npx = path.join(nodeDir, process.platform === 'win32' ? 'npx.cmd' : 'npx');
process.env.PATH = `${nodeDir}${path.delimiter}${process.env.PATH || ''}`;

const child = spawn(npx, ['-y', 'harness-mcp-v2@latest'], {
  cwd: root,
  env: process.env,
  stdio: 'inherit',
  shell: process.platform === 'win32',
});

child.on('error', (err) => {
  console.error(err);
  process.exit(1);
});

child.on('exit', (code, signal) => {
  if (signal) process.exit(1);
  process.exit(code === null ? 1 : code);
});
