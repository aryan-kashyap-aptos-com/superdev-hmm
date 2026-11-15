# OMS AWS RDS Connector — Agent Guide

Query AWS RDS PostgreSQL using Secrets Manager credentials — same approach as the AWS console "Connect to database" dialog.

## When to use

- Query RDS databases when you have AWS credentials + Secrets Manager ARN
- Environments like Road Runner UAT where RDS is private (no SSH tunnel needed)
- Read-only SQL against PostgreSQL 15 databases

## Setup

```powershell
cd C:\PROD\ConnectorSuite\oms_aws_rds_connector
copy .env.example .env
pip install -r requirements.txt
```

Use `--env` to point at environment-specific files (e.g. `.env.rruat`). **Never read or print `.env` contents.**

## Environment variables

| Variable | Purpose |
|----------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `AWS_SESSION_TOKEN` | Session token (required for temporary STS creds) |
| `AWS_REGION` | AWS region (e.g. `us-east-1`) |
| `RDS_CLUSTER_ID` | Cluster name from AWS console (optional if secret has `dbClusterIdentifier`) |
| `SECRET_ARN` | Secrets Manager ARN for DB credentials |
| `PGDATABASE` | Target database name |
| `CONNECTION_MODE` | `data_api` (default), `direct`, or `auto` |
| `PGHOST` | Override host (direct mode only, e.g. `127.0.0.1` for tunnel) |
| `PGPORT` | Override port (direct mode only) |
| `PGSSLMODE` | SSL mode for direct connections |
| `PGCONNECT_TIMEOUT` | Direct connection timeout (default 30s) |
| `PGPROBE_TIMEOUT` | TCP probe timeout (default 8s) |

## Connection modes

| Mode | How it works | When to use |
|------|-------------|-------------|
| `data_api` | RDS Data API over HTTPS (like AWS Query Editor) | **Default.** No tunnel needed. |
| `direct` | Direct PostgreSQL TCP via `psycopg` | When on VPN or using SSH tunnel |
| `auto` | Try direct TCP, fall back to Data API | Mixed environments |

**Prefer `data_api`** — it matches how the AWS console connects and works from any machine with valid AWS credentials.

## CLI commands

```powershell
python oms_aws_rds.py --env .env.rruat test
python oms_aws_rds.py --env .env.rruat secret-info
python oms_aws_rds.py --env .env.rruat probe
python oms_aws_rds.py --env .env.rruat sql "SELECT current_database(), current_user, now()"
python oms_aws_rds.py --env .env.rruat sql --write "UPDATE ..."  # mutations (use only when asked)
```

All commands accept `--env <path>` to select an env file (default `.env`).

## Agent rules

1. **Default to read-only** — do not use `--write` unless the user explicitly requests mutations.
2. **Never read, commit, or print** `.env`, `.env.*`, or credential values.
3. **Use `data_api` mode** unless the user needs direct/psycopg features.
4. **Use `--env`** when the user has environment-specific files (`.env.rruat`, `.env.prod`, etc.).
5. **Run `test` first** before long SQL sessions to confirm connectivity.
6. **Limit result rows** — `--limit` defaults to 50.
7. **Secret resolution order for cluster** — secret `dbClusterIdentifier` beats `RDS_CLUSTER_ID` env var.

## AWS console field mapping

| AWS Console field | Env variable |
|-------------------|--------------|
| Database instance or cluster | `RDS_CLUSTER_ID` (optional if in secret) |
| Secrets Manager ARN | `SECRET_ARN` |
| Database name | `PGDATABASE` |
| AWS session credentials | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` |

## Typical workflow

```powershell
python oms_aws_rds.py --env .env.rruat secret-info
python oms_aws_rds.py --env .env.rruat test
python oms_aws_rds.py --env .env.rruat sql "SELECT count(*) FROM oms.some_table"
```

## File map

| File | Role |
|------|------|
| `oms_aws_rds.py` | CLI entry point |
| `client.py` | Env loading, boto3 session |
| `secrets.py` | Secrets Manager credential fetch |
| `cluster.py` | RDS cluster metadata and ARN resolution |
| `data_api.py` | RDS Data API query execution |
| `db.py` | Direct PostgreSQL connection (direct mode) |
| `router.py` | Routes between data_api and direct modes |
| `probe.py` | Fast TCP reachability check |
| `progress.py` | Step-by-step CLI output |
| `.env.example` | Env template |

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Hangs with no output | Use `data_api` mode; direct TCP to private RDS will timeout |
| `DBClusterNotFound` | Check `RDS_CLUSTER_ID` — secret `dbClusterIdentifier` is preferred |
| `HttpEndpointEnabled: False` | Enable Data API on the cluster, or use `direct` + SSH tunnel |
| TCP probe fails | Expected for private RDS — use `CONNECTION_MODE=data_api` |
| Expired credentials | Refresh `AWS_SESSION_TOKEN` (STS tokens expire) |
| Wrong database | Verify `PGDATABASE` matches the console database name |

## Direct mode + tunnel (fallback)

Only needed if Data API is disabled:

```powershell
# In oms_db_connector:
python oms_db.py tunnel start

# In .env, set:
# CONNECTION_MODE=direct
# PGHOST=127.0.0.1
# PGPORT=1112
```
