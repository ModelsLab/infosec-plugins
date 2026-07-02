"""Tor SOCKS5 proxy reachability check (stdlib only)."""
from __future__ import annotations

import socket
import time

TOR_HOST = "127.0.0.1"
TOR_PORT = 9050


def check_tor_proxy(host: str = TOR_HOST, port: int = TOR_PORT, timeout: float = 5.0) -> dict:
    """Return {status: 'up'|'down', latency_ms, error}. Does NOT prove exit works, only that
    a SOCKS proxy is listening on host:port."""
    start = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            latency_ms = int((time.monotonic() - start) * 1000)
            return {"status": "up", "latency_ms": latency_ms, "error": None}
    except OSError as exc:
        return {"status": "down", "latency_ms": None, "error": str(exc)}
