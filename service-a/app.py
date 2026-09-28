from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import urllib.request

DIRECT_URL = os.getenv("SERVICE_B_URL", "http://service-b:8000")
CONNECT_URL = os.getenv("CONNECT_SERVICE_B_URL", "http://127.0.0.1:9000")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path.startswith("/connect"):
                target_url = CONNECT_URL
            else:
                target_url = DIRECT_URL

            with urllib.request.urlopen(target_url, timeout=5) as response:
                body = response.read()
                status = response.status

            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        except Exception as e:
            body = str(e).encode()

            self.send_response(502)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, format, *args):
        pass


HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
