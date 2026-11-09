# Product knowledge — OMS AWS Batch application (`oms-aws-service-manager-batch`)

**Repo:** `RepoSuite/oms-aws-service-manager-batch`  
**Stack:** .NET 8, AWS Batch (Fargate), Npgsql/Dapper, AWSSDK S3/SES/SSM  
**Boundary:** Application code and container images only. Job queues, CE, job definitions, IAM, and `evaluateOnExit` live in **oms-infrastructure**.

---

## What this repo is for

Replaces legacy **Windows Service Manager scheduled tasks** and parts of **ODX + RabbitMQ** with **containerized AWS Batch jobs** that talk to OMS PostgreSQL (and EOM where required). There is **no runtime dependency** on `oms_npgsql`, `odx`, or `export-service` as separate deployables.

| Legacy pattern | New pattern |
|----------------|-------------|
| OMS publishes to RabbitMQ `inventory_requested`; ODX consumes | **Inventory Feed:** scheduler + export **in-process**, S3 upload |
| ODX `ExportOrderItemsTaskHandler` → queue `export_requested` | **Export Order Items:** in-process sink + S3 (DCOMS-29257) |
| ODX task handlers for cancel / reset / update status | **TASK** jobs with `Eom.Component.*` adapters |

---

## Repository map

```text
Shared/OmsAwsBatch.Infrastructure/     Cross-job: SSM DB bootstrap, submit JSON, exit codes, JSON logging
Jobs/InventoryFeed/                    EXPORT PRODUCTINVENTORY (no EOM NuGet)
Jobs/ExportOrderItems/                 EXPORT + Generation + EomAdapter
Jobs/ResetItemsForReroute/             TASK + EomAdapter
Jobs/UpdateItemStatus/                 TASK + EomAdapter
Jobs/CancelItems/                      TASK + EomAdapter + optional SES
docs/ARCHITECTURE.md                   Exit codes, legacy notes (source of truth for infra)
docs/batch/*.example.json              Job definition + SubmitJob templates
```

**Solution:** `OmsAwsBatchJobs.sln`

---

## Jobs catalog

### Inventory Feed

| | |
|---|---|
| **DLL** | `OmsAwsBatch.InventoryFeed.Job.dll` |
| **Operation** | `configType: EXPORT`, `operation: PRODUCTINVENTORY` |
| **Batch parameter** | `inventoryFeedJobJson` → `Ref::inventoryFeedJobJson` |
| **Private NuGet** | None |
| **Notable types** | `InventoryFeedJobRunner`, `InventoryExportService`, `InProcessInventoryExportSink`, `S3DocumentSaveWrapper`, `ToronadoJobStepService` |

Legacy `configXml`-only envelopes are **rejected**; use generic EXPORT envelope (see intg fixtures).

### Export Order Items

| | |
|---|---|
| **DLL** | `OmsAwsBatch.ExportOrderItems.Job.dll` |
| **Operation** | `TASK` / `ExportOrderItems` |
| **Parameter** | `exportOrderItemsJobJson` |
| **Critical** | `settings.taskId` must be existing `oms_scheduler.task` **GUID** (not Batch job id, not step id) |
| **Exit 8** | Missing `ExportOrderItems:S3:BucketName` — checked **before** any order work (prevents duplicate order notes) |

### Reset Items for Reroute

| | |
|---|---|
| **DLL** | `OmsAwsBatch.ResetItemsForReroute.Job.dll` |
| **Parameter** | `resetItemsForRerouteJobJson` |
| **EOM** | `Eom.Component.Order` 3.0.1, `Eom.Component.Inventory` 1.1.263 |

### Update Item Status

| | |
|---|---|
| **DLL** | `OmsAwsBatch.UpdateItemStatus.Job.dll` |
| **Parameter** | `updateItemStatusJobJson` |
| **Filters** | Non-empty `itemStatuses`, exactly one `newItemStatuses` |

### Cancel Items

| | |
|---|---|
| **DLL** | `OmsAwsBatch.CancelItems.Job.dll` |
| **Parameter** | **`jobParamter`** (typo preserved for orchestrator parity) → `Ref::jobParamter` |
| **SES** | `CancelItems__Ses__Enabled`; uses `MailMessageSesSender` when true |

**EOM jobs:** `ConnectionStrings:Database` first, `OmsDatabase` fallback. `Npgsql.EnableLegacyTimestampBehavior = true` on Reset host (ODX parity).

---

## Submit-job contract

### Resolution order (`BatchSubmitJobJson.Resolve`)

1. **Last argv** if trimmed value starts with `{` or unsubstituted `Ref::`
2. Else configuration key `{JobSection}__SubmitJobParameterJson` (e.g. `InventoryFeed__SubmitJobParameterJson`)

### Generic envelope (`GenericJobConfig`)

| Field | Role |
|-------|------|
| `configType` | `EXPORT` or `TASK` |
| `operation` | e.g. `PRODUCTINVENTORY`, `CancelItems` |
| `settings` | Job-specific; reserved: `JobStepId`, `JobId`, `LastSynced` |
| `filters` | TASK jobs — filter dimensions (JSON) |
| `customFields` | EXPORT extensions |

