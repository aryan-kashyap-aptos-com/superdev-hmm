"""db-ssh: query PostgreSQL, MySQL/MariaDB or SQL Server, directly or through an SSH tunnel. Read-only unless --write."""
import argparse
import contextlib
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import common as c  # noqa: E402

c.load_env(HERE)

FETCH_CAP = 10000  # rows read from the server before stopping

ENGINES = {
    # name: default port, default schema for describe (None = the database name)
    "postgres": {"port": 5432, "schema": "public"},
    "mysql": {"port": 3306, "schema": None},
    "sqlserver": {"port": 1433, "schema": "dbo"},
}

TABLES_SQL = {
    "postgres": """select table_schema, table_name, table_type from information_schema.tables
        where table_schema not in ('pg_catalog', 'information_schema')
          and (%(schema)s::text is null or table_schema = %(schema)s) order by 1, 2""",
    "mysql": """select table_schema, table_name, table_type from information_schema.tables
        where table_schema not in ('mysql', 'sys', 'performance_schema', 'information_schema')
          and (%(schema)s is null or table_schema = %(schema)s) order by 1, 2""",
    "sqlserver": """select table_schema, table_name, table_type from information_schema.tables
        where (%(schema)s is null or table_schema = %(schema)s) order by 1, 2""",
}

DESCRIBE_SQL = """select column_name, data_type, is_nullable, column_default from information_schema.columns
    where table_schema = %(schema)s and table_name = %(table)s order by ordinal_position"""

TEST_SQL = {
    "postgres": "select current_database() as database_name, current_user as user_name, version() as version",
    "mysql": "select database() as database_name, current_user() as user_name, version() as version",
    "sqlserver": "select db_name() as database_name, suser_sname() as user_name, @@version as version",
}


def engine():
    name = (c.setting("DB_ENGINE", "postgres")).lower()
    if name not in ENGINES:
        raise c.ConnectorError(f"Unknown DB_ENGINE '{name}'.", "Use postgres, mysql, or sqlserver.")
    return name


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _tunnel_command(local_port, db_host, db_port):
    """OpenSSH for normal keys; PuTTY plink for .ppk keys."""
    ssh_host, user, key, port = c.setting("SSH_HOST"), c.setting("SSH_USER"), c.setting("SSH_KEY"), c.setting("SSH_PORT")
    target = f"{user}@{ssh_host}" if user else ssh_host
    forward = f"127.0.0.1:{local_port}:{db_host}:{db_port}"
    if key and key.lower().endswith(".ppk"):
        if not shutil.which("plink"):
            raise c.ConnectorError("SSH_KEY is a PuTTY .ppk key, but 'plink' was not found.",
                                   "Install PuTTY (it includes plink), or convert the key to OpenSSH format with PuTTYgen.")
        cmd = ["plink", "-batch", "-N", "-L", forward, "-i", os.path.expanduser(key)]
        if port:
            cmd += ["-P", port]
        if c.setting("SSH_HOST_KEY"):
            cmd += ["-hostkey", c.setting("SSH_HOST_KEY")]
        return cmd + [target]
    # BatchMode: never prompt. An unknown host key fails instead of being accepted silently.
    cmd = ["ssh", "-N", "-o", "BatchMode=yes", "-o", "ExitOnForwardFailure=yes", "-L", forward]
    if port:
        cmd += ["-p", port]
    if key:
        cmd += ["-i", os.path.expanduser(key)]
    return cmd + [target]


