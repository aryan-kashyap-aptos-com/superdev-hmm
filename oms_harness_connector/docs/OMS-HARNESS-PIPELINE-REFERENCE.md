# OMS Harness pipelines — reference (ConnectorSuite)

**Last updated:** 2026-09-21  
**Account:** parsed from PAT (`82alj-w-QGSN-OFFBTv9Ew` in our sessions)  
**Harness base:** `https://app.harness.io`

Durable notes from API/MCP investigation. For live runs, use `scripts/Fetch-PipelineData.ps1` or Harness MCP after restart.

---

## Scope (critical)

| Harness UI | API identifier | Notes |
|------------|----------------|-------|
| Org **Aptos OMS** | **`OMS_CICD`** | **Not** `Aptos_OMS` — wrong org causes `INVALID_REQUEST` / invalid scope |
| Project **OMS Development** | **`OMS_Development`** | Main dev CI: `oms release pipeline`, npgsql, React build |
| Project **OMS DevOps** | **`OMS_DevOps`** | Release / Harness maintenance (e.g. **OMS-App-Deploy**, DFS) |
| Client pod projects | e.g. `omstommybahamadev` | Under same org `OMS_CICD`; use only for client-specific CD |

Set in `oms_harness_connector/.env`:

```env
HARNESS_ORG=OMS_CICD
HARNESS_PROJECT=OMS_Development
```

Discover projects: `scripts/Dump-ScopeRaw.ps1` → `exports/project-table.txt`.

---

## Pipelines we care about

| Pipeline id (typical) | Purpose |
|----------------------|---------|
| **`oms_release_pipeline`** | Linux CI: alpha/beta, parallel builds (Payment, Crypto, OMS, **Build OMS Npgsql**), unit tests, versioning, artifact tag |
| **`oms_release_windows_pipeline`** | Windows leg (`alpha_win`, npgsql-related windows steps) |
| **`OMSDEVSITEMANAGERSHAREDCD`** | Shared dev **Site Manager deploy** (`sitemanager_deploy`, WinRM, artifact expand) — deploy, not compile |
| **OMS-App-Deploy** / **OMS-DFS-Namespace** | Documented in pod2 runbooks under **OMS DevOps** project (not always in `OMS_Development` list) |

**Build vs deploy:** Green **OMSDEVSITEMANAGERSHAREDCD** does not prove a new React bundle was built. Compile + `buildreact.ps1` live in **`oms_release_pipeline`** (and related CI).

---

## Manual run: input set **`oms_push`** (branch build, not tag webhook)

Use this when you want **`oms release pipeline`** to build a **Bitbucket branch** instead of waiting for **`tag_oms`**.

### Harness UI (operator)

1. **OMS Development** → **`oms release pipeline`** → **Run**.
2. **Use existing input sets** → select **`oms_push`**.
3. Set runtime inputs (names match what the input set defines; from execution YAML these resolve to CI codebase):
   - **Repo name:** `oms` → `pipeline.properties.ci.codebase.repoName`
   - **Branch:** e.g. `feature/akashyap/DCOMS-29203-odx-feed-pipeline-ci` → codebase branch on clone steps
4. **Run pipeline**. Trigger type in API is **`MANUAL`** (not `WEBHOOK` / `tag_oms`).

### What we learn from execution detail

| Field | Example |
|-------|---------|
| `inputSetIdentifiers` | `[ "oms_push" ]` |
| `repoName` | `oms` |
| `branch` | `feature/akashyap/DCOMS-29203-odx-feed-pipeline-e2e` (or `-ci` branch) |
| Companion run | **`oms_release_windows_pipeline`** often starts in parallel |

**Stage selection:** `alpha_common` runs when **`ENABLE_WINDOWS`** is not forcing Windows-only; `alpha_windows` when `ENABLE_WINDOWS == "true"` or repo is `eom-kernel` (see `whenCondition` in execution graph). For ODX React, prefer a run where **`alpha_common` = Success**, not Skipped.

### API (for later automation — not used in chat yet)

- Endpoint family: `POST /pipeline/api/pipeline/execute/oms_release_pipeline?...&inputSetIdentifiers=oms_push`
- Body: runtime input YAML (fetch template from Harness **Run** UI or Input Sets API when Git-backed).
- Read-only probe script: `scripts/Get-OmsPushInputSetTemplate.ps1` (template URLs vary by Git Experience; may 404 without correct `repoIdentifier` / branch query params).

### After you trigger: quick checks

```powershell
powershell -File C:\PROD\ConnectorSuite\oms_harness_connector\scripts\Fetch-PipelineData.ps1 -ExecutionLimit 10
powershell -File C:\PROD\ConnectorSuite\oms_harness_connector\scripts\Get-ExecutionMeta.ps1 -ExecId <planExecutionId>
```

Confirm **branch** on the execution, **`inputSetIdentifiers` includes `oms_push`**, and stage graph (**`alpha_common`** vs **`alpha_windows`**).

---

## Sample execution snapshot (2026-09-19 API pull)

Recent executions in **OMS_Development** (newest first, truncated):

| Status | Pipeline | planExecutionId |
|--------|----------|-----------------|
| Success | OMSDEVSITEMANAGERSHAREDCD | `ACjMzhx7Shak5mLsyCvlYA` |
| Success | oms_release_pipeline | `kHsWghZhTf6SqXxa7hU3gg`, `y82oJKhxTkOO1xxTXut2qg` |
| **Failed** | oms_release_pipeline | **`7QqDKxvCRjO9f8FktVIAsg`**, `abasoxtGRO-eSWXHsRLSqg` |
| **Failed** | oms_release_windows_pipeline | `d7WCb98-QTu9s2c5Ox-0MQ`, `Yx3JZFEUT4q0bHkSFjzTaw` |

