# `oms` monorepo — complete reference

**Repo:** `RepoSuite/oms`  
**Coverage:** **100% file inventory** (build artifacts excluded: `bin/`, `obj/`, `.git/`, `.vs/`).  
**Narrative guides:** [28-functional-oms-monorepo.md](./28-functional-oms-monorepo.md) (behavior), [06](./06-site-manager-shoplogic.md), [12](./12-monorepo-catalog.md), [21](./21-monorepo-folder-index.md).  
**Per-folder function:** [inventories/oms-functional-by-folder.md](./inventories/oms-functional-by-folder.md).

---

## Inventory (100%)

| Artifact | Count | Path |
|----------|------:|------|
| All files (excl. `bin`/`obj`) | **13,553** | [inventories/oms-all-files.txt](./inventories/oms-all-files.txt) |
| `.cs` files | **5,489** | [inventories/oms-cs-files.txt](./inventories/oms-cs-files.txt) |
| `.cs` by top-level folder | — | [inventories/oms-cs-by-top-level.md](./inventories/oms-cs-by-top-level.md) |
| Per-folder totals | **134** roots | [inventories/oms-counts-by-top-level.md](./inventories/oms-counts-by-top-level.md) |
| `.csproj` | **101** | [inventories/oms-csproj-files.txt](./inventories/oms-csproj-files.txt) |
| `.sln` | **26** | [inventories/oms-sln-files.txt](./inventories/oms-sln-files.txt) |
| Top-level directory names | **128** dirs | [inventories/oms-top-level-dirs.txt](./inventories/oms-top-level-dirs.txt) |

### Other high-volume paths (included in `oms-all-files.txt`)

| Path | Count (indicative) |
|------|-------------------:|
| `ShopVisible.Core.ShopLogic` `.aspx` | **422** |
| `SQLChangeScripts/` files | **673** |
| In-repo `docs/` | **1** (+ `oms/docs/*.md` runbooks linked from [16](./16-operations-runbooks.md)) |

---

## Solutions (26 — full list)

See [inventories/oms-sln-files.txt](./inventories/oms-sln-files.txt). Primary entry points:

| Solution | Build target |
|----------|----------------|
| `DCEOM.All.sln` / `Solutions/DCEOM.All.sln` | Broad DCEOM + dependencies |
| `Solutions/ShopVisible.ShopLogic.sln` | **Site Manager** (minisoft image) |
| `Solutions/ShopVisible.JobManager.JobProcessorService.sln` | Task processor (legacy) |
| `Solutions/ShopVisible.JobManager.JobManagerService.sln` | Job manager Windows service |
| `Solutions/ShopVisible.API.sln` | Core API V2 |
| `Solutions/DCEOM.Plugins.sln` | Payment/shipping plugins |
| `DCEOM.WebApi` (project) | **Batch scheduler HTTP proxy** (with ShopLogic deploy) |

---

## Batch migration touchpoints (in this repo)

| Component | Path |
|-----------|------|
| Batch Job Manager React UI | `Shopvisible.Core.Shoplogic.BatchJobManager.Frontend.React` |
| Scheduler proxy API | `DCEOM.WebApi` → `BatchSchedulerProxyController.cs` |
| Toronado / export metadata | `DCEOM.Toronado.*`, `ShopVisible.JobManager.*` |
| SQL baselines | `SQLChangeScripts/` |
| ODX monitor runbook | `docs/odx-feed-pipeline-monitor-runbook.md` |

Runtime Batch workers and scheduler API are **`oms-aws-service-manager-batch`** and **`oms-aws-job-scheduler`** — see [22](./22-batch-repo-complete-reference.md) and [23](./23-job-scheduler-complete-reference.md).

---

## Largest code folders (by `.cs` count)

From [inventories/oms-counts-by-top-level.md](./inventories/oms-counts-by-top-level.md):

| Folder | `.cs` | Role |
|--------|------:|------|
| `DCEOM.Models` | 875 | Domain / DB models |
| `DCEOM.Interfaces` | 529 | Contracts |
| `DCEOM.DataAccess` | 527 | Data access |
| `DCEOM.Services` | 431 | Business services |
| `ShopVisible.Core.ShopLogic` | 385 | Admin WebForms + `backadmin/` (3,755 files total — `.aspx`, assets) |

Use the counts table for **every** top-level folder (134 rows).

---

## Deploy mapping (what still builds from `oms`)

| AWS surface | Monorepo source | Infra stack |
|-------------|-----------------|-------------|
| Site Manager | `ShopVisible.Core.ShopLogic` | `04-minisoft` |
| Web API / BJM proxy | `DCEOM.WebApi` | bundled in minisoft / related deploy |
| Task scheduler/processor images | JobManager solutions | `06-taskscheduler`, `09-taskprocessor` (images often **separate ECR** — [09](./09-facades-core-edge.md)) |
| Facade APIs | Partial shared libs only | `eom-service-order-facade` etc. — **other Bitbucket repos** |

---

## Extension mix (top types)

Included at bottom of [inventories/oms-counts-by-top-level.md](./inventories/oms-counts-by-top-level.md): `.cs`, `.sql`, `.aspx`, `.js`, `.json`, `.config`, etc.

---

## Related

- [04-deep-repo-scan.md](./04-deep-repo-scan.md) — how monorepo connects to Batch repos  
- [13-deployables-catalog.md](./13-deployables-catalog.md) — four/five-repo deploy map  
- [COVERAGE.md](./COVERAGE.md) — per-repo **100%** inventory row for `oms`
