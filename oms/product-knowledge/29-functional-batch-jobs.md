# Functional guide — five AWS Batch jobs

**Repo:** `oms-aws-service-manager-batch`  
**Inventory:** [22-batch-repo-complete-reference.md](./22-batch-repo-complete-reference.md).  
**Terraform pairing:** [31-functional-infrastructure-platform.md](./31-functional-infrastructure-platform.md).

Every job shares: **SSM DB bootstrap** → **SubmitJob JSON** (argv or env) → **Processor/Runner** → **integer exit code** → CloudWatch JSON logs with `CorrelationId` / `ErrorCode`.

---

## Shared execution contract

| Concern | Behavior |
|---------|----------|
| JSON source | Last command-line argument **or** `{JobSection}__SubmitJobParameterJson` |
| `Ref::` literal | Exit **3** — Batch did not substitute parameters |
| Generic envelope | `configType` **EXPORT** or **TASK**; `operation`, `settings`, `filters` / `customFields` |
| DB | `ConnectionStrings:Database` from SSM merge |
| Retry | `BatchExitRetryClassifier` — only **inventory exit 4** and TASK **unhandled 4** retry by default |
| Logs | `AddOmsAwsBatchProcessLogging` + `BatchErrorCodes` for Insights queries |

---

## 1. Inventory feed

**User outcome:** Partner-ready **inventory XML** in **S3** for configured suppliers/sites.

| Phase | Code | Action |
|-------|------|--------|
| Validate | `InventoryFeedJobRunner` | `ExportType` must be `PRODUCTINVENTORY` |
| Resolve step | `InventoryFeedSubmitPayloadResolver` | `jobStepId` from JSON/env |
| Suppliers | `ProductSupplierService` | SQL consistent with legacy ExportClasses |
| Export | `InventoryExportService` | Demandware XML via `InProcessInventoryExportSink` |
| Upload | `S3DocumentSaveWrapper` | Bucket/region from `InventoryFeed:S3` |
| Metadata | `ToronadoJobStepService` | Updates `lastsynced` only on full success |

**Idempotency:** at-least-once; S3 keys depend on paths/timestamps.

---

## 2. Export order items

**User outcome:** Order export **file on S3** + per-order **order notes** (“published by service …”).

| Rule | Detail |
|------|--------|
| **taskId** required | Stable across runs for `OMSFeedsExportedItemRecord` de-dupe (not AWS Batch job id) |
| S3 guard | Exit **8** if bucket missing **before** any order touched |
| Empty filter | Allowed — exports up to `MaxRecords` (ODX parity) |
| Time | `ExportEndDate` from `IWallClock.ServerTime` (UTC-safe) |
| Errors | Per-order failures → exit **7** |

**Generation:** `OmsAwsBatch.ExportOrderItems.Generation` — XML/file shape; uses EOM NuGet.

---

## 3. Reset items for reroute

**User outcome:** Bulk **reset routing state** on order lines matching TASK filters.

| Step | Behavior |
|------|----------|
| Parse TASK payload | `ResetItemsForRerouteTaskPayloadParser` |
| EOM | `ResetItemsForRerouteProcessor` via EomAdapter |
| Time cap | Exit **6** when max execution exceeded |
| Partial EOM errors | Exit **7** with per-order detail |

---

## 4. Update item status

**User outcome:** Mass **status transition** on items (filters + limits).

Same TASK pattern as reset: `UpdateItemStatusProcessor`, `ExecutionTimeTracker`, EOM adapter, exits **0/1/2/3/4/6/7**.

---

## 5. Cancel items

**User outcome:** Mass **cancel** with optional customer email.

| Step | Behavior |
|------|----------|
| Filters | `CancelItemsFilterMapper` — **at least one dimension required** |
| Batch size | `PublishBatchSize` chunks through EOM cancel |
| Email | `MailMessageSesSender` when `CancelItems:Ses:Enabled` |
| Errors | Exit **7** if any order batch reports EOM errors |

---

## Operator ↔ developer matrix

| Symptom | Check |
|---------|--------|
| Exit 3 | Job definition `Ref::` mapping; inspect argv in logs |
| Exit 4 inventory | Scheduler returned false — supplier/export config |
| Exit 7 | EOM rejected specific orders — not always retry |
| Exit 8 export | Fix `ExportOrderItems__S3__BucketName` in job definition |
| Wrong data | Wrong `taskId` or filter in submit JSON |
| Old code | ECR tag / job definition revision drift |

---

## Related

- [01-batch.md](./01-batch.md)  
- [27-functional-cross-repo-flows.md](./27-functional-cross-repo-flows.md)  
- Repo `docs/ARCHITECTURE.md`, `docs/batch/*.example.json`
