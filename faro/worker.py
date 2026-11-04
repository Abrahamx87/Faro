"""Proceso acotado de análisis; entrada/salida JSON en memoria."""
import base64
import json
import sys

def main():
    if sys.platform != "win32":
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_CPU, (12, 12))
        resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    from .engine import analyze
    payload = json.loads(sys.stdin.buffer.read(15 * 1024 * 1024))
    result = analyze(base64.b64decode(payload["data"], validate=True), payload["filename"])
    sys.stdout.write(json.dumps(result, ensure_ascii=True))

if __name__ == "__main__":
    main()
