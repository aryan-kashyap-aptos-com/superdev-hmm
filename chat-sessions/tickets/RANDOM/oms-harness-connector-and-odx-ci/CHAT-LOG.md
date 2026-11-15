# Chat log — OMS Harness connector and ODX CI

Newest session sections first.

---

## 2026-09-19 — Green CI but stale ODX UI (alpha_common skipped)

**Status when closed:** in progress

- Latest **Success** `oms_release_pipeline` (`kHsWghZhTf6SqXxa7hU3gg`) built tag `1.58.0-feature-1ff56a0` / commit `7c29f19317` but **`alpha_common` = Skipped**; only **`alpha_windows`** ran. No Linux/React/npgsql stage on that green run.
- **Success** `OMSDEVSITEMANAGERSHAREDCD` deploy was **manual**; does not imply that run’s artifact included new `static/` React.
- Documented in `oms_harness_connector/docs/OMS-HARNESS-PIPELINE-REFERENCE.md`.

---

## 2026-09-19 — Harness connector, pipeline analysis, session docs

**Status when closed:** in progress

### What we did

- Confirmed there was **no** existing Harness connector; added **`oms_harness_connector`** using [harness/mcp-server](https://github.com/harness/mcp-server).
- Wired **Cursor MCP** (`%USERPROFILE%\.cursor\mcp.json`): fixed PowerShell **em dash** parse error; switched to **`run-harness-mcp.js`** (Node stdio) instead of PowerShell → npx.
- Mapped Harness UI **Aptos OMS** → org id **`OMS_CICD`**; **OMS Development** → **`OMS_Development`** (not `Aptos_OMS`).
- Pulled recent executions via **`scripts/Fetch-PipelineData.ps1`**; analyzed failed **`oms_release_pipeline`** run **`7QqDKxvCRjO9f8FktVIAsg`** → failed step **`sonar_qube_analysis_sm_npgsql`** in stage **`alpha`** (`exit status 1`); **`beta` skipped**.
- Noted **successful** **`OMSDEVSITEMANAGERSHAREDCD`** / **`sitemanager_deploy`** deploys vs **compile/React** path in **`oms_release_pipeline`**.
- Documented **stale ODX UI** hypothesis: **`buildreact.ps1`** runs full Mocha before `npm run build`; failures (e.g. Service Manager tests) can block React artifacts while pipeline/deploy still looks green.
- Local React dev: Node **18** via npx for `react-scripts` 1.x; mock ODX via `REACT_APP_ODX_FEED_MONITOR_MOCK` / `Start-OdxFeedMonitorReactDev.ps1`.
- Saved durable pipeline reference and this **tickets/RANDOM/** folder per `.cursor/rules/connector-suite-ticket-chat-sessions.mdc`.

### Files touched (paths)

- `oms_harness_connector/` — README, AGENTS.md, `.env.example`, `run-harness-mcp.js`, `cursor-mcp.snippet.json`, `scripts/*`, `docs/OMS-HARNESS-PIPELINE-REFERENCE.md`, `exports/execution-detail.json`
- `oms-infra-knowledge/README.md` — link to harness connector
- `tickets/RANDOM/oms-harness-connector-and-odx-ci/README.md`, `CHAT-LOG.md`
- User machine: `%USERPROFILE%\.cursor\mcp.json` (harness server entry)

### Related OMS work (context)

- Epic **DCOMS-29203** / branch **`feature/akashyap/DCOMS-29203-odx-feed-pipeline-e2e`**
- Docs: `tickets/DCOMS-29203-odx-feed-pipeline-monitor/`
- `oms-nuget-aws-setup/` for CodeArtifact + MSBuild slice
