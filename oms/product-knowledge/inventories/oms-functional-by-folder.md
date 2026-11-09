# OMS monorepo — functional role by top-level folder

**Folders:** 133

Paired with [28-functional-oms-monorepo.md](../28-functional-oms-monorepo.md).

| Folder | Functional role |
|--------|-----------------|
| `AmplifyTokenManager` | AWS Amplify token helper |
| `ApiBuild.proj` | MSBuild |
| `DBMigrationScript` | DB migration tooling |
| `DCEOM.All.sln` | Main solution entry |
| `DCEOM.BackAdmin.Application.Controllers` | Admin API controllers |
| `DCEOM.BackAdmin.Application.Controllers.UnitTests` | Supporting code; trace usage from solution references. |
| `DCEOM.Backadmin.UI` | Backadmin UI library |
| `DCEOM.BackAdmin.UI.UnitTests` | Supporting code; trace usage from solution references. |
| `DCEOM.DataAccess` | Executes SQL/ORM against OMS PostgreSQL; shared repositories used by services and batch adapters. |
| `DCEOM.DataAccess.Interfaces` | Supporting code; trace usage from solution references. |
| `DCEOM.DataAccess.IntgTests` | Supporting code; trace usage from solution references. |
| `DCEOM.DataAccess.UnitTests` | Supporting code; trace usage from solution references. |
| `DCEOM.HealthCheck` | Health checks |
| `DCEOM.HealthCheck.UnitTests` | Supporting code; trace usage from solution references. |
| `DCEOM.Infrastructure` | Infra helpers |
| `DCEOM.Infrastructure.IngTests` | Supporting code; trace usage from solution references. |
| `DCEOM.Infrastructure.Interfaces` | Supporting code; trace usage from solution references. |
| `DCEOM.Infrastructure.UnitTests` | Supporting code; trace usage from solution references. |
| `DCEOM.Interfaces` | Supporting code; trace usage from solution references. |
| `DCEOM.Models` | Persistent and DTO types for orders, products, suppliers, configuration. |
| `DCEOM.Plugins` | Payment/shipping plugins |
| `DCEOM.Plugins.IntgTests` | Supporting code; trace usage from solution references. |
| `DCEOM.Plugins.UnitTests` | Supporting code; trace usage from solution references. |
| `DCEOM.Product.Application` | Product domain |
| `DCEOM.Product.Application.UnitTests` | Supporting code; trace usage from solution references. |
| `DCEOM.Product.ApplicationVB` | VB product layer |
| `DCEOM.Services` | Core business operations on orders, items, inventory, affiliates—called from ShopLogic pages and APIs. |
| `DCEOM.Services.IntgTests` | Supporting code; trace usage from solution references. |
| `DCEOM.Services.UnitTests` | Supporting code; trace usage from solution references. |
| `DCEOM.Specflow.Common` | BDD |
| `DCEOM.Tests.nunit` | Supporting code; trace usage from solution references. |
| `DCEOM.Toronado.DataAccess` | oronado DB |
| `DCEOM.Toronado.DataAccess.IntgTests` | Supporting code; trace usage from solution references. |
| `DCEOM.Toronado.DataAccess.UnitTests` | Supporting code; trace usage from solution references. |
| `DCEOM.Toronado.Infrastructure` | Supporting code; trace usage from solution references. |
| `DCEOM.Toronado.Infrastructure.UnitTests` | Supporting code; trace usage from solution references. |
| `DCEOM.Toronado.Services` | Reads/writes Toronado job steps, export XML, lastsynced metadata in OMS DB. |
| `DCEOM.Toronado.Services.UnitTests` | Supporting code; trace usage from solution references. |
| `DCEOM.WebApi` | HTTP API including BatchSchedulerProxyController—only supported path from ShopLogic to new scheduler platform. |
| `DCEOM.WebApi.UnitTests` | Supporting code; trace usage from solution references. |
| `DCEOM.WebControls` | UI controls |
| `DevScripts` | Supporting code; trace usage from solution references. |
| `docs` | Runbooks (`odx-feed-pipeline-monitor-runbook.md`) |
| `EOM.Api` | API surface |
| `EOM.Component.Authentication` | Auth components |
| `EOM.Component.Authentication.UnitTests` | Supporting code; trace usage from solution references. |
| `EOM.ShopLogicApi` | ShopLogic API |
| `EOM.ShopLogicApi.IntgTests` | Supporting code; trace usage from solution references. |
| `EOM.ShopLogicApi.UnitTests` | Supporting code; trace usage from solution references. |
| `EOM.ShopLogicServices` | ShopLogic services |
| `EOM.ShopLogicServices.CodeBehind` | Supporting code; trace usage from solution references. |
| `EOM.ShopLogicServices.CodeBehind.UnitTests` | Supporting code; trace usage from solution references. |
| `EOM.Wrappers` | Supporting code; trace usage from solution references. |
| `ExternalAssemblies` | binary deps |
| `Jenkins Build Scripts` | CI scripts |
| `MarketplaceWebService` | Marketplace |
| `nuget` | Supporting code; trace usage from solution references. |
| `OMS.Configuration` | Reads infrastructure_setting / app configuration keys from OMS DB. |
| `OMS.Configuration.IntgTest` | Supporting code; trace usage from solution references. |
| `OMS.Configuration.UnitTests` | Supporting code; trace usage from solution references. |
| `package.json` | Supporting code; trace usage from solution references. |
| `README.md` | stub |
| `ShopVisible.API` | Legacy API V2 |
| `ShopVisible.API.IntgTests` | Supporting code; trace usage from solution references. |
| `Shopvisible.Core.AmazonS3` | S3 |
| `ShopVisible.Core.BusinessEntity.V2` | Supporting code; trace usage from solution references. |
| `ShopVisible.Core.BusinessEntity.V2.IntgTest` | Supporting code; trace usage from solution references. |
| `ShopVisible.Core.BusinessEntity.V2.UnitTests` | Supporting code; trace usage from solution references. |
| `ShopVisible.Core.ContentManager` | Supporting code; trace usage from solution references. |
| `ShopVisible.Core.ContentManager.UnitTests` | Supporting code; trace usage from solution references. |
| `ShopVisible.Core.DataLayer` | Supporting code; trace usage from solution references. |
| `ShopVisible.Core.DataObjects.V2` | Supporting code; trace usage from solution references. |
| `ShopVisible.Core.DataObjects.V2.IntgTests` | Supporting code; trace usage from solution references. |
| `ShopVisible.Core.DataObjects.V2.UnitTests` | Supporting code; trace usage from solution references. |
| `ShopVisible.Core.ExportClasses` | Legacy export orchestration (Toronado steps, supplier resolution); lineage for Inventory Feed Batch. |
| `ShopVisible.Core.ExportClasses.IntgTests` | Supporting code; trace usage from solution references. |
| `ShopVisible.Core.ExportClasses.Tests` | Supporting code; trace usage from solution references. |
| `ShopVisible.Core.FeedClasses` | Feeds |
| `ShopVisible.Core.HelperClasses` | Supporting code; trace usage from solution references. |
| `ShopVisible.Core.HelperClasses.CS` | Supporting code; trace usage from solution references. |
| `ShopVisible.Core.HelperClasses.UnitTests` | Supporting code; trace usage from solution references. |
| `ShopVisible.Core.ImportClasses` | Imports |
| `ShopVisible.Core.ImportClasses.IntgTests` | Supporting code; trace usage from solution references. |
| `ShopVisible.Core.ImportClasses.UnitTests` | Supporting code; trace usage from solution references. |
| `ShopVisible.Core.Scheduler` | Scheduler lib |
| `ShopVisible.Core.SerializationClasses` | Supporting code; trace usage from solution references. |
| `ShopVisible.Core.SerializationClasses.IntgTests` | Supporting code; trace usage from solution references. |
| `ShopVisible.Core.SerializationClasses.UnitTests` | Supporting code; trace usage from solution references. |
| `ShopVisible.Core.Shell` | Unity DI bootstrapper; registers BatchSchedulerProxyService and modernization guard dependencies. |
| `ShopVisible.Core.Shell.UnitTests` | Supporting code; trace usage from solution references. |
| `ShopVisible.Core.ShippingUtilities` | Supporting code; trace usage from solution references. |
| `ShopVisible.Core.ShippingUtilities.UnitTests` | Supporting code; trace usage from solution references. |
| `ShopVisible.Core.ShopLogic` | ASP.NET WebForms Site Manager UI under /backadmin; operator workflows, release management, BJM page host. |
| `ShopVisible.Core.ShopLogic.AppCode` | Supporting code; trace usage from solution references. |
| `Shopvisible.Core.Shoplogic.BatchJobManager.Frontend.React` | SPA for AWS Batch Job Manager; calls DCEOM.WebApi proxy → scheduler API. |
| `ShopVisible.Core.Shoplogic.Frontend` | Supporting code; trace usage from solution references. |
| `Shopvisible.Core.Shoplogic.Frontend.React` | React admin |
| `ShopVisible.Core.Tasks` | asks |
| `ShopVisible.Core.Tasks.IntgTests` | Supporting code; trace usage from solution references. |
| `ShopVisible.Core.Tasks.UnitTests` | Supporting code; trace usage from solution references. |
| `ShopVisible.Core.Tools.Reporting` | Supporting code; trace usage from solution references. |
| `ShopVisible.Core.Tools.Reporting.UnitTests` | Supporting code; trace usage from solution references. |
| `Shopvisible.Core.X12Builders` | EDI |
| `Shopvisible.Core.X12Parsers` | EDI |
| `ShopVisible.Feeds.Amazon` | Supporting code; trace usage from solution references. |
| `ShopVisible.Feeds.Amazon.IntgTests` | Supporting code; trace usage from solution references. |
| `ShopVisible.iZenda` | Reporting |
| `ShopVisible.JobManager.Common` | Supporting code; trace usage from solution references. |
| `ShopVisible.JobManager.ConfigurationSections` | Supporting code; trace usage from solution references. |
| `ShopVisible.JobManager.JobManager` | Supporting code; trace usage from solution references. |
| `ShopVisible.JobManager.JobManagerService` | Windows service |
| `ShopVisible.JobManager.JobManagerService.IntgTests` | Supporting code; trace usage from solution references. |
| `ShopVisible.JobManager.JobProcessorService` | Windows/ECS task worker: dequeues work, runs ODX-style task handlers against OMS DB. |
| `ShopVisible.JobManager.JobProcessorService.IntgTests` | Supporting code; trace usage from solution references. |
| `ShopVisible.JobManager.PostOfficeService` | Supporting code; trace usage from solution references. |
| `ShopVisible.JobManager.Reporting` | Supporting code; trace usage from solution references. |
| `ShopVisible.JobManager.UnitTests` | Supporting code; trace usage from solution references. |
| `ShopVisible.Services.Amazon` | Supporting code; trace usage from solution references. |
| `ShopVisible.Services.AmazonCommunciation` | Supporting code; trace usage from solution references. |
| `ShopVisible.Services.Shipping` | Supporting code; trace usage from solution references. |
| `ShopVisible.Services.Shipping.IntgTests` | Supporting code; trace usage from solution references. |
| `ShopVisible.WebReferenceWrappers` | Supporting code; trace usage from solution references. |
| `ShopVisible.WebReferenceWrappers.Interfaces` | Supporting code; trace usage from solution references. |
| `ShopVisible.WellsFargo` | Supporting code; trace usage from solution references. |
| `Solutions` | `.sln` collection |
| `SolutionUnitTests` | Supporting code; trace usage from solution references. |
| `SQLChangeScripts` | Versioned SQL shipped with releases; navigation, infrastructure_setting keys, schema deltas. |
| `Support` | Supporting code; trace usage from solution references. |
| `Support.Utilities` | Supporting code; trace usage from solution references. |
| `Utilities` | Supporting code; trace usage from solution references. |
| `Validation` | Supporting code; trace usage from solution references. |
| `version` | Supporting code; trace usage from solution references. |
| `WebsiteBuild.proj` | Supporting code; trace usage from solution references. |