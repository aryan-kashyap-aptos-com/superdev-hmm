"""Quick network reachability checks before opening a DB session."""

from __future__ import annotations

import os
import socket

from progress import step, warn
from secrets import get_db_credentials


def tcp_reachable(host: str, port: int, *, timeout: float) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        try:
            sock.connect((host, port))
            return True
        except OSError:
            return False


def probe_network(*, verbose: bool = True) -> dict[str, object]:
    creds = get_db_credentials(verbose=verbose)
    host = str(creds["host"])
    port = int(creds["port"])
    timeout = float(os.getenv("PGPROBE_TIMEOUT", "8"))

    connect_host = os.getenv("PGHOST", host)
    connect_port = int(os.getenv("PGPORT", str(port)))

    if verbose:
        step(f"Resolved target: {host}:{port}/{creds['dbname']} as {creds['user']}")
        if connect_host != host or connect_port != port:
            step(f"PGHOST/PGPORT override active: connecting via {connect_host}:{connect_port}")

    if verbose:
        step(f"Checking TCP reachability ({connect_host}:{connect_port}, timeout {timeout:g}s)...")

    reachable = tcp_reachable(connect_host, connect_port, timeout=timeout)
    if reachable:
        if verbose:
            step("TCP check: OK")
        return {"reachable": True, "host": connect_host, "port": connect_port, "creds": creds}

    warn(
        f"Cannot reach {connect_host}:{connect_port}. "
        "This RDS endpoint is likely private. Start an SSH tunnel and set PGHOST=127.0.0.1 "
        "(see oms_db_connector tunnel) or connect from inside the VPC."
    )
    return {"reachable": False, "host": connect_host, "port": connect_port, "creds": creds}