### Failed release run `7QqDKxvCRjO9f8FktVIAsg`

- **Pipeline:** `oms_release_pipeline` (manual rerun chain)
- **Harness failure metadata:**
  - **Stage:** `alpha`
  - **Step:** **`sonar_qube_analysis_sm_npgsql`**
  - **Message:** `exit status 1` (generic; open step console for Sonar CLI/gate detail)
- **Effect:** **`beta` stage skipped** after alpha failure
- **Saved graph:** `exports/execution-detail.json` (regenerate via `Fetch-PipelineData.ps1`)

This failure is **Sonar on SM/npgsql**, not deploy WinRM. Do not confuse with successful **sitemanager_deploy** logs.

---

## Stale ODX / React UI on pod (hypothesis, OMS repo)

From `c:\oms\Shopvisible.Core.Shoplogic.Frontend.React\buildreact.ps1`:

1. `npm install`
2. **`npm run unittests`** (full Mocha suite)
3. Only if exit **0** → `npm run build` → copy to `ShopVisible.Core.ShopLogic/static/`

**Risk:** Mocha fails (historically **Service Manager** / `TaskSchedulerView`, not ODX) → **no `npm run build`** → pod keeps old `static/` React. Harness may still print “Building react completed” if the **wrapper ignores `buildreact.ps1` exit code** (see `Jenkins Build Scripts/BuildAll.Pipeline.jenkins` — invoke without hard-fail).

**Pod symptom:** old ODX placeholder (“API connected. Summary rows: undefined”) while API/backend are newer.

**Verify in Harness:** `oms_release_pipeline` → **Build OMS** / **Build OMS Npgsql** step logs → search `Mocha exit code`, `Running build`, `buildreact`.

### Green pipeline but UI still old (2026-09-19 finding)

Latest **Success** `oms_release_pipeline` exec **`kHsWghZhTf6SqXxa7hU3gg`** (webhook `tag_oms`, tag `1.58.0-feature-1ff56a0`, commit `7c29f19317`):

| Node | Status |
|------|--------|
| **`alpha_common`** (Linux CI: clone, **Build OMS Npgsql**, React, unit tests) | **Skipped** |
| `alpha_windows` | Success |
| `beta` | Skipped |
| Pipeline overall | **Success** |

So Harness can show **Success** while **the stage that runs `buildreact.ps1` never ran**. The following **manual** deploy **`ACjMzhx7Shak5mLsyCvlYA`** (`OMSDEVSITEMANAGERSHAREDCD`) only copies whatever **artifact/version** you selected; it does not rebuild React.

**Implication:** API/backend may update from other paths; **`ShopVisible.Core.ShopLogic/static/js/mainReact.js`** (+ chunks) stay old until a run where **`alpha_common` succeeds** (not skipped) and that artifact is what deploy promotes.

**Checks on pod:** compare `mainReact.js` timestamp/hash; confirm deploy input version matches a build with `alpha_common` Success; open browser devtools Network for missing `*chunk.js` after lazy `OdxFeedMonitorApp` import.

---

## Connector tooling

| Path | Role |
|------|------|
| `run-harness-mcp.js` | Cursor MCP entry (load `.env`, `npx harness-mcp-v2@latest`) |
| `cursor-mcp.snippet.json` | Paste into `%USERPROFILE%\.cursor\mcp.json` |
| `scripts/Fetch-PipelineData.ps1` | List executions + execution detail + log fetch attempt |
| `scripts/Dump-ScopeRaw.ps1` | Org/project discovery → `exports/` |
| `AGENTS.md` | Agent playbook |
| [github.com/harness/mcp-server](https://github.com/harness/mcp-server) | Official MCP (11 tools, 251 resource types) |

### MCP capabilities (summary)

| Tool | Use |
|------|-----|
| `harness_list` / `harness_get` | Pipelines, executions, orgs, projects |
| `harness_diagnose` | Failed runs; **`include_logs: true`** for step consoles |
| `harness_search` | Find pipelines by name |
| `harness_execute` | Run/retry pipeline (confirm with user) |
| `harness_status` | Recent failures in project |

Paste a **Harness execution URL** into tools that support `url` for auto scope.

### Known pitfalls

- **Wrong org** `Aptos_OMS` → APIs fail; use **`OMS_CICD`**.
- **PowerShell** `".../$execId?$q"` — `$execId?` parses wrong; use **`${execId}?`** in URLs.
- **Log REST** (`log-service/v1/logs`) returned **404** in our script; prefer **`harness_diagnose`** via MCP for consoles.
- **MCP on Windows:** use **Node** launcher, not PowerShell wrapper (stdio).
- **Secrets:** never commit `.env`; rotate PAT if exposed in chat.

---

## Related ConnectorSuite / OMS work

| Topic | Path |
|-------|------|
| ODX monitor epic | `tickets/DCOMS-29203-odx-feed-pipeline-monitor/` |
| OMS branch (CI) | `c:\oms` — `feature/akashyap/DCOMS-29203-odx-feed-pipeline-ci` |
| OMS branch (e2e) | `feature/akashyap/DCOMS-29203-odx-feed-pipeline-e2e` (same code; `-ci` has prep commit for builds) |
| Local NuGet/build | `oms-nuget-aws-setup/` |
| Pod2 deploy runbooks | `tickets/DCOMS-29691-pod2dev-ec2-shutdown-restart-validation/` |
| Chat session folder | `tickets/RANDOM/oms-harness-connector-and-odx-ci/` |
