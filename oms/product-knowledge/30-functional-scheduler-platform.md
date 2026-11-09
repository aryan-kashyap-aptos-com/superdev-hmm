# Functional guide — scheduler platform (`oms_batch`)

**Repo:** `oms-aws-job-scheduler`  
**API inventory:** [23-job-scheduler-complete-reference.md](./23-job-scheduler-complete-reference.md).  
**UI path:** [07-batch-scheduler-api-ui.md](./07-batch-scheduler-api-ui.md).

The scheduler is the **system of record** for “what Batch *should* run” in the Service Manager modernization model. AWS Batch only executes; this service + Postgres **`oms_batch`** catalog + (optional) EventBridge + Step Functions **orchestrate**.

---

## Catalog entities (what operators manage)

| Entity | Purpose | AWS mirror |
|--------|---------|------------|
| **Compute environment** | Fargate pool definition | `aws_batch_compute_environment` |
| **Job queue** | Where jobs land | `aws_batch_job_queue` |
| **Job definition** | Image, CPU, command, env | `aws_batch_job_definition` |
| **Scheduled job** | Named workflow in UI | Logical grouping |
| **Scheduled job step** | Single Batch step in a job | Maps to SFN map item |
| **Schedule** | Cron / rate | EventBridge Scheduler rule (when enabled) |
| **Job run** | One execution attempt | Batch job + status mirror |
| **Job run attempt** | Retry attempt | `AWS_BATCH_JOB_ATTEMPT` |
| **Job run event** | Audit trail | API-appendable |
| **Job dependency** | Run-after rules | Orchestrator / SFN input |

All persisted under schema **`oms_batch`** (`Database:Schema` in appsettings).

---

## Operator journeys → API

| UI action | API (typical) |
|---------|----------------|
| Register platform CE/JQ from AWS | `POST /api/v1/compute-environments`, `POST /api/v1/job-queues` |
| Register job definition | `POST /api/v1/job-definitions` |
| Create scheduled job | `POST /api/v1/scheduled-jobs` |
| Add steps | `POST /api/v1/scheduled-jobs/{id}/steps` |
| Set cron | `PUT /api/v1/scheduled-jobs/{id}/schedule` |
| Manual / test run | `POST /api/v1/job-runs` |
| Inspect run | `GET /api/v1/job-runs/{id}`, `…/events`, `…/attempts` |
| Execution plan for SFN | `GET /api/v1/orchestrator/scheduled-jobs/{jobId}/plan` |

Full route list: [23](./23-job-scheduler-complete-reference.md).

---

## Job run lifecycle (functional)

States match **`JobRunStatus`**: Submitted → Pending → Runnable → Starting → Running → **Succeeded | Failed | Cancelled**.

**Rules:** `JobRunStatusTransitions` in Domain — illegal transitions throw `InvalidJobRunTransitionException`; PATCH status must respect graph.

**Who updates status:**

- Step Functions / workers call API or internal services after Batch events  
- Failed Batch exit codes surface as **Failed** runs (operator checks CloudWatch + exit code tables in [29](./29-functional-batch-jobs.md))

---

## EventBridge integration

| `EventBridgeScheduler:Enabled` | Behavior |
|-------------------------------|----------|
| **false** (local default) | `NoOpEventBridgeScheduleService` — DB rows update, **no AWS schedule** |
| **true** (target prod) | `EventBridgeScheduleService` creates/updates schedules → **StateMachineArn** |

Settings: `ScheduleGroupName`, `NamePrefix`, `SchedulerExecutionRoleArn` ([appsettings.json](RepoSuite/oms-aws-job-scheduler/src/oms-aws-job-scheduler.Api/appsettings.json)).

---

## Auth & deployment

| Concern | Behavior |
|---------|----------|
| ECS task | JWT issuer = Keycloak realm (`JwtValidation__ValidIssuer`) |
| ShopLogic path | Browser never holds scheduler JWT — **proxy** adds server-side auth |
| Migrations | `RUN_MIGRATIONS_ON_STARTUP=true` once per env bootstrap |
| Health | `/health`, `/health/ready` (Npgsql), ALB uses same paths |

Stack: `22-servicemanagerscheduler`.

---

## Validation layer

FluentValidation in `Application/Validation/*` — invalid DTO → **`ValidationAppException`** → middleware JSON error.

Concurrency: entities implement `IConcurrencyAware`; updates use row version pattern where configured.

---

## Related

- [27-functional-cross-repo-flows.md](./27-functional-cross-repo-flows.md)  
- [17-workflows-and-step-functions.md](./17-workflows-and-step-functions.md)  
- [18-scheduler-api.md](./18-scheduler-api.md)
