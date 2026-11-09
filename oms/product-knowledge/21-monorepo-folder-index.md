# `RepoSuite/oms` — complete top-level folder index

**Audience:** “What is this folder?” lookup.  
**100% inventory:** [26-oms-monorepo-complete-reference.md](./26-oms-monorepo-complete-reference.md), [inventories/oms-counts-by-top-level.md](./inventories/oms-counts-by-top-level.md).  
**Count:** **128** top-level directories; **134** folder rows with files under them.  
**Grouped narrative:** [12-monorepo-catalog.md](./12-monorepo-catalog.md).

Legend: **T** = tests/support/meta, **●** = primary product code.

---

## A–D

| Folder | Note |
|--------|------|
| AmplifyTokenManager | ● AWS Amplify token helper |
| ApiBuild.proj | T MSBuild |
| DBMigrationScript | ● DB migration tooling |
| DCEOM.All.sln | T Main solution entry |
| DCEOM.BackAdmin.Application.Controllers | ● Admin API controllers |
| DCEOM.BackAdmin.Application.Controllers.UnitTests | T |
| DCEOM.BackAdmin.UI.UnitTests | T |
| DCEOM.Backadmin.UI | ● Backadmin UI library |
| DCEOM.DataAccess | ● Data access |
| DCEOM.DataAccess.Interfaces | ● |
| DCEOM.DataAccess.IntgTests | T |
| DCEOM.DataAccess.UnitTests | T |
| DCEOM.HealthCheck | ● Health checks |
| DCEOM.HealthCheck.UnitTests | T |
| DCEOM.Infrastructure | ● Infra helpers |
| DCEOM.Infrastructure.IngTests | T |
| DCEOM.Infrastructure.Interfaces | ● |
| DCEOM.Infrastructure.UnitTests | T |
| DCEOM.Interfaces | ● |
| DCEOM.Models | ● Domain models |
| DCEOM.Plugins | ● Payment/shipping plugins |
| DCEOM.Plugins.IntgTests | T |
| DCEOM.Plugins.UnitTests | T |
| DCEOM.Product.Application | ● Product domain |
| DCEOM.Product.Application.UnitTests | T |
| DCEOM.Product.ApplicationVB | ● VB product layer |
| DCEOM.Services | ● Business services |
| DCEOM.Services.IntgTests | T |
| DCEOM.Services.UnitTests | T |
| DCEOM.Specflow.Common | T BDD |
| DCEOM.Tests.nunit | T |
| DCEOM.Toronado.DataAccess | ● Toronado DB |
| DCEOM.Toronado.DataAccess.IntgTests | T |
| DCEOM.Toronado.DataAccess.UnitTests | T |
| DCEOM.Toronado.Infrastructure | ● |
| DCEOM.Toronado.Infrastructure.UnitTests | T |
| DCEOM.Toronado.Services | ● Toronado services |
| DCEOM.Toronado.Services.UnitTests | T |
| DCEOM.WebApi | ● Web API (**Batch proxy**) |
| DCEOM.WebApi.UnitTests | T |
| DCEOM.WebControls | ● UI controls |
| DevScripts | T |

---

## E–O

| Folder | Note |
|--------|------|
| EOM.Api | ● API surface |
| EOM.Component.Authentication | ● Auth components |
| EOM.Component.Authentication.UnitTests | T |
| EOM.ShopLogicApi | ● ShopLogic API |
| EOM.ShopLogicApi.IntgTests | T |
| EOM.ShopLogicApi.UnitTests | T |
| EOM.ShopLogicServices | ● ShopLogic services |
| EOM.ShopLogicServices.CodeBehind | ● |
| EOM.ShopLogicServices.CodeBehind.UnitTests | T |
| EOM.Wrappers | ● |
| ExternalAssemblies | T binary deps |
| Jenkins Build Scripts | T CI scripts |
| MarketplaceWebService | ● Marketplace |
| OMS.Configuration | ● Config |
| OMS.Configuration.IntgTest | T |
| OMS.Configuration.UnitTests | T |

---

## S (ShopVisible core)

