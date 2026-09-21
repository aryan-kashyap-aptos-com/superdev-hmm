"""Resolve RDS cluster metadata for Data API connections."""

from __future__ import annotations

import os
from typing import Any

from client import aws_session, load_env, secret_arn
from progress import step
from secrets import get_db_credentials


def _cluster_id_from_secret() -> str:
    import json

    load_env()
    session = aws_session()
    client = session.client("secretsmanager")
    payload = json.loads(client.get_secret_value(SecretId=secret_arn())["SecretString"])
    if not isinstance(payload, dict):
        raise RuntimeError("Secret JSON must be an object")
    cluster_id = (
        str(payload.get("dbClusterIdentifier") or "").strip()
        or str(payload.get("dbInstanceIdentifier") or "").strip()
        or os.getenv("RDS_CLUSTER_ID", "").strip()
    )
    if not cluster_id:
        raise RuntimeError("Could not resolve RDS cluster id from secret or RDS_CLUSTER_ID")
    return cluster_id


def get_cluster_info(*, verbose: bool = False) -> dict[str, Any]:
    load_env()
    creds = get_db_credentials(verbose=verbose)
    cluster_id = str(creds.get("cluster_id") or _cluster_id_from_secret())

    if verbose:
        step(f"Fetching cluster metadata for {cluster_id!r}...")

    session = aws_session()
    client = session.client("rds")
    response = client.describe_db_clusters(DBClusterIdentifier=cluster_id)
    clusters = response.get("DBClusters", [])
    if not clusters:
        raise RuntimeError(f"RDS cluster not found: {cluster_id!r}")

    cluster = clusters[0]
    cluster_arn = cluster.get("DBClusterArn")
    if not cluster_arn:
        raise RuntimeError(f"RDS cluster {cluster_id!r} has no ARN")

    return {
        "cluster_id": cluster_id,
        "cluster_arn": str(cluster_arn),
        "http_endpoint_enabled": bool(cluster.get("HttpEndpointEnabled")),
        "engine": str(cluster.get("Engine") or ""),
        "dbname": str(creds["dbname"]),
        "user": str(creds["user"]),
    }
