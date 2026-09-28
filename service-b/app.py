from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import time

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        response = {
            "service": "service-b",
            "message": "Hello from Service B",
            "timestamp": time.time()
        }

        body = json.dumps(response).encode()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass

HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
