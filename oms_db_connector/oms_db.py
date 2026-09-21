#!/usr/bin/env python3
"""OMS DB connector CLI — tunnel + query helpers.

Usage:
  python oms_db.py tunnel start|stop|status
  python oms_db.py test
  python oms_db.py sql "SELECT current_database()"
  python oms_db.py sql --write "UPDATE ..."   # mutations (use carefully)

Open this folder in Cursor, copy .env.example -> .env, then:
  pip install -r requirements.txt
  python oms_db.py tunnel start
  python oms_db.py test
"""

from __future__ import annotations

import argparse
import sys

from db import connect, load_env, session, verify_database
from tunnel import get_status, start, stop


def cmd_tunnel(args: argparse.Namespace) -> int:
    if args.action == "start":
        status = start()
    elif args.action == "stop":
        status = stop()
    else:
        status = get_status()
    print(f"{status.message}")
    print(f"  localhost:{status.port} -> {status.remote_host or '(not configured)'}")
    if status.pid:
        print(f"  pid: {status.pid}")
    return 0 if status.running or args.action == "stop" else 1


def cmd_test(_: argparse.Namespace) -> int:
    load_env()
    if not get_status().running:
        print("Warning: tunnel does not appear to be listening. Run: python oms_db.py tunnel start")
    with session(readonly=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), version()")
            db_name, version = cur.fetchone()
    print(f"OK  database={db_name}")
    print(f"    {version.split(',')[0]}")
    return 0


def cmd_sql(args: argparse.Namespace) -> int:
    if not get_status().running:
        print("Warning: tunnel may not be running.", file=sys.stderr)
    conn = connect(readonly=not args.write)
    try:
        verify_database(conn)
        with conn.cursor() as cur:
            cur.execute(args.query)
            if cur.description is None:
                if args.write:
                    conn.commit()
                print(f"OK ({cur.rowcount} rows affected)")
                return 0
            cols = [d.name for d in cur.description]
            rows = cur.fetchmany(args.limit)
            print("\t".join(cols))
            for row in rows:
                print("\t".join("" if v is None else str(v) for v in row))
            if len(rows) == args.limit:
                print(f"... (limited to {args.limit} rows)")
    finally:
        conn.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="OMS DB connector")
    sub = parser.add_subparsers(dest="command", required=True)

    tunnel = sub.add_parser("tunnel", help="Manage SSH tunnel")
    tunnel.add_argument("action", choices=("start", "stop", "status"))
    tunnel.set_defaults(func=cmd_tunnel)

    test = sub.add_parser("test", help="Test DB connection")
    test.set_defaults(func=cmd_test)

    sql = sub.add_parser("sql", help="Run SQL")
    sql.add_argument("query")
    sql.add_argument("--write", action="store_true", help="Allow writes (default: read-only)")
    sql.add_argument("--limit", type=int, default=50)
    sql.set_defaults(func=cmd_sql)

    args = parser.parse_args()
    try:
        return args.func(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
