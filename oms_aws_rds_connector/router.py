"""Choose direct PostgreSQL or RDS Data API based on CONNECTION_MODE."""

from __future__ import annotations

import os
from typing import Any

from data_api import connection_mode, execute_sql, test_connection
from db import connect, verify_database
from probe import probe_network
from progress import step, warn


def run_test(*, verbose: bool = True) -> dict[str, Any]:
    mode = connection_mode()
    if mode == "data_api":
        return test_connection(verbose=verbose)

    if mode == "direct":
        return _test_direct(verbose=verbose)

    probe = probe_network(verbose=verbose)
    if probe["reachable"]:
        return _test_direct(verbose=verbose)

    warn("Direct TCP connection unavailable; falling back to RDS Data API.")
    return test_connection(verbose=verbose)


def run_sql(
    query: str,
    *,
    write: bool = False,
    limit: int = 50,
    verbose: bool = True,
) -> dict[str, Any]:
    mode = connection_mode()
    readonly = not write

    if mode == "data_api":
        return execute_sql(query, readonly=readonly, limit=limit, verbose=verbose)

    if mode == "direct":
        return _run_sql_direct(query, write=write, limit=limit, verbose=verbose)

    probe = probe_network(verbose=verbose)
    if probe["reachable"]:
        return _run_sql_direct(query, write=write, limit=limit, verbose=verbose)

    warn("Direct TCP connection unavailable; falling back to RDS Data API.")
    return execute_sql(query, readonly=readonly, limit=limit, verbose=verbose)


def _test_direct(*, verbose: bool = True) -> dict[str, Any]:
    if verbose:
        step("Using direct PostgreSQL connection...")
    conn = connect(readonly=True, verbose=verbose)
    try:
        verify_database(conn)
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), current_user, version()")
            db_name, user, version = cur.fetchone()
    finally:
        conn.close()
    return {
        "database": db_name,
        "user": user,
        "version": version,
        "mode": "direct",
    }


def _run_sql_direct(
    query: str,
    *,
    write: bool,
    limit: int,
    verbose: bool,
) -> dict[str, Any]:
    if verbose:
        step("Using direct PostgreSQL connection...")
    conn = connect(readonly=not write, verbose=verbose)
    try:
        verify_database(conn)
        with conn.cursor() as cur:
            cur.execute(query)
            if cur.description is None:
                if write:
                    conn.commit()
                return {
                    "columns": [],
                    "rows": [],
                    "truncated": False,
                    "number_of_records_updated": cur.rowcount,
                    "mode": "direct",
                }
            cols = [d.name for d in cur.description]
            rows = cur.fetchmany(limit)
            return {
                "columns": cols,
                "rows": [list(row) for row in rows],
                "truncated": len(rows) == limit,
                "mode": "direct",
            }
    finally:
        conn.close()
