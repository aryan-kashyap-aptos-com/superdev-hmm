# DCOMS-29203 — ODX Feed Pipeline Monitor

Documentation package for epic [DCOMS-29203](https://aptos.atlassian.net/browse/DCOMS-29203): **ODX feed pipeline monitoring — React admin page leveraging odxtasklogging**.

**Created:** 2026-09-10  
**Primary assignee (Story 5 / DCOMS-29423):** Aryan Kashyap  
**Target release:** 2026.7.0

---

## What this folder contains

| Document | Purpose |
|----------|---------|
| [01-epic-and-tickets.md](./01-epic-and-tickets.md) | Epic goals, scope, all linked DCOMS tickets, status snapshot |
| [02-odx-pipeline-technical-reference.md](./02-odx-pipeline-technical-reference.md) | End-to-end ODX feed architecture from OMS + ODX repos |
| [03-data-model-and-fields.md](./03-data-model-and-fields.md) | Every ODX-related table, column, enum, and what it means |
| [04-ticket-dependencies.md](./04-ticket-dependencies.md) | Dependency graph, build order, blockers for DCOMS-29423 |
| [05-ui-implementation-guide-DCOMS-29423.md](./05-ui-implementation-guide-DCOMS-29423.md) | React shell guide mirroring Service Manager / Site Manager |
| [06-monitoring-capabilities-and-hypotheses.md](./06-monitoring-capabilities-and-hypotheses.md) | What the monitor can actually track vs epic hypotheses |
| [07-export-jobs-and-inventory-explained.md](./07-export-jobs-and-inventory-explained.md) | Inventory vs order feeds, export job types |
| [08-read-only-validation-queries.sql](./08-read-only-validation-queries.sql) | Manual read-only SQL for podqa/staging validation |
| [mock-ui/odx-feed-pipeline-monitor-mock.html](./mock-ui/odx-feed-pipeline-monitor-mock.html) | **Interactive HTML mock** — open in browser to preview landing + detail views |

---

## Quick summary

**Problem:** Support teams troubleshoot OMS feed exports by stitching together Toronado job history, Service Manager run counts, CloudWatch logs, and manual SQL against `odxtasklogging` (28M+ rows on podqa). No unified UI exists.

**Solution:** A new Site Manager React page (`ODX feed pipeline`) that reads existing tables via `OdxFeedMonitorController` APIs and collapses append-only `odxtasklogging` events into per-message pipeline timelines.

**Your immediate focus:** [DCOMS-29423](https://aptos.atlassian.net/browse/DCOMS-29423) (Story 5) — React application shell following the Service Manager migration pattern.

---

## Epic attachments (Jira)

The epic has two HTML mockups (not downloadable via API without attachment permission):

- `odx-feed-monitor-mockup.html`
- `odx-feed-pipeline-monitor-mockup (2).html`

Download from the epic attachments tab for visual reference when building Stories 6–7.

---

## Key code locations (OMS repo)

| Area | Path |
|------|------|
| ODX producer | `ShopVisible.Core.ExportClasses/OMSFeedsScheduledProcessing.cs` |
| Task logging (write) | `DCEOM.Services/ODX/OdxTaskLoggingService.cs` |
| Service Manager pattern | `ShopVisible.Core.ShopLogic/backadmin/ServiceManager.aspx` |
| React entry | `Shopvisible.Core.Shoplogic.Frontend.React/src/index.js` |
| React Service Manager | `Shopvisible.Core.Shoplogic.Frontend.React/src/serviceManager/` |
| Site Manager master | `ShopVisible.Core.ShopLogic/backadmin/siteManager.master` |

**Note:** `OdxFeedMonitor*` classes are specified in Stories 2–4 but were **not found in the local `c:\oms` workspace** at documentation time. Jira shows Stories 2–3 as Closed — confirm the implementing branch is merged or available locally before wiring axios in Story 5.
