# Functional guide — `RepoSuite/oms` monorepo

**Audience:** Developers changing Site Manager, tasks, exports, or the Batch Job Manager integration.  
**Inventory (paths):** [26-oms-monorepo-complete-reference.md](./26-oms-monorepo-complete-reference.md).  
**Every folder’s role:** [inventories/oms-functional-by-folder.md](./inventories/oms-functional-by-folder.md) (**133** rows).

---

## Runtime architecture (logical)

```text
Operator / integrator
        │
        ▼
ShopVisible.Core.ShopLogic  (/backadmin/*.aspx)
        │ server-side calls
        ├──► DCEOM.Services ──► DCEOM.DataAccess ──► PostgreSQL (OMS)
        ├──► EOM.ShopLogicApi / EOM.ShopLogicServices
        └──► DCEOM.WebApi (JSON, Batch proxy)
                    │
                    └──► oms-aws-job-scheduler (external repo)

Background (legacy): JobManager services / ECS taskprocessor
Background (target): AWS Batch containers (external repo)
```

---

## Domain A — Site Manager & admin UI

| Capability | Where it lives | Behavior |
|------------|----------------|----------|
| Login, roles, navigation | `ShopVisible.Core.ShopLogic` | WebForms pages; resource/role tables in OMS DB |
| Release / version display | ShopLogic + `SQLChangeScripts` | Nav entries and version metadata per release train |
| Modern React panels | `Shopvisible.Core.Shoplogic.Frontend.React` | Bundled into admin; build via front-end toolchain |
| **Batch Job Manager SPA** | `Shopvisible.Core.Shoplogic.BatchJobManager.Frontend.React` | Manages scheduler catalog via proxy only |
| BJM host page | `backadmin/BatchJobManager.aspx` | Checks `ServiceManagerModernizationGuard` before load |
| Reporting embed | `ShopVisible.iZenda` | iZenda integration |

Deep dive: [06-site-manager-shoplogic.md](./06-site-manager-shoplogic.md).

---

## Domain B — APIs & Batch proxy

| Component | Function |
|-----------|----------|
| `DCEOM.WebApi` | ASP.NET Web API; **`BatchSchedulerProxyController`** catch-all `api/v1/{*path}` forwards to scheduler base URL |
| `DCEOM.Services.BatchScheduler` | `BatchSchedulerProxyService`, `BatchSchedulerClientSettingsProvider` — HTTP client, auth headers |
| `ShopVisible.Core.Shell` / `Bootstrapper` | Unity DI registration for proxy + settings |
| `EOM.ShopLogicApi` | ShopLogic-oriented HTTP API |
| `ShopVisible.API` | Core services V2 surface |

**Modernization guard:** `ServiceManagerModernizationGuard.Evaluate` reads OMS configuration; when false, BJM and proxy deny **all** verbs (security: config-driven, not role-driven).

---

## Domain C — Business core (DCEOM)

| Layer | Responsibility |
|-------|----------------|
| `DCEOM.Models` | Entities: orders, items, products, suppliers, affiliates |
| `DCEOM.Interfaces` | Service/repository contracts |
| `DCEOM.Services` | Order actions, inventory, pricing hooks — **what Batch EomAdapters call** for TASK jobs |
| `DCEOM.Product.Application` | Product/catalog application rules |
| `DCEOM.Plugins` | Payment (Adyen, WorldPay, …), shipping integrations |
| `DCEOM.WebControls` | Reusable admin controls |

Changing cancel/update/reroute **business rules** for Batch often requires **EOM NuGet + adapter** in `oms-aws-service-manager-batch`, not only Batch repo code.

---

## Domain G/H — Tasks, Toronado, feeds

| Component | Function |
|-----------|----------|
| `DCEOM.Toronado.Services` / `.DataAccess` | Job steps, export definitions, scheduling metadata |
| `ShopVisible.Core.ExportClasses` | Pre-Batch export pipeline (supplier resolution, messages) |
| `ShopVisible.Core.Tasks` | Task handler implementations (ODX lineage) |
| `ShopVisible.JobManager.*` | Poll DB queue, run tasks on worker (Windows or ECS image) |
| `ShopVisible.Core.FeedClasses` / `Feeds.Amazon` | Marketplace feed helpers |

**Toronado `jobstep.lastsynced`:** still updated by **Inventory Feed Batch** on success ([29-functional-batch-jobs.md](./29-functional-batch-jobs.md)).

Legacy monitor: `docs/odx-feed-pipeline-monitor-runbook.md` → [16](./16-operations-runbooks.md).

---

## Domain L — Data & SQL

| Artifact | Function |
|----------|----------|
| `DCEOM.DataAccess` | Primary PostgreSQL access for .NET stack |
| `ShopVisible.Core.DataLayer` / `DataObjects.V2` | Legacy V2 data layer (still referenced) |
| `SQLChangeScripts/` | **Release SQL** — new nav links, `infrastructure_setting`, feature flags |
| `DBMigrationScript/` | Tooling for DB migrations |

**BJM enablement SQL (examples):**

- Insert Batch Job Manager into resources/roles  
- `Insert_APIGatewayBatchSchedulerURL_InfrastructureSetting.sql` — points ShopLogic at scheduler URL  

Always ship SQL with the **same release** as ShopLogic/BJM UI changes.

---

## Domain O — Configuration

| Piece | Function |
|-------|----------|
| `OMS.Configuration` | Typed access to DB configuration |
| `InfrastructureSetting` enums | Keys like scheduler API URL, feature toggles |
| Harness / Terraform | Writes overlapping values to **SSM**; SM often reads **DB** copy |

---

## Integrations (when you touch them)

| Area | Folders | Typical work |
|------|---------|----------------|
| Amazon | `ShopVisible.Services.Amazon*`, `Feeds.Amazon` | Listing, feeds |
| Shipping | `ShopVisible.Services.Shipping`, `ShippingUtilities` | Rates, labels |
| EDI X12 | `Shopvisible.Core.X12*` | B2B documents |
| Wells Fargo | `ShopVisible.WellsFargo` | Scheduled bank flows |

---

## What is **not** implemented in `oms`

| Capability | Repo |
|------------|------|
| Scheduler API process | `oms-aws-job-scheduler` |
| Batch worker hosts | `oms-aws-service-manager-batch` |
| AWS resources | `oms-infrastructure` |
| Order/inventory **facade** HTTP services | Separate service repos (ECR names in [09](./09-facades-core-edge.md)) |

---

## Build & solutions (functional)

| Solution | When to build |
|----------|----------------|
| `Solutions/ShopVisible.ShopLogic.sln` | Site Manager image (**minisoft**) |
| `DCEOM.All.sln` | Broad regression |
| `Solutions/ShopVisible.JobManager.JobProcessorService.sln` | Task processor ECS image lineage |
| `DCEOM.WebApi` project | Included in SM deploy; proxy changes |

---

## Related

- [27-functional-cross-repo-flows.md](./27-functional-cross-repo-flows.md)  
- [08-task-engine-feeds.md](./08-task-engine-feeds.md)  
- [12-monorepo-catalog.md](./12-monorepo-catalog.md)  
- [FUNCTIONAL-COVERAGE.md](./FUNCTIONAL-COVERAGE.md)