@contextlib.contextmanager
def tunnel(db_engine):
    """Yield (host, port) for the database. Opens an SSH tunnel when SSH_HOST is set."""
    db_host = c.need("DB_HOST")[0]
    db_port = int(c.setting("DB_PORT", ENGINES[db_engine]["port"]))
    if not c.setting("SSH_HOST"):
        yield db_host, db_port
        return

    local_port = _free_port()
    cmd = _tunnel_command(local_port, db_host, db_port)
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise c.ConnectorError(f"The '{cmd[0]}' command was not found.", "Install the OpenSSH client (or PuTTY for .ppk keys).") from None
    try:
        deadline = time.time() + 20
        while True:
            if proc.poll() is not None:
                err = proc.stderr.read().decode(errors="replace").strip()
                raise c.ConnectorError(
                    f"SSH tunnel failed: {err or cmd[0] + ' exited'}",
                    "Check SSH_* settings. If the host key is unknown: for OpenSSH, connect once by hand with ssh to accept it; "
                    "for .ppk keys, set SSH_HOST_KEY to the key fingerprint shown in the error.")
            try:
                socket.create_connection(("127.0.0.1", local_port), timeout=1).close()
                break
            except OSError:
                if time.time() > deadline:
                    raise c.ConnectorError("SSH tunnel did not open within 20 seconds.", "Check network, VPN, and SSH_HOST.")
                time.sleep(0.3)
        yield "127.0.0.1", local_port
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def _connect(db_engine, host, port, name, user, password, write):
    """Return (connection, driver error class). Read-only is set up here."""
    timeout_s = int(c.setting("DB_TIMEOUT_SECONDS", "60"))
    if db_engine == "postgres":
        import psycopg
        conn = psycopg.connect(host=host, port=port, dbname=name, user=user, password=password, connect_timeout=10,
                               sslmode=c.setting("DB_SSLMODE", "prefer"), options=f"-c statement_timeout={timeout_s * 1000}")
        conn.read_only = not write   # the server rejects INSERT, UPDATE, DELETE and DDL
        return conn, psycopg.Error
    if db_engine == "mysql":
        import pymysql
        conn = pymysql.connect(host=host, port=port, user=user, password=password, database=name,
                               connect_timeout=10, read_timeout=timeout_s, autocommit=False)
        cur = conn.cursor()
        cur.execute("SET SESSION TRANSACTION " + ("READ WRITE" if write else "READ ONLY"))
        try:
            cur.execute(f"SET SESSION max_execution_time = {timeout_s * 1000}")   # MySQL 5.7+; MariaDB ignores it
        except pymysql.Error:
            pass
        cur.close()
        return conn, pymysql.Error
    import pymssql
    conn = pymssql.connect(server=host, port=str(port), user=user, password=password, database=name,
                           login_timeout=10, timeout=timeout_s, autocommit=False)
    return conn, pymssql.Error


@contextlib.contextmanager
def open_db(write=False):
    db_engine = engine()
    _, name, user, password = c.need("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD")
    with tunnel(db_engine) as (host, port):
        try:
            conn, driver_error = _connect(db_engine, host, port, name, user, password, write)
        except ImportError:
            raise c.ConnectorError(f"The Python package for {db_engine} is not installed.",
                                   "Run: pip install -r requirements.txt") from None
        except Exception as e:
            raise c.ConnectorError(f"Cannot connect to the database: {str(e).strip()}",
                                   "Check DB_* settings, the VPN, and SSH_* settings if you use a tunnel.") from None
        try:
            yield conn
            if write:
                conn.commit()
            else:
                conn.rollback()   # read-only work never keeps changes
        except driver_error as e:
            conn.rollback()
            text = str(e).strip()
            hint = ""
            if "read-only" in text.lower() or "read only" in text.lower():
                hint = "This statement changes data. Ask the user for permission, then add --write."
            elif "timeout" in text.lower() or "cancel" in text.lower():
                hint = "The query took too long. Add filters or a LIMIT."
            raise c.ConnectorError(f"Database error: {text}", hint) from None
        finally:
            conn.close()


def query(conn, sql, params=None, limit=c.MAX_ROWS, name="db-ssh"):
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        if cur.description is None:
            print(f"OK. Rows affected: {cur.rowcount}")
            return
        columns = [d[0] for d in cur.description]
        rows = cur.fetchmany(FETCH_CAP)
        more = cur.fetchone() is not None
    finally:
        cur.close()
    c.show_table(rows, columns, name, limit=limit, more_exists=more)


def cmd_test(args):
    db_engine = engine()
    with open_db() as conn:
        query(conn, TEST_SQL[db_engine])
    via = f"SSH tunnel through {c.setting('SSH_HOST')}" if c.setting("SSH_HOST") else "direct connection"
    print(f"Connection OK ({db_engine}, {via}, read-only).")


def cmd_tables(args):
    with open_db() as conn:
        query(conn, TABLES_SQL[engine()], {"schema": args.schema}, limit=args.limit, name="db-ssh-tables")


def cmd_describe(args):
    schema, _, table = args.table.rpartition(".")
    default = ENGINES[engine()]["schema"] or c.setting("DB_NAME")
    with open_db() as conn:
        query(conn, DESCRIBE_SQL, {"schema": schema or default, "table": table}, limit=500, name="db-ssh-describe")


def cmd_sql(args):
    sql = Path(args.file).read_text(encoding="utf-8") if args.file else args.query
    if not sql:
        raise c.ConnectorError("Give a query or --file.")
    if args.write:
        c.require_write(args, "sql --write")
    elif engine() != "postgres":
        c.check_read_only_sql(sql)   # PostgreSQL enforces read-only in the server; the others get this check too
    with open_db(write=args.write) as conn:
        query(conn, sql, limit=args.limit)


def main():
    p = argparse.ArgumentParser(description="Query PostgreSQL, MySQL or SQL Server (read-only unless --write).")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("test", help="check settings and connection").set_defaults(func=cmd_test)

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
