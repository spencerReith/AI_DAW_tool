const { app, BrowserWindow, ipcMain } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

const FLASK_PORT = 5001;
let flaskProcess = null;

function startFlask() {
  const python = path.join(__dirname, '../venv/bin/python');
  const script = path.join(__dirname, '../backend/app.py');
  flaskProcess = spawn(python, [script]);
  flaskProcess.stderr.on('data', (d) => process.stderr.write(d));
}

function createWindow() {
  const win = new BrowserWindow({
    width: 900,
    height: 680,
    title: '',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
    },
  });
  win.loadURL('http://localhost:5173');
}

// Proxy JSON API calls to Flask
ipcMain.handle('api-call', async (_, { method = 'GET', apiPath, body }) => {
  const res = await fetch(`http://localhost:${FLASK_PORT}${apiPath}`, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  return res.json();
});

app.whenReady().then(() => {
  startFlask();
  createWindow();
});

app.on('window-all-closed', () => {
  flaskProcess?.kill();
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
