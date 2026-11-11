# RDS connector and AWS SSO

**Status:** verified  
**Evidence:** `tickets/RANDOM/oms-aws-rds-sso-credentials/`, `oms_aws_rds_connector/AGENTS.md`, 35+ agent transcripts on `rds-sso`

## Problem we solved

Manually copying **IAM Identity Center temporary keys** into `.env.*` for `oms_aws_rds_connector` expired constantly and broke mid-investigation.

## Pattern

1. Configure **`AWS_PROFILE`** in `.env.{tenant}` (e.g. Cole Haan prod SSO profile wired 2026-10-17).
2. Run **`aws sso login --profile <name>`** once per session.
3. Use connector CLI / Python client - it picks up profile credentials.

See `.env.example` and `client.py` in `C:\PROD\ConnectorSuite\oms_aws_rds_connector\`.

## Related DB gotcha (oms_db_connector)

When shell has `PGDATABASE=podqa`, ad-hoc queries can **lie about which DB** you hit.

- Always pass explicit `dbname=` in scripts
- `query_poddev_sql.py` was added after confusing poddev vs podqa order lookups during MQ/feed debug

## Live triage examples

- DCOMS-29916 LL Bean export limits - live DB via connector
- DCOMS-29903 True Religion delta rollup - timezone + JobManager schedule vs RDS `now()` UTC
- DCOMS-29645 PODQA simfa baseline resets
