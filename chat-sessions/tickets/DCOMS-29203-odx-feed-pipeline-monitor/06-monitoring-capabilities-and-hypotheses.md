# Monitoring Capabilities and Hypotheses

Separates **what the monitor will actually support** (backed by data and epic scope) from **hypothetical scenarios** in the epic and attached mockups that need validation or are explicitly out of scope.

---

## Confirmed monitor capabilities (in epic scope)

These are backed by existing tables and specified in Stories 1–11.

### Landing page health checks

| Capability | Data source | Story |
|------------|-------------|-------|
| Summary counts by task × state | `odxtasklogging` GROUP BY | 3, 4, 6 |
| Backlog count (Queued without Done) | `odxtasklogging` anti-join on `messageid` | 3, 4, 6 |
| Stuck order count | `omsfeedsqueuedorder` age > threshold | 3, 4, 6 |
| Recent error list | `odxfeederror` by `createdateutc` | 3, 4, 6 |
| Search by order ID | `odxtasklogging.referenceid` + time window | 2, 4, 6 |
| Search by message ID | `odxtasklogging.messageid` | 2, 4, 6 |
| Search by task name | `odxtasklogging.taskname` filter | 4, 6 |
| Time window selector (24h default, 7d max) | API enforcement | 4, 6 |

### Detail page lifecycle tracking

| Stage | Data source | Story |
|-------|-------------|-------|
| Queued | `odxtasklogging` TaskState=Queued | 7 |
| Started | `odxtasklogging` TaskState=Started | 7 |
| Done / Error | `odxtasklogging` TaskState=Done + Result | 7 |
| Staged | `omsfeedexport` row for order | 7, 8 |
| File written | `omsfeedexportreader` cursor + file output metadata | 7, 8 |
| Consumer error inline | `odxfeederror` linked to message | 7, 9 |
| Stuck in queue panel | `omsfeedsqueuedorder` for order | 9 |

### Pipeline-specific coverage

| Pipeline | Monitor support | Story |
|----------|-----------------|-------|
| Toronado OMS feeds (Fulfillment, OrderCreated, etc.) | Full Queued→Done via `odxtasklogging` | 6, 7 |
| ExportOrderItems / Generate Notifications | 3-stage: staged → cursor → file | 8 |
| Inventory feed | `odxtasklogging` + S3 indicator where metadata exists | 10 |
| Service Manager scheduled tasks | Indirect — via `odxtasklogging` tasknames | 6 |

---

## Hypotheses from the epic — validated against code

### Hypothesis 1: "Each message produces exactly 3 rows (Queued → Started → Done)"

**Partially true.**

- Epic data: 746K messages with exactly 3 rows in last 7 days on podqa
- Also: 164K messages with **only 1 row** (Queued only — consumer never wrote Started/Done, or partial logging paths)
- OMS only writes `Queued`; if consumer fails silently, you see 1-row messages
- DCOMS-27496: orders stuck in `omsfeedsqueuedorder` with no `odxfeederror`

**Monitor behaviour:** Timeline shows partial states. Backlog panel catches Queued-without-Done. This is a core value proposition.

### Hypothesis 2: "`odxtasklogging` alone is sufficient for full pipeline visibility"

**False for complete picture.**

Missing without joins:

| Gap | Supplementary table |
|-----|---------------------|
| Consumer exceptions | `odxfeederror` |
| In-flight lock | `omsfeedsqueuedorder` |
| Export staging | `omsfeedexport` |
| File output progress | `omsfeedexportreader` |
| Inventory S3 output | ODX metadata (may not be in DB) |

Epic correctly designs lazy joins on detail view only.

### Hypothesis 3: "28M rows means we need aggregates, not raw event grids"

**True and enforced.**

- Landing uses `GROUP BY taskname, taskstate` — not `DISTINCT ON (messageid)` over full window
- Mandatory time windows (24h default, 7d max)
- Server-side pagination on search results
- New indexes on `referenceid` + `createdateutc`

### Hypothesis 4: "Monitor replaces CloudWatch"

**False — explicitly out of scope.**

Monitor shows structured status. CloudWatch still needed for:

- Full stack traces
- Consumer internal logic debugging
- Infrastructure issues (ECS task crashes, MQ connectivity)

Story 11 runbook will document when to link out to CloudWatch.

### Hypothesis 5: "Monitor can show live RabbitMQ queue depth"

**False — out of scope.**

Would require new infra integration (RabbitMQ management API). Listed as follow-on in epic. ConnectorSuite MQ pilot runbooks cover manual queue monitoring today.

