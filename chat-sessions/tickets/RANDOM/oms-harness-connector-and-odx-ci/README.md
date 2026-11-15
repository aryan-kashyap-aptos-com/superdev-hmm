# OMS Harness connector + ODX CI investigation

**Last updated:** 2026-09-19  
**Status:** in progress

## Intent

Stand up **Harness MCP** for Aptos OMS CI/CD in ConnectorSuite, fix scope and Cursor wiring, and document **build vs deploy** behavior for **ODX Feed Pipeline Monitor** (DCOMS-29203) work on `c:\oms`.

## Status snapshot

| Area | State |
|------|--------|
| `oms_harness_connector` | Created; Node MCP launcher; `.env` scope **`OMS_CICD` / `OMS_Development`** |
| Cursor `mcp.json` | `harness` → `node.exe` + `run-harness-mcp.js` |
| Harness MCP in agent | User must **restart MCP** in Cursor; session may still show discovery error until reload |
| API scripts | `Fetch-PipelineData.ps1` lists executions; sample failure analyzed |
| ODX feature branch | Canonical: `feature/akashyap/DCOMS-29203-odx-feed-pipeline-e2e` on `c:\oms` |
| Pod stale React UI | Hypothesis: Mocha fails before `npm run build` in `buildreact.ps1`; deploy can still succeed |

## Decisions

- Use official **[harness/mcp-server](https://github.com/harness/mcp-server)** via `npx harness-mcp-v2@latest`, not a custom API wrapper.
- Store PAT only in gitignored `oms_harness_connector/.env`.
- UI org **Aptos OMS** → Harness identifier **`OMS_CICD`** (discovered via aggregate projects API).
- Durable pipeline write-up lives in **`oms_harness_connector/docs/OMS-HARNESS-PIPELINE-REFERENCE.md`**.

## Artifacts

| Item | Path |
|------|------|
| Harness connector | `oms_harness_connector/` |
| Pipeline reference (markdown) | `oms_harness_connector/docs/OMS-HARNESS-PIPELINE-REFERENCE.md` |
| Sample execution JSON | `oms_harness_connector/exports/execution-detail.json` |
| ODX epic docs | `tickets/DCOMS-29203-odx-feed-pipeline-monitor/` |
| NuGet local build kit | `oms-nuget-aws-setup/` |
| Infra index | `oms-infra-knowledge/README.md` |

## Open questions

- Confirm **Sonar** failure text in UI for exec `7QqDKxvCRjO9f8FktVIAsg` (`sonar_qube_analysis_sm_npgsql`).
- Whether Furnace/Harness step should **fail** when `buildreact.ps1` returns non-zero.
- Exact **Harness project** for **OMS-App-Deploy** when not in `OMS_Development`.

## Previous names

- (none)
