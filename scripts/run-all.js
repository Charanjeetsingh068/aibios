/**
 * AI-BOS Workspace Process Manager
 * Concurrently runs Next.js frontend and FastAPI backend dev servers.
 * Gracefully handles child termination to prevent orphaned ports.
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const isWin = process.platform === 'win32';

// Resolve project directories
const rootDir = path.resolve(__dirname, '..');
const backendDir = path.join(rootDir, 'backend');
const frontendDir = path.join(rootDir, 'frontend');

console.log('\x1b[36m%s\x1b[0m', '==========================================================');
console.log('\x1b[36m%s\x1b[0m', '   AI-BOS Enterprise Console Orchestrator Server          ');
console.log('\x1b[36m%s\x1b[0m', '==========================================================');

// Resolve the Python executable inside the virtual environment
let pythonExec = isWin ? 'venv\\Scripts\\python.exe' : 'venv/bin/python';
const venvPythonPath = path.join(backendDir, pythonExec);

if (fs.existsSync(venvPythonPath)) {
  pythonExec = venvPythonPath;
  console.log('\x1b[32m%s\x1b[0m', `[System] Using Python virtual environment: ${pythonExec}`);
} else {
  pythonExec = isWin ? 'python' : 'python3';
  console.log('\x1b[33m%s\x1b[0m', `[System] Warning: Virtual environment not found at ${venvPythonPath}. Falling back to system: ${pythonExec}`);
}

// 1. Spawn FastAPI Backend Server
console.log('\x1b[35m%s\x1b[0m', '[Backend] Starting FastAPI REST Gateway...');
const backendProcess = spawn(pythonExec, ['-m', 'uvicorn', 'app.main:app', '--reload', '--port', '8000'], {
  cwd: backendDir,
  shell: true,
  stdio: 'inherit'
});

// 2. Spawn Next.js Frontend Server
console.log('\x1b[34m%s\x1b[0m', '[Frontend] Starting Next.js Dev Server...');
const frontendProcess = spawn(isWin ? 'npm.cmd' : 'npm', ['run', 'dev'], {
  cwd: frontendDir,
  shell: true,
  stdio: 'inherit'
});

// Monitor process exits to alert if one server crashes unexpectedly
backendProcess.on('exit', (code) => {
  if (code !== null && code !== 0) {
    console.error('\x1b[31m%s\x1b[0m', `[Backend] Process exited unexpectedly with code ${code}`);
    cleanup();
  }
});

frontendProcess.on('exit', (code) => {
  if (code !== null && code !== 0) {
    console.error('\x1b[31m%s\x1b[0m', `[Frontend] Process exited unexpectedly with code ${code}`);
    cleanup();
  }
});

let isShuttingDown = false;

// Cleanup function to kill child processes cleanly
function cleanup() {
  if (isShuttingDown) return;
  isShuttingDown = true;

  console.log('\n\x1b[36m%s\x1b[0m', '[System] Gracefully shutting down child processes...');

  // Use taskkill on Windows to ensure the entire process tree is terminated
  if (isWin) {
    if (backendProcess.pid) {
      spawn('taskkill', ['/pid', backendProcess.pid, '/f', '/t'], { stdio: 'ignore' });
    }
    if (frontendProcess.pid) {
      spawn('taskkill', ['/pid', frontendProcess.pid, '/f', '/t'], { stdio: 'ignore' });
    }
  } else {
    backendProcess.kill('SIGTERM');
    frontendProcess.kill('SIGTERM');
  }

  console.log('\x1b[32m%s\x1b[0m', '[System] Servers successfully terminated.');
  process.exit();
}

// Bind termination signals to cleanup
process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);
process.on('SIGHUP', cleanup);
process.on('exit', cleanup);
