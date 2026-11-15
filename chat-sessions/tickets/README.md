# Ticket workspaces

Real work product for a Jira ticket: specs, data models, queries, runbooks, test results. **Not** chat notes —
those stay in the dated session files one level up (`chat-sessions/*.md`), which point here for detail.

Flat folders only, named after the Jira ID: `tickets/DCOMS-29203/`, not nested by date.

## How a folder gets here

`chat-sessions/save-session.py start "<topic>" --goal "..." --ticket DCOMS-29203` creates
`tickets/DCOMS-29203/` automatically the first time that ticket is used. Put whatever the ticket actually
produced inside it — there's no fixed shape, use whatever files the work calls for (a spec, a SQL file, a
`runbook/`, `test-results/`, screenshots, a mock UI).

## Work with no ticket

Exploration, internal tooling, and other work not tied to a Jira ID has no folder here — it's just a session
file with `Ticket: (none)`. Don't invent a ticket ID to force it into this folder.

## See also

- `../EXAMPLE.md` — a full worked example, ticket-tied, pointing at `EXAMPLE-000/` below.
- `EXAMPLE-000/` — the dummy workspace that example session points to.
