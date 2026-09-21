"""Run SQL through the RDS Data API (same path as AWS Query Editor)."""

from __future__ import annotations

import os
from typing import Any

from client import aws_session, load_env, secret_arn
from cluster import get_cluster_info
from progress import step, warn


def connection_mode() -> str:
    load_env()
    mode = os.getenv("CONNECTION_MODE", "data_api").strip().lower()
    if mode not in {"data_api", "direct", "auto"}:
        raise RuntimeError("CONNECTION_MODE must be one of: data_api, direct, auto")
    return mode


def _field_value(field: dict[str, Any]) -> Any:
    if field.get("isNull"):
        return None
    for key in ("stringValue", "longValue", "doubleValue", "booleanValue", "blobValue"):
        if key in field:
            return field[key]
    return None


def _parse_records(response: dict[str, Any]) -> tuple[list[str], list[list[Any]]]:
    metadata = response.get("columnMetadata") or []
    columns = [str(col.get("name") or f"col{i}") for i, col in enumerate(metadata)]
    rows: list[list[Any]] = []
    for record in response.get("records") or []:
        rows.append([_field_value(field) for field in record])
    return columns, rows


def execute_sql(
    sql: str,
    *,
    readonly: bool = True,
    limit: int = 50,
    verbose: bool = True,
) -> dict[str, Any]:
    if not readonly and sql.strip().upper().startswith(("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE")):
        pass
    elif not readonly:
        warn("Running a write query through Data API.")

    load_env()
    info = get_cluster_info(verbose=verbose)
    if not info["http_endpoint_enabled"]:
        raise RuntimeError(
            f"RDS Data API / HTTP endpoint is not enabled on cluster {info['cluster_id']!r}. "
            "Enable it in the AWS console (Modify cluster -> Data API), or set CONNECTION_MODE=direct "
            "and use an SSH tunnel."
        )

    if verbose:
        step(
            f"Running SQL via RDS Data API on {info['cluster_id']} "
            f"database={info['dbname']} (readonly={readonly})..."
        )

    client = aws_session().client("rds-data")
    response = client.execute_statement(
        resourceArn=info["cluster_arn"],
        secretArn=secret_arn(),
        database=info["dbname"],
        sql=sql,
        includeResultMetadata=True,
    )

    columns, rows = _parse_records(response)
    if limit and len(rows) > limit:
        rows = rows[:limit]
        truncated = True
    else:
        truncated = False

    return {
        "columns": columns,
        "rows": rows,
        "truncated": truncated,
        "number_of_records_updated": response.get("numberOfRecordsUpdated"),
        "mode": "data_api",
        "cluster_id": info["cluster_id"],
        "database": info["dbname"],
    }


def test_connection(*, verbose: bool = True) -> dict[str, Any]:
    result = execute_sql(
        "SELECT current_database() AS database, current_user AS user, version() AS version",
        readonly=True,
        limit=1,
        verbose=verbose,
    )
    if not result["rows"]:
        raise RuntimeError("Data API test query returned no rows")

    row = dict(zip(result["columns"], result["rows"][0]))
    expected = os.getenv("PGDATABASE")
    if expected and row.get("database") != expected:
        raise RuntimeError(f"Expected database {expected!r}, got {row.get('database')!r}")

    return {
        "database": row.get("database"),
        "user": row.get("user"),
        "version": row.get("version"),
        "mode": "data_api",
        "cluster_id": result["cluster_id"],
    }
