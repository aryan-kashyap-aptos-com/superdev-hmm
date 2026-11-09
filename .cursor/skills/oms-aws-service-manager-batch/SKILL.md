---
name: oms-aws-service-manager-batch
description: >-
  RepoSuite oms-aws-service-manager-batch — .NET 8 AWS Batch jobs (inventory
  feed, export order items, reset reroute, update item status, cancel items).
  Use for SubmitJob JSON, exit codes, SSM DB bootstrap, Docker publish, tests.
---

# oms-aws-service-manager-batch

**Path:** `/Users/akashyap/RepoSuite/oms-aws-service-manager-batch`

Standalone .NET 8 batch jobs — **no** dependency on `oms_npgsql`, `odx`, or `export-service` as runtime coupling.

## Layout

```text
Shared/OmsAwsBatch.Infrastructure/   # DB factory, SSM bootstrap, logging, exit codes, SES
Jobs/
  InventoryFeed/                     # PRODUCTINVENTORY export, S3, Toronado lastsynced
  ExportOrderItems/                  # In-process export (was Rabbit export_requested)
  ResetItemsForReroute/              # EOM adapter + private NuGet
  UpdateItemStatus/
  CancelItems/
docs/
  ARCHITECTURE.md                    # Exit codes, legacy vs new, observability
  batch/*.example.json               # Job definition + submit-job templates
```

## Jobs summary

| Job | Export type / notes |
|-----|---------------------|
| **InventoryFeed** | `ExportType` must be `PRODUCTINVENTORY`. Phase 1 scheduler + phase 2 in-process sink; S3 via AWSSDK. |
| **ExportOrderItems** | Requires stable `taskId` in settings (not Batch job id). Exit **8** if S3 bucket missing (checked before work). |
| **ResetItemsForReroute** | Generic TASK envelope; exit **7** if EOM reports per-order errors. |
| **UpdateItemStatus** | `itemStatuses` + exactly one `newItemStatuses` in filters. |
| **CancelItems** | See job README under `Jobs/CancelItems/`. |

## Exit codes (infra must match)

Canonical tables: `docs/ARCHITECTURE.md`. Infrastructure **`evaluateOnRetry`** / **`evaluateOnExit`** must use the same numeric meanings.

Examples:

- InventoryFeed: **7** = success flag but `ErrorCount > 0`
- ExportOrderItems: **8** = missing `ExportOrderItems:S3:BucketName` (non-retryable)

## SubmitJob / argv

1. Build inner JSON (`configXml`, `jobStepId`, job-specific `settings` / `filters`).
2. Pass as Batch parameter (e.g. `inventoryFeedJobJson`) with job definition `command: ["Ref::inventoryFeedJobJson"]` after `ENTRYPOINT` `dotnet …dll`.
3. Runner reads **last argv segment** if it looks like `{...}`, else env `*__SubmitJobParameterJson`.

Never put literal `Ref::` in containerOverrides without Batch substitution.

## Database

- Env: `ssm_connectionstring` (parameter **name**), `connectionstringParams` (suffix).
- Merged in-memory to `ConnectionStrings:Database`.
- InventoryFeed also updates `jobstep.lastsynced` when configured.

## Build & test

```powershell
dotnet build OmsAwsBatchJobs.sln
dotnet test OmsAwsBatchJobs.sln --filter "TestCategory!=RequiresDocker&TestCategory!=RequiresOmsDatabase"
```

Docker: **publish on agent, COPY into runtime Dockerfile** — see `README.md` and `docs/docker-images.md`.

Private **Eom.Component.*** packages: `docs/nuget-private-feed.md`.

## Observability

- `AddOmsAwsBatchProcessLogging` → JSON console for CloudWatch Insights.
- Scopes: `CorrelationId` (`OMS_BATCH_CORRELATION_ID`), `AwsBatchJobId`, `AwsBatchJobAttempt`.
- No raw submit JSON in logs — use `LogRedaction` summaries.
- Regression / queries: `docs/batch/REGRESSION-TESTS-OBSERVABILITY.md`.

## Idempotency

Treat reruns as **at-least-once** unless EOM/export layer guarantees otherwise. Inventory `lastsynced` only on full success (zero errors).
