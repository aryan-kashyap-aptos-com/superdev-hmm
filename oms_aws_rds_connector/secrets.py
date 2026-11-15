"""Fetch database credentials from AWS Secrets Manager."""

from __future__ import annotations

import json
import os
from typing import Any

from client import aws_session, load_env, secret_arn
from progress import step


def _resolve_rds_host(cluster_or_instance_id: str) -> tuple[str, int]:
    step(f"Looking up RDS endpoint for {cluster_or_instance_id!r}...")
    session = aws_session()
    client = session.client("rds")

    try:
        response = client.describe_db_clusters(DBClusterIdentifier=cluster_or_instance_id)
        clusters = response.get("DBClusters", [])
        if clusters:
            cluster = clusters[0]
            host = cluster.get("Endpoint")
            if host:
                return str(host), int(cluster.get("Port") or 5432)
    except client.exceptions.DBClusterNotFoundFault:
        pass

    response = client.describe_db_instances(DBInstanceIdentifier=cluster_or_instance_id)
    instances = response.get("DBInstances", [])
    if not instances:
        raise RuntimeError(f"RDS cluster/instance not found: {cluster_or_instance_id!r}")

    instance = instances[0]
    endpoint = instance.get("Endpoint") or {}
    host = endpoint.get("Address")
    if not host:
        raise RuntimeError(f"RDS instance {cluster_or_instance_id!r} has no endpoint")

    return str(host), int(endpoint.get("Port") or instance.get("Endpoint", {}).get("Port") or 5432)


def get_db_credentials(*, verbose: bool = False) -> dict[str, Any]:
    """Return connection kwargs derived from Secrets Manager and .env overrides."""
    load_env()
    if verbose:
        step("Fetching secret from AWS Secrets Manager...")
    session = aws_session()
    client = session.client("secretsmanager")

    response = client.get_secret_value(SecretId=secret_arn())
    secret_string = response.get("SecretString")
    if not secret_string:
        raise RuntimeError("Secret has no SecretString payload")

    try:
        payload = json.loads(secret_string)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Secret value is not valid JSON") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("Secret JSON must be an object")

    username = payload.get("username") or payload.get("user")
    password = payload.get("password")
    host = payload.get("host") or payload.get("hostname") or os.getenv("PGHOST")
    port = payload.get("port") or os.getenv("PGPORT")
    dbname = os.getenv("PGDATABASE") or payload.get("dbname") or payload.get("database")
    cluster_id = (
        str(payload.get("dbClusterIdentifier") or "").strip()
        or str(payload.get("dbInstanceIdentifier") or "").strip()
        or os.getenv("RDS_CLUSTER_ID", "").strip()
    )

    if not host and cluster_id:
        host, cluster_port = _resolve_rds_host(cluster_id)
        if not port:
            port = str(cluster_port)

    if not port:
        port = "5432"

    missing = [name for name, value in (("username", username), ("password", password), ("host", host), ("dbname", dbname)) if not value]
    if missing:
        hint = " Set RDS_CLUSTER_ID or PGHOST if the secret has no host field."
        raise RuntimeError(f"Could not resolve DB fields from secret/env: {', '.join(missing)}.{hint}")

    return {
        "host": str(host),
        "port": int(port),
        "dbname": str(dbname),
        "user": str(username),
        "password": str(password),
        "cluster_id": cluster_id or None,
    }
