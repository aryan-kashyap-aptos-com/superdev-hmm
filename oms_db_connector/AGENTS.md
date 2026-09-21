# OMS DB Connector — Agent Guide

PostgreSQL access via SSH tunnel through a bastion host to RDS Proxy.

## When to use

- Query OMS PostgreSQL databases that require bastion/SSH access
- Run read-only SQL against `oms` schema databases
- Local development when RDS is not directly reachable

## Setup

```powershell
cd C:\PROD\ConnectorSuite\oms_db_connector
copy .env.example .env
pip install -r requirements.txt
```

Fill in `.env` with bastion SSH details and PostgreSQL credentials. **Never read or print `.env` contents.**

## Environment variables

| Variable | Purpose |
|----------|---------|
| `PGHOST` | Local tunnel endpoint (default `127.0.0.1`) |
| `PGPORT` | Local tunnel port (default `1112`) |
| `PGDATABASE` | Target database name |
| `PGUSER` | PostgreSQL username |
| `PGPASSWORD` | PostgreSQL password |
| `PGSSLMODE` | SSL mode (default `require`) |
| `PGCONNECT_TIMEOUT` | Connection timeout seconds |
| `SSH_HOST` | Bastion hostname |
| `SSH_PORT` | Bastion SSH port (default `22`) |
| `SSH_USER` | Bastion SSH user |
| `SSH_PPK_PATH` | Path to PuTTY `.ppk` key file |
| `SSH_REMOTE_HOST` | RDS proxy hostname |
| `SSH_REMOTE_PORT` | RDS port (default `5432`) |

## CLI commands

```powershell
python oms_db.py tunnel start          # start SSH tunnel (required before queries)
python oms_db.py tunnel status         # check tunnel status
python oms_db.py tunnel stop           # stop tunnel
python oms_db.py test                  # verify DB connection
python oms_db.py sql "SELECT 1"        # read-only query (default)
python oms_db.py sql --write "UPDATE ..."  # mutations (use only when asked)
```

## Agent rules

1. **Always start the tunnel** before `test` or `sql` if status shows not running.
2. **Default to read-only** — do not use `--write` unless the user explicitly requests mutations.
3. **Never read, commit, or print** `.env` or credentials.
4. **Expect PostgreSQL 15** — `verify_database()` enforces PG 15 and checks `PGDATABASE`.
5. **Limit result rows** — use `--limit` (default 50) for large result sets.
6. **Schema** — OMS data lives in the `oms` schema unless the user specifies otherwise.

## Typical workflow

```powershell
python oms_db.py tunnel start
python oms_db.py tunnel status
python oms_db.py test
python oms_db.py sql "SELECT current_database(), version()"
python oms_db.py sql "SELECT count(*) FROM oms.some_table"
```

## File map

| File | Role |
|------|------|
| `oms_db.py` | CLI entry point |
| `db.py` | Env loading, `connect()`, `session()` |
| `tunnel.py` | SSH port-forward management |
| `ppk.py` | PuTTY key parser |
| `.env.example` | Env template |

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Tunnel not running | `python oms_db.py tunnel start` |
| Connection timeout | Check bastion host, PPK path, and RDS proxy host |
| Wrong database | Verify `PGDATABASE` in `.env` |
| PG version error | Connector expects PostgreSQL 15 |
