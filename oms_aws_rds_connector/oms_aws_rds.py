#!/usr/bin/env python3
"""OMS AWS RDS connector CLI — Secrets Manager + PostgreSQL.

Usage:
  python oms_aws_rds.py test
  python oms_aws_rds.py sql "SELECT current_database()"
  python oms_aws_rds.py sql --write "UPDATE ..."   # mutations (use carefully)
  python oms_aws_rds.py secret-info                # show resolved host/db (no password)

Open this folder in Cursor, copy .env.example -> .env, then:
  pip install -r requirements.txt
  python oms_aws_rds.py test
"""

from __future__ import annotations

import argparse
import sys

from client import load_env, secret_arn, set_env_file
from cluster import get_cluster_info
from data_api import connection_mode
from probe import probe_network
from progress import step
from router import run_sql, run_test
from secrets import get_db_credentials


def cmd_probe(_: argparse.Namespace) -> int:
    load_env()
    result = probe_network(verbose=True)
    return 0 if result["reachable"] else 1


def cmd_test(_: argparse.Namespace) -> int:
    load_env()
    step(f"Starting connection test (mode={connection_mode()})...")
    result = run_test(verbose=True)
    print(f"OK  mode={result['mode']}")
    print(f"    database={result['database']}")
    print(f"    user={result.get('user')}")
    if result.get("cluster_id"):
        print(f"    cluster={result['cluster_id']}")
    print(f"    secret_arn={secret_arn()}")
    version = str(result.get("version") or "")
    if version:
        print(f"    {version.split(',')[0]}")
    return 0


def cmd_secret_info(_: argparse.Namespace) -> int:
    load_env()
    step("Resolving credentials...")
    creds = get_db_credentials(verbose=True)
    info = get_cluster_info(verbose=False)
    print("Resolved connection details:")
    print(f"  mode: {connection_mode()}")
    if creds.get("cluster_id"):
        print(f"  cluster: {creds['cluster_id']}")
    print(f"  cluster_arn: {info['cluster_arn']}")
    print(f"  data_api_enabled: {info['http_endpoint_enabled']}")
    print(f"  host: {creds['host']}")
    print(f"  port: {creds['port']}")
    print(f"  database: {creds['dbname']}")
    print(f"  user: {creds['user']}")
    print(f"  secret_arn: {secret_arn()}")
    return 0


def cmd_sql(args: argparse.Namespace) -> int:
    result = run_sql(args.query, write=args.write, limit=args.limit, verbose=True)
    if result.get("number_of_records_updated") is not None and not result.get("columns"):
        print(f"OK ({result['number_of_records_updated']} rows affected)")
        return 0
    if result.get("columns"):
        print("\t".join(result["columns"]))
        for row in result.get("rows", []):
            print("\t".join("" if v is None else str(v) for v in row))
        if result.get("truncated"):
            print(f"... (limited to {args.limit} rows)")
    else:
        print("OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="OMS AWS RDS connector")
    parser.add_argument("--env", default=".env", help="Path to env file (default: .env)")
    sub = parser.add_subparsers(dest="command", required=True)

    probe = sub.add_parser("probe", help="Fast TCP reachability check (fails fast if RDS is private)")
    probe.set_defaults(func=cmd_probe)

    test = sub.add_parser("test", help="Test DB connection via Secrets Manager")
    test.set_defaults(func=cmd_test)

    secret_info = sub.add_parser("secret-info", help="Show resolved host/db from secret (no password)")
    secret_info.set_defaults(func=cmd_secret_info)

    sql = sub.add_parser("sql", help="Run SQL")
    sql.add_argument("query")
    sql.add_argument("--write", action="store_true", help="Allow writes (default: read-only)")
    sql.add_argument("--limit", type=int, default=50)
    sql.set_defaults(func=cmd_sql)

    args = parser.parse_args()
    set_env_file(args.env)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
