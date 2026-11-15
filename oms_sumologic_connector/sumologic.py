#!/usr/bin/env python3
"""Sumo Logic connector CLI — query logs and export to Excel.

Usage:
  python sumologic.py test
  python sumologic.py query "_sourceCategory=prod/* | limit 20" --from -15m --to now
  python sumologic.py export "_sourceCategory=prod/* | count" --output my_report.xlsx
  python sumologic.py export-file saved_query.txt --output my_report.xlsx

Open this folder in Cursor, copy .env.example -> .env, then:
  pip install -r requirements.txt
  python sumologic.py test
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from client import ROOT, load_env
from export import default_output_path, write_excel
from search import run_query, verify_connection


def cmd_test(_: argparse.Namespace) -> int:
    load_env()
    status = verify_connection()
    print("OK  Sumo Logic connection verified")
    print(f"    state={status.get('state')}")
    print(f"    messageCount={status.get('messageCount', 0)}")
    print(f"    recordCount={status.get('recordCount', 0)}")
    return 0


def _print_rows(fields: list[str], rows: list[dict[str, Any]], limit: int) -> None:
    if not fields and rows:
        fields = sorted({key for row in rows for key in row.keys()})
    print("\t".join(fields))
    shown = rows[:limit]
    for row in shown:
        print("\t".join("" if row.get(field) is None else str(row.get(field, "")) for field in fields))
    if len(rows) > limit:
        print(f"... ({len(rows) - limit} more rows not shown)")


def cmd_query(args: argparse.Namespace) -> int:
    fields, rows, status = run_query(
        args.query,
        time_from=args.time_from,
        time_to=args.time_to,
        time_zone=args.timezone,
        result_type=args.result_type,
        limit=args.page_size,
        max_rows=args.max_rows,
    )
    print(f"OK  rows={len(rows)} messages={status.get('messageCount', 0)} records={status.get('recordCount', 0)}")
    _print_rows(fields, rows, args.limit)
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    fields, rows, status = run_query(
        args.query,
        time_from=args.time_from,
        time_to=args.time_to,
        time_zone=args.timezone,
        result_type=args.result_type,
        limit=args.page_size,
        max_rows=args.max_rows,
    )
    if args.output:
        output = Path(args.output)
        if not output.is_absolute():
            output = ROOT / "exports" / output
    else:
        output = default_output_path()

    metadata = {
        "from": args.time_from,
        "to": args.time_to,
        "messageCount": status.get("messageCount", 0),
        "recordCount": status.get("recordCount", 0),
        "exportedRows": len(rows),
    }
    saved = write_excel(fields, rows, output, query=args.query, metadata=metadata)
    print(f"OK  exported {len(rows)} rows")
    print(f"    {saved}")
    return 0


def cmd_export_file(args: argparse.Namespace) -> int:
    query_path = Path(args.query_file)
    if not query_path.exists():
        raise RuntimeError(f"Query file not found: {query_path}")
    query = query_path.read_text(encoding="utf-8").strip()
    if not query:
        raise RuntimeError(f"Query file is empty: {query_path}")
    args.query = query
    return cmd_export(args)


def _add_time_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--from", dest="time_from", default="-15m", help="Start time (-15m, -1h, ISO, or now)")
    parser.add_argument("--to", dest="time_to", default="now", help="End time (-15m, -1h, ISO, or now)")
    parser.add_argument("--timezone", default=None, help="Timezone for the search job (default from .env)")
    parser.add_argument(
        "--result-type",
        choices=("auto", "messages", "records"),
        default="auto",
        help="Use aggregate records when available (default: auto)",
    )
    parser.add_argument("--page-size", type=int, default=1000, help="API page size (max 1000)")
    parser.add_argument("--max-rows", type=int, default=None, help="Stop after this many rows")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sumo Logic connector")
    sub = parser.add_subparsers(dest="command", required=True)

    test = sub.add_parser("test", help="Verify Sumo Logic credentials")
    test.set_defaults(func=cmd_test)

    query = sub.add_parser("query", help="Run a Sumo query and print results")
    query.add_argument("query")
    query.add_argument("--limit", type=int, default=50, help="Rows to print")
    _add_time_args(query)
    query.set_defaults(func=cmd_query)

    export = sub.add_parser("export", help="Run a Sumo query and save results to Excel")
    export.add_argument("query")
    export.add_argument("--output", "-o", help="Output .xlsx path (default: exports/sumologic_<timestamp>.xlsx)")
    _add_time_args(export)
    export.set_defaults(func=cmd_export)

    export_file = sub.add_parser("export-file", help="Run a query from a text file and save to Excel")
    export_file.add_argument("query_file")
    export_file.add_argument("--output", "-o", help="Output .xlsx path")
    _add_time_args(export_file)
    export_file.set_defaults(func=cmd_export_file)

    args = parser.parse_args()
    try:
        return args.func(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
