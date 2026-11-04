/* Transporte de la edición web: los bytes se transfieren solo a un Web Worker. */
(() => {
  'use strict';
  const asset = (path) => new URL(path, document.baseURI);
  const demos = new Set(['legitimo.pdf', 'verificacion.html', 'contenido_disfrazado.pdf']);
  let worker = null;
  let ready = null;
  let sequence = 0;
  const pending = new Map();

  function stop(message) {
    worker?.terminate();
    worker = null;
    ready = null;
    for (const {reject, timer} of pending.values()) {
      clearTimeout(timer);
      reject(new Error(message));
    }
    pending.clear();
  }

  function request(type, payload, timeout, transfers = []) {
    return new Promise((resolve, reject) => {
      const id = ++sequence;
      const timer = setTimeout(() => stop(type === 'init'
        ? 'El motor tardó demasiado en iniciar. Revisa tu conexión y vuelve a intentarlo.'
        : 'El análisis superó 15 segundos y se detuvo. El archivo no fue evaluado completamente.'), timeout);
      pending.set(id, {resolve, reject, timer});
      try { worker.postMessage({id, type, ...payload}, transfers); }
      catch (_) { stop('No se pudo iniciar el análisis en este navegador.'); }
    });
  }

  function init() {
    if (ready) return ready;
    if (!('Worker' in window) || !('WebAssembly' in window)) {
      return Promise.reject(new Error('Este navegador no admite el motor local de Faro.'));
    }
    worker = new Worker(asset('./worker.mjs'), {type: 'module'});
    worker.addEventListener('error', () => stop('No se pudo cargar el motor. Intenta recargar la página con un navegador actualizado.'));
    worker.addEventListener('message', ({data}) => {
      const reply = pending.get(data.id);
      if (!reply) return;
      clearTimeout(reply.timer);
      pending.delete(data.id);
      data.error ? reply.reject(new Error(data.error)) : reply.resolve(data.result);
    });
    ready = request('init', {}, 60000).catch(error => { stop(error.message); throw error; });
    return ready;
  }

  window.faroTransport = {
    async health() {
      await init();
      return 'Motor listo en tu navegador';
    },
    async analyze(path, file, headers) {
      let name, bytes;
      await init();
      if (path === '/api/demo') {
        name = headers['X-Demo'];
        if (!demos.has(name)) throw new Error('Ejemplo desconocido.');
        const response = await fetch(asset(`./samples/${name}.bin`), {signal: AbortSignal.timeout(15000)});
        if (!response.ok) throw new Error('No se pudo cargar el ejemplo de demostración.');
        bytes = await response.arrayBuffer();
      } else {
        name = file.name;
        bytes = await file.arrayBuffer();
      }
      if (!bytes.byteLength || bytes.byteLength > 10 * 1024 * 1024) throw new Error('Selecciona un archivo no vacío de hasta 10 MiB.');
      return request('analyze', {name, bytes}, 15000, [bytes]);
    },
  };
})();
