from __future__ import annotations

from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from time import sleep
from typing import ClassVar
from urllib.parse import parse_qs, urlparse


class _DelayRequestHandler(BaseHTTPRequestHandler):
    server_version: ClassVar[str] = "ConcurrencyLabDelayHTTP/1.0"

    def do_GET(self) -> None:  # noqa: N802 - assinatura do BaseHTTPRequestHandler
        parsed_url = urlparse(self.path)
        if parsed_url.path != "/delay":
            self.send_error(404, "Not found")
            return

        delay_ms = _parse_delay_ms(parsed_url.query)
        if delay_ms is None:
            self.send_error(400, "Invalid delay")
            return

        sleep(delay_ms / 1000)
        body = f"delayed {delay_ms} ms".encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


class _LocalDelayHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


@dataclass(slots=True)
class LocalDelayServer:
    """Servidor HTTP mínimo para experimentos I/O-bound controlados."""

    host: str = "127.0.0.1"
    port: int = 0
    _server: ThreadingHTTPServer | None = None
    _thread: Thread | None = None

    def __enter__(self) -> LocalDelayServer:
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

    def start(self) -> None:
        if self._server is not None:
            return

        self._server = _LocalDelayHTTPServer((self.host, self.port), _DelayRequestHandler)
        self._thread = Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is None:
            return

        self._server.shutdown()
        self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5)
        self._server = None
        self._thread = None

    @property
    def base_url(self) -> str:
        if self._server is None:
            raise RuntimeError("O servidor HTTP local ainda não foi iniciado.")

        host, port = self._server.server_address[:2]
        return f"http://{host}:{port}"

    def delay_url(self, delay_ms: int) -> str:
        return f"{self.base_url}/delay?ms={delay_ms}"


def _parse_delay_ms(query: str) -> int | None:
    values = parse_qs(query).get("ms", [])
    if not values:
        return 0

    try:
        delay_ms = int(values[0])
    except ValueError:
        return None

    if delay_ms < 0:
        return None
    return delay_ms
