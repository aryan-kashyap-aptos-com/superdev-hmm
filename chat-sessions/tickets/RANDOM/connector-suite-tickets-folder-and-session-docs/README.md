# ConnectorSuite tickets layout and session docs

**Last updated:** 2026-09-19  
**Status:** done

## Intent

Central `tickets/` folder for Jira workspaces and Cursor chat trails, with a flat folder structure (no date subdirectories).

## Decisions

- Moved `DCOMS-*` ticket workspaces from repo root into `tickets/`.
- Session history lives in **`CHAT-LOG.md`** per folder; dates are section headers, not folders.
- Cursor rule: `.cursor/rules/connector-suite-ticket-chat-sessions.mdc` (`alwaysApply: true`).

## Artifacts

| Item | Path |
|------|------|
| Tickets index | `tickets/README.md` |
| Cursor rule | `.cursor/rules/connector-suite-ticket-chat-sessions.mdc` |
| DCOMS-29203 workspace | `tickets/DCOMS-29203-odx-feed-pipeline-monitor/` |
| DCOMS-29691 workspace | `tickets/DCOMS-29691-pod2dev-ec2-shutdown-restart-validation/` |

## Open questions

- Whether `shared-mq-pilot-pod-omnipod` should move under `tickets/`.
