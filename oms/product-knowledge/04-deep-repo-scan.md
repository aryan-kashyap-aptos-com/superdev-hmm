# Deep repo scan — Batch jobs & `oms-infrastructure`

**Scanned:** `RepoSuite/oms-aws-service-manager-batch`, `RepoSuite/oms-infrastructure` (local trees on disk).  
**Use with:** [01-batch.md](./01-batch.md), [02-terraform.md](./02-terraform.md).

This page is the **second-pass map** — runtime flows, orchestration, Postgres catalog contracts, what is deployed in examples vs documented-only, and sharp edges for agents.

---

## 1. System slice (how pieces connect)

```mermaid
flowchart TB
  subgraph schedule [Scheduling]
    EB[EventBridge Scheduler]
    SFN[Step Functions workflow]
    L[Catalog Lambda]
    PG[(Postgres oms_batch + OMS)]
  end
  subgraph batch [AWS Batch Fargate]
    Q[Job queue - stage A]
    JD[Job definition - stage B]
    NET[.NET 8 container - batch repo]
  end
  subgraph longrun [ECS - still relevant]
    TS[taskscheduler]
    TP[taskprocessor]
    OF[omsfeed / omsinventoryfeed]
    FAC[orderfacade / inventoryfacade]
  end
  EB --> SFN
  SFN --> L
  L --> PG
  SFN -->|submitJob.sync Map MaxConcurrency 1| JD
  JD --> NET
  NET --> PG
  NET --> S3[(S3 exports)]
  TS --> PG
  TP --> PG
  OF -. legacy queue paths -. TP
```

**Takeaway:** Batch jobs **replace** specific Windows scheduled tasks and RabbitMQ hops; they still share the **same OMS Postgres** (and S3) as ECS facades and feeds. Site Manager / backadmin is a **separate** deployable (see [03-qa-environments.md](./03-qa-environments.md)), not this repo.

---

## 2. Batch application repo — structure

| Area | Count / note |
|------|----------------|
| Job hosts | **5** — `Jobs/*/(*.Job)/Program.cs` only |
| Shared library | `Shared/OmsAwsBatch.Infrastructure` — SSM, submit JSON, exit codes, logging, SES |
| Per-job layout | `OmsAwsBatch.<Job>/` (+ `EomAdapter` for 4 jobs), `UnitTests`, `IntgTests`, `Dockerfile`, `README` |
| Export-only extra | `OmsAwsBatch.ExportOrderItems.Generation` — export file generation |
| Solution | `OmsAwsBatchJobs.sln` |

**No sixth job folder** in the app repo today — scope is exactly the five Service Manager migrations.

### 2.1 Per-job execution pipeline (common pattern)

Almost every host follows the same skeleton:

1. `BatchProcessContext.EnsureInitialized()` + logging scope (`CorrelationId`, `AWS_BATCH_JOB_*`).
2. `BatchSubmitJobJson.Resolve` — **command-line last argv wins** over `{Job}__SubmitJobParameterJson`.
3. Reject literal `Ref::` (exit **3**) — means Batch never substituted the parameter.
4. Parse **generic envelope** (`configType`, `operation`, `settings`, `filters` / `customFields`).
5. DI-resolve `*Processor` or run `*JobRunner` orchestration.
6. Return **integer exit code** — infra/ops must treat as contract.

| Job | Runner entry | Processor / core work | Private EOM NuGet |
|-----|----------------|----------------------|-------------------|
| Inventory Feed | `InventoryFeedJobRunner` | `InventoryFeedScheduler` + `InventoryExportService` → S3 | No |
| Export Order Items | `ExportOrderItemsJobRunner` | `ExportOrderItemsProcessor` + in-process sink (no RabbitMQ) | Yes |
| Reset for reroute | `ResetItemsForRerouteJobRunner` | `ResetItemsForRerouteProcessor` + EomAdapter | Yes |
| Update item status | `UpdateItemStatusJobRunner` | `UpdateItemStatusProcessor` + `ExecutionTimeTracker` | Yes |
| Cancel items | `CancelItemsJobRunner` | `CancelItemsProcessor` + optional `MailMessageSesSender` | Yes |

