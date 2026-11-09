# Batch Job Manager UI and Service Manager Scheduler API

**Audience:** Anyone wiring **Windows Service Manager → AWS Batch**, or debugging “Batch Job Manager” in Site Manager.  
**Prerequisites:** [01-batch.md](./01-batch.md), [06-site-manager-shoplogic.md](./06-site-manager-shoplogic.md).

---

## What problem this solves

Operators and implementers need to **define, schedule, and monitor AWS Batch jobs** without only using the AWS Console. The product provides:

1. A **React UI** inside Site Manager (Batch Job Manager).  
2. A **scheduler REST API** on ECS (`servicemanagerscheduler`) backed by Postgres schema for batch metadata.  
3. **Workers** that run when Batch starts a container ([01-batch.md](./01-batch.md)).

---

## End-to-end request flow

```text
Browser (React)
    │  same origin: ShopLogic /api/v1/*
    ▼
DCEOM.WebApi  BatchSchedulerProxyController
    │  server-side forward
    ▼
Scheduler API  (servicemanagerscheduler ECS)  /api/v1/*
    │  SubmitJob, schedules, catalog
    ▼
AWS Batch  →  Fargate container  →  oms-aws-service-manager-batch
```

**Important:** The browser **never** calls the scheduler hostname directly. ShopLogic **proxies** using `APIGatewayBatchSchedulerURL` from **Infrastructure Settings** in the database.

Source: `Shopvisible.Core.Shoplogic.BatchJobManager.Frontend.React/README.md`.

---

## Application components (`RepoSuite/oms`)

| Artifact | Path |
|----------|------|
| React SPA | `Shopvisible.Core.Shoplogic.BatchJobManager.Frontend.React/` |
| Hosted page | `ShopVisible.Core.ShopLogic/backadmin/BatchJobManager.aspx` |
| Static bundle | `ShopVisible.Core.ShopLogic/static/batch-job-manager/` (after `npm run copy`) |
| Proxy | `DCEOM.WebApi/BatchSchedulerProxyController.cs` |
| DI registration | `ShopVisible.Core.Shell/Bootstrapper.cs` (`BatchSchedulerProxyService`) |
| DB setting seed | `SQLChangeScripts/2026.5/Insert_APIGatewayBatchSchedulerURL_InfrastructureSetting.sql` |
| Nav SQL | `SQLChangeScripts/2026.5/Insert_BatchJobManager_to_ResourcesAndRolesVsResources.sql` |

**Build (developer machine):**

```powershell
cd Shopvisible.Core.Shoplogic.BatchJobManager.Frontend.React
npm install
npm run build
npm run copy
```

---

## Scheduler API container (`RepoSuite/oms-infrastructure`)

| Item | Detail |
|------|--------|
| Terraform stack | `03-application/01-aws-ecs-service/22-servicemanagerscheduler` |
| API deep-dive | [18-scheduler-api.md](./18-scheduler-api.md) (controllers, EF, EventBridge) |
| Service name | `servicemanagerscheduler` (Harness may add deploy stage in future YAML — verify pipeline) |
| SSM prefix | `…/servicemanagerscheduler/` (see parameter store locals) |
| Runtime | ASP.NET Core on Fargate (`ASPNETCORE_URLS`, port from tfvars) |
| Database | `ConnectionStrings__DefaultConnection` / `AdminConnection` with **`SearchPath`** = batch scheduler schema from SSM |
| Auth | JWT: `JwtValidation__ValidIssuer` = Keycloak realm URL |
| Migrations | `RUN_MIGRATIONS_ON_STARTUP` — off until env baselined |
| EventBridge | `EventBridgeScheduler__*` — when enabled, UI-created schedules reach AWS; otherwise **NoOp** placeholder ARNs |

**Application source:** Bitbucket repo **`oms-aws-job-scheduler`** (not under `RepoSuite/oms`). ECR: `oms-aws-job-scheduler`. Full deploy order and traps: `RepoSuite/oms-aws-service-manager-batch/docs/batch-job-manager-deployment-runbook.md` and [13-deployables-catalog.md](./13-deployables-catalog.md).

---

## How this connects to Batch platform

| Layer | Doc |
|-------|-----|
| Job definitions, ECR, `Ref::` JSON | [02-terraform.md](./02-terraform.md) stage **B** |
| Postgres catalog rows | Stage **C** (platform) + **D** (per job) |
| Step Functions multi-step | [04-deep-repo-scan.md](./04-deep-repo-scan.md) — `06-aws-stepfunction` |
| Worker exit codes | [01-batch.md](./01-batch.md) |

**SubmitJob JSON** shape for workers is defined in the **batch repo** (`docs/batch/*.example.json`), not in the scheduler UI repo.

---

## Configuration checklist (new environment)

| Step | Action |
|------|--------|
| 1 | Apply Batch **A → C → B → D** for each job ([02-terraform.md](./02-terraform.md)) |
| 2 | Deploy **servicemanagerscheduler** ECS with Keycloak issuer + DB schema |
| 3 | Set **`APIGatewayBatchSchedulerURL`** in OMS Infrastructure Settings (no `/api/v1` suffix) |
| 4 | Deploy **minisoft** with WebApi proxy + React bundle |
| 5 | Run Batch Job Manager **nav SQL** for roles/resources |
| 6 | If using UI schedules, enable **EventBridgeScheduler** env vars on scheduler task |

---

## Troubleshooting

| Symptom | Likely cause |
|---------|----------------|
| UI loads but API 404 | Proxy path; WebApi not deployed; wrong `APIGatewayBatchSchedulerURL` |
| 401 from scheduler | JWT issuer/Keycloak mismatch |
| Schedules show fake ARN | `EventBridgeScheduler__Enabled` false or missing IAM on scheduler task role |
| Batch runs but wrong payload | Job definition `Ref::` key ≠ SubmitJob parameters ([01-batch.md](./01-batch.md)) |
| `Ref::` in container logs | Batch substitution failed — fix JD command/parameters |

---

## Relationship to legacy Service Manager

| Legacy | AWS path |
|--------|----------|
| Windows scheduled .NET EXE on SM server | **AWS Batch** container ([01-batch.md](./01-batch.md)) |
| Toronado job steps / `jobstep.lastsynced` | Inventory Feed + scheduler DB ([04-deep-repo-scan.md](./04-deep-repo-scan.md)) |
| ODX queue handlers | In-process in Batch jobs (export, inventory) |

---

## Next reading

- [01-batch.md](./01-batch.md) — worker behavior  
- [02-terraform.md](./02-terraform.md) — infra stages  
- [04-deep-repo-scan.md](./04-deep-repo-scan.md) — Step Functions + `oms_batch` catalog  