**AWS Batch outer layer:** `parameters.<key>` = stringified inner JSON; job definition `command: ["Ref::<key>"]` after `ENTRYPOINT dotnet …dll`.

| Job | Parameter key |
|-----|----------------|
| Inventory Feed | `inventoryFeedJobJson` |
| Reset | `resetItemsForRerouteJobJson` |
| Update Item Status | `updateItemStatusJobJson` |
| Export Order Items | `exportOrderItemsJobJson` |
| Cancel Items | `jobParamter` |

Do **not** put literal `Ref::` in `containerOverrides` without Batch substitution.

---

## Exit codes (infra must mirror)

Defined under `Shared/OmsAwsBatch.Infrastructure/Diagnostics/`.  
**Retry classifier:** `BatchExitRetryClassifier` — only **`UnhandledException` (4)** on TASK-style jobs is retryable; Inventory **scheduler failure (4)** is retryable; **Export 5/8** and **Inventory 7** are not.

### Inventory Feed

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Invalid/missing job step |
| 2 | Job step not found |
| 3 | Bad payload / export XML |
| 4 | Scheduler returned false (**retryable**) |
| 5 | Wrong export type |
| 7 | Success flag but `ErrorCount > 0` |

### TASK jobs (Reset, Update, Cancel) + shared pattern

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Missing submit JSON |
| 2 | DI failure |
| 3 | Invalid JSON / `Ref::` placeholder |
| 4 | Unhandled exception (**retryable**) |
| 6 | Max execution time |
| 7 | Finished with per-order EOM errors |

### Export Order Items (adds)

| 5 | Missing `taskId` |
| 8 | Missing S3 bucket config |

Update Terraform `evaluateOnExit` whenever these change.

---

## Database & SSM

At container start:

| Env | Purpose |
|-----|---------|
| `ssm_connectionstring` | SSM parameter **name** (not the secret) |
| `connectionstringParams` | Suffix merged with `;` |
| `AWS__Region` / `AWS_REGION` | SSM client region |

→ `SsmDatabaseConnectionBootstrap` → in-memory `ConnectionStrings:Database`.

**Job role IAM:** `ssm:GetParameter`, `kms:Decrypt` if CMK. Export also needs S3; Cancel may need SES.

---

## Build, Docker, publish

**Pattern:** Publish on CI/agent, **COPY** into chiseled `mcr.microsoft.com/dotnet/runtime:8.0-jammy` image — no `dotnet restore` in Dockerfile.

```bash
dotnet publish Jobs/InventoryFeed/InventoryFeed.Job/InventoryFeed.Job.csproj \
  -c Release -o artifacts/inventory-feed-publish -r linux-x64 --self-contained false
docker build -f Jobs/InventoryFeed/Dockerfile -t oms-aws-inventory-feed:latest .
```

EOM jobs need private feed **`aptos-oms-nuget`** (`docs/nuget-private-feed.md`).

| Job | Artifact dir |
|-----|----------------|
| Inventory Feed | `artifacts/inventory-feed-publish` |
| Reset | `artifacts/resetitemsforreroute-publish` |
| Update Item Status | `artifacts/update-item-status-publish` |
| Export Order Items | `artifacts/export-order-items-publish` |
| Cancel Items | `artifacts/cancel-items-publish` |

---

## Tests

Default CI:

```bash
dotnet test OmsAwsBatchJobs.sln --filter "TestCategory!=RequiresDocker&TestCategory!=RequiresOmsDatabase"
```

| Category | Meaning |
|----------|---------|
| `RequiresOmsDatabase` | Integration tests hitting real Postgres |
| `RequiresEomPrivateFeed` | EOM intg suites |

Many intg tests are `[Explicit]` — run by name locally.

---

## Observability

- `AddOmsAwsBatchProcessLogging` → JSON lines for CloudWatch Insights
- Scopes: `CorrelationId` (`OMS_BATCH_CORRELATION_ID`), `AwsBatchJobId`, `AwsBatchJobAttempt`
- **Never** log raw submit JSON — `LogRedaction` summaries only
- See `docs/batch/REGRESSION-TESTS-OBSERVABILITY.md`

---

## Idempotency (operations)

- **Inventory:** `lastsynced` only on full success (zero errors). Reruns may repeat S3 work.
- **TASK jobs:** Exit **7** means “ran but EOM reported errors” — do not assume idempotent side effects.
- **Export:** De-dup via `OMSFeedsExportedItemRecord` + stable `taskId`.

---

## Handoff to infrastructure

When you change exit codes, logging, env vars, or container command:

1. Update **job definition** stage **B** (`03-application/03-aws-batch-job/02-servicemanager-scheduled-job`)
2. Update **catalog row** stage **D** if metadata shape changes
3. Ship **ECR tag** and Terraform in the same release

See `oms/product-knowledge/02-terraform.md`.
