import {loadPyodide} from './runtime/pyodide.mjs';

const path = '/tmp/faro-input.bin';
let runtime;

async function init() {
  const py = await loadPyodide({indexURL: new URL('./runtime/', import.meta.url).href});
  const response = await fetch(new URL('./faro-engine.zip', import.meta.url));
  if (!response.ok) throw new Error('No se encontró el motor de análisis.');
  py.unpackArchive(await response.arrayBuffer(), 'zip', {extractDir: '/faro-engine'});
  py.runPython(`
import json, sys
sys.path.insert(0, '/faro-engine')
import pypdf
from faro_engine import analyze as _faro_analyze

def _faro_report(filename):
    with open('/tmp/faro-input.bin', 'rb') as stream:
        return json.dumps(_faro_analyze(stream.read(), filename), ensure_ascii=True)
`);
  return py;
}

self.addEventListener('message', async ({data}) => {
  try {
    if (data.type === 'init') {
      runtime ||= init();
      await runtime;
      self.postMessage({id: data.id, result: true});
      return;
    }
    if (data.type !== 'analyze' || !runtime) throw new Error('El motor aún no está disponible.');
    const py = await runtime;
    const buffer = new Uint8Array(data.bytes);
    if (!buffer.length || buffer.length > 10 * 1024 * 1024) throw new Error('Tamaño de archivo no válido.');
    try {
      py.FS.writeFile(path, buffer);
      py.globals.set('_faro_filename', data.name);
      const report = JSON.parse(py.runPython('_faro_report(_faro_filename)'));
      self.postMessage({id: data.id, result: report});
    } finally {
      if (py.FS.analyzePath(path).exists) py.FS.unlink(path);
      py.globals.delete('_faro_filename');
    }
  } catch (_) {
    self.postMessage({id: data.id, error: data.type === 'init'
      ? 'No se pudo iniciar el motor local. Recarga la página o prueba con un navegador actualizado.'
      : 'El análisis se detuvo. El archivo no fue evaluado completamente.'});
  }
});
