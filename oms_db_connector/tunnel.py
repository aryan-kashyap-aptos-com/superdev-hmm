"""SSH local port forward: localhost:PGPORT -> RDS via bastion."""

from __future__ import annotations

import os
import socket
import socketserver
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import paramiko

from db import load_env
from ppk import ppk_to_paramiko

ROOT = Path(__file__).resolve().parent
_process: subprocess.Popen[str] | None = None


@dataclass
class TunnelStatus:
    running: bool
    port: int
    remote_host: str
    pid: int | None = None
    message: str = ""


def _local_port() -> int:
    load_env()
    return int(os.getenv("PGPORT", "1112"))


def port_listening(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def get_status() -> TunnelStatus:
    load_env()
    port = _local_port()
    remote = os.getenv("SSH_REMOTE_HOST", "")
    global _process
    pid = _process.pid if _process and _process.poll() is None else None
    running = port_listening(port)
    message = "Tunnel active" if running else "Tunnel not running"
    if _process and _process.poll() is not None:
        message = f"Tunnel process exited (code {_process.returncode})"
    return TunnelStatus(running=running, port=port, remote_host=remote, pid=pid, message=message)


def _forward(source: socket.socket, destination: paramiko.Channel) -> None:
    try:
        while True:
            data = source.recv(65536)
            if not data:
                break
            destination.sendall(data)
    finally:
        source.close()
        destination.close()


def _run_worker() -> int:
    load_env()
    local_port = int(os.getenv("PGPORT", "1112"))
    remote_host = os.environ["SSH_REMOTE_HOST"]
    remote_port = int(os.getenv("SSH_REMOTE_PORT", "5432"))
    ppk_path = os.environ["SSH_PPK_PATH"]

    ppk = Path(ppk_path).read_text(encoding="utf-8")
    pkey = ppk_to_paramiko(ppk)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        os.environ["SSH_HOST"],
        port=int(os.getenv("SSH_PORT", "22")),
        username=os.environ["SSH_USER"],
        pkey=pkey,
        allow_agent=False,
        look_for_keys=False,
        timeout=30,
    )
    transport = client.get_transport()
    if transport is None:
        raise RuntimeError("SSH transport unavailable")
    transport.set_keepalive(30)

    class Handler(socketserver.BaseRequestHandler):
        def handle(self) -> None:
            assert transport is not None
            chan = transport.open_channel("direct-tcpip", (remote_host, remote_port), self.client_address)
            if chan is None:
                self.request.close()
                return
            threading.Thread(target=_forward, args=(self.request, chan), daemon=True).start()
            try:
                while True:
                    data = chan.recv(65536)
                    if not data:
                        break
                    self.request.sendall(data)
            finally:
                chan.close()
                self.request.close()

    class ForwardServer(socketserver.ThreadingTCPServer):
        daemon_threads = True
        allow_reuse_address = True

    server = ForwardServer(("127.0.0.1", local_port), Handler)
    print(f"TUNNEL_READY localhost:{local_port} -> {remote_host}:{remote_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        client.close()
    return 0


def start() -> TunnelStatus:
    global _process
    status = get_status()
    if status.running:
        return TunnelStatus(True, status.port, status.remote_host, status.pid, "Tunnel already running")

    load_env()
    for key in ("SSH_HOST", "SSH_USER", "SSH_PPK_PATH", "SSH_REMOTE_HOST"):
        if not os.getenv(key):
            raise RuntimeError(f"Missing {key} in .env")

    cmd = [sys.executable, str(ROOT / "tunnel.py"), "worker"]
    _process = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )

    deadline = time.time() + 30
    while time.time() < deadline:
        if _process.poll() is not None:
            output = _process.stdout.read() if _process.stdout else ""
            raise RuntimeError(f"Tunnel failed to start:\n{output}")
        if port_listening(_local_port()):
            return get_status()
        time.sleep(0.3)
    raise RuntimeError("Tunnel start timed out after 30 seconds")


def stop() -> TunnelStatus:
    global _process
    if _process and _process.poll() is None:
        _process.terminate()
        try:
            _process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _process.kill()
        _process = None
    return get_status()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "worker":
        raise SystemExit(_run_worker())
    print("Use: python oms_db.py tunnel start|stop|status", file=sys.stderr)
    raise SystemExit(1)
