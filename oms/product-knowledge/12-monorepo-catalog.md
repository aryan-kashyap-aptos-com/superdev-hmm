# `RepoSuite/oms` monorepo catalog (for newcomers)

**Audience:** Developers lost in 133 top-level folders.  
**Path:** `/Users/akashyap/RepoSuite/oms`  
**100% file inventory:** [26-oms-monorepo-complete-reference.md](./26-oms-monorepo-complete-reference.md) (13,553 files, 5,489 `.cs`).  
**Not deployable as one unit on AWS** — pieces feed **minisoft**, **JobManager Windows services**, and **ShopLogic**; many ECS images come from **other repos**.

---

## How to build (entry points)

| Solution | Use when |
|----------|----------|
| `DCEOM.All.sln` | Large full build (Site Manager + DCEOM stack) |
| `Solutions/ShopVisible.ShopLogic.sln` | Admin site only |
| `Solutions/ShopVisible.JobManager.JobProcessorService.sln` | Task processor |
| `Solutions/ShopVisible.JobManager.JobManagerService.sln` | Job manager service |
| `Solutions/ShopVisible.API.sln` | Legacy API layer |

Jenkins scripts: `Jenkins Build Scripts/` (Windows build agents, NuGet, `GlobalAssemblyInfo` versioning).

---

## Families (every top-level folder grouped)

### Site Manager & admin UI (domain A)

| Folder | Role |
|--------|------|
| `ShopVisible.Core.ShopLogic` | **Main admin site** — `backadmin/` |
| `ShopVisible.Core.ShopLogic.AppCode` | App_code |
| `ShopVisible.Core.Shoplogic.Frontend` / `Shopvisible.Core.Shoplogic.Frontend.React` | Modern JS bundles |
| `Shopvisible.Core.Shoplogic.BatchJobManager.Frontend.React` | Batch Job Manager UI |
| `DCEOM.Backadmin.UI` | Backadmin UI library |
| `DCEOM.BackAdmin.Application.Controllers` | Admin controllers |
| `ShopVisible.iZenda` | Reporting integration |

### APIs & services (domain B)

| Folder | Role |
|--------|------|
| `EOM.ShopLogicApi` | ShopLogic API |
| `EOM.ShopLogicServices` / `.CodeBehind` | Service implementation |
| `DCEOM.WebApi` | Web API (**Batch scheduler proxy**) |
| `EOM.Api` | Additional API surface |
| `ShopVisible.API` | Core services V2 |

### DCEOM core (orders, products, plugins)

| Folder | Role |
|--------|------|
| `DCEOM.Services` | Business services |
| `DCEOM.Product.Application` / `.ApplicationVB` | Product domain |
| `DCEOM.Models` / `DCEOM.Interfaces` | Shared types |
| `DCEOM.Plugins` | Payment/shipping plugins (WorldPay, Adyen, …) |
| `DCEOM.WebControls` | UI controls |
| `DCEOM.HealthCheck` | Health endpoints |

### Data access (domain L)

| Folder | Role |
|--------|------|
| `DCEOM.DataAccess` / `.Interfaces` | DB access |
| `DCEOM.Toronado.DataAccess` | Scheduler/Toronado tables |
| `DCEOM.Toronado.Services` / `.Infrastructure` | Toronado logic |
| `ShopVisible.Core.DataLayer` | Legacy data layer |
| `ShopVisible.Core.DataObjects.V2` / `.BusinessEntity.V2` | DTOs/entities |

### Job engine & tasks (domain G)

| Folder | Role |
|--------|------|
| `ShopVisible.JobManager.JobManager` | Job manager core |
| `ShopVisible.JobManager.JobManagerService` | Windows service host |
| `ShopVisible.JobManager.JobProcessorService` | Processor service |
| `ShopVisible.JobManager.PostOfficeService` | Post office / messaging |
| `ShopVisible.JobManager.Common` / `.ConfigurationSections` | Shared config |
| `ShopVisible.Core.Scheduler` | Scheduler library |
| `ShopVisible.Core.Tasks` | Task implementations |

### Feeds, import/export (domain H)

| Folder | Role |
|--------|------|
| `ShopVisible.Core.ExportClasses` | Exports (**Batch inventory lineage**) |
| `ShopVisible.Core.ImportClasses` | Imports |
| `ShopVisible.Core.FeedClasses` | Feed utilities |
| `ShopVisible.Feeds.Amazon` | Amazon feeds |
| `Shopvisible.Core.AmazonS3` | S3 helpers |

### Integration & EDI

| Folder | Role |
|--------|------|
| `ShopVisible.Services.Amazon` / `.AmazonCommunciation` | Amazon integrations |
| `ShopVisible.Services.Shipping` | Shipping |
| `Shopvisible.Core.X12Builders` / `.X12Parsers` | X12 EDI |
| `MarketplaceWebService` | Marketplace APIs |
| `ShopVisible.WellsFargo` | Wells Fargo scheduling |

### Configuration & shell

| Folder | Role |
|--------|------|
| `OMS.Configuration` | OMS configuration |
| `ShopVisible.Core.Shell` | Bootstrap/DI (**registers BatchSchedulerProxy**) |
| `ShopVisible.Core.HelperClasses` | Shared helpers |
| `ShopVisible.Core.ContentManager` | Content |
| `ShopVisible.Core.SerializationClasses` | Serialization |

### Auth

| Folder | Role |
|--------|------|
| `EOM.Component.Authentication` | Auth components |

### Database & ops scripts

| Folder | Role |
|--------|------|
| `SQLChangeScripts/` | **Versioned DB changes** (nav, infra settings) |
| `DBMigrationScript/` | Migration tooling |
| `DevScripts/` | Dev utilities |

### Docs in repo

| File | Topic |
|------|--------|
| `docs/odx-feed-pipeline-monitor-runbook.md` | ODX feed queue monitoring (legacy pipeline) |

### Build / meta / test (usually skip unless you own CI)

Folders ending in `.UnitTests`, `.IntgTests`, `SolutionUnitTests`, `ExternalAssemblies`, `Support`, `Utilities`, `Validation`, `nuget`, `version`, `package.json`, `*Build.proj`.

---

## What is **not** in this monorepo (but couples to it)

| Deliverable | Repository (per team runbook) |
|-------------|-------------------------------|
| Scheduler API container | **`oms-aws-job-scheduler`** |
| Batch worker images | **`oms-aws-service-manager-batch`** |
| AWS Terraform | **`oms-infrastructure`** |
| Order/inventory **facade** images | Separate service repos (image via Harness only) |

See [13-deployables-catalog.md](./13-deployables-catalog.md).

---

## SQL scripts newcomers touch

| Script area | Example |
|-------------|---------|
| Batch Job Manager nav | `SQLChangeScripts/2026.5/Insert_BatchJobManager_to_ResourcesAndRolesVsResources.sql` |
| Scheduler URL setting | `Insert_APIGatewayBatchSchedulerURL_InfrastructureSetting.sql` |

---

## Related

- [28-functional-oms-monorepo.md](./28-functional-oms-monorepo.md) — **functional** depth by domain  
- [inventories/oms-functional-by-folder.md](./inventories/oms-functional-by-folder.md) — **133** folder roles  
- [06-site-manager-shoplogic.md](./06-site-manager-shoplogic.md)  
- [08-task-engine-feeds.md](./08-task-engine-feeds.md)  
- [13-deployables-catalog.md](./13-deployables-catalog.md)  
