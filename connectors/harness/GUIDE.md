# Connector: harness

## When to use

To check Harness CI/CD pipelines: which runs failed, which stage failed and why, who triggered a run, what ran recently.
Starting a run is possible but needs permission.

## Setup

1. Create a Harness API key (your profile → API Keys → Token).
2. Copy `.env.example` to `.env` and fill it in.
3. `python connectors/harness/run.py test`

## Commands

| Command | What it does |
|---------|--------------|
| `test` | Checks access to the project. |
| `list [--search TEXT]` | Lists pipelines with their last status. |
| `runs [--pipeline ID] [--status Failed] [--limit 20]` | Lists recent runs. |
| `run-detail <execution_id>` | Shows each stage, its status, and the failure message. |
| `start <pipeline_id> [--inputs file.yaml] --write` | Starts a run. Needs the user's permission. |

Global options before the command: `--org ORG --project PROJECT` (defaults come from `.env`).

## Rules

1. For a failure, use `runs --status Failed`, then `run-detail` on the run. Read the failure message before you guess.
2. Before `start`: tell the user the pipeline, the environment it deploys to, and the inputs. Wait for "yes".
3. Never start a pipeline that deploys to production unless the user names production explicitly.
4. If the failure message points to logs or a server, continue with the `sumologic` or `ec2-ssm` connector.

## Examples

```
python connectors/harness/run.py runs --status Failed --limit 10
python connectors/harness/run.py run-detail AbC123xyz
python connectors/harness/run.py --project payments list --search deploy
```

## Using it from Cursor as an MCP server (OMS)

For deeper, OMS-specific pipeline investigation (org/project scope resolution, React build history, deploy pipeline
comparisons) beyond the three CLI commands above, this folder also wires up the official
[Harness MCP Server](https://github.com/harness/mcp-server) for Cursor, plus terminal-only scripts that call the
Harness API directly without MCP.

1. Copy `.env.example` to `.env` here and set `HARNESS_API_KEY` (same file `run.py` uses — nothing extra to configure).
2. In Cursor Settings → MCP (or `%USERPROFILE%\.cursor\mcp.json`), add the `harness` entry from
   [cursor-mcp.snippet.json](./cursor-mcp.snippet.json), replacing `<path-to-this-repo>` with where you cloned this repo.
   Node runs [run-harness-mcp.js](./run-harness-mcp.js) — don't use a PowerShell wrapper, it breaks MCP's stdio on Windows.
3. Reload MCP servers in Cursor. You should see tools like `harness_list`, `harness_get`.

See [AGENTS.md](./AGENTS.md) for the OMS-specific agent playbook (org/project scope table, typical flow, troubleshooting)
and [docs/OMS-HARNESS-PIPELINE-REFERENCE.md](./docs/OMS-HARNESS-PIPELINE-REFERENCE.md) for durable pipeline notes.
`scripts/` holds terminal fallbacks (`Fetch-PipelineData.ps1`, `Resolve-OrgId.ps1`, `Discover-Scope.ps1`, and others)
for probing the Harness API directly when MCP isn't available.
