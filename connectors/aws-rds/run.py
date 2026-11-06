"""aws-rds: query AWS Aurora (PostgreSQL or MySQL) through the RDS Data API. Read-only unless --write."""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import common as c  # noqa: E402

c.load_env(HERE)

TABLES_SQL = {
    "postgres": """select table_schema, table_name, table_type from information_schema.tables
        where table_schema not in ('pg_catalog', 'information_schema')
          and (cast(:schema as text) is null or table_schema = :schema) order by 1, 2""",
    "mysql": """select table_schema, table_name, table_type from information_schema.tables
        where table_schema not in ('mysql', 'sys', 'performance_schema', 'information_schema')
          and (:schema is null or table_schema = :schema) order by 1, 2""",
}

DESCRIBE_SQL = """select column_name, data_type, is_nullable, column_default from information_schema.columns
    where table_schema = :schema and table_name = :table order by ordinal_position"""

TEST_SQL = {
    "postgres": "select current_database() as database_name, current_user as user_name, version() as version",
    "mysql": "select database() as database_name, current_user() as user_name, version() as version",
}


def engine():
    name = (c.setting("RDS_ENGINE", "postgres")).lower()
    if name not in TABLES_SQL:
        raise c.ConnectorError(f"Unknown RDS_ENGINE '{name}'.", "Use postgres or mysql.")
    return name


def _client():
    try:
        import boto3
    except ImportError:
        raise c.ConnectorError("The boto3 package is not installed.",
                               "Run: pip install -r requirements.txt") from None
    return boto3.client("rds-data", region_name=c.setting("AWS_REGION"))


def _param(name, value):
    return {"name": name, "value": {"isNull": True} if value is None else {"stringValue": value}}


def execute(sql, params=None, write=False, limit=c.MAX_ROWS, name="aws-rds"):
    from botocore.exceptions import BotoCoreError, ClientError
    db_engine = engine()
    if not write and db_engine == "mysql":
        c.check_read_only_sql(sql)   # MySQL cannot switch a running Data API transaction to read-only
    arn, secret, db = c.need("RDS_CLUSTER_ARN", "RDS_SECRET_ARN", "DB_NAME")
    rds = _client()
    tx = None
    done = False
    try:
        tx = rds.begin_transaction(resourceArn=arn, secretArn=secret, database=db)["transactionId"]
        base = dict(resourceArn=arn, secretArn=secret, database=db, transactionId=tx)
        if not write and db_engine == "postgres":
            rds.execute_statement(sql="SET TRANSACTION READ ONLY", **base)   # PostgreSQL rejects any change
        res = rds.execute_statement(sql=sql, parameters=params or [], includeResultMetadata=True,
                                    formatRecordsAs="JSON", **base)
        if write:
            rds.commit_transaction(resourceArn=arn, secretArn=secret, transactionId=tx)
            done = True
    except ClientError as e:
        msg = e.response.get("Error", {}).get("Message", str(e))
        hint = ""
        if "read-only" in msg.lower() or "read only" in msg.lower():
            hint = "This statement changes data. Ask the user for permission, then add --write."
        elif "resuming" in msg.lower():
            hint = "The cluster is waking up. Wait 30 seconds and try again."
        elif "credentials" in msg.lower() or "token" in msg.lower():
            hint = "Check AWS_PROFILE / AWS credentials, and log in again if the session expired."
        raise c.ConnectorError(f"AWS error: {msg}", hint) from None
    except BotoCoreError as e:
        raise c.ConnectorError(f"AWS error: {e}", "Check AWS_PROFILE, AWS_REGION and your AWS login.") from None
    finally:
        if tx and not done:
            try:
                rds.rollback_transaction(resourceArn=arn, secretArn=secret, transactionId=tx)   # read-only work never keeps changes
            except Exception:
                pass

    if "formattedRecords" not in res:
        print(f"OK. Rows affected: {res.get('numberOfRecordsUpdated', 0)}")
        return
    records = json.loads(res["formattedRecords"])
    columns = [m["name"] for m in res.get("columnMetadata", [])] or (list(records[0]) if records else [])
    rows = [[r.get(col) for col in columns] for r in records]
    c.show_table(rows, columns, name, limit=limit)


def cmd_test(args):
    execute(TEST_SQL[engine()])
    print(f"Connection OK (RDS Data API, {engine()}, read-only).")


def cmd_tables(args):
    execute(TABLES_SQL[engine()], [_param("schema", args.schema)], limit=args.limit, name="aws-rds-tables")


def cmd_describe(args):
    schema, _, table = args.table.rpartition(".")
    default = "public" if engine() == "postgres" else c.setting("DB_NAME")
    execute(DESCRIBE_SQL, [_param("schema", schema or default), _param("table", table)], limit=500, name="aws-rds-describe")


def cmd_sql(args):
    sql = Path(args.file).read_text(encoding="utf-8") if args.file else args.query
    if not sql:
        raise c.ConnectorError("Give a query or --file.")
    if args.write:
        c.require_write(args, "sql --write")
    execute(sql, write=args.write, limit=args.limit)


def main():
    p = argparse.ArgumentParser(description="Query Aurora PostgreSQL or MySQL via the RDS Data API (read-only unless --write).")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("test", help="check settings and access").set_defaults(func=cmd_test)

    s = sub.add_parser("tables", help="list tables")
    s.add_argument("--schema", help="only this schema (MySQL: database)")
    s.add_argument("--limit", type=int, default=200)
    s.set_defaults(func=cmd_tables)

    s = sub.add_parser("describe", help="list columns of a table (schema.table or table)")
    s.add_argument("table")
    s.set_defaults(func=cmd_describe)

    s = sub.add_parser("sql", help="run a SQL query")
    s.add_argument("query", nargs="?", help="SQL text (or use --file)")
    s.add_argument("--file", help="read SQL from this file")
    s.add_argument("--limit", type=int, default=c.MAX_ROWS, help="rows to print (all rows go to a file)")
    s.add_argument("--write", action="store_true", help="allow changes; needs the user's permission")
    s.set_defaults(func=cmd_sql)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    c.run(main)
