const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  // заглушки, позже дополним IPC-вызовами
  ping: () => ipcRenderer.invoke('ping')
});

