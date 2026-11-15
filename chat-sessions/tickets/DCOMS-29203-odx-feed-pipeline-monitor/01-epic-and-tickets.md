# Epic DCOMS-29203 — Overview and Ticket Breakdown

**Epic:** [DCOMS-29203](https://aptos.atlassian.net/browse/DCOMS-29203)  
**Parent initiative:** [DCOMS-28397](https://aptos.atlassian.net/browse/DCOMS-28397) — 2026 ongoing maintenance and discovery  
**Status:** In Progress  
**Fix version:** 2026.7.0  
**Labels:** ODX-Feed-Pipeline-Monitor, OMS, WasteReduction

---

## Business value

Operations and support teams troubleshooting OMS feed exports (OrderCreated, Fulfillment, Inventory, Export Order Items / Generate Notifications) must today stitch together **disconnected signals**:

| Source today | What it shows | Gap |
|--------------|-----------------|-----|
| Toronado job history | Messages published to RabbitMQ | No per-order lifecycle |
| Service Manager run history | Scheduler-level record counts | No ODX consumer state |
| CloudWatch | ODX consumer logs | No structured correlation to orders |
| Manual SQL on `odxtasklogging` | Full event log | 28M+ rows, no UI, no pivot |

`odxtasklogging` is an **append-only event log**: each RabbitMQ `messageid` produces **separate rows** per state (`Queued`, `Started`, `Done`), not a single status row. A successful message typically produces three rows. The data exists but is unusable without time-bounded queries and a UI that collapses events into a pipeline timeline.

**Goal:** Reduce time-to-diagnose feed pipeline issues, eliminate routine CloudWatch/SQL archaeology, and give operators one place to answer: *"Was this order queued, consumed, staged for export, written to file, or stuck?"*

---

## In scope (epic level)

1. **React monitoring page** in Site Manager backadmin (Service Manager migration pattern)
2. **Read APIs** over existing data — no changes to feed processing hot paths
3. **Pipeline coverage:**
   - Toronado scheduled feeds (`OMSFeedsScheduled`, `InventoryFeedScheduler`)
   - Service Manager ExportOrderItems → `omsfeedexport` → `OMSFeedsFileOutput`
   - Inventory feed → S3 XML (correlation where metadata available)
4. **Landing page:** summary tiles, backlog, stuck orders, recent errors, searchable grid
5. **Detail page:** vertical timeline per message/order
6. **Index DDL** for read performance on podqa-scale data

## Out of scope (epic level)

- Changing RabbitMQ topology or ODX consumer ACK behaviour
- Replacing CloudWatch for deep stack traces (link out only)
- Live RabbitMQ queue-depth monitoring
- Toronado job scheduling UI changes
- Writing new rows to `odxtasklogging`
- Inventory S3 file browser
- Unbounded time-range queries

---

## Story breakdown (implementation tickets)

| Story | Ticket | Summary | Status | Assignee |
|-------|--------|---------|--------|----------|
| 1 | [DCOMS-29419](https://aptos.atlassian.net/browse/DCOMS-29419) | Index DDL on `odxtasklogging`, `odxfeederror`, `omsfeedexport` | **Closed** | Aryan Kashyap |
| 2 | [DCOMS-29420](https://aptos.atlassian.net/browse/DCOMS-29420) | `OdxTaskLoggingRepository` read methods + `MessagePipelineStatus` pivot DTO | **Closed** | Sanika A M |
| 3 | [DCOMS-29421](https://aptos.atlassian.net/browse/DCOMS-29421) | `OdxFeedMonitorService` — summary, backlog, stuck orders | **Closed** | Sanika A M |
| 4 | [DCOMS-29422](https://aptos.atlassian.net/browse/DCOMS-29422) | `OdxFeedMonitorController` Web API endpoints | **In Progress** | Sanika A M |
| 5 | [DCOMS-29423](https://aptos.atlassian.net/browse/DCOMS-29423) | React shell — ASPX, index.js, `OdxFeedMonitorApp` | **In Progress** | **Aryan Kashyap** |
| 6 | [DCOMS-29424](https://aptos.atlassian.net/browse/DCOMS-29424) | Landing page — tiles, panels, ag-Grid search | Open | Aryan Kashyap |
| 7 | [DCOMS-29425](https://aptos.atlassian.net/browse/DCOMS-29425) | Detail page — vertical timeline component | To Do | Sabyasachi Sanyal |
| 8 | [DCOMS-29426](https://aptos.atlassian.net/browse/DCOMS-29426) | ExportOrderItems 3-stage correlation | To Do | Sabyasachi Sanyal |
| 9 | [DCOMS-29428](https://aptos.atlassian.net/browse/DCOMS-29428) | `odxfeederror` + `omsfeedsqueuedorder` panels on detail view | To Do | Sabyasachi Sanyal |
| 10 | [DCOMS-29427](https://aptos.atlassian.net/browse/DCOMS-29427) | Inventory feed pipeline path + S3 indicator | To Do | Sabyasachi Sanyal |
| 11 | [DCOMS-29429](https://aptos.atlassian.net/browse/DCOMS-29429) | QA perf validation on podqa + Confluence runbook | To Do | Sabyasachi Sanyal |

---

## Review / process subtasks

| Ticket | Type | Status |
|--------|------|--------|
| [DCOMS-29204](https://aptos.atlassian.net/browse/DCOMS-29204) | Integration Review | Review Not Needed |
| [DCOMS-29205](https://aptos.atlassian.net/browse/DCOMS-29205) | Architecture Review | Review Not Needed |
| [DCOMS-29224](https://aptos.atlassian.net/browse/DCOMS-29224) | QA/BA Epic Test Case Review | Review Needed |
| [DCOMS-29225](https://aptos.atlassian.net/browse/DCOMS-29225) | Deployment Review | Review Not Needed |
| [DCOMS-29554](https://aptos.atlassian.net/browse/DCOMS-29554) | Integration Review (duplicate) | Review Not Needed |
| [DCOMS-29555](https://aptos.atlassian.net/browse/DCOMS-29555) | Architecture Review (duplicate) | Review Needed |

---

## Related external tickets

| Ticket | Relationship |
|--------|--------------|
| [DCOMS-27496](https://aptos.atlassian.net/browse/DCOMS-27496) | Stuck `omsfeedsqueuedorder` rows with no `odxfeederror` — monitor surfaces this via stuck-order panel |
| [NETMIS-22261](https://aptos.atlassian.net/browse/NETMIS-22261) | Referenced in DCOMS-27496 — NetOps CloudWatch review |

---

## Performance targets (podqa-validated)

| Endpoint / query | Target |
|------------------|--------|
| Summary / backlog APIs | < 2 seconds |
| Message timeline by `messageid` | < 200 ms |
| Order search by `referenceid` | < 2 seconds (requires Story 1 index) |
| Mandatory time window | Default 24h, max 7d — **no unbounded queries** |

### podqa scale reference (Jul 2026, from epic)

| Table | Row count |
|-------|-----------|
| `odxtasklogging` | 28.3M |
| `odxfeederror` | 4.1M |
| `omsfeedexport` | 223K |
| `omsfeedsqueuedorder` | 205 (203 > 1 day old) |

Typical message pattern: 746K messages with exactly 3 rows in last 7 days; 164K with 1 row only (partial logging paths).

---

## Who writes `odxtasklogging` rows

| Component | TaskState written |
|-----------|-------------------|
| OMS `OMSFeedsScheduledProcessing` | `Queued` |
| OMS `InventoryFeedScheduledProcessing` | `Queued` |
| ODX `ExportOrderItemsTaskHandler` | `Queued` (per order published) |
| ODX `omsfeedsupervisor` / `inventoryfeedsupervisor` | `Started`, `Done` (or `Error` result) |

OMS repo only writes `Queued`. Full lifecycle visibility requires consumer-side rows (ODX services).

---

## Epic references (from Jira description)

- `oms/docs/react-migration-example.md` — **not found in local repo**; use `ServiceManager.aspx` as reference
- `odx/docs/oms-feeds-export-order-items-record-count-support.md`
- `oms/docs/cross-repo-oms-odx-scheduler-payment.md`
- `oms/docs/inventory-feed-export-pipeline.md`
- Code: `OdxTaskLoggingService.cs`, `OMSTaskLoggingService.cs` (ODX), `OMSFeedsScheduledProcessing.cs`, `ExportOrderItemsTaskHandler.cs`

---

## Epic attachments

Two HTML mockups attached to the epic for UI design reference. See README for filenames.
