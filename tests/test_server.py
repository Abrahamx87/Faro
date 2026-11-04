import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer

from faro.engine import MAX_BYTES
from faro.server import Handler

class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=20)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        status, response_headers, data = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return status, response_headers, data

    def test_health_and_security_headers(self):
        status, headers, body = self.request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["ok"])
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertIn("object-src 'none'", headers["Content-Security-Policy"])

    def test_actual_file_upload(self):
        status, _, body = self.request("POST", "/api/analyze", b"Documento de clase.", {"Content-Type":"application/octet-stream", "X-Filename":"clase.txt"})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["file"]["type"], "text")

    def test_demo_uses_real_engine(self):
        status, _, body = self.request("POST", "/api/demo", headers={"X-Demo":"verificacion.html"})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["score"],60)

    def test_cross_origin_blocked(self):
        status, _, _ = self.request("POST", "/api/demo", headers={"X-Demo":"legitimo.pdf", "Origin":"https://externo.example.invalid"})
        self.assertEqual(status,403)

    def test_dns_rebinding_host_blocked(self):
        status, _, _ = self.request("GET", "/api/health", headers={"Host":"externo.example.invalid"})
        self.assertEqual(status,403)

    def test_oversize_rejected_before_body_read(self):
        status, _, _ = self.request("POST", "/api/analyze", headers={"Content-Type":"application/octet-stream", "Content-Length":str(MAX_BYTES+1)})
        self.assertEqual(status,413)

    def test_html_not_served_from_filesystem(self):
        for path in ("/../README.md","/samples/verificacion.html","/engine.py"):
            with self.subTest(path=path):
                status, _, _ = self.request("GET", path)
                self.assertEqual(status,404)

    def test_wrong_content_type_rejected(self):
        status, _, _ = self.request("POST", "/api/analyze", b"texto", {"Content-Type":"text/plain"})
        self.assertEqual(status,415)

if __name__ == "__main__":
    unittest.main()
