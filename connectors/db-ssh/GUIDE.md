# Connector: db-ssh

## When to use

To read data from a database you can reach over the network, directly or through an SSH bastion host:
check records, count rows, inspect tables, confirm a bug in data.
Works with **PostgreSQL**, **MySQL / MariaDB**, and **SQL Server**.
If you have AWS access but no network path to an Aurora database, use `aws-rds` instead.

## Setup

1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill it in. Set `DB_ENGINE`.
3. SSH tunnel:
   - OpenSSH key: connect once by hand (`ssh user@bastion`) to accept the host key.
   - PuTTY `.ppk` key: install PuTTY (the script uses its `plink`). If plink does not know the host, set `SSH_HOST_KEY` to the fingerprint from the error message.
4. `python connectors/db-ssh/run.py test`

## Settings (`.env`)

| Setting | Meaning |
|---------|---------|
| `DB_ENGINE` | `postgres` (default), `mysql` (also MariaDB), or `sqlserver` |
| `DB_HOST`, `DB_PORT` | Database host and port. Empty port = engine default (5432, 3306, 1433) |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Database and login |
| `DB_SSLMODE` | PostgreSQL only: `disable`, `prefer` (default), `require`, `verify-full` |
| `DB_TIMEOUT_SECONDS` | Query time limit (default 60) |
| `SSH_HOST`, `SSH_PORT`, `SSH_USER` | Bastion host. Empty `SSH_HOST` = connect directly |
| `SSH_KEY` | OpenSSH key path, or a PuTTY `.ppk` key path |
| `SSH_HOST_KEY` | `.ppk` only: host key fingerprint, when plink does not know the host yet |

## Commands

| Command | What it does |
|---------|--------------|
| `test` | Connects and shows database, user, and version. |
| `tables [--schema S]` | Lists tables and views. |
| `describe <schema.table>` | Lists the columns of a table. Default schema: `public` (PostgreSQL), `dbo` (SQL Server), the database (MySQL). |
| `sql "<query>" [--limit N]` | Runs a query. Prints up to N rows (default 50). All rows go to a CSV file. |
| `sql --file q.sql` | Runs the SQL in a file. |
| `sql "<statement>" --write` | Runs a statement that changes data. Needs the user's permission. |

## How read-only works

- **PostgreSQL:** the session is read-only. The database rejects changes.
- **MySQL / MariaDB:** the session is read-only. The database rejects changes. The script also checks the SQL.
- **SQL Server:** the script allows only one `SELECT` or `WITH` statement, blocks words like `INSERT`, `UPDATE`, `DELETE`, `DROP`, `EXEC`, and always rolls the transaction back. For full safety, ask the user for a read-only database login.

## Rules

1. Before `--write`: show the user the exact statement and the target database. Wait for "yes".
2. Run `tables` and `describe` before you write a query against an unknown table.
3. Use `where` filters, `limit` / `top`, and `count(*)` first. Avoid `select *` on big tables.
4. Queries stop after `DB_TIMEOUT_SECONDS` (default 60).
5. Select only the columns you need. Do not print personal data you do not need.

## Examples

```
python connectors/db-ssh/run.py tables --schema sales
python connectors/db-ssh/run.py describe sales.orders
python connectors/db-ssh/run.py sql "select status, count(*) from sales.orders group by status"
```
