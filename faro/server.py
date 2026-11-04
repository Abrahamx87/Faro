"""Servidor de demostración local. No es un servicio público de producción."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from .engine import MAX_BYTES
from .service import isolated_analysis

ROOT = Path(__file__).parent / "web"
EXAMPLES = Path(__file__).parent / "samples"

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # No registrar nombres de archivos, enlaces, cuerpos ni reportes.
        pass

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
        super().end_headers()

    def reply(self, status, data, mime="application/json; charset=utf-8"):
        body = json.dumps(data, ensure_ascii=False).encode() if isinstance(data, dict) else data
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.valid_host():
            return self.reply(403, {"error": "Host no permitido para el servidor local."})
        path = urlsplit(self.path).path
        if path == "/api/health":
            import importlib.util
            return self.reply(200, {"ok": True, "version": "0.1.0", "mode": "local", "max_bytes": MAX_BYTES,
                                    "pdf_parser_available": importlib.util.find_spec("pypdf") is not None})
        assets = {"/": ("index.html", "text/html; charset=utf-8"), "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                  "/styles.css": ("styles.css", "text/css; charset=utf-8"), "/icon.svg": ("icon.svg", "image/svg+xml")}
        if path in assets:
            name, mime = assets[path]
            return self.reply(200, (ROOT / name).read_bytes(), mime)
        return self.reply(404, {"error": "Recurso no encontrado."})

    def do_POST(self):
        self.connection.settimeout(20)
        # Solo clientes del mismo origen. JSON y octet-stream exigen preflight
        # en navegadores de otro origen; no se habilita CORS.
        host = self.headers.get("Host", "")
        origin = self.headers.get("Origin")
        if not self.valid_host() or (origin and origin not in (f"http://{host}", f"https://{host}")):
            return self.reply(403, {"error": "Origen no permitido."})
        path = urlsplit(self.path).path
        if path == "/api/demo":
            name = unquote(self.headers.get("X-Demo", ""))
            allowed = {"legitimo.pdf", "verificacion.html", "contenido_disfrazado.pdf"}
            if name not in allowed:
                return self.reply(400, {"error": "Ejemplo desconocido."})
            data = (EXAMPLES / name).read_bytes()
        elif path == "/api/analyze":
            if self.headers.get_content_type() != "application/octet-stream":
                return self.reply(415, {"error": "Se requiere un archivo binario."})
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                return self.reply(400, {"error": "Tamaño no válido."})
            if not 0 < length <= MAX_BYTES:
                self.close_connection = True
                return self.reply(413, {"error": "Selecciona un archivo no vacío de hasta 10 MiB."})
            try:
                data = self.rfile.read(length)
            except (TimeoutError, OSError):
                self.close_connection = True
                return self.reply(408, {"error": "Se agotó el tiempo de recepción del archivo."})
            if len(data) != length:
                return self.reply(400, {"error": "El archivo llegó incompleto."})
            name = unquote(self.headers.get("X-Filename", "archivo"))
        else:
            return self.reply(404, {"error": "Recurso no encontrado."})
        try:
            result = isolated_analysis(data, name)
            self.reply(200, result)
        except ValueError as exc:
            self.reply(400, {"error": str(exc)})
        except RuntimeError as exc:
            self.reply(422, {"error": str(exc)})

    def valid_host(self):
        host = self.headers.get("Host", "").lower()
        if not host:
            return False
        # Evitar DNS rebinding en el modo local predeterminado.
        if self.server.server_address[0] in ("127.0.0.1", "::1"):
            return host.split(":", 1)[0] in ("localhost", "127.0.0.1")
        return True

def serve(host="127.0.0.1", port=8765):
    print(f"Faro · http://{host}:{port} · Ctrl+C para salir", flush=True)
    server = ThreadingHTTPServer((host, port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
