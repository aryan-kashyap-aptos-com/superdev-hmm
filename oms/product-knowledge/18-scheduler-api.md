# `oms-aws-job-scheduler` — scheduler API

**Audience:** Developers on Batch Job Manager backend, platform wiring EventBridge.  
**Repo:** `/Users/akashyap/RepoSuite/oms-aws-job-scheduler` (cloned from Bitbucket `aptosretail/oms-aws-job-scheduler`).  
**Runs as:** ECS `servicemanagerscheduler` ([07-batch-scheduler-api-ui.md](./07-batch-scheduler-api-ui.md)).  
**100% inventory:** [23-job-scheduler-complete-reference.md](./23-job-scheduler-complete-reference.md).

---

## What it does

ASP.NET Core API that **owns the `oms_batch` catalog in Postgres** (EF Core):

- Compute environments, job queues, job definitions (mirror of AWS + metadata)  
- **Scheduled jobs**, steps, dependencies, cron schedules  
- **Job runs**, attempts, events  
- **EventBridge Scheduler** integration — creates real schedules when enabled, or no-op locally

It does **not** execute Batch work itself — Step Functions submits jobs using catalog data ([17-workflows-and-step-functions.md](./17-workflows-and-step-functions.md)).

---

## Solution layout

```text
src/oms-aws-job-scheduler.Api/           HTTP host, controllers
src/oms-aws-job-scheduler.Application/   Services, validators, DTOs
src/oms-aws-job-scheduler.Domain/        Entities, enums
src/oms-aws-job-scheduler.Infrastructure/ EF Core, migrations, EventBridge adapter
tests/oms-aws-job-scheduler.UnitTests/
```

---

## HTTP API (`/api/v1/*`)

| Controller | Route prefix | Purpose |
|------------|--------------|---------|
| `HealthController` | `api/v1/health` | Liveness (`/health` on task also used by ECS) |
| `ComputeEnvironmentsController` | `api/v1/compute-environments` | CE catalog CRUD |
| `JobQueuesController` | `api/v1/job-queues` | Queue catalog CRUD |
| `JobDefinitionsController` | `api/v1/job-definitions` | JD catalog CRUD |
| `ScheduledJobTypesController` | `api/v1/scheduled-job-types` | Job type enum / metadata |
| `ScheduledJobsController` | `api/v1/scheduled-jobs` | Jobs, steps, **schedule** PUT/DELETE |
| `JobRunsController` | `api/v1/job-runs` | Run history |
| `OrchestratorController` | `api/v1/orchestrator` | Orchestration triggers / status |

**UI path:** Browser → ShopLogic proxy → these routes (never direct from browser to ECS hostname).

Notable schedule endpoints (from README):

- `PUT /api/v1/scheduled-jobs/{id}/schedule` — cron, timezone, sync EventBridge  
- `DELETE /api/v1/scheduled-jobs/{id}/schedule` — remove schedule  
- `DELETE /api/v1/scheduled-jobs/{id}` — deletes job; unschedules first if ARN exists  

---

## Domain entities (Postgres / `oms_batch`)

| Entity | Role |
|--------|------|
| `ComputeEnvironment` | Maps to Batch CE |
| `JobQueue` | Maps to Batch JQ |
| `JobDefinition` | Maps to Batch JD (+ `job_type`: import/export/task) |
| `ScheduledJob` | Logical scheduled job (UI “job”) |
| `ScheduledJobStep` | Steps within a job (+ optional `LastSyncedAt`) |
| `JobDependency` | Step ordering / conditions |
| `JobRun` / `JobRunAttempt` / `JobRunEvent` | Execution audit |

Terraform stages **C/D** upsert overlapping rows via bastion SQL; API owns runtime CRUD from UI.

---

## Configuration (ECS / local)

| Setting | Purpose |
|---------|---------|
| `ConnectionStrings:DefaultConnection` | Postgres (+ `Database__Schema` for search path on ECS) |
| `JwtValidation:*` | Keycloak issuer validation on ECS |
| `EventBridgeScheduler:Enabled` | `false` = NoOp schedules; `true` = real AWS schedules |
| `EventBridgeScheduler:NamePrefix` | e.g. `oms-pod-dev` |
| `EventBridgeScheduler:ScheduleGroupName` | Align with Step Functions module |
| `EventBridgeScheduler:StateMachineArn` | Target SFN for cron |
| `EventBridgeScheduler:SchedulerExecutionRoleArn` | IAM for `scheduler:*` |
| `RUN_MIGRATIONS_ON_STARTUP` | EF migrate on boot (baselined envs only) |

Local: copy `appsettings.Development.local.json.example`; keep `EventBridgeScheduler:Enabled` **false** without IAM.

---

## EventBridge vs NoOp

| `Enabled` | Behavior |
|-----------|----------|
| `false` | Schedules saved in DB; placeholder ARN; safe for laptop dev |
| `true` | Real `scheduler:CreateSchedule`; must match infra IAM from `06-aws-stepfunction` |

ECS task env documents this — UI schedules “do nothing” in AWS if disabled (see [07-batch-scheduler-api-ui.md](./07-batch-scheduler-api-ui.md)).

---

## Tests

```powershell
dotnet test
```

Unit tests cover: `ScheduledJobScheduleService`, `ComputeEnvironmentService`, cron formatting, job run status transitions.

---

## ECR & deploy

| Item | Value |
|------|--------|
| ECR repo | `oms-aws-job-scheduler` |
| Harness | `OMSDEVAWSECSSERVICESHAREDCD` — set `imagePath` + tag |
| Terraform | `22-servicemanagerscheduler` — `container_image` var |

---

## Related

- [07-batch-scheduler-api-ui.md](./07-batch-scheduler-api-ui.md)  
- [13-deployables-catalog.md](./13-deployables-catalog.md)  
- [16-operations-runbooks.md](./16-operations-runbooks.md)  
- Repo `README.md` — local setup, API table, IAM notes  
