"""Lanza el parser en un proceso separado con tiempo y concurrencia limitados."""
import base64
import json
import subprocess
import sys
import threading

SLOTS = threading.BoundedSemaphore(2)

def isolated_analysis(data, filename):
    from .engine import MAX_BYTES
    if not data or len(data) > MAX_BYTES:
        raise ValueError("Selecciona un archivo no vacío de hasta 10 MiB.")
    if not SLOTS.acquire(blocking=False):
        raise RuntimeError("Hay dos análisis en curso. Vuelve a intentarlo en unos segundos.")
    try:
        payload = json.dumps({"filename": filename, "data": base64.b64encode(data).decode("ascii")})
        completed = subprocess.run([sys.executable, "-m", "faro.worker"], input=payload,
                                   text=True, capture_output=True, timeout=15)
        if completed.returncode:
            raise RuntimeError("El análisis se detuvo por un error de lectura o un límite de recursos. El archivo no fue evaluado completamente.")
        return json.loads(completed.stdout)
    except subprocess.TimeoutExpired:
        raise RuntimeError("Se alcanzó el límite de 15 segundos. El archivo no fue evaluado completamente.") from None
    finally:
        SLOTS.release()