| Folder | Note |
|--------|------|
| ShopVisible.API | ● Legacy API V2 |
| ShopVisible.API.IntgTests | T |
| ShopVisible.Core.BusinessEntity.V2 | ● |
| ShopVisible.Core.BusinessEntity.V2.IntgTest | T |
| ShopVisible.Core.BusinessEntity.V2.UnitTests | T |
| ShopVisible.Core.ContentManager | ● |
| ShopVisible.Core.ContentManager.UnitTests | T |
| ShopVisible.Core.DataLayer | ● |
| ShopVisible.Core.DataObjects.V2 | ● |
| ShopVisible.Core.DataObjects.V2.IntgTests | T |
| ShopVisible.Core.DataObjects.V2.UnitTests | T |
| ShopVisible.Core.ExportClasses | ● **Exports / Batch lineage** |
| ShopVisible.Core.ExportClasses.IntgTests | T |
| ShopVisible.Core.ExportClasses.Tests | T |
| ShopVisible.Core.FeedClasses | ● Feeds |
| ShopVisible.Core.HelperClasses | ● |
| ShopVisible.Core.HelperClasses.CS | ● |
| ShopVisible.Core.HelperClasses.UnitTests | T |
| ShopVisible.Core.ImportClasses | ● Imports |
| ShopVisible.Core.ImportClasses.IntgTests | T |
| ShopVisible.Core.ImportClasses.UnitTests | T |
| ShopVisible.Core.Scheduler | ● Scheduler lib |
| ShopVisible.Core.SerializationClasses | ● |
| ShopVisible.Core.SerializationClasses.IntgTests | T |
| ShopVisible.Core.SerializationClasses.UnitTests | T |
| ShopVisible.Core.Shell | ● **DI / Bootstrapper** |
| ShopVisible.Core.Shell.UnitTests | T |
| ShopVisible.Core.ShippingUtilities | ● |
| ShopVisible.Core.ShippingUtilities.UnitTests | T |
| ShopVisible.Core.ShopLogic | ● **Site Manager site** |
| ShopVisible.Core.ShopLogic.AppCode | ● |
| ShopVisible.Core.Shoplogic.Frontend | ● |
| ShopVisible.Core.Tasks | ● Tasks |
| ShopVisible.Core.Tasks.IntgTests | T |
| ShopVisible.Core.Tasks.UnitTests | T |
| ShopVisible.Core.Tools.Reporting | ● |
| ShopVisible.Core.Tools.Reporting.UnitTests | T |
| ShopVisible.Feeds.Amazon | ● |
| ShopVisible.Feeds.Amazon.IntgTests | T |
| ShopVisible.JobManager.Common | ● |
| ShopVisible.JobManager.ConfigurationSections | ● |
| ShopVisible.JobManager.JobManager | ● |
| ShopVisible.JobManager.JobManagerService | ● Windows service |
| ShopVisible.JobManager.JobManagerService.IntgTests | T |
| ShopVisible.JobManager.JobProcessorService | ● Processor |
| ShopVisible.JobManager.JobProcessorService.IntgTests | T |
| ShopVisible.JobManager.PostOfficeService | ● |
| ShopVisible.JobManager.Reporting | ● |
| ShopVisible.JobManager.UnitTests | T |
| ShopVisible.Services.Amazon | ● |
| ShopVisible.Services.AmazonCommunciation | ● |
| ShopVisible.Services.Shipping | ● |
| ShopVisible.Services.Shipping.IntgTests | T |
| ShopVisible.WebReferenceWrappers | ● |
| ShopVisible.WebReferenceWrappers.Interfaces | ● |
| ShopVisible.WellsFargo | ● |
| ShopVisible.iZenda | ● Reporting |
| Shopvisible.Core.AmazonS3 | ● S3 |
| Shopvisible.Core.Shoplogic.BatchJobManager.Frontend.React | ● **BJM UI** |
| Shopvisible.Core.Shoplogic.Frontend.React | ● React admin |
| Shopvisible.Core.X12Builders | ● EDI |
| Shopvisible.Core.X12Parsers | ● EDI |

---

## S–Z (meta)

| Folder | Note |
|--------|------|
| SolutionUnitTests | T |
| Solutions | T `.sln` collection |
| SQLChangeScripts | ● **Versioned SQL** |
| Support | T |
| Support.Utilities | T |
| Utilities | T |
| Validation | T |
| WebsiteBuild.proj | T |
| docs | ● Runbooks (`odx-feed-pipeline-monitor-runbook.md`) |
| nuget | T |
| package.json | T |
| README.md | T stub |
| version | T |

---

## Related

- [12-monorepo-catalog.md](./12-monorepo-catalog.md)  
- [COVERAGE.md](./COVERAGE.md)  
