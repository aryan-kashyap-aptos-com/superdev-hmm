"""Connect to PostgreSQL using credentials from AWS Secrets Manager."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Generator

import psycopg
from psycopg import Connection, OperationalError

from client import load_env
from progress import step, warn
from secrets import get_db_credentials


def _connect_host(creds: dict[str, Any]) -> tuple[str, int]:
    host = os.getenv("PGHOST", str(creds["host"]))
    port = int(os.getenv("PGPORT", str(creds["port"])))
    return host, port


def connect(*, readonly: bool = False, verbose: bool = True) -> Connection:
    load_env()
    creds = get_db_credentials(verbose=verbose)
    host, port = _connect_host(creds)
    timeout = int(os.getenv("PGCONNECT_TIMEOUT", "30"))

    if verbose:
        step(
            f"Opening PostgreSQL connection to {host}:{port}/{creds['dbname']} "
            f"as {creds['user']} (timeout {timeout}s)..."
        )
        if host != creds["host"]:
            step(f"Note: using PGHOST override (resolved endpoint was {creds['host']}:{creds['port']})")

    kwargs: dict[str, Any] = {
        "host": host,
        "port": port,
        "dbname": creds["dbname"],
        "user": creds["user"],
        "password": creds["password"],
        "connect_timeout": timeout,
    }
    sslmode = os.getenv("PGSSLMODE", "require")
    if sslmode and sslmode != "disable":
        kwargs["sslmode"] = sslmode

    try:
        conn = psycopg.connect(**kwargs)
    except OperationalError as exc:
        message = str(exc).lower()
        if "timeout" in message or "timed out" in message:
            warn(
                f"Connection timed out after {timeout}s to {host}:{port}. "
                "Run `python oms_aws_rds.py probe` first. If TCP fails, start an SSH tunnel "
                "and set PGHOST=127.0.0.1 in your env file."
            )
        raise RuntimeError(f"Could not connect to {host}:{port}: {exc}") from exc

    conn.autocommit = False
    with conn.cursor() as cur:
        if readonly:
            cur.execute("SET TRANSACTION READ ONLY")
        cur.execute("SET tcp_keepalives_idle = 30")
        cur.execute("SET tcp_keepalives_interval = 10")
        cur.execute("SET tcp_keepalives_count = 5")
    conn.commit()
    if verbose:
        step("Connected.")
    return conn


def verify_database(conn: Connection) -> None:
    load_env()
    expected = os.getenv("PGDATABASE")
    if not expected:
        raise RuntimeError("Missing env: PGDATABASE")

    with conn.cursor() as cur:
        cur.execute("SELECT current_database(), current_setting('server_version_num')")
        db_name, version_num = cur.fetchone()
        if db_name != expected:
            raise RuntimeError(f"Expected database {expected!r}, got {db_name!r}")
        if int(str(version_num)) // 10000 != 15:
            raise RuntimeError("Expected PostgreSQL 15")


@contextmanager
def session(*, readonly: bool = False) -> Generator[Connection, None, None]:
    conn = connect(readonly=readonly)
    try:
        verify_database(conn)
        with conn.cursor() as cur:
            cur.execute("SET statement_timeout = 0")
        yield conn
        if not readonly:
            conn.commit()
        else:
            conn.rollback()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
