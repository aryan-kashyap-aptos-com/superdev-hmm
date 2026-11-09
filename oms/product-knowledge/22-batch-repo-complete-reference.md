# `oms-aws-service-manager-batch` — complete reference

**Repo:** `RepoSuite/oms-aws-service-manager-batch`  
**Functional guide:** [29-functional-batch-jobs.md](./29-functional-batch-jobs.md).  
**Coverage:** **100% file inventory** on disk (see [inventories](#inventories)). Narrative guide: [01-batch.md](./01-batch.md).

---

## Inventory (100%)

| Artifact | Count | Path |
|----------|------:|------|
| All tracked files (excl. `.git`) | **565** | [inventories/batch-all-files.txt](./inventories/batch-all-files.txt) |
| `.cs` files | **480** | [inventories/batch-cs-files.txt](./inventories/batch-cs-files.txt) |
| `.cs` by area | — | [inventories/batch-cs-by-area.md](./inventories/batch-cs-by-area.md) |

---

## Solution & projects (27 `.csproj`)

| Project | Role |
|---------|------|
| `OmsAwsBatchJobs.sln` | Solution root |
| **Shared** | |
| `Shared/OmsAwsBatch.Infrastructure` | SSM, submit JSON, exit codes, SES, DB factory |
| `Shared/OmsAwsBatch.Infrastructure.UnitTests` | Infrastructure tests |
| **Inventory feed** | |
| `Jobs/InventoryFeed/OmsAwsBatch.InventoryFeed` | Scheduler + S3 export |
| `Jobs/InventoryFeed/InventoryFeed.Job` | `Program.cs` host |
| `Jobs/InventoryFeed/OmsAwsBatch.InventoryFeed.UnitTests` | |
| `Jobs/InventoryFeed/OmsAwsBatch.InventoryFeed.IntgTests` | |
| **Export order items** | |
| `Jobs/ExportOrderItems/OmsAwsBatch.ExportOrderItems` | Processor |
| `Jobs/ExportOrderItems/OmsAwsBatch.ExportOrderItems.Generation` | File generation |
| `Jobs/ExportOrderItems/OmsAwsBatch.ExportOrderItems.EomAdapter` | EOM NuGet |
| `Jobs/ExportOrderItems/ExportOrderItems.Job` | Host |
| `+ UnitTests/IntgTests` | |
| **Reset items for reroute** | |
| `Jobs/ResetItemsForReroute/OmsAwsBatch.ResetItemsForReroute` | Processor |
| `Jobs/ResetItemsForReroute/OmsAwsBatch.ResetItemsForReroute.EomAdapter` | |
| `Jobs/ResetItemsForReroute/ResetItemsForReroute.Job` | Host |
| `+ UnitTests/IntgTests` | |
| **Update item status** | |
| `Jobs/UpdateItemStatus/OmsAwsBatch.UpdateItemStatus` | Processor |
| `Jobs/UpdateItemStatus/OmsAwsBatch.UpdateItemStatus.EomAdapter` | |
| `Jobs/UpdateItemStatus/UpdateItemStatus.Job` | Host |
| `+ UnitTests/IntgTests` | |
| **Cancel items** | |
| `Jobs/CancelItems/OmsAwsBatch.CancelItems` | Processor |
| `Jobs/CancelItems/OmsAwsBatch.CancelItems.EomAdapter` | |
| `Jobs/CancelItems/CancelItems.Job` | Host |
| `+ UnitTests/IntgTests` | |

---

## Exit codes (all jobs)

### Inventory feed (`InventoryFeedExitCode`)

| Code | Name | Retry? |
|-----:|------|--------|
| 0 | Success | No |
| 1 | InvalidJobStepConfiguration | No |
| 2 | JobStepNotFound | No |
| 3 | InvalidPayloadOrExportXml | No |
| 4 | SchedulerReturnedFailure | **Yes** |
| 5 | WrongExportType | No |
| 7 | SchedulerSucceededWithErrorCount | No |

### TASK jobs (Reset / Update / Cancel — shared pattern)

| Code | Reset | Update | Cancel |
|-----:|-------|--------|--------|
| 0 | Success | Success | Success |
| 1 | MissingSubmitJobJson | MissingSubmitJobJson | MissingSubmitJobJson |
| 2 | DependencyResolutionFailed | DependencyResolutionFailed | DependencyResolutionFailed |
| 3 | InvalidSubmitJobJsonOrRefPlaceholder | InvalidSubmitJobJsonOrRefPlaceholder | InvalidSubmitJobJsonOrRefPlaceholder |
| 4 | UnhandledException | UnhandledException | UnhandledException |
| 6 | MaxExecutionTimeReached | MaxExecutionTimeReached | MaxExecutionTimeReached |
| 7 | CompletedWithOrderActionErrors | CompletedWithOrderActionErrors | CompletedWithOrderActionErrors |

**Export order items** adds **5** `MissingTaskId`, **8** `MissingS3Configuration`; codes **5** and **8** are not retryable (`BatchExitRetryClassifier`).

---

## Structured log error codes (`BatchErrorCodes`)

All constants in `Shared/OmsAwsBatch.Infrastructure/Diagnostics/BatchErrorCodes.cs`:

- **Inventory:** `INV_FEED_REF_NOT_SUBSTITUTED`, `INV_FEED_INVALID_SUBMIT_JSON`, `INV_FEED_INVALID_JOBSTEP_CONFIG`, `INV_FEED_JOBSTEP_NOT_FOUND`, `INV_FEED_EXPORT_DESERIALIZE_FAILED`, `INV_FEED_WRONG_EXPORT_TYPE`, `INV_FEED_SCHEDULER_FAILED`, `INV_FEED_SCHEDULER_ERROR_COUNT`
- **Reset:** `RESET_*` (8 codes)
- **Update:** `UPDATE_*` (8 codes)
- **Export:** `EXPORT_*` (10 codes)
- **Cancel:** `CANCEL_*` (8 codes)

---

## Shared infrastructure types

| Area | Types |
|------|--------|
| DB | `IOmsDatabaseConnectionFactory`, `OmsDatabaseConnectionFactory` |
| DI | `InfrastructureServiceCollectionExtensions.AddOmsAwsInfrastructure` |
| SSM | `SsmConnectionStringBootstrap`, `SsmDatabaseConnectionBootstrap`, `ParameterStoreOptionalExtensions` |
| Submit JSON | `BatchSubmitJobJson`, `GenericJobConfig*`, `GenericJobSubmitEnvelope`, `GenericJobStepMetadata*` |
| Diagnostics | `*ExitCode`, `BatchExitRetryClassifier`, `BatchErrorCodes`, `LogRedaction`, `BatchProcessContext`, `JobLogScope` |
| Logging | `BatchLoggingExtensions` |
| Email | `MailMessageSesSender`, `SesEmailOptions` |
| Test defaults | `PodDevOmsConnectionDefaults` |

---

## Docker images

| Job | ECR pattern | Dockerfile | Publish dir |
|-----|-------------|------------|-------------|
| Inventory feed | `oms-aws-service-manager-batch-inventory-feed` | `Jobs/InventoryFeed/Dockerfile` | `artifacts/inventory-feed-publish` |
| Export order items | `oms-aws-service-manager-batch-export-order-items` | `Jobs/ExportOrderItems/Dockerfile` | `artifacts/export-order-items-publish` |
| Reset reroute | `oms-aws-service-manager-batch-resetitemsforreroute` | `Jobs/ResetItemsForReroute/Dockerfile` | `artifacts/resetitemsforreroute-publish` |
| Update status | `oms-aws-service-manager-batch-updateitemstatus` | `Jobs/UpdateItemStatus/Dockerfile` | `artifacts/update-item-status-publish` |
| Cancel items | `oms-aws-service-manager-batch-cancelitems` | `Jobs/CancelItems/Dockerfile` | `artifacts/cancel-items-publish` |

Base image: `mcr.microsoft.com/dotnet/runtime:8.0-jammy-chiseled`.

---

## In-repo documentation (every `docs/` file)

| File | Topic |
|------|--------|
| `README.md` | Repo overview |
| `docs/ARCHITECTURE.md` | Architecture |
| `docs/batch/README.md` | SubmitJob / JD examples index |
| `docs/batch-job-manager-deployment-runbook.md` | Full deploy (BJM) |
| `docs/batch/REGRESSION-TESTS-OBSERVABILITY.md` | CloudWatch / exit codes |
| `docs/docker-images.md` | Image build matrix |
| `docs/nuget-private-feed.md` | EOM NuGet |
| `docs/batch/*.example.json` | Per-job SubmitJob + JD samples (5 jobs) |

---

## Terraform pairing (`oms-infrastructure`)

| `jobname` (stage B) | App folder | Catalog (stage D) |
|---------------------|------------|-------------------|
| `inventory-feed` | `Jobs/InventoryFeed` | matching `jobname` |
| `export-order-items` | `Jobs/ExportOrderItems` | … |
| `reset-items-for-reroute` | `Jobs/ResetItemsForReroute` | … |
| `update-item-status` | `Jobs/UpdateItemStatus` | … |
| `cancel-items` | `Jobs/CancelItems` | … |

Platform: `02-platform/03-aws-batch/02-aws-batch-servicemanager-platform` (A), `03-aws-batch-servicemanager-catalog-platform-db` (C). Per job: `03-application/03-aws-batch-job/02-servicemanager-scheduled-job` (B), `03-servicemanager-batch-catalog-job-db` (D).

---

## Related

- [04-deep-repo-scan.md](./04-deep-repo-scan.md) — cross-repo flows  
- [13-deployables-catalog.md](./13-deployables-catalog.md) — ECR + pipelines  
- Skill: `superdev-hmm/.cursor/skills/oms-aws-service-manager-batch/reference.md`