### 2.2 Inventory Feed — extra depth

- Submit JSON is resolved through `InventoryFeedSubmitPayloadResolver` → **generic EXPORT** envelope; export XML lives inside settings/customFields, not legacy top-level-only `configXml` envelopes (`GenericJobConfigDetector`).
- **JobStepId optional:** `settings.JobStepId` &gt; 0 links to Toronado `jobstep` for `lastsynced`; **0 is allowed** (export runs, no write-back).
- **Export type gate:** must be `PRODUCTINVENTORY` (exit **5**).
- **Phase 1+2 in one process:** supplier SQL (Dapper/Npgsql) → `InProcessInventoryExportSink` → Demandware XML → `S3DocumentSaveWrapper`.
- **Site paths:** `MutableSiteNameHolder` from export XML `SiteName`.
- **POC override:** `AppConfig:PocOutputPathOverride` rewrites UNC paths for local/dir testing.

### 2.3 Export Order Items — extra depth

- Port of ODX `ExportOrderItemsTaskHandler`; queue `export_requested` **removed**.
- **`settings.taskId`** must be stable **OMS scheduler GUID** — not AWS Batch job id (exit **5** if missing).
- **Exit 8 before any order work** — missing `ExportOrderItems:S3:BucketName` (prevents duplicate order notes).
- De-dup via `OMSFeedsExportedItemRecord`; empty filter is **legal** (parity with ODX).
- `ExportEndDate` from `IWallClock` (UTC-safe).

### 2.4 TASK jobs (Reset, Update, Cancel)

- Shared exit pattern: **1** missing JSON, **2** DI, **3** bad JSON/`Ref::`, **4** unhandled (**retryable** in classifier), **6** max runtime, **7** EOM per-order errors.
- DB: `ConnectionStrings:Database` first; `OmsDatabase` fallback on Reset host for tests.
- `Npgsql.EnableLegacyTimestampBehavior = true` on Reset (ODX parity).
- Cancel: Batch param key **`jobParamter`** (typo intentional); SES off unless `CancelItems__Ses__Enabled`.

### 2.5 Submit JSON formats

| Format | Detection | Status |
|--------|-----------|--------|
| Legacy Toronado | Top-level `configXml` string | Detected by `GenericJobConfigDetector`; **rejected** for generic TASK paths via `TryRequireGeneric` |
| Generic scheduler | `configType` present | **Required** for TASK jobs and current Inventory path |

**AWS Batch outer shape:** `parameters.<key> = stringify(inner JSON)`; JD `command` includes `Ref::<key>` **after** `dotnet …dll`.

| Job | Parameter key |
|-----|----------------|
| inventory-feed | `inventoryFeedJobJson` |
| reset-items-for-reroute | `resetItemsForRerouteJobJson` |
| update-item-status | `updateItemStatusJobJson` |
| export-order-items | `exportOrderItemsJobJson` |
| cancel-items | `jobParamter` |

**Anti-pattern:** `Ref::` inside `containerOverrides.environment` — not substituted (documented in runner error text).

### 2.6 Exit codes vs Terraform today

`BatchExitRetryClassifier` in the app repo defines **which exit codes are logically retryable** (Inventory **4**; TASK/Export **4** only).

**Infra scan finding:** `02-servicemanager-scheduled-job/9-batch-job-definition.tf` defines `retry_strategy { attempts = … }` only — **no `evaluateOnExit` blocks** appear anywhere in `oms-infrastructure` on disk. That means retries today are **attempt-count based**, not exit-code-selective, until IA adds `evaluateOnExit` to match the app contract.

### 2.7 Tests

```bash
dotnet test OmsAwsBatchJobs.sln --filter "TestCategory!=RequiresDocker&TestCategory!=RequiresOmsDatabase"
```

| Layer | Projects |
|-------|----------|
| Shared | `OmsAwsBatch.Infrastructure.UnitTests` |
| Per job | `OmsAwsBatch.<Job>.UnitTests` |
| Integration | `OmsAwsBatch.<Job>.IntgTests` (+ `*IntegrationTestInputSets` / `Defaults`) |

