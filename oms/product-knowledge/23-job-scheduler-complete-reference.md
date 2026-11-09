# `oms-aws-job-scheduler` — complete reference

**Repo:** `RepoSuite/oms-aws-job-scheduler`  
**Coverage:** **100% file inventory** — [inventories/scheduler-all-files.txt](./inventories/scheduler-all-files.txt) (114 files), **98** `.cs` → [inventories/scheduler-cs-by-layer.md](./inventories/scheduler-cs-by-layer.md).  
**Functional guide:** [30-functional-scheduler-platform.md](./30-functional-scheduler-platform.md).  
**Narrative:** [18-scheduler-api.md](./18-scheduler-api.md).

---

## Layers

| Layer | Project | Responsibility |
|-------|---------|----------------|
| Api | `src/oms-aws-job-scheduler.Api` | Controllers, `Program.cs`, Swagger, health probes |
| Application | `src/oms-aws-job-scheduler.Application` | Services, DTOs, FluentValidation |
| Domain | `src/oms-aws-job-scheduler.Domain` | Entities, enums, transition rules |
| Infrastructure | `src/oms-aws-job-scheduler.Infrastructure` | EF Core, migrations, EventBridge |
| Tests | `tests/oms-aws-job-scheduler.UnitTests` | Unit tests |

---

## HTTP API (100% routes)

Base: `/api/v1`. JSON enums as strings. Validation via `FluentValidationFilter`.

### `HealthController` — `api/v1/health`

| Method | Path | Notes |
|--------|------|--------|
| GET | `live` | API health |
| — | `/`, `/health`, `/health/live`, `/health/ready` | ECS/ALB (in `Program.cs`) |

### `ComputeEnvironmentsController` — `api/v1/compute-environments`

| GET | list |
| GET | `{id:guid}` |
| POST | create |
| PUT | `{id:guid}` |
| DELETE | `{id:guid}` |

### `JobQueuesController` — `api/v1/job-queues`

| GET | list |
| GET | `{id:guid}` |
| POST | create |
| PUT | `{id:guid}` |
| DELETE | `{id:guid}` |

### `JobDefinitionsController` — `api/v1/job-definitions`

| GET | list (paging) |
| GET | `{id:guid}` |
| POST | create |
| PUT | `{id:guid}` |
| DELETE | `{id:guid}` |

### `ScheduledJobTypesController` — `api/v1/scheduled-job-types`

| GET | list types |

### `ScheduledJobsController` — `api/v1/scheduled-jobs`

| GET | list |
| GET | `{id:guid}` |
| POST | create |
| PUT | `{id:guid}` |
| DELETE | `{id:guid}` |
| PUT | `{id:guid}/schedule` | attach cron / EventBridge |
| DELETE | `{id:guid}/schedule` | remove schedule |
| GET | `{jobId:guid}/steps` | |
| GET | `{jobId:guid}/steps/{stepId:guid}` | |
| POST | `{jobId:guid}/steps` | |
| PUT | `{jobId:guid}/steps/{stepId:guid}` | |
| DELETE | `{jobId:guid}/steps/{stepId:guid}` | |

### `JobRunsController` — `api/v1/job-runs`

| GET | list |
| GET | `{id:guid}` |
| POST | create |
| PATCH | `{id:guid}/status` |
| DELETE | `{id:guid}` |
| GET | `{id:guid}/attempts` |
| GET | `{id:guid}/events` |
| POST | `{id:guid}/events` |
| GET | `{id:guid}/dependencies` |
| POST | `{id:guid}/dependencies` |
| DELETE | `{id:guid}/dependencies/{dependencyId:guid}` |

### `OrchestratorController` — `api/v1/orchestrator`

| GET | `scheduled-jobs/{jobId:guid}/plan` | Step Function–style plan |

---

## Domain model

### Entities (`oms_batch` schema — `Database:Schema` = `oms_batch`)

| Entity | Notes |
|--------|--------|
| `ComputeEnvironment` | CE catalog row |
| `JobQueue` | Queue catalog |
| `JobDefinition` | JD metadata |
| `ScheduledJob` | Multi-step scheduled work |
| `ScheduledJobStep` | Steps + `LastSyncedAt` migration |
| `JobRun` | Run instance |
| `JobRunAttempt` | AWS Batch attempt mirror |
| `JobRunEvent` | Audit stream |
| `JobDependency` | Between runs |

