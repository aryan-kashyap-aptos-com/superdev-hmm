# OMS Harness MCP — Agent Guide

Use the **harness** MCP server ([github.com/harness/mcp-server](https://github.com/harness/mcp-server)) for CI/CD investigation on OMS.

**Durable pipeline notes:** [docs/OMS-HARNESS-PIPELINE-REFERENCE.md](./docs/OMS-HARNESS-PIPELINE-REFERENCE.md)  
**Chat session:** [../tickets/RANDOM/oms-harness-connector-and-odx-ci/](../tickets/RANDOM/oms-harness-connector-and-odx-ci/)

## When to use

- Pipeline run failed (compile, React `buildreact.ps1`, deploy)
- Find latest execution for a branch or pipeline name
- Read stage/step status and logs metadata
- Compare deploy pipelines (**OMS-App-Deploy**, **OMS-DFS-Namespace**)

## Rules

1. **Never read or print** `oms_harness_connector/.env` or API keys.
2. **Confirm scope** — org, project, pipeline name, time range — before write actions.
3. **Read before write** — prefer `harness_list` / `harness_get` over create/update/trigger unless the user asks to run or change something.
4. **OMS context** — pod deploys often use registry key `pod2` when Harness env is `pod2-dev` (see `tickets/DCOMS-29691-pod2dev-ec2-shutdown-restart-validation` runbooks).

## Typical flow

1. `harness_list` organizations (if `HARNESS_ORG` not set in `.env`).
2. `harness_list` projects in that org.
3. `harness_list` pipelines (or filter by name containing `OMS`, `npgsql`, `Furnace`).
4. `harness_get` / list executions for the pipeline; drill into failed stages.

## Aptos OMS scope (from Harness UI)

| UI name | Typical `identifier` | Use for |
|---------|----------------------|---------|
| **Aptos OMS** (UI label) | **`OMS_CICD`** (Harness org identifier) | All OMS pipelines in that org |
| **OMS Development** | `OMS_Development` | Dev team builds (npgsql, React, most feature branches) |
| **OMS DevOps** | `OMS_DevOps` | Release / Harness maintenance (**OMS-App-Deploy**, DFS) |
| **oms-*-dev** client projects | e.g. `omstoommybahamamdev` | Client-specific pod pipelines only |

Set `HARNESS_ORG` + `HARNESS_PROJECT` in `.env` so MCP defaults match where you work.

## Optional `.env` defaults

| Variable | Purpose |
|----------|---------|
| `HARNESS_ORG` | Default org identifier |
| `HARNESS_PROJECT` | Default project identifier |
| `HARNESS_BASE_URL` | Non-default Harness host |

Account id is usually parsed from `pat.<accountId>...` / `sat.<accountId>...` tokens.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| MCP server fails to start | Check `.env` exists; `HARNESS_API_KEY` is a real PAT/SAT |
| `spawn npx ENOENT` | Use `Start-HarnessMcp.ps1` (absolute Node path) in `mcp.json` |
| 401 / forbidden | Rotate key; confirm account and RBAC in Harness UI |
| Wrong SaaS environment | Set `HARNESS_BASE_URL` in `.env` |