Categories: `RequiresOmsDatabase`, `RequiresDocker`, `RequiresEomPrivateFeed`; many intg tests `[Explicit]`.

### 2.8 Docs & examples in app repo

| Path | Role |
|------|------|
| `docs/ARCHITECTURE.md` | Legacy vs new, exit tables, idempotency |
| `docs/batch/*.example.json` | JD + SubmitJob for all five jobs |
| `docs/batch/README.md` | SSM env, Ref:: precedence, lambda note |
| `docs/docker-images.md` | Publish + COPY Docker pattern |
| `docs/batch-job-manager-deployment-runbook.md` | Ops runbook |
| `Jobs/InventoryFeed/TESTS.md` | Testcontainers Postgres |

`docs/batch/README.md` references `docs/lambda/inventory_feed_batch_submit_from_toronado.py` — **not present** in the local tree (doc may be ahead of or behind the clone).

---

## 3. Infrastructure repo — layers (inventory)

Rough scale: **thousands** of files (many local `.terraform` caches if you ran init). Logical layout:

### 3.1 `01-infrastructure/`

Foundation: VPC, RDS/Aurora, MQ, peering, bastion (`06-database-operation/01-rds-init`), KMS, Cognito-related shared bits, Harness samples under `08-core/harness-pipeline-source/`, cost tag script at repo root.

### 3.2 `02-platform/`

| Path | Role |
|------|------|
| `01-ecs-cluster` | Cluster + execution role (Batch JD reuses execution role ARN) |
| `03-aws-batch/01-aws-batch-sql-job` | Legacy SQL batch platform |
| `03-aws-batch/02-aws-batch-servicemanager-platform` | **Stage A** — CE + JQ + platform SSM |
| `03-aws-batch/03-aws-batch-servicemanager-catalog-platform-db` | **Stage C** — bastion → `oms_batch` CE/JQ rows |
| `03-aws-batch/scripts/` | DDL / helper SQL (see stage C README for `aws_batch_scheduler_model.sql` path) |

Default catalog schema name: **`oms_batch`** (`batch_scheduler_catalog_schema`).

### 3.3 `03-application/` — Batch (Service Manager)

| Folder | Stage | State key (example) |
|--------|-------|-------------------|
| `03-aws-batch-job/02-servicemanager-scheduled-job` | **B** | `…/servicemanager-scheduled-job/{jobname}/…` |
| `03-aws-batch-job/03-servicemanager-batch-catalog-job-db` | **D** | `…/servicemanager-batch-catalog-job-db/{jobname}/…` |
| `03-aws-batch-job/01-sql-job` | Legacy per-job SQL | superseded pattern |

**Stage B creates:** Fargate JD, CloudWatch log group, **job IAM role**, optional DB connection SecureString in SSM, **job metadata JSON** at `/{owners}/{space}/{env}/{jobname}/batch/metadata`.

**Stage D:** SSH bastion → render `batch_catalog_upsert.sql` from SSM → upsert `job_definition` row (and related FKs). See `03-servicemanager-batch-catalog-job-db/docs/catalog-db-sync.md`.

### 3.4 Tfvars examples on disk (deployment maturity)

| Job | Stage B example | Stage D example |
|-----|-----------------|-----------------|
| inventory-feed | `config.tfvars.example` | `config.tfvars.example` |
| cancel-items | `config.cancel-items.tfvars.example` | `config.cancel-items.tfvars.example` |
| export-order-items, reset, update | **No dedicated tfvars** in tree | **No dedicated tfvars** — copy inventory/cancel pattern, change `jobname`, ECR repo, `Ref::` key, env block |

**ECR naming convention (examples):** `oms-aws-service-manager-batch-{jobname}` on account `767398067331` (dev examples).

### 3.5 Step Functions & workflows (`03-application/06-aws-stepfunction`)

When `isWorkflowBatchOrchestrationDeployment = true`:

