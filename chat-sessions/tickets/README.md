# Ticket workspaces

Real work product for a Jira ticket: specs, data models, queries, runbooks, test results. **Not** chat notes —
those stay in the dated session files one level up (`chat-sessions/*.md`), which point here for detail.

Flat folders only, named after the Jira ID: `tickets/DCOMS-29203-.../`, not nested by date.

## Current workspaces

| Folder | Jira | Summary |
|--------|------|---------|
| [DCOMS-29203-odx-feed-pipeline-monitor](./DCOMS-29203-odx-feed-pipeline-monitor/) | [DCOMS-29203](https://aptos.atlassian.net/browse/DCOMS-29203) | ODX feed pipeline monitoring |
| [DCOMS-29625-shipfrom-phone-canonical](./DCOMS-29625-shipfrom-phone-canonical/) | [DCOMS-29625](https://aptos.atlassian.net/browse/DCOMS-29625) | Ship-from phone canonicalization |
| [DCOMS-29691-pod2dev-ec2-shutdown-restart-validation](./DCOMS-29691-pod2dev-ec2-shutdown-restart-validation/) | [DCOMS-29691](https://aptos.atlassian.net/browse/DCOMS-29691) | pod2-dev EC2 shutdown/restart validation |

## RANDOM (non-ticket work, kept for reference)

| Folder | Summary |
|--------|---------|
| [RANDOM/connector-suite-tickets-folder-and-session-docs](./RANDOM/connector-suite-tickets-folder-and-session-docs/) | Tickets folder layout and session-doc conventions (predates this unified version) |
| [RANDOM/ecom-order-facade-tax-rate](./RANDOM/ecom-order-facade-tax-rate/) | Order facade tax rate investigation |
| [RANDOM/mcp-connector-suite-public-repo](./RANDOM/mcp-connector-suite-public-repo/) | MCP / public repo notes |
| [RANDOM/name-tag-runs](./RANDOM/name-tag-runs/) | Name-tag audit script and run outputs |
| [RANDOM/oms-engine-gui](./RANDOM/oms-engine-gui/) | OMS engine GUI notes |
| [RANDOM/oms-harness-connector-and-odx-ci](./RANDOM/oms-harness-connector-and-odx-ci/) | Harness MCP connector, pipeline analysis, ODX CI context |

## How a folder gets here

`chat-sessions/save-session.py start "<topic>" --goal "..." --ticket DCOMS-29203` creates a new workspace here
automatically. Put whatever the ticket actually produced inside it — there's no fixed shape, use whatever files
the work calls for (a spec, a SQL file, a `runbook/`, `test-results/`, screenshots, a mock UI).

**`CHAT-LOG.md` files inside existing workspaces are from the old ConnectorSuite convention and are now
superseded** — chat continuity lives in the dated session files one level up (`chat-sessions/*.md`), not inside
the ticket folder. Leave the old `CHAT-LOG.md` files as historical record; don't add new ones.

## Work with no ticket

Omit `--ticket` and `save-session.py` auto-assigns an `SD-NNNN` id and creates its workspace here the same way —
nobody has to invent an ID by hand or leave work untracked. `RANDOM/` above predates this and is kept only for
its historical content; new non-ticket work gets its own `SD-NNNN/` folder instead of going into `RANDOM/`.

## See also

- `../EXAMPLE.md` — a full worked example, ticket-tied, pointing at `EXAMPLE-000/` below.
- `EXAMPLE-000/` — the dummy workspace that example session points to.
