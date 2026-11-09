# Product knowledge — OMS AWS Batch application (`oms-aws-service-manager-batch`)

> **New to OMS?** Read [00-onboarding.md](./00-onboarding.md) first (glossary, diagram, what each job does in plain language).

**Repo:** `RepoSuite/oms-aws-service-manager-batch`  
**100% file inventory:** [22-batch-repo-complete-reference.md](./22-batch-repo-complete-reference.md) (565 files, 480 `.cs`).  
**Stack:** .NET 8, AWS Batch (Fargate), Npgsql/Dapper, AWSSDK S3/SES/SSM  

### In plain English

This repository is the **source code for short-lived “worker” programs** that run inside Docker on AWS Batch. Each program connects to the **OMS database**, does one kind of bulk work (export inventory, cancel lines, etc.), writes **logs**, and **exits with a number** that tells AWS whether to retry.

It does **not** create VPCs, job queues, or IAM roles — that is **`oms-infrastructure`** ([02-terraform.md](./02-terraform.md)).

---

## What this repo is for

We are moving **scheduled Windows tasks** (Service Manager) and old **message-queue exports** (ODX + RabbitMQ) to **one container per run** on AWS Batch.

| Old way (simplified) | New way in this repo |
|----------------------|----------------------|
| Message on RabbitMQ → another service exports inventory | **Inventory Feed:** one container does scheduling + export → **S3** |
| ODX publishes “export orders” to a queue | **Export Order Items:** same work **inside one process** → **S3** |
| ODX “task handlers” for cancel / reset / status | **TASK** jobs calling shared **EOM** libraries |

No runtime dependency on legacy deployables `oms_npgsql`, `odx`, or `export-service`.

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

Each job = a folder under `Jobs/`, a **.NET executable**, and a **Docker image** pushed to ECR by your pipeline.

### Inventory Feed

**Plain English:** “Pull supplier inventory from OMS using export settings, build commerce-style XML, upload to S3, optionally update ‘last synced’ in scheduler tables.”

| | |
|---|---|
| **DLL** | `OmsAwsBatch.InventoryFeed.Job.dll` |
| **Operation** | `configType: EXPORT`, `operation: PRODUCTINVENTORY` |
| **Batch parameter** | `inventoryFeedJobJson` → `Ref::inventoryFeedJobJson` |
| **Private NuGet** | None |
| **Notable types** | `InventoryFeedJobRunner`, `InventoryExportService`, `InProcessInventoryExportSink`, `S3DocumentSaveWrapper`, `ToronadoJobStepService` |

Legacy `configXml`-only envelopes are **rejected**; use generic EXPORT envelope (see intg fixtures).

### Export Order Items

**Plain English:** “Find order lines that haven’t been exported yet for this scheduled task, write export records and notes, upload a JSON export file to S3.” Needs a stable **task id** from the OMS scheduler (not the AWS Batch run id).

| | |
|---|---|
| **DLL** | `OmsAwsBatch.ExportOrderItems.Job.dll` |
| **Operation** | `TASK` / `ExportOrderItems` |
| **Parameter** | `exportOrderItemsJobJson` |
| **Critical** | `settings.taskId` must be existing `oms_scheduler.task` **GUID** (not Batch job id, not step id) |
| **Exit 8** | Missing `ExportOrderItems:S3:BucketName` — checked **before** any order work (prevents duplicate order notes) |

### Reset Items for Reroute

**Plain English:** “Given filters (which orders/lines), call EOM to reset items so routing can run again.”

| | |
|---|---|
| **DLL** | `OmsAwsBatch.ResetItemsForReroute.Job.dll` |
| **Parameter** | `resetItemsForRerouteJobJson` |
| **EOM** | `Eom.Component.Order` 3.0.1, `Eom.Component.Inventory` 1.1.263 |

### Update Item Status

**Plain English:** “Bulk-change line item status (from status A to status B) for everything matching filters.”

| | |
|---|---|
| **DLL** | `OmsAwsBatch.UpdateItemStatus.Job.dll` |
| **Parameter** | `updateItemStatusJobJson` |
| **Filters** | Non-empty `itemStatuses`, exactly one `newItemStatuses` |

### Cancel Items

**Plain English:** “Bulk-cancel order lines matching filters; optionally email stakeholders via SES.”

| | |
|---|---|
| **DLL** | `OmsAwsBatch.CancelItems.Job.dll` |
| **Parameter** | **`jobParamter`** (typo preserved for orchestrator parity) → `Ref::jobParamter` |
| **SES** | `CancelItems__Ses__Enabled`; uses `MailMessageSesSender` when true |

**EOM jobs:** `ConnectionStrings:Database` first, `OmsDatabase` fallback. `Npgsql.EnableLegacyTimestampBehavior = true` on Reset host (ODX parity).

---

## Submit-job contract

**Plain English:** Every run needs a **JSON instruction**. AWS Batch passes it into the container (usually as the **last argument** after `dotnet MyJob.dll`). The program parses that JSON to learn operation, filters, and settings.

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

**Plain English:** When the container finishes, it returns an integer to the OS. **0 = success.** Other numbers mean specific failures. Terraform job definitions can say “retry only on code 4” etc. If you change a number in code, **update Terraform** or retries will be wrong.

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
