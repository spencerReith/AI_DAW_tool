const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  call: (apiPath, options = {}) => ipcRenderer.invoke('api-call', { apiPath, ...options }),
});