### Hypothesis 6: "Monitor can show why an order was never queued"

**False — no data exists.**

POS suppression happens **before** `LogQueuedBulk`. Orders filtered at selection time leave no `odxtasklogging` trace. Support must still check Toronado job config and order eligibility SQL.

### Hypothesis 7: "ExportOrderItems 3-stage correlation is always possible"

**Partially true.**

Stages 1–2 (`omsfeedexport`, `omsfeedexportreader`) are DB-correlatable by order ID + time window. Stage 3 (file written) depends on ODX metadata and Toronado job logs — "where correlatable" per Story 8.

### Hypothesis 8: "Inventory S3 stage is always visible"

**Partially true.**

Story 10: "S3 status not available" when ODX metadata lacks file path. No S3 browser in scope.

### Hypothesis 9: "Stuck `omsfeedsqueuedorder` always has a matching `odxfeederror`"

**False — proven in production.**

DCOMS-27496: LLBean orders stuck 11+ hours with **no** `odxfeederror` rows. Daily cleanup script eventually clears queue and produces late JSONs.

**Monitor value:** Surfaces stuck orders even when no error was logged. Does not fix root cause.

### Hypothesis 10: "All feed types use the same `taskname` pattern"

**Mostly true for OMS feeds.**

- OMS: `OMSFeeds:{TransactionType}`
- Inventory: `Inventory feed` or `InventoryFeedScheduler`
- ExportOrderItems: may use different taskname from ODX handler

Story 6 tiles group by actual `taskname` values in data — not hardcoded list.

---

## What tracking the monitor should support (recommended priority)

### P0 — Must have (Stories 1–7)

1. Pipeline health at a glance (tiles + backlog + errors)
2. Order ID search with time window
3. Message lifecycle timeline (Queued → Done)
4. Stuck order visibility
5. Auth + permissions gating

### P1 — Should have (Stories 8–10)

6. ExportOrderItems 3-stage correlation
7. Error detail panels on detail view
8. Inventory feed basic coverage
9. S3 stage indicator (when metadata available)

### P2 — Nice to have (post-epic / follow-on)

10. Live RabbitMQ queue depth
11. Link to CloudWatch log stream for messageid
12. Toronado job run correlation (complement, not replace)
13. Alerting / proactive notification when backlog exceeds threshold
14. Suppression reason visibility (would need new logging)

---

## Additional functionalities beyond current epic

These are **not** in DCOMS-29203 but may be valuable follow-ups:

| Feature | Effort | Value |
|---------|--------|-------|
| Auto-refresh landing page (polling) | Low | Ops convenience |
| Export search results to CSV | Low | Support documentation |
| Configurable stuck-order threshold per site | Medium | Flexibility |
| Datadog/Sumo dashboard integration | Medium | Centralized alerting |
| Write actions (re-queue, clear stuck row) | High + risky | Operational recovery — explicitly read-only today |
| Message body preview (sanitized) | Medium + security review | Deeper debugging |

---

## Support scenario → monitor action map (for Story 11 runbook)

| Support question | Monitor action | Still need CloudWatch/SQL? |
|------------------|----------------|----------------------------|
| Is the feed pipeline healthy right now? | Landing page tiles + backlog | No |
| Why hasn't order X exported? | Search order ID → detail timeline | Maybe — if never queued |
| Is order X stuck in the queue? | Stuck-order panel | No |
| What error occurred for message Y? | Detail page error panel | Yes — for full stack trace |
| Was notification file written for order Z? | ExportOrderItems 3-stage timeline | Maybe — if stage 3 not correlatable |
| Is inventory feed working? | Inventory tile + detail | Maybe — S3 verification |
| How many Fulfillment messages failed today? | Fulfillment tile Error count | No |
| What's in the RabbitMQ queue right now? | **Not supported** | Yes — RabbitMQ UI |

---

## Mockup vs implementation notes

The epic has two HTML mockup attachments (`odx-feed-monitor-mockup.html`, `odx-feed-pipeline-monitor-mockup (2).html`). Download from Jira for pixel reference.

When implementing Story 6, align with:

- Site Manager chrome (from `siteManager.master` — already provided by ASPX host)
- Service Manager grid density and `ag-theme-aptos` styling
- Epic mockup panel layout for tiles and side panels
- Story 6 spec for exact menu placement and permission checkbox

Story 5 (your current work) should **not** try to replicate the full mockup — only the shell, title, and description text.
