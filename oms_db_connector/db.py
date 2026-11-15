"""Load .env and connect to PostgreSQL through the local SSH tunnel."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

import psycopg
from psycopg import Connection

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"
SCHEMA = "oms"


def load_env() -> None:
    if not ENV_FILE.exists():
        raise RuntimeError(f"Missing {ENV_FILE}. Copy .env.example to .env and fill in values.")
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def connect(*, readonly: bool = False) -> Connection:
    load_env()
    missing = [name for name in ("PGHOST", "PGUSER", "PGPASSWORD") if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing env: {', '.join(missing)}")

    kwargs: dict[str, Any] = {
        "host": os.environ["PGHOST"],
        "port": int(os.getenv("PGPORT", "1112")),
        "dbname": os.getenv("PGDATABASE", "regression202510qa"),
        "user": os.environ["PGUSER"],
        "password": os.environ["PGPASSWORD"],
        "connect_timeout": int(os.getenv("PGCONNECT_TIMEOUT", "60")),
    }
    sslmode = os.getenv("PGSSLMODE", "require")
    if sslmode and sslmode != "disable":
        kwargs["sslmode"] = sslmode

    conn = psycopg.connect(**kwargs)
    conn.autocommit = False
    with conn.cursor() as cur:
        if readonly:
            cur.execute("SET TRANSACTION READ ONLY")
        cur.execute("SET tcp_keepalives_idle = 30")
        cur.execute("SET tcp_keepalives_interval = 10")
        cur.execute("SET tcp_keepalives_count = 5")
    conn.commit()
    return conn


def verify_database(conn: Connection) -> None:
    expected = os.getenv("PGDATABASE", "regression202510qa")
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
