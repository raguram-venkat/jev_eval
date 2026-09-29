"""Block any non-loopback network access so `uv run pytest` proves it runs offline."""
from __future__ import annotations

import socket

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
