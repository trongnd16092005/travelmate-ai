import argparse
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import ClassVar


class WslProxyHandler(BaseHTTPRequestHandler):
    distro: ClassVar[str]
    target_port: ClassVar[int]
    allowed_origins: ClassVar[set[str]] = {
        "http://localhost:8081",
        "http://127.0.0.1:8081",
    }

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.end_headers()

    def do_GET(self) -> None:
        self._forward("GET")

    def do_POST(self) -> None:
        self._forward("POST")

    def _forward(self, method: str) -> None:
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length else b""
        target_url = f"http://127.0.0.1:{self.target_port}{self.path}"
        command = [
            "wsl.exe",
            "-d",
            self.distro,
            "--",
            "curl",
            "--silent",
            "--show-error",
            "--max-time",
            "300",
            "--request",
            method,
            "--header",
            "Content-Type: application/json",
        ]
        if body:
            command.extend(("--data-binary", "@-"))
        status_marker = b"__WSL_PROXY_STATUS__"
        command.extend(
            (
                "--write-out",
                f"{status_marker.decode()}%{{http_code}}",
                target_url,
            )
        )

        try:
            result = subprocess.run(
                command,
                input=body,
                capture_output=True,
                check=False,
                timeout=320,
            )
            response_body, status_line = result.stdout.rsplit(status_marker, 1)
            status = int(status_line)
        except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
            response_body = f'{{"detail":"WSL proxy error: {exc}"}}'.encode()
            status = 502

        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)

    def _send_cors_headers(self) -> None:
        origin = self.headers.get("Origin")
        if origin in self.allowed_origins:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Proxy demo Windows sang AI Service trong WSL")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--target-port", type=int, default=8002)
    parser.add_argument("--distro", default="Ubuntu-24.04")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    WslProxyHandler.distro = args.distro
    WslProxyHandler.target_port = args.target_port
    server = ThreadingHTTPServer((args.host, args.port), WslProxyHandler)
    print(f"WSL demo proxy: http://{args.host}:{args.port} -> WSL:{args.target_port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
