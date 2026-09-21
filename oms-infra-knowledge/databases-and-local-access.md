# Databases and local access

Postgres for shared dev / QA often sits behind the **same RDS Proxy** (`oms-shared-dev-postgresql-rds-proxy…`). Multiple **database names** coexist on that cluster; Toronado and apps connect directly from EC2. Your laptop uses a **bastion SSH tunnel**.

## Database vs Toronado host (quick map)

| Postgres database | OMS `environment` name (example) | Toronado EC2 |
|-------------------|----------------------------------|--------------|
| `regression202510qa` | `regression202510qa` | `eom-core-shared-dev-toronado` |
| `poddev` | pod2-dev / shared dev contexts | `oms-pod2-dev-toronado` (standalone pod2) |
| perf15 QA DB | perf15 QA env | `eom-core-perf15-qa-toronado` |

Changing **only** the database segment in a local connection string (MCP or `oms_db_connector`) switches **which data you query**. It does **not** reconfigure Toronado on AWS.

## Local tunnel ports (typical on this team)

| Port | Common use |
|------|------------|
| `1111` | Cursor Postgres MCP (`~/.cursor/mcp.json`) |
| `1112` | `oms_db_connector` (`.env` `PGPORT`) |

Use **one tunnel per local port**. User/credential pairs are **per role** (e.g. `shareddev_postgres` vs `podqa_postgres`) — match what your DBA/runbook specifies for each database.

## MCP (Cursor)

Config file: `C:\Users\<user>\.cursor\mcp.json` → `postgres` server connection URL.

After edits, reload the Postgres MCP server (toggle in Cursor Settings → MCP).

## `oms_db_connector`

```powershell
cd C:\PROD\ConnectorSuite\oms_db_connector
python oms_db.py tunnel start
python oms_db.py test
```

Set `PGDATABASE` in `.env` to the target database (e.g. `regression202510qa`). Do not commit `.env`.

## When Toro looks “down” in SQL

On the **correct** database:

- `SELECT max(lastrundate) FROM oms.job WHERE active = true;` — flat line for hours ⇒ processors not completing work.
- `oms.jobqueue` with `processstate = 0` and recent `laststatechangedate` ⇒ queued but not picked up.

Then SSM to the Toronado host from [toronado-hosts.md](./toronado-hosts.md) for that environment’s `OMS-JobProcessor-*` service.
