# Deployables catalog — repos, ECR, pipelines, Terraform

**Audience:** Anyone asking “which repo builds what?” or “which pipeline do I run?”  
**Source of truth in code:** `oms-aws-service-manager-batch/docs/batch-job-manager-deployment-runbook.md` (POD QA, Oct 2026) — summarized here for newcomers.

---

## Four repositories (Batch migration stack)

| Repository | Delivers | Runs on |
|------------|----------|---------|
| **`oms`** | Site Manager UI, WebAPI proxy, `SQLChangeScripts`, Toronado/JobManager code | **minisoft** ECS (image from release pipeline) |
| **`oms-aws-job-scheduler`** | Scheduler REST API, EF Core `oms_batch` schema — **local:** `RepoSuite/oms-aws-job-scheduler` | **`servicemanagerscheduler`** ECS |
| **`oms-aws-service-manager-batch`** | Five AWS Batch worker images | **AWS Batch** Fargate |
| **`oms-infrastructure`** | Terraform: ECS, Batch JD, Step Functions, SSM | Harness apply |

**Runtime flow:**

```text
Batch Job Manager (oms UI)
  → DCEOM.WebApi proxy
    → oms-aws-job-scheduler (/api/v1)
      → oms_batch Postgres + EventBridge schedules
        → Step Functions (optional) → AWS Batch
          → oms-aws-service-manager-batch container
```

API detail: [18-scheduler-api.md](./18-scheduler-api.md). UI/proxy: [07-batch-scheduler-api-ui.md](./07-batch-scheduler-api-ui.md).

---

## ECR repository names (shared naming)

Published from **`oms release pipeline`** (build account often **`767398067331`**; workloads in tenant account e.g. **`268173716021`** — cross-account pull).

| Image / service | ECR repository name |
|-----------------|---------------------|
| Scheduler API | `oms-aws-job-scheduler` |
| Inventory feed job | `oms-aws-service-manager-batch-inventory-feed` |
| Cancel items | `oms-aws-service-manager-batch-cancelitems` |
| Update item status | `oms-aws-service-manager-batch-updateitemstatus` |
| Reset for reroute | `oms-aws-service-manager-batch-resetitemsforreroute` |
| Export order items | `oms-aws-service-manager-batch-export-order-items` (see batch `docs/docker-images.md`) |

Terraform examples sometimes use `oms-aws-service-manager-batch-cancel-items` (hyphen) — **match the ECR repo name in your account** before apply.

**Symptom:** Batch job “succeeds” but old code runs → JD revision points at stale image tag; verify with `aws batch describe-job-definitions` (runbook § sanity check).

---

## Harness pipelines (names from runbook — adjust for your estate)

| Pipeline | Stage / purpose |
|----------|-----------------|
| **`oms release pipeline`** | Build & **publish** images to ECR (may need **second run** with Build Type `Git Tag`) |
| **`OMS-DEV-SERVICE-MANAGER-BATCH-CD`** | Step Functions + Batch job definition deploy |
| **`OMS-DEV-AWS-ECS-SERVICE-CD`** | `servicemanagerscheduler_deploy` |
| **`OMSDEVAWSECSSERVICESHAREDCD`** | Scheduler image tag bump |
| **`oms15-ECS`** (in infra repo) | Classic ECS: minisoft, feeds, facades, … |

**Order for new env (Batch Job Manager):** DB baseline → Parameter Store scheduler endpoint → Step Function stack → scheduler ECS with EventBridge → publish image → Batch JD → catalog SQL fix-up → UI smoke (full steps in batch repo runbook).

---

## ECS services ↔ Terraform folder ↔ typical image source

| ECS name | Infra folder | Application source |
|----------|--------------|-------------------|
| minisoft | `04-minisoft` | **`oms`** monorepo (ShopLogic) |
| servicemanagerscheduler | `22-servicemanagerscheduler` | **`oms-aws-job-scheduler`** |
| taskscheduler | `06-taskscheduler` | Legacy task stack image (not top-level in `oms` listing) |
| taskprocessor | `09-taskprocessor` | Job processor build (JobManager solutions) |
| omsfeed | `07-omsfeed` | Feed worker image |
| omsinventoryfeed | `08-omsinventoryfeed` | Feed worker image |
| orderfacade | `10-orderfacade` | ECR **`eom-service-order-facade`** (`oms15-ECS.yaml` `imagePath`) |
| inventoryfacade | `11-inventoryfacade` | ECR **`eom_service_inventory_api`** |
| keycloak | `03-keycloak` | Upstream Keycloak image + config |
| extensibility | `05-extensibility` | Extensibility API repo |
| coreapi | `16-coreapi` | Core API image |
| coreservice | `17-coreservice` | Core service image |
| corepaymentapi | `18-corepaymentapi` | Payment API image |
| corekekservice | `19-corekekservice` | KEK service image |
| omstaxationfacade / omstaxation | `20` / `21` | Tax services |
| configrulemanager | `15-configrulemanager` | Config rules manager |

All use `var.container_image` at deploy time — image URL comes from **Harness**, not from git in infra repo.

---

## AWS Batch ↔ Terraform ↔ batch repo

| jobname (example) | ECR (example) | Code folder |
|-------------------|---------------|-------------|
| `inventory-feed` | `oms-aws-service-manager-batch-inventory-feed` | `Jobs/InventoryFeed/` |
| `cancel-items` | `oms-aws-service-manager-batch-cancelitems` | `Jobs/CancelItems/` |
| `update-item-status` | `oms-aws-service-manager-batch-updateitemstatus` | `Jobs/UpdateItemStatus/` |
| `reset-items-for-reroute` | `oms-aws-service-manager-batch-resetitemsforreroute` | `Jobs/ResetItemsForReroute/` |
| `export-order-items` | `…-export-order-items` | `Jobs/ExportOrderItems/` |

Terraform: `03-application/03-aws-batch-job/02-servicemanager-scheduled-job` (stage **B**).  
Platform queue: `02-platform/03-aws-batch/02-aws-batch-servicemanager-platform` (stage **A**).

---

## Parameter Store endpoints (must exist for UI)

| Parameter | Purpose |
|-----------|---------|
| `…/servicemanagerscheduler/endpoint` | Full **https://** URL to scheduler API (runbook §7 — set via pipeline, not by hand) |
| `…/sm/batchjobmanager/enabled` | Feature flag — **Site Manager owns** after create |
| Infrastructure setting `APIGatewayBatchSchedulerURL` | OMS DB setting for proxy (no `/api/v1` suffix) |

---

## Deep runbooks (read in RepoSuite, not duplicated here)

| Document | Path |
|----------|------|
| Batch Job Manager deploy & traps | `RepoSuite/oms-aws-service-manager-batch/docs/batch-job-manager-deployment-runbook.md` |
| ODX feed monitor (legacy) | `RepoSuite/oms/docs/odx-feed-pipeline-monitor-runbook.md` |
| Batch architecture | `RepoSuite/oms-aws-service-manager-batch/docs/ARCHITECTURE.md` |

---

## Related product knowledge

- [11-environments-matrix.md](./11-environments-matrix.md)  
- [02-terraform.md](./02-terraform.md)  
- [01-batch.md](./01-batch.md)  
