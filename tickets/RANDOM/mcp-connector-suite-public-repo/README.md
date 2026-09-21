# MCP Connector Suite — public cloneable repo

**Intent:** Publish ConnectorSuite connectors + agent rules in `mcp-connector-suite` so anyone can clone, configure `.env`, and use the same Cursor/agent workflows.

**Status:** Implemented in Downloads clone (2026-09-20)

## Target path

`C:\Users\akashyap\Downloads\mcp-connector-suite-main\mcp-connector-suite-main\`

## In scope

| Source (ConnectorSuite) | Destination role |
|-------------------------|------------------|
| `Rules/` (already in target) | Agent engineering rules |
| `oms_*_connector/` (5 folders) | Runnable connector packages |
| `oms-infra-knowledge/` | Optional `docs/infra/` (OMS-specific reference) |

## Out of scope (stay in PROD only)

- `tickets/` — internal Jira/session work
- `scripts/apply-missing-name-tags.py` and name-tag runs
- `shared-mq-pilot-pod-omnipod/` — ops pilot with SSM secrets workflow
- `oms-nuget-aws-setup/` — local OMS MSBuild helper (not a connector)
- Any `.env`, `.env.*`, credentials, or baseline JSON with secrets

## Decisions (proposed)

1. **Layout:** `connectors/<name>/` under monorepo root; keep Python entry script names (`oms_ec2.py`, etc.) for now to avoid breaking agent docs.
2. **Paths:** Replace `C:\PROD\ConnectorSuite\...` with repo-relative paths and `examples/cursor-mcp.json` using a documented clone root.
3. **Secrets:** Only committed `.env.example` with placeholders; no live instance IDs in examples (use `refresh` workflow in README).
4. **Harness exports:** Replace or trim `exports/` samples that expose org/project structure.

## Open questions

- Rename `oms_*` → generic names (`ec2-ssm`, `sumologic`) for wider audience, or keep OMS branding?
- Include `oms-nuget-aws-setup` under `tooling/` for Aptos devs only?
- License: single MIT at root (rules already MIT); confirm for connector code.

## Artifacts

- Public tree: `C:\Users\akashyap\Downloads\mcp-connector-suite-main\mcp-connector-suite-main\`
- Root `README.md`, `index.html`, `connectors/*`, `scripts/setup.ps1`, sanitized `.env.example` files
