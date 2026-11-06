# Connector: aws-rds

## When to use

To read data from an AWS Aurora database (PostgreSQL or MySQL) through the RDS Data API.
Use it when you have AWS access but no network path to the database (no VPN, no bastion).
If you can reach the database over the network or through an SSH bastion, use `db-ssh` instead.

## Setup

1. `pip install -r connectors/requirements.txt`
2. The cluster must have the Data API turned on. The database password must be stored in AWS Secrets Manager.
3. Copy `.env.example` to `.env` and fill it in. Set `RDS_ENGINE` to `postgres` or `mysql`.
4. Log in to AWS the way you normally do (profile or SSO), then run `python connectors/aws-rds/run.py test`.

## Settings (`.env`)

| Setting | Meaning |
|---------|---------|
| `AWS_PROFILE`, `AWS_REGION` | Your AWS login profile and region |
| `RDS_ENGINE` | `postgres` (default) or `mysql` |
| `RDS_CLUSTER_ARN` | ARN of the Aurora cluster |
| `RDS_SECRET_ARN` | ARN of the Secrets Manager secret with the database login |
| `DB_NAME` | Database name |

## Commands

| Command | What it does |
|---------|--------------|
| `test` | Runs a small query and shows database, user, and version. |
| `tables [--schema S]` | Lists tables and views. |
| `describe <schema.table>` | Lists the columns of a table. Default schema: `public` (PostgreSQL) or the database (MySQL). |
| `sql "<query>" [--limit N]` | Runs a query. Prints up to N rows (default 50). All rows go to a CSV file. |
| `sql --file q.sql` | Runs the SQL in a file. |
| `sql "<statement>" --write` | Runs a statement that changes data. Needs the user's permission. |

## How read-only works

- **PostgreSQL:** every query runs in a read-only transaction. The database rejects changes.
- **MySQL:** the script allows only one `SELECT`, `WITH`, `SHOW`, `DESCRIBE` or `EXPLAIN` statement, and blocks words like `INSERT`, `UPDATE`, `DELETE`, `DROP`, `CALL`. The transaction is always rolled back.
- `SELECT ... FOR UPDATE` is blocked in read-only mode. You do not need it to read.

## Rules

1. Before `--write`: show the user the exact statement and the cluster. Wait for "yes".
2. The Data API returns at most 1 MB per query. Use filters and `limit`.
3. If the error says the cluster is resuming, wait 30 seconds and try once more.

## Examples

```
python connectors/aws-rds/run.py tables --schema public
python connectors/aws-rds/run.py sql "select id, status, updated_at from orders where id = 1042"
```
