from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .server import MCPServer


def serve_http(server: MCPServer, host: str = "127.0.0.1", port: int = 8000) -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", 0))
            message = json.loads(self.rfile.read(length))
            response = server.dispatch(message)
            payload = json.dumps(response).encode("utf-8") if response is not None else b""
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            if payload:
                self.wfile.write(payload)

        def log_message(self, *args: object) -> None:
            pass

    address = ThreadingHTTPServer((host, port), Handler)
    print(f"{server.name} MCP HTTP server listening on http://{host}:{port}",
          file=sys.stderr, flush=True)
    address.serve_forever()
