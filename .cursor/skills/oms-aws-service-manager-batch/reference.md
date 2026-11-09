# Batch reference (detailed)

**100% file inventory:** `oms/product-knowledge/22-batch-repo-complete-reference.md` and `oms/product-knowledge/inventories/batch-*`.  
Canonical narrative: `oms/product-knowledge/01-batch.md`. Below is agent-oriented distillation.

## Shared infrastructure assembly

**Path:** `Shared/OmsAwsBatch.Infrastructure/`

| Area | Types |
|------|--------|
| DB | `IOmsDatabaseConnectionFactory`, `OmsDatabaseConnectionFactory` |
| DI | `AddOmsAwsInfrastructure` |
| SSM | `SsmConnectionStringBootstrap`, `SsmDatabaseConnectionBootstrap` |
| Submit JSON | `BatchSubmitJobJson`, `GenericJobConfig*`, `GenericJobSubmitEnvelope` |
| Diagnostics | `*ExitCode`, `BatchExitRetryClassifier`, `BatchErrorCodes`, `LogRedaction`, `BatchProcessContext`, `JobLogScope` |
| Logging | `AddOmsAwsBatchProcessLogging` |
| Email | `MailMessageSesSender`, `SesEmailOptions` |

## Generic envelope helpers

- `GenericJobSubmitEnvelope.TryRequireGeneric` — rejects legacy top-level-only `configXml`
- `GenericJobSettingsReader` — reserved keys `JobStepId`, `JobId`, `LastSynced`
- `BatchSubmitJobJson.Resolve` — argv last segment vs `{Section}__SubmitJobParameterJson`

**EXPORT example shape:** `configType: EXPORT`, `operation: PRODUCTINVENTORY`, settings + customFields.

**TASK example shape:** `configType: TASK`, `operation: CancelItems|…`, filters + settings.

## Exit code retry matrix

| Job family | Retryable codes |
|------------|-----------------|
| Inventory Feed | **4** (scheduler false) |
| TASK + Export | **4** (unhandled exception) only |
| Export | **5**, **8** explicitly **not** retryable |

## Configuration env cheat sheet

| Pattern | Example |
|---------|---------|
| Nested sections | `ConnectionStrings__Database`, `InventoryFeed__S3__BucketName` |
| Batch correlation | `OMS_BATCH_CORRELATION_ID` |
| AWS Batch injected | `AWS_BATCH_JOB_ID`, `AWS_BATCH_JOB_ATTEMPT` |
| Cancel SES | `CancelItems__Ses__Enabled` |

## Docker matrix

| Job | Publish dir | Dockerfile |
|-----|-------------|------------|
| Inventory Feed | `artifacts/inventory-feed-publish` | `Jobs/InventoryFeed/Dockerfile` |
| Reset | `artifacts/resetitemsforreroute-publish` | `Jobs/ResetItemsForReroute/Dockerfile` |
| Update | `artifacts/update-item-status-publish` | `Jobs/UpdateItemStatus/Dockerfile` |
| Export | `artifacts/export-order-items-publish` | `Jobs/ExportOrderItems/Dockerfile` |
| Cancel | `artifacts/cancel-items-publish` | `Jobs/CancelItems/Dockerfile` |

Base: `mcr.microsoft.com/dotnet/runtime:8.0-jammy-chiseled`, `InvariantGlobalization=true`.

## Export Order Items — operational detail

- De-dup: `OMSFeedsExportedItemRecord` + stable `taskId`
- Skips orders without `OrderCreated` in TransactionSequence (ODX parity)
- Order note: “published by service {Name}” via `SalesPerson.AutoNotificationUser`
- `ExportEndDate` from `IWallClock`, not `DateTime.Now`
- Empty filter allowed (up to `MaxRecords`) — `ValidateFilterOrThrow` no-op

## Cancel Items — operational detail

- `CancelItemsFilterMapper` — at least one filter dimension required
- Email path off by default (`Ses__Enabled=false`)

## Docs index (in app repo)

| Doc | Path |
|-----|------|
| Architecture | `docs/ARCHITECTURE.md` |
| Batch examples | `docs/batch/README.md` |
| Observability | `docs/batch/REGRESSION-TESTS-OBSERVABILITY.md` |
| Docker | `docs/docker-images.md` |
| NuGet | `docs/nuget-private-feed.md` |
