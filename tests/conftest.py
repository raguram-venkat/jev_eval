"""Block any non-loopback network access so `uv run pytest` proves it runs offline."""
from __future__ import annotations

import http.server
import json
import socket
import threading

import pytest

_ALLOWED_HOSTS = {"127.0.0.1", "::1", "localhost"}

_orig_connect = socket.socket.connect
_orig_getaddrinfo = socket.getaddrinfo


def _guarded_connect(self, address):
    host = address[0] if isinstance(address, tuple) else address
    if host not in _ALLOWED_HOSTS:
        pytest.fail(f"blocked network connect to {host!r} during offline tests")
    return _orig_connect(self, address)


def _guarded_getaddrinfo(host, *args, **kwargs):
    if host not in _ALLOWED_HOSTS:
        pytest.fail(f"blocked getaddrinfo for {host!r} during offline tests")
    return _orig_getaddrinfo(host, *args, **kwargs)


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", _guarded_connect)
    monkeypatch.setattr(socket, "getaddrinfo", _guarded_getaddrinfo)


class _Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _handle(self):
        seen = self.server.seen
        seen[self.path] = seen.get(self.path, 0) + 1
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else None
        responder = self.server.responders.get(self.path, self.server.default_responder)
        result = responder(seen, seen[self.path], body)
        if result is None:
            self.close_connection = True
            return
        status, body, headers = result
        payload = json.dumps(body).encode() if not isinstance(body, bytes) else body
        self.send_response(status)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    do_GET = _handle
    do_POST = _handle


class FakeServer:
    """A loopback HTTP server for tests. Register a responder per path:
    `fn(seen, n, body) -> (status, response_body, headers) | None`, called with the hit
    count `n` for that path (1-based) and the parsed JSON request body (`None` for GET).
    Returning `None` drops the connection with no response, which surfaces to httpx as
    a transport error.
    """

    def __init__(self):
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self.httpd.seen = {}
        self.httpd.responders = {}
        self.httpd.default_responder = staticmethod(lambda seen, n, body: (200, {"model": "jev-1.0.0"}, {}))
        self.thread = threading.Thread(target=self.httpd.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
        self.thread.start()

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.httpd.server_port}"

    def set_responder(self, path, fn):
        self.httpd.responders[path] = fn

    def hits(self, path: str) -> int:
        return self.httpd.seen.get(path, 0)

    def shutdown(self):
        self.httpd.shutdown()
        self.thread.join(timeout=2)


@pytest.fixture
def fake_server():
    server = FakeServer()
    yield server
    server.shutdown()


@pytest.fixture
def dead_url():
    """A loopback address nothing listens on, for connection-refused tests."""
    return "http://127.0.0.1:1"
