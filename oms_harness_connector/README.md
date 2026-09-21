# OMS Harness connector (MCP)

Thin wrapper around [Harness MCP Server 2.0](https://github.com/harness/mcp-server) so Cursor agents can list pipelines, inspect executions, and debug OMS CI (for example **OMS-App-Deploy**, Furnace/npgsql builds) without leaving the IDE.

## Setup

```powershell
cd C:\PROD\ConnectorSuite\oms_harness_connector
copy .env.example .env
# Edit .env — set HARNESS_API_KEY to a Harness PAT or SAT (not a random placeholder)
```

Wire Cursor once (global config):

1. Open **Cursor Settings → MCP** or edit `%USERPROFILE%\.cursor\mcp.json`.
2. Use the `harness` entry from [cursor-mcp.snippet.json](./cursor-mcp.snippet.json) — **Node** runs [run-harness-mcp.js](./run-harness-mcp.js) (do not use PowerShell for MCP; it breaks stdio on Windows).

Reload MCP servers in Cursor (or restart Cursor).

### Troubleshooting MCP "failed discovery"

| Symptom | Fix |
|---------|-----|
| Red harness server in Cursor | Restart harness MCP after updating `mcp.json` to use `node.exe` + `run-harness-mcp.js` |
| `spawn npx ENOENT` | Set `PATH` in `mcp.json` env to `C:\\Program Files\\nodejs` |
| Wrong default org/project | Run `scripts\\Resolve-OrgId.ps1`, fix `HARNESS_ORG` / `HARNESS_PROJECT` in `.env`, restart MCP |
| API works but wrong pipelines | Deploy pipelines may be under another project (e.g. shared CD); override `project_id` per call or paste execution URL |

## Verify

After reload, the agent should see Harness tools (`harness_list`, `harness_get`, etc.). Try: list organizations, then pipelines in your OMS org/project.

## Documentation

| Doc | Purpose |
|-----|---------|
| [docs/OMS-HARNESS-PIPELINE-REFERENCE.md](./docs/OMS-HARNESS-PIPELINE-REFERENCE.md) | Org/project ids, pipelines, failure analysis, React CI notes (for new chats) |
| [AGENTS.md](./AGENTS.md) | Agent playbook |
| [../tickets/RANDOM/oms-harness-connector-and-odx-ci/](../tickets/RANDOM/oms-harness-connector-and-odx-ci/) | Session README + CHAT-LOG |

## Files

| Path | Purpose |
|------|---------|
| `run-harness-mcp.js` | Cursor MCP entry (preferred) |
| `scripts/Start-HarnessMcp.ps1` | Terminal smoke test (calls `run-harness-mcp.js`) |
| `scripts/Fetch-PipelineData.ps1` | List executions + detail without MCP |
| `.env` | Local API key (gitignored) |
| `AGENTS.md` | Agent playbook for OMS Harness tasks |
| `cursor-mcp.snippet.json` | Copy-paste MCP block |

## Hosted MCP (optional)

Harness also offers `https://mcp.harness.io/mcp` with **OAuth** (not API keys). That path requires account enablement by Harness Support. This folder uses the **local npx** path so you can set `HARNESS_BASE_URL` for non-default SaaS hosts.

## Security

- Never commit `.env`.
- Never paste PATs into chat or into repo files.
- Prefer scoped PAT/SAT with least privilege.