`IConcurrencyAware` on CE, JQ, JD, ScheduledJob, JobQueue, JobRun.

### Enums

| Enum | Values |
|------|--------|
| `JobRunStatus` | Submitted, Pending, Runnable, Starting, Running, Succeeded, Failed, Cancelled |
| `ComputeEnvironmentType` | (see Domain source) |
| `ScheduledJobType` | (see Domain source) |
| `DependencyCondition` | (see Domain source) |

**Transitions:** `JobRunStatusTransitions.CanTransition` / `IsTerminal` — legal edges only (Batch-style lifecycle).

---

## Application services & DTOs

| Service | Interface | DTO file |
|---------|-----------|----------|
| `ComputeEnvironmentService` | `IComputeEnvironmentService` | `ComputeEnvironmentDtos.cs` |
| `JobQueueService` | `IJobQueueService` | `JobQueueDtos.cs` |
| `JobDefinitionService` | `IJobDefinitionService` | `JobDefinitionDtos.cs` |
| `ScheduledJobService` | `IScheduledJobService` | `ScheduledJobDtos.cs`, `ScheduledJobStepDtos.cs` |
| `ScheduledJobScheduleService` | `IScheduledJobScheduleService` | `ScheduleScheduledJobDtos.cs` |
| `ScheduledJobTypeService` | `IScheduledJobTypeService` | `ScheduledJobTypeDtos.cs` |
| `JobRunService` | `IJobRunService` | `JobRunDtos.cs` |
| `OrchestratorService` | `IOrchestratorService` | `OrchestratorDtos.cs` |

Validators: one FluentValidation class per aggregate under `Application/Validation/`.

Exceptions: `ValidationAppException`, `NotFoundException`, `ConflictException`, `InvalidJobRunTransitionException`.

---

## Infrastructure

| Component | Type |
|-----------|------|
| `OmsAwsJobSchedulerDbContext` | EF Core |
| `OmsAwsJobSchedulerRepository` | `IOmsAwsJobSchedulerRepository` |
| `UnitOfWork` | `IUnitOfWork` |
| `EventBridgeScheduleService` | Real AWS Scheduler |
| `NoOpEventBridgeScheduleService` | When disabled |
| `NpgsqlDataSourceFactory` | Connection pooling |
| Migrations | `20260706000000_InitialCreate`, `20261026064854_AddScheduledJobStepLastSyncedAt` |

---

## Configuration

### `appsettings.json`

| Key | Purpose |
|-----|---------|
| `ConnectionStrings:DefaultConnection` | App DB user (`SearchPath=oms_batch` in ECS) |
| `ConnectionStrings:AdminConnection` | Migrations |
| `Database:Schema` | `oms_batch` |
| `EventBridgeScheduler:Enabled` | `false` locally → NoOp |
| `EventBridgeScheduler:ScheduleGroupName` | AWS group |
| `EventBridgeScheduler:NamePrefix` | Schedule name prefix |
| `EventBridgeScheduler:StateMachineArn` | Target SFN |
| `EventBridgeScheduler:SchedulerExecutionRoleArn` | IAM role |
| `AWSRegion` | default `us-east-1` |

### Environment variables (ECS / local)

| Variable | Effect |
|----------|--------|
| `RUN_MIGRATIONS_ON_STARTUP` | `true` → `MigrateAsync()` on boot |
| `ENABLE_SWAGGER` | `true` → Swagger UI in non-Dev |
| `ConnectionStrings__DefaultConnection` | Overrides appsettings |
| `ConnectionStrings__AdminConnection` | Migration user |

ECS task definition: stack `22-servicemanagerscheduler` ([07-batch-scheduler-api-ui.md](./07-batch-scheduler-api-ui.md)).

---

## Tests (all files in repo)

| Test class | Focus |
|------------|--------|
| `ComputeEnvironmentServiceTests` | CE service |
| `ScheduledJobScheduleServiceTests` | Cron + EventBridge |
| `JobRunStatusTransitionsTests` | State machine |
| `CronExpressionFormatterTests` | AWS cron format |

---

## Related

- [17-workflows-and-step-functions.md](./17-workflows-and-step-functions.md)  
- [13-deployables-catalog.md](./13-deployables-catalog.md) — ECR `oms-aws-job-scheduler`