1. **EventBridge Scheduler** → `states:StartExecution` with `{"workflowId":"…"}`.
2. **Lambda** loads step list from Postgres (`workflow_orchestration.asl.tftpl` — `LoadCatalog`).
3. **Map** state, **`MaxConcurrency: 1`**, each step **`batch:submitJob.sync`**.

Module: `modules/05-workflow-batch-orchestration/`. Remote state pulls **`servicemanager_batch_job`** state for `batch_job_role_arn` and ECS cluster for execution role.

**Docs:** `02-servicemanager-scheduled-job/docs/workflow-stepfunctions.md`, `workflow-stack-split.md`, `workflow-external-step-jobs.md`.

**Note:** Docs still mention a separate stack **`03-workflow-batch-platform`** for “profile → JD name” SSM map — **that folder is not in the local clone**; treat as Harness/workspace layout or renamed stack; follow `workflow-stack-split.md` for apply order.

### 3.6 ECS microservices (same OMS estate)

Each numbered folder under `03-application/01-aws-ecs-service/` is its own Terraform root, including:

`taskscheduler`, `taskprocessor`, `omsfeed`, `omsinventoryfeed`, `orderfacade`, `inventoryfacade`, `minisoft`, `keycloak`, `coreapi`, `coreservice`, `configrulemanager`, taxation stacks, etc.

These are **not** replaced by Batch; they still matter for **understanding legacy paths** (feeds, task dispatch) and for **shared RDS/SSM**.

---

## 4. README / path traps (infra)

Several READMEs use **stale folder numbers**:

| README says | On disk |
|-------------|---------|
| `03-servicemanager-scheduled-job` (stage B) | `02-servicemanager-scheduled-job` |
| `05-servicemanager-batch-catalog-job-db` (stage D) | `03-servicemanager-batch-catalog-job-db` |
| Stage C under `03-application/04-…` | **`02-platform/03-aws-batch/03-aws-batch-servicemanager-catalog-platform-db`** |

Apply order remains **A → C → B → D** (platform catalog before per-job catalog).

Terraform variable spelling: **`business_divsion`** (typo preserved).

---

## 5. Cross-repo change checklist (expanded)

| You change… | Also update… |
|-------------|--------------|
| New exit code or retry semantics | `BatchExitRetryClassifier`, docs, **and** JD `retry_strategy` / future `evaluateOnExit` in stage B |
| New env var consumed at startup | Stage B `environment` map + SSM metadata JSON shape |
| New Batch parameter key | JD `parameters` + `Ref::` command + example JSON in `docs/batch/` |
| New job | Full app folder + Docker + ECR + A (if needed) → C → B → D; Step Functions catalog rows if part of a workflow |
| Export S3 bucket | `ExportOrderItems__S3__BucketName` in B **before** first prod run (exit 8) |
| Inventory S3 | `InventoryFeed__S3__BucketName`, `InventoryFeed__S3__KeyPrefix` in B |

---

## 6. Agent quick pointers

| Question | Where to look |
|----------|----------------|
| How is submit JSON parsed? | `BatchSubmitJobJson.cs`, `GenericJobConfigParser.cs`, each `*JobRunner.cs` |
| What does infra pass into the container? | `config.tfvars.example`, `9-batch-job-definition.tf`, SSM metadata in `11-batch-job-metadata-ssm.tf` |
| How does workflow order steps? | `workflow_orchestration.asl.tftpl`, catalog Lambda in `02-aws-lambda` (per split doc) |
| What goes into Postgres catalog? | `batch_catalog_upsert.sql`, `catalog-db-sync.md` |
| Legacy behavior comments | `docs/ARCHITECTURE.md`, job READMEs under `Jobs/*/` |

---

## 7. Suggested next scans (not done here)

- Harness pipeline YAML → which jobs are wired in **pod-dev** vs prod.
- ECR tag matrix in CI for all five images (not only inventory-feed / cancel-items).
- Site Manager ↔ Batch Job Manager UI flows (Toronado / `oms_scheduler` tables).
- Confluence / internal runbooks for pod URL matrix (complement [03-qa-environments.md](./03-qa-environments.md)).
